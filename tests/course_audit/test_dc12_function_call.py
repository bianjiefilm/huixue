import importlib
import os

import pytest


def _student():
    return importlib.import_module(os.environ.get("DC12_MODULE", "content_orchestrator.stages_config.data_collection.student_dc12"))


RECORDS_WITH_DUP = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}, {"id": 1, "name": "A2"}]
RECORDS_WITH_MISSING = [{"id": 1, "name": None, "age": 20}, {"id": 2, "name": "B", "age": None}]


CASES = [
    (RECORDS_WITH_DUP, "deduplicate", [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]),
    (RECORDS_WITH_MISSING, "fill_missing", [{"id": 1, "name": "", "age": 20}, {"id": 2, "name": "B", "age": ""}]),
    (RECORDS_WITH_DUP + [{"id": 3, "name": None}], "report", {"total": 4, "duplicate_ids": [1], "missing_fields": ["name"]}),
    ("13812345678", "phone", True),
    ("12812345678", "phone", False),
    (18, "age", {"valid": True, "reason": ""}),
    (150, "age", {"valid": False, "reason": "out_of_range"}),
    ("user@example.com", "email", {"valid": True, "reason": ""}),
    ("user@@example.com", "email", {"valid": False, "reason": "format_error"}),
    ([{"id": 1, "name": "A"}], "unknown", {"error": "unsupported_check"}),
]


@pytest.mark.parametrize(("data", "check_type", "expected"), CASES)
def test_check_data_quality(data, check_type, expected):
    assert _student().check_data_quality(data, check_type) == expected


def test_rejects_non_string_check_type():
    with pytest.raises(TypeError):
        _student().check_data_quality([], None)


def test_rejects_non_list_for_deduplicate():
    with pytest.raises(TypeError):
        _student().check_data_quality("bad", "deduplicate")


def test_rejects_non_string_phone():
    with pytest.raises(TypeError):
        _student().check_data_quality(13812345678, "phone")
