"""Per-block communications metrics.

Following Cegarra et al. (2020), the communications task is scored as response
accuracy and response time within a signal-detection framing. Correctly-ignored
distractors are not logged, so accuracy is computed over signal trials only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

_SDT_ERROR = {"BAD_RADIO", "BAD_FREQ", "BAD_RADIO_FREQ"}


def _events_table(block_rows: pd.DataFrame) -> pd.DataFrame:
    """Pivot comms performance rows into one row per event (indexed by scenario_time)."""
    sel = block_rows[(block_rows["module"] == "communications")
                     & (block_rows["type"] == "performance")]
    if sel.empty:
        return pd.DataFrame()
    table = sel.pivot_table(
        index="scenario_time", columns="address", values="value", aggfunc="first"
    )
    return table


def _num(series: pd.Series) -> np.ndarray:
    vals = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    return vals


def comms_metrics(block_rows: pd.DataFrame) -> dict[str, float]:
    """Compute communications metrics for one block's rows."""
    empty = {
        "n_events": 0, "n_signal": 0, "n_hit": 0, "n_miss": 0, "n_fa": 0,
        "n_bad_radio": 0, "n_bad_freq": 0, "n_bad_radio_freq": 0,
        "accuracy": float("nan"), "miss_rate": float("nan"),
        "fa_count": 0, "mean_rt_hit": float("nan"),
        "mean_abs_freq_dev": float("nan"),
    }
    table = _events_table(block_rows)
    if table.empty or "sdt_value" not in table.columns:
        return empty

    sdt = table["sdt_value"].astype(str)
    n_hit = int((sdt == "HIT").sum())
    n_miss = int((sdt == "MISS").sum())
    n_fa = int((sdt == "FA").sum())
    n_bad_radio = int((sdt == "BAD_RADIO").sum())
    n_bad_freq = int((sdt == "BAD_FREQ").sum())
    n_bad_radio_freq = int((sdt == "BAD_RADIO_FREQ").sum())

    n_signal = int(sdt.isin({"HIT", "MISS"} | _SDT_ERROR).sum())  # everything but FA
    accuracy = n_hit / n_signal if n_signal else float("nan")
    miss_rate = n_miss / n_signal if n_signal else float("nan")

    rt_all = _num(table["response_time"]) if "response_time" in table else np.array([])
    rt_hit = rt_all[(sdt == "HIT").to_numpy()] if rt_all.size else np.array([])
    rt_hit = rt_hit[np.isfinite(rt_hit)]
    mean_rt_hit = float(np.mean(rt_hit)) if rt_hit.size else float("nan")

    dev_all = _num(table["response_deviation"]) if "response_deviation" in table else np.array([])
    dev_resp = dev_all[np.isfinite(dev_all)]
    mean_abs_freq_dev = float(np.mean(np.abs(dev_resp))) if dev_resp.size else float("nan")

    return {
        "n_events": int(len(table)),
        "n_signal": n_signal,
        "n_hit": n_hit,
        "n_miss": n_miss,
        "n_fa": n_fa,
        "n_bad_radio": n_bad_radio,
        "n_bad_freq": n_bad_freq,
        "n_bad_radio_freq": n_bad_radio_freq,
        "accuracy": accuracy,
        "miss_rate": miss_rate,
        "fa_count": n_fa,
        "mean_rt_hit": mean_rt_hit,
        "mean_abs_freq_dev": mean_abs_freq_dev,
    }
