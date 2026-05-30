"""Per-block resource-management metrics.

Definitions follow Cegarra et al. (2020) and Santiago-Espada et al. (2011):
RMS error of the two target tanks from the 2500 target, and the proportion of
time the tank level stays within tolerance.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _values(df: pd.DataFrame, address: str) -> np.ndarray:
    """Numeric values for a given resman performance address (non-finite dropped)."""
    sel = df[(df["module"] == "resman") & (df["type"] == "performance")
             & (df["address"] == address)]
    vals = pd.to_numeric(sel["value"], errors="coerce").to_numpy(dtype=float)
    return vals[np.isfinite(vals)]


def _rmsd(vals: np.ndarray) -> float:
    return float(np.sqrt(np.mean(vals ** 2))) if vals.size else float("nan")


def _mad(vals: np.ndarray) -> float:
    return float(np.mean(np.abs(vals))) if vals.size else float("nan")


def _pct_in_tol(vals: np.ndarray) -> float:
    # keep only 0/1 entries; percentage of sampled rows in tolerance
    binary = vals[(vals == 0) | (vals == 1)]
    return float(np.mean(binary) * 100.0) if binary.size else float("nan")


def _nanmean(a: float, b: float) -> float:
    pair = [x for x in (a, b) if not np.isnan(x)]
    return float(np.mean(pair)) if pair else float("nan")


def resman_metrics(block_rows: pd.DataFrame) -> dict[str, float]:
    """Compute resource-management metrics for one block's rows."""
    dev_a, dev_b = _values(block_rows, "a_deviation"), _values(block_rows, "b_deviation")
    tol_a, tol_b = _values(block_rows, "a_in_tolerance"), _values(block_rows, "b_in_tolerance")
    exc = np.concatenate([
        _values(block_rows, "a_response_time"),
        _values(block_rows, "b_response_time"),
    ]) if block_rows.size else np.array([])

    rmsd_a, rmsd_b = _rmsd(dev_a), _rmsd(dev_b)
    pct_a, pct_b = _pct_in_tol(tol_a), _pct_in_tol(tol_b)

    return {
        "rmsd_a": rmsd_a,
        "rmsd_b": rmsd_b,
        "rmsd_mean": _nanmean(rmsd_a, rmsd_b),
        "mad_a": _mad(dev_a),
        "mad_b": _mad(dev_b),
        "pct_in_tolerance_a": pct_a,
        "pct_in_tolerance_b": pct_b,
        "pct_in_tolerance_mean": _nanmean(pct_a, pct_b),
        "n_excursions": int(exc.size),
        "mean_excursion_sec": float(np.mean(exc) / 1000.0) if exc.size else float("nan"),
    }
