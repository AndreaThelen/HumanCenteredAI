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
