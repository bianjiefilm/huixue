"""
同步监控和管理模块
提供同步过程的监控、状态查询、验证等功能
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models import models
from app.core.database import get_db


@dataclass
class SyncStatus:
    """同步状态信息"""
    total_resources: int = 0
    synced_resources: int = 0
    failed_resources: int = 0
    last_sync_time: Optional[datetime] = None
    is_healthy: bool = True
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class SyncMonitor:
    """同步监控器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def get_sync_status(self, db: Session) -> SyncStatus:
        """获取同步状态"""
        try:
            status = SyncStatus()

            # 统计资源总数
            status.total_resources = db.query(func.count(models.CourseResource.id)).scalar() or 0

            # 统计最近24小时的同步情况
            yesterday = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

            # 获取最后同步时间（通过created_at或updated_at推断）
            last_resource = db.query(models.CourseResource).order_by(
                models.CourseResource.created_at.desc()
            ).first()

            if last_resource:
                status.last_sync_time = last_resource.created_at

            # 检查是否有错误（这里可以扩展为检查具体的错误日志表）
            # 目前简单检查是否有资源文件不存在的情况
            status.is_healthy = self._check_sync_health(db)

            return status

        except Exception as e:
            self.logger.error(f"获取同步状态失败: {e}")
            status = SyncStatus()
            status.is_healthy = False
            status.errors.append(f"获取状态失败: {str(e)}")
            return status

    def _check_sync_health(self, db: Session) -> bool:
        """检查同步健康状态"""
        try:
            # 检查是否有孤立的资源记录（文件不存在但记录存在）
            resources = db.query(models.CourseResource).all()
            missing_files = 0

            for resource in resources:
                # 这里可以添加文件存在性检查逻辑
                # 暂时返回True，表示健康
                pass

            return True

        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False

    def validate_sync_integrity(self, db: Session) -> Dict[str, Any]:
        """验证同步完整性"""
        result = {
            "is_valid": True,
            "issues": [],
            "statistics": {},
            "recommendations": []
        }

        try:
            # 1. 检查资源文件存在性
            resources = db.query(models.CourseResource).all()
            missing_files = []

            for resource in resources:
                # 模拟文件存在性检查（实际实现需要文件系统访问）
                file_exists = self._check_file_exists(resource)
                if not file_exists:
                    missing_files.append(resource.title)
                    result["issues"].append(f"资源文件不存在: {resource.title}")

            # 2. 检查重复资源
            duplicates = db.query(
                models.CourseResource.title,
                func.count(models.CourseResource.id).label('count')
            ).group_by(models.CourseResource.title).having(
                func.count(models.CourseResource.id) > 1
            ).all()

            if duplicates:
                result["issues"].append(f"发现 {len(duplicates)} 个重复资源标题")
                result["recommendations"].append("清理重复的资源记录")

            # 3. 检查无效的资源类型
            valid_types = ['pdf', 'ppt', 'pptx', 'doc', 'docx', 'xls', 'xlsx',
                          'mp4', 'avi', 'mov', 'jpg', 'jpeg', 'png', 'gif',
                          'md', 'markdown', 'txt', 'json']

            invalid_types = db.query(models.CourseResource).filter(
                ~models.CourseResource.resource_type.in_(valid_types)
            ).all()

            if invalid_types:
                result["issues"].append(f"发现 {len(invalid_types)} 个无效的资源类型")
                result["recommendations"].append("更新无效的资源类型")

            # 4. 统计信息
            result["statistics"] = {
                "total_resources": len(resources),
                "missing_files": len(missing_files),
                "duplicate_titles": len(duplicates),
                "invalid_types": len(invalid_types)
            }

            # 5. 总体验证结果
            if result["issues"]:
                result["is_valid"] = False
                result["recommendations"].append("运行同步修复脚本来解决这些问题")

            return result

        except Exception as e:
            self.logger.error(f"验证同步完整性失败: {e}")
            result["is_valid"] = False
            result["issues"].append(f"验证过程出错: {str(e)}")
            return result

    def _check_file_exists(self, resource: models.CourseResource) -> bool:
        """检查资源文件是否存在"""
        try:
            # 这里应该实现实际的文件存在性检查
            # 暂时返回True
            return True
        except Exception:
            return False

    def get_sync_logs(self, db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        """获取同步日志"""
        # 这里可以实现从专门的日志表获取同步日志
        # 暂时返回模拟数据
        return [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "message": "同步开始",
                "details": {"total_actions": 150}
            },
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "message": "同步完成",
                "details": {"successful": 148, "failed": 2}
            }
        ]

    def cleanup_orphaned_records(self, db: Session) -> Dict[str, int]:
        """清理孤立的记录"""
        cleanup_stats = {
            "removed_resources": 0,
            "removed_assessments": 0,
            "removed_practices": 0
        }

        try:
            # 这里可以实现清理逻辑
            # 暂时返回空统计
            return cleanup_stats

        except Exception as e:
            self.logger.error(f"清理孤立记录失败: {e}")
            return cleanup_stats


# 全局监控器实例
sync_monitor = SyncMonitor()


def get_sync_status(db: Session = next(get_db())) -> SyncStatus:
    """获取同步状态的便捷函数"""
    return sync_monitor.get_sync_status(db)


def validate_sync_integrity(db: Session = next(get_db())) -> Dict[str, Any]:
    """验证同步完整性的便捷函数"""
    return sync_monitor.validate_sync_integrity(db)
