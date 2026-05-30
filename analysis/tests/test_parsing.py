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
