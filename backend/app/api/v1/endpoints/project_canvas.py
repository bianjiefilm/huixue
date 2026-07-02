"""
Project Canvas API Endpoints
项目画布 API 端点 - 获取实训项目的星图数据
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from pydantic import BaseModel

from app.api.deps import get_db
from app.core.security import get_current_user
from app.models import models
from app.utils.canvas_helpers import (
    get_status_color as _get_status_color,
    node_status_from_publish,
    node_size_from_hours,
    distribute_nodes_deterministic,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Response Models ====================

class ProjectNode(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = None
    progress: Optional[int] = None
    status: str  # completed, in_progress, warning, pending, default
    x: float
    y: float
    size: str  # large, medium, small
    color: str
    connections: List[str] = []
    trainingType: Optional[str] = None
    difficulty: Optional[str] = None
    industry: Optional[str] = None


class ProjectCanvasResponse(BaseModel):
    success: bool
    nodes: List[ProjectNode]
    totalProjects: int
    completedCount: int
    inProgressCount: int


# ==================== Helpers (delegates to pure functions) ====================

def calculate_node_status(training: models.Training) -> str:
    """根据实训状态计算节点状态"""
    status_val = training.publish_status.value if training.publish_status else ""
    return node_status_from_publish(status_val)


def get_status_color(status: str) -> str:
    return _get_status_color(status)


def calculate_node_size(training: models.Training) -> str:
    return node_size_from_hours(training.course_hours)


def distribute_nodes(count: int) -> List[Dict[str, float]]:
    return distribute_nodes_deterministic(count)


# ==================== Endpoints ====================

@router.get("/canvas", response_model=ProjectCanvasResponse)
async def get_project_canvas(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取项目画布数据
    
    返回所有实训项目的节点数据，用于星图可视化
    """
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        
        # 查询所有实训项目
        trainings = db.query(models.Training).filter(
            or_(
                models.Training.creator_id == user_id,
                models.Training.visibility == models.TrainingVisibilityEnum.PUBLIC
            )
        ).order_by(models.Training.created_at.desc()).limit(12).all()
        
        if not trainings:
            # 如果没有实训，返回空数据
            return ProjectCanvasResponse(
                success=True,
                nodes=[],
                totalProjects=0,
                completedCount=0,
                inProgressCount=0
            )
        
        # 分配节点位置
        positions = distribute_nodes(len(trainings))
        
        # 构建节点数据
        nodes = []
        completed_count = 0
        in_progress_count = 0
        
        for i, training in enumerate(trainings):
            status = calculate_node_status(training)
            
            if status == "completed":
                completed_count += 1
            elif status in ["in_progress", "pending"]:
                in_progress_count += 1
            
            # 计算进度（基于发布状态）
            progress = None
            if status == "completed":
                progress = 100
            elif status == "in_progress":
                progress = 50
            elif status == "pending":
                progress = 75
            
            # 获取难度作为副标题
            subtitle = None
            if training.difficulty:
                difficulty_map = {
                    "BEGINNER": "入门",
                    "INTERMEDIATE": "中级",
                    "ADVANCED": "高级"
                }
                subtitle = difficulty_map.get(training.difficulty.value, training.difficulty.value)
            
            # 计算连接（简单实现：相同行业或类型的项目相连）
            connections = []
            for j, other in enumerate(trainings):
                if i != j:
                    # 同行业连接
                    if training.industry and other.industry and training.industry == other.industry:
                        connections.append(str(other.id))
                    # 同类型连接
                    elif training.training_type and other.training_type and training.training_type == other.training_type:
                        if str(other.id) not in connections:
                            connections.append(str(other.id))
            
            # 限制连接数量
            connections = connections[:3]
            
            node = ProjectNode(
                id=str(training.id),
                title=training.title,
                subtitle=subtitle,
                progress=progress,
                status=status,
                x=positions[i]["x"],
                y=positions[i]["y"],
                size=calculate_node_size(training),
                color=get_status_color(status),
                connections=connections,
                trainingType=training.training_type.value if training.training_type else None,
                difficulty=training.difficulty.value if training.difficulty else None,
                industry=training.industry
            )
            nodes.append(node)
        
        return ProjectCanvasResponse(
            success=True,
            nodes=nodes,
            totalProjects=len(nodes),
            completedCount=completed_count,
            inProgressCount=in_progress_count
        )
        
    except Exception as e:
        logger.error(f"获取项目画布数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取项目画布数据失败: {str(e)}")


@router.get("/canvas/node/{node_id}")
async def get_project_node_detail(
    node_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取单个项目节点的详细信息"""
    try:
        training = db.query(models.Training).filter(
            models.Training.id == node_id
        ).first()
        
        if not training:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        return {
            "success": True,
            "data": {
                "id": training.id,
                "title": training.title,
                "intro": training.intro,
                "industry": training.industry,
                "difficulty": training.difficulty.value if training.difficulty else None,
                "trainingType": training.training_type.value if training.training_type else None,
                "courseHours": training.course_hours,
                "publishStatus": training.publish_status.value if training.publish_status else None,
                "createdAt": training.created_at.isoformat() if training.created_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")

