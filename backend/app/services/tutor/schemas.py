"""
tutor 输出/输入结构定义

字段对齐《慧学AI升级方案-v2.md》第十六章「学生端 AI 辅导」接口设计
（`POST /api/ai/student-hints` 请求/返回示例）。

这里的 pydantic 模型只用于 tutor 内部对请求/响应做结构校验，
不是 backend/app/models/models.py 里的 ORM 模型，也不落库。
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class StudentHintRequest(BaseModel):
    """
    对齐方案第十六章 `POST /api/ai/student-hints` 请求体。

    hint_level 对齐第十二章「三层提示机制」：
    1 = 思路提示（首次提问）
    2 = 错误解释（评测失败后）
    3 = 局部修正建议（连续失败多次）
    """

    challenge_id: str = Field(..., description="关卡 ID")
    question: str = Field(..., description="学生的问题，如“为什么我的评测失败？”")
    eval_error: Optional[str] = Field(None, description="评测报错信息，可为空（未评测过）")
    hint_level: int = Field(..., ge=1, le=3, description="提示层级：1/2/3")

    @field_validator("challenge_id", "question")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("字段不能为空字符串")
        return v.strip()


class StudentHintResponse(BaseModel):
    """对齐方案第十六章 `POST /api/ai/student-hints` 返回体。"""

    hint_level: int = Field(..., ge=1, le=3, description="本次实际返回的提示层级")
    message: str = Field(..., description="AI 提示内容，已经过输出过滤")
