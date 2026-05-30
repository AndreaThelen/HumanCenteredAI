"""Embedded study-design constants for validation.

These mirror the scenario generator
(``OpenMATB/includes/scenarios/study/_regenerate.py``) so the analysis can
cross-check a session's realised structure without ever reading the OpenMATB
scenario files. Keep these in sync if the design changes.
"""
from __future__ import annotations

# Counterbalanced (form, block) order each participant runs (Latin square).
PARTICIPANT_ORDERS: dict[str, list[tuple[str, str]]] = {
    "P01": [("F1", "A"), ("F2", "B"), ("F3", "C")],
    "P02": [("F1", "A"), ("F3", "B"), ("F2", "C")],
    "P03": [("F2", "A"), ("F1", "B"), ("F3", "C")],
    "P04": [("F2", "A"), ("F3", "B"), ("F1", "C")],
    "P05": [("F3", "A"), ("F1", "B"), ("F2", "C")],
    "P06": [("F3", "A"), ("F2", "B"), ("F1", "C")],
    "P07": [("F1", "B"), ("F2", "C"), ("F3", "A")],
    "P08": [("F2", "B"), ("F3", "C"), ("F1", "A")],
    "P09": [("F3", "B"), ("F1", "C"), ("F2", "A")],
    "P10": [("F1", "C"), ("F2", "A"), ("F3", "B")],
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
