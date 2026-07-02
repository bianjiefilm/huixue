"""BD12 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_bd12 import (
    validate_pipeline_input_schema,
    get_tool_for_purpose,
    compute_pipeline_total_size,
    combine_bd_pipeline_report,
)

TOL = 1e-6


# F1: validate_pipeline_input_schema
def test_validate_all_present():
    stages = [{"name": "s1", "tool": "hdfs", "output_size_gb": 10}]
    assert validate_pipeline_input_schema(stages) is True

def test_validate_missing_name():
    stages = [{"tool": "hdfs", "output_size_gb": 10}]
    assert validate_pipeline_input_schema(stages) is False

def test_validate_missing_tool():
    stages = [{"name": "s1", "output_size_gb": 10}]
    assert validate_pipeline_input_schema(stages) is False

def test_validate_missing_size():
    stages = [{"name": "s1", "tool": "hdfs"}]
    assert validate_pipeline_input_schema(stages) is False

def test_validate_wrong_type_name():
    """name 不是 str"""
    stages = [{"name": 123, "tool": "hdfs", "output_size_gb": 10}]
    assert validate_pipeline_input_schema(stages) is False

def test_validate_negative_size():
    """size 负数"""
    stages = [{"name": "s1", "tool": "hdfs", "output_size_gb": -1}]
    assert validate_pipeline_input_schema(stages) is False

def test_validate_raises_on_non_list():
    with pytest.raises(TypeError):
        validate_pipeline_input_schema("stages")


# F2: get_tool_for_purpose
def test_purpose_compute():
    assert get_tool_for_purpose("compute") == "mapreduce"

def test_purpose_scheduling():
    assert get_tool_for_purpose("scheduling") == "yarn"

def test_purpose_sql():
    assert get_tool_for_purpose("sql") == "hive"

def test_purpose_nosql():
    assert get_tool_for_purpose("nosql") == "hbase"

def test_purpose_streaming():
    assert get_tool_for_purpose("streaming") == "kafka"

def test_purpose_migration():
    assert get_tool_for_purpose("migration") == "sqoop"

def test_purpose_raises_on_unknown():
    with pytest.raises(ValueError):
        get_tool_for_purpose("unknown")

def test_purpose_raises_on_empty():
    with pytest.raises(ValueError):
        get_tool_for_purpose("")

def test_purpose_raises_on_non_string():
    with pytest.raises(TypeError):
        get_tool_for_purpose(123)


# F3: compute_pipeline_total_size
def test_total_simple():
    """[10, 20, 30] → 60"""
    stages = [
        {"name": "s1", "tool": "x", "output_size_gb": 10},
        {"name": "s2", "tool": "x", "output_size_gb": 20},
        {"name": "s3", "tool": "x", "output_size_gb": 30},
    ]
    assert abs(compute_pipeline_total_size(stages) - 60.0) < TOL

def test_total_decimal():
    stages = [
        {"name": "s1", "tool": "x", "output_size_gb": 1.5},
        {"name": "s2", "tool": "x", "output_size_gb": 2.5},
    ]
    assert abs(compute_pipeline_total_size(stages) - 4.0) < TOL

def test_total_one_stage():
    stages = [{"name": "only", "tool": "x", "output_size_gb": 100}]
    assert abs(compute_pipeline_total_size(stages) - 100.0) < TOL

def test_total_empty():
    """空 → 0"""
    assert abs(compute_pipeline_total_size([]) - 0.0) < TOL

def test_total_raises_on_missing_size():
    with pytest.raises(ValueError):
        compute_pipeline_total_size([{"name": "s1", "tool": "x"}])

def test_total_raises_on_negative():
    with pytest.raises(ValueError):
        compute_pipeline_total_size([{"name": "s1", "tool": "x", "output_size_gb": -1}])


# F4: combine_bd_pipeline_report
def test_report_partial():
    r = combine_bd_pipeline_report(8, 10, {"hive": 1, "kafka": 2})
    assert r["stages_done"] == 8
    assert r["stages_total"] == 10
    assert abs(r["progress_ratio"] - 0.8) < TOL
    assert r["total_errors"] == 3
    assert r["is_success"] is False

def test_report_success():
    """全 done + 无 errors → success"""
    r = combine_bd_pipeline_report(10, 10, {})
    assert r["is_success"] is True
    assert abs(r["progress_ratio"] - 1.0) < TOL
    assert r["total_errors"] == 0

def test_report_done_but_errors():
    """全 done 但有 errors → 仍非 success"""
    r = combine_bd_pipeline_report(10, 10, {"hive": 1})
    assert r["is_success"] is False

def test_report_keys_complete():
    r = combine_bd_pipeline_report(5, 10, {})
    for k in ["stages_done", "stages_total", "progress_ratio",
              "errors", "total_errors", "is_success"]:
        assert k in r

def test_report_zero_done():
    r = combine_bd_pipeline_report(0, 10, {})
    assert abs(r["progress_ratio"] - 0.0) < TOL

def test_report_raises_on_done_gt_total():
    with pytest.raises(ValueError):
        combine_bd_pipeline_report(11, 10, {})

def test_report_raises_on_zero_total():
    with pytest.raises(ValueError):
        combine_bd_pipeline_report(0, 0, {})

def test_report_raises_on_negative_error():
    with pytest.raises(ValueError):
        combine_bd_pipeline_report(5, 10, {"hive": -1})
