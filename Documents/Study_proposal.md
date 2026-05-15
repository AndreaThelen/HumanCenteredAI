# Explainability vs. Explicability under Multitasking Load

Does the form of an automation aid's reasoning explanation — holding information content constant — change whether the operator's mental model actually updates under multitasking load?

## Problem / research gap

When an AI system explains itself, the system produces an explanation, and (separately) the user's mental model of the system updates. The lecture calls these **explainability** and **explicability**, and they are not the same. The transparency literature has so far focused on *how much* information an aid provides, not on *how* it provides it. We want to focus on the effects of different forms of an explanation while holding the information content constant.

## Why it is relevant

The distinction matters wherever a human supervises an automated system — aviation, medical monitoring, autonomous driving aids. If an explanation is long and reads like a status log, the operator may feel informed without being able to predict the system's next action. That is precisely the failure mode the lecture warns against, and it has measurable consequences for detecting automation errors. 

## Relation to the lecture

The project is anchored in two lectures: **Transparency** (the three-gap model — operator's mental model ↔ AI's internal model ↔ ground truth — and the question of what level of information the aid should communicate: only its current state, or also its reasoning, or also its projections) and **Explainability & Explicability** (Miller's criteria of selectivity, contrastiveness, actionability). Supporting constructs come from **Human-Centered AI / Trustworthy AI** (Madsen & Gregor cognitive vs. affective trust), **Mental Models**, and **Human-in-the-Loop.**

## How the project differs from other work

Transparency studies in the supervisory-control literature (Mercado 2016, Stowers 2017\) vary the *level* of information — current state, reasoning, or projection — and therefore do not distinguish information content and presentation. Our design holds content constant (every condition communicates the aid's reasoning) and varies only the form, which isolates the form effect. The XAI literature (Wang & Yin 2021, Bansal 2021\) has shown explanations can raise trust without improving understanding, but only in one-shot decisions; we test the same dissociation under multitasking load.

## Research question

In a multitasking supervisory-control environment with an imperfect automation aid that communicates its reasoning, does the *form* of the explanation — varied along Miller's criteria of selectivity, contrastiveness, and actionability — produce measurable mental-model alignment and improved detection of automation errors, beyond what an equally informative but verbose, always-on explanation provides?

## Concept

Three explanation forms. All three communicate the aid's reasoning, with identical information content but different delivery:

* **F1 — Verbose / always-on.** A status panel fires every automation cycle in routine prose ("Scale-1 was 47.0 \> upper bound 45.0, auto-aid not engaged. Scale-2: 31.5, in range...").  
* **F2 — Selective \+ contrastive.** A panel fires only on near-misses and misses ("Reset scale-1 — would have failed in \~2.5 s." / "Skipped scale-2 — auto-aid did not act.").  
* **F3 — Selective \+ contrastive \+ actionable.** Same as F2 plus an explicit operator cue on misses ("Check it yourself.").

The verbose F1 stream contains every fact that F2 and F3 surface, embedded in routine status language. The comparison is therefore between forms of explanation, not between explanation and no explanation.

## Hypotheses

Four predictions, ordered from most to least important. H1 and H2 are the load-bearing pair; H3 and H4 are supporting.

### H1 — Perceived informativeness vs. actual understanding

* **Prediction.** Subjective transparency ("the system told me what it was doing") is highest under F1, while objective mental-model accuracy is highest under F2/F3. The crossover is the operational signature of explainability ≠ explicability.  
* **Reasoning.** More text on screen feels more informative even when the relevant facts are harder to extract. F1 maximises perceived informativeness; F2/F3 maximise actual extraction.  
* **What falsifies it.** Subjective and objective measures move together across forms.

### H2 — Form modulates explicability

* **Prediction.** Post-block mental-model accuracy is higher under F2/F3 than under F1, even with information content matched.  
* **Reasoning.** Selectivity and contrastive framing make the relevant facts easier to extract under multitasking load; participants cannot read all of F1's text and still attend to the other three tasks.  
* **What falsifies it.** Accuracy is flat across forms — content matters more than form.

### H3 — Selectivity directs attention to anomalies

* **Prediction.** Detection rate of automation-missed events is higher under F2/F3 than under F1, even though F1 announces those events too.  
* **Reasoning.** F1 embeds the miss announcement in routine status prose; F2/F3 fire it as its own panel.  
* **What falsifies it.** Detection rate is flat — once content is matched, selectivity offers no attentional advantage.

### H4 — Saved attention is redeployed

* **Prediction.** Performance on the non-automated tasks (communications, scheduling) is higher under F2/F3 than under F1.  
* **Reasoning.** Reading less in the automated subtask frees capacity for tasks the automation does not support.  
* **What falsifies it.** Non-automation performance is flat or worse — the saved capacity is consumed by extra monitoring of an aid that no longer narrates itself.

## Method

The platform is **OpenMATB**, a four-task supervisory simulator (system monitoring, communications, scheduling, resource management). The automation aid runs only on system monitoring at approximately 78% reliability; the remaining three tasks compete for the participant's attention. The design is **within-subjects**: each runs all three forms once on three different gauge sets, so the post-block memory probe cannot be answered by recall from another block. One session lasts approximately 20 minutes: 3 min practice, three 5 min experimental blocks, and a final questionnaire battery.

**What we measure.** Two kinds of measures: things the participant *tells* us (questionnaires after each block and at the end) and things the platform *records* (key presses, response times, hits and misses on each task). Each measure maps onto one or more of the hypotheses above.

* **Mental-model probe (questionnaire, after each block).** Five short slider questions about what the participant believes the automation actually did during that block — e.g. "how many gauges did it act on?", "how often did it skip a gauge that needed attention?", "what percentage of events did it handle correctly?" Compared against the ground truth from the scenario, this gives an objective score of how well the participant's understanding of the automation matches reality. This is the main measure for **H1** (paired with the next item) and **H2**.  
* **Subjective transparency (questionnaire, after each block).** Three ratings: "The system told me what it was doing", "I understood why the system acted or did not act", and "The amount of information felt about right". This captures the participant's *feeling* of being informed — which the literature suggests can diverge from objective understanding. Paired with the mental-model probe to test the H1 dissociation.  
* **Detection of automation misses (platform log).** Whenever the automation skips an event, the participant should catch it manually. We record whether they did (hit / miss) and how fast they responded (reaction time). Primary measure for **H3**.  
* **Performance on the non-automated tasks (platform log).** The communications task records whether each radio call was answered correctly and how quickly; the scheduling task records correct entries on a time-table. These are the tasks the automation does *not* help with, so they tell us whether reading less in the automation panel actually frees up attention elsewhere. Primary measure for **H4**.

**Considerations.** Content matching across F1/F2/F3 is the central design constraint — any leak invalidates the comparison. Load is held at a single moderate level; generalisation across load levels is a stated limitation.

