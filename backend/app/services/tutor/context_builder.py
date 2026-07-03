"""
tutor 上下文物理隔离（本任务安全核心）

对齐《慧学AI升级方案-v2.md》第十二章「2. AI 可读取的上下文（物理隔离）」表格：

| 上下文 | 是否允许 |
|--------|---------|
| 当前关卡任务说明 | 允许 |
| 学生当前代码 / 提交内容 | 允许，但限制长度 |
| 可见测试集 | 允许 |
| 评测报错信息 | 允许 |
| 学生历史失败次数 | 允许 |
| 技能标签 | 允许 |
| 参考答案 | 不允许（不进 context） |
| 隐藏测试集 | 不允许（不进 context） |
| 教师私有评语 | 不允许 |

关键机制（方案原文）：
"参考答案与隐藏测试集在服务端组装 prompt 时物理排除，不依赖提示词
'请不要透露'这种软约束。模型拿不到的东西，永远泄露不出去。"

因此本模块的强制手段不是"参数传了但不用"，而是函数签名本身：
build_tutor_context 根本不接收 reference_answer / hidden_test_cases /
teacher_private_comment 这几个参数名。调用方即便手里有这些数据，
也没有任何入口把它们传进 tutor context —— 这是签名级别的边界，
不是运行时判断出来的边界。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# 学生当前代码限长（字符数），避免超长提交打爆 prompt / 变相泄露上下文预算
STUDENT_SUBMISSION_MAX_CHARS = 4000


def build_tutor_context(
    challenge_task_instructions: str,
    student_submission: Optional[str],
    visible_test_cases: Optional[List[Dict[str, Any]]],
    eval_error: Optional[str],
    failure_count: int,
    skill_tags: Optional[List[str]],
) -> Dict[str, Any]:
    """
    组装学生端 AI 辅导可见的上下文（物理隔离实现）。

    注意这个函数签名本身就是安全边界：它只接受方案第十二章表格里
    「允许」的六项——任务说明 / 学生当前代码（限长）/ 可见测试集 /
    评测报错 / 历史失败次数 / 技能标签。

    它**没有** reference_answer 参数，**没有** hidden_test_cases 参数，
    **没有** teacher_private_comment 参数。调用方如果手上有这些数据，
    物理上无法通过这个函数传入学生端 context —— 不是"传了但函数不用"，
    而是函数根本不接收，callers 在类型检查阶段就会报错。

    Args:
        challenge_task_instructions: 当前关卡任务说明（Markdown）。
        student_submission: 学生当前代码 / 提交内容，允许为空（未提交过）。
            会被截断到 STUDENT_SUBMISSION_MAX_CHARS。
        visible_test_cases: 可见测试集（学生可看到的输入输出），不是隐藏测试集。
        eval_error: 评测报错信息，可为空。
        failure_count: 学生在本关卡的历史失败次数。
        skill_tags: 本关卡技能标签。

    Returns:
        只包含允许字段的 dict，直接喂给 prompts.build_hint_prompt。
    """
    truncated_submission: Optional[str] = None
    submission_truncated = False
    if student_submission:
        if len(student_submission) > STUDENT_SUBMISSION_MAX_CHARS:
            truncated_submission = student_submission[:STUDENT_SUBMISSION_MAX_CHARS]
            submission_truncated = True
        else:
            truncated_submission = student_submission

    return {
        "task_instructions": challenge_task_instructions,
        "student_submission": truncated_submission,
        "student_submission_truncated": submission_truncated,
        "visible_test_cases": visible_test_cases or [],
        "eval_error": eval_error,
        "failure_count": max(0, failure_count),
        "skill_tags": skill_tags or [],
    }
