"""
AI 编排服务 (ai_orch)

对齐《慧学AI升级方案-v2.md》第六、七、十七章:
- 知识点拆解 (extract_knowledge_points)
- 关卡草稿生成 (generate_challenge_drafts)

本模块只负责调用 doubao_client 完成 LLM 编排、解析与校验，不做任何数据库读写。
调用方（API 层 / 任务编排层）负责把返回的 usage dict 落库到 AIUsageLog。
"""

from .orchestrator import (
    AIOrchestrationError,
    extract_knowledge_points,
    generate_challenge_drafts,
)
from .schemas import ChallengeDraft, KnowledgePoint

__all__ = [
    "AIOrchestrationError",
    "extract_knowledge_points",
    "generate_challenge_drafts",
    "KnowledgePoint",
    "ChallengeDraft",
]
