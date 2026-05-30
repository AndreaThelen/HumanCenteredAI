# OpenMATB resman & communications performance analysis

Computes resource-management and communications task performance per experimental
block and compares the three explanation forms (F1/F2/F3) for hypothesis H4
(saved attention is redeployed: performance on the non-automated tasks is higher
under F2/F3 than under F1).

## Setup

```bash
cd analysis
uv sync
```

## Run the analysis

```bash
uv run jupyter lab    # open notebooks/01_resman_comms_performance.ipynb
```

Or execute headless:

```bash
uv run jupyter nbconvert --to notebook --execute --inplace \
    notebooks/01_resman_comms_performance.ipynb
```

Outputs (tidy table + figures) are written to `outputs/` (gitignored).

## Tests

```bash
uv run pytest -q
```

## Metrics (literature)

- **Resman:** RMSD of tanks A/B from the 2500 target; % time in tolerance (±500).
  Cegarra et al. (2020); Santiago-Espada et al. (2011); Comstock & Arnegard (1992).
- **Comms:** response accuracy (hits ÷ signal trials) and response time on hits
  (ms), in a signal-detection framing. Cegarra et al. (2020).
- **Sysmon (H3):** detection rate + reaction time on aid-skipped events, and
  overwrite rate + false alarms on aid-handled events (aid vs. user separated via
  the `automaticsolver` state). Comstock & Arnegard (1992); Santiago-Espada et al.
  (2011); SAT/agent-transparency framing from Chen et al. (2014), Mercado et al.
  (2016), Stowers et al. (2017).
- **Questionnaires (H1/H2):** subjective transparency & trust (1–7), and an
  objective mental-model score vs. ground truth (set-ID accuracy, miss-count &
  reliability error, composite explicability). Chen et al. (2014), Mercado et al.
  (2016), Stowers et al. (2017), Miller (2019), Wang & Yin (2021), Jian et al. (2000).

## Adding data

Put the session logs you want analysed into **`session_logs/`** (this folder).
Only `.csv` files placed there are read — copy the relevant runs from
`../OpenMATB/sessions/<date>/`. The search is recursive, so a flat layout or the
original date subfolders both work. To analyse a different location instead, pass
it explicitly: `find_study_sessions(r"D:\path\to\logs")`.

## How it works

The pipeline auto-discovers study sessions under `session_logs/`, keeps only those
whose scenario is under `scenarios/study/`, segments each into its experimental
blocks (F1/F2/F3 × A/B/C), and computes one tidy row of metrics per
(participant, form, block). It runs unchanged as more participant data (P01–P10)
is collected.

Everything is read from the logs themselves — the participant from the
`scenario_path` row, the form of each block from its briefing event, and the
block/gauge set from the panel paths (with the failed sysmon gauges as an
independent fallback). The scenario `.txt` files are never opened.

**Validation.** `validate_sessions()` cross-checks each session: briefing form vs.
panel form, panel block vs. the gauges that actually failed, and the realised
(form, block) order vs. the participant's Latin-square row (embedded in
`study_design.py`). The notebook surfaces this as a per-session ✅/❌ report so a
mislabelled or aborted session is flagged rather than silently analysed.

## Layout

- `matb_analysis/` — importable, tested package:
  - `discovery.py` — find study sessions, map to participant/condition
  - `parsing.py` — load CSV logs, segment into blocks
  - `metrics_resman.py` — resource-management metrics
  - `metrics_comms.py` — communications metrics
  - `metrics_sysmon.py` — system-monitoring metrics (H3: detection, overwrites)
  - `metrics_questionnaire.py` — transparency/trust (H1) & mental-model (H2)
  - `aggregate.py` — assemble the tidy per-block table
  - `validation.py` — cross-check each session against the study design
  - `study_design.py` — embedded Latin-square orders and gauge→block map
- `notebooks/01_resman_comms_performance.ipynb` — H4: non-automated task performance
- `notebooks/02_sysmon_detection_overwrite.ipynb` — H3: miss detection & aid overwrites
- `notebooks/03_questionnaires.ipynb` — H1/H2: transparency, trust, mental-model, debrief
- `session_logs/` — curated input logs (only these are analysed)
- `tests/` — pytest unit + integration tests
- `outputs/` — generated CSVs and figures (gitignored)
