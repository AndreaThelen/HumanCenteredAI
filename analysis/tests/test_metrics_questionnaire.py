import math
import pandas as pd
from matb_analysis.metrics_questionnaire import questionnaire_metrics
from matb_analysis.study_design import TRUE_RELIABILITY_PCT

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


def test_mental_model_block_A_perfect_revised_scale():
    # Block A set = scales-1, scales-3 -> both recognition truths are "Yes".
    # Recognition sliders on the revised 0..100 scale.
    m = questionnaire_metrics(_q([
        ("MM_A_q_misses", 2),
        ("MM_A_q_closecalls", 2),
        ("MM_A_q_reliability", TRUE_RELIABILITY_PCT),
        ("MM_A_rec_scale1", 90),   # Yes (correct)
        ("MM_A_rec_scale3", 100),  # Yes (correct)
    ]))
    assert math.isclose(m["mm_misses_error"], 0.0)
    assert math.isclose(m["mm_closecalls_error"], 0.0)
    assert math.isclose(m["mm_reliability_error"], 0.0, abs_tol=1e-6)
    assert math.isclose(m["mm_rec_accuracy"], 1.0)
    assert math.isclose(m["mm_explicability"], 1.0, abs_tol=1e-6)


def test_mental_model_block_B_partial_and_errors():
    # Block B set = lights-1, lights-2. Probes: light2 (in set -> Yes), scale1
    # (out of set -> No). Recognition on the 0..1 pilot scale.
    m = questionnaire_metrics(_q([
        ("MM_B_rec_light2", 1.0),   # Yes (correct)
        ("MM_B_rec_scale1", 1.0),   # Yes (wrong: truth No)
        ("MM_B_q_misses", 5),       # |5 - 2| = 3
        ("MM_B_q_closecalls", 0),   # |0 - 2| = 2
        ("MM_B_q_reliability", 50),  # |50 - 77.78|
    ]))
    assert math.isclose(m["mm_rec_accuracy"], 0.5)   # 1 of 2 correct
    assert math.isclose(m["mm_misses_error"], 3.0)
    assert math.isclose(m["mm_closecalls_error"], 2.0)
    assert math.isclose(m["mm_reliability_error"], abs(50 - TRUE_RELIABILITY_PCT))


def test_block_C_all_no_recognition():
    # Block C set = scales-2, scales-4. Probes: light1, light2 -> both out of
    # set -> both "No". Slider parked low (0..100 scale) = No.
    m = questionnaire_metrics(_q([
        ("MM_C_rec_light1", 0),
        ("MM_C_rec_light2", 10),
    ]))
    assert math.isclose(m["mm_rec_accuracy"], 1.0)   # both correctly "No"


def test_empty_is_safe():
    m = questionnaire_metrics(pd.DataFrame([], columns=COLS))
    assert math.isnan(m["subj_transparency"])
    assert math.isnan(m["workload"])
    assert math.isnan(m["mm_rec_accuracy"])
    assert math.isnan(m["mm_explicability"])
