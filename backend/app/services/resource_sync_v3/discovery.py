"""
单一来源事实 - V3.0 资源发现服务

负责扫描ziyuan目录结构，发现所有有效的资源目录和metadata.json文件。
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import (
    ResourceType, ResourceMetadata, ResourceManifest,
    ValidationError, ContentResource, AssetType
)

logger = logging.getLogger(__name__)


class ResourceDiscoveryService:
    """资源发现服务

    扫描ziyuan目录结构，发现所有有效的资源目录。
    支持实训资源(training)和实践资源(practice)的自动识别。
    """

    def __init__(self, ziyuan_root: str):
        """
        初始化发现服务

        Args:
            ziyuan_root: ziyuan目录的根路径
        """
        self.ziyuan_root = Path(ziyuan_root)
        self.logger = logging.getLogger(__name__)

        if not self.ziyuan_root.exists():
            raise ValueError(f"ziyuan根目录不存在: {ziyuan_root}")

    async def discover_resources(self) -> Dict[str, Dict[str, ResourceManifest]]:
        """
        发现所有资源

        Returns:
            按资源类型分组的资源清单字典
            {
                "training": {"training_id": ResourceManifest},
                "practice": {"practice_id": ResourceManifest}
            }
        """
        self.logger.info(f"开始扫描资源目录: {self.ziyuan_root}")

        resources = {
            ResourceType.TRAINING: {},
            ResourceType.PRACTICE: {}
        }

        # 扫描实训资源
        training_dir = self.ziyuan_root / "实训资源"
        if training_dir.exists():
            self.logger.info("扫描实训资源目录...")
            training_resources = await self._scan_resource_directory(training_dir, ResourceType.TRAINING)
            resources[ResourceType.TRAINING] = training_resources
            self.logger.info(f"发现 {len(training_resources)} 个实训资源")

        # 扫描实践资源
        practice_dir = self.ziyuan_root / "课程资源"
        if practice_dir.exists():
            self.logger.info("扫描实践资源目录...")
            practice_resources = await self._scan_resource_directory(practice_dir, ResourceType.PRACTICE)
            resources[ResourceType.PRACTICE] = practice_resources
            self.logger.info(f"发现 {len(practice_resources)} 个实践资源")

        total_count = sum(len(res_list) for res_list in resources.values())
        self.logger.info(f"资源发现完成，共发现 {total_count} 个资源")

        return resources

    async def _scan_resource_directory(self, base_dir: Path, resource_type: ResourceType) -> Dict[str, ResourceManifest]:
        """
        扫描特定类型的资源目录

        Args:
            base_dir: 基础目录路径
            resource_type: 资源类型

        Returns:
            资源ID到ResourceManifest的映射
        """
        resources = {}

        if not base_dir.exists():
            self.logger.warning(f"资源目录不存在: {base_dir}")
            return resources

        # 遍历所有子目录
        for item in base_dir.iterdir():
            if not item.is_dir():
                continue

            try:
                # 检查是否包含metadata.json
                metadata_file = item / "metadata.json"
                if not metadata_file.exists():
                    self.logger.debug(f"跳过目录（无metadata.json）: {item.name}")
                    continue

                # 解析资源
                manifest = await self._process_resource_dir(item, resource_type)
                if manifest:
                    resource_id = manifest.metadata.id
                    resources[resource_id] = manifest
                    self.logger.debug(f"发现资源: {resource_type}:{resource_id}")
                else:
                    self.logger.warning(f"解析资源失败: {item.name}")

            except Exception as e:
                self.logger.error(f"处理资源目录出错 {item.name}: {e}")
                continue

        return resources

    async def _process_resource_dir(self, resource_dir: Path, resource_type: ResourceType) -> Optional[ResourceManifest]:
        """
        处理单个资源目录

        Args:
            resource_dir: 资源目录路径
            resource_type: 资源类型

        Returns:
            ResourceManifest对象，如果解析失败返回None
        """
        try:
            # 读取和解析metadata.json
            metadata_file = resource_dir / "metadata.json"
            metadata = await self._parse_metadata_file(metadata_file, resource_type)

            if not metadata:
                return None

            # 验证资源文件存在性
            if not await self._validate_resource_files(metadata, resource_dir):
                self.logger.error(f"资源文件验证失败: {resource_dir.name}")
                return None

            # 创建ResourceManifest
            manifest = ResourceManifest.from_metadata(metadata, resource_dir)

            return manifest

        except Exception as e:
            self.logger.error(f"处理资源目录失败 {resource_dir.name}: {e}")
            return None

    async def _parse_metadata_file(self, metadata_file: Path, resource_type: ResourceType) -> Optional[ResourceMetadata]:
        """
        解析metadata.json文件

        Args:
            metadata_file: metadata.json文件路径
            resource_type: 资源类型

        Returns:
            ResourceMetadata对象，如果解析失败返回None
        """
        try:
            # 读取JSON文件
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 添加资源类型
            data['resource_type'] = resource_type

            # 转换旧格式到新格式（如果需要）
            data = self._migrate_legacy_format(data, resource_type)

            # 创建并验证ResourceMetadata对象
            metadata = ResourceMetadata(**data)

            return metadata

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误 {metadata_file}: {e}")
            return None
        except ValidationError as e:
            self.logger.error(f"元数据验证错误 {metadata_file}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"解析metadata文件出错 {metadata_file}: {e}")
            return None

    def _migrate_legacy_format(self, data: Dict[str, Any], resource_type: ResourceType) -> Dict[str, Any]:
        """
        将旧格式的metadata迁移到新格式

        Args:
            data: 原始数据
            resource_type: 资源类型

        Returns:
            迁移后的数据
        """
        # 处理版本号
        if 'version' not in data:
            data['version'] = '1.0.0'

        # 处理资源类型特定的迁移
        if resource_type == ResourceType.TRAINING:
            # 实训资源迁移
            data = self._migrate_training_format(data)
        else:
            # 实践资源迁移
            data = self._migrate_practice_format(data)

        # 处理环境配置
        if 'environment_config' not in data:
            data['environment_config'] = self._infer_environment_config(data, resource_type)

        # 处理内容资源清单
        if 'content_resources' not in data:
            data['content_resources'] = self._extract_content_resources(data)

        return data

    def _migrate_training_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """迁移实训资源格式"""
        # 处理training_type
        if 'training_type' in data:
            # 转换旧的枚举值
            training_type_map = {
                'DRAG_DROP': 'drag_and_drop',
                'CODING': 'coding',
                'drag_and_drop': 'drag_and_drop',
                'coding': 'coding'
            }
            data['training_type'] = training_type_map.get(data['training_type'], 'drag_and_drop')

        # 处理difficulty
        if 'difficulty' in data:
            difficulty_map = {
                'easy': 'beginner',
                'medium': 'intermediate',
                'hard': 'advanced',
                'beginner': 'beginner',
                'intermediate': 'intermediate',
                'advanced': 'advanced'
            }
            data['difficulty'] = difficulty_map.get(data['difficulty'], 'beginner')

        return data

    def _migrate_practice_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """迁移实践资源格式"""
        # 实践资源通常没有training_type
        if 'training_type' in data:
            del data['training_type']
        return data

    def _infer_environment_config(self, data: Dict[str, Any], resource_type: ResourceType) -> Dict[str, Any]:
        """推断环境配置"""
        training_type = data.get('training_type', 'drag_and_drop')

        if resource_type == ResourceType.TRAINING:
            if training_type == 'coding':
                return {
                    'env_type': 'JUPYTER',
                    'docker_image_name': 'jupyter/scipy-notebook:latest'
                }
            else:  # drag_and_drop
                # 根据industry或其他字段推断是BI还是AI
                industry = data.get('industry', '').lower()
                if 'ai' in industry or '机器学习' in industry:
                    return {
                        'env_type': 'TEMPO_AI',
                        'docker_image_name': 'knime/knime-full:latest'
                    }
                else:
                    return {
                        'env_type': 'HUIXUE_BI',
                        'docker_image_name': 'apache/superset:latest'
                    }
        else:
            # 实践资源默认使用Jupyter
            return {
                'env_type': 'JUPYTER',
                'docker_image_name': 'jupyter/scipy-notebook:latest'
            }

    def _extract_content_resources(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从旧格式数据中提取内容资源"""
        content_resources = {
            'datasets': [],
            'sql_scripts': [],
            'bi_templates': [],
            'ai_models': []
        }

        # 处理datasets
        if 'datasets' in data and isinstance(data['datasets'], list):
            for dataset in data['datasets']:
                if isinstance(dataset, dict) and 'path' in dataset:
                    content_resources['datasets'].append({
                        'name': dataset.get('name', Path(dataset['path']).stem),
                        'path': dataset['path'],
                        'description': dataset.get('description', '')
                    })

        # 处理jupyter路径（编码式实训）
        if 'jupyter_notebooks_path' in data and data['jupyter_notebooks_path']:
            # 将jupyter目录下的.ipynb文件作为资源
            pass  # 这里将在文件验证阶段处理

        return content_resources

    async def _validate_resource_files(self, metadata: ResourceMetadata, base_path: Path) -> bool:
        """
        验证资源文件是否存在

        Args:
            metadata: 资源元数据
            base_path: 基础路径

        Returns:
            所有必需文件都存在返回True，否则False
        """
        try:
            # 检查handbook文件
            if metadata.handbook_content_path:
                handbook_path = base_path / metadata.handbook_content_path
                if not handbook_path.exists():
                    self.logger.error(f"手册文件不存在: {handbook_path}")
                    return False

            # 检查封面文件
            if metadata.cover_url_path:
                cover_path = base_path / metadata.cover_url_path
                if not cover_path.exists():
                    self.logger.error(f"封面文件不存在: {cover_path}")
                    return False

            # 检查内容资源文件
            for resource_list in [
                metadata.content_resources.datasets,
                metadata.content_resources.sql_scripts,
                metadata.content_resources.bi_templates,
                metadata.content_resources.ai_models
            ]:
                for resource in resource_list:
                    resource_path = base_path / resource.path
                    if not resource_path.exists():
                        self.logger.error(f"资源文件不存在: {resource_path}")
                        return False

            return True

        except Exception as e:
            self.logger.error(f"验证资源文件出错: {e}")
            return False

    async def discover_single_resource(self, resource_id: str, resource_type: ResourceType) -> Optional[ResourceManifest]:
        """
        发现单个资源

        Args:
            resource_id: 资源ID
            resource_type: 资源类型

        Returns:
            ResourceManifest对象，不存在返回None
        """
        # 确定基础目录
        if resource_type == ResourceType.TRAINING:
            base_dir = self.ziyuan_root / "实训资源"
        else:
            base_dir = self.ziyuan_root / "课程资源"

        # 查找包含指定ID的目录
        for item in base_dir.iterdir():
            if not item.is_dir():
                continue

            try:
                metadata_file = item / "metadata.json"
                if not metadata_file.exists():
                    continue

                # 读取metadata并检查ID
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if data.get('id') == resource_id:
                    return await self._process_resource_dir(item, resource_type)

            except Exception as e:
                self.logger.debug(f"检查目录 {item.name} 时出错: {e}")
                continue

        return None
