"""
AI额度管理系统
控制不同用户角色的AI功能使用额度
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.models.models import AIUsageLog, User

logger = logging.getLogger(__name__)


class AIQuotaManager:
    """AI额度管理器"""

    # 每月额度配置（次）
    QUOTA_CONFIG = {
        "teacher": 100,    # 教师每月100次
        "student": 20,     # 学生每月20次
        "admin": float('inf')  # 管理员无限
    }

    # 功能对应的消耗系数
    COST_CONFIG = {
        "chat": 1,           # 普通对话
        "explain": 1,        # 概念解释
        "generate_question": 2,  # 生成试题
        "quality_check": 0.5,    # 质量检查
        "analyze_content": 2,    # 内容分析
    }

    def __init__(self, db: Session):
        self.db = db

    def check_quota(self, user_id: int, action_type: str) -> Dict[str, any]:
        """
        检查用户是否还有额度

        Args:
            user_id: 用户ID
            action_type: 操作类型

        Returns:
            Dict containing:
            - allowed: bool 是否允许使用
            - remaining: int 剩余额度
            - reset_date: datetime 额度重置日期
            - cost: float 此次操作消耗的额度
        """
        try:
            # 获取用户信息
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_date": None,
                    "cost": 0,
                    "error": "用户不存在"
                }

            # 获取用户角色对应的额度
            user_role = self._get_user_role(user)
            monthly_quota = self.QUOTA_CONFIG.get(user_role, 20)

            # 计算本月已使用额度
            current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = (current_month + timedelta(days=32)).replace(day=1)

            used_quota = self.db.query(AIUsageLog).filter(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at >= current_month,
                AIUsageLog.created_at < next_month,
                AIUsageLog.error_message.is_(None)  # 只计算成功的调用
            ).count()

            # 计算此次操作消耗
            cost = self.COST_CONFIG.get(action_type, 1)

            # 计算剩余额度
            remaining = monthly_quota - used_quota
            allowed = remaining >= cost

            return {
                "allowed": allowed,
                "remaining": max(0, remaining),
                "reset_date": next_month,
                "cost": cost,
                "user_role": user_role,
                "monthly_quota": monthly_quota,
                "used_this_month": used_quota
            }

        except Exception as e:
            logger.error(f"检查AI额度失败: {e}")
            return {
                "allowed": False,
                "remaining": 0,
                "reset_date": None,
                "cost": 1,
                "error": str(e)
            }

    def consume_quota(self, user_id: int, action_type: str, actual_cost: Optional[float] = None) -> bool:
        """
        消费用户额度

        Args:
            user_id: 用户ID
            action_type: 操作类型
            actual_cost: 实际消耗额度（可选，默认使用配置值）

        Returns:
            bool: 是否成功消费
        """
        try:
            # 先检查额度
            quota_info = self.check_quota(user_id, action_type)
            if not quota_info["allowed"]:
                return False

            # 确定消耗额度
            cost = actual_cost if actual_cost is not None else quota_info["cost"]

            # 这里可以记录更详细的消耗信息
            # 目前先通过check_quota中的计数来控制

            return True

        except Exception as e:
            logger.error(f"消费AI额度失败: {e}")
            return False

    def get_quota_stats(self, user_id: int) -> Dict[str, any]:
        """
        获取用户的额度统计信息

        Args:
            user_id: 用户ID

        Returns:
            Dict: 额度统计信息
        """
        try:
            # 获取当月使用情况
            current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = (current_month + timedelta(days=32)).replace(day=1)

            monthly_usage = self.db.query(AIUsageLog).filter(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at >= current_month,
                AIUsageLog.created_at < next_month
            ).all()

            # 按功能类型统计
            usage_by_type = {}
            total_cost = 0
            successful_calls = 0

            for log in monthly_usage:
                if log.error_message:  # 失败的调用
                    continue

                successful_calls += 1
                feature_type = log.feature_type or "unknown"

                if feature_type not in usage_by_type:
                    usage_by_type[feature_type] = 0
                usage_by_type[feature_type] += 1

                # 估算成本
                if log.total_tokens:
                    total_cost += log.total_tokens * 0.000002  # 按token估算

            # 获取用户信息和额度配置
            user = self.db.query(User).filter(User.id == user_id).first()
            user_role = self._get_user_role(user) if user else "student"
            monthly_quota = self.QUOTA_CONFIG.get(user_role, 20)

            return {
                "user_role": user_role,
                "monthly_quota": monthly_quota,
                "used_this_month": successful_calls,
                "remaining": max(0, monthly_quota - successful_calls),
                "usage_by_type": usage_by_type,
                "estimated_cost": round(total_cost, 4),
                "reset_date": next_month,
                "current_month": current_month
            }

        except Exception as e:
            logger.error(f"获取AI额度统计失败: {e}")
            return {
                "error": str(e),
                "monthly_quota": 20,
                "used_this_month": 0,
                "remaining": 20
            }

    def get_user_role(self, user_id: int) -> str:
        """按 user_id 获取用户角色（供调用方在异常兜底路径直接传 user_id 使用）"""
        user = self.db.query(User).filter(User.id == user_id).first()
        return self._get_user_role(user) if user else "student"

    def _get_user_role(self, user: User) -> str:
        """获取用户角色"""
        try:
            # 这里需要根据你的用户角色判断逻辑来实现
            # 假设用户有role字段或者通过其他方式判断
            if hasattr(user, 'role'):
                return user.role.lower()
            elif hasattr(user, 'is_admin') and user.is_admin:
                return "admin"
            elif hasattr(user, 'is_teacher') and user.is_teacher:
                return "teacher"
            else:
                return "student"
        except:
            return "student"


# 全局额度管理器实例
quota_manager = AIQuotaManager(None)  # 需要在使用时传入db

def get_quota_manager(db: Session) -> AIQuotaManager:
    """获取额度管理器实例"""
    global quota_manager
    if quota_manager.db is None:
        quota_manager.db = db
    return quota_manager
