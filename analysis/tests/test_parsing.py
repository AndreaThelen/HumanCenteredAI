import pandas as pd
from matb_analysis.parsing import load_raw, segment_blocks, rows_for_block, Block

# A minimal synthetic log: practice block, then F1/block_A, then F2/block_B.
# Columns: logtime, scenario_time, type, module, address, value
SYNTHETIC_ROWS = [
    # practice
    (100.0, 0.0,   "event",     "instructions", "filename", "study/briefing_practice.txt"),
    (100.1, 1.0,   "performance","resman",       "a_deviation", "10"),
    # block 1: F1 / A  (briefing at t=10, a panel reveals block letter A)
    (110.0, 10.0,  "event",     "instructions", "filename", "study/briefing_F1.txt"),
    (110.1, 10.0,  "parameter", "instructions", "filename", "study/briefing_F1.txt"),
    (111.0, 12.0,  "performance","resman",       "a_deviation", "20"),
    (112.0, 13.0,  "event",     "instructions", "filename", "study/panels/F1/block_A_event_01.txt"),
    # block 2: F2 / B
    (120.0, 30.0,  "event",     "instructions", "filename", "study/briefing_F2.txt"),
    (121.0, 32.0,  "performance","resman",       "a_deviation", "30"),
    (122.0, 33.0,  "event",     "instructions", "filename", "study/panels/F2/block_B_event_03.txt"),
]

def _make_df():
    return pd.DataFrame(
        SYNTHETIC_ROWS,
        columns=["logtime", "scenario_time", "type", "module", "address", "value"],
    )

def test_segment_blocks_excludes_practice_and_labels_forms():
    blocks = segment_blocks(_make_df())
    assert [b.form for b in blocks] == ["F1", "F2"]
    assert [b.block_letter for b in blocks] == ["A", "B"]

def test_segment_blocks_intervals_are_contiguous():
    blocks = segment_blocks(_make_df())
    assert blocks[0].start_time == 10.0
    assert blocks[0].end_time == 30.0      # up to next briefing
    assert blocks[1].start_time == 30.0
    assert blocks[1].end_time == float("inf")  # last block open-ended

def test_rows_for_block_selects_by_scenario_time():
    df = _make_df()
    blocks = segment_blocks(df)
    rows = rows_for_block(df, blocks[0])
    devs = rows[(rows.module == "resman") & (rows.address == "a_deviation")]
    assert list(devs.value) == ["20"]      # practice (t=1) and block2 (t=32) excluded

def test_block_is_a_dataclass_with_expected_fields():
    b = Block(form="F1", block_letter="A", start_time=0.0, end_time=1.0)
    assert (b.form, b.block_letter, b.start_time, b.end_time) == ("F1", "A", 0.0, 1.0)


# --- discovery tests (appended) ---
from pathlib import Path
from matb_analysis.discovery import scenario_kind_and_participant, find_study_sessions

def test_scenario_kind_full_participant():
    kind, pid, form, block = scenario_kind_and_participant(
        "includes\\scenarios\\study\\full_P03.txt")
    assert (kind, pid) == ("full", "P03")
    assert form is None and block is None

def test_scenario_kind_single_block():
    kind, pid, form, block = scenario_kind_and_participant(
        "includes/scenarios/study/F2_block_A.txt")
    assert kind == "single_block"
    assert (form, block) == ("F2", "A")

def test_scenario_kind_non_study():
    kind, pid, form, block = scenario_kind_and_participant(
        "includes/scenarios/default_en.txt")
    assert kind == "other"

def test_find_study_sessions_filters_and_reads(tmp_path):
    # Build a fake sessions tree with one study session and one non-study session.
    day = tmp_path / "2026-01-01"
    day.mkdir()
    header = "logtime,scenario_time,type,module,address,value\n"
    study = day / "1_x.csv"
    study.write_text(
        header
        + "1,0,scenario_path,,,includes/scenarios/study/full_P01.txt\n"
        + "2,1,event,instructions,filename,study/briefing_F1.txt\n",
        encoding="utf-8",
    )
    other = day / "2_x.csv"
    other.write_text(
        header + "1,0,scenario_path,,,includes/scenarios/default_en.txt\n",
        encoding="utf-8",
    )
    sessions = find_study_sessions(tmp_path)
    assert len(sessions) == 1
    assert sessions[0].participant == "P01"
    assert sessions[0].scenario_kind == "full"


def test_segment_blocks_dedupes_event_and_parameter_briefing_rows():
    """Real logs fire an `event` and a `parameter` briefing row ~6ms apart at
    DIFFERENT scenario_times. Both must collapse to one block per form."""
    rows = [
        (1.0, 10.000, "event",     "instructions", "filename", "study/briefing_F1.txt"),
        (1.1, 10.006, "parameter", "instructions", "filename", "study/briefing_F1.txt"),
        (1.2, 12.0,   "event",     "instructions", "filename", "study/panels/F1/block_A_event_01.txt"),
        (1.3, 13.0,   "performance","resman",      "a_deviation", "20"),
        (2.0, 30.000, "event",     "instructions", "filename", "study/briefing_F2.txt"),
        (2.1, 30.006, "parameter", "instructions", "filename", "study/briefing_F2.txt"),
        (2.2, 31.0,   "event",     "instructions", "filename", "study/panels/F2/block_B_event_03.txt"),
    ]
    df = pd.DataFrame(rows, columns=["logtime", "scenario_time", "type",
                                     "module", "address", "value"])
    blocks = segment_blocks(df)
    assert [b.form for b in blocks] == ["F1", "F2"]
    assert [b.block_letter for b in blocks] == ["A", "B"]
    assert blocks[0].start_time == 10.0
    assert blocks[0].end_time == 30.0  # next briefing's EVENT row, not the parameter dup
