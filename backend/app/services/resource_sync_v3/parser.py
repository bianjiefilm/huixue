"""
单一来源事实 - V3.0 元数据解析器

负责解析和验证metadata.json文件的详细逻辑。
提供更丰富的错误信息和修复建议。
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .models import (
    ResourceType, ResourceMetadata, ValidationError,
    ContentResource, AssetType, EnvironmentConfig
)
from app.utils.metadata_validators import (
    clean_empty_values as _clean_empty_values,
    migrate_legacy_format as _migrate_legacy_format,
    validate_required_fields as _validate_required_fields,
    validate_data_formats as _validate_data_formats,
    validate_content_resources as _validate_content_resources,
    validate_business_rules as _validate_business_rules,
    suggest_fixes as _suggest_fixes,
)

logger = logging.getLogger(__name__)


class MetadataParser:
    """元数据解析器

    提供详细的metadata.json解析和验证功能，
    包括错误诊断和自动修复建议。
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_metadata_file(self, file_path: Path, resource_type: ResourceType) -> Tuple[Optional[ResourceMetadata], List[str]]:
        """
        解析metadata.json文件

        Args:
            file_path: metadata.json文件路径
            resource_type: 资源类型

        Returns:
            (ResourceMetadata对象, 错误信息列表)
            如果解析成功，错误列表为空
        """
        errors = []

        try:
            # 读取和解析JSON
            data = self._read_json_file(file_path)
            if data is None:
                return None, ["无法读取或解析JSON文件"]

            # 预处理数据
            data = self._preprocess_data(data, resource_type)

            # 验证必需字段
            validation_errors = self._validate_required_fields(data, resource_type)
            if validation_errors:
                errors.extend(validation_errors)

            # 验证数据类型和格式
            format_errors = self._validate_data_formats(data)
            if format_errors:
                errors.extend(format_errors)

            # 验证业务逻辑
            business_errors = self._validate_business_rules(data, resource_type)
            if business_errors:
                errors.extend(business_errors)

            # 如果有错误，返回None和错误列表
            if errors:
                return None, errors

            # 创建ResourceMetadata对象
            try:
                metadata = ResourceMetadata(**data)
                return metadata, []
            except Exception as e:
                return None, [f"创建元数据对象失败: {str(e)}"]

        except Exception as e:
            self.logger.error(f"解析metadata文件出错 {file_path}: {e}")
            return None, [f"解析过程出错: {str(e)}"]

    def _read_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """读取JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            return None
        except FileNotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"读取文件失败 {file_path}: {e}")
            return None

    def _preprocess_data(self, data: Dict[str, Any], resource_type: ResourceType) -> Dict[str, Any]:
        """预处理数据，添加默认值和转换格式"""
        # 添加资源类型
        data['resource_type'] = resource_type

        # 添加版本号
        if 'version' not in data:
            data['version'] = '1.0.0'

        # 处理时间戳
        for time_field in ['created_at', 'updated_at']:
            if time_field in data and isinstance(data[time_field], str):
                try:
                    data[time_field] = datetime.fromisoformat(data[time_field].replace('Z', '+00:00'))
                except:
                    # 如果解析失败，移除字段
                    del data[time_field]

        # 处理空值
        data = self._clean_empty_values(data)

        # 迁移旧格式
        data = self._migrate_legacy_format(data, resource_type)

        return data

    def _clean_empty_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理空值（委托给纯函数）"""
        return _clean_empty_values(data)

    def _migrate_legacy_format(self, data: Dict[str, Any], resource_type: ResourceType) -> Dict[str, Any]:
        """迁移旧格式数据（委托给纯函数）"""
        return _migrate_legacy_format(data)

    def _validate_required_fields(self, data: Dict[str, Any], resource_type: ResourceType) -> List[str]:
        """验证必需字段（委托给纯函数）"""
        is_training = (resource_type == ResourceType.TRAINING)
        return _validate_required_fields(data, is_training=is_training)

    def _validate_data_formats(self, data: Dict[str, Any]) -> List[str]:
        """验证数据格式（委托给纯函数）"""
        return _validate_data_formats(data)

    def _validate_content_resources(self, content_resources: Dict[str, Any]) -> List[str]:
        """验证内容资源格式（委托给纯函数）"""
        return _validate_content_resources(content_resources)

    def _validate_business_rules(self, data: Dict[str, Any], resource_type: ResourceType) -> List[str]:
        """验证业务规则（委托给纯函数）"""
        is_training = (resource_type == ResourceType.TRAINING)
        return _validate_business_rules(data, is_training=is_training)

    def validate_resource_files(self, metadata: ResourceMetadata, base_path: Path) -> List[str]:
        """
        验证资源文件是否存在

        Args:
            metadata: 资源元数据
            base_path: 基础路径

        Returns:
            错误信息列表
        """
        errors = []

        # 检查handbook文件
        if metadata.handbook_content_path:
            handbook_path = base_path / metadata.handbook_content_path
            if not handbook_path.exists():
                errors.append(f"手册文件不存在: {metadata.handbook_content_path}")
            elif not handbook_path.is_file():
                errors.append(f"手册路径不是文件: {metadata.handbook_content_path}")

        # 检查封面文件
        if metadata.cover_url_path:
            cover_path = base_path / metadata.cover_url_path
            if not cover_path.exists():
                errors.append(f"封面文件不存在: {metadata.cover_url_path}")
            elif not cover_path.is_file():
                errors.append(f"封面路径不是文件: {metadata.cover_url_path}")

        # 检查内容资源文件
        for resource_list_name, resource_list in [
            ('datasets', metadata.content_resources.datasets),
            ('sql_scripts', metadata.content_resources.sql_scripts),
            ('bi_templates', metadata.content_resources.bi_templates),
            ('ai_models', metadata.content_resources.ai_models)
        ]:
            for resource in resource_list:
                resource_path = base_path / resource.path
                if not resource_path.exists():
                    errors.append(f"{resource_list_name}资源文件不存在: {resource.path}")
                elif not resource_path.is_file():
                    errors.append(f"{resource_list_name}资源路径不是文件: {resource.path}")

        return errors

    def suggest_fixes(self, errors: List[str], data: Dict[str, Any]) -> Dict[str, Any]:
        """根据错误信息提供修复建议（委托给纯函数）"""
        return _suggest_fixes(errors)
