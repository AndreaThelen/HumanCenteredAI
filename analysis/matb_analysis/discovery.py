"""Discover OpenMATB study sessions and map each to participant / condition."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Dedicated, curated session-logs folder for this analysis. Only logs placed here
# are analysed. Copy the relevant OpenMATB session CSVs into it.
# discovery.py -> matb_analysis -> analysis
_ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SESSIONS_DIR = _ANALYSIS_ROOT / "session_logs"

_FULL_RE = re.compile(r"full_(P\d+)")
_SINGLE_RE = re.compile(r"(F\d)_block_([A-C])")
_MIN_ROWS = 1  # skip empty files; real aborted runs are filtered by a valid study scenario_path


@dataclass
class SessionInfo:
    path: Path
    participant: str
    scenario_path: str
    scenario_kind: str          # "full" | "single_block" | "other"
    form: str | None = None     # set for single_block sessions
    block: str | None = None    # set for single_block sessions


def scenario_kind_and_participant(scenario_path: str):
    """Classify a scenario_path string. Returns (kind, participant, form, block)."""
    s = str(scenario_path).replace("\\", "/")
    if "scenarios/study/" not in s:
        return "other", None, None, None
    m = _FULL_RE.search(s)
    if m:
        return "full", m.group(1), None, None
    m = _SINGLE_RE.search(s)
    if m:
        return "single_block", f"{m.group(1)}_{m.group(2)}", m.group(1), m.group(2)
    return "other", None, None, None


def _read_scenario_path(csv_path: Path) -> str | None:
    """Read the scenario_path value from a session CSV without loading the whole file."""
    try:
        head = pd.read_csv(csv_path, dtype=str, nrows=50)
    except Exception:
        return None
    rows = head[head.get("type") == "scenario_path"]
    if rows.empty:
        return None
    return str(rows.iloc[0]["value"])


def find_study_sessions(sessions_dir: str | Path = DEFAULT_SESSIONS_DIR) -> list[SessionInfo]:
    """Return SessionInfo for every non-trivial study session under sessions_dir.

    Searches recursively, so logs may sit directly in the folder or inside the
    OpenMATB date subfolders (e.g. ``2026-05-30/19_*.csv``).
    """
    sessions_dir = Path(sessions_dir)
    if not sessions_dir.exists():
        return []
    out: list[SessionInfo] = []
    for csv_path in sorted(sessions_dir.rglob("*.csv")):
        # Skip tiny / aborted files quickly.
        try:
            n_lines = sum(1 for _ in csv_path.open(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
        if n_lines < _MIN_ROWS:
            continue
        sp = _read_scenario_path(csv_path)
        if sp is None:
            continue
        kind, pid, form, block = scenario_kind_and_participant(sp)
        if kind == "other":
            continue
        out.append(SessionInfo(
            path=csv_path,
            participant=pid if pid else "?",
            scenario_path=sp,
            scenario_kind=kind,
            form=form,
            block=block,
        ))
    return out
