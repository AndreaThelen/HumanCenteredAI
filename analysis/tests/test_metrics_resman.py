import math
import pandas as pd
from matb_analysis.metrics_resman import resman_metrics

COLUMNS = ["logtime", "scenario_time", "type", "module", "address", "value"]

def _rows(triples):
    # triples: (address, value); fills boilerplate columns
    data = [(0.0, float(i), "performance", "resman", addr, val)
            for i, (addr, val) in enumerate(triples)]
    return pd.DataFrame(data, columns=COLUMNS)

def test_rmsd_and_mad():
    df = _rows([("a_deviation", "3"), ("a_deviation", "-4")])  # rms=sqrt(12.5)=3.5355, mad=3.5
    m = resman_metrics(df)
    assert math.isclose(m["rmsd_a"], math.sqrt(12.5), rel_tol=1e-9)
    assert math.isclose(m["mad_a"], 3.5, rel_tol=1e-9)

def test_pct_in_tolerance_ignores_non_binary():
    df = _rows([("a_in_tolerance", "1"), ("a_in_tolerance", "0"),
                ("a_in_tolerance", "1"), ("a_in_tolerance", "nan")])
    m = resman_metrics(df)
    assert math.isclose(m["pct_in_tolerance_a"], 200.0 / 3.0, rel_tol=1e-9)  # 2 of 3 valid

def test_excursions_converted_to_seconds():
    df = _rows([("a_response_time", "4000"), ("b_response_time", "6000")])  # ms -> s
    m = resman_metrics(df)
    assert m["n_excursions"] == 2
    assert math.isclose(m["mean_excursion_sec"], 5.0, rel_tol=1e-9)

def test_empty_block_returns_nan_not_crash():
    df = _rows([])
    m = resman_metrics(df)
    assert math.isnan(m["rmsd_mean"])
    assert m["n_excursions"] == 0

# --- aggregate test (appended) ---
from pathlib import Path
from matb_analysis.aggregate import build_metrics_table
from matb_analysis.discovery import SessionInfo

def test_build_metrics_table_one_full_session(tmp_path):
    header = "logtime,scenario_time,type,module,address,value\n"
    rows = [
        "1,0,scenario_path,,,includes/scenarios/study/full_P01.txt",
        # block F1/A
        "2,10,event,instructions,filename,study/briefing_F1.txt",
        "3,12,event,instructions,filename,study/panels/F1/block_A_event_01.txt",
        "4,13,performance,resman,a_deviation,100",
        "5,14,performance,communications,response_was_needed,1",
        "6,14,performance,communications,sdt_value,HIT",
        "7,14,performance,communications,response_time,2000",
        "8,14,performance,communications,response_deviation,0",
        # block F2/B
        "9,30,event,instructions,filename,study/briefing_F2.txt",
        "10,31,event,instructions,filename,study/panels/F2/block_B_event_03.txt",
        "11,32,performance,resman,a_deviation,200",
    ]
    csv = tmp_path / "s.csv"
    csv.write_text(header + "\n".join(rows) + "\n", encoding="utf-8")
    info = SessionInfo(path=csv, participant="P01",
                       scenario_path="includes/scenarios/study/full_P01.txt",
                       scenario_kind="full")
    table = build_metrics_table([info])
    assert set(table["form"]) == {"F1", "F2"}
    assert list(table.columns[:4]) == ["participant", "form", "block", "session_file"]
    f1 = table[table.form == "F1"].iloc[0]
    assert f1["block"] == "A"
    assert f1["n_hit"] == 1
    assert f1["rmsd_a"] == 100.0

def test_build_metrics_table_empty_has_columns_and_no_rows():
    """No sessions -> empty frame that still exposes every column (so the
    notebook's grouping/plotting cells don't crash before any data exists)."""
    table = build_metrics_table([])
    assert len(table) == 0
    assert list(table.columns[:4]) == ["participant", "form", "block", "session_file"]
    for col in ["rmsd_mean", "pct_in_tolerance_mean", "accuracy", "mean_rt_hit"]:
        assert col in table.columns
