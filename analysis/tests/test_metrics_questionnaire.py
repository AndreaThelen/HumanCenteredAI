import math
import pandas as pd
from matb_analysis.metrics_questionnaire import questionnaire_metrics

COLS = ["logtime", "scenario_time", "type", "module", "address", "value"]


def _q(pairs):
    return pd.DataFrame(
        [(0.0, 1.0, "performance", "genericscales", k, str(v)) for k, v in pairs],
        columns=COLS,
    )


def test_subjective_transparency_reverse_scores_keep_track():
    # keep_track is reverse-keyed ("hard to keep track"): 2 -> 6 on a 1..7 scale.
    m = questionnaire_metrics(_q([
        ("Subjective_transparency_what", 6),
        ("Subjective_keep_track_REV", 2),       # reversed -> 6
        ("Subjective_information_volume", 6),
    ]))
    assert math.isclose(m["subj_transparency"], 6.0)   # mean(6, 6, 6)


def test_keep_track_matches_unsuffixed_title():
    # Early pilot logged the item without the explicit _REV suffix.
    m = questionnaire_metrics(_q([
        ("Subjective_transparency_what", 5),
        ("Subjective_keep_track", 1),           # reversed -> 7
        ("Subjective_information_volume", 6),
    ]))
    assert math.isclose(m["subj_transparency"], 6.0)   # mean(5, 7, 6)


def test_workload_single_item():
    m = questionnaire_metrics(_q([("Workload_overall", 6)]))
    assert math.isclose(m["workload"], 6.0)


def test_mental_model_block_A_all_correct():
    # Block A: handled = Scale 3, missed = Scale 1. The probe (PROBE_TARGETS["A"])
    # asks: act on Scale 3 (->Yes), fail on Scale 1 (->Yes), close call on Scale 1
    # (->No). A perfect respondent (0..100 scale).
    m = questionnaire_metrics(_q([
        ("MM_A_act_scale3", 90),    # Yes (correct: Scale 3 is handled)
        ("MM_A_miss_scale1", 95),   # Yes (correct: Scale 1 is missed)
        ("MM_A_close_scale1", 5),   # No  (correct: close calls are on Scale 3)
    ]))
    assert math.isclose(m["mm_act_accuracy"], 1.0)
    assert math.isclose(m["mm_miss_accuracy"], 1.0)
    assert math.isclose(m["mm_close_accuracy"], 1.0)
    assert math.isclose(m["mm_explicability"], 1.0)


def test_mental_model_truth_by_role():
    # Cross-check the three truths against the roles directly (block A).
    # act: Yes only for the handled gauge (Scale 3); miss: Yes only for the missed
    # gauge (Scale 1); close: Yes only for the handled gauge (Scale 3).
    m = questionnaire_metrics(_q([
        ("MM_A_act_scale1", 90),    # Yes (WRONG: Scale 1 is missed -> act=No)
        ("MM_A_miss_scale3", 90),   # Yes (WRONG: Scale 3 is handled -> miss=No)
        ("MM_A_close_scale3", 90),  # Yes (correct: close call is on Scale 3)
    ]))
    assert math.isclose(m["mm_act_accuracy"], 0.0)
    assert math.isclose(m["mm_miss_accuracy"], 0.0)
    assert math.isclose(m["mm_close_accuracy"], 1.0)
    assert math.isclose(m["mm_explicability"], 1.0 / 3.0)


def test_empty_is_safe():
    m = questionnaire_metrics(pd.DataFrame([], columns=COLS))
    assert math.isnan(m["subj_transparency"])
    assert math.isnan(m["workload"])
    assert math.isnan(m["mm_act_accuracy"])
    assert math.isnan(m["mm_miss_accuracy"])
    assert math.isnan(m["mm_close_accuracy"])
    assert math.isnan(m["mm_explicability"])
