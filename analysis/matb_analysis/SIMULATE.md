# Simulated session-log generator (`simulate.py`)

Generates realistic OpenMATB study session logs for **developing and validating the
analysis code** — without running OpenMATB or collecting participants. It reads one real
session CSV as a structural *template* and re-emits it once per participant (P01–P20), so the
`matb_analysis` pipeline can be exercised on a full counterbalanced cohort with **known
ground truth**.

> Source: `analysis/matb_analysis/simulate.py`
> Template: `analysis/session_logs/26_260602_190745.csv` (real pilot, participant P03)
> Default output: `analysis/session_logs/simulated/`

---

## Quick start

```bash
cd analysis

# Generate the full 20-participant cohort and print a validation + effects report
uv run python -m matb_analysis.simulate --n 20 --self-check

# Neutral data with no systematic F1/F2/F3 differences (for null/parser testing)
uv run python -m matb_analysis.simulate --n 20 --no-effects

# Custom seed / output location / count
uv run python -m matb_analysis.simulate --n 6 --seed 42 --out /tmp/sim
```

### CLI options

| Flag | Default | Meaning |
|------|---------|---------|
| `--template` | the P03 pilot CSV | Real session log used as the structural template. |
| `--out` | `session_logs/simulated` | Output directory (created if missing). |
| `--n` | `20` | Number of participants (P01…P`n`, capped at the 20 defined orders). |
| `--seed` | `0` | Master RNG seed; fully reproducible per seed. |
| `--no-effects` | off | Collapse all form effects → neutral data (forms statistically identical). |
| `--self-check` | off | After writing, validate the cohort and print form-wise metric means. |

Output files are named `sim_P##_<stamp>.csv`. The participant is read by the pipeline from
the `scenario_path` row (`full_P##`), **not** the filename, so the name is cosmetic.

---

## What the script does

Taken literally, it produces *"randomly modified versions of the example,"* at full fidelity.

1. **Parse the template** into a header (everything up to the first form briefing), three
   **block segments** keyed by block letter (A/B/C), and a footer (`end_of_session` +
   `preference_debrief`).

2. **Reorder + retarget per participant.** Each participant runs the three segments in their
   Latin-square order from `study_design.PARTICIPANT_ORDERS`. This works because of the
   study's content-constant design:
   - A block's **content depends only on its letter** — gauges (A=scales-1/3, B=lights-1/2,
     C=scales-2/4), `-failure` events, the `automaticsolver` skip pattern, the
     `mental_model_block_X` probe and its `rec_*` sliders.
   - The **form** (F1/F2/F3) only changes the `briefing_F#` and `panels/F#/...` path tokens.

   So each letter-segment is time-shifted into its slot and its form tokens are
   string-substituted to the target form.

3. **Re-sample only the analysis-relevant rows** from an effects model (below). Everything
   else — the ~80k bulk `state` (200 ms sysmon samples), `aoi`, `seed_*`, `parameter` rows —
   is copied verbatim with shifted timestamps, so each file matches a real log's size and
   shape.

4. **Regenerate header tokens**: new `scenario_path` participant id, fresh communications
   callsigns/frequencies, and a per-participant absolute clock offset.

### Rows that get re-sampled

| Rows | Drives |
|------|--------|
| `performance \| sysmon` (`signal_detection`, `response_time`) + `event \| sysmon \| automaticsolver` | H3a miss detection, H3b overwrites |
| `performance \| genericscales` (`MM_*_q_*`, `MM_*_rec_*`, `Subjective_*`, `Workload_overall`) | H1 transparency, H2 mental model, workload |
| `performance \| genericscales` (`PREF_q1..q5_*`, in the footer) | preference debrief |
| `performance \| communications` (`sdt_value`, `response_time`, `response_deviation`, `correct_radio`) | H4 comms performance |
| `performance \| resman` (`a_deviation`, `b_deviation`, `a_in_tolerance`, `b_in_tolerance`) | H4 resman tracking |

---

## Embedded effects model

The `EFFECTS` dict at the top of `simulate.py` is the single place to tune effect sizes. Each
construct has a baseline, a per-form delta, within-form noise (`sd`), and a per-participant
random-effect SD (`p_sd`, shared across that participant's blocks for realistic
within-subject correlation). With `--no-effects` only the baselines are used.

The embedded directions mirror the study hypotheses:

| Construct | Direction | Hypothesis |
|-----------|-----------|------------|
| Subjective transparency (1–7) | **F1 highest** (verbose feels most informed) | H1 |
| Workload (1–7) | **F1 highest** | mechanism check |
| Mental-model accuracy (calibration + recognition) | **F2/F3 better** | H2 |
| Miss detection rate / RT | **F2/F3 better / faster** | H3a |
| Overwrites of correct aid actions | **F1 highest** | H3b |
| Comms accuracy / RT, resman tracking error | **F2/F3 better** | H4 |

The H1↔H2 opposite directions (F1 feels most transparent yet F2/F3 yield the more accurate
mental model) are the explainability ≠ explicability crossover the study targets.

Scales used: transparency/workload 1–7; mental-model `q_misses`/`q_closecalls` 0–9 (truth 2);
`q_reliability` 0–100 (truth ≈ 78); recognition sliders 0–100 (threshold 50). The reverse-keyed
`Subjective_keep_track` item is emitted reversed (high transparency → low logged value) to
match how `metrics_questionnaire.py` reverse-scores it.

---

## How it ties into the analysis pipeline

The output is auto-discovered by `matb_analysis`:

```python
from matb_analysis.discovery import find_study_sessions
from matb_analysis.validation import validate_sessions
from matb_analysis.aggregate import build_metrics_table

sessions = find_study_sessions("session_logs/simulated")   # isolate the simulated cohort
validate_sessions(sessions)        # all 20 should be ok
build_metrics_table(sessions)      # one tidy row per (participant, form, block)
```

> **Note on discovery scope.** The pipeline's default `find_study_sessions()` searches
> `session_logs/` **recursively**, so by default it picks up the 20 simulated sessions *and*
> the real P03 log together. To analyse only one set, pass an explicit path as above.

---

## Verification (what was checked)

- `uv run pytest -q` → all tests pass, including `tests/test_simulate.py`.
- All 20 generated sessions pass `validate_sessions` (briefing form = panel form =
  gauge-derived block letter; realised order = each participant's `PARTICIPANT_ORDERS` row).
- Each file is **81,553 rows / ~4.4 MB** with the same per-type row composition as the real
  log, and monotone `scenario_time`.
- Form-wise metric means recover every embedded effect, e.g. for N=20, seed 0:

  | form | subj_transparency | workload | mm_explicability | detection_rate | overwrite_rate | accuracy | rmsd_mean |
  |------|------|------|------|------|------|------|------|
  | F1 | 5.51 | 5.41 | 0.73 | 0.50 | 0.093 | 0.57 | 428.5 |
  | F2 | 4.44 | 4.24 | 0.90 | 0.83 | 0.036 | 0.91 | 300.0 |
  | F3 | 4.48 | 4.49 | 0.89 | 0.90 | 0.029 | 0.79 | 293.3 |

  (Exact numbers depend on `--seed` and `--n`.)

---

## Limitation

The low-level `state` and `input` rows keep the **template's** behaviour and are *not*
re-derived to match each re-sampled outcome (e.g. a re-sampled detected miss is not backed by
a matching key-press/gauge-reset trajectory). The analysis metrics read the `performance`
rows, so the output is **analysis-faithful but not a physically-consistent replay**. If a
future metric starts reading raw `state`/`input` rows, that path would need to be re-sampled
too.

---

## Files

- `simulate.py` — the generator (importable module + `python -m matb_analysis.simulate` CLI).
- `tests/test_simulate.py` — generates a small cohort to a tmp dir and asserts it validates
  and that the effect directions hold (plus a flat `--no-effects` check).
