"""
审计日志 CRUD 操作

用于记录成绩修改、反馈修改等重要操作
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class AuditCRUD:
    """审计日志数据操作"""
    
    @staticmethod
    def log_grade_change(
        db: Session,
        entity_type: str,
        entity_id: int,
        old_value: Optional[Dict[str, Any]],
        new_value: Dict[str, Any],
        changed_by: int,
        action: str = "grade_changed"
    ):
        """
        记录成绩修改日志
        
        Args:
            entity_type: 实体类型 (如 'student_course_progress')
            entity_id: 实体ID
            old_value: 旧值
            new_value: 新值
            changed_by: 修改者ID
            action: 操作类型
        """
        try:
            from app.models import AuditLog
            
            audit_log = AuditLog(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                old_value=json.dumps(old_value) if old_value else None,
                new_value=json.dumps(new_value) if new_value else None,
                changed_by=changed_by,
                changed_at=datetime.utcnow()
            )
            
            db.add(audit_log)
            db.commit()
            
            logger.info(f"审计日志记录成功: {entity_type} {entity_id} {action}")
            
        except Exception as e:
            logger.error(f"记录审计日志失败: {str(e)}")
            db.rollback()
    
    @staticmethod
    def get_audit_logs(
        db: Session,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取审计日志
        """
        try:
            from app.models import AuditLog
            
            query = db.query(AuditLog)
            
            if entity_type:
                query = query.filter(AuditLog.entity_type == entity_type)
            
            if entity_id:
                query = query.filter(AuditLog.entity_id == entity_id)
            
            total = query.count()
            logs = query.order_by(
                desc(AuditLog.changed_at)
            ).offset((page - 1) * page_size).limit(page_size).all()
            
            data = [
                {
                    "id": log.id,
                    "entity_type": log.entity_type,
                    "entity_id": log.entity_id,
                    "action": log.action,
                    "old_value": json.loads(log.old_value) if log.old_value else None,
                    "new_value": json.loads(log.new_value) if log.new_value else None,
                    "changed_by": log.changed_by,
                    "changed_at": log.changed_at.isoformat() if log.changed_at else None
                }
                for log in logs
            ]
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "data": data
            }
            
        except Exception as e:
            logger.error(f"获取审计日志失败: {str(e)}")
            return {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "data": []
            }

