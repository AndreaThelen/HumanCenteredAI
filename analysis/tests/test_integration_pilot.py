"""Smoke test against the real pilot logs (skips cleanly if none are present)."""
import pytest

from matb_analysis.discovery import find_study_sessions
from matb_analysis.aggregate import build_metrics_table
from matb_analysis.parsing import load_raw
from matb_analysis.validation import validate_session, validate_sessions
from matb_analysis.study_design import PARTICIPANT_ORDERS


def test_pilot_sessions_discovered():
    sessions = find_study_sessions()
    if not sessions:
        pytest.skip("no OpenMATB study sessions present")
    assert all(s.scenario_kind in {"full", "single_block"} for s in sessions)


def test_biggest_full_session_matches_its_latin_square():
    sessions = [s for s in find_study_sessions() if s.scenario_kind == "full"]
    if not sessions:
        pytest.skip("no full_PXX pilot sessions present")
    # Pick the largest full session (most complete run) and validate it against
    # that participant's own Latin-square order -- not a hard-coded sequence.
    biggest = max(sessions, key=lambda s: s.path.stat().st_size)
    v = validate_session(load_raw(biggest.path), biggest)
    assert v.ok, v.issues
    expected = PARTICIPANT_ORDERS[biggest.participant]
    assert v.realized == expected[:len(v.realized)]
    assert all(letter for _, letter in v.realized)  # every block letter resolved


def test_all_discovered_sessions_validate():
    sessions = find_study_sessions()
    if not sessions:
        pytest.skip("no sessions present")
    report = validate_sessions(sessions)
    bad = report[~report["ok"]]
    assert bad.empty, "sessions with validation issues:\n" + bad.to_string(index=False)


def test_metrics_table_columns_present():
    sessions = find_study_sessions()
    if not sessions:
        pytest.skip("no sessions present")
    table = build_metrics_table(sessions)
    for col in ["rmsd_mean", "pct_in_tolerance_mean", "accuracy", "mean_rt_hit"]:
        assert col in table.columns
