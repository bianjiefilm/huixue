"""
Unit tests for backend/app/utils/eval_helpers.py — evaluation pure functions.
"""
import json
import pytest
from app.utils.eval_helpers import (
    match_output,
    format_testcase,
    create_unit_test_script,
    create_dataframe_eval_script,
)


# ==================== match_output ====================

class TestMatchOutput:

    def test_exact_match(self):
        assert match_output("hello", "hello", "exact") is True

    def test_exact_no_match(self):
        assert match_output("hello", "world", "exact") is False

    def test_exact_whitespace_matters(self):
        assert match_output("hello ", "hello", "exact") is False

    def test_regex_match(self):
        assert match_output("abc123", r"abc\d+", "regex") is True

    def test_regex_no_match(self):
        assert match_output("xyz", r"abc\d+", "regex") is False

    def test_json_equal_same(self):
        assert match_output('{"a":1}', '{"a": 1}', "json_equal") is True

    def test_json_equal_different(self):
        assert match_output('{"a":1}', '{"a": 2}', "json_equal") is False

    def test_json_equal_invalid(self):
        assert match_output("not json", '{"a":1}', "json_equal") is False

    def test_subset_found(self):
        assert match_output("hello world foo", "world", "subset") is True

    def test_subset_not_found(self):
        assert match_output("hello", "world", "subset") is False

    def test_unknown_rule_falls_back_exact(self):
        assert match_output("abc", "abc", "unknown") is True
        assert match_output("abc", "def", "unknown") is False

    def test_empty_strings_exact(self):
        assert match_output("", "", "exact") is True

    def test_json_equal_arrays(self):
        assert match_output("[1,2,3]", "[1, 2, 3]", "json_equal") is True

    def test_json_equal_nested(self):
        a = json.dumps({"a": {"b": [1, 2]}})
        b = json.dumps({"a": {"b": [1, 2]}})
        assert match_output(a, b, "json_equal") is True


# ==================== format_testcase ====================

class TestFormatTestcase:

    def test_script_io(self):
        tc = {"id": "t1", "input": "5", "expected": "25"}
        result = format_testcase(tc, "script_io")
        assert result["input"] == "5"
        assert result["expected"] == "25"
        assert result["id"] == "t1"

    def test_script_io_fallback_output_key(self):
        tc = {"output": "hello"}
        result = format_testcase(tc, "script_io")
        assert result["expected"] == "hello"

    def test_sql_query(self):
        tc = {"sql": "SELECT 1", "expected_rows": [[1]]}
        result = format_testcase(tc, "sql_query")
        assert result["sql"] == "SELECT 1"
        assert result["expected_rows"] == [[1]]

    def test_api_service_defaults(self):
        tc = {}
        result = format_testcase(tc, "api_service")
        assert result["method"] == "GET"
        assert result["url"] == "/"
        assert result["expect_status"] == 200

    def test_api_service_custom(self):
        tc = {"method": "POST", "url": "/api", "expect_status": 201}
        result = format_testcase(tc, "api_service")
        assert result["method"] == "POST"
        assert result["expect_status"] == 201

    def test_web_static(self):
        tc = {"page": "app.html", "assert": {"selector": "#main"}}
        result = format_testcase(tc, "web_static")
        assert result["page"] == "app.html"
        assert result["assert"]["selector"] == "#main"

    def test_web_static_defaults(self):
        tc = {}
        result = format_testcase(tc, "web_static")
        assert result["page"] == "index.html"
        assert result["assert"] == {}

    def test_dataframe_task(self):
        tc = {"check": "columns", "expected": ["a", "b"]}
        result = format_testcase(tc, "dataframe_task")
        assert result["check"] == "columns"
        assert result["expected"] == ["a", "b"]

    def test_dataframe_task_defaults(self):
        tc = {}
        result = format_testcase(tc, "dataframe_task")
        assert result["check"] == "shape"
        assert result["tolerance"] == {"abs": 0.01}

    def test_function_unit_default(self):
        tc = {"function": "add", "args": [1, 2], "expected": 3}
        result = format_testcase(tc, "function_unit")
        assert result["function"] == "add"
        assert result["args"] == [1, 2]
        assert result["expected"] == 3

    def test_unknown_subtype_uses_function_unit(self):
        tc = {"function": "foo"}
        result = format_testcase(tc, "some_new_type")
        assert result["function"] == "foo"

    def test_common_fields_always_present(self):
        tc = {"id": "x", "visible": True, "match_rule": "regex"}
        for subtype in ["script_io", "sql_query", "api_service", "web_static", "dataframe_task", "function_unit"]:
            result = format_testcase(tc, subtype)
            assert result["id"] == "x"
            assert result["visible"] is True
            assert result["match_rule"] == "regex"

    def test_defaults_for_common_fields(self):
        tc = {}
        result = format_testcase(tc, "script_io")
        assert result["id"] == ""
        assert result["visible"] is False
        assert result["match_rule"] == "exact"


# ==================== create_unit_test_script ====================

class TestCreateUnitTestScript:

    def test_empty_testcases(self):
        script = create_unit_test_script([])
        assert "from submission import" in script
        assert "results = []" in script

    def test_single_testcase(self):
        tcs = [{"function": "add", "args": [1, 2], "expected": 3, "id": "t1"}]
        script = create_unit_test_script(tcs)
        assert "add(1, 2)" in script
        assert "'t1'" in script
        assert "result ==" in script

    def test_multiple_testcases(self):
        tcs = [
            {"function": "square", "args": [4], "expected": 16, "id": "a"},
            {"function": "square", "args": [0], "expected": 0, "id": "b"},
        ]
        script = create_unit_test_script(tcs)
        assert "square(4)" in script
        assert "square(0)" in script
        assert script.count("try:") == 2

    def test_visible_flag(self):
        tcs = [{"function": "f", "args": [], "expected": 1, "visible": True}]
        script = create_unit_test_script(tcs)
        assert "'visible': True" in script

    def test_string_args(self):
        tcs = [{"function": "greet", "args": ["world"], "expected": "hello world"}]
        script = create_unit_test_script(tcs)
        assert "'world'" in script

    def test_output_is_valid_python(self):
        tcs = [{"function": "noop", "args": [], "expected": None, "id": "x"}]
        script = create_unit_test_script(tcs)
        # Should be parseable Python
        compile(script, "<test>", "exec")

    def test_exit_code_logic(self):
        script = create_unit_test_script([])
        assert "sys.exit" in script


# ==================== create_dataframe_eval_script ====================

class TestCreateDataframeEvalScript:

    def test_empty_testcases(self):
        script = create_dataframe_eval_script([])
        assert "import pandas" in script
        assert "get_dataframe()" in script

    def test_shape_check(self):
        tcs = [{"check": "shape", "expected": [100, 5], "id": "s1"}]
        script = create_dataframe_eval_script(tcs)
        assert "df.shape" in script
        assert "tuple(" in script

    def test_columns_check(self):
        tcs = [{"check": "columns", "expected": ["a", "b", "c"], "id": "c1"}]
        script = create_dataframe_eval_script(tcs)
        assert "df.columns" in script

    def test_unknown_check(self):
        tcs = [{"check": "dtypes", "expected": "int64", "id": "d1"}]
        script = create_dataframe_eval_script(tcs)
        assert "passed = False" in script

    def test_multiple_checks(self):
        tcs = [
            {"check": "shape", "expected": [10, 3]},
            {"check": "columns", "expected": ["x", "y", "z"]},
        ]
        script = create_dataframe_eval_script(tcs)
        assert "df.shape" in script
        assert "df.columns" in script

    def test_output_is_valid_python(self):
        tcs = [{"check": "shape", "expected": [5, 2], "id": "t"}]
        script = create_dataframe_eval_script(tcs)
        compile(script, "<test>", "exec")
