"""Embedded study-design constants for validation.

These mirror the scenario generator
(``OpenMATB/includes/scenarios/study/_regenerate.py``) so the analysis can
cross-check a session's realised structure without ever reading the OpenMATB
scenario files. Keep these in sync if the design changes.
"""
from __future__ import annotations

# Number of participant scenarios generated (mirrors _regenerate.py).
N_PARTICIPANTS = 20

# Base counterbalancing set of 10 unique (form, block) orderings. Participants
# beyond P10 replicate this set in order (P11 == P01, ..., P20 == P10).
_BASE_ORDERS: list[list[tuple[str, str]]] = [
    [("F1", "A"), ("F2", "B"), ("F3", "C")],
    [("F1", "A"), ("F3", "B"), ("F2", "C")],
    [("F2", "A"), ("F1", "B"), ("F3", "C")],
    [("F2", "A"), ("F3", "B"), ("F1", "C")],
    [("F3", "A"), ("F1", "B"), ("F2", "C")],
    [("F3", "A"), ("F2", "B"), ("F1", "C")],
    [("F1", "B"), ("F2", "C"), ("F3", "A")],
    [("F2", "B"), ("F3", "C"), ("F1", "A")],
    [("F3", "B"), ("F1", "C"), ("F2", "A")],
    [("F1", "C"), ("F2", "A"), ("F3", "B")],
]

# Counterbalanced (form, block) order each participant runs (Latin square).
PARTICIPANT_ORDERS: dict[str, list[tuple[str, str]]] = {
    f"P{i + 1:02d}": _BASE_ORDERS[i % len(_BASE_ORDERS)]
    for i in range(N_PARTICIPANTS)
}

# The two sysmon gauges each block uses, and the inverse (gauge -> block letter).
GAUGE_BY_BLOCK: dict[str, tuple[str, str]] = {
    "A": ("scales-1", "scales-3"),
    "B": ("lights-1", "lights-2"),
    "C": ("scales-2", "scales-4"),
}
GAUGE_TO_BLOCK: dict[str, str] = {
    gauge: letter for letter, gauges in GAUGE_BY_BLOCK.items() for gauge in gauges
}
