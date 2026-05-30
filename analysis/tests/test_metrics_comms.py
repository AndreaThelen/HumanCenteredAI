import math
import pandas as pd
from matb_analysis.metrics_comms import comms_metrics

COLUMNS = ["logtime", "scenario_time", "type", "module", "address", "value"]

def _event(t, **fields):
    """One comms performance event = several rows sharing scenario_time t."""
    return [(0.0, float(t), "performance", "communications", addr, str(val))
            for addr, val in fields.items()]

def _df(events):
    rows = []
    for ev in events:
        rows.extend(ev)
    return pd.DataFrame(rows, columns=COLUMNS)

def test_hit_miss_fa_counts_and_accuracy():
    df = _df([
        _event(1, response_was_needed=1, correct_radio=1, response_deviation=0,
               response_time=2000, sdt_value="HIT"),
        _event(2, response_was_needed=1, correct_radio=0, response_deviation="nan",
               response_time="nan", sdt_value="MISS"),
        _event(3, response_was_needed=0, correct_radio=0, response_deviation=0,
               response_time=1500, sdt_value="FA"),
    ])
    m = comms_metrics(df)
    assert m["n_signal"] == 2      # HIT + MISS (FA is not a signal trial)
    assert m["n_hit"] == 1
    assert m["n_miss"] == 1
    assert m["n_fa"] == 1
    assert math.isclose(m["accuracy"], 0.5, rel_tol=1e-9)
    assert math.isclose(m["miss_rate"], 0.5, rel_tol=1e-9)

def test_mean_rt_hit_uses_hits_only():
    df = _df([
        _event(1, response_was_needed=1, correct_radio=1, response_deviation=0,
               response_time=2000, sdt_value="HIT"),
        _event(2, response_was_needed=1, correct_radio=1, response_deviation=0,
               response_time=4000, sdt_value="HIT"),
        _event(3, response_was_needed=1, correct_radio=0, response_deviation=1.0,
               response_time=9000, sdt_value="BAD_FREQ"),
    ])
    m = comms_metrics(df)
    assert math.isclose(m["mean_rt_hit"], 3000.0, rel_tol=1e-9)  # excludes BAD_FREQ

def test_mean_abs_freq_dev_over_responded():
    df = _df([
        _event(1, response_was_needed=1, correct_radio=0, response_deviation=-2.0,
               response_time=3000, sdt_value="BAD_FREQ"),
        _event(2, response_was_needed=1, correct_radio=0, response_deviation="nan",
               response_time="nan", sdt_value="MISS"),
    ])
    m = comms_metrics(df)
    assert math.isclose(m["mean_abs_freq_dev"], 2.0, rel_tol=1e-9)  # MISS excluded (nan)

def test_empty_block_returns_zero_counts_and_nan_rates():
    m = comms_metrics(pd.DataFrame([], columns=COLUMNS))
    assert m["n_signal"] == 0
    assert math.isnan(m["accuracy"])
    assert math.isnan(m["mean_rt_hit"])
