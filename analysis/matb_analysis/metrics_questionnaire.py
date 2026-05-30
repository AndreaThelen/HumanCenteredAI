"""Per-block questionnaire metrics for hypotheses H1 (subjective transparency &
trust) and H2 (objective mental-model accuracy / explicability).

Responses are logged by the genericscales plugin as
``performance | genericscales | <item key> | <value>`` when each questionnaire
screen is dismissed. Yes/No mental-model items are continuous sliders (0..1), so
they are thresholded at 0.5. The mental-model answers are scored against the
study ground truth (which gauges the aid acted on, 2 misses/block, ~78%
reliability).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .study_design import (GAUGE_BY_BLOCK, N_MISSES_PER_BLOCK, TRUE_RELIABILITY_PCT)

_TRUST_KEYS = ["Trust_01_reliable", "Trust_02_expected", "Trust_03_confident", "Trust_04_trust"]
_SET_RE = re.compile(r"^MM_([ABC])_set_(scale|light)(\d)$")
_SKIP_RE = re.compile(r"^MM_[ABC]_q_skipped$")
_REL_RE = re.compile(r"^MM_[ABC]_q_reliability$")

# Worst-case errors (truth at one end of the slider range) used to normalise the
# composite explicability score to [0, 1].
_MAX_SKIP_ERR = 9 - N_MISSES_PER_BLOCK            # truth 2 on a 0..9 slider -> 7
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


def questionnaire_metrics(block_rows: pd.DataFrame) -> dict[str, float]:
    """Compute H1/H2 questionnaire metrics for one block's rows."""
    s = _scores(block_rows)

    # --- H1: subjective transparency (info-volume item kept separate) ---
    subj_transparency = _mean([s.get("Subjective_transparency_what"),
                               s.get("Subjective_attention_guidance")])
    vol = s.get("Subjective_information_volume")
    info_volume = float(vol) if pd.notna(vol) else float("nan")
    info_volume_miscal = float(abs(vol - 4)) if pd.notna(vol) else float("nan")

    # --- H1: subjective trust ---
    subj_trust = _mean([s.get(k) for k in _TRUST_KEYS])

    # --- H2: mental-model accuracy vs ground truth ---
    n_correct = n_total = 0
    for key, val in s.items():
        m = _SET_RE.match(key)
        if not m or pd.isna(val):
            continue
        block, gtype, num = m.group(1), m.group(2), m.group(3)
        gauge = f"{'scales' if gtype == 'scale' else 'lights'}-{num}"
        truth = 1 if gauge in GAUGE_BY_BLOCK.get(block, ()) else 0
        answer = 1 if val >= 0.5 else 0
        n_total += 1
        n_correct += int(answer == truth)
    mm_set_accuracy = (n_correct / n_total) if n_total else float("nan")

    skip_key = next((k for k in s if _SKIP_RE.match(k)), None)
    mm_skipped_error = (abs(s[skip_key] - N_MISSES_PER_BLOCK)
                        if skip_key and pd.notna(s[skip_key]) else float("nan"))
    rel_key = next((k for k in s if _REL_RE.match(k)), None)
    mm_reliability_error = (abs(s[rel_key] - TRUE_RELIABILITY_PCT)
                            if rel_key and pd.notna(s[rel_key]) else float("nan"))

    # Composite explicability: mean of three [0,1] accuracy sub-scores.
    parts = []
    if pd.notna(mm_set_accuracy):
        parts.append(mm_set_accuracy)
    if pd.notna(mm_skipped_error):
        parts.append(1 - min(mm_skipped_error, _MAX_SKIP_ERR) / _MAX_SKIP_ERR)
    if pd.notna(mm_reliability_error):
        parts.append(1 - min(mm_reliability_error, _MAX_REL_ERR) / _MAX_REL_ERR)
    mm_explicability = float(np.mean(parts)) if parts else float("nan")

    return {
        "subj_transparency": subj_transparency,
        "info_volume": info_volume,
        "info_volume_miscal": info_volume_miscal,
        "subj_trust": subj_trust,
        "mm_set_accuracy": mm_set_accuracy,
        "mm_skipped_error": mm_skipped_error,
        "mm_reliability_error": mm_reliability_error,
        "mm_explicability": mm_explicability,
    }
