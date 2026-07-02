#!/usr/bin/env python3
"""
数据导入器 - 处理多种数据源的导入

支持的数据源类型：
1. SQL脚本执行
2. CSV文件导入
3. API数据拉取
4. 对象存储文件下载
"""

import asyncio
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import requests
import json

from .models import ContentResource, ResourceMetadata

logger = logging.getLogger(__name__)


class DataImporter:
    """数据导入器"""

    def __init__(self, static_root: str, db_url: str = None):
        """
        初始化数据导入器

        Args:
            static_root: 静态文件根目录
            db_url: 数据库连接URL（可选，用于直接数据库操作）
        """
        self.static_root = Path(static_root)
        self.db_url = db_url
        self.logger = logging.getLogger(__name__)

    async def import_training_data(self, metadata: ResourceMetadata, base_path: Path, db: Session) -> Dict[str, Any]:
        """
        导入实训数据

        Args:
            metadata: 资源元数据
            base_path: 资源基础路径
            db: 数据库会话

        Returns:
            导入结果
        """
        result = {
            'success': True,
            'imported_datasets': 0,
            'imported_records': 0,
            'errors': [],
            'warnings': []
        }

        try:
            # 按执行顺序处理SQL脚本
            sql_scripts = sorted(
                [s for s in metadata.content_resources.sql_scripts if hasattr(s, 'execution_order')],
                key=lambda x: getattr(x, 'execution_order', 0)
            )

            for script in sql_scripts:
                script_result = await self._execute_sql_script(script, base_path, db)
                if not script_result['success']:
                    result['errors'].extend(script_result['errors'])
                    result['success'] = False
                else:
                    result['imported_records'] += script_result.get('records_affected', 0)

            # 处理数据集导入
            for dataset in metadata.content_resources.datasets:
                dataset_result = await self._import_dataset(dataset, base_path, db)
                if dataset_result['success']:
                    result['imported_datasets'] += 1
                    result['imported_records'] += dataset_result.get('records_imported', 0)
                else:
                    result['errors'].extend(dataset_result['errors'])
                    result['success'] = False

        except Exception as e:
            self.logger.error(f"数据导入失败: {e}")
            result['success'] = False
            result['errors'].append(f"导入过程出错: {str(e)}")

        return result

    async def _execute_sql_script(self, script_config: Dict[str, Any], base_path: Path, db: Session) -> Dict[str, Any]:
        """执行SQL脚本"""
        result = {'success': True, 'errors': [], 'records_affected': 0}

        try:
            script_path = base_path / script_config['file_path']
            if not script_path.exists():
                result['success'] = False
                result['errors'].append(f"SQL脚本文件不存在: {script_path}")
                return result

            # 读取SQL脚本
            with open(script_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # 分割多个SQL语句
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

            for statement in statements:
                if statement:
                    try:
                        # 执行SQL语句
                        db.execute(text(statement))
                        # 对于INSERT/UPDATE/DELETE，记录影响的行数
                        if any(keyword in statement.upper() for keyword in ['INSERT', 'UPDATE', 'DELETE']):
                            result['records_affected'] += 1
                    except Exception as e:
                        result['errors'].append(f"SQL执行失败: {statement[:100]}... - {str(e)}")
                        result['success'] = False

            if result['success']:
                db.commit()

        except Exception as e:
            result['success'] = False
            result['errors'].append(f"SQL脚本执行出错: {str(e)}")

        return result

    async def _import_dataset(self, dataset_resource, base_path: Path, db: Session) -> Dict[str, Any]:
        """导入数据集"""
        result = {'success': True, 'errors': [], 'records_imported': 0}

        try:
            # 处理ContentResource对象
            if hasattr(dataset_resource, 'data_source') and dataset_resource.data_source:
                # 有data_source配置，根据类型处理
                data_source = dataset_resource.data_source
                if data_source.type == 'sql':
                    result = await self._import_sql_dataset(dataset_resource, base_path, db)
                elif data_source.type == 'csv':
                    result = await self._import_csv_dataset(dataset_resource, base_path, db)
                elif data_source.type == 'api':
                    result = await self._import_api_dataset(dataset_resource, db)
                else:
                    result['success'] = False
                    result['errors'].append(f"不支持的数据源类型: {data_source.type}")
            else:
                # 没有data_source，默认按SQL文件处理
                result = await self._import_sql_file_dataset(dataset_resource, base_path, db)

        except Exception as e:
            result['success'] = False
            result['errors'].append(f"数据集导入出错: {str(e)}")

        return result

    async def _import_sql_file_dataset(self, dataset_resource, base_path: Path, db: Session) -> Dict[str, Any]:
        """导入SQL文件数据集（ContentResource格式）"""
        result = {'success': True, 'errors': [], 'records_imported': 0}

        try:
            # 获取SQL文件路径
            sql_file = base_path / dataset_resource.path

            if not sql_file.exists():
                result['success'] = False
                result['errors'].append(f"SQL文件不存在: {sql_file}")
                return result

            # 读取SQL文件
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # 执行SQL（这里假设SQL文件包含完整的建表和插入语句）
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

            for statement in statements:
                if statement:
                    try:
                        db.execute(text(statement))
                    except Exception as e:
                        # 忽略重复表创建等非关键错误
                        if 'already exists' not in str(e).lower():
                            result['errors'].append(f"SQL执行失败: {statement[:50]}... - {str(e)}")
                            result['success'] = False

            if result['success']:
                db.commit()

                # 简单的数据行计数（基于INSERT语句数量）
                insert_count = sql_content.upper().count('INSERT INTO')
                result['records_imported'] = max(insert_count, 0)

        except Exception as e:
            result['success'] = False
            result['errors'].append(f"SQL文件数据集导入出错: {str(e)}")

        return result

    async def _import_sql_dataset(self, dataset_resource: ContentResource, base_path: Path, db: Session) -> Dict[str, Any]:
        """导入SQL数据集"""
        result = {'success': True, 'errors': [], 'records_imported': 0}

        try:
            if not dataset_resource.data_source or not dataset_resource.data_source.file_path:
                result['success'] = False
                result['errors'].append("数据源配置不完整，缺少file_path")
                return result

            sql_file = base_path / dataset_resource.data_source.file_path

            if not sql_file.exists():
                result['success'] = False
                result['errors'].append(f"数据文件不存在: {sql_file}")
                return result

            # 读取SQL文件
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # 简单的数据行计数（基于INSERT语句数量）
            insert_count = sql_content.upper().count('INSERT INTO')
            expected_count = dataset_resource.data_source.record_count or 0
            result['records_imported'] = max(insert_count, expected_count)

            # 执行SQL（这里假设SQL文件包含完整的建表和插入语句）
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

            for statement in statements:
                if statement:
                    try:
                        db.execute(text(statement))
                    except Exception as e:
                        # 忽略重复表创建等非关键错误
                        if 'already exists' not in str(e).lower():
                            result['errors'].append(f"SQL执行失败: {statement[:50]}... - {str(e)}")
                            result['success'] = False

            if result['success']:
                db.commit()

        except Exception as e:
            result['success'] = False
            result['errors'].append(f"SQL数据集导入出错: {str(e)}")

        return result

    async def _import_csv_dataset(self, dataset_resource: ContentResource, base_path: Path, db: Session) -> Dict[str, Any]:
        """导入CSV数据集"""
        result = {'success': True, 'errors': [], 'records_imported': 0}

        try:
            if not dataset_resource.data_source or not dataset_resource.data_source.file_path:
                result['success'] = False
                result['errors'].append("数据源配置不完整，缺少file_path")
                return result

            csv_file = base_path / dataset_resource.data_source.file_path

            if not csv_file.exists():
                result['success'] = False
                result['errors'].append(f"CSV文件不存在: {csv_file}")
                return result

            # 读取CSV文件
            df = pd.read_csv(csv_file)

            # 获取表名
            table_name = dataset_resource.data_source.table_name or dataset_resource.name

            # 转换为SQL插入语句
            columns = df.columns.tolist()
            values_list = []

            for _, row in df.iterrows():
                values = []
                for col in columns:
                    value = row[col]
                    if pd.isna(value):
                        values.append('NULL')
                    elif isinstance(value, str):
                        escaped_value = value.replace("'", "''")
                        values.append(f"'{escaped_value}'")
                    else:
                        values.append(str(value))
                values_list.append(f"({', '.join(values)})")

            # 构建INSERT语句
            columns_str = ', '.join(f'`{col}`' for col in columns)
            values_str = ', '.join(values_list)

            insert_sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES {values_str}"

            # 执行插入
            db.execute(text(insert_sql))
            db.commit()

            result['records_imported'] = len(df)

        except Exception as e:
            result['success'] = False
            result['errors'].append(f"CSV数据集导入出错: {str(e)}")

        return result

    async def _import_api_dataset(self, dataset_config: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """从API导入数据集"""
        result = {'success': True, 'errors': [], 'records_imported': 0}

        try:
            data_source = dataset_config['data_source']
            api_url = data_source['url']
            headers = data_source.get('headers', {})

            # 调用API
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            # 处理返回的数据（假设是记录列表）
            if isinstance(data, list):
                table_name = data_source.get('table_name', dataset_config['name'])

                for record in data:
                    # 动态构建INSERT语句
                    columns = list(record.keys())
                    values = []
                    for col in columns:
                        value = record[col]
                        if value is None:
                            values.append('NULL')
                        elif isinstance(value, str):
                            escaped_value = value.replace("'", "''")
                            values.append(f"'{escaped_value}'")
                        else:
                            values.append(str(value))

                    columns_str = ', '.join(f'`{col}`' for col in columns)
                    values_str = ', '.join(values)

                    insert_sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({values_str})"
                    db.execute(text(insert_sql))

                result['records_imported'] = len(data)
                db.commit()

        except Exception as e:
            result['success'] = False
            result['errors'].append(f"API数据集导入出错: {str(e)}")

        return result

    async def validate_data_integrity(self, metadata: ResourceMetadata, db: Session) -> Dict[str, Any]:
        """
        验证数据完整性

        Args:
            metadata: 资源元数据
            db: 数据库会话

        Returns:
            验证结果
        """
        result = {
            'valid': True,
            'checks': [],
            'issues': []
        }

        for dataset in metadata.content_resources.datasets:
            # 确保data_source存在且包含table_name
            if not hasattr(dataset, 'data_source') or not dataset.data_source or not hasattr(dataset.data_source, 'table_name'):
                result['valid'] = False
                result['issues'].append(f"数据集 {dataset.name} 缺少 'data_source' 或 'table_name' 配置，无法验证。")
                continue

            table_name = dataset.data_source.table_name
            expected_count = dataset.data_source.record_count

            try:
                # 检查表是否存在
                # SQLite does not have SHOW TABLES LIKE, use sqlite_master
                if 'sqlite' in self.db_url:
                    table_exists_query = text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                else:
                    table_exists_query = text(f"SHOW TABLES LIKE '{table_name}'")

                table_exists = db.execute(table_exists_query).fetchone()

                if not table_exists:
                    result['valid'] = False
                    result['issues'].append(f"表 '{table_name}' 不存在。")
                    continue

                # 检查记录数量
                if expected_count > 0:
                    count_query = text(f"SELECT COUNT(*) FROM `{table_name}`")
                    actual_record_count = db.execute(count_query).scalar()

                    if actual_record_count != expected_count:
                        result['valid'] = False
                        result['issues'].append(f"表 '{table_name}' 记录数量不匹配: 预期 {expected_count}, 实际 {actual_record_count}。")
                    else:
                        result['checks'].append(f"表 '{table_name}' 记录数量验证通过: {actual_record_count} 条。")

            except Exception as e:
                result['valid'] = False
                result['issues'].append(f"验证表 {table_name} 时出错: {str(e)}")

        return result
