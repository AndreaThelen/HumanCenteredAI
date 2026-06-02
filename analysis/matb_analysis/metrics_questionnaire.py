"""Per-block questionnaire metrics for the revised (wording-only) design.

Two per-block constructs from the lean battery (per-block trust and the full
NASA-TLX were dropped in the revised design):

* **H1 -- subjective transparency.** Three agreement items (1..7), one
  reverse-keyed, averaged into a single transparency score (higher = feels more
  transparent).
* **H2 -- objective explicability.** The five-slider mental-model probe (3
  calibration + 2 recognition), scored against the block's ground truth.
* **Workload mechanism check.** A single mental-effort item (1..7).

Trust is measured only once, in the end-of-session preference debrief
(``build_debrief_table`` in ``aggregate.py``), not per block.

Responses are logged by the genericscales plugin as
``performance | genericscales | <slider title> | <value>`` when each
questionnaire screen is dismissed, where ``<value>`` is in the slider's own
declared ``min..max`` units. The mental-model answers are scored against the
study ground truth (which indicators the aid acted on, 2 misses/block,
2 near-misses/block, ~78% reliability).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .study_design import (GAUGE_BY_BLOCK, N_EVENTS_PER_BLOCK, N_MISSES_PER_BLOCK,
                           N_NEARMISS_PER_BLOCK, TRUE_RELIABILITY_PCT)

# --- slider keys (match the revised questionnaire .txt files) ---
_WHAT_KEY = "Subjective_transparency_what"
_INFO_KEY = "Subjective_information_volume"
# Reverse-keyed item ("It was hard to keep track ..."). The logged title may or
# may not carry the explicit ``_REV`` suffix, so match the stem either way.
_KEEP_TRACK_RE = re.compile(r"^Subjective_keep_track(_REV)?$")
_WORKLOAD_KEY = "Workload_overall"

_TRANSPARENCY_MIN, _TRANSPARENCY_MAX = 1, 7  # 1..7 agreement scale

# Mental-model probe sliders.
_MISSES_RE = re.compile(r"^MM_[ABC]_q_misses$")
_CLOSECALLS_RE = re.compile(r"^MM_[ABC]_q_closecalls$")
_REL_RE = re.compile(r"^MM_[ABC]_q_reliability$")
_REC_RE = re.compile(r"^MM_([ABC])_rec_(scale|light)(\d)$")

# Worst-case errors (truth at one end of the slider) used to normalise the
# composite explicability score to [0, 1].
_MAX_MISS_ERR = N_EVENTS_PER_BLOCK - N_MISSES_PER_BLOCK            # truth 2 on 0..9 -> 7
_MAX_NEARMISS_ERR = N_EVENTS_PER_BLOCK - N_NEARMISS_PER_BLOCK      # truth 2 on 0..9 -> 7
_MAX_REL_ERR = max(TRUE_RELIABILITY_PCT, 100 - TRUE_RELIABILITY_PCT)  # ~77.8


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
    # Calibration sliders (signed truth, scored as absolute error).
    miss_key = next((k for k in s if _MISSES_RE.match(k)), None)
    mm_misses_error = (abs(s[miss_key] - N_MISSES_PER_BLOCK)
                       if miss_key and pd.notna(s[miss_key]) else float("nan"))
    cc_key = next((k for k in s if _CLOSECALLS_RE.match(k)), None)
    mm_closecalls_error = (abs(s[cc_key] - N_NEARMISS_PER_BLOCK)
                           if cc_key and pd.notna(s[cc_key]) else float("nan"))
    rel_key = next((k for k in s if _REL_RE.match(k)), None)
    mm_reliability_error = (abs(s[rel_key] - TRUE_RELIABILITY_PCT)
                            if rel_key and pd.notna(s[rel_key]) else float("nan"))

    # Recognition items: "did the aid act on indicator X?". Truth = indicator is
    # in this block's set (the aid acts on, and only on, that block's two gauges).
    rec_vals = {k: v for k, v in s.items() if _REC_RE.match(k) and pd.notna(v)}
    rec_scale_max = max(rec_vals.values(), default=0.0)
    rec_scale_max = 1.0 if rec_scale_max <= 1.0 else 100.0  # 0..1 pilot vs 0..100
    n_correct = n_total = 0
    for key, val in rec_vals.items():
        m = _REC_RE.match(key)
        block, gtype, num = m.group(1), m.group(2), m.group(3)
        gauge = f"{'scales' if gtype == 'scale' else 'lights'}-{num}"
        truth = 1 if gauge in GAUGE_BY_BLOCK.get(block, ()) else 0
        n_total += 1
        n_correct += int(_rec_is_yes(val, rec_scale_max) == truth)
    mm_rec_accuracy = (n_correct / n_total) if n_total else float("nan")

    # Composite explicability: mean of the available [0,1] accuracy sub-scores
    # (calibration errors normalised to accuracy; recognition proportion correct).
    parts: list[float] = []
    if pd.notna(mm_misses_error):
        parts.append(1 - min(mm_misses_error, _MAX_MISS_ERR) / _MAX_MISS_ERR)
    if pd.notna(mm_closecalls_error):
        parts.append(1 - min(mm_closecalls_error, _MAX_NEARMISS_ERR) / _MAX_NEARMISS_ERR)
    if pd.notna(mm_reliability_error):
        parts.append(1 - min(mm_reliability_error, _MAX_REL_ERR) / _MAX_REL_ERR)
    if pd.notna(mm_rec_accuracy):
        parts.append(mm_rec_accuracy)
    mm_explicability = float(np.mean(parts)) if parts else float("nan")

    return {
        "subj_transparency": subj_transparency,
        "workload": workload,
        "mm_misses_error": mm_misses_error,
        "mm_closecalls_error": mm_closecalls_error,
        "mm_reliability_error": mm_reliability_error,
        "mm_rec_accuracy": mm_rec_accuracy,
        "mm_explicability": mm_explicability,
    }
