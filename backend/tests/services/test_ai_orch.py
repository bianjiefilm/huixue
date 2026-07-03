"""
针对 backend/app/services/ai_orch/orchestrator.py 的单元测试。

mock 掉 doubao_client 的网络调用 (get_doubao_client().chat_completion)，
覆盖:
- JSON 解析成功路径
- JSON 解析失败重试后仍失败 -> 抛 AIOrchestrationError
- 字段缺失 (pydantic 校验失败) -> 抛 AIOrchestrationError
- 编造来源 (source_chunk_id 不在输入 chunks 里) -> 抛 AIOrchestrationError
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.services.ai_orch.orchestrator import (
    AIOrchestrationError,
    extract_knowledge_points,
    generate_challenge_drafts,
)


def _fake_response(content: str, prompt_tokens=100, completion_tokens=50):
    """构造一个符合 doubao_client.chat_completion 返回结构的假响应。"""
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def _patch_client(mock_chat_completion):
    """返回一个 patch 上下文，替换 get_doubao_client() 的返回对象。"""
    fake_client = AsyncMock()
    fake_client.chat_completion = mock_chat_completion
    return patch(
        "app.services.ai_orch.orchestrator.get_doubao_client",
        return_value=fake_client,
    )


VALID_CHUNKS = [
    {"chunk_id": "chunk_001", "page": 1, "content": "Python 列表推导式用于..."},
    {"chunk_id": "chunk_002", "page": 2, "content": "字典的 get 方法..."},
]

VALID_KNOWLEDGE_POINT_ITEM = {
    "name": "列表推导式",
    "summary": "使用列表推导式简化循环创建列表的写法",
    "source_chunk_id": "chunk_001",
    "source_location": "第1页",
    "suggested_difficulty": "入门",
    "suggested_for_challenge": True,
    "is_practical_skill": True,
}

VALID_CHALLENGE_DRAFT_ITEM = {
    "challenge_name": "实现一个列表推导式练习",
    "difficulty": "入门",
    "skill_tags": ["python", "列表推导式"],
    "task_instructions": "请完成 task.py 中的函数",
    "evaluation_mode": "自动评测",
    "student_task_file": "task.py",
    "task_file_template": "def solve(x):\n    pass",
    "evaluation_script_file": "test_task.py",
    "evaluation_command": "python test_task.py",
    "visible_test_cases": [{"input": "1", "output": "1"}],
    "hidden_test_cases": [{"input": "2", "output": "2"}],
    "reference_solution": "def solve(x):\n    return x",
    "submission_requirements": None,
    "grading_rubric": None,
    "failure_hint_rules": "第一次失败提示语法错误，第二次提示逻辑思路",
    "source_knowledge_point_ids": ["kp_1"],
    "source_location": "第1页",
}


# ---------------------------------------------------------------------------
# extract_knowledge_points: JSON 解析成功路径
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_extract_knowledge_points_success():
    response = _fake_response(json.dumps([VALID_KNOWLEDGE_POINT_ITEM], ensure_ascii=False))
    mock_chat = AsyncMock(return_value=response)

    with _patch_client(mock_chat):
        result = await extract_knowledge_points(VALID_CHUNKS, objective="教Python基础", student_level="入门")

    assert len(result) == 1
    assert result[0].name == "列表推导式"
    assert result[0].source_chunk_id == "chunk_001"
    mock_chat.assert_awaited_once()


@pytest.mark.asyncio
async def test_extract_knowledge_points_strips_markdown_fence():
    fenced = "```json\n" + json.dumps([VALID_KNOWLEDGE_POINT_ITEM], ensure_ascii=False) + "\n```"
    response = _fake_response(fenced)
    mock_chat = AsyncMock(return_value=response)

    with _patch_client(mock_chat):
        result = await extract_knowledge_points(VALID_CHUNKS, objective="教Python基础", student_level="入门")

    assert len(result) == 1


@pytest.mark.asyncio
async def test_extract_knowledge_points_empty_chunks_raises_without_calling_client():
    mock_chat = AsyncMock()
    with _patch_client(mock_chat):
        with pytest.raises(AIOrchestrationError):
            await extract_knowledge_points([], objective="教Python基础", student_level="入门")
    mock_chat.assert_not_awaited()


# ---------------------------------------------------------------------------
# JSON 解析失败重试后仍失败 -> 抛 AIOrchestrationError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_extract_knowledge_points_json_parse_fails_retries_then_raises():
    # 两次调用都返回非法 JSON
    bad_response = _fake_response("这不是合法JSON，模型瞎输出了一段文字")
    mock_chat = AsyncMock(return_value=bad_response)

    with _patch_client(mock_chat):
        with pytest.raises(AIOrchestrationError):
            await extract_knowledge_points(VALID_CHUNKS, objective="教Python基础", student_level="入门")

    # 断言确实重试了 (最多 2 次)
    assert mock_chat.await_count == 2


@pytest.mark.asyncio
async def test_extract_knowledge_points_retry_succeeds_on_second_attempt():
    bad_response = _fake_response("not json at all")
    good_response = _fake_response(json.dumps([VALID_KNOWLEDGE_POINT_ITEM], ensure_ascii=False))
    mock_chat = AsyncMock(side_effect=[bad_response, good_response])

    with _patch_client(mock_chat):
        result = await extract_knowledge_points(VALID_CHUNKS, objective="教Python基础", student_level="入门")

    assert len(result) == 1
    assert mock_chat.await_count == 2


@pytest.mark.asyncio
async def test_extract_knowledge_points_non_array_json_raises():
    # 顶层是对象而不是数组
    response = _fake_response(json.dumps({"not": "an array"}))
    mock_chat = AsyncMock(return_value=response)

    with _patch_client(mock_chat):
        with pytest.raises(AIOrchestrationError):
            await extract_knowledge_points(VALID_CHUNKS, objective="教Python基础", student_level="入门")


# ---------------------------------------------------------------------------
# 字段缺失 -> pydantic ValidationError 包装为 AIOrchestrationError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_extract_knowledge_points_missing_field_raises():
    incomplete_item = dict(VALID_KNOWLEDGE_POINT_ITEM)
    del incomplete_item["source_location"]  # 缺必填字段
    response = _fake_response(json.dumps([incomplete_item], ensure_ascii=False))
    mock_chat = AsyncMock(return_value=response)

    with _patch_client(mock_chat):
        with pytest.raises(AIOrchestrationError):
            await extract_knowledge_points(VALID_CHUNKS, objective="教Python基础", student_level="入门")


@pytest.mark.asyncio
async def test_extract_knowledge_points_invalid_difficulty_enum_raises():
    bad_item = dict(VALID_KNOWLEDGE_POINT_ITEM)
    bad_item["suggested_difficulty"] = "超级困难"  # 不在允许的枚举值内
    response = _fake_response(json.dumps([bad_item], ensure_ascii=False))
    mock_chat = AsyncMock(return_value=response)

    with _patch_client(mock_chat):
        with pytest.raises(AIOrchestrationError):
            await extract_knowledge_points(VALID_CHUNKS, objective="教Python基础", student_level="入门")


# ---------------------------------------------------------------------------
# 编造来源: source_chunk_id 不在输入 chunks 里 -> 抛 AIOrchestrationError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_extract_knowledge_points_fabricated_source_chunk_id_raises():
    fabricated_item = dict(VALID_KNOWLEDGE_POINT_ITEM)
    fabricated_item["source_chunk_id"] = "chunk_999"  # 不存在于 VALID_CHUNKS
    response = _fake_response(json.dumps([fabricated_item], ensure_ascii=False))
    mock_chat = AsyncMock(return_value=response)

    with _patch_client(mock_chat):
        with pytest.raises(AIOrchestrationError, match="编造来源|不存在的 source_chunk_id"):
            await extract_knowledge_points(VALID_CHUNKS, objective="教Python基础", student_level="入门")


# ---------------------------------------------------------------------------
# generate_challenge_drafts: 成功路径 + 校验路径
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_challenge_drafts_success():
    response = _fake_response(json.dumps([VALID_CHALLENGE_DRAFT_ITEM], ensure_ascii=False))
    mock_chat = AsyncMock(return_value=response)

    with _patch_client(mock_chat):
        result = await generate_challenge_drafts(
            [{"id": "kp_1", "name": "列表推导式"}], student_level="入门", challenge_count=1
        )

    assert len(result) == 1
    assert result[0].challenge_name == "实现一个列表推导式练习"


@pytest.mark.asyncio
async def test_generate_challenge_drafts_empty_knowledge_points_raises():
    mock_chat = AsyncMock()
    with _patch_client(mock_chat):
        with pytest.raises(AIOrchestrationError):
            await generate_challenge_drafts([], student_level="入门", challenge_count=1)
    mock_chat.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_challenge_drafts_non_positive_count_raises():
    mock_chat = AsyncMock()
    with _patch_client(mock_chat):
        with pytest.raises(AIOrchestrationError):
            await generate_challenge_drafts(
                [{"id": "kp_1", "name": "x"}], student_level="入门", challenge_count=0
            )
    mock_chat.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_challenge_drafts_auto_eval_missing_required_fields_raises():
    incomplete = dict(VALID_CHALLENGE_DRAFT_ITEM)
    incomplete["evaluation_mode"] = "自动评测"
    incomplete["reference_solution"] = None  # 自动评测模式下必填字段缺失
    incomplete["evaluation_script_file"] = None
    response = _fake_response(json.dumps([incomplete], ensure_ascii=False))
    mock_chat = AsyncMock(return_value=response)

    with _patch_client(mock_chat):
        with pytest.raises(AIOrchestrationError, match="缺少字段"):
            await generate_challenge_drafts(
                [{"id": "kp_1", "name": "x"}], student_level="入门", challenge_count=1
            )


@pytest.mark.asyncio
async def test_generate_challenge_drafts_manual_review_missing_fields_raises():
    manual = dict(VALID_CHALLENGE_DRAFT_ITEM)
    manual["evaluation_mode"] = "人工验收"
    manual["submission_requirements"] = None
    manual["grading_rubric"] = None
    response = _fake_response(json.dumps([manual], ensure_ascii=False))
    mock_chat = AsyncMock(return_value=response)

    with _patch_client(mock_chat):
        with pytest.raises(AIOrchestrationError, match="submission_requirements|grading_rubric"):
            await generate_challenge_drafts(
                [{"id": "kp_1", "name": "x"}], student_level="入门", challenge_count=1
            )


@pytest.mark.asyncio
async def test_generate_challenge_drafts_json_parse_failure_retries_then_raises():
    bad_response = _fake_response("not valid json output")
    mock_chat = AsyncMock(return_value=bad_response)

    with _patch_client(mock_chat):
        with pytest.raises(AIOrchestrationError):
            await generate_challenge_drafts(
                [{"id": "kp_1", "name": "x"}], student_level="入门", challenge_count=1
            )
    assert mock_chat.await_count == 2


@pytest.mark.asyncio
async def test_generate_challenge_drafts_empty_skill_tags_raises():
    bad_item = dict(VALID_CHALLENGE_DRAFT_ITEM)
    bad_item["skill_tags"] = []  # pydantic 校验：列表字段不能为空
    response = _fake_response(json.dumps([bad_item], ensure_ascii=False))
    mock_chat = AsyncMock(return_value=response)

    with _patch_client(mock_chat):
        with pytest.raises(AIOrchestrationError):
            await generate_challenge_drafts(
                [{"id": "kp_1", "name": "x"}], student_level="入门", challenge_count=1
            )


# ---------------------------------------------------------------------------
# 响应结构异常 (缺 choices / 无法取出 content)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_extract_knowledge_points_missing_choices_raises():
    mock_chat = AsyncMock(return_value={"usage": {}})  # 无 choices 字段
    with _patch_client(mock_chat):
        with pytest.raises(AIOrchestrationError):
            await extract_knowledge_points(VALID_CHUNKS, objective="x", student_level="入门")
    assert mock_chat.await_count == 2
