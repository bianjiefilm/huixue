"""
微型实验API接口
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from app.core.database import get_db
from app.models.models import Practice
from app.schemas.schemas import PracticeResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/practice"
    # tags removed - using tags from main.py include_router instead
)

@router.get("/lists", tags=["微型实验"])
async def get_practice_materials(
    limit: int = Query(12, ge=1, le=100),
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    categories: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取微型实验列表"""
    logger.info(f"Fetching practice materials - page: {page}, limit: {limit}, search: {search}")
    
    # 计算偏移量
    offset = (page - 1) * limit
    
    # 构建查询
    query = db.query(Practice)
    
    # 搜索过滤
    if search:
        query = query.filter(Practice.title.contains(search))
    
    # 方向过滤
    if direction:
        query = query.filter(Practice.direction.contains(direction))
    
    # 难度过滤
    if difficulty:
        query = query.filter(Practice.difficulty == difficulty)
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    practices = query.offset(offset).limit(limit).all()
    
    logger.info(f"Found {len(practices)} practice materials, total: {total}")
    
    # 转换为响应格式
    practice_list = []
    for practice in practices:
        practice_list.append({
            "id": practice.id,
            "title": practice.title,
            "description": practice.description,
            "cover_url": practice.cover_url,
            "difficulty": practice.difficulty.value if hasattr(practice.difficulty, 'value') else practice.difficulty,
            "direction": practice.direction,
            "category": practice.category,
            "categories": practice.categories,
            "task_count": practice.task_count,
            "coin": practice.coin,
            "summary": practice.summary,
            "intro": practice.intro,
            "publish_status": practice.publish_status.value if practice.publish_status else None,
            "visibility": practice.visibility.value if practice.visibility else None,
            "created_at": practice.created_at,
            "updated_at": practice.updated_at
        })
    
    return {
        "code": 1,
        "data": {
            "list": practice_list,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        },
        "msg": "success"
    }

@router.get("/{practice_id}", tags=["微型实验"])
async def get_practice_material_detail(practice_id: int, db: Session = Depends(get_db)):
    """获取微型实验详情"""
    logger.info(f"Fetching practice material detail for ID: {practice_id}")
    
    practice = db.query(Practice).options(
        selectinload(Practice.tasks),
        selectinload(Practice.skills)
    ).filter(Practice.id == practice_id).first()
    
    if not practice:
        return {
            "code": 0,
            "data": None,
            "msg": "Practice not found"
        }
    
    # Get tasks data
    tasks = []
    for task in practice.tasks:
        # Parse skills from JSON string
        task_skills = []
        if task.skills:
            try:
                import json
                task_skills = json.loads(task.skills) if isinstance(task.skills, str) else task.skills
            except:
                task_skills = []
        
        tasks.append({
            "id": task.id,
            "title": task.title,
            "description": task.handbook_markdown[:100] + "..." if task.handbook_markdown and len(task.handbook_markdown) > 100 else task.handbook_markdown or "",
            "type": task.task_type.value if task.task_type else None,
            "difficulty": task.difficulty if task.difficulty else None,
            "coin": task.coin,
            "order_in_practice": task.order_in_practice,
            "skills": task_skills
        })
    
    practice_detail = {
        "id": practice.id,
        "title": practice.title,
        "description": practice.description,
        "cover_url": practice.cover_url,
        "difficulty": practice.difficulty.value if hasattr(practice.difficulty, 'value') else practice.difficulty,
        "direction": practice.direction,
        "category": practice.category,
        "categories": practice.categories,
        "task_count": practice.task_count,
        "coin": practice.coin,
        "summary": practice.summary,
        "intro": practice.intro,
        "publish_status": practice.publish_status.value if practice.publish_status else None,
        "visibility": practice.visibility.value if practice.visibility else None,
        "created_at": practice.created_at,
        "updated_at": practice.updated_at,
        "tasks": sorted(tasks, key=lambda x: x.get('order_in_practice', 0)),
        "skills": [{"id": skill.id, "skill_name": skill.skill_name} for skill in practice.skills] if practice.skills else []
    }
    
    return {
        "code": 1,
        "data": practice_detail,
        "msg": "success"
    }