# Form of Explanation — revised design (v2)

**Change vs. previous version:** the manipulation is now **wording-form only**. Information
content (events, relevant facts, panel frequency) is held **constant** across conditions.
*Selectivity is no longer a manipulated variable* — selecting fewer facts (by frequency or
by fact-count) necessarily removes information, which conflicts with the research gap. We
therefore isolate **contrastiveness** (how the same facts are framed) and **actionability**
(an added operator cue), holding everything else equal.

---

## Research question

**Main.** Under multitasking load, does the *linguistic form* of an automation aid's
explanation — holding information content constant — change subjective transparency and
whether the operator's mental model actually updates?

- **RQ1 (subjective).** Does form change subjective transparency (the *feeling* of being
  informed)? → **H1**
- **RQ2 (objective).** Does form change whether the operator's mental model actually
  updates (explicability)? → **H2**

*Trust* is measured only once, in the end-of-session debrief (forced choice), not as a
per-block scale — transparency is the primary subjective construct for the crossover.

*Novelty:* prior transparency work (Mercado 2016, Stowers 2017) varies the *amount/level*
of information. We hold content constant and vary only the form, isolating presentation.
XAI work (Wang & Yin 2021, Bansal 2021) shows the subjective/objective dissociation in
single-shot decisions; we test it under continuous multitasking load.

---

## Hypotheses

**H1, H2 are the load-bearing pair (the explainability ≠ explicability crossover).**

- **H1 — Verbose feels more transparent.** Subjective transparency is highest under the
  verbose form (F1), even though content is identical across forms.
- **H2 — Contrastive form improves explicability.** Post-block mental-model accuracy is
  highest under the contrastive forms (F2/F3). The opposite directions of H1 and H2 are the
  operational signature of explainability ≠ explicability.
- **H3 — Contrastive framing aids extraction (supporting).** Because the relevant fact is
  easier to read off a contrastive panel, participants (a) detect more automation **misses**
  and (b) make fewer unnecessary **overwrites** of correct aid actions under F2/F3 than F1.
  *(Reframed from "selectivity" — the mechanism is framing, not frequency.)*
- **H4 — Saved reading time is redeployed (supporting).** Performance on the non-aided
  tasks is higher under F2/F3 than F1, because less time is spent reading the panel.
- **Mechanism check (workload).** Subjective workload is higher under F1. This tests
  Rebecca's concern that F1's transparency rating could be confounded by feeling
  overwhelmed, and supplies the mediating step behind H2 and H4 (verbose → higher load →
  worse extraction and less spare capacity).

---

## Study setup

**Platform.** OpenMATB — four concurrent supervisory tasks (system monitoring,
communications, resource management, scheduling). The participant actively performs **all**
tasks. An automation aid runs **only** on system monitoring at **~78% reliability**; the
other three tasks are unaided and compete for attention.

**Aid is identical across all three forms** — same reliability, same failure timeline, same
event pattern. Only the panel wording differs.

**Design.** Within-subjects. Each participant runs all three forms (F1/F2/F3), each paired
with a different gauge set (A/B/C) so the mental-model probe cannot be answered by recall
from another block. Form order counterbalanced (Latin square). N ≈ 20.

**Session (~20 min).** 3 min practice → three 5 min blocks → questionnaires + final debrief.

**Per block: 9 events, one every 30 s.**

| Events | Kind | Aid behaviour | Panel fires? |
|--------|------|---------------|--------------|
| 5 | Routine | acts (in time) | yes — all forms |
| 2 | Near-miss | acts just in time | yes — all forms |
| 2 | **Miss** | does **not** act | yes — all forms |

→ 7 of 9 handled appropriately ≈ 78% reliability. **A panel fires on every event in every
form (9× per block), reporting the same relevant facts.** Only the wording differs.

**Content-constant rule (the design constraint).** For each event, the action-relevant
facts — which gauge, in/out of range, whether the aid acted, and (for near-misses)
time-to-failure — are **identical** in F1, F2, and F3. The verbose form only adds
grammatical scaffolding and redundant exact sensor values; it introduces **no new
action-relevant fact**. Audit every F1/F2/F3 triplet against this rule before running.

---

## Wording examples (same facts, different form)

**Routine** (aid corrected a drifting gauge):
- **F1:** "Cycle 02 — Scale-3 reached 44.6, near the upper bound of 45.0. The automation
  adjusted it back to 30.1. Gauge now in range."
- **F2:** "Scale-3 corrected — aid kept it in range."
- **F3:** *(same as F2 — no cue; no operator action needed)*

**Near-miss** (aid acted just in time):
- **F1:** "Cycle 03 — Scale-1 rose to 46.8, above the upper bound of 45.0, for 0.8 s. The
  automation reset it to 32.0; without the reset it would have failed in ~2.5 s."
- **F2:** "Reset scale-1 — would have failed in ~2.5 s."
- **F3:** *(same as F2)*

**Miss** (aid did NOT act → operator must intervene):
- **F1:** "Cycle 05 — Scale-1 was 47.0, above the upper bound of 45.0. The automation did
  not engage on this gauge."
- **F2:** "Skipped scale-1 — aid did not act."
- **F3:** "Skipped scale-1 — aid did not act. **Check it yourself.**"

→ F1↔F2 isolates **contrastiveness**; F2↔F3 isolates **actionability** (cue attaches only
on misses).

---

## Questionnaires

All are OpenMATB slider/forced-choice scales. The **per-block battery** fires after each of
the three blocks (it pauses the MATB clock); the **debrief** fires once at the end. The
battery is deliberately lean (~9 items) so it doesn't itself become a load manipulation
between blocks. **Per-block trust and the full NASA-TLX have been dropped** — transparency
carries the subjective side of the crossover, trust is captured once in the debrief, and
workload is reduced to a single item.

### Per-block battery (after every block — administer in this order)

Order matters: probe **first** (capture the mental model before reflection contaminates it),
workload **last** (so rating effort doesn't colour the earlier answers).

**1. Mental-model probe — objective explicability DV (H2).** 5 sliders (3 calibration + 2
recognition). MATB's `genericscales` allow **no number entry** — each answer is a *position
between two verbal anchors*, scored against the block's true value. "Indicators" = the system-monitoring
**gauges *and* lights** (block A = scales, B = lights, C = scales), so wording is
indicator-neutral and can't be answered from another block.
- q1 *(misses)*: "How often did the automation fail to step in when an indicator needed
  attention?" — anchors *never ↔ on most events*; truth ≈ 2 of ~9.
- q2 *(close calls)*: "How often did the automation step in only just in time (a close
  call)?" — anchors *never ↔ on most events*; truth ≈ 2 of ~9.
- q3 *(reliability)*: "Overall, how reliable was the automation this block?" — anchors *not
  at all reliable ↔ completely reliable*; truth ≈ 78%.
- q4 *(recognition)*: "Did the automation act on [indicator X] at any point this block?" —
  slider *No ↔ Yes*; scored against ground truth.
- q5 *(recognition)*: "Did the automation act on [indicator Y] at any point this block?" —
  same format.

  **Balancing across the three blocks** (one combination per block, *tied to the block, not
  the form* — because blocks are crossed with forms via the Latin square, every form meets
  every combination equally, with **no confound** between condition and the recognition
  answer). A "Yes" is realised by probing an indicator **in** that block's set (the aid
  acted on it at least once); a "No" by probing an indicator **not** in that block's set (it
  never needed action, so the aid never acted on it). As implemented:

  | Block | Set | q4 / q5 probed | Correct answers |
  |-------|-----|----------------|-----------------|
  | A | scales-1, scales-3 | Scale 1, Scale 3 | **Yes / Yes** |
  | B | lights-1, lights-2 | Warning light 2, Scale 1 | **Yes / No** |
  | C | scales-2, scales-4 | Warning light 1, Warning light 2 | **No / No** |

  This also kills a "the aid always acts" response bias: a participant who isn't tracking
  can't score well by answering uniformly. *(Note: with exactly 2 misses on a 2-indicator
  set, "both acted (Yes/Yes)" cannot be made clean from misses alone — an in-set indicator
  that was missed was still acted on earlier — so Yes/No/No-combinations are realised via
  in-set vs. out-of-set indicators as above.)*

*Scoring:* for q1–q3, explicability accuracy = mean absolute deviation of slider position
from the true value (lower = better-calibrated mental model); q1 and q3 are related (both
calibration to the aid's error rate) and can be averaged, while q2 taps the just-in-time
saves (which F1/F2 frame very differently). For q4–q5, score proportion correct (or signed
confidence toward the correct pole) — the most direct test of whether the participant
tracked *which specific indicators* the aid touched.

*Ground truth per block (for offline scoring; MATB slider files cannot store the key):*
misses = 2 of 9, close calls (near-misses) = 2 of 9, reliability ≈ 78%; recognition answers
per the table above.

**2. Subjective transparency — H1 (the subjective half of the crossover).** 3 sliders
(strongly disagree ↔ strongly agree):
- "The system told me what it was doing."
- "I could easily keep track of what the automation was doing."
- "The amount of information felt about right."

**3. Workload — single-item mechanism check.** One slider (Paas-style mental-effort rating):
- "How mentally demanding / overwhelmed did you feel during this block?" *(very low ↔ very high)*

A single item is enough: within-subjects, we only need the *direction* (is F1 higher load?),
not the 6-way NASA-TLX decomposition. Declared a priori as a mediation check.

> Pairing logic: **(2) captures the *feeling* of being informed; (1) captures *actual*
> understanding.** The H1↔H2 crossover is the divergence between them. (3) lets us check
> whether any F1 transparency effect is confounded by overload, and mediates the F1→H2/H4
> path.

### End-of-session debrief (once, after block 3)

**Preference debrief.** 5 forced-choice items asking which of F1/F2/F3 felt **most
informative**, **most useful**, **most trustworthy**, **least distracting**, and **would be
self-chosen** for a future task. This is the **only** place trust is measured, and fires
just once, so it adds negligible load while triangulating the objective DVs.

### Notes
- Total per block ≈ **9 items** (5 + 3 + 1), repeated 3×.
- Reverse-score at least one transparency item to detect straight-lining at N≈20.
- Slider defaults should be neutral/mid-scale, **not** the correct value, so they don't anchor
  the mental-model answers.

---

## Measures (each maps to one hypothesis)

| Measure | Source | Hypothesis |
|---------|--------|-----------|
| Mental-model probe (5 sliders: 3 calibration + 2 recognition, vs. ground truth) → objective explicability score | Questionnaire / block | **H2** (objective half of H1 crossover) |
| Subjective transparency (3 items) | Questionnaire / block | **H1** |
| Subjective workload (single item) | Questionnaire / block | mechanism for H1, H2, H4 |
| Miss detection: hit/miss + reaction time | Platform log | **H3a** |
| Unnecessary overwrites of correct aid actions | Platform log | **H3b** |
| Non-aided task performance (comms, resource mgmt, scheduling) | Platform log | **H4** |
| Preference debrief (forced choice: most informative / useful / trustworthy / least distracting / self-chosen) | Questionnaire / end | triangulation |

---

## Analysis ideas

- **Within-subject omnibus per DV:** repeated-measures ANOVA across F1/F2/F3 (or Friedman if
  non-normal / small N). Then **planned contrasts**: F1 vs {F2, F3} = the form (contrastive)
  effect; F2 vs F3 = the actionability effect.
- **The H1×H2 dissociation (the core test):** fit a mixed model with **form × measure-type**
  (subjective transparency vs. objective accuracy, z-scored to a common scale). A significant
  *interaction* in opposite directions is the crossover. Reporting both main effects with the
  interaction is cleaner than two separate tests.
- **Mixed-effects models** preferred over ANOVA at N≈20: random intercept per participant
  (and per gauge set) handles the within-subject structure and counterbalancing; include
  **block order** as a covariate to absorb learning effects.
- **Effect sizes + confidence intervals** throughout, given small N. Pre-register H1/H2 as
  confirmatory; treat **H3/H4 as exploratory** (few miss trials per block → low power).
- **Workload mediation:** test whether the single-item workload measure mediates the
  form→transparency (H1), form→mental-model (H2), and form→non-aided-performance (H4)
  relationships — directly answers the "is F1's transparency rating just overwhelm?" question.
- **Detection sensitivity:** if feasible, summarise miss-detection as hit-rate (and RT) per
  form; pool the 6 misses per participant (2 × 3 blocks) to stabilise the estimate.

---

## Limitations (state up front)

- Wording-only is a **subtle** manipulation; effects may be small at N≈20 (within-subjects
  and the workload measure help). Honest trade: *novel but subtle* over *strong but
  unoriginal* (a frequency change would re-introduce the amount-of-information confound and
  close the research gap).
- Load held at a single moderate level — no generalisation across load levels.
- Few misses per block (2) → H3 statistics are fragile; exploratory.
