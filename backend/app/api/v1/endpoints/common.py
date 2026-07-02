"""
通用API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import uuid
import logging
from datetime import datetime, timezone, timedelta

from app.core.database import get_db, engine, Base
from app.models.models import User, Post
import app.crud.crud as crud
import app.schemas.schemas as schemas
import app.models.models as models

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/api/v1",
    tags=['common']
)

# ==================== 课程实践相关API ====================

@router.get("/filter-tags/practices", response_model=schemas.ApiResponse)
def get_practice_filter_tags(db: Session = Depends(get_db)):
    """获取微型实验筛选标签"""
    try:
        tags = crud.get_practice_filter_tags(db)
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=tags
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/statistics", response_model=schemas.ApiResponse)
def get_statistics(db: Session = Depends(get_db)):
    """获取统计信息"""
    try:
        stats = crud.get_statistics(db)
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=stats
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/organization-tree", response_model=schemas.ApiResponse)
async def get_organization_tree(db: Session = Depends(get_db)):
    """获取组织架构树"""
    try:
        organization_tree = crud.get_organization_tree(db)

        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={"organization_tree": organization_tree}
        )

    except Exception as e:
        logger.error(f"获取组织架构树失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取组织架构树失败: {str(e)}") 