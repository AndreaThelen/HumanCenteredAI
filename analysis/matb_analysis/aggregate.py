"""Assemble a tidy per-(participant, form, block) metrics table across sessions."""
from __future__ import annotations

import pandas as pd

from .discovery import SessionInfo, find_study_sessions
from .parsing import load_raw, rows_for_block, segment_blocks
from .metrics_resman import resman_metrics
from .metrics_comms import comms_metrics

_KEY_COLS = ["participant", "form", "block", "session_file"]


def build_metrics_table(sessions: list[SessionInfo] | None = None) -> pd.DataFrame:
    """Compute resman + comms metrics for every block of every session.

    If `sessions` is None, discovers them via find_study_sessions().
    Returns one tidy row per (participant, form, block).
    """
    if sessions is None:
        sessions = find_study_sessions()

    records: list[dict] = []
    for info in sessions:
        df = load_raw(info.path)
        for block in segment_blocks(df):
            block_rows = rows_for_block(df, block)
            # single-block sessions: trust the scenario-derived form/block if detection blank
            block_letter = block.block_letter or (info.block or "")
            record = {
                "participant": info.participant,
                "form": block.form,
                "block": block_letter,
                "session_file": info.path.name,
            }
            record.update(resman_metrics(block_rows))
            record.update(comms_metrics(block_rows))
            records.append(record)

    table = pd.DataFrame(records)
    if not table.empty:
        ordered = _KEY_COLS + [c for c in table.columns if c not in _KEY_COLS]
        table = table[ordered]
    return table
