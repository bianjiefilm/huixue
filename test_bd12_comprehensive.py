"""BD12 综合关 pytest_module 测试."""
import pytest
from student_bd12 import (
    validate_pipeline_input_schema,
    get_tool_for_purpose,
    compute_pipeline_total_size,
    combine_bd_pipeline_report,
)

TOL = 1e-6


def _stage(name="s1", tool="hdfs", size=10.0):
    return {"name": name, "tool": tool, "output_size_gb": size}


# F1: validate_pipeline_input_schema (7 cases)
def test_vpis_valid():
    assert validate_pipeline_input_schema([_stage()]) is True

def test_vpis_empty():
    assert validate_pipeline_input_schema([]) is True

def test_vpis_missing_key():
    assert validate_pipeline_input_schema([{"name": "s", "tool": "hdfs"}]) is False

def test_vpis_negative_size():
    assert validate_pipeline_input_schema([_stage(size=-1)]) is False

def test_vpis_non_str_name():
    assert validate_pipeline_input_schema([_stage(name=123)]) is False

def test_vpis_raises_on_non_list():
    with pytest.raises(TypeError):
        validate_pipeline_input_schema("not list")

def test_vpis_raises_on_non_dict_stage():
    with pytest.raises(TypeError):
        validate_pipeline_input_schema(["not dict"])


# F2: get_tool_for_purpose (8 cases)
def test_gtfp_storage():
    assert get_tool_for_purpose("storage") == "hdfs"

def test_gtfp_compute():
    assert get_tool_for_purpose("compute") == "mapreduce"

def test_gtfp_scheduling():
    assert get_tool_for_purpose("scheduling") == "yarn"

def test_gtfp_sql():
    assert get_tool_for_purpose("sql") == "hive"

def test_gtfp_nosql():
    assert get_tool_for_purpose("nosql") == "hbase"

def test_gtfp_streaming():
    assert get_tool_for_purpose("streaming") == "kafka"

def test_gtfp_migration():
    assert get_tool_for_purpose("migration") == "sqoop"

def test_gtfp_raises_on_unknown():
    with pytest.raises(ValueError):
        get_tool_for_purpose("unknown")


# F3: compute_pipeline_total_size (6 cases)
def test_cpts_basic():
    assert abs(compute_pipeline_total_size([_stage(size=1.5), _stage(size=2.5)]) - 4.0) < TOL

def test_cpts_empty():
    assert compute_pipeline_total_size([]) == 0.0

def test_cpts_zero_size():
    assert compute_pipeline_total_size([_stage(size=0)]) == 0.0

def test_cpts_raises_on_negative():
    with pytest.raises(ValueError):
        compute_pipeline_total_size([_stage(size=-1)])

def test_cpts_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_pipeline_total_size("xx")

def test_cpts_raises_on_missing_key():
    with pytest.raises(ValueError):
        compute_pipeline_total_size([{"name": "s", "tool": "hdfs"}])


# F4: combine_bd_pipeline_report (7 cases)
def test_cbpr_full_success():
    r = combine_bd_pipeline_report(10, 10, {})
    assert r["progress_ratio"] == 1.0
    assert r["total_errors"] == 0
    assert r["is_success"] is True

def test_cbpr_partial():
    r = combine_bd_pipeline_report(5, 10, {"timeout": 1})
    assert r["progress_ratio"] == 0.5
    assert r["total_errors"] == 1
    assert r["is_success"] is False

def test_cbpr_zero_done():
    r = combine_bd_pipeline_report(0, 10, {})
    assert r["progress_ratio"] == 0.0
    assert r["is_success"] is False

def test_cbpr_full_with_errors():
    r = combine_bd_pipeline_report(10, 10, {"warn": 2})
    assert r["progress_ratio"] == 1.0
    assert r["is_success"] is False  # progress=1 但 total_errors > 0

def test_cbpr_raises_on_zero_total():
    with pytest.raises(ValueError):
        combine_bd_pipeline_report(0, 0, {})

def test_cbpr_raises_on_done_gt_total():
    with pytest.raises(ValueError):
        combine_bd_pipeline_report(11, 10, {})

def test_cbpr_raises_on_negative_error():
    with pytest.raises(ValueError):
        combine_bd_pipeline_report(5, 10, {"e": -1})
