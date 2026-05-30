"""Parse OpenMATB session CSV logs and segment them into experimental blocks."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .study_design import GAUGE_TO_BLOCK

COLUMNS = ["logtime", "scenario_time", "type", "module", "address", "value"]
_TRUE_VALUES = {"1", "True", "true"}

_BRIEFING_RE = re.compile(r"briefing_(F\d)\.txt")
_PANEL_RE = re.compile(r"panels/F\d/block_([A-C])_")
_PANEL_FB_RE = re.compile(r"panels/(F\d)/block_([A-C])_")  # captures (form, block)
_MENTAL_RE = re.compile(r"mental_model_block_([A-C])")
_FAILURE_RE = re.compile(r"^(.*)-failure$")


@dataclass
class Block:
    """One experimental block within a session: a scenario_time interval [start, end)."""
    form: str            # "F1" | "F2" | "F3"
    block_letter: str    # "A" | "B" | "C"  (may be "" if undetectable)
    start_time: float    # scenario_time of the briefing event
    end_time: float      # scenario_time of the next briefing, or +inf for the last block


def load_raw(path: str | Path) -> pd.DataFrame:
    """Read a session CSV into a DataFrame with typed columns.

    `scenario_time` and `logtime` are floats; `value` stays a string (heterogeneous).
    """
    df = pd.read_csv(path, dtype=str)
    # Defensive: some aborted logs may lack the header or columns; keep known columns.
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[COLUMNS].copy()
    df["logtime"] = pd.to_numeric(df["logtime"], errors="coerce")
    df["scenario_time"] = pd.to_numeric(df["scenario_time"], errors="coerce")
    return df


def _briefing_starts(df: pd.DataFrame) -> list[tuple[str, float]]:
    """Return (form, scenario_time) for each experimental briefing, in order.

    Real logs fire both an `event` and a `parameter` row per briefing (a few ms
    apart); we key off the `event` row and keep the first occurrence per form.
    """
    mask = (
        (df["module"] == "instructions")
        & (df["address"] == "filename")
        & (df["type"] == "event")
        & (df["value"].astype(str).str.contains("briefing_F"))
    )
    seen: set[str] = set()
    out: list[tuple[str, float]] = []
    for _, row in df[mask].sort_values("scenario_time").iterrows():
        m = _BRIEFING_RE.search(str(row["value"]))
        if not m:
            continue
        form = m.group(1)
        if form in seen:
            continue
        seen.add(form)
        out.append((form, float(row["scenario_time"])))
    return out


def _detect_block_letter(window: pd.DataFrame) -> str:
    """Find the block letter (A/B/C) from panel or mental-model file paths in a window."""
    values = window["value"].dropna().astype(str)
    for v in values:
        m = _PANEL_RE.search(v)
        if m:
            return m.group(1)
    for v in values:
        m = _MENTAL_RE.search(v)
        if m:
            return m.group(1)
    return ""


def segment_blocks(df: pd.DataFrame) -> list[Block]:
    """Split a session into experimental blocks (practice excluded).

    Each block spans [briefing_start, next_briefing_start); the last block is open-ended.
    """
    starts = _briefing_starts(df)
    blocks: list[Block] = []
    for i, (form, start) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else float("inf")
        window = df[(df["scenario_time"] >= start) & (df["scenario_time"] < end)]
        blocks.append(
            Block(
                form=form,
                block_letter=_detect_block_letter(window),
                start_time=start,
                end_time=end,
            )
        )
    return blocks


def rows_for_block(df: pd.DataFrame, block: Block) -> pd.DataFrame:
    """Return the rows whose scenario_time falls inside the block interval."""
    mask = (df["scenario_time"] >= block.start_time) & (df["scenario_time"] < block.end_time)
    return df[mask].copy()


def panel_forms_blocks(block_rows: pd.DataFrame) -> set[tuple[str, str]]:
    """Distinct (form, block_letter) pairs named by panel paths in a block window.

    A correctly-built block fires panels for one form/block only, so this set
    should have at most one element. More than one signals a labelling problem.
    """
    values = block_rows["value"].dropna().astype(str)
    return {(m.group(1), m.group(2)) for v in values if (m := _PANEL_FB_RE.search(v))}


def block_letter_from_gauges(block_rows: pd.DataFrame) -> str:
    """Independently derive the block letter from which sysmon gauges failed.

    Each block uses a fixed pair of gauges (see ``GAUGE_BY_BLOCK``). Returns the
    single agreed letter, or "" if there are no failures or they conflict.
    """
    failures = block_rows[
        (block_rows["module"] == "sysmon")
        & (block_rows["type"] == "event")
        & (block_rows["address"].astype(str).str.endswith("-failure"))
        & (block_rows["value"].astype(str).isin(_TRUE_VALUES))
    ]
    letters = set()
    for addr in failures["address"].astype(str):
        m = _FAILURE_RE.match(addr)
        if m and m.group(1) in GAUGE_TO_BLOCK:
            letters.add(GAUGE_TO_BLOCK[m.group(1)])
    return letters.pop() if len(letters) == 1 else ""
