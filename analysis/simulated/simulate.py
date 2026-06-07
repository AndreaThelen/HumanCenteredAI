"""Generate simulated OpenMATB study sessions from a real example log.

This is a *data generator for developing and validating the analysis code* -- it
does not run OpenMATB. It reads one real session CSV (the P03 pilot) as a
structural **template** and re-emits it once per participant (P01..P20), so the
``matb_analysis`` pipeline can be exercised on a full counterbalanced cohort with
**known ground truth**.

Strategy ("randomly modified versions of the example", at full fidelity):

* The template's three block segments are keyed by their **block letter**
  (A/B/C). A block's content -- gauges, ``-failure`` events, the
  ``automaticsolver`` skip pattern, the ``mental_model_block_X`` probe and its
  ``rec_*`` sliders -- depends only on the letter. The **form** (F1/F2/F3) only
  changes the ``briefing_F#`` and ``panels/F#/...`` path tokens (the study is
  content-constant). So a letter-segment can be retargeted to any form by string
  substitution.
* For each participant we place the three letter-segments into that participant's
  Latin-square order (``study_design.PARTICIPANT_ORDERS``), time-shifted to sit
  back-to-back, retarget their form tokens, and **re-sample only the
  analysis-relevant outcome values** (the ``performance`` and questionnaire rows)
  from an effects model. All other rows -- the bulk 200 ms sysmon states, AOIs,
  seed values, parameters -- are copied verbatim (with shifted timestamps) for
  realistic size and shape.
* The effects model embeds the study hypotheses (toggle with ``--no-effects``):
  F1 = highest subjective transparency + workload + overwrites; F2/F3 = better
  mental-model accuracy, miss detection, and non-aided (comms/resman) performance.
  Effect sizes live in the ``EFFECTS`` table at the top of this file.

Limitation: the low-level ``state``/``input`` rows keep the template's behaviour
and are *not* re-derived to match each re-sampled outcome. The metrics read the
``performance`` rows, so the output is analysis-faithful but not a
physically-consistent replay.

CLI::

    python -m matb_analysis.simulate --n 20 --self-check
"""
from __future__ import annotations

import argparse
import csv
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..matb_analysis.study_design import (HANDLED_GAUGE_BY_BLOCK, MISSED_GAUGE_BY_BLOCK,
                           PARTICIPANT_ORDERS, PROBE_TARGETS)

COLUMNS = ["logtime", "scenario_time", "type", "module", "address", "value"]

_THIS_DIR = Path(__file__).resolve().parent
_ANALYSIS_ROOT = _THIS_DIR.parent
DEFAULT_TEMPLATE = _ANALYSIS_ROOT / "session_logs" / "26_260602_190745.csv"
DEFAULT_OUT = _ANALYSIS_ROOT / "session_logs" / "simulated"

_TRUE_VALUES = {"1", "True", "true"}

# ---------------------------------------------------------------------------
# Effects model. Each construct gives a baseline plus a per-form delta; with
# ``--no-effects`` only the baseline is used (all forms identical). ``sd`` is the
# within-form noise; ``p_sd`` the per-participant random-effect SD (shared across
# that participant's blocks for the construct, for realistic within-subject corr).
# Scales: transparency/workload 1..7; mental-model probe act/miss/close yes/no
# sliders 0..100, threshold 50 (scored against each gauge's role this block).
# ---------------------------------------------------------------------------
EFFECTS: dict[str, dict] = {
    # H1: subjective transparency feeling (higher under verbose F1).
    "transparency": {"base": 4.7, "form": {"F1": 0.9, "F2": -0.2, "F3": 0.0},
                     "sd": 0.6, "p_sd": 0.7},
    # Mechanism: workload (higher under verbose F1).
    "workload": {"base": 4.5, "form": {"F1": 1.0, "F2": -0.2, "F3": -0.1},
                 "sd": 0.6, "p_sd": 0.7},
    # H2 mental-model probe: probability of answering each yes/no probe item on
    # the correct side (better under the contrastive forms). Drives all three
    # probe types (`act`, `miss`, `close`).
    "mm_probe_p_correct": {"base": 0.74, "form": {"F1": -0.15, "F2": 0.09, "F3": 0.12},
                           "p_sd": 0.10},
    # H3a: probability the operator detects an aid-skipped miss.
    "detect_p": {"base": 0.72, "form": {"F1": -0.18, "F2": 0.10, "F3": 0.13},
                 "p_sd": 0.12},
    # H3a: reaction time (ms) on detected misses (faster under contrastive forms).
    "detect_rt": {"base": 3200.0, "form": {"F1": 600.0, "F2": -500.0, "F3": -600.0},
                  "sd": 700.0, "p_sd": 600.0},
    # H3b: probability of a pre-emptive overwrite of a correct aid action.
    "overwrite_p": {"base": 0.08, "form": {"F1": 0.06, "F2": -0.04, "F3": -0.05},
                    "p_sd": 0.04},
    # H4: communications response accuracy (HIT proportion on signal trials).
    "comms_p_hit": {"base": 0.76, "form": {"F1": -0.10, "F2": 0.07, "F3": 0.08},
                    "p_sd": 0.10},
    # H4: communications RT on hits (ms).
    "comms_rt": {"base": 7500.0, "form": {"F1": 900.0, "F2": -700.0, "F3": -800.0},
                 "sd": 2500.0, "p_sd": 1500.0},
    # H4: resman tracking error SD (tank deviation from target; smaller = better).
    "resman_dev_sd": {"base": 330.0, "form": {"F1": 90.0, "F2": -40.0, "F3": -50.0},
                      "p_sd": 60.0},
}

_RESMAN_TOL = 500.0  # |deviation| <= tol counts as in-tolerance


# ---------------------------------------------------------------------------
# Template parsing.
# ---------------------------------------------------------------------------
_BRIEF_RE = re.compile(r"briefing_(F\d)\.txt")
_PANEL_RE = re.compile(r"panels/(F\d)/block_([A-C])_")
_MENTAL_RE = re.compile(r"mental_model_block_([A-C])")


@dataclass
class Segment:
    """One block segment of the template, keyed by block letter."""
    letter: str
    src_form: str
    rows: list[dict]
    t_min: float
    t_max: float

    @property
    def duration(self) -> float:
        return self.t_max - self.t_min


@dataclass
class Template:
    header: list[dict]                       # everything up to the first F-briefing
    segments: dict[str, Segment]             # letter -> Segment
    footer: list[dict]                       # end_of_session + preference_debrief
    columns: list[str] = field(default_factory=lambda: list(COLUMNS))


def _to_float(s: str) -> float:
    try:
        return float(s)
    except (TypeError, ValueError):
        return float("nan")


def load_template(path: str | Path) -> Template:
    """Read the example CSV into header / per-letter segments / footer."""
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [dict(r) for r in reader]

    def is_briefing(r: dict) -> str | None:
        if (r["type"] == "event" and r["module"] == "instructions"
                and r["address"] == "filename"):
            m = _BRIEF_RE.search(str(r["value"]))
            return m.group(1) if m else None
        return None

    brief_idx = [i for i, r in enumerate(rows) if is_briefing(r)]
    if len(brief_idx) < 3:
        raise ValueError(f"template has {len(brief_idx)} F-briefings, expected 3")
    footer_idx = next((i for i, r in enumerate(rows)
                       if "end_of_session" in str(r["value"])), len(rows))

    header = rows[: brief_idx[0]]
    bounds = brief_idx[:3] + [footer_idx]
    segments: dict[str, Segment] = {}
    for k in range(3):
        seg_rows = rows[bounds[k]: bounds[k + 1]]
        src_form = is_briefing(seg_rows[0])
        letter = _segment_letter(seg_rows)
        times = [_to_float(r["scenario_time"]) for r in seg_rows]
        times = [t for t in times if t == t]  # drop NaN
        segments[letter] = Segment(letter, src_form, seg_rows, min(times), max(times))
    footer = rows[footer_idx:]
    return Template(header=header, segments=segments, footer=footer)


def _segment_letter(seg_rows: list[dict]) -> str:
    for r in seg_rows:
        m = _PANEL_RE.search(str(r["value"]))
        if m:
            return m.group(2)
    for r in seg_rows:
        m = _MENTAL_RE.search(str(r["value"]))
        if m:
            return m.group(1)
    raise ValueError("could not determine block letter for a template segment")


# ---------------------------------------------------------------------------
# Effects sampler.
# ---------------------------------------------------------------------------
class OutcomeModel:
    """Draws per-block outcome values, with optional embedded form effects."""

    def __init__(self, seed: int, embed_effects: bool = True):
        self.embed = embed_effects
        self._seed = seed

    def block_rng(self, pid: str, form: str, letter: str) -> random.Random:
        return random.Random(f"{self._seed}|{pid}|{form}|{letter}")

    def participant_rng(self, pid: str) -> random.Random:
        return random.Random(f"{self._seed}|participant|{pid}")

    # -- effect helpers --
    def _delta(self, construct: str, form: str) -> float:
        if not self.embed:
            return 0.0
        return EFFECTS[construct].get("form", {}).get(form, 0.0)

    def _p_offset(self, construct: str, prng: random.Random) -> float:
        sd = EFFECTS[construct].get("p_sd", 0.0)
        return prng.gauss(0.0, sd) if (self.embed and sd) else 0.0


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _fmt(x: float, nd: int = 6) -> str:
    return f"{x:.{nd}f}"


# ---------------------------------------------------------------------------
# Value rewriting per placed segment.
# ---------------------------------------------------------------------------
def _retarget_form(rows: list[dict], src_form: str, dst_form: str) -> None:
    """In-place: rewrite briefing/panel path tokens from src_form to dst_form."""
    if src_form == dst_form:
        return
    for r in rows:
        v = str(r["value"])
        if "F" in v and ("panels/" in v or "briefing_" in v):
            v = v.replace(f"panels/{src_form}/", f"panels/{dst_form}/")
            v = v.replace(f"briefing_{src_form}", f"briefing_{dst_form}")
            r["value"] = v


def _shift_time(rows: list[dict], d_scenario: float, d_logtime: float) -> None:
    for r in rows:
        st = _to_float(r["scenario_time"])
        if st == st:
            r["scenario_time"] = _fmt(st + d_scenario)
        lt = _to_float(r["logtime"])
        if lt == lt:
            r["logtime"] = _fmt(lt + d_logtime)


def _groups(rows: list[dict], module: str):
    """Yield lists of consecutive performance rows sharing a scenario_time."""
    buf: list[dict] = []
    key = None
    for r in rows:
        if r["module"] == module and r["type"] == "performance":
            if buf and r["scenario_time"] != key:
                yield buf
                buf = []
            buf.append(r)
            key = r["scenario_time"]
        else:
            if buf:
                yield buf
                buf = []
                key = None
    if buf:
        yield buf


def _solver_state_by_time(rows: list[dict]) -> list[tuple[float, bool]]:
    out = []
    for r in rows:
        if r["module"] == "sysmon" and r["address"] == "automaticsolver":
            out.append((_to_float(r["scenario_time"]), str(r["value"]) in _TRUE_VALUES))
    return out


def _resample_segment(seg_rows: list[dict], form: str, letter: str,
                      pid: str, model: OutcomeModel,
                      solver_delay: float = 1000.0) -> None:
    """Rewrite the analysis-relevant performance/questionnaire values in place."""
    brng = model.block_rng(pid, form, letter)
    prng = model.participant_rng(pid)
    solver_tl = _solver_state_by_time(seg_rows)

    def solver_on_at(t: float) -> bool:
        on = True
        for st, state in solver_tl:
            if st <= t:
                on = state
            else:
                break
        return on

    _resample_sysmon(seg_rows, form, pid, model, brng, prng, solver_on_at, solver_delay)
    _resample_genericscales(seg_rows, form, letter, model, brng, prng)
    _rewrite_mm_probe(seg_rows, letter, form, model, brng, prng)
    _resample_comms(seg_rows, form, model, brng, prng)
    _resample_resman(seg_rows, form, model, brng, prng)


def _resample_sysmon(seg_rows, form, pid, model, brng, prng, solver_on_at, solver_delay):
    detect_off = model._p_offset("detect_p", prng)
    over_off = model._p_offset("overwrite_p", prng)
    rt_off = model._p_offset("detect_rt", prng)
    for grp in _groups(seg_rows, "sysmon"):
        t = _to_float(grp[0]["scenario_time"])
        sdt_row = next((r for r in grp if r["address"] == "signal_detection"), None)
        rt_row = next((r for r in grp if r["address"] == "response_time"), None)
        if sdt_row is None:
            continue
        if str(sdt_row["value"]) == "FA":   # keep false alarms as-is
            continue
        if solver_on_at(t):                 # aid-handled event (H3B overwrites)
            p = _clip(EFFECTS["overwrite_p"]["base"]
                      + model._delta("overwrite_p", form) + over_off, 0.0, 1.0)
            if brng.random() < p:
                sdt_row["value"] = "HIT"
                if rt_row is not None:
                    rt_row["value"] = _fmt(brng.uniform(300, solver_delay - 50), 0)
            else:
                sdt_row["value"] = "HIT"    # the aid solves it
                if rt_row is not None:
                    rt_row["value"] = _fmt(solver_delay, 0)
        else:                               # aid-skipped event (H3A detection)
            p = _clip(EFFECTS["detect_p"]["base"]
                      + model._delta("detect_p", form) + detect_off, 0.02, 0.98)
            if brng.random() < p:
                sdt_row["value"] = "HIT"
                rt = EFFECTS["detect_rt"]["base"] + model._delta("detect_rt", form) \
                    + rt_off + brng.gauss(0, EFFECTS["detect_rt"]["sd"])
                if rt_row is not None:
                    rt_row["value"] = _fmt(_clip(rt, 600, 9500), 0)
            else:
                sdt_row["value"] = "MISS"
                if rt_row is not None:
                    rt_row["value"] = "nan"


def _gauge_token(gauge: str) -> str:
    """'scales-1' -> 'scale1', 'lights-2' -> 'light2' (the slider-title form)."""
    kind, num = gauge.split("-")
    return f"{'scale' if kind == 'scales' else 'light'}{num}"


def _probe_battery(blk: str) -> list[tuple[str, str, bool]]:
    """The 3-question probe for a block: (qtype, gauge, truth_yes).

    Mirrors the questionnaire generated by ``_regenerate.PROBE_TARGETS``: one
    `act`, one `miss`, one `close` item, each naming the handled or missed gauge
    per the counterbalanced role table.
    """
    out: list[tuple[str, str, bool]] = []
    for qtype, role in PROBE_TARGETS[blk]:
        gauge = (HANDLED_GAUGE_BY_BLOCK[blk] if role == "handled"
                 else MISSED_GAUGE_BY_BLOCK[blk])
        truth_yes = (role == "handled") if qtype in ("act", "close") else (role == "missed")
        out.append((qtype, gauge, truth_yes))
    return out


def _rewrite_mm_probe(seg_rows, blk, form, model, brng, prng):
    """Remap the template's MM_* probe rows to the revised localised battery."""
    if blk not in PROBE_TARGETS:
        return
    off = model._p_offset("mm_probe_p_correct", prng)
    p = _clip(EFFECTS["mm_probe_p_correct"]["base"]
              + model._delta("mm_probe_p_correct", form) + off, 0.02, 0.98)
    mm_rows = [r for r in seg_rows
               if r["module"] == "genericscales" and r["type"] == "performance"
               and str(r["address"]).startswith(f"MM_{blk}_")]
    battery = _probe_battery(blk)
    for row, (qtype, gauge, truth_yes) in zip(mm_rows, battery):
        row["address"] = f"MM_{blk}_{qtype}_{_gauge_token(gauge)}"
        answer_yes = truth_yes if (brng.random() < p) else (not truth_yes)
        row["value"] = _fmt(brng.uniform(55, 100) if answer_yes else brng.uniform(0, 45))
    # Neutralise any leftover template MM rows (none expected for the 5-row probe).
    for i, row in enumerate(mm_rows[len(battery):]):
        row["address"] = f"MM_{blk}_unused_{i}"
        row["value"] = _fmt(50.0)


def _resample_genericscales(seg_rows, form, letter, model, brng, prng):
    t_off = model._p_offset("transparency", prng)
    w_off = model._p_offset("workload", prng)

    def set_addr(row, value):
        row["value"] = value

    for r in seg_rows:
        if not (r["module"] == "genericscales" and r["type"] == "performance"):
            continue
        addr = str(r["address"])

        # --- H1 transparency (1..7) ---
        if addr == "Subjective_transparency_what" or addr == "Subjective_information_volume":
            latent = EFFECTS["transparency"]["base"] + model._delta("transparency", form) \
                + t_off + brng.gauss(0, EFFECTS["transparency"]["sd"])
            set_addr(r, _fmt(_clip(latent, 1, 7)))
        elif addr.startswith("Subjective_keep_track"):
            # Reverse-keyed: logged as "hard to keep track" -> high transparency = low value.
            latent = EFFECTS["transparency"]["base"] + model._delta("transparency", form) \
                + t_off + brng.gauss(0, EFFECTS["transparency"]["sd"])
            set_addr(r, _fmt(_clip(8.0 - latent, 1, 7)))

        # --- Workload (1..7) ---
        elif addr == "Workload_overall":
            wl = EFFECTS["workload"]["base"] + model._delta("workload", form) \
                + w_off + brng.gauss(0, EFFECTS["workload"]["sd"])
            set_addr(r, _fmt(_clip(wl, 1, 7)))

        # --- Preference debrief (once/session, 1..7) ---
        elif addr.startswith("PREF_"):
            set_addr(r, _fmt(float(brng.randint(1, 7)), 1))

    # The H2 mental-model probe rows are rewritten as a group (the template's old
    # count/recognition sliders are remapped to the revised localised battery).
    # See _rewrite_mm_probe, called from _resample_segment.


def _resample_comms(seg_rows, form, model, brng, prng):
    p_off = model._p_offset("comms_p_hit", prng)
    rt_off = model._p_offset("comms_rt", prng)
    for grp in _groups(seg_rows, "communications"):
        rows = {r["address"]: r for r in grp}
        if "sdt_value" not in rows:
            continue
        if str(rows["sdt_value"]["value"]) == "FA":
            continue
        p = _clip(EFFECTS["comms_p_hit"]["base"]
                  + model._delta("comms_p_hit", form) + p_off, 0.02, 0.98)
        if brng.random() < p:
            rows["sdt_value"]["value"] = "HIT"
            if "response_time" in rows:
                rt = EFFECTS["comms_rt"]["base"] + model._delta("comms_rt", form) \
                    + rt_off + brng.gauss(0, EFFECTS["comms_rt"]["sd"])
                rows["response_time"]["value"] = _fmt(_clip(rt, 400, 28000), 0)
            if "response_deviation" in rows:
                rows["response_deviation"]["value"] = _fmt(brng.uniform(-0.1, 0.1), 1)
            if "correct_radio" in rows:
                rows["correct_radio"]["value"] = "1"
        else:
            err = brng.choice(["BAD_FREQ", "BAD_RADIO", "MISS"])
            rows["sdt_value"]["value"] = err
            if err == "MISS":
                if "response_time" in rows:
                    rows["response_time"]["value"] = "nan"
                if "response_deviation" in rows:
                    rows["response_deviation"]["value"] = "nan"
            else:
                if "response_time" in rows:
                    rt = EFFECTS["comms_rt"]["base"] + 2000 + brng.gauss(0, 3000)
                    rows["response_time"]["value"] = _fmt(_clip(rt, 400, 28000), 0)
                if "response_deviation" in rows and err == "BAD_FREQ":
                    rows["response_deviation"]["value"] = _fmt(brng.uniform(-1.5, 1.5), 1)
                if "correct_radio" in rows:
                    rows["correct_radio"]["value"] = "0" if err == "BAD_RADIO" else "1"


def _resample_resman(seg_rows, form, model, brng, prng):
    dev_off = model._p_offset("resman_dev_sd", prng)
    sd = max(40.0, EFFECTS["resman_dev_sd"]["base"]
             + model._delta("resman_dev_sd", form) + dev_off)
    for grp in _groups(seg_rows, "resman"):
        rows = {r["address"]: r for r in grp}
        for side in ("a", "b"):
            dkey, tkey = f"{side}_deviation", f"{side}_in_tolerance"
            if dkey in rows:
                dev = brng.gauss(0, sd)
                rows[dkey]["value"] = _fmt(dev, 1)
                if tkey in rows:
                    rows[tkey]["value"] = "1" if abs(dev) <= _RESMAN_TOL else "0"


# ---------------------------------------------------------------------------
# Session assembly.
# ---------------------------------------------------------------------------
def _clone(rows: list[dict]) -> list[dict]:
    return [dict(r) for r in rows]


def _regenerate_header_tokens(header: list[dict], pid: str, brng: random.Random) -> None:
    """New scenario_path participant + fresh comms callsigns / frequencies."""
    def rand_callsign() -> str:
        L = "".join(brng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(3))
        return f"{L}{brng.randint(0, 999):03d}"

    for r in header:
        if r["type"] == "scenario_path":
            r["value"] = re.sub(r"full_P\d+", f"full_{pid}", str(r["value"]))
        elif r["type"] == "seed_output" and r["module"] == "communications":
            v = str(r["value"])
            if re.fullmatch(r"[A-Z]{3}\d{3}", v):
                r["value"] = rand_callsign()
            elif re.fullmatch(r"\d+\.\d+", v):   # a radio frequency
                r["value"] = _fmt(brng.uniform(108.0, 137.0), 6)


def build_session(template: Template, pid: str, order: list[tuple[str, str]],
                  model: OutcomeModel, logtime_base: float) -> list[dict]:
    """Assemble all rows for one simulated participant."""
    brng = model.block_rng(pid, "header", "_")
    rows: list[dict] = []

    # Header + practice (timestamps only shifted by the global logtime base).
    header = _clone(template.header)
    _regenerate_header_tokens(header, pid, brng)
    _shift_time(header, 0.0, logtime_base)
    rows.extend(header)

    # The first F-briefing in the template marks the practice->block boundary.
    slot_start = template.segments[order[0][1]].t_min  # = first briefing scenario_time
    slot_start = min(s.t_min for s in template.segments.values())  # earliest briefing

    cursor = slot_start
    for form, letter in order:
        seg = template.segments[letter]
        seg_rows = _clone(seg.rows)
        d_sc = cursor - seg.t_min
        _shift_time(seg_rows, d_sc, d_sc + logtime_base)
        _retarget_form(seg_rows, seg.src_form, form)
        _resample_segment(seg_rows, form, letter, pid, model)
        rows.extend(seg_rows)
        cursor += seg.duration + 0.5  # small gap before the next briefing

    # Footer (end_of_session + preference debrief) after the last slot.
    footer = _clone(template.footer)
    f_min = min((_to_float(r["scenario_time"]) for r in footer
                 if _to_float(r["scenario_time"]) == _to_float(r["scenario_time"])),
                default=cursor)
    d_sc = cursor - f_min
    _shift_time(footer, d_sc, d_sc + logtime_base)
    _retarget_form(footer, "F_", "F_")  # footer is form-neutral
    _resample_genericscales(footer, order[-1][0], order[-1][1], model, brng,
                            model.participant_rng(pid))
    rows.extend(footer)
    return rows


def write_session(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def generate(template_path: str | Path = DEFAULT_TEMPLATE,
             out_dir: str | Path = DEFAULT_OUT, n: int = 20, seed: int = 0,
             embed_effects: bool = True) -> list[Path]:
    """Generate ``n`` simulated sessions; return the written file paths."""
    template = load_template(template_path)
    model = OutcomeModel(seed=seed, embed_effects=embed_effects)
    out_dir = Path(out_dir)

    pids = list(PARTICIPANT_ORDERS)[:n]
    written: list[Path] = []
    base_clock = _to_float(template.header[0]["logtime"]) if template.header else 480000.0
    for i, pid in enumerate(pids):
        order = PARTICIPANT_ORDERS[pid]
        # Distinct absolute clock per participant (keeps logtime monotone, realistic).
        logtime_base = i * 5000.0 + random.Random(f"{seed}|clock|{pid}").uniform(0, 1000)
        rows = build_session(template, pid, order, model, logtime_base)
        stamp = f"2606{i + 1:02d}_19{i:02d}45"  # synthetic YYMMDD_HHMMSS, unique per file
        path = out_dir / f"sim_{pid}_{stamp}.csv"
        write_session(rows, path)
        written.append(path)
    return written


# ---------------------------------------------------------------------------
# CLI + self-check.
# ---------------------------------------------------------------------------
def _self_check(out_dir: Path) -> None:
    from ..matb_analysis.discovery import find_study_sessions
    from ..matb_analysis.validation import validate_sessions
    from ..matb_analysis.aggregate import build_metrics_table

    sessions = find_study_sessions(out_dir)
    report = validate_sessions(sessions)
    ok = bool(report["ok"].all()) if not report.empty else False
    print(f"\nvalidation: {report['ok'].sum()}/{len(report)} sessions ok")
    if not ok:
        print(report[~report["ok"]][["session_file", "issues"]].to_string(index=False))
    table = build_metrics_table(sessions)
    cols = [c for c in ["subj_transparency", "workload", "mm_explicability",
                        "detection_rate", "overwrite_rate", "accuracy", "rmsd_mean"]
            if c in table.columns]
    print("\nform-wise means (expect F1 high transparency/workload/overwrite, "
          "F2/F3 high explicability/detection/accuracy, low rmsd):")
    print(table.groupby("form")[cols].mean().round(3).to_string())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate simulated OpenMATB study sessions.")
    p.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    p.add_argument("--out", default=str(DEFAULT_OUT))
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--no-effects", action="store_true",
                   help="generate neutral data (no systematic F1/F2/F3 differences)")
    p.add_argument("--self-check", action="store_true",
                   help="validate the output and print form-wise metric means")
    args = p.parse_args(argv)

    paths = generate(args.template, args.out, n=args.n, seed=args.seed,
                     embed_effects=not args.no_effects)
    print(f"wrote {len(paths)} sessions to {args.out}")
    if args.self_check:
        _self_check(Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
