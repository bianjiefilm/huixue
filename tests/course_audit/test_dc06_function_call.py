import importlib
import os

import pytest


def _student():
    return importlib.import_module(os.environ.get("DC06_MODULE", "student_dc06"))


CASES = [
    (
        [{"title": "新闻A", "content": "内容A", "author": "作者A"}, {"title": "新闻B", "content": None, "author": "作者B"}],
        100,
        95,
        5,
        50.0,
        {
            "quality_report": {"completeness": 83.33, "accuracy": 83.33, "duplicate_rate": 0.0},
            "efficiency_report": {"success_rate": 95.0, "throughput": 0.04},
            "overall_score": 65.92,
        },
    ),
    (
        [{"id": 1, "name": "商品1", "price": 99.9}, {"id": 2, "name": "商品2", "price": None}, {"id": 3, "name": "商品3", "price": -10.0}, {"id": 1, "name": "商品1", "price": 99.9}],
        200,
        180,
        20,
        120.0,
        {
            "quality_report": {"completeness": 91.67, "accuracy": 83.33, "duplicate_rate": 25.0},
            "efficiency_report": {"success_rate": 90.0, "throughput": 0.03},
            "overall_score": 66.67,
        },
    ),
    (
        [{"title": f"Item_{i}", "url": f"http://example.com/{i}", "timestamp": "2026-04-24T10:00:00"} for i in range(10)],
        100,
        100,
        0,
        3.0,
        {
            "quality_report": {"completeness": 100.0, "accuracy": 100.0, "duplicate_rate": 0.0},
            "efficiency_report": {"success_rate": 100.0, "throughput": 3.33},
            "overall_score": 100.0,
        },
    ),
    (
        [{"field_a": "data", "field_b": None} for _ in range(10)],
        50,
        50,
        0,
        2.0,
        {
            "quality_report": {"completeness": 50.0, "accuracy": 50.0, "duplicate_rate": 90.0},
            "efficiency_report": {"success_rate": 100.0, "throughput": 5.0},
            "overall_score": 75.0,
        },
    ),
    (
        [],
        0,
        0,
        0,
        0.0,
        {
            "quality_report": {"completeness": 0.0, "accuracy": 0.0, "duplicate_rate": 0.0},
            "efficiency_report": {"success_rate": 0.0, "throughput": 0.0},
            "overall_score": 0.0,
        },
    ),
    (
        [{"product": f"P{i}", "price": 100 + i, "category": "test"} for i in range(20)],
        1000,
        950,
        50,
        2.0,
        {
            "quality_report": {"completeness": 100.0, "accuracy": 100.0, "duplicate_rate": 0.0},
            "efficiency_report": {"success_rate": 95.0, "throughput": 10.0},
            "overall_score": 98.75,
        },
    ),
    (
        [{"name": "A", "score": 0}, {"name": "B", "score": 100}],
        2,
        1,
        1,
        2.0,
        {
            "quality_report": {"completeness": 100.0, "accuracy": 100.0, "duplicate_rate": 0.0},
            "efficiency_report": {"success_rate": 50.0, "throughput": 1.0},
            "overall_score": 75.0,
        },
    ),
    (
        [{"name": "A", "score": -1}, {"name": "B", "score": None}],
        4,
        3,
        1,
        4.0,
        {
            "quality_report": {"completeness": 75.0, "accuracy": 50.0, "duplicate_rate": 0.0},
            "efficiency_report": {"success_rate": 75.0, "throughput": 0.5},
            "overall_score": 56.25,
        },
    ),
]


@pytest.mark.parametrize(("records", "total_requests", "successful_requests", "failed_requests", "seconds", "expected"), CASES)
def test_evaluate_collection_project(records, total_requests, successful_requests, failed_requests, seconds, expected):
    assert _student().evaluate_collection_project(records, total_requests, successful_requests, failed_requests, seconds) == expected


def test_rejects_non_list_records():
    with pytest.raises(TypeError):
        _student().evaluate_collection_project({"id": 1}, 1, 1, 0, 1.0)


def test_rejects_non_dict_record():
    with pytest.raises(TypeError):
        _student().evaluate_collection_project([{"id": 1}, ["bad"]], 1, 1, 0, 1.0)


def test_rejects_non_numeric_metrics():
    with pytest.raises(TypeError):
        _student().evaluate_collection_project([], "1", 1, 0, 1.0)


def test_rejects_negative_metrics():
    with pytest.raises(ValueError):
        _student().evaluate_collection_project([], 1, -1, 0, 1.0)


def test_rejects_inconsistent_request_counts():
    with pytest.raises(ValueError):
        _student().evaluate_collection_project([], 5, 4, 2, 1.0)
