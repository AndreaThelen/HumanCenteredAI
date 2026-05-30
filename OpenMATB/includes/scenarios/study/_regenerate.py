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

# Two-element gauge set per block. The pattern alternates a/b across events.
GAUGE_BY_BLOCK = {
    "A": ("scales-1", "scales-3"),
    "B": ("lights-1", "lights-2"),
    "C": ("scales-2", "scales-4"),
}

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
    """1-indexed event_idx → gauge name. Alternates the two gauges; pattern keeps
    each gauge family roughly balanced across routine / nearmiss / miss events."""
    a, b = GAUGE_BY_BLOCK[block_letter]
    # Same alternation as the original hand-built scenarios:
    # event 1=a, 2=b, 3=a, 4=b, 5=a, 6=b, 7=b, 8=a, 9=b
    mapping = [a, b, a, b, a, b, b, a, b]
    return mapping[event_idx - 1]


def panel_fires(form, event_idx):
    """F1 panels fire on every event; F2/F3 only on events 3, 5, 7, 8."""
    if form == "F1":
        return True
    return event_idx in (3, 5, 7, 8)


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
    # Order is subjective-first, objective-probe-last (see tmp/proposal2.md S5):
    # the mental-model probe must not contaminate self-reported transparency/trust.
    #   1. subjective_transparency (4 items, researcher-designed)
    #   2. subjective_trust        (4 items, plain-English, non-native-friendly;
    #                               adapted from Jian/Bisantz 2000, reverse-worded
    #                               distrust items dropped for clarity)
    #   3. mental_model_block_X    (objective probe, scored vs. ground truth)
    # genericscales renders every item on one screen and only logs the final page,
    # so each file is kept <=6 items (one blocking screen, logged on its own stop()).
    items = [
        ("instructions",  "study/end_of_block.txt"),
        ("genericscales", "study/subjective_transparency.txt"),
        ("genericscales", "study/subjective_trust.txt"),
        ("genericscales", f"study/mental_model_block_{block_letter}.txt"),
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
        f"# Hold transparency content matched at SAT Level 2; vary form (selectivity, contrastiveness, actionability).",
        f"# Block {block_letter} uses a distinct gauge set so the post-block mental-model probe cannot be answered by recall from another block.",
        "",
    ]
    lines += render_briefing(form, t0)
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
