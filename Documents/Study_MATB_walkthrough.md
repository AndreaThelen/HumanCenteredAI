# Study walkthrough 

A plain-English tour of the three `study/` folders in OpenMATB:

- `includes/scenarios/study/` — *timing scripts* that drive a session
- `includes/instructions/study/` — *briefing screens and pop-up panels*
- `includes/questionnaires/study/` — *slider questionnaires* shown between blocks and at the end

Together they implement the *Form of Explanation* experiment described in `Documents/Study_proposal.md`. The independent variable is the **form** of the automation aid's panel (F1 verbose / F2 selective+contrastive / F3 + actionable cue); the content of what is communicated is held constant.

---

## 1. The big picture: one session, end-to-end

A single participant runs `full_PXX.txt` once (where XX = 01..10). That scenario is **~20 minutes** of wall-clock and chains five segments:

| # | Segment | Duration (MATB) | Auto-aid | Purpose |
|---|---|---|---|---|
| 1 | Practice | 3 min | OFF | Learn the four MATB tasks and keys |
| 2 | Block 1 | 5 min | ON | First experimental form (F1, F2, or F3 — per Latin square) |
| 3 | Block 2 | 5 min | ON | Second form |
| 4 | Block 3 | 5 min | ON | Third form |
| 5 | Final questionnaires | <1 min | — | 3-form preference debrief |

Between every block the participant fills a battery of two questionnaires (mental-model probe, subjective transparency). Those screens *pause* the MATB clock until dismissed, so the real wall-clock for one participant is **~20 min**.

### Latin-square order across the ten participants

Each participant sees every form exactly once, paired with a different *gauge set* (A = scales-1/3, B = lights-1/2, C = scales-2/4) so the post-block memory probe cannot be answered by recall from another block.

| Participant | Block 1 | Block 2 | Block 3 |
|---|---|---|---|
| P01 | F1-A | F2-B | F3-C |
| P02 | F1-A | F3-B | F2-C |
| P03 | F2-A | F1-B | F3-C |
| P04 | F2-A | F3-B | F1-C |
| P05 | F3-A | F1-B | F2-C |
| P06 | F3-A | F2-B | F1-C |
| P07 | F1-B | F2-C | F3-A |
| P08 | F2-B | F3-C | F1-A |
| P09 | F3-B | F1-C | F2-A |
| P10 | F1-C | F2-A | F3-B |

---

## 2. The three forms (the experimental manipulation)

All three forms run the **same** sysmon failure timeline at the same moderate load. The automation acts on ~78% of events (7 of 9) and *skips* the rest (2 of 9). The forms differ only in **how the participant is told what the automation just did**:

- **F1 — Continuous status panel.** A panel fires on **every** event. It reads like a routine log: numbers, in-range/out-of-range, "auto-aid not engaged". No alarms, no contrastive framing. Every fact F2/F3 will surface later is *already* in the F1 stream — embedded in routine status language. Example (block A, event 5, a miss): *"Cycle 05 (auto-aid) — Scale-1: was 47.0 > upper bound 45.0, auto-aid not engaged. Scale-2: 31.5, in range. ..."*

- **F2 — Selective + contrastive.** A panel fires **only** on near-misses (the automation just acted) and misses (the automation did not). Routine, uneventful auto-resets do *not* trigger a panel. Wording is contrastive. Example (near-miss): *"Reset scale-1 — would have failed in ~2.5 s."* Example (miss): *"Skipped scale-1 — auto-aid did not act."*

- **F3 — Selective + contrastive + actionable.** Same selectivity and contrastive wording as F2, plus an explicit operator cue on misses. Example (miss): *"Skipped scale-1 — auto-aid did not act. **Check it yourself.**"*

The hypothesis: F2/F3 produce better *explicability* (the participant's mental model of the automation actually updates), even though F1 has the highest *explainability* (most words on screen).

---

## 3. The three blocks (gauge sets)

Each block uses a different pair of system-monitoring gauges so the post-block memory probe cannot be answered from another block.

| Block | Gauges that fail | Mental-model probe filename |
|---|---|---|
| A | scales-1 and scales-3 | `mental_model_block_A.txt` |
| B | lights-1 and lights-2 | `mental_model_block_B.txt` |
| C | scales-2 and scales-4 | `mental_model_block_C.txt` |

Event pattern is identical within a block (9 events, every 30 s):

| Event | Kind | Auto-aid | F1 panel? | F2/F3 panel? |
|---|---|---|---|---|
| 01 | Routine | acts | yes | — |
| 02 | Routine | acts | yes | — |
| 03 | Near-miss | acts (just in time) | yes | **yes** (contrastive) |
| 04 | Routine | acts | yes | — |
| 05 | **Miss** | does NOT act | yes | **yes** (skipped) |
| 06 | Routine | acts | yes | — |
| 07 | Near-miss | acts | yes | **yes** (contrastive) |
| 08 | **Miss** | does NOT act | yes | **yes** (skipped) |
| 09 | Routine | acts | yes | — |

So F1 fires 9 panels per block; F2 and F3 fire 4 panels per block (events 3, 5, 7, 8).

---

## 4. Folder 1 — `scenarios/study/` (21 .txt files)

These are *scenario scripts* OpenMATB reads line-by-line. Each line is `time;plugin;command;arg` (semicolon-separated), e.g. `0:01:30;sysmon;scales-1-failure;True` triggers a scale-1 failure at one-and-a-half minutes.

### `practice.txt`
3-minute practice. Auto-aid OFF. Mixes scales, lights, comms, and pump events so the participant learns the keys. Used standalone if you ever want to drill the practice alone.

### `F{1,2,3}_block_{A,B,C}.txt` (9 files — the **test scenarios**)
Standalone single-block runs. Each is briefing + ~5 min of MATB + 4 post-block questionnaires (~7–8 min wall-clock). Useful for testing a single form on a single gauge set without playing through the whole session.

**To run one:** edit `OpenMATB/config.ini` and set `scenario_path = study/F1_block_A.txt` (or whichever combination), then `python main.py`.

### `full_P01.txt` … `full_P10.txt` (10 files — the **real session** scenarios)
One per participant. Each concatenates `practice` + three blocks (in that participant's Latin-square order) + `final_questionnaires`. Tasks start once at 0:00:00 and run continuously; blocking screens (briefings, panels, questionnaires) auto-pause the MATB clock until dismissed. The actual session order is set by which `full_PXX.txt` is loaded.

### `final_questionnaires.txt`
The closing 3 screens, in the standalone form (offset 0:00:00). Inlined into every `full_PXX.txt` at the very end; this standalone copy exists for completeness.

### `_regenerate.py`
**Source of truth.** All 21 scenario files above are produced by this Python script. To re-tune timings (more/fewer events, longer/shorter practice, change the participant orders), edit the constants at the top and re-run `python _regenerate.py` from this folder. Hand-edits to the .txt files are lost on regeneration.

---

## 5. Folder 2 — `instructions/study/` (57 .txt files)

These are HTML snippets shown as full-screen modal dialogs. The participant reads, presses SPACE, and the MATB clock resumes.

### Briefings (5 files)

Shown once at the start of each segment.

- `briefing_practice.txt` — explains the four MATB tasks and which keys do what. Reminds the participant the practice is unscored.
- `briefing_F1.txt` — "A status panel will appear briefly each time the automation cycle reports its state... routine status language."
- `briefing_F2.txt` — "A panel will appear ONLY when something noteworthy has happened... contrastive wording."
- `briefing_F3.txt` — same as F2 plus: "the panel ends with an explicit operator cue: **Check it yourself.**"

### `end_of_block.txt`
Single screen shown after each experimental block: "This block is over. You will now answer a short series of questions about what you observed." Press SPACE → questionnaire battery starts.

### `end_of_session.txt`
Single screen after the third block: "You have completed all three experimental blocks. A final short questionnaire will now ask you to compare the three forms..."

### `panels/F1/` — 27 files (9 events × 3 blocks)
Verbose status panels. Each one names *every* scale + light, in-range or out-of-range, with numbers.

Example (`panels/F1/block_A_event_05.txt`, a miss):
> *Cycle 05 (auto-aid) — Scale-1: was 47.0 > upper bound 45.0, **auto-aid not engaged**. Scale-2: 31.5, in range. ...*

The phrase "auto-aid not engaged" is the F1 way of telling the participant the automation skipped this one — embedded in routine prose, no salience boost. Whether the participant *extracts* that fact under multitasking load is precisely what the experiment measures.

### `panels/F2/` — 12 files (4 events × 3 blocks)
Files exist for events 3, 5, 7, 8 — exactly the events at which the F2 scenarios fire a panel. Wording is short and contrastive.

Examples:
> *Reset scale-1 — would have failed in ~2.5 s.* (near-miss)
> *Skipped scale-1 — auto-aid did not act.* (miss)

### `panels/F3/` — 12 files (same indices as F2)
F3 panels are identical to F2 *except* on misses, where they append the actionable cue:

> *Skipped scale-2 — auto-aid did not act. **Check it yourself.***

(Near-miss panels are the same as F2 — the actionable cue only attaches when the operator must intervene.)

---

## 6. Folder 3 — `questionnaires/study/` (5 .txt files)

These are slider questionnaires in OpenMATB's `genericscales` format. One line per question:

`id;question text;left-anchor/right-anchor;min/max/default`

Each line becomes one labelled slider on screen. The participant moves the slider, presses SPACE, and the value is logged to the session CSV.

### Per-block battery (fires after every block, in this order)

1. `mental_model_block_{A,B,C}.txt` — **the explicability DV**. 5 items per block, scenario-specific:
   - q1: how many gauges did the automation act on?
   - q2: how many events did it skip? (slider range 0–9, default 2 — matches the 9-event block with 2 expected misses)
   - q3: which pair of gauges was its responsibility? (anchored to the correct pair for that block)
   - q4: estimated reliability percentage (default 78, matching the 7-of-9 auto-aid hit rate)
   - q5: subjective predictability of automation behaviour
2. `subjective_transparency.txt` — **the paired subjective DV** (3 items, same across blocks): "the system told me what it was doing", "I understood why the system acted", and information-volume sufficiency.

The H1 dissociation hypothesis hinges on the pairing of (1) and (2): subjective transparency predicted highest under F1, objective mental-model accuracy predicted highest under F2/F3.

### End-of-session questionnaire (fires once, after block 3)

- `preference_debrief.txt` — 5 forced-choice items asking the participant which of F1/F2/F3 felt most informative, most useful, most trustworthy, least distracting, and would be self-chosen for a future task. Triangulates the objective DVs.

---

## 7. Chronological walk-through for participant P01

Concrete example. P01's order is F1-A → F2-B → F3-C.

| t (m:ss) | Screen / event |
|---|---|
| 0:00 | `briefing_practice.txt` — read keys, press SPACE |
| 0:00 → 3:00 | Practice MATB (no auto-aid). Mixed scale/light failures, 5 comms calls, 3 pump events. |
| 3:01 | `briefing_F1.txt` — "continuous status panel" |
| 3:01 → 8:01 | **Block 1 (F1-A)** — 9 scales-1/3 failures every 30 s; an F1 panel fires after every event. |
| 8:02 → 8:04 | `end_of_block` → `mental_model_block_A` → `subjective_transparency` |
| 8:07 | `briefing_F2.txt` |
| 8:07 → 13:07 | **Block 2 (F2-B)** — 9 lights-1/2 failures; panels only on events 3, 5, 7, 8. |
| 13:08 → 13:10 | Same battery, B-variant mental-model |
| 13:13 | `briefing_F3.txt` |
| 13:13 → 18:13 | **Block 3 (F3-C)** — 9 scales-2/4 failures; selective panels with the actionable cue on misses. |
| 18:14 → 18:16 | Same battery, C-variant mental-model |
| 18:19 → 18:20 | `end_of_session` → `preference_debrief` |
| 18:28 | All four MATB tasks stop. Session log written. |

Wall-clock total ≈ 20 min once the participant's questionnaire-reading time is added.

---

## 8. Quick reference: what to edit to change what

| Want to change... | Edit this... | Then... |
|---|---|---|
| Block length, event count, practice length, participant order | Constants at the top of `scenarios/study/_regenerate.py` | Re-run `python _regenerate.py` |
| Wording of the F1/F2/F3 briefings | `instructions/study/briefing_F{1,2,3}.txt` | No regeneration needed — the scenarios reference these by filename. |
| Exact panel text on any event | `instructions/study/panels/F{form}/block_{letter}_event_{NN}.txt` | No regeneration needed. |
| Mental-model probe items, subjective-transparency items, preference debrief items | The corresponding file in `questionnaires/study/` | No regeneration needed. |
| Final-session questionnaires order | `_regenerate.py`'s `render_final()` and `final_questionnaires.txt` if used standalone | Re-run regenerator. |

---

## 9. What is **not** in these folders

- **Dropped questionnaires.** Earlier drafts included NASA-TLX (workload), an engagement check, and the Madsen & Gregor trust scale. Per `Documents/Study_proposal.md`, the per-block battery is now just mental-model + subjective-transparency, and the end-of-session battery is just the preference debrief. NASA-TLX still ships with OpenMATB at `includes/questionnaires/nasatlx_en.txt` if you want to re-add it via `_regenerate.py`.
- The post-session **CSV log** is written by OpenMATB to `OpenMATB/sessions/<date>/`. The scenarios do not produce it directly; it's the platform's standard output.
