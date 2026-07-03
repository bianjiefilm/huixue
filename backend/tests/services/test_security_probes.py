"""
安全探针测试: 防泄题 / 防刷分。

意义: 确保 draft_validator 的攻击矩阵能真正把"刷分"提交判定为不合格 —
一个纯 stub / hardcode 提交，绝不能被判定为通过评测门禁。
如果这类探针失败，意味着攻击门禁被绕过，是一个安全性 (而非功能性) 缺陷。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.draft_validator.attack_engine import (
    ATTACK_THRESHOLDS,
    build_hardcode_submission,
    build_identity_submission,
    build_shape_only_submission,
    build_stub_submission,
    run_attack_matrix,
    run_pytest_module,
)

PYTEST_MODULES_DIR = (
    Path(__file__).resolve().parents[2] / "app" / "services" / "pytest_modules"
)
SAMPLE_TEST_FILE = PYTEST_MODULES_DIR / "test_wind06.py"

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


@pytest.mark.slow
class TestStubSubmissionRejected:
    """核心安全断言: 纯 stub 提交必须被判定为不合格，不能绕过评测拿分。"""

    def test_pure_stub_submission_fails_all_or_nearly_all_tests(self, sample_test_content):
        stub_code = build_stub_submission(REFERENCE_CODE)
        result = run_pytest_module(
            test_file_name="test_wind06.py",
            test_file_content=sample_test_content,
            student_module_name="student_wind06",
            student_code=stub_code,
        )
        assert result.total > 0, "样例测试文件未能正常收集到测试用例"
        assert result.fail_rate == 1.0, (
            f"安全漏洞: stub 提交 fail_rate 应为 1.0（100% 不合格），实际: {result.fail_rate}. "
            f"这意味着学生仅靠 pass/return None 就能通过部分测试，攻击门禁被绕过。"
        )

    def test_stub_submission_judged_unqualified_by_attack_matrix(self, sample_test_content):
        """从 draft_validator 攻击矩阵整体视角断言: stub 攻击类别必须达标(不合格判定生效)。"""
        matrix = run_attack_matrix(
            test_file_name="test_wind06.py",
            test_file_content=sample_test_content,
            student_module_name="student_wind06",
            reference_code=REFERENCE_CODE,
        )
        stub_detail = matrix.detail["stub"]
        assert stub_detail["meets_threshold"] is True, (
            f"安全漏洞: stub 攻击未达标 (threshold={ATTACK_THRESHOLDS['stub']})，"
            f"意味着 evaluator 无法拦截纯 stub 刷分提交。detail={stub_detail}"
        )
        assert stub_detail["fail_rate"] == 1.0


@pytest.mark.slow
class TestOtherCheapAttacksRejected:
    """其余 3 类低成本攻击 (hardcode/shape/identity) 同样必须被拦截 (>=80% fail)。"""

    def test_hardcode_submission_mostly_rejected(self, sample_test_content):
        code = build_hardcode_submission(REFERENCE_CODE)
        result = run_pytest_module(
            test_file_name="test_wind06.py",
            test_file_content=sample_test_content,
            student_module_name="student_wind06",
            student_code=code,
        )
        assert result.fail_rate >= ATTACK_THRESHOLDS["hardcode"], (
            f"安全漏洞: hardcode 攻击 fail_rate={result.fail_rate} 低于门禁阈值 "
            f"{ATTACK_THRESHOLDS['hardcode']}，刷分提交可能蒙混过关"
        )

    def test_shape_only_submission_mostly_rejected(self, sample_test_content):
        code = build_shape_only_submission(REFERENCE_CODE)
        result = run_pytest_module(
            test_file_name="test_wind06.py",
            test_file_content=sample_test_content,
            student_module_name="student_wind06",
            student_code=code,
        )
        assert result.fail_rate >= ATTACK_THRESHOLDS["shape"], (
            f"安全漏洞: shape-only 攻击 fail_rate={result.fail_rate} 低于门禁阈值 "
            f"{ATTACK_THRESHOLDS['shape']}"
        )

    def test_identity_submission_mostly_rejected(self, sample_test_content):
        code = build_identity_submission(REFERENCE_CODE)
        result = run_pytest_module(
            test_file_name="test_wind06.py",
            test_file_content=sample_test_content,
            student_module_name="student_wind06",
            student_code=code,
        )
        assert result.fail_rate >= ATTACK_THRESHOLDS["identity"], (
            f"安全漏洞: identity 攻击 fail_rate={result.fail_rate} 低于门禁阈值 "
            f"{ATTACK_THRESHOLDS['identity']}"
        )


@pytest.mark.slow
def test_full_attack_matrix_overall_passed_flag_is_true_for_solid_evaluator(sample_test_content):
    """样例 evaluator (test_wind06.py) 本身质量较高时，整体 passed 标志应为 True。

    这是一个探针而非硬性红线：如果某个 evaluator 样例质量不足导致这里失败，
    应该视为该 evaluator 需要加强，而不是弱化本测试断言。
    """
    matrix = run_attack_matrix(
        test_file_name="test_wind06.py",
        test_file_content=sample_test_content,
        student_module_name="student_wind06",
        reference_code=REFERENCE_CODE,
    )
    assert matrix.passed is True, (
        f"样例 evaluator test_wind06.py 未能通过完整 4 类攻击门禁: {matrix.as_dict()}"
    )
