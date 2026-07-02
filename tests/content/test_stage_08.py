"""
Stage 8 (函数与模块) TDD tests.
Red phase: all tests should FAIL on the current output/stage_08_function_module.json.
Green phase: fix JSON until all tests pass.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path

import pytest

# Path constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
JSON_PATH = PROJECT_ROOT / "output" / "stage_08_function_module.json"
YAML_PATH = PROJECT_ROOT / "content_orchestrator" / "stages_config" / "python" / "stage_8.yaml"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def raw_json() -> dict:
    """Load and parse the stage 8 JSON file."""
    assert JSON_PATH.exists(), f"JSON file not found: {JSON_PATH}"
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def stage_config(raw_json: dict) -> dict:
    """Parse stage_8.yaml expectations."""
    import yaml

    assert YAML_PATH.exists(), f"YAML config not found: {YAML_PATH}"
    with open(YAML_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


@pytest.fixture(scope="module")
def handbook(raw_json: dict) -> str:
    return raw_json["handbook_markdown"]


@pytest.fixture(scope="module")
def questions(raw_json: dict) -> list[dict]:
    return raw_json["question_data"]["questions"]


@pytest.fixture(scope="module")
def baseline_code(raw_json: dict) -> str:
    return raw_json["question_data"]["baseline_code"]


@pytest.fixture(scope="module")
def test_cases(raw_json: dict) -> list[dict]:
    return raw_json.get("test_cases") or raw_json["question_data"].get("test_cases", [])


# ---------------------------------------------------------------------------
# 基础断言: JSON 结构
# ---------------------------------------------------------------------------

class TestBasicStructure:
    def test_json_loadable(self, raw_json: dict):
        """JSON must be loadable and top-level keys present."""
        required = {"handbook_markdown", "question_data", "test_cases"}
        missing = required - set(raw_json.keys())
        assert not missing, f"Missing top-level keys: {missing}"
        qd = raw_json["question_data"]
        assert "questions" in qd, "question_data missing 'questions'"
        assert "baseline_code" in qd, "question_data missing 'baseline_code'"

    def test_handbook_min_chars(self, handbook: str, stage_config: dict):
        """Handbook chars must meet expected_handbook_min_chars."""
        min_chars = stage_config["expected_handbook_min_chars"]
        actual = len(handbook)
        assert (
            actual >= min_chars
        ), f"Handbook has {actual} chars, need >= {min_chars}"

    def test_questions_count(self, questions: list[dict], stage_config: dict):
        """Number of questions must be at least expected - 1."""
        expected = stage_config["expected_questions_count"]
        actual = len(questions)
        assert actual >= expected - 1, f"Questions: {actual}, expected >= {expected - 1}"

    def test_visible_test_cases_count(
        self, test_cases: list[dict], stage_config: dict
    ):
        """Visible test cases must match expected_test_cases_visible."""
        expected = stage_config["expected_test_cases_visible"]
        visible = [tc for tc in test_cases if not tc.get("hidden", False)]
        assert len(visible) == expected, (
            f"Visible test cases: {len(visible)}, expected: {expected}"
        )

    def test_hidden_test_cases_count(
        self, test_cases: list[dict], stage_config: dict
    ):
        """Hidden test cases must match expected_test_cases_hidden."""
        expected = stage_config["expected_test_cases_hidden"]
        hidden = [tc for tc in test_cases if tc.get("hidden", False)]
        assert len(hidden) == expected, (
            f"Hidden test cases: {len(hidden)}, expected: {expected}"
        )


# ---------------------------------------------------------------------------
# 内容一致性断言
# ---------------------------------------------------------------------------

class TestContentConsistency:
    def test_answers_in_options(self, questions: list[dict]):
        """Multiple-choice questions: answer must be in options."""
        failures = []
        for q in questions:
            opts = q.get("options")
            if opts is None:
                continue
            answer = q.get("answer", "").strip()
            in_opts = any(opt.strip().startswith(answer) for opt in opts)
            if not in_opts:
                failures.append(
                    f"{q['id']}: answer={answer!r} not in options {opts!r}"
                )
        assert not failures, "\n".join(failures)

    def test_baseline_code_incomplete(self, baseline_code: str):
        """
        baseline_code must NOT be a complete solution.
        Should contain TODO/FIXME/pass stub.
        """
        try:
            tree = ast.parse(baseline_code)
        except SyntaxError:
            pytest.fail(f"baseline_code has SyntaxError: {baseline_code[:100]}")

        has_marker = bool(
            re.search(r"\bTODO\b", baseline_code, re.IGNORECASE)
            or re.search(r"\bFIXME\b", baseline_code, re.IGNORECASE)
        )

        has_stub = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                body = node.body
                if len(body) == 1 and isinstance(body[0], ast.Pass):
                    has_stub = True
                returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
                if not returns and len(body) > 1:
                    has_stub = True

        assert has_marker or has_stub, (
            "baseline_code appears to be a COMPLETE implementation "
            "(no TODO/FIXME marker and function body is not a stub)."
        )

    def test_baseline_code_fails_all_test_cases(
        self, baseline_code: str, test_cases: list[dict]
    ):
        """
        baseline_code should NOT pass any test case.
        If it passes even one, it means it's too complete.
        """
        any_passed = False
        failures_info = []
        for tc in test_cases:
            inp = tc["input"]
            expected = tc["expected"]
            try:
                result = subprocess.run(
                    ["python3", "-c", baseline_code],
                    input=inp,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                got = result.stdout.strip()
                if got == expected.strip():
                    any_passed = True
                    failures_info.append(
                        f"  input={inp!r}: baseline PASSED (got {got!r})"
                    )
            except subprocess.TimeoutExpired:
                pass
            except Exception as e:
                pass

        if any_passed:
            pytest.fail(
                "baseline_code passes at least one test case (should fail ALL):\n"
                + "\n".join(failures_info)
            )


# ---------------------------------------------------------------------------
# test_cases 覆盖断言
# ---------------------------------------------------------------------------

class TestTestCases:
    def test_visibility_split(self, test_cases: list[dict]):
        """First 2 test cases must be visible, last 2 must be hidden."""
        assert len(test_cases) >= 4, f"Need at least 4 test cases, got {len(test_cases)}"
        visible = [tc for tc in test_cases if not tc.get("hidden", False)]
        hidden = [tc for tc in test_cases if tc.get("hidden", False)]
        assert len(visible) >= 2, f"Need >=2 visible, got {len(visible)}"
        assert len(hidden) >= 2, f"Need >=2 hidden, got {len(hidden)}"
        assert not test_cases[0].get("hidden", False), "case_1 must be visible"
        assert not test_cases[1].get("hidden", False), "case_2 must be visible"
        assert test_cases[2].get("hidden", False), "case_3 must be hidden"
        assert test_cases[3].get("hidden", False), "case_4 must be hidden"

    def test_boundary_case_exists(self, test_cases: list[dict]):
        """At least 1 test case must be a boundary case: edge values."""
        BOUNDARY_VALUES = {"32", "212", "0", "100", "98"}
        has_boundary = any(tc["input"] in BOUNDARY_VALUES for tc in test_cases)
        assert has_boundary, (
            f"No boundary case found. Test cases inputs: "
            f"{[tc['input'] for tc in test_cases]}"
        )

    def test_expected_output_no_trailing_newline(self, test_cases: list[dict]):
        """expected_output must NOT end with \\n (评测器 strips)."""
        failures = []
        for tc in test_cases:
            if tc["expected"].endswith("\n"):
                failures.append(
                    f"{tc['input']!r}: expected_output ends with \\n "
                    f"(value: {tc['expected']!r})"
                )
        assert not failures, "\n".join(failures)
