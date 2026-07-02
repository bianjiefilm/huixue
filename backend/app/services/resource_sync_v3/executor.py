"""
单一来源事实 - V3.0 事务性执行器

负责执行同步计划中的所有操作，确保操作的原子性和一致性。
处理数据库变更和文件系统操作的协调。
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from .models import (
    SyncAction, SyncActionType, ResourceManifest,
    ResourceMetadata
)
from app.models.models import TrainingAsset
from .file_manager import FileManager
from .data_importer import DataImporter

logger = logging.getLogger(__name__)


class TransactionalExecutor:
    """事务性执行器

    以事务方式执行同步操作，确保数据一致性。
    处理元数据同步和文件资源管理。
    """

    def __init__(self, static_root: str, db_url: str = None):
        """
        初始化执行器

        Args:
            static_root: 静态文件根目录路径
            db_url: 数据库连接URL
        """
        self.static_root = Path(static_root)
        self.file_manager = FileManager(self.static_root)
        self.data_importer = DataImporter(str(static_root), db_url)
        self.logger = logging.getLogger(__name__)

        # 确保目录存在
        self.static_root.mkdir(parents=True, exist_ok=True)

    async def execute_sync_plan(self, db: Session, plan: List[SyncAction]) -> Dict[str, Any]:
        """
        执行同步计划

        Args:
            db: 数据库会话
            plan: 同步动作列表

        Returns:
            执行结果字典
        """
        results = {
            'success': True,
            'executed_actions': 0,
            'failed_actions': 0,
            'errors': [],
            'details': []
        }

        # 按类型分组执行
        actions_by_type = self._group_actions_by_type(plan)

        try:
            # 1. 先执行删除操作
            if SyncActionType.DELETE in actions_by_type:
                delete_results = await self._execute_delete_actions(db, actions_by_type[SyncActionType.DELETE])
                results['executed_actions'] += delete_results['executed']
                results['failed_actions'] += delete_results['failed']
                results['errors'].extend(delete_results['errors'])
                results['details'].extend(delete_results['details'])

            # 2. 再执行创建和更新操作
            for action_type in [SyncActionType.CREATE, SyncActionType.UPDATE]:
                if action_type in actions_by_type:
                    type_results = await self._execute_metadata_actions(db, actions_by_type[action_type])
                    results['executed_actions'] += type_results['executed']
                    results['failed_actions'] += type_results['failed']
                    results['errors'].extend(type_results['errors'])
                    results['details'].extend(type_results['details'])

            # 检查是否有失败的操作
            if results['failed_actions'] > 0:
                results['success'] = False

        except Exception as e:
            self.logger.error(f"执行同步计划失败: {e}")
            results['success'] = False
            results['errors'].append(f"执行失败: {str(e)}")

        return results

    def _group_actions_by_type(self, actions: List[SyncAction]) -> Dict[SyncActionType, List[SyncAction]]:
        """按动作类型分组"""
        grouped = {}
        for action in actions:
            if action.action_type not in grouped:
                grouped[action.action_type] = []
            grouped[action.action_type].append(action)
        return grouped

    async def _execute_delete_actions(self, db: Session, actions: List[SyncAction]) -> Dict[str, Any]:
        """执行删除操作"""
        results = {
            'executed': 0,
            'failed': 0,
            'errors': [],
            'details': []
        }

        for action in actions:
            try:
                await self._execute_delete_action(db, action)
                results['executed'] += 1
                results['details'].append(f"✅ 删除成功: {action.resource_id}")
                self.logger.info(f"删除资源成功: {action.resource_id}")
            except Exception as e:
                results['failed'] += 1
                error_msg = f"删除失败 {action.resource_id}: {str(e)}"
                results['errors'].append(error_msg)
                results['details'].append(f"❌ {error_msg}")
                self.logger.error(error_msg)

        return results

    async def _execute_delete_action(self, db: Session, action: SyncAction):
        """执行单个删除操作"""
        resource_id = action.resource_id

        # 删除实训资源
        if action.resource_type == 'training':
            # 删除training_assets
            db.execute(text("DELETE FROM training_assets WHERE training_id = :id"), {'id': resource_id})

            # 删除training_datasets
            db.execute(text("DELETE FROM training_datasets WHERE training_id = :id"), {'id': resource_id})

            # 删除trainings表记录
            db.execute(text("DELETE FROM trainings WHERE id = :id"), {'id': resource_id})

        # 删除实践资源
        elif action.resource_type == 'practice':
            # 删除相关联的tasks
            db.execute(text("DELETE FROM tasks WHERE practice_id = :id"), {'id': resource_id})

            # 删除practice_code_repositories
            db.execute(text("DELETE FROM practice_code_repositories WHERE practice_id = :id"), {'id': resource_id})

            # 删除practice_datasets
            db.execute(text("DELETE FROM practice_datasets WHERE practice_id = :id"), {'id': resource_id})

            # 删除practice_skills
            db.execute(text("DELETE FROM practice_skills WHERE practice_id = :id"), {'id': resource_id})

            # 删除practices表记录
            db.execute(text("DELETE FROM practices WHERE id = :id"), {'id': resource_id})

        # 删除关联的静态文件
        await self.file_manager.cleanup_resource_files(resource_id)

    async def _execute_metadata_actions(self, db: Session, actions: List[SyncAction]) -> Dict[str, Any]:
        """执行元数据操作（创建和更新）"""
        results = {
            'executed': 0,
            'failed': 0,
            'errors': [],
            'details': []
        }

        for action in actions:
            try:
                await self._execute_metadata_action(db, action)
                results['executed'] += 1
                action_desc = "创建" if action.action_type == SyncActionType.CREATE else "更新"
                results['details'].append(f"✅ {action_desc}成功: {action.resource_id}")
                self.logger.info(f"{action_desc}资源成功: {action.resource_id}")
            except Exception as e:
                results['failed'] += 1
                action_desc = "创建" if action.action_type == SyncActionType.CREATE else "更新"
                error_msg = f"{action_desc}失败 {action.resource_id}: {str(e)}"
                results['errors'].append(error_msg)
                results['details'].append(f"❌ {error_msg}")
                self.logger.error(error_msg)

        return results

    async def _execute_metadata_action(self, db: Session, action: SyncAction):
        """执行单个元数据操作"""
        if not action.manifest:
            raise ValueError(f"动作 {action} 缺少资源清单")

        metadata = action.manifest.metadata

        if action.resource_type == 'training':
            await self._execute_training_action(db, action, metadata)
        elif action.resource_type == 'practice':
            await self._execute_practice_action(db, action, metadata)
        else:
            raise ValueError(f"不支持的资源类型: {action.resource_type}")

    async def _execute_training_action(self, db: Session, action: SyncAction, metadata: ResourceMetadata):
        """执行实训操作（增强版，包含数据导入）"""
        training_data = self._prepare_training_data(metadata)

        if action.action_type == SyncActionType.CREATE:
            # 插入trainings表（不指定id，让数据库自动生成）
            insert_query = text("""
                INSERT INTO trainings (
                    title, training_type, intro, industry, difficulty, prerequisites,
                    learning_objectives, tags, course_hours, estimated_completion_time,
                    handbook_content, assignment_nodes, require_design_files, require_experiment_report,
                    environment_id, storage_limit, memory_limit, cpu_limit,
                    publish_status, visibility, is_published, published_at,
                    creator_id, created_at, updated_at, version
                ) VALUES (
                    :title, :training_type, :intro, :industry, :difficulty, :prerequisites,
                    :learning_objectives, :tags, :course_hours, :estimated_completion_time,
                    :handbook_content, :assignment_nodes, :require_design_files, :require_experiment_report,
                    :environment_id, :storage_limit, :memory_limit, :cpu_limit,
                    :publish_status, :visibility, :is_published, :published_at,
                    :creator_id, :created_at, :updated_at, :version
                )
            """)
            db.execute(insert_query, training_data)

            # 获取刚插入的training ID (SQLite兼容)
            training_id = db.execute(text("SELECT last_insert_rowid()")).scalar()
            self.logger.info(f"创建实训成功，ID: {training_id}")

            # 导入实训数据
            base_path = action.manifest.base_path
            self.logger.info(f"开始导入实训 {training_id} 的数据...")

            data_import_result = await self.data_importer.import_training_data(metadata, base_path, db)

            if data_import_result['success']:
                self.logger.info(f"实训 {training_id} 数据导入成功: {data_import_result['imported_datasets']} 个数据集, {data_import_result['imported_records']} 条记录")
            else:
                self.logger.warning(f"实训 {training_id} 数据导入失败: {data_import_result['errors']}")

            # 验证数据完整性
            integrity_result = await self.data_importer.validate_data_integrity(metadata, db)
            if integrity_result['valid']:
                self.logger.info(f"实训 {training_id} 数据完整性验证通过")
            else:
                self.logger.warning(f"实训 {training_id} 数据完整性检查失败: {integrity_result['issues']}")

        elif action.action_type == SyncActionType.UPDATE:
            # 更新trainings表
            update_query = text("""
                UPDATE trainings SET
                    title = :title, training_type = :training_type, intro = :intro,
                    industry = :industry, difficulty = :difficulty, prerequisites = :prerequisites,
                    learning_objectives = :learning_objectives, tags = :tags,
                    course_hours = :course_hours, estimated_completion_time = :estimated_completion_time,
                    handbook_content = :handbook_content, assignment_nodes = :assignment_nodes,
                    require_design_files = :require_design_files, require_experiment_report = :require_experiment_report,
                    environment_id = :environment_id, storage_limit = :storage_limit,
                    memory_limit = :memory_limit, cpu_limit = :cpu_limit,
                    updated_at = :updated_at, version = :version
                WHERE id = :id
            """)
            db.execute(update_query, training_data)

        # 处理资源文件
        await self._process_training_resources(db, action, metadata)

    async def _execute_practice_action(self, db: Session, action: SyncAction, metadata: ResourceMetadata):
        """执行实践操作"""
        practice_data = self._prepare_practice_data(metadata)

        if action.action_type == SyncActionType.CREATE:
            # 插入practices表
            insert_query = text("""
                INSERT INTO practices (
                    id, title, description, direction, category, difficulty,
                    parent_course_id, summary, coin, task_count, order_index,
                    practice_type, intro, categories, environment_id,
                    storage_limit, memory_limit, cpu_limit,
                    enable_code_editor, enable_terminal, repo_visibility, allow_skip_levels,
                    publish_status, visibility, published_at, creator_id, created_at, updated_at
                ) VALUES (
                    :id, :title, :description, :direction, :category, :difficulty,
                    :parent_course_id, :summary, :coin, :task_count, :order_index,
                    :practice_type, :intro, :categories, :environment_id,
                    :storage_limit, :memory_limit, :cpu_limit,
                    :enable_code_editor, :enable_terminal, :repo_visibility, :allow_skip_levels,
                    :publish_status, :visibility, :published_at, :creator_id, :created_at, :updated_at
                )
            """)
            db.execute(insert_query, practice_data)

        elif action.action_type == SyncActionType.UPDATE:
            # 更新practices表
            update_query = text("""
                UPDATE practices SET
                    title = :title, description = :description, direction = :direction,
                    category = :category, difficulty = :difficulty, summary = :summary,
                    coin = :coin, task_count = :task_count, order_index = :order_index,
                    practice_type = :practice_type, intro = :intro, categories = :categories,
                    environment_id = :environment_id, storage_limit = :storage_limit,
                    memory_limit = :memory_limit, cpu_limit = :cpu_limit,
                    updated_at = :updated_at
                WHERE id = :id
            """)
            db.execute(update_query, practice_data)

        # 处理实践相关的资源文件（如果有的话）
        await self._process_practice_resources(db, action, metadata)

    def _prepare_training_data(self, metadata: ResourceMetadata) -> Dict[str, Any]:
        """准备实训数据"""
        import json
        from app.core.enums import TrainingTypeEnum, TrainingPublishStatusEnum, TrainingVisibilityEnum, DifficultyLevelEnum

        # 转换枚举值为字符串
        training_type = metadata.training_type
        if hasattr(training_type, 'value'):
            training_type = training_type.value

        difficulty = metadata.difficulty
        if hasattr(difficulty, 'value'):
            difficulty = difficulty.value

        return {
            'title': metadata.title,
            'training_type': training_type,
            'intro': metadata.intro,
            'industry': metadata.industry,
            'difficulty': difficulty,
            'prerequisites': json.dumps([]),  # 暂时为空数组
            'learning_objectives': json.dumps([]),  # 暂时为空数组
            'tags': json.dumps([]),  # 暂时为空数组
            'course_hours': metadata.course_hours,
            'estimated_completion_time': f"{metadata.course_hours}小时",
            'handbook_content': None,  # 将通过文件管理器处理
            'assignment_nodes': json.dumps([node.dict() for node in metadata.assignment_nodes]),
            'require_design_files': metadata.require_design_files,
            'require_experiment_report': metadata.require_experiment_report,
            'environment_id': metadata.environment_config.docker_image_name,
            'storage_limit': '1Gi',
            'memory_limit': '1Gi',
            'cpu_limit': '1',
            'publish_status': 'EDITING',
            'visibility': 'PRIVATE',
            'is_published': False,
            'published_at': None,
            'creator_id': 1,  # 默认创建者ID
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'version': metadata.version
        }

    def _prepare_practice_data(self, metadata: ResourceMetadata) -> Dict[str, Any]:
        """准备实践数据"""
        import json

        return {
            'id': metadata.id,
            'title': metadata.title,
            'description': metadata.intro,
            'direction': metadata.industry if hasattr(metadata, 'industry') else '未分类',
            'category': '编程实践' if metadata.training_type == 'coding' else '数据分析',
            'difficulty': metadata.difficulty,
            'parent_course_id': None,
            'summary': metadata.intro,
            'coin': 100,  # 默认金币数
            'task_count': 0,  # 稍后计算
            'order_index': 0,
            'practice_type': 'online_coding' if metadata.training_type == 'coding' else 'cloud_desktop',
            'intro': metadata.intro,
            'categories': json.dumps([metadata.industry]),
            'environment_id': metadata.environment_config.docker_image_name,
            'storage_limit': '1Gi',
            'memory_limit': '1Gi',
            'cpu_limit': '1',
            'enable_code_editor': True,
            'enable_terminal': True,
            'repo_visibility': 'visible',
            'allow_skip_levels': True,
            'publish_status': 'EDITING',
            'visibility': 'PRIVATE',
            'published_at': None,
            'creator_id': 1,  # 默认创建者ID
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

    async def _process_training_resources(self, db: Session, action: SyncAction, metadata: ResourceMetadata):
        """处理实训资源文件"""
        training_id = metadata.id

        # 处理handbook文件
        if metadata.handbook_content_path:
            handbook_url = await self.file_manager.process_file(
                action.manifest.base_path / metadata.handbook_content_path,
                f"trainings/{training_id}/handbook.md"
            )
            if handbook_url:
                db.execute(
                    text("UPDATE trainings SET handbook_content_url = :url WHERE id = :id"),
                    {'url': handbook_url, 'id': training_id}
                )

        # 处理封面文件
        if metadata.cover_url_path:
            cover_url = await self.file_manager.process_file(
                action.manifest.base_path / metadata.cover_url_path,
                f"trainings/{training_id}/cover{Path(metadata.cover_url_path).suffix}"
            )
            if cover_url:
                db.execute(
                    text("UPDATE trainings SET cover_url = :url WHERE id = :id"),
                    {'url': cover_url, 'id': training_id}
                )

        # 处理内容资源
        await self._process_content_resources(db, training_id, metadata, action.manifest.base_path)

    async def _process_content_resources(self, db: Session, training_id: str, metadata: ResourceMetadata, base_path: Path):
        """处理内容资源清单"""
        import json

        # 删除现有的资源记录
        db.execute(text("DELETE FROM training_assets WHERE training_id = :id"), {'id': training_id})
        db.execute(text("DELETE FROM training_datasets WHERE training_id = :id"), {'id': training_id})

        # 处理数据集
        for dataset in metadata.content_resources.datasets:
            file_path = base_path / dataset.path
            asset_url = await self.file_manager.process_file(
                file_path,
                f"trainings/{training_id}/datasets/{Path(dataset.path).name}"
            )
            if asset_url:
                db.execute(text("""
                    INSERT INTO training_datasets (
                        training_id, name, file_url, file_type, description, uploader_id
                    ) VALUES (:training_id, :name, :file_url, :file_type, :description, :uploader_id)
                """), {
                    'training_id': training_id,
                    'name': dataset.name,
                    'file_url': asset_url,
                    'file_type': Path(dataset.path).suffix[1:],  # 去掉点
                    'description': dataset.description or '',
                    'uploader_id': 1
                })

        # 处理SQL脚本
        for sql_script in metadata.content_resources.sql_scripts:
            file_path = base_path / sql_script.path
            asset_url = await self.file_manager.process_file(
                file_path,
                f"trainings/{training_id}/sql/{Path(sql_script.path).name}"
            )
            if asset_url:
                db.execute(text("""
                    INSERT INTO training_assets (
                        training_id, name, relative_path, file_type, description, asset_type, uploader_id
                    ) VALUES (:training_id, :name, :relative_path, :file_type, :description, :asset_type, :uploader_id)
                """), {
                    'training_id': training_id,
                    'name': sql_script.name,
                    'relative_path': f"sql/{Path(sql_script.path).name}",
                    'file_type': 'sql',
                    'description': sql_script.description or '',
                    'asset_type': 'sql_script',
                    'uploader_id': 1
                })

        # 处理BI模板
        for bi_template in metadata.content_resources.bi_templates:
            file_path = base_path / bi_template.path
            asset_url = await self.file_manager.process_file(
                file_path,
                f"trainings/{training_id}/bi_templates/{Path(bi_template.path).name}"
            )
            if asset_url:
                db.execute(text("""
                    INSERT INTO training_assets (
                        training_id, name, relative_path, file_type, description, asset_type, uploader_id
                    ) VALUES (:training_id, :name, :relative_path, :file_type, :description, :asset_type, :uploader_id)
                """), {
                    'training_id': training_id,
                    'name': bi_template.name,
                    'relative_path': f"bi_templates/{Path(bi_template.path).name}",
                    'file_type': Path(bi_template.path).suffix[1:],
                    'description': bi_template.description or '',
                    'asset_type': 'bi_template',
                    'uploader_id': 1
                })

    async def _process_practice_resources(self, db: Session, action: SyncAction, metadata: ResourceMetadata):
        """处理实践资源文件（目前主要是文件管理）"""
        # 实践资源可能不需要特殊的资源文件处理
        # 这里可以根据需要添加处理逻辑
        pass
