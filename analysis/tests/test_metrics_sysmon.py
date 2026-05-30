import math
import pandas as pd
from matb_analysis.metrics_sysmon import sysmon_metrics

COLS = ["logtime", "scenario_time", "type", "module", "address", "value"]


def _solver(t, on):
    return [(0.0, float(t), "event", "sysmon", "automaticsolver", "1" if on else "0")]


def _perf(t, name, sdt, rt):
    return [(0.0, float(t), "performance", "sysmon", "name", name),
            (0.0, float(t), "performance", "sysmon", "signal_detection", sdt),
            (0.0, float(t), "performance", "sysmon", "response_time", str(rt))]


def _df(groups):
    rows = []
    for g in groups:
        rows += g
    return pd.DataFrame(rows, columns=COLS)


def test_detection_of_aid_missed_events():
    df = _df([
        _solver(9, False), _perf(12, "F1", "HIT", 3000),   # aid off, user caught it
        _solver(39, False), _perf(50, "F2", "MISS", "nan"),  # aid off, user missed
    ])
    m = sysmon_metrics(df)
    assert m["n_aid_miss_events"] == 2
    assert m["n_detected"] == 1
    assert math.isclose(m["detection_rate"], 0.5)
    assert math.isclose(m["mean_detect_rt"], 3000.0)


def test_overwrite_vs_aidsolve_on_handled_events():
    df = _df([
        _solver(9, True), _perf(12, "F1", "HIT", 1000),   # aid solved (rt == delay)
        _solver(39, True), _perf(42, "F2", "HIT", 500),   # user preempted -> overwrite
    ])
    m = sysmon_metrics(df, automaticsolverdelay=1000)
    assert m["n_aid_handled_events"] == 2
    assert m["n_overwrite"] == 1
    assert math.isclose(m["overwrite_rate"], 0.5)


def test_false_alarms_counted():
    df = _df([_perf(20, "F3", "FA", "nan")])
    m = sysmon_metrics(df)
    assert m["n_false_alarms"] == 1
    # an FA is neither an aid-miss nor an aid-handled event
    assert m["n_aid_miss_events"] == 0
    assert m["n_aid_handled_events"] == 0


def test_empty_block_is_safe():
    m = sysmon_metrics(pd.DataFrame([], columns=COLS))
    assert m["n_aid_miss_events"] == 0
    assert m["n_false_alarms"] == 0
    assert math.isnan(m["detection_rate"])
    assert math.isnan(m["overwrite_rate"])
