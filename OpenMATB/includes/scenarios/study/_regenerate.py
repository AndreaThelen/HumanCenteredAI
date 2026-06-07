#!/usr/bin/env python3
# Regenerates the study scenario files.
# Output: practice.txt, F{1,2,3}_block_{A,B,C}.txt, full_P01..P{N_PARTICIPANTS}.txt,
#         final_questionnaires.txt.
# Tune the constants below and re-run; do not hand-edit the .txt files.
#
# Run:   python _regenerate.py     (from this folder)
#
# Target wall-clock per full_PXX ≈ 20 min once participant time on briefings /
# questionnaires is added. Scenario MATB time is ~18:30.
#
# History: the original design used 5 min practice, 6:30 blocks, and 12
# sysmon events per block. The current values (3, 5:00, 9) match
# Documents/Study_proposal.md.

from pathlib import Path

OUT_DIR = Path(__file__).parent

# --- Timing knobs ----------------------------------------------------------
PRACTICE_DURATION_SEC   = 3 * 60
BLOCK_MATB_DURATION_SEC = 5 * 60
EVENTS_PER_BLOCK        = 9
EVENT_FIRST_OFFSET_SEC  = 30      # first sysmon event after task start
EVENT_GAP_SEC           = 30      # spacing between sysmon events
PANEL_DELAY_SEC         = 2       # panel fires this many seconds after the failure
QUESTIONNAIRE_GAP_SEC   = 0       # fire questionnaire screens back-to-back. A >0
                                  # gap lets the (paused) MATB task windows flash
                                  # back into view between blocking screens.

# --- Event pattern (length must equal EVENTS_PER_BLOCK) --------------------
# R = routine auto-solved · NM = near-miss auto-solved · M = miss (no aid)
EVENT_PATTERN = ["R", "R", "NM", "R", "M", "R", "NM", "M", "R"]
assert len(EVENT_PATTERN) == EVENTS_PER_BLOCK

# Two-element gauge set per block.
GAUGE_BY_BLOCK = {
    "A": ("scales-1", "scales-3"),
    "B": ("lights-1", "lights-2"),
    "C": ("scales-2", "scales-4"),
}

# Per block the aid HANDLES one active gauge (acts on it; all routine events and
# BOTH near-misses land here) and MISSES the other (its only events are the two
# unhandled failures). This gives each active gauge one clean, distinct role for
# the post-block mental-model probe (H2): one gauge the aid clearly worked, one it
# clearly abandoned. Counterbalanced across blocks (the missed gauge is the lower
# number in A, the higher in B and C) so "the lower-numbered gauge is always
# missed" is not a usable heuristic.
HANDLED_GAUGE_BY_BLOCK = {"A": "scales-3", "B": "lights-1", "C": "scales-2"}


def missed_gauge(block_letter):
    """The active gauge the aid skips this block (the non-handled one of the set)."""
    return next(g for g in GAUGE_BY_BLOCK[block_letter]
                if g != HANDLED_GAUGE_BY_BLOCK[block_letter])

# Communications schedule inside a block: spacing 30 s, starting 15 s in.
COMM_PATTERN = ["own", "other", "own", "own", "other",
                "own", "own", "other", "own"]
COMM_FIRST_OFFSET_SEC = 15
COMM_GAP_SEC          = 30

# Resman pump events (offset within the block, in seconds).
RESMAN_EVENTS = [
    (60,  "pump-1-state", "failure"),
    (105, "pump-1-state", "on"),
    (210, "pump-3-state", "failure"),
    (255, "pump-3-state", "on"),
]

# --- Latin-square orderings -----------------------------------------------
# Base counterbalancing set of 10 unique (form, block) orderings. Participants
# beyond P10 replicate this set in order (P11 == P01, ..., P20 == P10), which
# keeps the design balanced while providing spare, pre-counterbalanced scenarios
# for replacements or extra recruitment. Bump N_PARTICIPANTS to generate more.
N_PARTICIPANTS = 20

_BASE_ORDERS = [
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

PARTICIPANT_ORDERS = {
    f"P{i + 1:02d}": _BASE_ORDERS[i % len(_BASE_ORDERS)]
    for i in range(N_PARTICIPANTS)
}


# --- Helpers --------------------------------------------------------------
def hms(total_sec):
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    return f"{h}:{m:02d}:{s:02d}"


def block_event_gauge(block_letter, event_idx):
    """1-indexed event_idx → gauge name. The aid MISSES one gauge of the block (its
    only events are the two unhandled failures) and HANDLES the other (all routine
    events plus both near-misses land here), so each active gauge has one clean
    role for the post-block probe. See PROBE_TARGETS / mental_model_items."""
    kind = EVENT_PATTERN[event_idx - 1]
    return missed_gauge(block_letter) if kind == "M" else HANDLED_GAUGE_BY_BLOCK[block_letter]


def panel_fires(form, event_idx):
    """Revised design (Documents/Study_design_revised.md): information content is held
    CONSTANT across forms, so a panel fires on EVERY event in EVERY form. The forms differ
    only in wording (F1 verbose / F2 contrastive / F3 contrastive + actionable cue on
    misses). Frequency is no longer a manipulated variable."""
    return True


# --- Panel content (single source of truth for F1/F2/F3) ------------------
# Content-constant rule (Documents/Study_design_revised.md): for each event the
# action-relevant facts -- which indicator, that it was out of range/active, whether the
# aid acted, and (for near-misses) the time-to-failure -- are IDENTICAL across F1/F2/F3.
# F1 only adds grammatical scaffolding and redundant exact sensor values; it introduces no
# new action-relevant fact. All three panels are rendered here from the same event facts so
# they cannot drift apart.

PANELS_DIR = OUT_DIR.parent.parent / "instructions" / "study" / "panels"


def _val(i):
    """Deterministic out-of-range scale value (above the 45.0 upper bound)."""
    return round(46.0 + ((i * 7) % 6) * 0.4, 1)


def _ttf(i):
    """Deterministic near-miss time-to-failure in seconds (shared by F1 and F2)."""
    return round(2.0 + ((i * 5) % 5) * 0.5, 1)


def _dur(i):
    """Deterministic out-of-range duration in seconds (verbose-only detail)."""
    return round(0.5 + ((i * 3) % 5) * 0.4, 1)


def indicator_parts(gauge):
    """Return display attributes for a gauge name like 'scales-1' / 'lights-2'."""
    family, num = gauge.split("-")
    if family == "scales":
        return {"type": "scale", "n": num, "name": f"scale-{num}",
                "actverb": "Reset", "routine_state": "in range"}
    # lights: light-1 is the green status light (failure = switches off, fix = restore),
    # light-2 is the red warning light (failure = comes on, fix = clear).
    if num == "1":
        return {"type": "light", "n": num, "name": f"light-{num}",
                "desc": "The green status light", "fail": "switched off",
                "fixed": "restored", "fixv": "restore", "actverb": "Restored",
                "routine_state": "nominal"}
    return {"type": "light", "n": num, "name": f"light-{num}",
            "desc": "The red warning light", "fail": "came on",
            "fixed": "cleared", "fixv": "clear", "actverb": "Cleared",
            "routine_state": "cleared"}


def _wrap(head, body):
    return f"<p><strong>{head}</strong></p>\n<p>{body}</p>\n"


def panel_F1(i, kind, gauge):
    """Verbose / descriptive narration of this event's facts (no other indicators)."""
    p = indicator_parts(gauge)
    if p["type"] == "scale":
        v, n = _val(i), p["n"]
        if kind == "R":
            body = (f"Scale-{n} rose to {v}, above the upper bound of 45.0; "
                    f"the automation reset it to 32.0 and it is back in range.")
        elif kind == "NM":
            body = (f"Scale-{n} rose to {v}, above the 45.0 bound, for {_dur(i)} s; "
                    f"the automation reset it to 32.0. Without the reset it would have "
                    f"failed in ~{_ttf(i)} s.")
        else:
            body = (f"Scale-{n} was {v}, above the upper bound of 45.0; "
                    f"the automation did not act on this gauge.")
    else:
        n = p["n"]
        if kind == "R":
            body = f"{p['desc']} (light-{n}) {p['fail']}; the automation {p['fixed']} it."
        elif kind == "NM":
            body = (f"{p['desc']} (light-{n}) {p['fail']}; the automation {p['fixed']} it "
                    f"just in time - it would have been missed in ~{_ttf(i)} s.")
        else:
            body = (f"{p['desc']} (light-{n}) {p['fail']}; "
                    f"the automation did not {p['fixv']} it.")
    return _wrap(f"Cycle {i:02d} (auto-aid)", body)


def panel_F2(i, kind, gauge, actionable=False):
    """Concise / contrastive framing of the SAME facts. F3 = actionable=True."""
    p = indicator_parts(gauge)
    if kind == "R":
        body = f"Handled {p['name']} - aid kept it {p['routine_state']}."
    elif kind == "NM":
        body = f"{p['actverb']} {p['name']} - would have failed in ~{_ttf(i)} s."
    else:
        body = f"Skipped {p['name']} - auto-aid did not act."
        if actionable:
            body += " <strong>Check it yourself.</strong>"
    return _wrap("Auto-aid panel", body)


def render_panel(form, i, kind, gauge):
    if form == "F1":
        return panel_F1(i, kind, gauge)
    return panel_F2(i, kind, gauge, actionable=(form == "F3"))


def write_panels():
    """(Re)generate every F1/F2/F3 panel from the shared event facts."""
    for form in ("F1", "F2", "F3"):
        (PANELS_DIR / form).mkdir(parents=True, exist_ok=True)
        for block_letter in ("A", "B", "C"):
            for i, kind in enumerate(EVENT_PATTERN, start=1):
                gauge = block_event_gauge(block_letter, i)
                text = render_panel(form, i, kind, gauge)
                path = PANELS_DIR / form / f"block_{block_letter}_event_{i:02d}.txt"
                path.write_text(text, encoding="utf-8")
    print(f"  wrote 81 panel files into {PANELS_DIR}")


# --- Post-block mental-model probe (H2) -----------------------------------
# Three yes/no questions per block, each about ONE active gauge, whose correct
# answer is fixed by THIS block's roles (handled vs missed, above) -- so the probe
# can never drift from the scenario and genuinely tests per-block mental-model
# updating (the earlier count/reliability items were dropped: their truth was a
# design constant, identical every block, so they rewarded learning the design
# rather than tracking the block). Question types:
#   act   -- "did the aid act on X?"             (truth Yes if X is the handled gauge)
#   miss  -- "did the aid FAIL to act on Y?"     (truth Yes if Y is the missed gauge)
#   close -- "was there a close call on Z?"      (truth Yes if Z is the handled gauge,
#                                                 which carries both near-misses)
#
# Each question targets a gauge by ROLE; the roles are counterbalanced across
# blocks (PROBE_TARGETS) so no fixed yes/no answer pattern wins, and the act/miss
# questions always name DIFFERENT gauges (the "X" and "Y" of the design).
QUESTIONNAIRES_DIR = OUT_DIR.parent.parent / "questionnaires" / "study"
PROBE_TARGETS = {
    "A": [("act", "handled"), ("miss", "missed"), ("close", "missed")],   # Yes Yes No
    "B": [("act", "missed"),  ("miss", "handled"), ("close", "handled")],  # No  No  Yes
    "C": [("act", "missed"),  ("miss", "handled"), ("close", "handled")],  # No  No  Yes
}


def indicator_label(gauge):
    """Display name used in the probe wording (matches the gauge labels in OpenMATB)."""
    family, num = gauge.split("-")
    if family == "scales":
        return f"Scale {num}"
    return f"Status light {num}" if num == "1" else f"Warning light {num}"


def gauge_slider_token(gauge):
    """'scales-1' -> 'scale1', 'lights-2' -> 'light2' (the slider-id form)."""
    family, num = gauge.split("-")
    return f"{'scale' if family == 'scales' else 'light'}{num}"


def role_gauge(block_letter, role):
    return (HANDLED_GAUGE_BY_BLOCK[block_letter] if role == "handled"
            else missed_gauge(block_letter))


def mental_model_items(block_letter):
    """The 3 probe items for a block: (qtype, gauge)."""
    return [(qtype, role_gauge(block_letter, role))
            for qtype, role in PROBE_TARGETS[block_letter]]


def render_mental_model(block_letter):
    lines = []
    for qtype, gauge in mental_model_items(block_letter):
        sid = f"MM_{block_letter}_{qtype}_{gauge_slider_token(gauge)}"
        label = indicator_label(gauge)
        if qtype == "act":
            prompt = f"Did the automation act on {label} at any point during this block?"
        elif qtype == "miss":
            prompt = (f"Did the automation FAIL to act on {label} at some point, "
                      f"leaving you to handle it yourself?")
        else:  # close
            prompt = f"Was there a close call (near miss) on {label} during this block?"
        lines.append(f"{sid};{prompt};No/Yes;0/100/50")
    return lines


def write_mental_model_probes():
    """(Re)generate the three post-block mental-model questionnaire files."""
    QUESTIONNAIRES_DIR.mkdir(parents=True, exist_ok=True)
    for block_letter in ("A", "B", "C"):
        lines = render_mental_model(block_letter)
        path = QUESTIONNAIRES_DIR / f"mental_model_block_{block_letter}.txt"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  wrote {path.name}  ({len(lines)} items)")


# --- Rendering blocks -----------------------------------------------------
def render_briefing(form, t0):
    return [
        f"# 1. Briefing (form-specific)",
        f"{hms(t0)};instructions;filename;study/briefing_{form}.txt",
        f"{hms(t0)};instructions;start",
        "",
    ]


def render_sysmon_params(t0):
    return [
        f"# 2. Sysmon parameters (Frontiers 2024 moderate-load configuration)",
        f"{hms(t0)};sysmon;automaticsolverdelay;1000",
        f"{hms(t0)};sysmon;alerttimeout;10000",
        f"{hms(t0)};sysmon;feedbackduration;1500",
        f"{hms(t0)};sysmon;automaticsolver;True",
        "",
    ]


def render_task_starts(t0, with_auto_aid):
    return [
        f"# 3. Start the four MATB tasks (sysmon supported by auto-aid; the others are NOT)",
        f"{hms(t0)};sysmon;automaticsolver;{'True' if with_auto_aid else 'False'}",
        f"{hms(t0)};sysmon;start",
        f"{hms(t0)};communications;start",
        f"{hms(t0)};scheduling;start",
        f"{hms(t0)};resman;start",
        "",
    ]


def render_comms(t0):
    out = [f"# 4. Communications schedule ({EVENTS_PER_BLOCK} calls)"]
    for i, prompt in enumerate(COMM_PATTERN[:EVENTS_PER_BLOCK]):
        t = t0 + COMM_FIRST_OFFSET_SEC + i * COMM_GAP_SEC
        out.append(f"{hms(t)};communications;radioprompt;{prompt}")
    out.append("")
    return out


# Resman default state (mirrors plugins/resman.py): every block starts here.
RESMAN_DEFAULT_TANKS = [("a", 2500), ("b", 2500), ("c", 1000),
                        ("d", 1000), ("e", 3000), ("f", 3000)]


def render_resman_reset(t0):
    """Reset resman tanks and pumps to their defaults so every block starts from an
    identical state. In full_PXX the tasks run continuously (never stopped/restarted
    between blocks), so without this the mutated tank levels -- and any failed/active
    pumps -- drift from one block straight into the next. These set_parameter events
    fire at the block's t0; while the briefing is on screen the scenario clock is
    paused, so they take effect the instant the MATB tasks resume for the block."""
    out = ["# 0. Reset resman to default state (identical block-start conditions)"]
    for letter, level in RESMAN_DEFAULT_TANKS:
        out.append(f"{hms(t0)};resman;tank-{letter}-level;{level}")
    for n in range(1, 9):
        out.append(f"{hms(t0)};resman;pump-{n}-state;off")
    out.append("")
    return out


def render_resman(t0):
    out = [f"# 5. Resman background load ({len(RESMAN_EVENTS)} pump events)"]
    for off, cmd, val in RESMAN_EVENTS:
        out.append(f"{hms(t0 + off)};resman;{cmd};{val}")
    out.append("")
    return out


def render_sysmon_events(t0, form, block_letter):
    n_miss = EVENT_PATTERN.count("M")
    n_solved = EVENTS_PER_BLOCK - n_miss
    out = [f"# 6. Sysmon experimental events ({EVENTS_PER_BLOCK} total, "
           f"{n_solved} auto-solved + {n_miss} missed)"]
    for i, kind in enumerate(EVENT_PATTERN, start=1):
        gauge = block_event_gauge(block_letter, i)
        t_event = t0 + EVENT_FIRST_OFFSET_SEC + (i - 1) * EVENT_GAP_SEC
        t_setup = t_event - 1
        t_panel = t_event + PANEL_DELAY_SEC
        label = {"R": "routine", "NM": "nearmiss", "M": "miss"}[kind]
        out.append(f"# Event {i:02d} at {hms(EVENT_FIRST_OFFSET_SEC + (i-1)*EVENT_GAP_SEC)}"
                   f" : {gauge} ({label})")
        out.append(f"{hms(t_setup)};sysmon;automaticsolver;"
                   f"{'False' if kind == 'M' else 'True'}")
        out.append(f"{hms(t_event)};sysmon;{gauge}-failure;True")
        if panel_fires(form, i):
            panel_path = f"study/panels/{form}/block_{block_letter}_event_{i:02d}.txt"
            out.append(f"{hms(t_panel)};instructions;filename;{panel_path}")
            out.append(f"{hms(t_panel)};instructions;start")
        out.append("")
    return out


def render_task_stops(t0):
    return [
        f"# 7. End of experimental block - stop tasks",
        f"{hms(t0)};sysmon;stop",
        f"{hms(t0)};communications;stop",
        f"{hms(t0)};scheduling;stop",
        f"{hms(t0)};resman;stop",
        "",
    ]


def render_post_block_questionnaires(t0, block_letter):
    """Returns (lines, end_time_sec) where end_time is when the last item fires."""
    g = QUESTIONNAIRE_GAP_SEC
    out = ["# 8. Post-block questionnaire battery"]
    # Revised lean battery (Documents/Study_design_revised.md). Per-block trust and the
    # full NASA-TLX are dropped; trust is captured once in the end-of-session debrief.
    # Order is PROBE-FIRST, then transparency, then workload last:
    #   1. mental_model_block_X    (objective explicability probe; captured first to
    #                               minimise memory decay/reconstruction -- H2)
    #   2. subjective_transparency (3 items, the subjective half of the crossover -- H1)
    #   3. workload                (single Paas-style item; rated last so effort-rating
    #                               does not colour the earlier answers -- mechanism check)
    # genericscales renders every item on one screen and only logs the final page,
    # so each file is kept <=6 items (one blocking screen, logged on its own stop()).
    items = [
        ("instructions",  "study/end_of_block.txt"),
        ("genericscales", f"study/mental_model_block_{block_letter}.txt"),
        ("genericscales", "study/subjective_transparency.txt"),
        ("genericscales", "study/workload.txt"),
    ]
    last_t = t0
    for i, (plugin, fname) in enumerate(items):
        last_t = t0 + i * g
        out.append(f"{hms(last_t)};{plugin};filename;{fname}")
        out.append(f"{hms(last_t)};{plugin};start")
    out.append("")
    return out, last_t


def render_block(form, block_letter, t0, include_task_lifecycle):
    """Returns (lines, end_time_sec). end_time = last questionnaire fired."""
    lines = []
    lines += [
        f"# Study scenario - Form {form}, Block {block_letter}",
        f"# Information content held CONSTANT across forms (same events, same facts, same panel frequency);",
        f"# vary ONLY the wording-form: F1 verbose / F2 contrastive / F3 contrastive + actionable cue on misses.",
        f"# Block {block_letter} uses a distinct gauge set so the post-block mental-model probe cannot be answered by recall from another block.",
        "",
    ]
    lines += render_briefing(form, t0)
    lines += render_resman_reset(t0)
    lines += render_sysmon_params(t0)
    if include_task_lifecycle:
        lines += render_task_starts(t0, with_auto_aid=True)
    lines += render_comms(t0)
    lines += render_resman(t0)
    lines += render_sysmon_events(t0, form, block_letter)
    matb_end = t0 + BLOCK_MATB_DURATION_SEC
    if include_task_lifecycle:
        lines += render_task_stops(matb_end)
    q_start = matb_end + 1
    q_lines, end = render_post_block_questionnaires(q_start, block_letter)
    lines += q_lines
    return lines, end


# --- Practice -------------------------------------------------------------
def render_practice(t0, include_task_lifecycle):
    lines = [
        f"# Practice scenario - {PRACTICE_DURATION_SEC // 60} minutes, no automation aid",
        f"# Run ONCE per participant before any experimental block.",
        "",
        f"# 1. Briefing",
        f"{hms(t0)};instructions;filename;study/briefing_practice.txt",
        f"{hms(t0)};instructions;start",
        "",
    ]
    if include_task_lifecycle:
        lines += render_task_starts(t0, with_auto_aid=False)
    else:
        # In full_PXX, set the auto-aid OFF for practice without (re)starting tasks.
        lines += [
            f"# 2. Sysmon auto-aid OFF for practice",
            f"{hms(t0)};sysmon;automaticsolver;False",
            f"{hms(t0)};sysmon;start",
            f"{hms(t0)};communications;start",
            f"{hms(t0)};scheduling;start",
            f"{hms(t0)};resman;start",
            "",
        ]

    # Sample sysmon failures (manual), one every ~30 s, capped by PRACTICE_DURATION_SEC
    practice_sysmon = [
        ("scales-1-failure", 30),
        ("lights-2-failure", 60),
        ("scales-3-failure", 90),
        ("lights-1-failure", 120),
        ("scales-2-failure", 150),
    ]
    lines.append("# Practice sysmon failures (manual response expected)")
    for cmd, off in practice_sysmon:
        if off >= PRACTICE_DURATION_SEC:
            break
        lines.append(f"{hms(t0 + off)};sysmon;{cmd};True")
    lines.append("")

    practice_comms = [
        ("own",   45),
        ("other", 75),
        ("own",   105),
        ("other", 135),
        ("own",   165),
    ]
    lines.append("# Practice communications")
    for prompt, off in practice_comms:
        if off >= PRACTICE_DURATION_SEC:
            break
        lines.append(f"{hms(t0 + off)};communications;radioprompt;{prompt}")
    lines.append("")

    # Every pump failure MUST be repaired before practice ends. In the full_PXX
    # scenarios the tasks run continuously (no stop/restart between segments), so
    # an unrepaired pump failure here would persist through all experimental
    # blocks. Repair pump-2 back to its default 'off' (idle, usable) state.
    practice_resman = [
        ("pump-1-state", "failure", 60),
        ("pump-1-state", "on",      120),
        ("pump-2-state", "failure", 150),
        ("pump-2-state", "off",     170),
    ]
    lines.append("# Practice resman pump events")
    for cmd, val, off in practice_resman:
        if off >= PRACTICE_DURATION_SEC:
            break
        lines.append(f"{hms(t0 + off)};resman;{cmd};{val}")
    lines.append("")

    if include_task_lifecycle:
        end = t0 + PRACTICE_DURATION_SEC
        lines.append(f"# End of practice")
        lines += [
            f"{hms(end)};sysmon;stop",
            f"{hms(end)};communications;stop",
            f"{hms(end)};scheduling;stop",
            f"{hms(end)};resman;stop",
            "",
        ]
        return lines, end
    return lines, t0 + PRACTICE_DURATION_SEC


# --- Final questionnaires -------------------------------------------------
def render_final(t0):
    """End-of-session battery. Per Documents/Study_proposal.md the only
    remaining item is the preference debrief comparing the three forms."""
    g = QUESTIONNAIRE_GAP_SEC
    lines = [
        f"# Final session questionnaires - run ONCE after the third experimental block",
        "",
        f"{hms(t0)};instructions;filename;study/end_of_session.txt",
        f"{hms(t0)};instructions;start",
        "",
        f"# End-of-session preference comparison across the three forms",
        f"{hms(t0 + g)};genericscales;filename;study/preference_debrief.txt",
        f"{hms(t0 + g)};genericscales;start",
        "",
    ]
    return lines, t0 + g


# --- File writers ---------------------------------------------------------
def write_lines(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  wrote {path.name}  ({len(lines)} lines)")


def main():
    print("Regenerating study scenarios into", OUT_DIR)

    # 0. F1/F2/F3 panels (rendered from the shared event facts; content held constant)
    write_panels()

    # 0b. Post-block mental-model probe questionnaires (H2), derived from the same
    #     event/gauge schedule so their correct answers can never drift.
    write_mental_model_probes()

    # 1. practice.txt
    lines, _ = render_practice(0, include_task_lifecycle=True)
    write_lines(OUT_DIR / "practice.txt", lines)

    # 2. F{1,2,3}_block_{A,B,C}.txt
    for form in ("F1", "F2", "F3"):
        for block_letter in ("A", "B", "C"):
            lines, _ = render_block(form, block_letter, 0, include_task_lifecycle=True)
            write_lines(OUT_DIR / f"{form}_block_{block_letter}.txt", lines)

    # 3. final_questionnaires.txt (standalone copy at offset 0)
    fin_lines, _ = render_final(0)
    write_lines(OUT_DIR / "final_questionnaires.txt", fin_lines)

    # 4. full_P01..P{N_PARTICIPANTS}.txt
    for pid, order in PARTICIPANT_ORDERS.items():
        all_lines = [
            f"# Full-session scenario for participant {pid}",
            f"# Order: practice -> "
            + " -> ".join(f"{f}_block_{b}" for f, b in order)
            + " -> final_questionnaires",
            f"# Set OpenMATB/config.ini -> scenario_path=study/full_{pid}.txt and run main.py once.",
            f"# Inter-segment task start/stop events are removed: tasks run continuously and are",
            f"# auto-paused whenever a blocking plugin (briefing/panel/questionnaire) is on screen.",
            f"# The tasks are stopped once after the last block so OpenMATB auto-exits when the",
            f"# final questionnaire is dismissed.",
            "",
        ]

        # Practice
        all_lines.append(f"# === Segment 1: practice (0:00:00 - {hms(PRACTICE_DURATION_SEC)}) ===")
        prac_lines, prac_end = render_practice(0, include_task_lifecycle=False)
        all_lines += prac_lines

        cursor = prac_end + 1
        for seg_i, (form, block_letter) in enumerate(order, start=2):
            block_lines, block_end = render_block(form, block_letter, cursor,
                                                  include_task_lifecycle=False)
            all_lines.append(
                f"# === Segment {seg_i}: {form}_block_{block_letter}"
                f" ({hms(cursor)} - {hms(block_end)}) ==="
            )
            all_lines += block_lines
            cursor = block_end + 1

        # Stop the four MATB tasks once the last experimental block is over, BEFORE
        # the end-of-session questionnaires. This (a) stops the task windows from
        # flashing behind the final questionnaires and (b) lets OpenMATB auto-exit
        # the moment the last questionnaire is dismissed: with no plugin left alive
        # and no events queued, the scheduler closes the window by itself (no manual
        # quit, no trailing seconds of the tasks running on).
        all_lines += [
            f"# === End of experiments: stop the four MATB tasks ===",
            f"{hms(cursor)};sysmon;stop",
            f"{hms(cursor)};communications;stop",
            f"{hms(cursor)};scheduling;stop",
            f"{hms(cursor)};resman;stop",
            "",
        ]

        # Final questionnaires (run with the tasks already stopped)
        fin_lines, fin_end = render_final(cursor)
        all_lines.append(f"# === Segment 5: final_questionnaires"
                         f" ({hms(cursor)} - {hms(fin_end)}) ===")
        all_lines += fin_lines

        write_lines(OUT_DIR / f"full_{pid}.txt", all_lines)

    print("Done.")


if __name__ == "__main__":
    main()
