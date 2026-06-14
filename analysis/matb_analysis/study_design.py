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

# Per-block ground truth for scoring the mental-model probe (H2).
# Each block has 9 sysmon events: 5 routine + 2 near-miss (aid acts just in time)
# + 2 miss (aid does not act). The aid skips 2 of the 9, so its reliability is
# 7/9 (~78%). The aid acts on (is "responsible for") exactly the two gauges of
# that block's set; the other indicators it never touches.
N_EVENTS_PER_BLOCK = 9
N_MISSES_PER_BLOCK = 2
N_NEARMISS_PER_BLOCK = 2
TRUE_RELIABILITY_PCT = 100.0 * (N_EVENTS_PER_BLOCK - N_MISSES_PER_BLOCK) / N_EVENTS_PER_BLOCK

# Ground truth for the 3-question mental-model probe (H2). Mirrors
# ``HANDLED_GAUGE_BY_BLOCK`` + ``PROBE_TARGETS`` in the scenario generator
# (``OpenMATB/includes/scenarios/study/_regenerate.py``). Per block the aid
# HANDLES one active gauge (acts on it; both near-misses land here) and MISSES the
# other (its only events are the two unhandled failures), so each active gauge has
# one clean role: handled -> act=Yes, close-call=Yes, miss=No; missed -> the
# reverse. Counterbalanced across blocks so no fixed yes/no pattern wins.
HANDLED_GAUGE_BY_BLOCK: dict[str, str] = {"A": "scales-3", "B": "lights-1", "C": "scales-2"}
MISSED_GAUGE_BY_BLOCK: dict[str, str] = {
    b: next(g for g in gs if g != HANDLED_GAUGE_BY_BLOCK[b])
    for b, gs in GAUGE_BY_BLOCK.items()
}
# Which active gauge each probe question targets, by role. Mirrors
# ``_regenerate.PROBE_TARGETS`` (the scenario generator that emits the probe
# slider ids); kept here so the analysis can score each item without reading the
# scenario files.
PROBE_TARGETS: dict[str, list[tuple[str, str]]] = {
    "A": [("act", "handled"), ("miss", "missed"), ("close", "missed")],
    "B": [("act", "missed"),  ("miss", "handled"), ("close", "handled")],
    "C": [("act", "missed"),  ("miss", "handled"), ("close", "handled")],
}
# Back-compat alias: the gauge the aid skips (single-element tuple per block).
MISS_INDICATORS_BY_BLOCK: dict[str, tuple[str, ...]] = {
    b: (g,) for b, g in MISSED_GAUGE_BY_BLOCK.items()
}

