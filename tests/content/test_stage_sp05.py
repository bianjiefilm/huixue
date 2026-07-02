"""
Stage SP-5 (RDD Transformation与Action) TDD tests.
"""
from __future__ import annotations
import ast, json, re, subprocess
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
JSON_FILE = PROJECT_ROOT / "output" / "stage_spark_01-06.json"
YAML_FILE = PROJECT_ROOT / "content_orchestrator" / "stages_config" / "spark" / "stage_5.yaml"

@pytest.fixture(scope="module")
def raw_json() -> dict:
    assert JSON_FILE.exists(), f"JSON not found: {JSON_FILE}"
    with open(JSON_FILE, encoding="utf-8") as f:
        data = json.load(f)
    if "stages" in data:
        for s in data["stages"]:
            if s.get("task_id") == 5:
                return s
        pytest.fail("task_id=5 not found")
    return data

@pytest.fixture(scope="module")
def stage_config() -> dict:
    import yaml
    with open(YAML_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="module")
def handbook(raw_json: dict) -> str:
    return raw_json.get("handbook_markdown") or raw_json.get("handbook", "")

@pytest.fixture(scope="module")
def questions(raw_json: dict) -> list[dict]:
    return raw_json.get("question_data", {}).get("questions") or raw_json.get("questions", [])

@pytest.fixture(scope="module")
def baseline_code(raw_json: dict) -> str:
    return raw_json.get("baseline_code") or raw_json.get("question_data", {}).get("baseline_code") or ""

@pytest.fixture(scope="module")
def test_cases(raw_json: dict) -> list[dict]:
    return raw_json.get("test_cases") or raw_json.get("question_data", {}).get("test_cases", [])

class TestBasicStructure:
    def test_json_has_required_fields(self, raw_json: dict):
        hb = raw_json.get("handbook_markdown") or raw_json.get("handbook", "")
        qs = raw_json.get("question_data", {}).get("questions") or raw_json.get("questions", [])
        tcs = raw_json.get("test_cases") or raw_json.get("question_data", {}).get("test_cases", [])
        assert hb, "Missing handbook"
        assert qs, "Missing questions"
        assert tcs, "Missing test_cases"

    def test_handbook_min_chars(self, handbook: str, stage_config: dict):
        min_chars = stage_config["expected_handbook_min_chars"]
        assert len(handbook) >= min_chars, f"Handbook {len(handbook)} chars < {min_chars}"

    def test_questions_count(self, questions: list[dict], stage_config: dict):
        expected = stage_config.get("expected_questions_count") or stage_config.get("expected_questions", 10)
        assert len(questions) >= expected - 1

    def test_visible_test_cases(self, test_cases: list[dict], stage_config: dict):
        visible = [tc for tc in test_cases if not tc.get("hidden", False)]
        assert len(visible) == stage_config["expected_test_cases_visible"]

    def test_hidden_test_cases(self, test_cases: list[dict], stage_config: dict):
        hidden = [tc for tc in test_cases if tc.get("hidden", False)]
        assert len(hidden) == stage_config["expected_test_cases_hidden"]

class TestContentConsistency:
    def test_answers_in_options(self, questions: list[dict]):
        failures = []
        for q in questions:
            opts = q.get("options")
            if opts is None:
                continue
            answer = str(q.get("answer", "")).strip()
            in_opts = any(str(opt).strip().startswith(answer) for opt in opts)
            if not in_opts:
                failures.append(f"{q.get('id','?')}: answer={answer!r} not in options")
        assert not failures, "\n".join(failures)

    def test_baseline_code_incomplete(self, baseline_code: str):
        if not baseline_code:
            pytest.skip("No baseline_code")
        try:
            ast.parse(baseline_code)
        except SyntaxError:
            pytest.fail(f"SyntaxError in baseline_code")
        has_marker = bool(re.search(r"\bTODO\b|\bFIXME\b", baseline_code, re.IGNORECASE))
        has_stub = False
        try:
            tree = ast.parse(baseline_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    body = node.body
                    if len(body) == 1 and isinstance(body[0], ast.Pass):
                        has_stub = True
                    elif not any(isinstance(n, ast.Return) for n in ast.walk(node)) and len(body) > 1:
                        has_stub = True
        except:
            pass
        assert has_marker or has_stub, "baseline_code appears complete"

class TestTestCases:
    def test_visibility_split(self, test_cases: list[dict]):
        visible = [tc for tc in test_cases if not tc.get("hidden", False)]
        hidden = [tc for tc in test_cases if tc.get("hidden", False)]
        assert len(visible) >= 2, f"Need >=2 visible, got {len(visible)}"
        assert len(hidden) >= 2, f"Need >=2 hidden, got {len(hidden)}"
        assert not test_cases[0].get("hidden", False)
        assert not test_cases[1].get("hidden", False)
        if len(test_cases) >= 4:
            assert test_cases[2].get("hidden", False)
            assert test_cases[3].get("hidden", False)

    def test_boundary_case_exists(self, test_cases: list[dict]):
        BOUNDARY = {"0", "1", ""}
        has_boundary = any(tc.get("input", "").strip() in BOUNDARY for tc in test_cases)
        assert has_boundary

    def test_expected_no_trailing_newline(self, test_cases: list[dict]):
        failures = [f"{tc['input']!r}: expected ends with \\n" for tc in test_cases if tc.get("expected", "").endswith("\n")]
        assert not failures, "\n".join(failures)
