"""
单一来源事实 - V3.0 差分引擎

负责比较文件系统状态和数据库状态，计算需要执行的同步操作。
支持版本号比对和智能差异检测。
"""

import logging
from typing import Dict, List, Any, Set
from datetime import datetime

from .models import (
    ResourceType, ResourceManifest, SyncAction, SyncPlan,
    SyncActionType, ResourceMetadata
)
from app.utils.sync_diff_helpers import (
    infer_resource_type as _infer_resource_type,
    is_version_newer as _is_version_newer,
    check_file_changes as _check_file_changes,
    validate_sync_plan_actions as _validate_sync_plan_actions,
)

logger = logging.getLogger(__name__)


class IntelligentDiffEngine:
    """智能差分引擎

    比较文件系统和数据库状态，生成精确的同步计划。
    支持版本控制和依赖关系处理。
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_sync_plan(
        self,
        filesystem_state: Dict[str, ResourceManifest],
        database_state: Dict[str, Any]
    ) -> SyncPlan:
        """
        计算同步计划

        Args:
            filesystem_state: 文件系统状态 (resource_id -> ResourceManifest)
            database_state: 数据库状态 (resource_id -> db_record)

        Returns:
            同步计划对象
        """
        plan = SyncPlan()

        # 获取所有资源ID的并集
        fs_ids = set(filesystem_state.keys())
        db_ids = set(database_state.keys())
        all_ids = fs_ids | db_ids

        self.logger.info(f"文件系统资源数: {len(fs_ids)}, 数据库资源数: {len(db_ids)}")

        for resource_id in all_ids:
            actions = self._calculate_resource_actions(
                resource_id,
                filesystem_state.get(resource_id),
                database_state.get(resource_id)
            )

            for action in actions:
                plan.add_action(action)

        self.logger.info(f"生成同步计划: {plan.get_summary_text()}")
        return plan

    def _calculate_resource_actions(
        self,
        resource_id: str,
        fs_manifest: ResourceManifest = None,
        db_record: Dict[str, Any] = None
    ) -> List[SyncAction]:
        """
        计算单个资源的同步动作

        Args:
            resource_id: 资源ID
            fs_manifest: 文件系统中的资源清单
            db_record: 数据库中的记录

        Returns:
            同步动作列表
        """
        actions = []

        # 情况1: 文件系统中存在，数据库中不存在 -> 创建
        if fs_manifest and not db_record:
            actions.append(SyncAction(
                action_type=SyncActionType.CREATE,
                resource_id=resource_id,
                resource_type=fs_manifest.metadata.resource_type,
                manifest=fs_manifest,
                reason="文件系统中存在的新资源"
            ))
            return actions

        # 情况2: 文件系统中不存在，数据库中存在 -> 删除
        if not fs_manifest and db_record:
            # 从数据库记录推断资源类型
            resource_type = self._infer_resource_type_from_db(db_record)
            actions.append(SyncAction(
                action_type=SyncActionType.DELETE,
                resource_id=resource_id,
                resource_type=resource_type,
                reason="文件系统中已删除的资源"
            ))
            return actions

        # 情况3: 两者都存在 -> 比较是否需要更新
        if fs_manifest and db_record:
            update_actions = self._calculate_update_actions(fs_manifest, db_record)
            actions.extend(update_actions)

        return actions

    def _infer_resource_type_from_db(self, db_record: Dict[str, Any]) -> ResourceType:
        """从数据库记录推断资源类型（委托给纯函数）"""
        return ResourceType(_infer_resource_type(db_record))

    def _calculate_update_actions(
        self,
        fs_manifest: ResourceManifest,
        db_record: Dict[str, Any]
    ) -> List[SyncAction]:
        """
        计算更新动作

        Args:
            fs_manifest: 文件系统清单
            db_record: 数据库记录

        Returns:
            更新动作列表
        """
        actions = []
        resource_id = fs_manifest.metadata.id
        resource_type = fs_manifest.metadata.resource_type

        # 版本号比较
        fs_version = fs_manifest.metadata.version
        db_version = db_record.get('version', '0.0.0')

        if self._is_version_newer(fs_version, db_version):
            self.logger.info(f"资源 {resource_id} 版本更新: {db_version} -> {fs_version}")
            actions.append(SyncAction(
                action_type=SyncActionType.UPDATE,
                resource_id=resource_id,
                resource_type=resource_type,
                manifest=fs_manifest,
                reason=f"版本更新: {db_version} -> {fs_version}"
            ))
            return actions

        # 检查校验和变化（即使版本号相同）
        fs_checksum = fs_manifest.checksum
        db_checksum = db_record.get('checksum')

        if fs_checksum != db_checksum:
            self.logger.info(f"资源 {resource_id} 内容变化，校验和不匹配")
            actions.append(SyncAction(
                action_type=SyncActionType.UPDATE,
                resource_id=resource_id,
                resource_type=resource_type,
                manifest=fs_manifest,
                reason="内容变更检测（校验和变化）"
            ))
            return actions

        # 检查文件修改时间
        db_updated_at = db_record.get('updated_at')
        if db_updated_at and isinstance(db_updated_at, datetime):
            if fs_manifest.last_modified > db_updated_at:
                self.logger.info(f"资源 {resource_id} 文件修改时间更新")
                actions.append(SyncAction(
                    action_type=SyncActionType.UPDATE,
                    resource_id=resource_id,
                    resource_type=resource_type,
                    manifest=fs_manifest,
                    reason="文件修改时间更新"
                ))
                return actions

        # 检查资源文件变化
        file_changes = self._check_file_changes(fs_manifest, db_record)
        if file_changes:
            self.logger.info(f"资源 {resource_id} 检测到文件变化: {len(file_changes)} 个文件")
            actions.append(SyncAction(
                action_type=SyncActionType.UPDATE,
                resource_id=resource_id,
                resource_type=resource_type,
                manifest=fs_manifest,
                reason=f"资源文件变化: {', '.join(file_changes[:3])}{'...' if len(file_changes) > 3 else ''}"
            ))

        return actions

    def _is_version_newer(self, fs_version: str, db_version: str) -> bool:
        """比较版本号（委托给纯函数）"""
        return _is_version_newer(fs_version, db_version)

    def _check_file_changes(self, fs_manifest: ResourceManifest, db_record: Dict[str, Any]) -> List[str]:
        """检查资源文件的变化（委托给纯函数）"""
        db_files = db_record.get('resource_files', {})
        return _check_file_changes(fs_manifest.resource_files, db_files)

    def validate_sync_plan(self, plan: SyncPlan) -> List[str]:
        """验证同步计划的合理性（委托给纯函数）"""
        action_dicts = [
            {"action_type": a.action_type, "resource_id": a.resource_id}
            for a in plan.actions
        ]
        return _validate_sync_plan_actions(action_dicts)

    def optimize_sync_plan(self, plan: SyncPlan) -> SyncPlan:
        """
        优化同步计划

        Args:
            plan: 原始同步计划

        Returns:
            优化后的同步计划
        """
        optimized_actions = []

        # 按优先级排序：删除 -> 创建 -> 更新
        priority_order = {
            SyncActionType.DELETE: 1,
            SyncActionType.CREATE: 2,
            SyncActionType.UPDATE: 3
        }

        sorted_actions = sorted(
            plan.actions,
            key=lambda a: priority_order.get(a.action_type, 4)
        )

        # 合并相同的动作（去重）
        seen_actions = set()
        for action in sorted_actions:
            action_key = (action.action_type, action.resource_id)
            if action_key not in seen_actions:
                optimized_actions.append(action)
                seen_actions.add(action_key)
            else:
                self.logger.warning(f"移除重复动作: {action}")

        # 创建新的计划
        optimized_plan = SyncPlan()
        for action in optimized_actions:
            optimized_plan.add_action(action)

        self.logger.info(f"同步计划优化: {len(plan.actions)} -> {len(optimized_plan.actions)} 个动作")

        return optimized_plan




