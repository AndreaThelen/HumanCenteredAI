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


def test_subjective_transparency_separates_info_volume():
    m = questionnaire_metrics(_q([
        ("Subjective_transparency_what", 6),
        ("Subjective_attention_guidance", 4),
        ("Subjective_information_volume", 7),  # "far too much" -> miscalibrated by 3
    ]))
    assert math.isclose(m["subj_transparency"], 5.0)      # mean of the two monotone items
    assert math.isclose(m["info_volume"], 7.0)
    assert math.isclose(m["info_volume_miscal"], 3.0)     # |7 - 4|


def test_subjective_trust_mean():
    m = questionnaire_metrics(_q([
        ("Trust_01_reliable", 6), ("Trust_02_expected", 6),
        ("Trust_03_confident", 4), ("Trust_04_trust", 4),
    ]))
    assert math.isclose(m["subj_trust"], 5.0)


def test_mental_model_block_A_perfect():
    # Block A gauges = scales-1, scales-3 -> set truth: s1=Yes, s2=No, s3=Yes, s4=No.
    m = questionnaire_metrics(_q([
        ("MM_A_set_scale1", 0.6), ("MM_A_set_scale2", 0.1),
        ("MM_A_set_scale3", 0.9), ("MM_A_set_scale4", 0.0),
        ("MM_A_q_skipped", 2),
        ("MM_A_q_reliability", TRUE_RELIABILITY_PCT),
    ]))
    assert math.isclose(m["mm_set_accuracy"], 1.0)
    assert math.isclose(m["mm_skipped_error"], 0.0)
    assert math.isclose(m["mm_reliability_error"], 0.0, abs_tol=1e-6)
    assert math.isclose(m["mm_explicability"], 1.0, abs_tol=1e-6)


def test_mental_model_block_B_partial_and_errors():
    # Block B gauges = lights-1, lights-2 -> light1=Yes, light2=Yes, scale1=No, scale2=No.
    m = questionnaire_metrics(_q([
        ("MM_B_set_light1", 1.0),   # correct (Yes)
        ("MM_B_set_light2", 0.0),   # wrong (truth Yes)
        ("MM_B_set_scale1", 0.0),   # correct (No)
        ("MM_B_set_scale2", 1.0),   # wrong (truth No)
        ("MM_B_q_skipped", 5),      # |5 - 2| = 3
        ("MM_B_q_reliability", 50),  # |50 - 77.78|
    ]))
    assert math.isclose(m["mm_set_accuracy"], 0.5)   # 2 of 4 correct
    assert math.isclose(m["mm_skipped_error"], 3.0)
    assert math.isclose(m["mm_reliability_error"], abs(50 - TRUE_RELIABILITY_PCT))


def test_empty_is_safe():
    m = questionnaire_metrics(pd.DataFrame([], columns=COLS))
    assert math.isnan(m["subj_transparency"])
    assert math.isnan(m["subj_trust"])
    assert math.isnan(m["mm_set_accuracy"])
    assert math.isnan(m["mm_explicability"])
