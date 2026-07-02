"""
智能状态比对引擎
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass

from .models import (
    ResourceManifest, SyncPlan, SyncAction, ResourceType,
    MetadataChange, FileDependencyChange, VersionChange
)
from app.utils.diff_helpers import (
    find_new_keys as _find_new_keys,
    find_deleted_keys as _find_deleted_keys,
    determine_deletion_action as _determine_deletion_action,
    compare_metadata_fields as _compare_metadata_fields,
    compare_file_keys as _compare_file_keys,
    should_mark_version_change as _should_mark_version_change,
)


@dataclass
class ResourceState:
    """资源状态"""
    id: str
    resource_type: ResourceType
    checksum: Optional[str]
    last_modified: datetime
    metadata: Dict[str, Any]
    files: Dict[str, Any]


class IntelligentDiffEngine:
    """智能状态比对引擎"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def calculate_sync_plan(self, file_system_state: Dict[str, ResourceManifest],
                           database_state: Dict[str, ResourceState]) -> SyncPlan:
        """
        计算智能差异

        Args:
            file_system_state: 文件系统状态（从ziyuan目录发现的资源）
            database_state: 数据库状态（从数据库查询的资源）

        Returns:
            同步计划
        """
        self.logger.info(f"开始计算差异 - 文件系统: {len(file_system_state)} 个资源, 数据库: {len(database_state)} 个资源")

        plan = SyncPlan()

        # 分析新增资源
        new_resources = self._find_new_resources(file_system_state, database_state)
        for resource_id, manifest in new_resources.items():
            plan.add_action(SyncAction(
                action_type='create',
                resource_id=resource_id,
                resource_type=manifest.metadata.resource_type,
                manifest=manifest,
                reason=f"新发现的资源: {manifest.metadata.title}"
            ))

        # 分析删除资源
        deleted_resources = self._find_deleted_resources(file_system_state, database_state)
        for resource_id, db_resource in deleted_resources.items():
            action_type = self._determine_deletion_action(db_resource)
            plan.add_action(SyncAction(
                action_type=action_type,
                resource_id=resource_id,
                resource_type=db_resource.resource_type,
                manifest=None,  # 删除操作不需要manifest
                reason=f"文件系统中不存在的资源: {db_resource.metadata.get('title', resource_id)}"
            ))

        # 分析变更资源
        changed_resources = self._find_changed_resources(file_system_state, database_state)
        for resource_id, changes in changed_resources.items():
            fs_manifest = file_system_state[resource_id]
            plan.add_action(SyncAction(
                action_type='update',
                resource_id=resource_id,
                resource_type=fs_manifest.metadata.resource_type,
                manifest=fs_manifest,
                changes=changes,
                reason=f"检测到变更: {fs_manifest.metadata.title}"
            ))

        self.logger.info(f"差异计算完成 - 新增: {len(new_resources)}, 删除: {len(deleted_resources)}, 更新: {len(changed_resources)}")
        return plan

    def _find_new_resources(self, fs_state: Dict[str, ResourceManifest],
                          db_state: Dict[str, ResourceState]) -> Dict[str, ResourceManifest]:
        """查找新增的资源"""
        new_ids = _find_new_keys(set(fs_state.keys()), set(db_state.keys()))
        new_resources = {}
        for resource_id in new_ids:
            new_resources[resource_id] = fs_state[resource_id]
            self.logger.debug(f"发现新增资源: {resource_id} ({fs_state[resource_id].metadata.title})")
        return new_resources

    def _find_deleted_resources(self, fs_state: Dict[str, ResourceManifest],
                              db_state: Dict[str, ResourceState]) -> Dict[str, ResourceState]:
        """查找已删除的资源"""
        deleted_ids = _find_deleted_keys(set(fs_state.keys()), set(db_state.keys()))
        deleted_resources = {}
        for resource_id in deleted_ids:
            deleted_resources[resource_id] = db_state[resource_id]
            self.logger.debug(f"发现删除资源: {resource_id}")
        return deleted_resources

    def _find_changed_resources(self, fs_state: Dict[str, ResourceManifest],
                              db_state: Dict[str, ResourceState]) -> Dict[str, List[Any]]:
        """查找变更的资源"""
        changed_resources = {}

        for resource_id in fs_state.keys():
            if resource_id in db_state:
                fs_manifest = fs_state[resource_id]
                db_resource = db_state[resource_id]

                changes = self._compare_resources(fs_manifest, db_resource)
                if changes:
                    changed_resources[resource_id] = changes
                    self.logger.debug(f"发现变更资源: {resource_id}, 变更数: {len(changes)}")

        return changed_resources

    def _compare_resources(self, fs_manifest: ResourceManifest,
                          db_resource: ResourceState) -> List[Any]:
        """智能比较两个资源版本"""
        changes = []

        fs_metadata = fs_manifest.metadata
        db_metadata = db_resource.metadata

        # 1. 版本时间/校验和比较（最重要的）
        if _should_mark_version_change(
            fs_manifest.last_modified, db_resource.last_modified,
            fs_metadata.checksum, db_resource.checksum,
        ):
            changes.append(VersionChange(
                field='content',
                old_value=db_resource.checksum,
                new_value=fs_metadata.checksum,
            ))

        # 2. 元数据字段比较
        metadata_changes = self._compare_metadata_fields(fs_metadata, db_metadata)
        changes.extend(metadata_changes)

        # 3. 文件依赖比较
        file_changes = self._compare_file_dependencies(fs_manifest, db_resource)
        changes.extend(file_changes)

        return changes

    def _compare_metadata_fields(self, fs_metadata: Any, db_metadata: Dict[str, Any]) -> List[MetadataChange]:
        """比较元数据字段"""
        raw_changes = _compare_metadata_fields(fs_metadata, db_metadata)
        return [
            MetadataChange(field=field, old_value=old, new_value=new)
            for field, old, new in raw_changes
        ]

    def _compare_file_dependencies(self, fs_manifest: ResourceManifest,
                                db_resource: ResourceState) -> List[FileDependencyChange]:
        """比较文件依赖"""
        added, removed = _compare_file_keys(fs_manifest.files, db_resource.files)
        if added or removed:
            return [FileDependencyChange(added_files=added, removed_files=removed)]
        return []

    def _determine_deletion_action(self, db_resource: ResourceState) -> str:
        """确定删除操作类型"""
        resource_title = db_resource.metadata.get('title', '')
        return _determine_deletion_action(resource_title)


class ConflictResolver:
    """冲突解决器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def resolve_conflicts(self, plan: SyncPlan,
                         conflict_strategy: str = 'latest_wins') -> SyncPlan:
        """
        解决同步冲突

        Args:
            plan: 原始同步计划
            conflict_strategy: 冲突解决策略
                - 'latest_wins': 最新版本胜出
                - 'manual': 需要手动解决
                - 'conservative': 保守策略，只处理新增和明确删除

        Returns:
            解决冲突后的同步计划
        """
        self.logger.info(f"开始解决冲突，策略: {conflict_strategy}")

        if conflict_strategy == 'latest_wins':
            # 最新版本胜出策略 - 保持原有逻辑
            return plan
        elif conflict_strategy == 'conservative':
            # 保守策略 - 只处理新增，忽略更新和删除
            conservative_plan = SyncPlan()
            for action in plan.actions:
                if action.action_type == 'create':
                    conservative_plan.add_action(action)
            return conservative_plan
        elif conflict_strategy == 'manual':
            # 手动解决 - 这里可以实现更复杂的逻辑
            # 例如：标记冲突的actions，需要人工审核
            return self._mark_conflicts_for_manual_review(plan)
        else:
            raise ValueError(f"不支持的冲突解决策略: {conflict_strategy}")

    def _mark_conflicts_for_manual_review(self, plan: SyncPlan) -> SyncPlan:
        """标记需要手动审核的冲突"""
        # 为有风险的操作添加标记
        for action in plan.actions:
            if action.action_type == 'delete':
                action.reason += " [需要手动确认]"
            elif action.action_type == 'update' and len(action.changes or []) > 5:
                action.reason += " [大量变更，建议审核]"

        return plan
