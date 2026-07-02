import pytest, sys, os, json
sys.path.insert(0, '/Users/jimfu/Work/huixue')
from student_dc10 import deduplicate_records, handle_missing_values, generate_quality_report

def test_deduplicate():
    """数据去重"""
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}, {"id": 1, "name": "Alice"}]
    result = deduplicate_records(data)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, (list, dict)), f"期望 list/dict，实际 {type(result).__name__}"
    assert len(result) == 2, f"去重后应为 2 条，实际 {len(result)}"

def test_handle_missing():
    """缺失值处理"""
    data = [{"a": 1, "b": None}, {"a": 2, "b": 3}]
    result = handle_missing_values(data)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, (list, dict)), f"期望 list/dict，实际 {type(result).__name__}"
    assert len(result) == 2, f"记录数应为 2，实际 {len(result)}"

def test_quality_report():
    """数据质量报告"""
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": None}]
    result = generate_quality_report(data)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, dict), f"期望 dict，实际 {type(result).__name__}"
    assert "quality_score" in result or "score" in result or "total" in result, "缺少质量报告字段"
