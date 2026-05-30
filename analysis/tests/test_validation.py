import pandas as pd
import pytest

from matb_analysis.discovery import SessionInfo
from matb_analysis.study_design import GAUGE_BY_BLOCK
from matb_analysis.validation import validate_session, validate_sessions

COLS = ["logtime", "scenario_time", "type", "module", "address", "value"]


def _block_rows(t0, form, block, *, panel=True, gauges=True, panel_form=None, panel_block=None):
    """Rows for one block starting at scenario_time t0."""
    rows = [(0.0, t0, "event", "instructions", "filename", f"study/briefing_{form}.txt")]
    if panel:
        pf, pb = panel_form or form, panel_block or block
        rows.append((0.0, t0 + 2, "event", "instructions", "filename",
                     f"study/panels/{pf}/block_{pb}_event_03.txt"))
    if gauges:
        g1, g2 = GAUGE_BY_BLOCK[block]
        rows.append((0.0, t0 + 3, "event", "sysmon", f"{g1}-failure", "1"))
        rows.append((0.0, t0 + 4, "event", "sysmon", f"{g2}-failure", "1"))
    return rows


def _session_df(blocks, **kw):
    rows = [(0.0, 0.0, "event", "instructions", "filename", "study/briefing_practice.txt")]
    for i, (form, block) in enumerate(blocks):
        rows += _block_rows(10.0 + i * 20, form, block, **kw)
    return pd.DataFrame(rows, columns=COLS)


def _info(participant, kind="full", form=None, block=None, name="s.csv"):
    from pathlib import Path
    return SessionInfo(path=Path(name), participant=participant,
                       scenario_path=f"study/{participant}", scenario_kind=kind,
                       form=form, block=block)


def test_clean_full_session_is_ok():
    df = _session_df([("F1", "A"), ("F3", "B"), ("F2", "C")])  # P02 order
    v = validate_session(df, _info("P02"))
    assert v.ok, v.issues
    assert v.realized == [("F1", "A"), ("F3", "B"), ("F2", "C")]
    assert v.expected == [("F1", "A"), ("F3", "B"), ("F2", "C")]


def test_wrong_order_flagged():
    df = _session_df([("F1", "A"), ("F2", "B"), ("F3", "C")])  # P01 order...
    v = validate_session(df, _info("P02"))                     # ...but tagged P02
    assert not v.ok
    assert any("does not match expected" in s for s in v.issues)


def test_briefing_panel_form_mismatch_flagged():
    # briefing says F1 but the panel path says F2
    df = _session_df([("F1", "A")], panel_form="F2")
    v = validate_session(df, _info("P01"))
    assert not v.ok
    assert any("panel form" in s for s in v.issues)


def test_missing_panel_recovered_from_gauges():
    # no panel, but gauges identify block B -> letter recovered, still ok
    df = _session_df([("F3", "B")], panel=False)
    v = validate_session(df, _info("P09"))  # P09 block 1 = (F3, B)
    assert v.realized == [("F3", "B")]
    assert v.ok, v.issues


def test_partial_session_prefix_is_ok():
    df = _session_df([("F1", "A")])  # only first block of P01
    v = validate_session(df, _info("P01"))
    assert v.ok, v.issues


def test_block_letter_undetermined_flagged():
    df = _session_df([("F1", "A")], panel=False, gauges=False)
    v = validate_session(df, _info("P01"))
    assert not v.ok
    assert any("block letter" in s for s in v.issues)


def test_validate_sessions_report_and_strict(tmp_path):
    good = _session_df([("F1", "A")])
    bad = _session_df([("F2", "B")])  # wrong for P01
    gp, bp = tmp_path / "good.csv", tmp_path / "bad.csv"
    good.to_csv(gp, index=False)
    bad.to_csv(bp, index=False)
    sessions = [_info("P01", name=str(gp)), _info("P01", name=str(bp))]
    report = validate_sessions(sessions)
    assert set(report["ok"]) == {True, False}
    with pytest.raises(ValueError):
        validate_sessions(sessions, strict=True)
