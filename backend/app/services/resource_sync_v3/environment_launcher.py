"""
单一来源事实 - V3.0 环境启动器

负责在启动容器时自动注入ziyuan中的资源，实现数据同步缺口的解决方案。
支持SQL脚本导入、仪表盘模板加载等功能。
"""

import asyncio
import httpx
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from .models import ResourceType
from app.models.models import TrainingAsset
from app.core.config import settings

logger = logging.getLogger(__name__)


class EnvironmentLauncher:
    """环境启动器

    在启动容器时自动注入ziyuan中定义的资源，实现：
    1. SQL脚本自动导入
    2. 仪表盘模板自动加载
    3. 数据集文件自动挂载
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def prepare_environment_resources(
        self,
        training_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        准备环境启动资源

        Args:
            training_id: 实训ID
            db: 数据库会话

        Returns:
            环境启动配置字典
        """
        self.logger.info(f"准备实训 {training_id} 的环境资源")

        # 查询实训的资源配置
        training_assets = db.query(TrainingAsset).filter(
            TrainingAsset.training_id == training_id
        ).all()

        # 按类型组织资源
        resources = {
            'sql_scripts': [],
            'bi_templates': [],
            'datasets': []
        }

        for asset in training_assets:
            asset_info = {
                'name': asset.name,
                'url': asset.relative_path,  # 使用相对路径，容器内会解析为完整URL
                'type': asset.asset_type,
                'file_type': asset.file_type
            }

            if asset.asset_type == 'sql_script':
                resources['sql_scripts'].append(asset_info)
            elif asset.asset_type == 'bi_template':
                resources['bi_templates'].append(asset_info)
            elif asset.asset_type in ['dataset', 'csv', 'excel']:
                resources['datasets'].append(asset_info)

        # 生成环境变量
        env_vars = self._generate_environment_variables(resources)

        # 生成初始化配置
        init_config = {
            'training_id': training_id,
            'resources': resources,
            'env_vars': env_vars,
            'init_script_url': self._get_init_script_url()
        }

        self.logger.info(f"实训 {training_id} 资源准备完成: {len(training_assets)} 个资源文件")
        return init_config

    def _generate_environment_variables(self, resources: Dict[str, List[Dict[str, Any]]]) -> Dict[str, str]:
        """
        生成容器环境变量

        Args:
            resources: 资源配置

        Returns:
            环境变量字典
        """
        env_vars = {}

        # SQL脚本URL列表
        if resources['sql_scripts']:
            sql_urls = [script['url'] for script in resources['sql_scripts']]
            env_vars['SQL_SCRIPT_URLS'] = json.dumps(sql_urls)

        # BI模板URL
        if resources['bi_templates']:
            # 目前只支持一个仪表盘模板
            template_url = resources['bi_templates'][0]['url']
            env_vars['DASHBOARD_TEMPLATE_URL'] = template_url

        # 数据集URL列表
        if resources['datasets']:
            dataset_urls = [dataset['url'] for dataset in resources['datasets']]
            env_vars['DATASET_URLS'] = json.dumps(dataset_urls)

        # 资源基础URL
        env_vars['RESOURCE_BASE_URL'] = f"{settings.API_BASE_URL}/api/v1/files/trainings"

        return env_vars

    def _get_init_script_url(self) -> str:
        """获取初始化脚本URL"""
        # 这个脚本应该放在静态文件中，由容器启动时下载执行
        return f"{settings.API_BASE_URL}/api/v1/files/init-environment.sh"

    async def inject_resources_into_container(
        self,
        container_id: str,
        init_config: Dict[str, Any],
        container_host: str = "localhost",
        container_port: Optional[int] = None
    ) -> bool:
        """
        向运行中的容器注入资源

        Args:
            container_id: 容器ID
            init_config: 初始化配置
            container_host: 容器主机
            container_port: 容器端口

        Returns:
            注入是否成功
        """
        try:
            self.logger.info(f"向容器 {container_id} 注入资源")

            # 等待容器完全启动
            await self._wait_for_container_ready(container_host, container_port)

            # 执行资源注入
            success = await self._execute_resource_injection(
                container_host, container_port, init_config
            )

            if success:
                self.logger.info(f"容器 {container_id} 资源注入成功")
            else:
                self.logger.error(f"容器 {container_id} 资源注入失败")

            return success

        except Exception as e:
            self.logger.error(f"容器资源注入失败 {container_id}: {e}")
            return False

    async def _wait_for_container_ready(self, host: str, port: Optional[int], timeout: int = 60) -> bool:
        """
        等待容器就绪

        Args:
            host: 容器主机
            port: 容器端口
            timeout: 超时时间（秒）

        Returns:
            容器是否就绪
        """
        if not port:
            return True  # 如果没有端口，认为容器已就绪

        import asyncio

        for i in range(timeout):
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(f"http://{host}:{port}/health")
                    if response.status_code == 200:
                        self.logger.info(f"容器在 {host}:{port} 已就绪")
                        return True
            except Exception:
                pass

            if i % 10 == 0:  # 每10秒记录一次日志
                self.logger.debug(f"等待容器就绪: {host}:{port} ({i}/{timeout})")

            await asyncio.sleep(1)

        self.logger.warning(f"容器 {host}:{port} 在 {timeout} 秒内未就绪")
        return False

    async def _execute_resource_injection(
        self,
        host: str,
        port: int,
        init_config: Dict[str, Any]
    ) -> bool:
        """
        执行资源注入逻辑

        Args:
            host: 容器主机
            port: 容器端口
            init_config: 初始化配置

        Returns:
            注入是否成功
        """
        try:
            # 步骤1: 下载并执行SQL脚本（如果有）
            if init_config['env_vars'].get('SQL_SCRIPT_URLS'):
                await self._inject_sql_scripts(host, port, init_config)

            # 步骤2: 导入仪表盘模板（如果有）
            if init_config['env_vars'].get('DASHBOARD_TEMPLATE_URL'):
                await self._inject_dashboard_template(host, port, init_config)

            # 步骤3: 下载数据集文件（如果有）
            if init_config['env_vars'].get('DATASET_URLS'):
                await self._inject_datasets(host, port, init_config)

            return True

        except Exception as e:
            self.logger.error(f"资源注入执行失败: {e}")
            return False

    async def _inject_sql_scripts(self, host: str, port: int, init_config: Dict[str, Any]):
        """注入SQL脚本"""
        sql_urls = json.loads(init_config['env_vars']['SQL_SCRIPT_URLS'])
        base_url = init_config['env_vars']['RESOURCE_BASE_URL']

        for sql_url in sql_urls:
            try:
                # 构建完整的SQL文件URL
                full_sql_url = f"{base_url}/{sql_url}"

                # 下载SQL文件
                async with httpx.AsyncClient() as client:
                    response = await client.get(full_sql_url)
                    if response.status_code != 200:
                        self.logger.error(f"下载SQL文件失败: {full_sql_url}")
                        continue

                    sql_content = response.text

                # 执行SQL脚本（针对不同环境类型）
                env_type = init_config.get('env_type', 'HUIXUE_BI')
                if env_type == 'HUIXUE_BI':
                    await self._execute_superset_sql(host, port, sql_content)
                elif env_type == 'JUPYTER':
                    await self._execute_jupyter_sql(host, port, sql_content)

                self.logger.info(f"SQL脚本注入成功: {sql_url}")

            except Exception as e:
                self.logger.error(f"SQL脚本注入失败 {sql_url}: {e}")

    async def _execute_superset_sql(self, host: str, port: int, sql_content: str):
        """在Superset环境中执行SQL"""
        # 这里需要实现Superset的SQL执行逻辑
        # 可以通过Superset API执行SQL

        # 临时实现：记录SQL内容，实际应该通过API执行
        self.logger.info(f"准备在Superset中执行SQL: {len(sql_content)} 字符")

        # TODO: 实现Superset SQL执行
        pass

    async def _execute_jupyter_sql(self, host: str, port: int, sql_content: str):
        """在Jupyter环境中执行SQL"""
        # 在Jupyter环境中，可能需要连接到数据库执行SQL

        # 临时实现：记录SQL内容
        self.logger.info(f"准备在Jupyter中执行SQL: {len(sql_content)} 字符")

        # TODO: 实现Jupyter SQL执行
        pass

    async def _inject_dashboard_template(self, host: str, port: int, init_config: Dict[str, Any]):
        """注入仪表盘模板"""
        template_url = init_config['env_vars']['DASHBOARD_TEMPLATE_URL']
        base_url = init_config['env_vars']['RESOURCE_BASE_URL']

        try:
            # 构建完整的模板文件URL
            full_template_url = f"{base_url}/{template_url}"

            # 下载模板文件
            async with httpx.AsyncClient() as client:
                response = await client.get(full_template_url)
                if response.status_code != 200:
                    self.logger.error(f"下载仪表盘模板失败: {full_template_url}")
                    return

                template_content = response.content

            # 导入仪表盘
            env_type = init_config.get('env_type', 'HUIXUE_BI')
            if env_type == 'HUIXUE_BI':
                await self._import_superset_dashboard(host, port, template_content)

            self.logger.info(f"仪表盘模板注入成功: {template_url}")

        except Exception as e:
            self.logger.error(f"仪表盘模板注入失败 {template_url}: {e}")

    async def _import_superset_dashboard(self, host: str, port: int, template_content: bytes):
        """导入Superset仪表盘"""
        # 这里需要实现Superset仪表盘导入逻辑

        # 临时实现：记录模板大小
        self.logger.info(f"准备导入Superset仪表盘: {len(template_content)} 字节")

        # TODO: 实现Superset仪表盘导入
        pass

    async def _inject_datasets(self, host: str, port: int, init_config: Dict[str, Any]):
        """注入数据集文件"""
        dataset_urls = json.loads(init_config['env_vars']['DATASET_URLS'])
        base_url = init_config['env_vars']['RESOURCE_BASE_URL']

        for dataset_url in dataset_urls:
            try:
                # 构建完整的数据集文件URL
                full_dataset_url = f"{base_url}/{dataset_url}"

                # 下载数据集文件到容器的工作目录
                async with httpx.AsyncClient() as client:
                    response = await client.get(full_dataset_url)
                    if response.status_code != 200:
                        self.logger.error(f"下载数据集文件失败: {full_dataset_url}")
                        continue

                    dataset_content = response.content

                # 保存到容器的工作目录
                await self._save_file_to_container(host, port, dataset_url, dataset_content)

                self.logger.info(f"数据集文件注入成功: {dataset_url}")

            except Exception as e:
                self.logger.error(f"数据集文件注入失败 {dataset_url}: {e}")

    async def _save_file_to_container(self, host: str, port: int, file_path: str, content: bytes):
        """保存文件到容器"""
        # 这里需要实现文件保存到容器的逻辑
        # 可以通过容器的文件系统API或挂载目录实现

        # 临时实现：记录文件信息
        self.logger.info(f"准备保存文件到容器: {file_path} ({len(content)} 字节)")

        # TODO: 实现容器文件保存
        pass

    async def generate_init_script(self, env_type: str) -> str:
        """
        生成容器初始化脚本

        Args:
            env_type: 环境类型

        Returns:
            初始化脚本内容
        """
        if env_type == 'HUIXUE_BI':
            return self._generate_superset_init_script()
        elif env_type == 'JUPYTER':
            return self._generate_jupyter_init_script()
        else:
            return self._generate_generic_init_script()

    def _generate_superset_init_script(self) -> str:
        """生成Superset初始化脚本"""
        return """#!/bin/bash
set -e

echo "开始Superset环境初始化..."

# 等待Superset启动
echo "等待Superset服务启动..."
while ! curl -f http://localhost:8088/health > /dev/null 2>&1; do
    echo "等待Superset..."
    sleep 5
done

echo "Superset服务已启动"

# 执行SQL脚本导入
if [ -n "$SQL_SCRIPT_URLS" ]; then
    echo "开始导入SQL脚本..."
    # 下载并执行SQL脚本
    for sql_url in $(echo $SQL_SCRIPT_URLS | jq -r '.[]'); do
        echo "下载SQL脚本: $RESOURCE_BASE_URL/$sql_url"
        curl -o /tmp/script.sql "$RESOURCE_BASE_URL/$sql_url"
        # 执行SQL脚本到Superset数据库
        # 这里需要具体的Superset数据库连接信息
        echo "执行SQL脚本: /tmp/script.sql"
    done
fi

# 导入仪表盘模板
if [ -n "$DASHBOARD_TEMPLATE_URL" ]; then
    echo "开始导入仪表盘模板..."
    echo "下载仪表盘模板: $RESOURCE_BASE_URL/$DASHBOARD_TEMPLATE_URL"
    curl -o /tmp/dashboard.zip "$RESOURCE_BASE_URL/$DASHBOARD_TEMPLATE_URL"
    # 导入仪表盘到Superset
    echo "导入仪表盘模板: /tmp/dashboard.zip"
fi

# 下载数据集文件
if [ -n "$DATASET_URLS" ]; then
    echo "开始下载数据集文件..."
    mkdir -p /work/datasets
    for dataset_url in $(echo $DATASET_URLS | jq -r '.[]'); do
        echo "下载数据集: $RESOURCE_BASE_URL/$dataset_url"
        curl -o "/work/datasets/$(basename $dataset_url)" "$RESOURCE_BASE_URL/$dataset_url"
    done
fi

echo "Superset环境初始化完成"
"""

    def _generate_jupyter_init_script(self) -> str:
        """生成Jupyter初始化脚本"""
        return """#!/bin/bash
set -e

echo "开始Jupyter环境初始化..."

# 等待Jupyter启动
echo "等待Jupyter服务启动..."
while ! curl -f http://localhost:8888/tree > /dev/null 2>&1; do
    echo "等待Jupyter..."
    sleep 5
done

echo "Jupyter服务已启动"

# 下载数据集文件
if [ -n "$DATASET_URLS" ]; then
    echo "开始下载数据集文件..."
    mkdir -p /work/datasets
    for dataset_url in $(echo $DATASET_URLS | jq -r '.[]'); do
        echo "下载数据集: $RESOURCE_BASE_URL/$dataset_url"
        curl -o "/work/datasets/$(basename $dataset_url)" "$RESOURCE_BASE_URL/$dataset_url"
    done
fi

# 执行SQL脚本（如果需要）
if [ -n "$SQL_SCRIPT_URLS" ]; then
    echo "SQL脚本已准备就绪，可在Jupyter中执行"
fi

echo "Jupyter环境初始化完成"
"""

    def _generate_generic_init_script(self) -> str:
        """生成通用初始化脚本"""
        return """#!/bin/bash
set -e

echo "开始通用环境初始化..."

# 下载所有资源文件
if [ -n "$DATASET_URLS" ]; then
    echo "下载数据集文件..."
    mkdir -p /work/datasets
    for dataset_url in $(echo $DATASET_URLS | jq -r '.[]'); do
        curl -o "/work/datasets/$(basename $dataset_url)" "$RESOURCE_BASE_URL/$dataset_url"
    done
fi

echo "环境初始化完成"
"""
