"""
Stage Configuration Schema — Pydantic model for YAML-based stage definitions.

本文件定义"关卡规划配置"，即人工编写、长期稳定的 YAML 文件结构。
仅描述"这关要做什么"和"生成约束"，不包含实际内容（handbook、questions 等）。

与 content schema 的分工：
  - StageConfig  → 我手写，commit 进 git，长期稳定
  - ContentSchema → Claude Code 生成，存 output/，随 review 迭代变化
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator


# =============================================================================
# 辅助类型（约束扩展字段的值域）
# =============================================================================


# P1-1 约束：custom_constraints 的值必须是 str | int | bool | float | list | dict
_CONSTRAINT_TYPES = (str, int, bool, float, list, dict)

# P1-1 约束：metadata 的值必须是 str | int | bool | float | list
_METADATA_TYPES = (str, int, bool, float, list)


# =============================================================================
# 主模型
# =============================================================================


class StageConfig(BaseModel):
    """
    整关规划的根模型，对应一个 YAML 文件。

    本模型只包含规划信息，不包含实际内容。
    YAML 编写者可独立完成配置，无需了解 content schema 的结构。
    """

    # --------------------------------------------------------------------------
    # 必填字段：关卡标识
    # --------------------------------------------------------------------------

    stage_id: Annotated[
        str,
        Field(
            description="关卡唯一标识，格式必须为 'stage_N'（N 为数字），如 'stage_2'。不可与已有关卡重复。"
        ),
    ]
    """
    关卡 ID，用于关联数据库记录和前端路由。
    格式约束：必须匹配正则 ^stage_\\d+$（如 stage_2、stage_11）。
    """

    course: Annotated[
        str,
        Field(description="所属课程标识，如 'python'、'neural_network'。用于课程分类。"),
    ]
    """
    所属课程方向（小写英文），用于课程目录结构和路由。
    示例：'python'、'data_mining'、'neural_network'。
    """

    course_db_id: Annotated[
        int,
        Field(ge=1, description="数据库中对应的 course 记录 ID，用于关联关卡与课程。"),
    ]
    """
    数据库中 courses 表的主键 ID。
    创建关卡记录时需要此 ID 关联到正确的课程。
    """

    title: Annotated[
        str,
        Field(min_length=1, description="关卡中文标题，展示给学习者。如 '函数与作用域'。"),
    ]
    """关卡标题，将显示在课程页面和导航中。"""

    difficulty: Annotated[
        str,
        Field(
            description="关卡整体难度等级：beginner（入门）/ intermediate（进阶）/ advanced（综合）。"
        ),
    ]
    """
    难度等级，影响前端标签和推荐学习路径。
    枚举值：beginner / intermediate / advanced。
    """

    # --------------------------------------------------------------------------
    # 必填字段：生成目标
    # --------------------------------------------------------------------------

    knowledge_points: Annotated[
        list[str],
        Field(min_length=1, description="核心知识点清单，是 Claude Code 生成素材的依据。至少 1 个。"),
    ]
    """
    核心知识点列表，是生成 handbook 和题目的直接依据。
    示例：['for循环', 'while循环', 'break语句', 'continue语句', 'range()函数', '列表推导式']
    """

    expected_handbook_min_chars: Annotated[
        int,
        Field(ge=1, default=500, description="要求生成的手册正文最小字符数（汉字+标点）。用于质量门槛。"),
    ]
    """
    学习手册正文的最低字数要求。
    低于此值视为生成不完整，需要补写。
    """

    expected_questions_count: Annotated[
        int,
        Field(ge=1, default=10, description="要求生成的题目总数。用于质量门槛。"),
    ]
    """
    题目总数要求，包括 concept / calculation / coding 三类。
    低于此值视为生成不完整。
    """

    expected_test_cases_visible: Annotated[
        int,
        Field(ge=0, default=2, description="要求 visible 测试用例的数量（hidden=false）。"),
    ]
    """
    可见测试用例数量，会展示给学习者作为参考。
    通常 1-3 条，覆盖标准输入/输出。
    """

    expected_test_cases_hidden: Annotated[
        int,
        Field(ge=0, default=2, description="要求 hidden 测试用例的数量（hidden=true）。"),
    ]
    """
    隐藏测试用例数量，仅用于自动化评分。
    通常 1-3 条，覆盖边界值和防作弊用例。
    """

    total_score: Annotated[
        int,
        Field(ge=1, default=100, description="整关总分。具体分配由 Claude Code 自行决定，无需预设。"),
    ]
    """
    关卡总分（满分）。
    Claude Code 在生成测试用例时自行决定每条用例的分值，总分不超过此值。
    """

    # --------------------------------------------------------------------------
    # 可选字段：约束与引导
    # --------------------------------------------------------------------------

    style_reference: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="风格参考，可以是文字描述或引用已有 YAML 的 stage_id 列表。用于保持风格一致。",
        ),
    ]
    """
    风格参考列表。
    - 文字描述示例：['参考关卡1的手册风格，使用简短段落+代码块交替']
    - 引用示例：['stage_1', 'stage_5']（复用已有关卡的文风）
    """

    prerequisites: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="前置关卡 ID 列表。学习者需先完成这些关卡才能解锁当前关卡。",
        ),
    ]
    """
    前置关卡，用于学习路径控制。
    示例：['stage_1'] 表示需要先完成 stage_1。
    """

    topics_to_avoid: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="本关需要回避的话题列表。用于避免与前置关卡内容重复。",
        ),
    ]
    """
    回避话题，防止生成内容与已有知识重复。
    示例：['递归'（本关讲循环，下关再讲递归）]
    """

    baseline_code_hint: Annotated[
        str,
        Field(
            default="",
            description="基线代码模板提示（非强制）。描述学习者打开题目时的初始代码应包含什么。",
        ),
    ]
    """
    基线代码提示，供 Claude Code 参考，不强制要求。
    示例：'提供一个包含 input() 的空循环框架，学生需要补全循环体'。
    """

    codex_review_required: Annotated[
        bool,
        Field(
            default=True,
            description="生成完成后是否触发 Codex 自动审查。关闭可节省 token，但失去质量保障。",
        ),
    ]
    """
    Codex 自动审查开关。
    True（默认）：生成后运行 Codex review，通过后标记完成。
    False：跳过 Codex review，直接进入下一关。
    """

    # --------------------------------------------------------------------------
    # 扩展字段（给未来特殊关卡留白）
    # --------------------------------------------------------------------------

    custom_constraints: Annotated[
        dict,
        Field(
            default_factory=dict,
            description=(
                "自定义约束字典，用于未来扩展。示例：\n"
                "  - required_libraries: ['numpy']    # 强制要求使用特定库\n"
                "  - forbid_keywords: ['goto']        # 禁止使用的关键词\n"
                "  - max_code_lines: 50              # 代码最大行数限制\n"
                "  - dataset_path: 'data/iris.csv'   # 要求使用特定数据集\n"
                "所有扩展字段均通过此字典传入，不影响核心校验逻辑。"
            ),
        ),
    ]
    """
    自定义约束，供特殊关卡使用。
    核心 schema 不处理此字段的内容，由 downstream 代码解释。
    """

    metadata: Annotated[
        dict,
        Field(
            default_factory=dict,
            description="元数据字典，存放 author、created_at、version 等审计信息。",
        ),
    ]
    """
    元数据，用于版本追踪和审计。
    建议包含：author（编写者）、version（YAML 自身版本）、created_at（创建时间）。
    """

    # --------------------------------------------------------------------------
    # 校验器
    # --------------------------------------------------------------------------

    @field_validator("stage_id")
    @classmethod
    def stage_id_format(cls, v: str) -> str:
        """强制 stage_id 格式为 stage_N（N 为数字）。"""
        import re

        if not re.match(r"^stage_\d+$", v):
            raise ValueError(
                f"stage_id 格式错误：'{v}' 不匹配 'stage_N' 格式。"
                " 正确示例：stage_2、stage_11"
            )
        return v

    @field_validator("difficulty")
    @classmethod
    def difficulty_enum(cls, v: str) -> str:
        """difficulty 仅允许预定义的三级。"""
        allowed = {"beginner", "intermediate", "advanced"}
        if v not in allowed:
            raise ValueError(
                f"difficulty 值非法：'{v}'。可选值：{sorted(allowed)}"
            )
        return v

    @model_validator(mode="after")
    def _validate_constraints_and_list_items(self) -> "StageConfig":
        """
        P1-1: custom_constraints 值类型校验（str | int | bool | float | list | dict）
        P1-1: metadata 值类型校验（str | int | bool | float | list）
        P1-2: style_reference / prerequisites / topics_to_avoid 条目非空校验
        P1-2: knowledge_points 条目非空校验（原有逻辑，合并到这里）
        """
        # P1-1: custom_constraints
        for k, v in self.custom_constraints.items():
            if not isinstance(v, _CONSTRAINT_TYPES):
                raise ValueError(
                    f"custom_constraints['{k}'] 类型非法："
                    f"got {type(v).__name__}，期望 str | int | bool | float | list | dict"
                )

        # P1-1: metadata
        for k, v in self.metadata.items():
            if not isinstance(v, _METADATA_TYPES):
                raise ValueError(
                    f"metadata['{k}'] 类型非法："
                    f"got {type(v).__name__}，期望 str | int | bool | float | list"
                )

        # P1-2: knowledge_points 条目非空
        for item in self.knowledge_points:
            if not item.strip():
                raise ValueError(
                    "knowledge_points 中不允许空字符串条目。"
                    " 请移除或填充空白知识点。"
                )

        # P1-2: style_reference 条目非空
        for item in self.style_reference:
            if not item.strip():
                raise ValueError(
                    "style_reference 中不允许空字符串条目。"
                )

        # P1-2: prerequisites 条目非空
        for item in self.prerequisites:
            if not item.strip():
                raise ValueError(
                    "prerequisites 中不允许空字符串条目。"
                )

        # P1-2: topics_to_avoid 条目非空
        for item in self.topics_to_avoid:
            if not item.strip():
                raise ValueError(
                    "topics_to_avoid 中不允许空字符串条目。"
                )

        return self
