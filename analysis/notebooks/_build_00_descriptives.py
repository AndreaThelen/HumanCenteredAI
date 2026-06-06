"""Builder for 00_descriptives_by_hypothesis.ipynb.

Run once to (re)generate the notebook. Kept in the repo so the notebook's
structure is reviewable as plain Python; the .ipynb is the artefact that ships.
"""
from pathlib import Path
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []
def md(src): cells.append(nbf.v4.new_markdown_cell(src))
def code(src): cells.append(nbf.v4.new_code_cell(src))

# ---------------------------------------------------------------- title
md(r"""# Complete descriptive analysis — by hypothesis

OpenMATB transparency study (revised, *wording-only* design). This notebook is the
**single entry point** for the study's descriptive statistics: it loads every
session, builds the tidy per-(participant, form, block) metrics table, and walks
each hypothesis in turn, reporting form-wise means / medians / spreads and the
matching plots.

> **Scope.** *Descriptive only* — group means, dispersion, and distribution plots
> across the three explanation forms (F1 / F2 / F3). Inferential modelling
> (mixed-effects, planned contrasts, the H1×H2 crossover test, workload mediation)
> is deliberately deferred to a later notebook; the tidy table written here is its
> input.

## The manipulation in one line
Information **content** is held constant across F1/F2/F3; only the **linguistic
form** of the aid's explanation changes. F1 = verbose, F2 = contrastive,
F3 = contrastive + actionability cue.

## Hypotheses (and predicted direction across forms)

| H | Construct | Metric(s) | Predicted | Section |
|---|-----------|-----------|-----------|---------|
| **H1** | Subjective transparency (the *feeling*) | `subj_transparency` | **F1 highest** | [§2](#h1) |
| *mech.* | Workload (overwhelm check) | `workload` | **F1 highest** | [§3](#mech) |
| **H2** | Mental-model accuracy (explicability) | `mm_explicability` & parts | **F2/F3 best** | [§4](#h2) |
| — | H1×H2 crossover (descriptive preview) | z(transparency) vs z(explicability) | **opposite** | [§5](#crossover) |
| **H3a** | Miss detection | `detection_rate`, `mean_detect_rt` | **F2/F3 better/faster** | [§6](#h3) |
| **H3b** | Overwrites of correct aid actions | `overwrite_rate` | **F1 highest** | [§6](#h3) |
| **H4** | Non-aided task performance | resman + comms | **F2/F3 better** | [§7](#h4) |
| — | Preference debrief (triangulation) | `PREF_*` | — | [§8](#pref) |

The **H1↔H2 opposition** (F1 feels most transparent yet F2/F3 give the more
accurate mental model) is the explainability ≠ explicability crossover the study
targets.
""")

# ---------------------------------------------------------------- setup
md("""## 0. Setup""")
code("""import sys
from pathlib import Path

# Make the matb_analysis package importable when running from notebooks/.
sys.path.insert(0, str(Path.cwd().parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from matb_analysis.discovery import find_study_sessions
from matb_analysis.validation import validate_sessions
from matb_analysis.aggregate import build_metrics_table, build_debrief_table

sns.set_theme(style="whitegrid")
pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 60)

FORM_ORDER = ["F1", "F2", "F3"]
FORM_PALETTE = dict(zip(FORM_ORDER, sns.color_palette("Set2", 3)))

OUT = Path.cwd().parent / "outputs"
OUT.mkdir(exist_ok=True)

# Analyse the full simulated cohort (N=20, known ground truth). Point this at
# `session_logs` (the default) once real participants are collected, or leave it
# to fold the real pilot in alongside the simulated set.
DATA_DIR = Path.cwd().parent / "session_logs" / "simulated"
""")

# ---------------------------------------------------------------- helpers
md("""### Reusable descriptive helpers
`describe_by_form` returns a mean / median / SD / n table for any metric columns;
`box_by_form` draws one box-+-strip panel per column. Every section below is built
from these two, so the reporting style is identical throughout.""")
code('''def describe_by_form(df, cols, order=FORM_ORDER):
    """Form-wise mean / median / SD / n for the given metric columns (tidy long)."""
    g = df.groupby("form")
    out = []
    for c in cols:
        s = g[c]
        d = pd.DataFrame({"mean": s.mean(), "median": s.median(),
                          "sd": s.std(), "n": s.count()}).reindex(order)
        d.insert(0, "metric", c)
        out.append(d.reset_index())
    return (pd.concat(out, ignore_index=True)
              .set_index(["metric", "form"]).round(3))


def box_by_form(df, cols, titles=None, order=FORM_ORDER, ncols=2, save=None):
    """One box+strip panel per column, coloured by form."""
    titles = titles or cols
    n = len(cols)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(6.0 * ncols, 4.0 * nrows))
    axes = np.atleast_1d(axes).ravel()
    for ax, col, title in zip(axes, cols, titles):
        sns.boxplot(data=df, x="form", y=col, order=order, hue="form",
                    palette=FORM_PALETTE, legend=False, width=0.6, ax=ax)
        sns.stripplot(data=df, x="form", y=col, order=order, color="0.2",
                      size=3, alpha=0.6, ax=ax)
        ax.set_title(title)
        ax.set_xlabel("")
    for ax in axes[n:]:
        ax.set_visible(False)
    fig.tight_layout()
    if save:
        fig.savefig(OUT / save, dpi=150, bbox_inches="tight")
    plt.show()
''')

# ---------------------------------------------------------------- load
md("""## 1. Load sessions, validate, build the metrics table""")
code('''sessions = find_study_sessions(DATA_DIR)
print(f"Reading logs from: {DATA_DIR}")
print(f"Discovered {len(sessions)} session(s).")
if not sessions:
    raise SystemExit("No sessions found. Generate the cohort with "
                     "`uv run python -m matb_analysis.simulate --n 20`, "
                     "or point DATA_DIR at session_logs/.")

table = build_metrics_table(sessions)
table.to_csv(OUT / "metrics_by_block.csv", index=False)
print(f"Metrics table: {table.shape[0]} rows x {table.shape[1]} cols "
      f"({table['participant'].nunique()} participants).")
table.head()''')

md("""### 1a. Validation — realised structure vs. study design
Every session is cross-checked: briefing form vs. panel form, panel block vs. the
gauges that actually failed, and the realised (form, block) order vs. the
participant's Latin-square row. Any `ok = False` row must be resolved before the
numbers below can be trusted.""")
code('''report = validate_sessions(sessions)
n_bad = int((~report["ok"]).sum()) if not report.empty else 0
print(f"{len(report)} session(s) validated; {n_bad} with issues.")
if n_bad:
    display(report[~report["ok"]][["session_file", "participant", "issues"]])
report.head()''')

md("""### 1b. Cohort & counterbalancing overview
Each form should appear once per participant, and the form×block crosstab should be
balanced by the Latin square (every form meets every gauge set roughly equally).""")
code('''n_part = table["participant"].nunique()
print(f"Participants: {n_part}")
print(f"Blocks per form:\\n{table['form'].value_counts().reindex(FORM_ORDER).to_string()}")
print("\\nform x block (counterbalancing):")
display(pd.crosstab(table["form"], table["block"]).reindex(FORM_ORDER))

# Sanity: exactly one block per (participant, form).
dup = table.groupby(["participant", "form"]).size()
print(f"\\n(participant, form) cells with !=1 block: {(dup != 1).sum()}")''')

# ---------------------------------------------------------------- H1
md('''<a id="h1"></a>
## 2. H1 — Subjective transparency  *(predict F1 highest)*

`subj_transparency` is the mean of three 1–7 agreement items (one reverse-keyed):
"the system told me what it was doing", "I could keep track", "the amount of
information felt about right". Higher = the explanation *feels* more transparent.
H1 predicts the verbose form **F1** feels most transparent even though content is
identical.''')
code('''display(describe_by_form(table, ["subj_transparency"]))
box_by_form(table, ["subj_transparency"],
            ["Subjective transparency (1-7, higher = feels more transparent)"],
            ncols=1, save="h1_transparency_by_form.png")''')

# ---------------------------------------------------------------- workload
md('''<a id="mech"></a>
## 3. Mechanism check — Workload  *(predict F1 highest)*

Single mental-effort item (1–7). Tests whether any F1 transparency advantage is
confounded by overload — the mediating step behind H2/H4. H1 and this should move
**together** (verbose → feels informed *and* feels demanding).''')
code('''display(describe_by_form(table, ["workload"]))
box_by_form(table, ["workload"],
            ["Workload (1-7, higher = more demanding)"],
            ncols=1, save="workload_by_form.png")''')

# ---------------------------------------------------------------- H2
md('''<a id="h2"></a>
## 4. H2 — Mental-model accuracy / explicability  *(predict F2/F3 best)*

The five-slider mental-model probe scored against each block's ground truth:

- `mm_explicability` — composite [0–1] accuracy (higher = better-calibrated model).
- `mm_misses_error`, `mm_closecalls_error` — abs. deviation of the count sliders
  from truth (2 each); **lower = better**.
- `mm_reliability_error` — abs. deviation from ~78 %; **lower = better**.
- `mm_rec_accuracy` — proportion of the two recognition items answered on the
  correct side; **higher = better**.

H2 predicts the contrastive forms **F2/F3** yield the more accurate model — the
*opposite* direction to H1.''')
code('''mm_cols = ["mm_explicability", "mm_rec_accuracy", "mm_misses_error",
           "mm_closecalls_error", "mm_reliability_error"]
display(describe_by_form(table, mm_cols))
box_by_form(table, mm_cols,
            ["Explicability composite (0-1, higher=better)",
             "Recognition accuracy (0-1, higher=better)",
             "Miss-count error (lower=better)",
             "Close-call-count error (lower=better)",
             "Reliability error, % pts (lower=better)"],
            ncols=2, save="h2_mentalmodel_by_form.png")''')

# ---------------------------------------------------------------- crossover
md('''<a id="crossover"></a>
## 5. The H1 × H2 crossover — descriptive preview

The study's core claim is a *dissociation*: the form that feels most transparent
(H1) is **not** the form that builds the most accurate mental model (H2). Plotting
both constructs z-scored to a common scale makes the opposing slopes visible.
*(Descriptive only — the formal form×measure-type interaction test comes later.)*''')
code('''z = table.copy()
z["z_transparency"] = (z["subj_transparency"] - z["subj_transparency"].mean()) / z["subj_transparency"].std()
z["z_explicability"] = (z["mm_explicability"] - z["mm_explicability"].mean()) / z["mm_explicability"].std()

cross = (z.groupby("form")[["z_transparency", "z_explicability"]]
           .mean().reindex(FORM_ORDER))
display(cross.round(3))

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.plot(cross.index, cross["z_transparency"], "o-", lw=2, label="Subjective transparency (H1)")
ax.plot(cross.index, cross["z_explicability"], "s--", lw=2, label="Mental-model accuracy (H2)")
ax.axhline(0, color="0.7", lw=0.8)
ax.set_ylabel("z-score (cohort mean = 0)")
ax.set_xlabel("Explanation form")
ax.set_title("Explainability ≠ explicability: opposing form effects")
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "h1xh2_crossover.png", dpi=150)
plt.show()''')

# ---------------------------------------------------------------- H3
md('''<a id="h3"></a>
## 6. H3 — System monitoring  *(H3a: F2/F3 detect more/faster; H3b: F1 overwrites more)*

From the aided sysmon task, split by the aid's `automaticsolver` state at each event:

- **H3a (aid-skipped misses).** `detection_rate` = fraction of aid misses the
  operator caught (higher = better); `mean_detect_rt` = RT on caught misses, ms
  (lower = better).
- **H3b (aid-handled events).** `overwrite_rate` = fraction of correct aid actions
  the operator pre-emptively overwrote (lower = better; H3 predicts F1 highest).
- `n_false_alarms` reported alongside.

> Few misses per block (2) → these estimates are fragile; treat as exploratory.''')
code('''h3_cols = ["detection_rate", "mean_detect_rt", "overwrite_rate", "n_false_alarms"]
display(describe_by_form(table, h3_cols))
box_by_form(table, h3_cols,
            ["Miss detection rate (H3a, higher=better)",
             "Detection RT, ms (H3a, lower=better)",
             "Overwrite rate (H3b, lower=better)",
             "False alarms (count)"],
            ncols=2, save="h3_sysmon_by_form.png")''')

# ---------------------------------------------------------------- H4
md('''<a id="h4"></a>
## 7. H4 — Non-aided task performance  *(predict F2/F3 better)*

If the contrastive forms are quicker to read, the saved attention should show up as
better performance on the three **unaided** tasks. Headline measures:

- **Resource management** — `rmsd_mean` (tank deviation from target, lower=better),
  `pct_in_tolerance_mean` (higher=better).
- **Communications** — `accuracy` (hits/signal, higher=better), `mean_rt_hit`
  (ms, lower=better).''')
code('''h4_cols = ["rmsd_mean", "pct_in_tolerance_mean", "accuracy", "mean_rt_hit"]
display(describe_by_form(table, h4_cols))
box_by_form(table, h4_cols,
            ["Resman RMSD from target (lower=better)",
             "Resman % time in tolerance (higher=better)",
             "Comms accuracy (higher=better)",
             "Comms RT on hits, ms (lower=better)"],
            ncols=2, save="h4_nonaided_by_form.png")''')

# ---------------------------------------------------------------- preference
md('''<a id="pref"></a>
## 8. Preference debrief — triangulation

Five end-of-session forced-choice items (logged once per participant): which form
felt **most informative**, **most useful**, **most trustworthy**, **least
distracting**, and **would be self-chosen**. This is the *only* place trust is
measured. Reported here as per-item response distributions across the cohort.''')
code('''debrief = build_debrief_table(sessions)
print(f"Debrief rows (participants reaching debrief): {len(debrief)}")
pref_cols = [c for c in debrief.columns if c.startswith("PREF_")]
if pref_cols:
    debrief.to_csv(OUT / "preference_debrief.csv", index=False)
    display(debrief[["participant", *pref_cols]].describe().round(2))
    # Per-item response distribution (forced-choice values across the cohort).
    dist = (debrief[pref_cols].apply(lambda s: s.value_counts())
                              .fillna(0).astype(int).sort_index())
    dist.index.name = "response_value"
    display(dist)
else:
    print("No preference-debrief items found in these sessions.")''')

# ---------------------------------------------------------------- summary
md('''## 9. Master summary — every headline metric by form

One row per form gathering the section headlines, for a single at-a-glance read of
all hypotheses. Saved to `outputs/summary_by_form.csv`. The ✓/✗ in the comments
maps each column to its predicted winner; confirm directions here, then move to the
inferential notebook for significance.''')
code('''summary_cols = [
    "subj_transparency", "workload",                                  # H1, mech
    "mm_explicability", "mm_rec_accuracy",                            # H2
    "detection_rate", "mean_detect_rt", "overwrite_rate",            # H3
    "rmsd_mean", "pct_in_tolerance_mean", "accuracy", "mean_rt_hit", # H4
]
summary = table.groupby("form")[summary_cols].mean().reindex(FORM_ORDER).round(2)
summary.to_csv(OUT / "summary_by_form.csv")
summary.T''')

md('''## 10. Next steps (inferential — separate notebook)

The tidy table written to `outputs/metrics_by_block.csv` is the input for the
confirmatory analysis:

- **Within-subject omnibus per DV** — repeated-measures ANOVA across F1/F2/F3
  (Friedman if non-normal / small N), then planned contrasts F1 vs {F2,F3}
  (contrastiveness) and F2 vs F3 (actionability).
- **The H1×H2 dissociation** — mixed model with **form × measure-type** (z-scored
  transparency vs. explicability); a significant interaction in opposite directions
  is the crossover.
- **Mixed-effects models** with random intercepts per participant (and gauge set),
  block order as a covariate for learning.
- **Workload mediation** of the form→transparency / →mental-model / →non-aided
  paths. Effect sizes + CIs throughout; H1/H2 confirmatory, H3/H4 exploratory.''')

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}
out_path = Path(__file__).resolve().parent / "00_descriptives_by_hypothesis.ipynb"
nbf.write(nb, out_path)
print(f"wrote {out_path}")
