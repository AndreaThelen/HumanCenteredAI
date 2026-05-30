"""Per-block system-monitoring metrics for hypothesis H3.

The sysmon plugin logs ``signal_detection`` (HIT/MISS/FA) but records HIT for
*both* the automation aid's auto-solve and a user's manual response. We therefore
use the ``automaticsolver`` state in effect at each event to separate:

* **aid-skipped events** (solver off) -- H3A detection of automation misses:
  HIT = the user caught it, MISS = the user missed it;
* **aid-handled events** (solver on) -- H3B overwrites: a HIT with
  ``response_time`` below ``automaticsolverdelay`` means the user pressed the key
  before the aid acted (a pre-emptive overwrite); ``response_time`` at the delay
  is the aid solving it on its own.

False alarms (FA rows: a key press with no active target) are reported alongside.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

_TRUE_VALUES = {"1", "True", "true"}


def _solver_timeline(block_rows: pd.DataFrame):
    """Sorted (times, on/off) of automaticsolver changes within the block."""
    sel = block_rows[(block_rows["module"] == "sysmon")
                     & (block_rows["address"] == "automaticsolver")].sort_values("scenario_time")
    times = sel["scenario_time"].to_numpy(dtype=float)
    states = [str(v) in _TRUE_VALUES for v in sel["value"]]
    return times, states


def _events(block_rows: pd.DataFrame) -> pd.DataFrame:
    """One row per sysmon performance event (indexed by scenario_time)."""
    sel = block_rows[(block_rows["module"] == "sysmon")
                     & (block_rows["type"] == "performance")]
    if sel.empty:
        return pd.DataFrame()
    return sel.pivot_table(index="scenario_time", columns="address", values="value",
                           aggfunc="first")


def sysmon_metrics(block_rows: pd.DataFrame, automaticsolverdelay: float = 1000.0) -> dict:
    """Compute H3 system-monitoring metrics for one block's rows."""
    empty = {
        "n_aid_miss_events": 0, "n_detected": 0, "detection_rate": float("nan"),
        "mean_detect_rt": float("nan"),
        "n_aid_handled_events": 0, "n_overwrite": 0, "overwrite_rate": float("nan"),
        "n_false_alarms": 0,
    }
    table = _events(block_rows)
    if table.empty or "signal_detection" not in table.columns:
        return empty

    times, states = _solver_timeline(block_rows)

    def solver_on_at(t: float) -> bool:
        if times.size == 0:
            return True  # aid is on by default at block start
        idx = int(np.searchsorted(times, t, side="right")) - 1
        return states[idx] if idx >= 0 else True

    n_miss_events = n_detected = n_handled = n_overwrite = n_fa = 0
    detect_rts: list[float] = []

    rt_series = table["response_time"] if "response_time" in table else pd.Series(dtype=str)
    for t, sdt in table["signal_detection"].astype(str).items():
        if sdt == "FA":
            n_fa += 1
            continue
        rt = pd.to_numeric(rt_series.get(t), errors="coerce") if "response_time" in table else float("nan")
        if solver_on_at(float(t)):                       # aid-handled event (H3B)
            n_handled += 1
            if sdt == "HIT" and np.isfinite(rt) and rt < automaticsolverdelay:
                n_overwrite += 1
        else:                                            # aid-skipped event (H3A)
            n_miss_events += 1
            if sdt == "HIT":
                n_detected += 1
                if np.isfinite(rt):
                    detect_rts.append(float(rt))

    return {
        "n_aid_miss_events": n_miss_events,
        "n_detected": n_detected,
        "detection_rate": (n_detected / n_miss_events) if n_miss_events else float("nan"),
        "mean_detect_rt": float(np.mean(detect_rts)) if detect_rts else float("nan"),
        "n_aid_handled_events": n_handled,
        "n_overwrite": n_overwrite,
        "overwrite_rate": (n_overwrite / n_handled) if n_handled else float("nan"),
        "n_false_alarms": n_fa,
    }
