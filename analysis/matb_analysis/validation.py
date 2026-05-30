"""Validate that each session's realised structure matches the study design.

Turns silent mislabelling into explicit, reported errors by cross-checking the
independent in-log signals (briefing form, panel form/block, gauge-derived block)
against each other and against the Latin-square order for the participant.
Reads logs only -- it never opens the OpenMATB scenario files.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .discovery import SessionInfo, find_study_sessions
from .parsing import (block_letter_from_gauges, load_raw, panel_forms_blocks,
                      rows_for_block, segment_blocks)
from .study_design import PARTICIPANT_ORDERS

_REPORT_COLS = ["session_file", "participant", "kind", "ok", "n_blocks",
                "realized", "expected", "issues"]


@dataclass
class SessionValidation:
    session_file: str
    participant: str
    scenario_kind: str
    realized: list[tuple[str, str]]            # (form, block) per block, in order
    expected: list[tuple[str, str]] | None     # from the Latin square / scenario
    issues: list[str]

    @property
    def ok(self) -> bool:
        return not self.issues


def validate_session(df: pd.DataFrame, info: SessionInfo) -> SessionValidation:
    """Cross-check one session's blocks and order; collect any inconsistencies."""
    issues: list[str] = []
    realized: list[tuple[str, str]] = []

    for i, block in enumerate(segment_blocks(df), start=1):
        rows = rows_for_block(df, block)
        panel_fb = panel_forms_blocks(rows)
        panel_forms = {f for f, _ in panel_fb}
        gauge_letter = block_letter_from_gauges(rows)

        # Resolve the block letter: panel (primary) -> gauges -> scenario hint.
        letter = block.block_letter or gauge_letter or (info.block or "")
        realized.append((block.form, letter))

        # 1. briefing form must agree with the panel form.
        if panel_forms and block.form not in panel_forms:
            issues.append(f"block {i}: briefing form {block.form} != panel form "
                          f"{sorted(panel_forms)}")
        # 2. panel block letter must agree with the gauge-derived letter.
        if block.block_letter and gauge_letter and block.block_letter != gauge_letter:
            issues.append(f"block {i}: panel block {block.block_letter} != gauge block "
                          f"{gauge_letter}")
        # 3. the block letter must be determinable at all.
        if not letter:
            issues.append(f"block {i}: block letter could not be determined")

    # Session-level: realised order must match the design.
    expected: list[tuple[str, str]] | None = None
    if info.scenario_kind == "full":
        expected = PARTICIPANT_ORDERS.get(info.participant)
        if expected is None:
            issues.append(f"unknown participant {info.participant!r}; cannot check order")
        elif realized != expected[:len(realized)]:
            issues.append(f"order {realized} does not match expected {expected[:len(realized)]}")
    elif info.scenario_kind == "single_block":
        expected = [(info.form, info.block)]
        if realized and realized != expected:
            issues.append(f"single-block order {realized} does not match scenario {expected}")

    return SessionValidation(info.path.name, info.participant, info.scenario_kind,
                             realized, expected, issues)


def validate_sessions(sessions: list[SessionInfo] | None = None,
                      strict: bool = False) -> pd.DataFrame:
    """Validate every session and return a report (one row per session).

    With ``strict=True``, raise ValueError if any session has issues.
    """
    if sessions is None:
        sessions = find_study_sessions()

    records = []
    for info in sessions:
        v = validate_session(load_raw(info.path), info)
        records.append({
            "session_file": v.session_file,
            "participant": v.participant,
            "kind": v.scenario_kind,
            "ok": v.ok,
            "n_blocks": len(v.realized),
            "realized": v.realized,
            "expected": v.expected,
            "issues": "; ".join(v.issues),
        })

    report = pd.DataFrame(records, columns=_REPORT_COLS)
    if strict and not report.empty and not report["ok"].all():
        bad = report.loc[~report["ok"], ["session_file", "issues"]]
        raise ValueError("session validation failed:\n" + bad.to_string(index=False))
    return report
