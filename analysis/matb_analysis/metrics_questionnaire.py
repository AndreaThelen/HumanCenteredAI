"""Per-block questionnaire metrics for the revised (wording-only) design.

Two per-block constructs from the lean battery (per-block trust and the full
NASA-TLX were dropped in the revised design):

* **H1 -- subjective transparency.** Three agreement items (1..7), one
  reverse-keyed, averaged into a single transparency score (higher = feels more
  transparent).
* **H2 -- objective explicability.** A three-question mental-model probe, all
  yes/no, each about one *active* gauge, scored against the block's ground truth.
  Per block the aid HANDLES one active gauge and MISSES the other, giving three
  question types:
    - ``act``   -- "did the aid act on X?"            (truth Yes if X is handled).
    - ``miss``  -- "did the aid FAIL to act on Y?"    (truth Yes if Y is missed).
    - ``close`` -- "was there a close call on Z?"     (truth Yes if Z is handled;
      both near-misses land on the handled gauge).
  Every item's correct answer is determined by *this* block's roles, so it cannot
  be answered from a design-constant strategy (the old count/reliability items,
  whose truth was identical in every block, were dropped).
* **Workload mechanism check.** A single mental-effort item (1..7).

Trust is measured only once, in the end-of-session preference debrief
(``build_debrief_table`` in ``aggregate.py``), not per block.

Responses are logged by the genericscales plugin as
``performance | genericscales | <slider title> | <value>`` when each
questionnaire screen is dismissed, where ``<value>`` is in the slider's own
declared ``min..max`` units. The mental-model answers are scored against the
study ground truth (which indicators the aid acted on / skipped this block).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .study_design import HANDLED_GAUGE_BY_BLOCK, MISSED_GAUGE_BY_BLOCK

# --- slider keys (match the revised questionnaire .txt files) ---
_WHAT_KEY = "Subjective_transparency_what"
_INFO_KEY = "Subjective_information_volume"
# Reverse-keyed item ("It was hard to keep track ..."). The logged title may or
# may not carry the explicit ``_REV`` suffix, so match the stem either way.
_KEEP_TRACK_RE = re.compile(r"^Subjective_keep_track(_REV)?$")
_WORKLOAD_KEY = "Workload_overall"

_TRANSPARENCY_MIN, _TRANSPARENCY_MAX = 1, 7  # 1..7 agreement scale

# Mental-model probe sliders: MM_<BLK>_<qtype>_<scale|light><n>, all yes/no.
_PROBE_RE = re.compile(r"^MM_([ABC])_(act|miss|close)_(scale|light)(\d)$")


def _probe_truth(qtype: str, blk: str, gauge: str) -> int:
    """Ground-truth Yes(1)/No(0) for one probe item, from the block's gauge roles."""
    if qtype == "act":      # did the aid act on it? -> the handled gauge
        return int(gauge == HANDLED_GAUGE_BY_BLOCK.get(blk))
    if qtype == "miss":     # did the aid FAIL to act on it? -> the missed gauge
        return int(gauge == MISSED_GAUGE_BY_BLOCK.get(blk))
    if qtype == "close":    # was there a near-miss on it? -> the handled gauge
        return int(gauge == HANDLED_GAUGE_BY_BLOCK.get(blk))
    return 0


def _scores(block_rows: pd.DataFrame) -> dict[str, float]:
    sel = block_rows[(block_rows["module"] == "genericscales")
                     & (block_rows["type"] == "performance")]
    out: dict[str, float] = {}
    for _, r in sel.iterrows():
        out[str(r["address"])] = pd.to_numeric(r["value"], errors="coerce")
    return out


def _mean(vals: list[float]) -> float:
    vals = [v for v in vals if pd.notna(v)]
    return float(np.mean(vals)) if vals else float("nan")


def _rec_is_yes(value: float, scale_max: float) -> int:
    """1 if a recognition slider sits in the upper ("Yes") half of its range.

    Robust to the two scales seen in the data: the revised design declares the
    recognition sliders on 0..100 (neutral default 50), while an early pilot ran
    them on 0..1. Threshold at the midpoint of whichever range applies.
    """
    return int(value >= scale_max / 2.0)


def questionnaire_metrics(block_rows: pd.DataFrame) -> dict[str, float]:
    """Compute the revised per-block questionnaire metrics for one block."""
    s = _scores(block_rows)

    # --- H1: subjective transparency (3 items, one reverse-keyed) ---
    keep_track_key = next((k for k in s if _KEEP_TRACK_RE.match(k)), None)
    keep_track = s.get(keep_track_key) if keep_track_key else float("nan")
    # Reverse-score the "hard to keep track" item onto the transparency direction.
    keep_track_fwd = (_TRANSPARENCY_MIN + _TRANSPARENCY_MAX - keep_track
                      if pd.notna(keep_track) else float("nan"))
    subj_transparency = _mean([s.get(_WHAT_KEY), keep_track_fwd, s.get(_INFO_KEY)])

    # --- Workload mechanism check (single item) ---
    wl = s.get(_WORKLOAD_KEY)
    workload = float(wl) if pd.notna(wl) else float("nan")

    # --- H2: mental-model accuracy vs ground truth ---
    # Every probe item is a yes/no slider about one active gauge, scored
    # correct/incorrect against the block's roles. Three question types -- `act`,
    # `miss`, `close` -- are tallied separately and pooled into the composite.
    probe = {k: v for k, v in s.items() if _PROBE_RE.match(k) and pd.notna(v)}
    scale_max = max(probe.values(), default=0.0)
    scale_max = 1.0 if scale_max <= 1.0 else 100.0  # 0..1 pilot vs 0..100 revised

    hits = {"act": [0, 0], "miss": [0, 0], "close": [0, 0]}  # qtype -> [n_correct, n_total]
    for key, val in probe.items():
        blk, qtype, gtype, num = _PROBE_RE.match(key).groups()
        gauge = f"{'scales' if gtype == 'scale' else 'lights'}-{num}"
        truth = _probe_truth(qtype, blk, gauge)
        hits[qtype][1] += 1
        hits[qtype][0] += int(_rec_is_yes(val, scale_max) == truth)

    def _acc(pair: list[int]) -> float:
        return pair[0] / pair[1] if pair[1] else float("nan")

    mm_act_accuracy = _acc(hits["act"])      # "did the aid act on X?"
    mm_miss_accuracy = _acc(hits["miss"])    # "did the aid fail to act on Y?"
    mm_close_accuracy = _acc(hits["close"])  # "was there a close call on Z?"

    # Composite explicability: proportion of ALL probe items answered correctly.
    # Naturally in [0, 1], equal-weighted, every sub-score block-specific -- no
    # per-item normalisation needed.
    tot_correct = sum(p[0] for p in hits.values())
    tot_items = sum(p[1] for p in hits.values())
    mm_explicability = (tot_correct / tot_items) if tot_items else float("nan")

    return {
        "subj_transparency": subj_transparency,
        "workload": workload,
        "mm_act_accuracy": mm_act_accuracy,
        "mm_miss_accuracy": mm_miss_accuracy,
        "mm_close_accuracy": mm_close_accuracy,
        "mm_explicability": mm_explicability,
    }
