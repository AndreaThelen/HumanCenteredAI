"""Build (and execute) the H3 detection-of-misses notebook.

Run from the analysis/ dir with the project venv:
    ./.venv/Scripts/python.exe notebooks/_build_H3_detection.py

Generates notebooks/H3_detection_of_misses.ipynb with outputs embedded, and
writes the H3 figures + summary CSV into analysis/outputs/. The notebook itself
is self-contained and can be re-run unchanged whenever new session logs are
added to analysis/session_logs/.
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

NB_DIR = Path(__file__).resolve().parent
NB_PATH = NB_DIR / "H3_detection_of_misses.ipynb"


def md(text: str) -> nbf.NotebookNode:
    return nbf.v4.new_markdown_cell(text.strip("\n"))


def code(text: str) -> nbf.NotebookNode:
    return nbf.v4.new_code_cell(text.strip("\n"))


cells: list[nbf.NotebookNode] = []

cells.append(md(r"""
# H3 — Detection of Automation Misses (F1 / F2 / F3)

OpenMATB transparency study (content-constant, *wording-only* design). This
notebook covers **only hypothesis H3** (a supporting hypothesis), as stated in
the report (`Documents/Report/main.tex`, §3 and §4.5.3):

> **H3 (contrastive framing aids extraction).** Because the action-relevant fact
> is easier to read off a contrastive panel, participants detect a **higher
> proportion of automation-missed events** under the contrastive forms
> **F2 / F3** than under the verbose form **F1**.

**Design (from the study, see `project_3_study.pdf`).**

| Role | Variable | Detail |
|------|----------|--------|
| Independent variable | Explanation **form** | F1 verbose · F2 contrastive · F3 contrastive + actionable. **Within-subjects** — each participant sees all three (Latin-square counterbalanced). |
| Primary DV | **Miss-detection rate** | Of the **2** events per block the aid *skipped*, the proportion the participant caught manually. Higher = better. |
| Secondary DV | **Detection reaction time** | Time (ms) from the aid's panel firing to the participant's click, for *caught* misses only. Lower = faster extraction. |

Both DVs are read directly from the continuous OpenMATB platform log — no
questionnaire is involved in H3.

We report **descriptive statistics and visualisations**; the closing section
states the statistical approach and the test that applies to this design.
"""))

cells.append(code(r"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from matb_analysis.aggregate import build_metrics_table
from matb_analysis.discovery import find_study_sessions, DEFAULT_SESSIONS_DIR
from matb_analysis.validation import validate_sessions

sns.set_theme(style="whitegrid")
FORM_ORDER = ["F1", "F2", "F3"]
FORM_LABELS = {"F1": "F1\nverbose", "F2": "F2\ncontrastive", "F3": "F3\n+actionable"}
OUT = Path.cwd().parent / "outputs"
OUT.mkdir(exist_ok=True)
"""))

cells.append(md(r"""
## 1. Load the sessions and build the H3 metrics table

`find_study_sessions()` reads every study session under `session_logs/`. Each
session contributes three rows (one per form). The H3 metrics are produced by
`build_metrics_table()`, which uses the `automaticsolver` state at each event to
identify aid-skipped events and scores a HIT on a skipped event as a manual
detection.
"""))

cells.append(code(r"""
sessions = find_study_sessions()
print(f"Reading logs from: {DEFAULT_SESSIONS_DIR}")
print(f"Discovered {len(sessions)} study session(s).")

table = build_metrics_table(sessions)
h3_cols = ["n_aid_miss_events", "n_detected", "detection_rate", "mean_detect_rt"]
table[["participant", "form", "block"] + h3_cols].sort_values(["participant", "form"]).reset_index(drop=True)
"""))

cells.append(md(r"""
### 1b. Sanity check: design realised as intended

Each session is cross-checked against the Latin-square design (form ↔ block order,
panel form vs. briefing). Every block should also show exactly **2 aid-miss
events** (`n_aid_miss_events == 2`); otherwise the detection rate's denominator is
off for that block.
"""))

cells.append(code(r"""
report = validate_sessions(sessions)
n_bad = int((~report["ok"]).sum()) if not report.empty else 0
print(f"{len(report)} session(s) validated; {n_bad} with design issues.")

miss_counts = table["n_aid_miss_events"].value_counts().sort_index()
print("\nn_aid_miss_events per block (should all be 2):")
print(miss_counts.to_string())
"""))

cells.append(md(r"""
## 2. Primary DV — miss-detection rate by form

Descriptive statistics of the detection rate (proportion of the 2 aid-missed
events caught) for each form. With only 2 misses per block the rate can take just
three values — **0, 0.5, or 1.0** — so we report the mean, SD, median and the
spread, and below we also show the full distribution of how many misses (0/1/2)
were caught.
"""))

cells.append(code(r"""
def describe(df, col):
    g = df.groupby("form")[col]
    out = pd.DataFrame({
        "n_blocks": g.size(),
        "mean": g.mean(),
        "sd": g.std(),
        "median": g.median(),
        "min": g.min(),
        "max": g.max(),
    }).reindex(FORM_ORDER).round(3)
    return out

det_desc = describe(table, "detection_rate")
det_desc
"""))

cells.append(md(r"""
**Figure 1 — distribution of miss-detection rate by form.** Box = median and
interquartile range; whiskers = range; each dot is one block. H3 predicts the
F2/F3 distributions to sit above F1 (higher = more misses caught).
"""))

cells.append(code(r"""
fig, ax = plt.subplots(figsize=(6, 4.2))
sns.boxplot(data=table, x="form", y="detection_rate", order=FORM_ORDER,
            color="#3b6e8f", width=0.55, ax=ax)
sns.stripplot(data=table, x="form", y="detection_rate", order=FORM_ORDER,
              color="black", alpha=0.5, size=4, jitter=0.18, ax=ax)
ax.set_ylim(-0.05, 1.05)
ax.set_xlabel("Explanation form")
ax.set_ylabel("Miss-detection rate")
ax.set_xticks(range(len(FORM_ORDER)))
ax.set_xticklabels([FORM_LABELS[f] for f in FORM_ORDER])
ax.set_title("H3: miss-detection rate by explanation form")
fig.tight_layout()
fig.savefig(OUT / "h3_detection_rate_by_form.png", dpi=150)
plt.show()
"""))

cells.append(md(r"""
**Figure 2 — within-subject view.** Each grey line is one participant across the
three forms; the thick line is the mean. Because the design is within-subjects,
this shows whether *individuals* tend to improve from F1 to F2/F3, not just the
group average.
"""))

cells.append(code(r"""
wide = table.pivot_table(index="participant", columns="form", values="detection_rate")
wide = wide.reindex(columns=FORM_ORDER)

fig, ax = plt.subplots(figsize=(6, 4.2))
x = np.arange(len(FORM_ORDER))
for _, row in wide.iterrows():
    ax.plot(x, row.values, color="grey", alpha=0.35, marker="o", markersize=3,
            linewidth=1)
ax.plot(x, wide.mean(axis=0).values, color="#b8412e", marker="o", markersize=7,
        linewidth=2.5, label="mean")
ax.set_xticks(x)
ax.set_xticklabels([FORM_LABELS[f] for f in FORM_ORDER])
ax.set_ylim(-0.05, 1.05)
ax.set_xlabel("Explanation form")
ax.set_ylabel("Miss-detection rate")
ax.set_title("H3: per-participant detection rate across forms")
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "h3_detection_rate_perparticipant.png", dpi=150)
plt.show()
"""))

cells.append(md(r"""
**Figure 3 — distribution of how many of the 2 misses were caught.** For each
form, the share of blocks in which the participant caught 0, 1, or 2 of the misses.
This unpacks the coarse detection-rate values directly.
"""))

cells.append(code(r"""
dist = (table.groupby("form")["n_detected"].value_counts(normalize=True)
        .rename("share").reset_index())
dist = dist.pivot(index="form", columns="n_detected", values="share").reindex(FORM_ORDER)
dist = dist.reindex(columns=[0, 1, 2]).fillna(0.0)

fig, ax = plt.subplots(figsize=(6.4, 4.2))
bottom = np.zeros(len(FORM_ORDER))
colors = {0: "#d9534f", 1: "#e8c468", 2: "#4f9d69"}
for k in [0, 1, 2]:
    vals = dist[k].values
    ax.bar([FORM_LABELS[f] for f in FORM_ORDER], vals, bottom=bottom,
           color=colors[k], label=f"{k} of 2 caught")
    bottom += vals
ax.set_ylabel("Share of blocks")
ax.set_xlabel("Explanation form")
ax.set_ylim(0, 1)
ax.set_title("H3: how many of the 2 aid-missed events were caught")
ax.legend(title="misses caught", bbox_to_anchor=(1.02, 1), loc="upper left")
fig.tight_layout()
fig.savefig(OUT / "h3_detection_distribution_by_form.png", dpi=150)
plt.show()
dist.round(3)
"""))

cells.append(md(r"""
## 3. Secondary DV — detection reaction time (exploratory)

For the misses that *were* caught, how quickly did the participant click after the
panel fired? Lower = faster extraction of the action-relevant fact, which is the
mechanism H3 proposes.

**Missing data.** A block in which the participant caught **no** misses has no
reaction time (`mean_detect_rt` is `NaN`). These are reported and excluded from the
RT summary — they are not zeros. This is most common under F1, by H3's own logic.
"""))

cells.append(code(r"""
n_blocks = table.groupby("form").size().reindex(FORM_ORDER)
n_missing_rt = table.assign(missing=table["mean_detect_rt"].isna()).groupby("form")["missing"].sum().reindex(FORM_ORDER)
missing_tbl = pd.DataFrame({"n_blocks": n_blocks, "blocks_without_RT": n_missing_rt,
                            "blocks_with_RT": n_blocks - n_missing_rt})
print("Reaction time is undefined for blocks where 0 misses were caught:")
print(missing_tbl.to_string())

rt_desc = describe(table.dropna(subset=["mean_detect_rt"]), "mean_detect_rt")
rt_desc
"""))

cells.append(md(r"""
**Figure 4 — detection reaction time by form (caught misses only).**
"""))

cells.append(code(r"""
rt = table.dropna(subset=["mean_detect_rt"])
fig, ax = plt.subplots(figsize=(6, 4.2))
sns.boxplot(data=rt, x="form", y="mean_detect_rt", order=FORM_ORDER,
            color="#3b6e8f", width=0.55, ax=ax)
sns.stripplot(data=rt, x="form", y="mean_detect_rt", order=FORM_ORDER,
              color="black", alpha=0.5, size=4, jitter=0.18, ax=ax)
ax.set_xlabel("Explanation form")
ax.set_ylabel("Detection reaction time (ms)")
ax.set_xticks(range(len(FORM_ORDER)))
ax.set_xticklabels([FORM_LABELS[f] for f in FORM_ORDER])
ax.set_title("H3 (exploratory): RT to catch a miss, ms (lower = faster)")
fig.tight_layout()
fig.savefig(OUT / "h3_detection_rt_by_form.png", dpi=150)
plt.show()
"""))

cells.append(md(r"""
## 4. Compact summary table

One row per form, suitable for the report. H3 predicts detection rate to rise and
reaction time to fall from F1 to F2/F3.
"""))

cells.append(code(r"""
summary = pd.DataFrame({
    "n_blocks": table.groupby("form").size(),
    "detection_rate_mean": table.groupby("form")["detection_rate"].mean(),
    "detection_rate_sd": table.groupby("form")["detection_rate"].std(),
    "detect_rt_ms_mean": table.groupby("form")["mean_detect_rt"].mean(),
    "detect_rt_ms_sd": table.groupby("form")["mean_detect_rt"].std(),
}).reindex(FORM_ORDER).round(2)
summary.to_csv(OUT / "h3_detection_summary_by_form.csv")
summary
"""))

cells.append(md(r"""
## 5. Statistical analysis — descriptive focus

We report **descriptive statistics and visualisations** rather than a single
significance test, for two reasons tied to the measure and the design:

1. **The measure is coarse.** With only 2 aid-missed events per block the
   detection rate can take just three values (0, 0.5, 1.0). The means and medians
   above, together with the per-participant trajectories (Fig. 2) and the
   0/1/2-caught distribution (Fig. 3), convey the pattern more faithfully than a
   single test statistic would.
2. **Deliberate, transparent inference.** The study brief cautions against
   over-interpreting modest sample sizes and against using unfamiliar tests, so we
   keep the inferential step explicit rather than reflexive.

**The test that fits this design.** Because the design is within-subjects with
three related conditions and the DV is a coarse, non-normal proportion, the
appropriate test is **non-parametric**: a **Friedman test** as the omnibus across
F1/F2/F3, followed by **Wilcoxon signed-rank** post-hoc tests for the two planned,
directional contrasts (F1 < F2 and F1 < F3), with a Holm correction and a
rank-biserial effect size. Reaction time (continuous) can be examined the same
way, or with a repeated-measures ANOVA if its assumptions (normality, sphericity)
hold. The tidy table built above is the ready input for that step.
"""))

nb = nbf.v4.new_notebook()
nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}

print("Executing notebook ...")
ep = ExecutePreprocessor(timeout=300, kernel_name="python3")
ep.preprocess(nb, {"metadata": {"path": str(NB_DIR)}})

with NB_PATH.open("w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"Wrote {NB_PATH}")
