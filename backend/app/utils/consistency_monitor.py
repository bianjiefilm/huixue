"""
数据一致性监控和自动修复工具
用于检测和修复前后端数据不一致的问题
"""
import logging
import time
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.cache import get_cache
from app.crud import crud, my_practices_crud
from app.core.database import get_db
from app.utils.consistency_helpers import calculate_health_score as _calculate_health_score

logger = logging.getLogger(__name__)

class ConsistencyMonitor:
    """数据一致性监控器"""

    def __init__(self):
        self.cache = get_cache()
        self.db = next(get_db())

    def check_cache_consistency(self, practice_ids: List[int] = None) -> Dict[str, Any]:
        """
        检查缓存与数据库的一致性

        Args:
            practice_ids: 要检查的实践ID列表，如果为None则检查所有

        Returns:
            Dict[str, Any]: 检查结果
        """
        logger.info("开始检查缓存一致性...")

        results = {
            "total_checked": 0,
            "cache_hits": 0,
            "inconsistencies": [],
            "fixed_count": 0,
            "errors": []
        }

        try:
            if practice_ids is None:
                # 获取所有实践ID
                practices = self.db.query(crud.models.Practice).all()
                practice_ids = [p.id for p in practices]

            results["total_checked"] = len(practice_ids)

            for practice_id in practice_ids:
                try:
                    # 从数据库获取最新数据
                    practice = self.db.query(crud.models.Practice).filter(
                        crud.models.Practice.id == practice_id
                    ).first()

                    if not practice:
                        continue

                    # 从缓存获取数据
                    cached_data = self.cache.get_practice_status(practice_id)

                    if cached_data:
                        results["cache_hits"] += 1

                        # 比较关键字段
                        db_status = my_practices_crud._determine_practice_status(practice)
                        cache_status = cached_data.get("status")

                        if db_status != cache_status:
                            logger.warning(f"实践 {practice_id} 状态不一致: DB={db_status}, Cache={cache_status}")

                            results["inconsistencies"].append({
                                "practice_id": practice_id,
                                "field": "status",
                                "db_value": db_status,
                                "cache_value": cache_status,
                                "timestamp": datetime.now().isoformat()
                            })

                            # 自动修复：更新缓存
                            self._fix_cache_inconsistency(practice_id, practice)
                            results["fixed_count"] += 1

                except Exception as e:
                    logger.error(f"检查实践 {practice_id} 时出错: {e}")
                    results["errors"].append({
                        "practice_id": practice_id,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })

        except Exception as e:
            logger.error(f"检查缓存一致性时出错: {e}")
            results["errors"].append({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

        logger.info(f"缓存一致性检查完成: {results}")
        return results

    def _fix_cache_inconsistency(self, practice_id: int, practice) -> bool:
        """
        修复缓存不一致问题

        Args:
            practice_id: 实践ID
            practice: 数据库中的实践对象

        Returns:
            bool: 是否修复成功
        """
        try:
            # 计算关卡数量
            task_count = self.db.query(crud.models.Task).filter(
                crud.models.Task.practice_id == practice_id
            ).count()

            # 构造正确的缓存数据
            status_data = {
                "id": practice_id,
                "title": practice.title,
                "practice_type": practice.practice_type,
                "difficulty": practice.difficulty.value if practice.difficulty else "intermediate",
                "stage_count": task_count,
                "coin": practice.coin,
                "status": my_practices_crud._determine_practice_status(practice),
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

            # 更新缓存
            return self.cache.set_practice_status(practice_id, status_data, ttl=300)

        except Exception as e:
            logger.error(f"修复实践 {practice_id} 缓存失败: {e}")
            return False

    def check_operation_locks(self) -> Dict[str, Any]:
        """
        检查操作锁状态，清理过期的锁

        Returns:
            Dict[str, Any]: 检查结果
        """
        logger.info("开始检查操作锁状态...")

        results = {
            "active_locks": 0,
            "expired_locks": 0,
            "cleaned_locks": 0,
            "errors": []
        }

        try:
            # 这里简化实现，实际应该检查Redis中的锁
            # 由于我们使用的是简化的缓存实现，这里只是返回状态

            logger.info("操作锁检查完成")
            return results

        except Exception as e:
            logger.error(f"检查操作锁状态时出错: {e}")
            results["errors"].append({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return results

    def run_full_check(self) -> Dict[str, Any]:
        """
        运行完整的一致性检查

        Returns:
            Dict[str, Any]: 完整的检查结果
        """
        logger.info("开始运行完整一致性检查...")

        start_time = time.time()

        results = {
            "timestamp": datetime.now().isoformat(),
            "duration": 0,
            "cache_check": {},
            "lock_check": {},
            "summary": {}
        }

        try:
            # 检查缓存一致性
            results["cache_check"] = self.check_cache_consistency()

            # 检查操作锁
            results["lock_check"] = self.check_operation_locks()

            # 生成摘要
            results["summary"] = {
                "total_issues": len(results["cache_check"].get("inconsistencies", [])),
                "auto_fixed": results["cache_check"].get("fixed_count", 0),
                "manual_review_needed": len(results["cache_check"].get("errors", [])),
                "health_score": self._calculate_health_score(results)
            }

        except Exception as e:
            logger.error(f"运行完整检查时出错: {e}")
            results["summary"] = {
                "error": str(e),
                "health_score": 0
            }

        results["duration"] = time.time() - start_time
        logger.info(f"完整一致性检查完成，耗时: {results['duration']:.2f}秒")

        return results

    def _calculate_health_score(self, results: Dict[str, Any]) -> int:
        """计算健康评分（0-100）"""
        try:
            return _calculate_health_score(results)
        except Exception as e:
            logger.error(f"计算健康评分时出错: {e}")
            return 0

    def get_monitoring_report(self) -> Dict[str, Any]:
        """
        获取监控报告

        Returns:
            Dict[str, Any]: 监控报告
        """
        report = {
            "last_check_time": getattr(self, '_last_check_time', None),
            "health_score": getattr(self, '_last_health_score', 0),
            "recent_issues": getattr(self, '_recent_issues', []),
            "recommendations": self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """生成修复建议"""
        recommendations = []

        # 检查Redis连接
        if not self.cache.redis_client:
            recommendations.append("建议启用Redis服务以提升缓存性能")

        # 检查最近的错误
        if hasattr(self, '_last_check_results'):
            cache_check = self._last_check_results.get("cache_check", {})
            if cache_check.get("inconsistencies"):
                recommendations.append("发现缓存不一致问题，建议运行自动修复")

        return recommendations

# 全局监控实例
consistency_monitor = ConsistencyMonitor()

def get_consistency_monitor() -> ConsistencyMonitor:
    """获取一致性监控器实例"""
    return consistency_monitor
