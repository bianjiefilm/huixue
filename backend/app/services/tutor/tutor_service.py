"""
tutor_service 组装

对齐《慧学AI升级方案-v2.md》第十二章「学生端 AI 闯关辅导助手」整体流程：
context_builder（物理隔离组装 prompt 上下文，不含参考答案/隐藏测试集）
  -> prompts（三层提示 system/user messages）
  -> doubao_client（复用 backend/app/services/doubao_client.py 现成客户端）
  -> output_filter（单独传参考答案做相似度过滤，仅用于比对不用于生成）

设计约束（对齐 ai_orch/orchestrator.py 的风格）：
- 不在这里写数据库，调用方自行落库辅导日志 / AIUsageLog。
- get_hint 的 reference_answer_for_filter_only 参数名刻意写得很长，
  提醒调用方和未来维护者：这个参数只能流向 output_filter.filter_response，
  绝不能流向 context_builder.build_tutor_context 或 prompts.build_hint_prompt
  （这两个函数的签名本身也不接受这个参数，见 context_builder.py 注释）。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.services.doubao_client import get_doubao_client

from .context_builder import build_tutor_context
from .output_filter import filter_response
from .prompts import build_hint_prompt
from .schemas import StudentHintRequest, StudentHintResponse

logger = logging.getLogger(__name__)


class TutorServiceError(Exception):
    """tutor_service 调用失败的统一异常，对齐 ai_orch 的 AIOrchestrationError 风格。"""


async def get_hint(
    request: StudentHintRequest,
    challenge_context: Dict[str, Any],
    reference_answer_for_filter_only: Optional[str] = None,
) -> StudentHintResponse:
    """
    生成一次学生端 AI 提示。

    Args:
        request: 学生端请求（challenge_id / question / eval_error / hint_level）。
        challenge_context: 调用方（endpoint 层）从数据库查出的关卡上下文，
            只应包含 context_builder.build_tutor_context 需要的字段：
            task_instructions / student_submission / visible_test_cases /
            failure_count / skill_tags。**不要**把 reference_answer 或
            hidden_test_cases 塞进这个 dict 传进来——build_tutor_context
            的函数签名根本不接受这两个字段，传了也没有入口能被使用。
        reference_answer_for_filter_only: 参考答案代码，只会被传给
            output_filter.filter_response 做相似度比对，不会进入 prompt。
            该关卡若是人工验收型/无参考答案，传 None 即可。

    Returns:
        StudentHintResponse，message 字段已经过 output_filter 过滤。

    Raises:
        TutorServiceError: doubao_client 调用失败，或返回内容为空。
    """
    context = build_tutor_context(
        challenge_task_instructions=challenge_context.get("task_instructions", ""),
        student_submission=challenge_context.get("student_submission"),
        visible_test_cases=challenge_context.get("visible_test_cases"),
        eval_error=request.eval_error,
        failure_count=challenge_context.get("failure_count", 0),
        skill_tags=challenge_context.get("skill_tags"),
    )

    messages: List[Dict[str, str]] = build_hint_prompt(
        level=request.hint_level, context=context, question=request.question
    )

    client = get_doubao_client()
    try:
        raw_reply = await client.simple_chat(
            user_message=messages[-1]["content"],
            system_prompt=messages[0]["content"],
            temperature=0.5,
            max_tokens=600,
            use_cache=False,  # 辅导内容含学生个人提交/报错，不做跨请求缓存复用
        )
    except Exception as exc:
        logger.error("tutor_service 调用 doubao_client 失败: %s", exc)
        raise TutorServiceError(f"AI 辅导服务调用失败: {exc}") from exc

    if not raw_reply or not raw_reply.strip():
        raise TutorServiceError("AI 辅导服务返回空内容")

    filter_result = filter_response(raw_reply, reference_answer_for_filter_only)
    if filter_result["was_filtered"]:
        logger.warning(
            "tutor_service 输出被过滤: challenge_id=%s hint_level=%s reason=%s",
            request.challenge_id,
            request.hint_level,
            filter_result["reason"],
        )

    return StudentHintResponse(
        hint_level=request.hint_level,
        message=str(filter_result["filtered_text"]),
    )
