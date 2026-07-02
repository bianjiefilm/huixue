#!/usr/bin/env python3
"""
资源同步命令行工具
"""
import asyncio
import sys
import logging
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.resource_sync.discovery import ResourceDiscoveryService
from app.services.resource_sync.diff_engine import IntelligentDiffEngine
from app.services.resource_sync.executor import TransactionalExecutor
from app.services.resource_sync.monitoring import ResourceSyncMonitor


class ResourceSyncCLI:
    """资源同步命令行接口"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitor = ResourceSyncMonitor()

        # 初始化组件
        # 资源目录：优先使用环境变量，否则使用默认路径
        import os
        resource_base_dir = os.environ.get('RESOURCE_BASE_DIR') or os.environ.get('HUIXUE_RESOURCE_DIR')
        if not resource_base_dir:
            # 本地开发时使用项目根目录的 ziyuan_data
            resource_base_dir = str(project_root.parent / "ziyuan_data")

        self.discovery_service = ResourceDiscoveryService(
            base_path=resource_base_dir,
            logger=self.logger
        )

        self.diff_engine = IntelligentDiffEngine(logger=self.logger)
        self.executor = TransactionalExecutor(logger=self.logger)

    async def sync_all(self, dry_run: bool = False, force: bool = False):
        """同步所有资源"""
        self.logger.info("开始全量资源同步")

        try:
            # 1. 发现文件系统资源
            with self.monitor.record_sync_attempt('discover'):
                fs_resources = await self.discovery_service.discover_resources()

            self.logger.info(f"发现 {len(fs_resources)} 个文件系统资源")

            # 2. 获取数据库状态（这里需要实现）
            db_resources = await self._get_database_state()

            # 3. 计算差异
            plan = self.diff_engine.calculate_sync_plan(fs_resources, db_resources)
            self.logger.info(f"生成同步计划: {len(plan.actions)} 个操作")

            # 打印计划摘要
            self._print_plan_summary(plan)

            if dry_run:
                self.logger.info("干运行模式，跳过实际执行")
                return

            if not force and plan.actions:
                # 询问用户确认
                if not self._confirm_execution(plan):
                    self.logger.info("用户取消执行")
                    return

            # 4. 执行同步
            result = await self.executor.execute_plan(plan)

            # 5. 记录结果
            self.monitor.log_sync_result(result)

            # 6. 打印结果
            self._print_result_summary(result)

        except Exception as e:
            self.logger.error(f"同步失败: {e}")
            raise

    async def sync_resource(self, resource_id: str, dry_run: bool = False):
        """同步单个资源"""
        self.logger.info(f"开始同步单个资源: {resource_id}")

        try:
            # 发现特定资源
            fs_resources = await self.discovery_service.discover_resources()
            if resource_id not in fs_resources:
                raise ValueError(f"资源不存在: {resource_id}")

            fs_resource = {resource_id: fs_resources[resource_id]}

            # 获取数据库状态
            db_resource_raw = await self._get_single_resource_db_state(resource_id)

            # 转换为ResourceState格式
            from app.services.resource_sync.models import ResourceState
            db_resource = {}
            if db_resource_raw:
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
                self.logger.info("资源已是最新，无需同步")
                return

            self._print_plan_summary(plan)

            if dry_run:
                return

            # 执行同步
            result = await self.executor.execute_plan(plan)
            self.monitor.log_sync_result(result)
            self._print_result_summary(result)

        except Exception as e:
            self.logger.error(f"同步资源失败 {resource_id}: {e}")
            raise

    async def validate_resources(self):
        """验证资源完整性"""
        self.logger.info("开始验证资源完整性")

        try:
            resources = await self.discovery_service.discover_resources()
            total_resources = len(resources)
            valid_resources = 0
            invalid_resources = []

            for resource_id, manifest in resources.items():
                try:
                    # 验证元数据
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
                        'title': manifest.metadata.title if manifest.metadata else '未知',
                        'issues': [str(e)]
                    })

            # 打印验证结果
            self.logger.info(f"验证完成: {valid_resources}/{total_resources} 个资源有效")

            if invalid_resources:
                self.logger.warning(f"发现 {len(invalid_resources)} 个无效资源:")
                for invalid in invalid_resources:
                    self.logger.warning(f"  - {invalid['id']} ({invalid['title']}): {', '.join(invalid['issues'])}")

        except Exception as e:
            self.logger.error(f"验证资源失败: {e}")
            raise

    async def show_health(self):
        """显示系统健康状态"""
        report = self.monitor.get_health_report()
        health = report['health_status']

        print("=== 系统健康状态 ===")
        print(f"整体健康: {health['overall_health']}")
        print(f"成功率: {health['success_rate']:.2%}")
        print(f"总操作数: {health['total_operations']}")
        print(f"最后同步时间: {health['last_sync_time'] or '从未同步'}")

        if report['recent_alerts']:
            print(f"\n=== 最近告警 ({len(report['recent_alerts'])} 个) ===")
            for alert in report['recent_alerts'][:5]:  # 只显示最近5个
                print(f"[{alert['level'].upper()}] {alert['message']}")

        print(f"\n=== 指标摘要 ===")
        summary = report['metrics_summary']
        for key, value in summary.items():
            print(f"{key}: {value}")

    async def _get_database_state(self) -> dict:
        """获取数据库状态（简化实现）"""
        # 这里应该从数据库查询实际状态
        # 暂时返回空字典，代表数据库中没有资源
        return {}

    def _print_plan_summary(self, plan):
        """打印计划摘要"""
        print("\n=== 同步计划 ===")
        actions_by_type = {}
        for action in plan.actions:
            action_type = action.action_type
            if action_type not in actions_by_type:
                actions_by_type[action_type] = []
            actions_by_type[action_type].append(action)

        for action_type, actions in actions_by_type.items():
            print(f"{action_type}: {len(actions)} 个操作")
            for action in actions[:3]:  # 只显示前3个
                print(f"  - {action.resource_id}: {action.reason}")

        print(f"总计: {len(plan.actions)} 个操作")

    def _print_result_summary(self, result):
        """打印结果摘要"""
        print("\n=== 同步结果 ===")
        print(f"总操作数: {result.total_actions}")
        print(f"成功操作: {result.successful_actions}")
        print(f"失败操作: {result.failed_actions}")
        print(f"执行时间: {(result.completed_at - result.started_at).total_seconds():.2f}秒" if result.completed_at else "未知")
        print(f"状态: {'成功' if result.success else '失败'}")

        if result.errors:
            print(f"\n失败详情 (前{len(result.errors)}个):")
            for error in result.errors[:5]:
                print(f"  - {error['action']['resource_id']}: {error['error']}")

    def _confirm_execution(self, plan) -> bool:
        """询问用户是否确认执行"""
        print(f"\n即将执行 {len(plan.actions)} 个操作，是否继续？(y/N): ", end="")
        try:
            response = input().strip().lower()
            return response in ['y', 'yes']
        except KeyboardInterrupt:
            print("\n操作已取消")
            return False

    async def _get_single_resource_db_state(self, resource_id: str):
        """
        获取单个资源的数据库状态
        """
        # TODO: 实现从数据库查询单个资源状态的逻辑
        # 暂时返回空字典，模拟数据库中没有该资源
        return {}


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="资源同步工具")
    parser.add_argument(
        "command",
        choices=["sync", "sync-resource", "validate", "health"],
        help="要执行的命令"
    )
    parser.add_argument(
        "--resource-id",
        help="资源ID (用于sync-resource命令)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干运行模式，只显示将要执行的操作，不实际执行"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制执行，不询问用户确认"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别"
    )

    args = parser.parse_args()

    # 设置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 创建CLI实例
    cli = ResourceSyncCLI()

    try:
        if args.command == "sync":
            await cli.sync_all(dry_run=args.dry_run, force=args.force)
        elif args.command == "sync-resource":
            if not args.resource_id:
                parser.error("--resource-id is required for sync-resource command")
            await cli.sync_resource(args.resource_id, dry_run=args.dry_run)
        elif args.command == "validate":
            await cli.validate_resources()
        elif args.command == "health":
            await cli.show_health()

    except Exception as e:
        logging.error(f"命令执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
