"""Assemble a tidy per-(participant, form, block) metrics table across sessions."""
from __future__ import annotations

import pandas as pd

from .discovery import SessionInfo, find_study_sessions
from .parsing import block_letter_from_gauges, load_raw, rows_for_block, segment_blocks
from .metrics_resman import resman_metrics
from .metrics_comms import comms_metrics
from .metrics_sysmon import sysmon_metrics

_KEY_COLS = ["participant", "form", "block", "session_file"]
_DEFAULT_SOLVER_DELAY = 1000.0


def _metric_columns() -> list[str]:
    """Full metric column set, derived from the metric functions on an empty frame."""
    empty = pd.DataFrame(columns=["logtime", "scenario_time", "type",
                                  "module", "address", "value"])
    return (list(resman_metrics(empty).keys())
            + list(comms_metrics(empty).keys())
            + list(sysmon_metrics(empty).keys()))


def _solver_delay(df: pd.DataFrame) -> float:
    """The aid's auto-solve delay (ms) for a session; default 1000 if not logged."""
    sel = df[(df["module"] == "sysmon") & (df["address"] == "automaticsolverdelay")]
    vals = pd.to_numeric(sel["value"], errors="coerce").dropna()
    return float(vals.iloc[0]) if len(vals) else _DEFAULT_SOLVER_DELAY


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
        solver_delay = _solver_delay(df)
        for block in segment_blocks(df):
            block_rows = rows_for_block(df, block)
            # Resolve the block letter: panel (primary) -> failed-gauge fallback ->
            # scenario-derived hint for single-block sessions.
            block_letter = (block.block_letter
                            or block_letter_from_gauges(block_rows)
                            or (info.block or ""))
            record = {
                "participant": info.participant,
                "form": block.form,
                "block": block_letter,
                "session_file": info.path.name,
            }
            record.update(resman_metrics(block_rows))
            record.update(comms_metrics(block_rows))
            record.update(sysmon_metrics(block_rows, automaticsolverdelay=solver_delay))
            records.append(record)

    if not records:
        # No sessions / blocks: return an empty frame that still has every column,
        # so downstream grouping and plotting code does not crash.
        return pd.DataFrame(columns=_KEY_COLS + _metric_columns())

    table = pd.DataFrame(records)
    ordered = _KEY_COLS + [c for c in table.columns if c not in _KEY_COLS]
    return table[ordered]
