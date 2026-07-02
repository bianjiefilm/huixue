"""
我创建的实践管理相关的CRUD操作
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
import json

from app.models import models
from app.schemas import schemas
from app.utils.dashboard_helpers import (
    determine_practice_status as _determine_practice_status_pure,
    increment_version as _increment_version_pure,
)


def get_my_practices_enhanced(
    db: Session,
    creator_id: int,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取我创建的实践列表（增强版）- 支持搜索和状态管理"""
    from sqlalchemy import and_, or_

    # 检查是否有搜索条件，如果有搜索条件则不使用缓存
    use_cache = not keyword

    # 如果使用缓存且是第一页，尝试从缓存获取
    if use_cache and skip == 0:
        try:
            from app.core.cache import get_cache
            cache = get_cache()

            # 获取缓存的实践列表（简化版，只缓存基本信息）
            cached_practices = []
            # 这里简化实现，实际应该有更复杂的缓存策略
            # 对于有搜索的请求，我们还是从数据库查询

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"读取实践缓存失败: {e}")
            use_cache = False

    # 基础查询
    query = db.query(models.Practice).filter(
        models.Practice.creator_id == creator_id
    )
    
    # 关键字搜索
    if keyword:
        query = query.filter(
            models.Practice.title.ilike(f"%{keyword}%")
        )
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    practices = query.order_by(models.Practice.updated_at.desc()).offset(skip).limit(limit).all()
    
    # 转换为摘要格式
    practice_summaries = []
    for practice in practices:
        # 计算关卡数量
        stage_count = db.query(models.Task).filter(
            models.Task.practice_id == practice.id
        ).count()
        
        # 确定前端显示状态
        status = _determine_practice_status(practice)
        
        summary = {
            "id": practice.id,
            "title": practice.title,
            "practice_type": practice.practice_type,
            "difficulty": practice.difficulty.value if practice.difficulty else "intermediate",
            "stage_count": stage_count,
            "coin": practice.coin,
            "status": status,
            "publish_status": practice.publish_status.value if practice.publish_status else None,
            "visibility": practice.visibility.value if practice.visibility else None,
            "is_published": practice.is_published,
            "current_version": getattr(practice, 'current_version', None) or "1.0.0",
            "created_at": practice.created_at,
            "updated_at": practice.updated_at,
            "published_at": practice.published_at,
            "review_comments": practice.review_comments
        }
        practice_summaries.append(summary)
    
    return practice_summaries, total


def _determine_practice_status(practice):
    """根据实践的发布状态和可见性确定前端显示状态"""
    ps = practice.publish_status.value if practice.publish_status else ""
    vis = practice.visibility.value if practice.visibility else None
    return _determine_practice_status_pure(ps, vis, practice.is_published)


def update_practice_status(
    db: Session,
    practice_id: int,
    creator_id: int,
    action: str,
    expected_version: Optional[int] = None,
    **kwargs
):
    """更新实践状态（带乐观锁）"""
    # 验证权限和版本
    query = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    )

    # 如果提供了期望版本，添加乐观锁检查
    if expected_version is not None:
        query = query.filter(models.Practice.version == expected_version)

    practice = query.first()

    if not practice:
        if expected_version is not None:
            return None, "实践已被其他用户修改，请刷新页面后重试"
        else:
            return None, "实践不存在或无权限"
    
    try:
        if action == "start_edit":
            # 开启编辑
            if practice.publish_status != models.PracticePublishStatusEnum.PUBLISHED:
                return None, "只有已发布的实践才能开启编辑"
            
            practice.publish_status = models.PracticePublishStatusEnum.EDITING
            if hasattr(practice, 'has_unpublished_changes'):
                practice.has_unpublished_changes = True
            
        elif action == "publish":
            # 发布（个人发布）
            if practice.publish_status != models.PracticePublishStatusEnum.EDITING:
                return None, "只有编辑中的实践才能发布"
            
            # 检查是否有关卡
            stage_count = db.query(models.Task).filter(
                models.Task.practice_id == practice_id
            ).count()
            if stage_count == 0:
                return None, "实践至少需要包含一个关卡才能发布"
            
            practice.publish_status = models.PracticePublishStatusEnum.PUBLISHED
            practice.visibility = models.PracticeVisibilityEnum.PRIVATE
            practice.is_published = True
            practice.published_at = datetime.now(timezone.utc)
            if hasattr(practice, 'has_unpublished_changes'):
                practice.has_unpublished_changes = False
            
            # 更新版本号
            if hasattr(practice, 'last_published_version') and not practice.last_published_version:
                practice.last_published_version = getattr(practice, 'current_version', None) or "1.0.0"
            
        elif action == "publish_new_version":
            # 发布新版本
            if practice.publish_status != models.PracticePublishStatusEnum.EDITING:
                return None, "只有编辑中的实践才能发布新版本"
            
            version_type = kwargs.get("version_type", "minor")
            update_content = kwargs.get("update_content", "")
            
            # 更新版本号
            current_version = getattr(practice, 'current_version', None) or "1.0.0"
            new_version = _increment_version(current_version, version_type)
            
            if hasattr(practice, 'current_version'):
                practice.current_version = new_version
            if hasattr(practice, 'last_published_version'):
                practice.last_published_version = new_version
            
            # 如果是公开发布新版本，需要审核
            if practice.visibility == models.PracticeVisibilityEnum.PUBLIC:
                if not update_content:
                    return None, "公开发布新版本需要填写更新内容"
                practice.publish_status = models.PracticePublishStatusEnum.PENDING_REVIEW
                practice.submitted_for_review_at = datetime.now(timezone.utc)
                practice.review_comments = None
            else:
                practice.publish_status = models.PracticePublishStatusEnum.PUBLISHED
                practice.published_at = datetime.now(timezone.utc)
            
            if hasattr(practice, 'has_unpublished_changes'):
                practice.has_unpublished_changes = False
            
            # 记录版本历史
            _add_version_history(practice, new_version, update_content)
            
        elif action == "cancel_edit":
            # 撤销编辑
            if practice.publish_status != models.PracticePublishStatusEnum.EDITING:
                return None, "只有编辑中的实践才能撤销编辑"
            
            if not practice.is_published:
                return None, "未发布的实践不能撤销编辑"
            
            practice.publish_status = models.PracticePublishStatusEnum.PUBLISHED
            if hasattr(practice, 'has_unpublished_changes'):
                practice.has_unpublished_changes = False
            
        elif action == "public_publish":
            # 公开发布
            if practice.publish_status != models.PracticePublishStatusEnum.PUBLISHED:
                return None, "只有已发布的实践才能申请公开发布"
            
            if practice.visibility == models.PracticeVisibilityEnum.PUBLIC:
                return None, "实践已经是公开发布状态"
            
            practice.publish_status = models.PracticePublishStatusEnum.PENDING_REVIEW
            practice.visibility = models.PracticeVisibilityEnum.PUBLIC
            practice.submitted_for_review_at = datetime.now(timezone.utc)
            practice.review_comments = None
            
        elif action == "cancel_public":
            # 撤销公开发布
            cancel_reason = kwargs.get("cancel_reason", "")
            
            if practice.visibility != models.PracticeVisibilityEnum.PUBLIC:
                return None, "只有公开发布的实践才能撤销公开发布"
            
            practice.publish_status = models.PracticePublishStatusEnum.PENDING_REVIEW
            practice.submitted_for_review_at = datetime.now(timezone.utc)
            practice.review_comments = f"撤销公开发布申请：{cancel_reason}"
            
        elif action == "offline":
            # 下架
            if practice.publish_status != models.PracticePublishStatusEnum.PUBLISHED:
                return None, "只有已发布的实践才能下架"
            
            if practice.visibility != models.PracticeVisibilityEnum.PRIVATE:
                return None, "只有个人发布的实践才能下架"
            
            practice.publish_status = models.PracticePublishStatusEnum.EDITING
            practice.is_published = False
            if hasattr(practice, 'has_unpublished_changes'):
                practice.has_unpublished_changes = False
            
        elif action == "delete":
            # 删除
            if practice.publish_status != models.PracticePublishStatusEnum.EDITING or practice.is_published:
                return None, "只有编辑中（创建但未发布）状态的实践才能删除"
            
            # 检查是否被课堂使用
            classroom_usage = db.query(models.ClassroomPractice).filter(
                models.ClassroomPractice.practice_id == practice_id
            ).first()
            
            if classroom_usage:
                return None, "实践已被课堂使用，无法删除"
            
            # 删除实践及相关数据
            db.delete(practice)
            db.commit()
            return {"deleted": True}, "实践删除成功"
            
        else:
            return None, f"不支持的操作：{action}"

        # 更新版本号（乐观锁）
        try:
            current_version = int(practice.version) if practice.version is not None else 0
        except (ValueError, TypeError):
            current_version = 0
        practice.version = current_version + 1

        db.commit()
        db.refresh(practice)

        # 更新缓存以确保数据一致性
        try:
            from app.core.cache import get_cache
            cache = get_cache()

            if action == "delete":
                # 删除操作：清除缓存
                cache.delete_practice_status(practice_id)
                cache.invalidate_user_practices(creator_id)
            else:
                # 其他操作：更新缓存
                from app.crud.my_practices_crud import _determine_practice_status

                # 计算关卡数量
                task_count = db.query(models.Task).filter(
                    models.Task.practice_id == practice_id
                ).count()

                # 构造状态数据
                status_data = {
                    "id": practice_id,
                    "title": practice.title,
                    "practice_type": practice.practice_type,
                    "difficulty": practice.difficulty.value if practice.difficulty else "intermediate",
                    "stage_count": task_count,
                    "coin": practice.coin,
                    "status": _determine_practice_status(practice),
                    "publish_status": practice.publish_status.value if practice.publish_status else None,
                    "visibility": practice.visibility.value if practice.visibility else None,
                    "is_published": practice.is_published,
                    "current_version": getattr(practice, 'current_version', None) or "1.0.0",
                    "created_at": practice.created_at.isoformat() if practice.created_at else None,
                    "updated_at": practice.updated_at.isoformat() if practice.updated_at else None,
                    "published_at": practice.published_at.isoformat() if practice.published_at else None,
                    "submitted_for_review_at": practice.submitted_for_review_at.isoformat() if practice.submitted_for_review_at else None,
                    "review_comments": practice.review_comments
                }

                # 设置缓存（5分钟TTL）
                cache.set_practice_status(practice_id, status_data, ttl=300)

                # 使该用户的其他实践缓存失效，确保列表数据一致
                cache.invalidate_user_practices(creator_id)

        except Exception as e:
            # 缓存失败不影响主业务流程
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"更新实践缓存失败: {e}")

        return practice, "操作成功"
        
    except Exception as e:
        db.rollback()
        return None, f"操作失败：{str(e)}"


def _increment_version(current_version: str, version_type: str) -> str:
    """递增版本号"""
    return _increment_version_pure(current_version, version_type)


def _add_version_history(practice, version: str, update_content: str):
    """添加版本历史记录"""
    if not hasattr(practice, 'version_history'):
        return
        
    try:
        history = json.loads(practice.version_history) if practice.version_history else []
    except:
        history = []
    
    history.append({
        "version": version,
        "update_content": update_content,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "visibility": practice.visibility.value
    })
    
    # 只保留最近10个版本
    if len(history) > 10:
        history = history[-10:]
    
    practice.version_history = json.dumps(history, ensure_ascii=False)


def delete_practice_enhanced(
    db: Session,
    practice_id: int,
    creator_id: int
):
    """删除实践（增强版）"""
    # 验证权限和状态
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return False, "实践不存在或无权限"
    
    # 只有编辑中（创建但未发布）状态的实践才能删除
    if practice.publish_status != models.PracticePublishStatusEnum.EDITING or practice.is_published:
        return False, "只有编辑中（创建但未发布）状态的实践才能删除"
    
    # 检查是否被课堂使用
    classroom_usage = db.query(models.ClassroomPractice).filter(
        models.ClassroomPractice.practice_id == practice_id
    ).first()
    
    if classroom_usage:
        return False, "实践已被课堂使用，无法删除"
    
    try:
        # 删除实践（级联删除相关数据）
        db.delete(practice)
        db.commit()
        return True, "实践删除成功"
    except Exception as e:
        db.rollback()
        return False, f"删除失败：{str(e)}"


def get_practice_version_info(
    db: Session,
    practice_id: int,
    creator_id: int
):
    """获取实践版本信息"""
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return None
    
    version_history = []
    if hasattr(practice, 'version_history') and practice.version_history:
        try:
            version_history = json.loads(practice.version_history)
        except:
            version_history = []
    
    # 判断是否可以发布新版本
    has_unpublished_changes = getattr(practice, 'has_unpublished_changes', False)
    can_publish_new_version = (
        practice.publish_status == models.PracticePublishStatusEnum.EDITING and
        practice.is_published and
        has_unpublished_changes
    )
    
    return {
        "current_version": getattr(practice, 'current_version', None) or "1.0.0",
        "version_history": version_history,
        "can_publish_new_version": can_publish_new_version,
        "last_published_version": getattr(practice, 'last_published_version', None)
    } 