"""
ai_orch 输出结构定义

字段对齐《慧学AI升级方案-v2.md》:
- KnowledgePoint 对齐第六章「知识点拆解确认页」表格字段
- ChallengeDraft 对齐第八章「AI 生成的关卡草稿结构」表格字段

这里的 pydantic 模型只用于 ai_orch 内部对 LLM 输出做结构校验，
不是 backend/app/models/models.py 里的 ORM 模型，也不落库。
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class KnowledgePoint(BaseModel):
    """
    对齐方案第六章「知识点确认」表格字段。

    来源必须可追溯到具体 chunk / 页码，杜绝无来源的编造内容。
    """

    name: str = Field(..., description="知识点名称")
    summary: str = Field(..., description="简要说明：这个知识点讲什么")
    source_chunk_id: str = Field(..., description="来源 chunk_id，用于追溯资料原文")
    source_location: str = Field(..., description="来源位置，如第几页 / 哪个章节")
    suggested_difficulty: Literal["零基础", "入门", "中等", "综合"] = Field(
        ..., description="建议难度"
    )
    suggested_for_challenge: bool = Field(
        ..., description="是否建议转为实践任务"
    )
    is_practical_skill: bool = Field(
        default=True, description="是否已转化为可实践的技能点（而非泛泛的概念点）"
    )

    @field_validator("name", "summary", "source_chunk_id", "source_location")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("字段不能为空字符串")
        return v.strip()


class ChallengeDraft(BaseModel):
    """
    对齐方案第八章「AI 生成的关卡草稿结构」表格字段。

    docstring 泄题红线（继承自慧学 evaluator 标准）：
    - task_instructions / task_file_template 中的 docstring 只描述
      "函数应返回什么"，不得写算法公式或算法步骤。
    - 不内嵌完整可运行参考实现，只用伪代码 + 提示。
    这条红线由生成 prompt 侧约束，本 schema 只做结构校验，不做语义校验。
    """

    challenge_name: str = Field(..., description="关卡名称")
    difficulty: Literal["零基础", "入门", "中等", "综合"] = Field(..., description="难度")
    skill_tags: List[str] = Field(..., description="技能标签")
    task_instructions: str = Field(..., description="过关任务，Markdown 格式任务说明")
    evaluation_mode: Literal["自动评测", "人工验收"] = Field(..., description="评测方式")

    # 自动评测型关卡字段（人工验收型可为空）
    student_task_file: Optional[str] = Field(None, description="学生任务文件，如 task.py")
    task_file_template: Optional[str] = Field(
        None, description="任务文件模板：留空代码 / TODO / 注释"
    )
    evaluation_script_file: Optional[str] = Field(
        None, description="评测执行文件，如 test_task.py"
    )
    evaluation_command: Optional[str] = Field(
        None, description="评测命令，如 python test_task.py"
    )
    visible_test_cases: Optional[List[dict]] = Field(
        None, description="可见测试集：学生可看到的输入输出"
    )
    hidden_test_cases: Optional[List[dict]] = Field(
        None, description="隐藏测试集：学生不可见，用于防硬编码"
    )
    reference_solution: Optional[str] = Field(
        None, description="参考答案，仅教师端可见"
    )

    # 人工验收型关卡字段（自动评测型可为空）
    submission_requirements: Optional[str] = Field(
        None, description="提交要求：报告 / 截图 / 文件 / 链接等"
    )
    grading_rubric: Optional[str] = Field(None, description="评分 Rubric")

    failure_hint_rules: str = Field(..., description="失败提示规则：评测失败时 AI 如何提示")
    source_knowledge_point_ids: List[str] = Field(
        ..., description="来源知识点 ID 列表"
    )
    source_location: str = Field(..., description="来源资料位置：第几页 / 哪个章节")

    @field_validator("challenge_name", "task_instructions", "failure_hint_rules", "source_location")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("字段不能为空字符串")
        return v.strip()

    @field_validator("skill_tags", "source_knowledge_point_ids")
    @classmethod
    def _non_empty_list(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("列表字段不能为空")
        return v
