"""Tests for the simulated-session generator.

Generates a small cohort into a tmp dir and checks (a) every session validates
against its Latin-square order and (b) the embedded form effects are recovered by
the analysis pipeline.
"""
import pytest

from matb_analysis.simulate import DEFAULT_TEMPLATE, generate
from matb_analysis.discovery import find_study_sessions
from matb_analysis.validation import validate_sessions
from matb_analysis.aggregate import build_metrics_table

pytestmark = pytest.mark.skipif(
    not DEFAULT_TEMPLATE.exists(),
    reason="template example log not present",
)

N = 12


@pytest.fixture(scope="module")
def cohort(tmp_path_factory):
    out = tmp_path_factory.mktemp("sim")
    generate(DEFAULT_TEMPLATE, out, n=N, seed=1, embed_effects=True)
    return find_study_sessions(out)


def test_generates_requested_cohort(cohort):
    assert len(cohort) == N
    assert all(s.scenario_kind == "full" for s in cohort)


def test_all_sessions_validate(cohort):
    report = validate_sessions(cohort)
    bad = report[~report["ok"]]
    assert bad.empty, bad.to_string(index=False)


def test_structure_matches_real_log(cohort):
    import csv
    real = list(csv.DictReader(DEFAULT_TEMPLATE.open(newline="", encoding="utf-8")))
    sim = list(csv.DictReader(cohort[0].path.open(newline="", encoding="utf-8")))
    # Same overall shape: identical row count and per-type composition.
    import collections
    rt = lambda rows: collections.Counter(r["type"] for r in rows)
    assert len(sim) == len(real)
    assert rt(sim) == rt(real)


def test_effects_recovered(cohort):
    table = build_metrics_table(cohort)
    means = table.groupby("form").mean(numeric_only=True)
    # H1: verbose F1 feels most transparent and most effortful.
    assert means.loc["F1", "subj_transparency"] > means.loc["F2", "subj_transparency"]
    assert means.loc["F1", "subj_transparency"] > means.loc["F3", "subj_transparency"]
    assert means.loc["F1", "workload"] > means.loc["F2", "workload"]
    # H2: contrastive forms yield better mental-model accuracy.
    assert means.loc["F2", "mm_explicability"] > means.loc["F1", "mm_explicability"]
    assert means.loc["F3", "mm_explicability"] > means.loc["F1", "mm_explicability"]
    # H3b: more unnecessary overwrites under F1.
    assert means.loc["F1", "overwrite_rate"] > means.loc["F2", "overwrite_rate"]
    # H4: better non-aided performance (comms accuracy, resman tracking) under F2/F3.
    assert means.loc["F2", "accuracy"] > means.loc["F1", "accuracy"]
    assert means.loc["F2", "rmsd_mean"] < means.loc["F1", "rmsd_mean"]


def test_no_effects_mode_is_flat(tmp_path):
    generate(DEFAULT_TEMPLATE, tmp_path, n=10, seed=2, embed_effects=False)
    table = build_metrics_table(find_study_sessions(tmp_path))
    means = table.groupby("form")["subj_transparency"].mean()
    # Without embedded effects the forms should be within sampling noise of each other.
    assert means.max() - means.min() < 0.6
