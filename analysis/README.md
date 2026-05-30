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

## Layout

- `matb_analysis/` — importable, tested package:
  - `discovery.py` — find study sessions, map to participant/condition
  - `parsing.py` — load CSV logs, segment into blocks
  - `metrics_resman.py` — resource-management metrics
  - `metrics_comms.py` — communications metrics
  - `aggregate.py` — assemble the tidy per-block table
- `notebooks/01_resman_comms_performance.ipynb` — the analysis notebook
- `session_logs/` — curated input logs (only these are analysed)
- `tests/` — pytest unit + integration tests
- `outputs/` — generated CSVs and figures (gitignored)
