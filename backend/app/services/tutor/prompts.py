"""
tutor 三层提示 prompt 构造

对齐《慧学AI升级方案-v2.md》第十二章「3. 三层提示机制」示例语气：

- 第一层：思路提示（首次提问）
  示例：你可以先检查是否正确读取了文件路径，再确认输出字段数量是否符合任务要求。
- 第二层：错误解释（评测失败后）
  示例：当前错误说明程序没有输出预期字段。你可以检查 DataFrame 是否成功读取，
  以及列名是否和任务要求一致。
- 第三层：局部修正建议（连续失败多次）
  示例：请重点检查 read_csv 的路径参数，以及是否对缺失值进行了处理。
  可以先打印前 5 行确认数据读取是否成功。

以及第十八章「禁止行为清单」：不直接输出完整答案、不直接生成完整代码、
不透露隐藏测试集、不透露教师参考答案、不替学生完成报告、不绕过评测逻辑、
不教学生如何硬编码通过测试。

注意：本模块只接收 context_builder.build_tutor_context 产出的 dict，
该 dict 本身已经物理不含参考答案 / 隐藏测试集（见 context_builder.py 的
函数签名）。这里的"禁止输出完整答案"提示词是第十二章防泄题三层机制里的
第三层「行为约束（软）」，用于双保险，不是唯一防线。
"""

from __future__ import annotations

from typing import Any, Dict, List

_COMMON_RULES = (
    "你是慧学平台的 AI 闯关助教，帮助学生在实践关卡中卡关时获得启发，而不是替学生完成任务。\n"
    "硬性规则（不可违反）：\n"
    "1. 不输出完整参考答案或完整可运行代码，只给思路、方向或局部片段提示。\n"
    "2. 不透露隐藏测试集内容或存在细节。\n"
    "3. 不建议学生用硬编码 / 特判 / 绕过评测逻辑的方式通过测试。\n"
    "4. 不替学生代写报告或完整提交内容。\n"
    "5. 语气鼓励、简洁，聚焦在帮助学生自己想明白问题出在哪。\n"
)

_LEVEL_INSTRUCTIONS = {
    1: (
        "当前是第一层【思路提示】（学生首次提问）。只给方向性的检查建议，"
        "不解释具体报错细节，不给代码。参考语气：'你可以先检查是否正确读取了文件路径，"
        "再确认输出字段数量是否符合任务要求。'"
    ),
    2: (
        "当前是第二层【错误解释】（评测已失败）。可以结合评测报错信息，解释报错大致指向"
        "什么问题，并给出检查方向，但不给出修复后的完整代码。参考语气：'当前错误说明程序"
        "没有输出预期字段。你可以检查 DataFrame 是否成功读取，以及列名是否和任务要求一致。'"
    ),
    3: (
        "当前是第三层【局部修正建议】（学生已连续失败多次）。可以给出更具体的局部建议"
        "（比如该检查哪个函数/哪个参数/哪一步），但仍然不给出完整实现代码，不直接写出最终"
        "答案。参考语气：'请重点检查 read_csv 的路径参数，以及是否对缺失值进行了处理。"
        "可以先打印前 5 行确认数据读取是否成功。'"
    ),
}


def _format_context_block(context: Dict[str, Any]) -> str:
    """把 context_builder 产出的 dict 渲染成 prompt 里的上下文文本块。"""
    lines: List[str] = []

    lines.append("【任务说明】")
    lines.append(context.get("task_instructions") or "（无）")

    submission = context.get("student_submission")
    lines.append("\n【学生当前代码/提交内容】")
    if submission:
        if context.get("student_submission_truncated"):
            lines.append(submission + "\n...(内容过长，已截断)")
        else:
            lines.append(submission)
    else:
        lines.append("（学生尚未提交）")

    visible_tests = context.get("visible_test_cases") or []
    lines.append("\n【可见测试集】")
    lines.append(str(visible_tests) if visible_tests else "（无）")

    lines.append("\n【评测报错信息】")
    lines.append(context.get("eval_error") or "（暂无报错，学生主动提问）")

    lines.append("\n【历史失败次数】")
    lines.append(str(context.get("failure_count", 0)))

    skill_tags = context.get("skill_tags") or []
    lines.append("\n【技能标签】")
    lines.append("、".join(skill_tags) if skill_tags else "（无）")

    return "\n".join(lines)


def build_hint_prompt(level: int, context: Dict[str, Any], question: str = "") -> List[Dict[str, str]]:
    """
    构造三层提示的 system/user messages，直接喂给 doubao_client.chat_completion。

    Args:
        level: 提示层级，1/2/3，对齐第十二章三层提示机制。
        context: context_builder.build_tutor_context 的返回值，只包含
            允许字段（不含参考答案/隐藏测试集，物理隔离已在上游完成）。
        question: 学生本次提出的问题文本，可为空。

    Returns:
        [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
    """
    if level not in _LEVEL_INSTRUCTIONS:
        raise ValueError(f"非法的提示层级: {level!r}，只支持 1/2/3")

    system_content = _COMMON_RULES + "\n" + _LEVEL_INSTRUCTIONS[level]

    user_content = _format_context_block(context)
    if question:
        user_content += f"\n\n【学生的问题】\n{question}"
    user_content += "\n\n请给出符合当前层级要求的一段中文提示（不要输出完整代码/完整答案）。"

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]
