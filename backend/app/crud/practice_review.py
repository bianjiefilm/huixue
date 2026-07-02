"""
实践审核相关的CRUD操作
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models import models
from datetime import datetime, timezone


def get_practices_pending_review(
    db: Session,
    skip: int = 0,
    limit: int = 20
):
    """获取待审核的实践列表"""
    practices = db.query(models.Practice).filter(
        models.Practice.publish_status == models.PracticePublishStatusEnum.PENDING_REVIEW
    ).order_by(models.Practice.submitted_for_review_at.desc()).offset(skip).limit(limit).all()
    
    total = db.query(models.Practice).filter(
        models.Practice.publish_status == models.PracticePublishStatusEnum.PENDING_REVIEW
    ).count()
    
    return practices, total


def approve_practice_review(
    db: Session,
    practice_id: int,
    reviewer_id: int,
    comments: Optional[str] = None
):
    """审核通过实践"""
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.publish_status == models.PracticePublishStatusEnum.PENDING_REVIEW
    ).first()
    
    if not practice:
        return None
    
    # 更新审核状态
    practice.publish_status = models.PracticePublishStatusEnum.PUBLISHED
    practice.reviewed_at = datetime.now(timezone.utc)
    practice.reviewed_by = reviewer_id
    practice.review_comments = comments
    practice.published_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(practice)
    
    return practice


def reject_practice_review(
    db: Session,
    practice_id: int,
    reviewer_id: int,
    comments: str
):
    """审核拒绝实践"""
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.publish_status == models.PracticePublishStatusEnum.PENDING_REVIEW
    ).first()
    
    if not practice:
        return None
    
    # 更新审核状态
    practice.publish_status = models.PracticePublishStatusEnum.REJECTED
    practice.reviewed_at = datetime.now(timezone.utc)
    practice.reviewed_by = reviewer_id
    practice.review_comments = comments
    # 回退到编辑状态，允许重新编辑
    practice.is_published = False
    
    db.commit()
    db.refresh(practice)
    
    return practice


def get_practice_review_history(
    db: Session,
    practice_id: int
):
    """获取实践审核历史"""
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id
    ).first()
    
    if not practice:
        return None
    
    # 构建审核历史信息
    review_history = {
        "practice_id": practice.id,
        "title": practice.title,
        "creator_id": practice.creator_id,
        "current_status": practice.publish_status.value if practice.publish_status else "EDITING",
        "visibility": practice.visibility.value if practice.visibility else "PRIVATE",
        "submitted_for_review_at": practice.submitted_for_review_at,
        "reviewed_at": practice.reviewed_at,
        "reviewed_by": practice.reviewed_by,
        "review_comments": practice.review_comments,
        "published_at": practice.published_at
    }
    
    # 如果有审核人，获取审核人信息
    if practice.reviewed_by:
        reviewer = db.query(models.User).filter(
            models.User.id == practice.reviewed_by
        ).first()
        if reviewer:
            review_history["reviewer_name"] = reviewer.full_name or reviewer.username
    
    return review_history


def check_practice_can_be_edited(
    db: Session,
    practice_id: int,
    creator_id: int
):
    """检查实践是否可以编辑"""
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return False, "实践不存在或无权限"
    
    # 检查是否已被引用到课堂中
    classroom_practice_count = db.query(models.ClassroomPractice).filter(
        models.ClassroomPractice.practice_id == practice_id
    ).count()
    
    if classroom_practice_count > 0:
        return False, "实践已被引用到课堂中，无法切换回编辑状态"
    
    # 检查发布状态
    if practice.publish_status == models.PracticePublishStatusEnum.PENDING_REVIEW:
        return False, "实践正在审核中，无法编辑"
    
    return True, "可以编辑"


def revert_practice_to_editing(
    db: Session,
    practice_id: int,
    creator_id: int
):
    """将实践回退到编辑状态"""
    can_edit, reason = check_practice_can_be_edited(db, practice_id, creator_id)
    
    if not can_edit:
        raise ValueError(reason)
    
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return None
    
    # 回退到编辑状态
    practice.publish_status = models.PracticePublishStatusEnum.EDITING
    practice.is_published = False
    practice.published_at = None
    
    db.commit()
    db.refresh(practice)
    
    return practice 