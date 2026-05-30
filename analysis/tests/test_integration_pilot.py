"""Smoke test against the real pilot logs (skips cleanly if none are present)."""
import math
import pytest

from matb_analysis.discovery import find_study_sessions
from matb_analysis.aggregate import build_metrics_table


def test_pilot_sessions_discovered():
    sessions = find_study_sessions()
    if not sessions:
        pytest.skip("no OpenMATB study sessions present")
    assert all(s.scenario_kind in {"full", "single_block"} for s in sessions)


def test_full_session_has_three_blocks_in_order():
    sessions = [s for s in find_study_sessions() if s.scenario_kind == "full"]
    if not sessions:
        pytest.skip("no full_PXX pilot sessions present")
    table = build_metrics_table(sessions)
    # Pick the largest full session (most complete run).
    biggest = max(sessions, key=lambda s: s.path.stat().st_size)
    sub = table[table.session_file == biggest.path.name]
    assert len(sub) == 3, f"expected 3 blocks, got {len(sub)}"
    assert list(sub["form"]) == ["F1", "F2", "F3"]
    assert list(sub["block"]) == ["A", "B", "C"]  # P01 order


def test_metrics_table_columns_present():
    sessions = find_study_sessions()
    if not sessions:
        pytest.skip("no sessions present")
    table = build_metrics_table(sessions)
    for col in ["rmsd_mean", "pct_in_tolerance_mean", "accuracy", "mean_rt_hit"]:
        assert col in table.columns
