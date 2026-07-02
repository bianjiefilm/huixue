"""
资源同步主服务
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .discovery import ResourceDiscoveryService
from .diff_engine import IntelligentDiffEngine, ConflictResolver
from .executor import TransactionalExecutor
from .monitoring import ResourceSyncMonitor
from .models import (
    ResourceManifest, SyncPlan, SyncResult, ResourceType,
    HealthStatus, SyncAction
)


class ResourceSyncService:
    """资源同步主服务"""

    def __init__(self,
                 ziyuan_base_path: str = "ziyuan",
                 static_dir: str = "static/resources",
                 logger: Optional[logging.Logger] = None):

        self.ziyuan_base_path = Path(ziyuan_base_path)
        self.static_dir = static_dir
        self.logger = logger or logging.getLogger(__name__)

        # 初始化组件
        self.discovery_service = ResourceDiscoveryService(
            base_path=str(self.ziyuan_base_path),
            logger=self.logger
        )

        self.diff_engine = IntelligentDiffEngine(logger=self.logger)
        self.conflict_resolver = ConflictResolver(logger=self.logger)

        self.executor = TransactionalExecutor(logger=self.logger)

        self.monitor = ResourceSyncMonitor()

    async def sync_all_resources(self,
                               dry_run: bool = False,
                               force: bool = False,
                               conflict_strategy: str = 'latest_wins') -> SyncResult:
        """
        同步所有资源

        Args:
            dry_run: 是否为干运行模式
            force: 是否强制执行（跳过确认）
            conflict_strategy: 冲突解决策略

        Returns:
            同步结果
        """
        self.logger.info("开始全量资源同步")

        try:
            # 1. 发现所有文件系统资源
            fs_resources = await self.discovery_service.discover_resources()
            self.logger.info(f"发现 {len(fs_resources)} 个文件系统资源")

            # 2. 获取数据库当前状态
            db_resources = await self._get_database_state()
            self.logger.info(f"数据库中存在 {len(db_resources)} 个资源")

            # 3. 计算差异
            plan = self.diff_engine.calculate_sync_plan(fs_resources, db_resources)

            # 4. 解决冲突
            if conflict_strategy != 'latest_wins':
                plan = self.conflict_resolver.resolve_conflicts(plan, conflict_strategy)

            if not plan.actions:
                self.logger.info("无需要同步的操作")
                result = SyncResult()
                result.success = True
                result.complete()
                return result

            self._log_sync_plan(plan)

            # 5. 执行同步（如果不是干运行）
            if dry_run:
                self.logger.info("干运行模式，跳过实际执行")
                result = SyncResult()
                result.total_actions = len(plan.actions)
                result.successful_actions = len(plan.actions)  # 假设都成功
                result.success = True
                result.complete()
            else:
                # 根据操作数量选择执行器
                result = await self.executor.execute_plan(plan)

            # 6. 记录监控信息
            self.monitor.log_sync_result(result)

            return result

        except Exception as e:
            self.logger.error(f"资源同步失败: {e}")
            result = SyncResult()
            result.success = False
            result.errors = [{'error': str(e), 'timestamp': 'now'}]
            result.complete()
            return result

    async def sync_single_resource(self,
                                 resource_id: str,
                                 dry_run: bool = False) -> SyncResult:
        """
        同步单个资源

        Args:
            resource_id: 资源ID
            dry_run: 是否为干运行模式

        Returns:
            同步结果
        """
        self.logger.info(f"开始同步单个资源: {resource_id}")

        try:
            # 发现所有资源，然后筛选出指定的资源
            all_fs_resources = await self.discovery_service.discover_resources()

            if resource_id not in all_fs_resources:
                raise ValueError(f"资源不存在: {resource_id}")

            fs_resource = {resource_id: all_fs_resources[resource_id]}
            db_resource_raw = await self._get_single_resource_db_state(resource_id)

            # 转换为ResourceState格式
            from .models import ResourceState
            db_resource = {}
            if db_resource_raw:
                # 如果数据库中有资源记录，创建ResourceState对象
                db_resource[resource_id] = ResourceState(
                    id=resource_id,
                    resource_type=db_resource_raw.get('resource_type', 'practice'),
                    checksum=db_resource_raw.get('checksum'),
                    last_modified=db_resource_raw.get('updated_at', db_resource_raw.get('created_at')),
                    metadata=db_resource_raw,
                    files=db_resource_raw.get('files', {})
                )

            # 计算差异
            plan = self.diff_engine.calculate_sync_plan(fs_resource, db_resource)

            if not plan.actions:
                self.logger.info(f"资源 {resource_id} 已是最新")
                result = SyncResult()
                result.success = True
                result.complete()
                return result

            self._log_sync_plan(plan)

            # 执行同步
            if dry_run:
                result = SyncResult()
                result.total_actions = len(plan.actions)
                result.successful_actions = len(plan.actions)
                result.success = True
                result.complete()
            else:
                result = await self.executor.execute_plan(plan)

            self.monitor.log_sync_result(result)
            return result

        except Exception as e:
            self.logger.error(f"同步资源 {resource_id} 失败: {e}")
            result = SyncResult()
            result.success = False
            result.errors = [{'error': str(e), 'timestamp': 'now'}]
            result.complete()
            return result

    async def validate_resources(self) -> Dict[str, Any]:
        """
        验证资源完整性

        Returns:
            验证结果
        """
        self.logger.info("开始验证资源完整性")

        try:
            resources = await self.discovery_service.discover_resources()

            total_resources = len(resources)
            valid_resources = 0
            invalid_resources = []

            for resource_id, manifest in resources.items():
                try:
                    metadata = manifest.metadata

                    # 验证文件依赖
                    missing_files = metadata.validate_file_dependencies(manifest.base_path)
                    if missing_files:
                        invalid_resources.append({
                            'id': resource_id,
                            'title': metadata.title,
                            'issues': [f"缺少文件: {', '.join(missing_files)}"]
                        })
                        continue

                    # 验证校验和
                    if not metadata.validate_checksum():
                        invalid_resources.append({
                            'id': resource_id,
                            'title': metadata.title,
                            'issues': ["校验和验证失败"]
                        })
                        continue

                    valid_resources += 1

                except Exception as e:
                    invalid_resources.append({
                        'id': resource_id,
                        'title': getattr(manifest.metadata, 'title', '未知') if manifest.metadata else '未知',
                        'issues': [str(e)]
                    })

            result = {
                'total_resources': total_resources,
                'valid_resources': valid_resources,
                'invalid_resources': invalid_resources,
                'success_rate': valid_resources / total_resources if total_resources > 0 else 0
            }

            self.logger.info(f"验证完成: {valid_resources}/{total_resources} 个资源有效")
            return result

        except Exception as e:
            self.logger.error(f"验证资源失败: {e}")
            return {
                'total_resources': 0,
                'valid_resources': 0,
                'invalid_resources': [{'issues': [str(e)]}],
                'success_rate': 0
            }

    def get_health_status(self) -> HealthStatus:
        """获取系统健康状态"""
        return self.monitor.get_health_report()['health_status']

    def get_monitoring_report(self) -> Dict[str, Any]:
        """获取监控报告"""
        return self.monitor.get_health_report()

    async def _get_database_state(self) -> Dict[str, Any]:
        """
        获取数据库当前状态
        这里应该从实际的数据库查询，但暂时返回空字典
        """
        # TODO: 实现从数据库查询实际状态的逻辑
        # 为了测试目的，返回包含资源ID的模拟状态
        from .models import ResourceState
        return {}  # 对于全量同步，返回空字典表示数据库为空

    async def _get_single_resource_db_state(self, resource_id: str) -> Dict[str, Any]:
        """
        获取单个资源的数据库状态
        """
        # TODO: 实现从数据库查询单个资源状态的逻辑
        # 暂时返回空字典，模拟数据库中没有该资源
        return {}

    def _log_sync_plan(self, plan: SyncPlan):
        """记录同步计划"""
        self.logger.info(f"同步计划包含 {len(plan.actions)} 个操作:")

        actions_by_type = {}
        for action in plan.actions:
            action_type = action.action_type
            if action_type not in actions_by_type:
                actions_by_type[action_type] = []
            actions_by_type[action_type].append(action)

        for action_type, actions in actions_by_type.items():
            self.logger.info(f"  {action_type}: {len(actions)} 个操作")
            for action in actions[:3]:  # 只记录前3个
                self.logger.info(f"    - {action.resource_id}: {action.reason}")


# 全局服务实例
_sync_service_instance: Optional[ResourceSyncService] = None


def get_resource_sync_service() -> ResourceSyncService:
    """获取资源同步服务实例"""
    global _sync_service_instance
    if _sync_service_instance is None:
        _sync_service_instance = ResourceSyncService()
    return _sync_service_instance
