"""
针对 backend/app/services/draft_validator/attack_engine.py 的单元测试。

使用仓库真实的 backend/app/services/pytest_modules/test_wind06.py 作为样例
evaluator 文件，配合手写的参考答案 (reference_code)，实际用 subprocess 跑
pytest 断言:
- Stub 攻击 fail_rate == 1.0
- Hardcode / Shape / Identity 攻击 fail_rate >= 0.8
- check_redlines 返回结构正确 (dict key 结构)，不要求全部关卡 all_passed=true

这些测试会真实 fork subprocess 跑 pytest，属于慢测试范畴，属预期行为。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.draft_validator.attack_engine import (
    ATTACK_THRESHOLDS,
    AttackEngine,
    AttackMatrixResult,
    check_redlines,
    run_attack_matrix,
    run_pytest_module,
)

PYTEST_MODULES_DIR = (
    Path(__file__).resolve().parents[2] / "app" / "services" / "pytest_modules"
)
SAMPLE_TEST_FILE = PYTEST_MODULES_DIR / "test_wind06.py"

# 参考答案：满足 test_wind06.py 里对 student_wind06 模块的全部断言。
REFERENCE_CODE = '''
def clean_extension_events(rows):
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    cleaned = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        entity_id = row.get("entity_id")
        if not entity_id:
            continue
        risk_score = row.get("risk_score", 0)
        if isinstance(risk_score, bool):
            risk_score = 0
        try:
            risk_score = float(risk_score)
        except (TypeError, ValueError):
            risk_score = 0.0
        risk_score = max(0.0, min(1.0, risk_score))

        def _num(key, default=0):
            v = row.get(key, default)
            try:
                v = float(v)
            except (TypeError, ValueError):
                v = float(default)
            return max(0.0, v)

        business_value = _num("business_value", 0)
        action_cost = _num("action_cost", 0)
        if "impact" in row:
            impact = _num("impact", 0)
        else:
            impact = business_value - action_cost

        cleaned.append({
            "entity_id": entity_id,
            "risk_score": risk_score,
            "business_value": business_value,
            "action_cost": action_cost,
            "impact": impact,
            "category": row.get("category", ""),
        })
    cleaned.sort(key=lambda r: (-r["risk_score"], r["entity_id"]))
    return cleaned


def rank_extension_actions(rows):
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    actions = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("entity_id"):
            continue
        risk_score = row.get("risk_score", 0)
        business_value = row.get("business_value", 0)
        action_cost = row.get("action_cost", 0)
        net_gain = business_value - action_cost
        priority_score = risk_score * 100
        if risk_score >= 0.8:
            priority_score += 20
            action = "immediate"
        elif risk_score >= 0.3:
            action = "scheduled"
        else:
            action = "monitor"
        actions.append({
            "entity_id": row["entity_id"],
            "action": action,
            "priority_score": priority_score,
            "net_gain": net_gain,
        })
    actions.sort(key=lambda a: -a["priority_score"])
    return actions


def summarize_extension_report(rows, actions):
    if not isinstance(actions, list):
        actions = []
    valid_actions = [a for a in actions if isinstance(a, dict)]
    event_count = len(rows) if isinstance(rows, list) else 0
    total_value = sum(r.get("business_value", 0) for r in rows) if isinstance(rows, list) else 0
    immediate_actions = sum(1 for a in valid_actions if a.get("action") == "immediate")
    scheduled_actions = sum(1 for a in valid_actions if a.get("action") == "scheduled")
    expected_net_gain = sum(a.get("net_gain", 0) for a in valid_actions)

    if immediate_actions > 0:
        status = "urgent"
    elif scheduled_actions > 0:
        status = "watch"
    else:
        status = "stable"

    return {
        "event_count": event_count,
        "total_value": total_value,
        "immediate_actions": immediate_actions,
        "scheduled_actions": scheduled_actions,
        "expected_net_gain": expected_net_gain,
        "status": status,
    }
'''


@pytest.fixture(scope="module")
def sample_test_content():
    assert SAMPLE_TEST_FILE.exists(), f"样例文件不存在: {SAMPLE_TEST_FILE}"
    return SAMPLE_TEST_FILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def reference_ok(sample_test_content):
    """前置条件：参考答案本身必须能通过样例测试文件，否则攻击测试结论不可信。"""
    result = run_pytest_module(
        test_file_name="test_wind06.py",
        test_file_content=sample_test_content,
        student_module_name="student_wind06",
        student_code=REFERENCE_CODE,
    )
    assert result.total > 0, (
        f"参考答案跑起来 total=0，无法作为攻击测试基准。stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    return result


@pytest.mark.slow
class TestAttackMatrix:
    def test_reference_solution_mostly_passes(self, reference_ok):
        # 参考答案应该大部分通过（不要求 100%，因为手写实现可能与原始 student 实现细节略有差异）
        assert reference_ok.passed >= reference_ok.total * 0.7, (
            f"参考答案通过率过低，样例基准不可靠: passed={reference_ok.passed}/{reference_ok.total}\n"
            f"stdout_tail={reference_ok.stdout[-2000:]}"
        )

    def test_stub_attack_fail_rate_is_full(self, sample_test_content, reference_ok):
        matrix = run_attack_matrix(
            test_file_name="test_wind06.py",
            test_file_content=sample_test_content,
            student_module_name="student_wind06",
            reference_code=REFERENCE_CODE,
        )
        assert isinstance(matrix, AttackMatrixResult)
        assert matrix.stub_fail_rate == 1.0, (
            f"Stub 攻击 fail_rate 应为 1.0，实际: {matrix.stub_fail_rate}\n"
            f"detail={matrix.detail.get('stub')}"
        )

    def test_hardcode_attack_fail_rate_meets_threshold(self, sample_test_content):
        matrix = run_attack_matrix(
            test_file_name="test_wind06.py",
            test_file_content=sample_test_content,
            student_module_name="student_wind06",
            reference_code=REFERENCE_CODE,
        )
        assert matrix.hardcode_fail_rate >= ATTACK_THRESHOLDS["hardcode"], (
            f"Hardcode 攻击 fail_rate 应 >= {ATTACK_THRESHOLDS['hardcode']}，"
            f"实际: {matrix.hardcode_fail_rate}\ndetail={matrix.detail.get('hardcode')}"
        )

    def test_shape_attack_fail_rate_meets_threshold(self, sample_test_content):
        matrix = run_attack_matrix(
            test_file_name="test_wind06.py",
            test_file_content=sample_test_content,
            student_module_name="student_wind06",
            reference_code=REFERENCE_CODE,
        )
        assert matrix.shape_fail_rate >= ATTACK_THRESHOLDS["shape"], (
            f"Shape-only 攻击 fail_rate 应 >= {ATTACK_THRESHOLDS['shape']}，"
            f"实际: {matrix.shape_fail_rate}\ndetail={matrix.detail.get('shape')}"
        )

    def test_identity_attack_fail_rate_meets_threshold(self, sample_test_content):
        matrix = run_attack_matrix(
            test_file_name="test_wind06.py",
            test_file_content=sample_test_content,
            student_module_name="student_wind06",
            reference_code=REFERENCE_CODE,
        )
        assert matrix.identity_fail_rate >= ATTACK_THRESHOLDS["identity"], (
            f"Identity 攻击 fail_rate 应 >= {ATTACK_THRESHOLDS['identity']}，"
            f"实际: {matrix.identity_fail_rate}\ndetail={matrix.detail.get('identity')}"
        )

    def test_attack_matrix_as_dict_structure(self, sample_test_content):
        matrix = run_attack_matrix(
            test_file_name="test_wind06.py",
            test_file_content=sample_test_content,
            student_module_name="student_wind06",
            reference_code=REFERENCE_CODE,
        )
        d = matrix.as_dict()
        for key in (
            "stub_fail_rate",
            "hardcode_fail_rate",
            "shape_fail_rate",
            "identity_fail_rate",
            "passed",
            "detail",
        ):
            assert key in d
        for attack_type in ("stub", "hardcode", "shape", "identity"):
            assert attack_type in d["detail"]
            entry = d["detail"][attack_type]
            for field in ("fail_rate", "total", "passed", "failed", "threshold", "meets_threshold"):
                assert field in entry

    def test_attack_engine_class_wraps_run(self, sample_test_content):
        engine = AttackEngine(
            test_file_name="test_wind06.py",
            test_file_content=sample_test_content,
            student_module_name="student_wind06",
        )
        result = engine.run(reference_code=REFERENCE_CODE)
        assert isinstance(result, AttackMatrixResult)
        assert result.stub_fail_rate == 1.0


@pytest.mark.slow
class TestRunPytestModule:
    def test_run_pytest_module_stub_all_fail(self, sample_test_content):
        stub_code = "def clean_extension_events(rows):\n    pass\n\ndef rank_extension_actions(rows):\n    pass\n\ndef summarize_extension_report(rows, actions):\n    pass\n"
        result = run_pytest_module(
            test_file_name="test_wind06.py",
            test_file_content=sample_test_content,
            student_module_name="student_wind06",
            student_code=stub_code,
        )
        assert result.total > 0
        assert result.fail_rate == 1.0
        assert result.ok_ran is True

    def test_run_pytest_module_timeout_flag(self, sample_test_content):
        # 制造一个会挂起的学生代码，验证 timeout 分支返回结构
        hanging_code = (
            "import time\n"
            "def clean_extension_events(rows):\n    time.sleep(30)\n\n"
            "def rank_extension_actions(rows):\n    return []\n\n"
            "def summarize_extension_report(rows, actions):\n    return {}\n"
        )
        result = run_pytest_module(
            test_file_name="test_wind06.py",
            test_file_content=sample_test_content,
            student_module_name="student_wind06",
            student_code=hanging_code,
            timeout=2,
        )
        assert result.timed_out is True
        assert result.ok_ran is False
        assert result.fail_rate == 1.0


# ---------------------------------------------------------------------------
# check_redlines: 返回结构 (不要求所有关卡 all_passed=true)
# ---------------------------------------------------------------------------


class TestCheckRedlines:
    def test_check_redlines_return_structure(self, sample_test_content):
        result = check_redlines([{"test_code": sample_test_content}])
        assert "matrix" in result
        assert "all_passed" in result
        assert isinstance(result["matrix"], dict)
        assert isinstance(result["all_passed"], bool)

        # 每个函数应有 5 列红线检查结果
        for func_name, row in result["matrix"].items():
            for col in (
                "r1_min3_inputs",
                "r2_boundary",
                "r3_negative_type_assert",
                "r4_tolerance_not_eq",
                "r5_full_coverage_assert",
            ):
                assert col in row, f"函数 {func_name} 缺少红线列 {col}"
                assert isinstance(row[col], bool)

    def test_check_redlines_empty_input_fails_gracefully(self):
        result = check_redlines([])
        assert result["all_passed"] is False
        assert "error" in result

    def test_check_redlines_no_test_functions_fails_gracefully(self):
        result = check_redlines([{"test_code": "x = 1\ny = 2\n"}])
        assert result["all_passed"] is False
        assert "error" in result

    def test_check_redlines_syntax_error_reports_error(self):
        result = check_redlines([{"test_code": "def test_broken(:\n    pass"}])
        assert result["all_passed"] is False
        assert "error" in result

    def test_check_redlines_structured_entries_supported(self):
        code = (
            "def test_add_case1(): assert add(1, 2) == 3\n"
            "def test_add_case2(): assert add(-1, 1) == 0\n"
            "def test_add_case3(): assert add(0, 0) == 0\n"
            "def test_add_boundary(): assert add(0, 0) == 0\n"
            "def test_add_type():\n"
            "    import pytest\n"
            "    with pytest.raises(TypeError): add('a', 1)\n"
        )
        result = check_redlines([{"function": "add", "test_code": code}])
        assert "matrix" in result
        assert "add" in result["matrix"]
