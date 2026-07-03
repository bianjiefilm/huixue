"""
ai_orch 编排逻辑

调用 backend/app/services/doubao_client.py 里现成的火山方舟客户端完成：
- 知识点拆解（extract_knowledge_points）
- 关卡草稿生成（generate_challenge_drafts）

设计约束（来自任务要求，不可违反）：
- 不在这里写数据库，只返回一个 usage dict 供调用方自行落库到 AIUsageLog
  （字段参考 backend/app/models/models.py 里 AIUsageLog：
  user_id/user_role/feature_type/prompt_tokens/completion_tokens/total_tokens/
  cost_estimate/request_data/response_data/error_message/response_time）。
- JSON 解析失败要重试一次，仍失败则抛出明确异常，不允许静默吞掉、不允许返回空列表。
- 字段完整性用 pydantic schema 校验，不合规则抛异常。
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Tuple

from pydantic import ValidationError

from app.services.doubao_client import get_doubao_client
from .prompts import build_challenge_draft_prompt, build_knowledge_extraction_prompt
from .schemas import ChallengeDraft, KnowledgePoint

logger = logging.getLogger(__name__)


class AIOrchestrationError(Exception):
    """
    ai_orch 编排失败的统一异常。

    覆盖：LLM 响应格式错误、JSON 解析失败（含重试后仍失败）、
    字段校验失败（pydantic ValidationError）等场景。
    不允许调用方把这个异常静默吞掉当作空结果处理。
    """


def _extract_message_content(response: Dict[str, Any]) -> str:
    """从 doubao_client.chat_completion 的原始响应中取出 message content。"""
    choices = response.get("choices")
    if not choices:
        raise AIOrchestrationError(f"AI 响应缺少 choices 字段: {response!r}")
    try:
        return choices[0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIOrchestrationError(f"AI 响应结构异常，无法取出 content: {response!r}") from exc


def _strip_markdown_fence(text: str) -> str:
    """兼容模型偶尔仍用 ```json ... ``` 包裹输出的情况。"""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        # 去掉首行 ``` 或 ```json，以及末尾的 ```
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def _parse_json_array(text: str) -> List[Dict[str, Any]]:
    """
    解析模型输出的 JSON 数组。

    调用方负责重试逻辑；这里只负责单次解析，解析失败抛 AIOrchestrationError
    （不是 json.JSONDecodeError 本身，方便调用方统一捕获），绝不返回空列表当降级。
    """
    cleaned = _strip_markdown_fence(text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIOrchestrationError(
            f"AI 输出不是合法 JSON: {exc}. 原始内容前 500 字符: {cleaned[:500]!r}"
        ) from exc

    if not isinstance(parsed, list):
        raise AIOrchestrationError(
            f"AI 输出 JSON 顶层必须是数组，实际类型: {type(parsed).__name__}"
        )
    return parsed


def _build_usage_dict(
    feature_type: str,
    response: Dict[str, Any],
    elapsed_seconds: float,
    error_message: str | None = None,
) -> Dict[str, Any]:
    """
    构造 usage dict，字段对齐 backend/app/models/models.py 里的 AIUsageLog。

    本函数不写库，调用方拿到这个 dict 自行落库；user_id/user_role 由调用方
    （知道当前请求身份）补齐，这里留空占位。
    """
    usage = response.get("usage", {}) if isinstance(response, dict) else {}
    return {
        "user_id": None,
        "user_role": None,
        "feature_type": feature_type,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "cost_estimate": 0.0,
        "request_data": None,
        "response_data": json.dumps(response, ensure_ascii=False) if response else None,
        "error_message": error_message,
        "response_time": elapsed_seconds,
    }


async def _chat_json_array_with_retry(
    messages: List[Dict[str, str]],
    feature_type: str,
    max_tokens: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    调用 doubao_client.chat_completion 并解析出 JSON 数组，解析失败重试一次。

    返回 (解析后的 JSON 数组, usage dict)。
    两次都失败时抛出 AIOrchestrationError，绝不静默返回空数组。
    """
    client = get_doubao_client()
    last_error: Exception | None = None
    last_response: Dict[str, Any] = {}
    start = time.monotonic()

    for attempt in range(1, 3):  # 最多尝试 2 次（1 次正常 + 1 次重试）
        try:
            response = await client.chat_completion(
                messages,
                max_tokens=max_tokens,
                temperature=0.3,
                # 真实模型冒烟发现的P1 bug: use_cache=True 会让重试命中同一缓存键，
                # 拿到和第一次完全相同的坏响应，重试形同虚设。重试的意义就是给模型
                # 一次独立的新机会，必须关闭缓存。
                use_cache=False,
            )
            last_response = response
            content = _extract_message_content(response)
            parsed = _parse_json_array(content)
            elapsed = time.monotonic() - start
            usage = _build_usage_dict(feature_type, response, elapsed)
            return parsed, usage
        except AIOrchestrationError as exc:
            last_error = exc
            logger.warning(
                "ai_orch JSON 解析失败 (attempt %d/2, feature=%s): %s",
                attempt,
                feature_type,
                exc,
            )
        except Exception as exc:  # 网络/API 错误也计入重试
            last_error = exc
            logger.warning(
                "ai_orch 调用异常 (attempt %d/2, feature=%s): %s",
                attempt,
                feature_type,
                exc,
            )

    elapsed = time.monotonic() - start
    error_message = f"AI 调用/解析连续 2 次失败: {last_error}"
    usage = _build_usage_dict(feature_type, last_response, elapsed, error_message=error_message)
    raise AIOrchestrationError(f"{error_message}. usage={usage!r}") from last_error


async def extract_knowledge_points(
    chunks: List[Dict[str, Any]],
    objective: str,
    student_level: str,
) -> List[KnowledgePoint]:
    """
    知识点拆解（对齐方案第六章 + 第十七章第 2 条）。

    Args:
        chunks: 文档分块列表，每个元素至少包含 chunk_id / content，
            可选 page / section 用于标注来源位置。
        objective: 教师填写的教学目标。
        student_level: 学生水平。

    Returns:
        KnowledgePoint 列表，每个都携带来源 chunk_id / 来源位置，
        字段已通过 pydantic 校验。

    Raises:
        AIOrchestrationError: AI 响应格式错误、JSON 解析连续失败、
            或字段不完整/不合规（pydantic ValidationError）。
    """
    if not chunks:
        raise AIOrchestrationError("extract_knowledge_points 需要至少一个 chunk 作为输入")

    messages = build_knowledge_extraction_prompt(chunks, objective, student_level)
    raw_items, usage = await _chat_json_array_with_retry(
        messages, feature_type="knowledge_extraction", max_tokens=4000
    )

    valid_chunk_ids = {c.get("chunk_id") for c in chunks}
    result: List[KnowledgePoint] = []
    for idx, item in enumerate(raw_items):
        try:
            kp = KnowledgePoint.model_validate(item)
        except ValidationError as exc:
            raise AIOrchestrationError(
                f"知识点第 {idx} 项字段校验失败: {exc}. 原始数据: {item!r}"
            ) from exc

        if kp.source_chunk_id not in valid_chunk_ids:
            raise AIOrchestrationError(
                f"知识点第 {idx} 项引用了不存在的 source_chunk_id={kp.source_chunk_id!r}，"
                f"疑似编造来源。合法 chunk_id 集合: {valid_chunk_ids}"
            )
        result.append(kp)

    if not result:
        raise AIOrchestrationError("AI 未生成任何知识点，疑似输入资料不足或生成失败")

    logger.info(
        "extract_knowledge_points 完成: %d 个知识点, usage=%s",
        len(result),
        {k: usage[k] for k in ("prompt_tokens", "completion_tokens", "total_tokens", "response_time")},
    )
    return result


async def generate_challenge_drafts(
    knowledge_points: List[Dict[str, Any]],
    student_level: str,
    challenge_count: int,
) -> List[ChallengeDraft]:
    """
    关卡草稿生成（对齐方案第七、八章 + 第十七章第 3 条）。

    Args:
        knowledge_points: 教师确认保留的知识点列表（dict 形式，通常来自
            KnowledgePoint.model_dump() 或等价结构，至少包含 id/name 供关联）。
        student_level: 学生水平。
        challenge_count: 期望生成的关卡数量。

    Returns:
        ChallengeDraft 列表，字段对齐方案第八章表格，已通过 pydantic 校验。

    Raises:
        AIOrchestrationError: AI 响应格式错误、JSON 解析连续失败、
            或字段不完整/不合规（pydantic ValidationError）。
    """
    if not knowledge_points:
        raise AIOrchestrationError("generate_challenge_drafts 需要至少一个知识点作为输入")
    if challenge_count <= 0:
        raise AIOrchestrationError(f"challenge_count 必须为正整数，实际: {challenge_count}")

    messages = build_challenge_draft_prompt(knowledge_points, student_level, challenge_count)
    raw_items, usage = await _chat_json_array_with_retry(
        messages, feature_type="challenge_generation", max_tokens=8000
    )

    result: List[ChallengeDraft] = []
    for idx, item in enumerate(raw_items):
        try:
            draft = ChallengeDraft.model_validate(item)
        except ValidationError as exc:
            raise AIOrchestrationError(
                f"关卡草稿第 {idx} 项字段校验失败: {exc}. 原始数据: {item!r}"
            ) from exc

        # 评测方式与必填字段的一致性校验（对齐第八/九章：自动评测必须有可执行的评测要素）
        if draft.evaluation_mode == "自动评测":
            missing = [
                f
                for f in (
                    "student_task_file",
                    "task_file_template",
                    "evaluation_script_file",
                    "evaluation_command",
                    "hidden_test_cases",
                    "reference_solution",
                )
                if not getattr(draft, f)
            ]
            if missing:
                raise AIOrchestrationError(
                    f"关卡草稿第 {idx} 项 evaluation_mode=自动评测 但缺少字段: {missing}"
                )
        else:  # 人工验收
            if not draft.submission_requirements or not draft.grading_rubric:
                raise AIOrchestrationError(
                    f"关卡草稿第 {idx} 项 evaluation_mode=人工验收 但缺少 "
                    "submission_requirements 或 grading_rubric"
                )

        result.append(draft)

    if not result:
        raise AIOrchestrationError("AI 未生成任何关卡草稿，疑似输入知识点不足或生成失败")

    logger.info(
        "generate_challenge_drafts 完成: %d 个关卡草稿, usage=%s",
        len(result),
        {k: usage[k] for k in ("prompt_tokens", "completion_tokens", "total_tokens", "response_time")},
    )
    return result
