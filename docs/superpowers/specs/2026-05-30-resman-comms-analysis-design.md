# Resource-Management & Communications Performance Analysis — Design

**Date:** 2026-05-30
**Author:** Andrea Thelen (with Claude)
**Status:** Approved design, pending spec review

## 1. Purpose

Build a reusable analysis pipeline for the OpenMATB transparency study that
computes **resource-management** and **communications** task performance per
experimental block and compares the three explanation forms (F1/F2/F3). This is
the primary objective measure for **H4** ("saved attention is redeployed":
performance on the non-automated tasks is higher under F2/F3 than under F1).

The real participant dataset (P01–P10) does not exist yet — only pilot runs of
`full_P01` and a few single-block test sessions. This project is **preparation**:
the pipeline must be ready to run cleanly on the real data once collected, and is
demonstrated now on the available pilot logs.

## 2. Background: how performance is measured (literature)

Confirmed against the literature in `papers/` and the OpenMATB plugin source.
These citations are reproduced in the notebook itself (per requirement).

### Resource management
- **Cegarra et al. (2020), OpenMATB, *Behavior Research Methods* 52:1980–1990.**
  Performance on the resource-management task "can be interpreted in two ways…
  one can consider performance on the top two tanks as the RMS error over a given
  period." Target level = 2500 units for the two depleting tanks (A, B).
- **Santiago-Espada et al. (2011), The Multi-Attribute Task Battery II (MATB-II)
  User's Guide, NASA/TM-2011-217164.** Proposes a tolerance threshold (±500
  units) and computing the **proportion of time** the tank level stays within the
  band (2000–3000 units).
- **Comstock & Arnegard (1992), NASA TM-104174.** Original MATB; deviation of
  fuel-tank levels from target as the canonical resource-management measure.

Maps onto OpenMATB `resman` plugin logging: `a_deviation`/`b_deviation` (level −
target, sampled every `taskupdatetime` ≈ 2 s), `a_in_tolerance`/`b_in_tolerance`
(bool), and `{tank}_response_time` (duration of each out-of-tolerance excursion,
logged when the tank returns to tolerance).

### Communications
- **Cegarra et al. (2020).** The communications task represents ATC radio-frequency
  changes; participants respond to calls with their own call sign and ignore
  distractor call signs. Performance "is generally assessed in terms of response
  accuracy and response time." Ignoring distractors vs. responding to them maps
  onto a **signal-detection** framing (hits, misses, false alarms, correct
  rejections).

Maps onto OpenMATB `communications` plugin logging: `sdt_value` ∈ {HIT, MISS, FA,
BAD_RADIO, BAD_FREQ, BAD_RADIO_FREQ}, `response_time`, `response_deviation`
(frequency error), `correct_radio`, `response_was_needed`.

## 3. Study design recap (drives the analysis structure)

- Within-subjects; three explanation **forms** F1 (verbose/always-on), F2
  (selective + contrastive), F3 (selective + contrastive + actionable).
- Three **blocks** A/B/C use different gauge sets; Latin-square counterbalanced
  across P01–P10 (`PARTICIPANT_ORDERS` in `_regenerate.py`).
- One `full_PXX` session contains practice + three 5-min experimental blocks +
  questionnaires, all in a single CSV.
- The automation aid runs only on **system monitoring**. **Communications** and
  **resource management** are never aided — they are the H4 dependent tasks.

## 4. Architecture

New project at repository root: `analysis/`.

```
analysis/
├── pyproject.toml                uv project (Python >=3.12)
├── README.md                     how to run (uv sync; jupyter)
├── .gitignore                    __pycache__, .venv, .ipynb_checkpoints
├── matb_analysis/
│   ├── __init__.py
│   ├── discovery.py    find study sessions; read scenario_path; map session→participant/condition
│   ├── parsing.py      raw CSV → long DataFrame; segment into blocks; assign rows to blocks
│   ├── metrics_resman.py   per-block resman metrics
│   ├── metrics_comms.py     per-block communications metrics
│   └── aggregate.py    build tidy per-(participant, form, block) metrics table
├── notebooks/
│   └── 01_resman_comms_performance.ipynb
├── outputs/            exported tidy CSV + figures
└── tests/
    └── test_parsing.py   parsing/segmentation checks on pilot logs
```

**Rationale:** a small tested package + thin orchestrating notebook keeps parsing
logic reusable and unit-testable, directly serving the "pipeline ready before real
data" goal. The notebook imports the package and handles discovery → tables →
figures → narrative + citations.

## 5. Components

### discovery.py
- `find_study_sessions(sessions_dir) -> list[SessionInfo]`: walk
  `OpenMATB/sessions/*/*.csv`; read the `scenario_path` row; keep only sessions
  whose scenario is under `scenarios/study/` and excludes `practice`; skip empty/
  aborted files (below a minimum row count / missing task start events).
- Derive `participant` (`full_PXX` → `PXX`) or, for single-block test scenarios
  (`F1_block_A` etc.), a synthetic participant tag plus explicit (form, block).
- Returns session path, participant, scenario kind, and detected forms/blocks.

### parsing.py
- `load_raw(path) -> DataFrame`: read CSV with columns
  `logtime, scenario_time, type, module, address, value`; coerce types.
- `segment_blocks(df) -> list[Block]`: detect `instructions;filename;
  study/briefing_FX.txt` events as block starts; read form from the briefing file
  name and block letter from the subsequent `panels/{form}/block_{X}_…` (fallback:
  `mental_model_block_{X}` questionnaire, then participant order). Practice block
  excluded (no `briefing_FX`). Each block = a `scenario_time` interval
  `[start, next_start)`.
- `rows_for_block(df, block)`: select rows whose `scenario_time` falls in the
  block interval.

### metrics_resman.py
Per block, from `performance` rows (`a_deviation`, `b_deviation`,
`a_in_tolerance`, `b_in_tolerance`, `{tank}_response_time`):
- `rmsd_a`, `rmsd_b`, `rmsd_mean` — root-mean-square of deviation from target.
- `mad_a`, `mad_b` — mean absolute deviation.
- `pct_in_tolerance_a`, `pct_in_tolerance_b`, `pct_in_tolerance_mean` — fraction of
  sampled rows with `in_tolerance == 1`.
- `mean_excursion_sec`, `n_excursions` — from `{tank}_response_time` events.

### metrics_comms.py
Per block, from `performance` rows grouped by event (one event = the set of
`communications` performance rows sharing a `scenario_time`):
- `n_signal` (response_was_needed True), `n_distractor` (False).
- `n_hit`, `n_miss`, `n_fa`, plus error subtypes (`BAD_RADIO`, `BAD_FREQ`,
  `BAD_RADIO_FREQ`).
- `accuracy` = hits / signal trials; `miss_rate`; `fa_count`.
- `mean_rt_hit` — mean `response_time` (milliseconds) on **hits only** (correct
  radio + correct frequency). This is the latency from end-of-spoken-call to the
  validated response; misses are `nan` and excluded. Speed metric, reported
  alongside accuracy (Cegarra 2020: "response accuracy and response time").
- `mean_abs_freq_dev` — mean |`response_deviation`| on responded trials.

### aggregate.py
- `build_metrics_table(sessions) -> DataFrame`: one tidy row per (participant,
  form, block) with all resman + comms metric columns. This is the single
  artifact every figure/table consumes and is exported to `outputs/`.

### notebook 01_resman_comms_performance.ipynb
Sections:
1. **Intro + literature** — markdown citing Cegarra 2020, Santiago-Espada 2011,
   Comstock & Arnegard 1992, defining each metric and its source.
2. **Load** — call discovery + aggregate; show the tidy table.
3. **Resman descriptives + figures** — mean/median/SD by form; boxplots and
   bar-charts-with-error-bars for RMSD and % in tolerance.
4. **Comms descriptives + figures** — accuracy, RT, FA, freq deviation by form.
5. **Summary table** — all metrics by form, oriented to H4.
6. A clearly-labelled empty "Inferential tests (to add when N adequate)" stub.

## 6. Scope & non-goals

- **In scope:** resource management + communications metrics; descriptive stats +
  figures; reusable parser/discovery; demo on pilot data; literature citations in
  the notebook.
- **Out of scope (now):** scheduling and sysmon metrics; mental-model / trust /
  transparency questionnaire analysis; inferential statistics (Friedman/Wilcoxon/
  ANOVA) — left as a labelled stub for when N is adequate. Parser stays generic so
  these can be added later.

## 7. Decisions (from brainstorming)

- Data scope: **reusable pipeline + pilot demo** (preparation for real data).
- Statistics depth: **descriptives + figures only**, no p-values now.
- Code structure: **package + thin notebook**.
- Folder: `analysis/` at repository root; uv-managed; pandas/numpy/matplotlib/
  seaborn.
- Literature citations included in the notebook (added requirement).

## 8. Testing

- `tests/test_parsing.py`: on a known pilot log (`full_P01`), assert exactly 3
  experimental blocks detected with forms (F1,F2,F3) and blocks (A,B,C) in the
  order given by `PARTICIPANT_ORDERS["P01"]`; assert practice excluded; assert each
  block's row count > 0 and metric functions return finite values.
- Manual: notebook runs top-to-bottom on the current pilot data without error.
