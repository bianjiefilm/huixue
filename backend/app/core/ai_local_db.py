"""
AI 生成流水线专属本地数据库会话。

慧学 AI 升级方案-v2 第十五章新增的 7 张表(ai_generation_jobs 等)在本地开发
阶段独立使用一个 SQLite 文件，不接入 app 主体的 Postgres DATABASE_URL——
这 7 张表全部用 SQLAlchemy 通用列类型（无 PG 专有类型），create_all() 天然
跨方言可用，SQLite 不强制外键约束，因此不需要 api_users/classrooms 等
100+ 个既有模型真实存在即可建表使用。

这是刻意的范围收窄：只把新增的 AI 表挪到本地 SQLite，不动、不审查仓库里
既有的 100+ 个模型是否兼容 SQLite。
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.models import (
    AIGenerationJob,
    AISourceDocument,
    AIDocumentChunk,
    AIKnowledgePoint,
    AIChallengeDraft,
    AIChallengeDraftVersion,
    AIValidationResult,
)

AI_LOCAL_DB_PATH = os.getenv("AI_LOCAL_DB_PATH", os.path.join(
    os.path.dirname(__file__), "..", "..", "..", ".localdev", "ai_pipeline.db"
))

_AI_TABLES = [
    AIGenerationJob.__table__,
    AISourceDocument.__table__,
    AIDocumentChunk.__table__,
    AIKnowledgePoint.__table__,
    AIChallengeDraft.__table__,
    AIChallengeDraftVersion.__table__,
    AIValidationResult.__table__,
]

_engine = create_engine(
    f"sqlite:///{AI_LOCAL_DB_PATH}",
    connect_args={"check_same_thread": False},
)
Base.metadata.create_all(bind=_engine, tables=_AI_TABLES)

AILocalSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_ai_db():
    db = AILocalSession()
    try:
        yield db
    finally:
        db.close()
