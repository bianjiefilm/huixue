"""
tutor 输出相似度过滤

对齐《慧学AI升级方案-v2.md》第十二章「4. 防泄题三层机制（升级）」第 2 条：

"输出过滤（硬）：AI 回复落地前做相似度检测——回复与参考答案代码的相似度
超过阈值（如连续 N 行匹配）时截断降级为思路提示；检测'硬编码通过测试'
类建议关键词。"

这是防泄题的第二道硬防线（第一道是 context_builder 的物理隔离）。即使
prompt 没有把参考答案递给模型，模型仍可能凭训练知识/学生贴的代码片段
自己生成出高度相似的答案，所以这里在落地前再做一次基于参考答案的比对。

注意 reference_answer 只在本模块作为「比对基准」传入，绝不用于生成——
调用方（tutor_service）只在过滤这一步单独传参考答案，不会把它交给
context_builder 或 prompts。
"""

from __future__ import annotations

import re
from typing import Dict, Optional

# 连续多少行高度重合就判定为疑似泄题
SIMILAR_LINE_THRESHOLD = 3
# 单行相似度判定阈值（归一化后逐字符比较）
LINE_SIMILARITY_RATIO = 0.85

GENERIC_FALLBACK_MESSAGE = (
    "这里不能直接给你完整代码或答案哦。建议你先梳理一下当前的实现思路，"
    "对照任务要求逐步排查，比如先确认输入输出是否符合预期，再检查关键步骤"
    "的逻辑是否正确。如果还是卡住，可以带着具体报错再来问我。"
)

_HARDCODE_KEYWORDS = (
    "直接返回期望值",
    "硬编码通过测试",
    "把测试用例的答案写死",
    "写死结果",
    "特判掉测试",
    "hardcode",
    "hard-code",
    "hard code",
)


def _normalize_line(line: str) -> str:
    """去掉首尾空白和多余空格，方便做粗粒度行级比较。"""
    return re.sub(r"\s+", " ", line.strip())


def _line_similarity(a: str, b: str) -> float:
    """
    简单的行级相似度：基于最长公共子串长度占较长行长度的比例。

    不引入第三方 diff 库，保持这里逻辑可审计、无外部依赖。
    """
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0

    len_a, len_b = len(a), len(b)
    # dp[i][j] = a[:i] 和 b[:j] 的最长公共子串长度
    dp = [0] * (len_b + 1)
    longest = 0
    for i in range(1, len_a + 1):
        prev_row = dp[:]
        for j in range(1, len_b + 1):
            if a[i - 1] == b[j - 1]:
                dp[j] = prev_row[j - 1] + 1
                longest = max(longest, dp[j])
            else:
                dp[j] = 0
    return longest / max(len_a, len_b)


def _count_consecutive_similar_lines(candidate_lines: list, reference_lines: list) -> int:
    """
    找出 candidate_lines 中与 reference_lines 任意一行高度相似的最长连续段长度。
    """
    ref_set_normalized = [_normalize_line(l) for l in reference_lines if l.strip()]

    max_run = 0
    current_run = 0
    for raw_line in candidate_lines:
        line = _normalize_line(raw_line)
        if not line:
            # 空行不打断连续段判定，也不计入命中
            continue
        matched = any(_line_similarity(line, ref_line) >= LINE_SIMILARITY_RATIO for ref_line in ref_set_normalized)
        if matched:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 0
    return max_run


def _contains_hardcode_advice(text: str) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in _HARDCODE_KEYWORDS)


def filter_response(ai_reply: str, reference_answer: Optional[str]) -> Dict[str, object]:
    """
    对 AI 回复做落地前的相似度过滤，防止即便物理隔离之外仍生成出高相似度答案。

    Args:
        ai_reply: 模型生成的原始回复文本。
        reference_answer: 参考答案代码，仅在本函数用于比对，不用于生成，
            调用方不得把它传给 context_builder / prompts。可为 None
            （比如该关卡是人工验收型，没有参考答案代码）。

    Returns:
        {
            "filtered_text": str,   # 最终应返回给学生的文本
            "was_filtered": bool,   # 是否触发了过滤
            "reason": Optional[str],  # 触发原因，未触发为 None
        }
    """
    if not ai_reply or not ai_reply.strip():
        return {"filtered_text": ai_reply, "was_filtered": False, "reason": None}

    if _contains_hardcode_advice(ai_reply):
        return {
            "filtered_text": GENERIC_FALLBACK_MESSAGE,
            "was_filtered": True,
            "reason": "疑似建议硬编码/绕过测试通过，已替换为通用提示语",
        }

    if reference_answer and reference_answer.strip():
        candidate_lines = ai_reply.splitlines()
        reference_lines = reference_answer.splitlines()
        max_run = _count_consecutive_similar_lines(candidate_lines, reference_lines)
        if max_run >= SIMILAR_LINE_THRESHOLD:
            return {
                "filtered_text": GENERIC_FALLBACK_MESSAGE,
                "was_filtered": True,
                "reason": f"检测到连续 {max_run} 行与参考答案高度重合（阈值 {SIMILAR_LINE_THRESHOLD}），已截断降级",
            }

    return {"filtered_text": ai_reply, "was_filtered": False, "reason": None}
