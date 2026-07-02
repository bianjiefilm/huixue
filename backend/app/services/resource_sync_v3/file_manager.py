"""
单一来源事实 - V3.0 文件管理器

负责文件系统的操作，包括文件复制、Markdown链接重写、静态资源管理等。
提供统一的文件处理接口。
"""

import hashlib
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class FileManager:
    """文件管理器

    处理静态文件的复制、存储和管理，以及Markdown内容的链接重写。
    """

    def __init__(self, static_root: Path, base_url: str = "/api/v1/files"):
        """
        初始化文件管理器

        Args:
            static_root: 静态文件根目录
            base_url: 文件访问的基础URL
        """
        self.static_root = Path(static_root)
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

        # 确保目录存在
        self.static_root.mkdir(parents=True, exist_ok=True)

    async def process_file(self, source_path: Path, relative_target_path: str) -> Optional[str]:
        """
        处理单个文件：复制到静态目录并返回访问URL

        Args:
            source_path: 源文件路径
            relative_target_path: 相对目标路径（相对于static_root）

        Returns:
            文件访问URL，如果失败返回None
        """
        try:
            if not source_path.exists():
                self.logger.error(f"源文件不存在: {source_path}")
                return None

            # 构建目标路径
            target_path = self.static_root / relative_target_path
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 复制文件
            shutil.copy2(source_path, target_path)
            self.logger.debug(f"文件已复制: {source_path} -> {target_path}")

            # 生成访问URL
            url = urljoin(self.base_url + "/", relative_target_path)

            return url

        except Exception as e:
            self.logger.error(f"处理文件失败 {source_path}: {e}")
            return None

    async def process_markdown_with_links(
        self,
        markdown_path: Path,
        resource_base_path: Path,
        resource_id: str,
        resource_type: str
    ) -> Optional[str]:
        """
        处理Markdown文件，重写其中的相对链接

        Args:
            markdown_path: Markdown文件路径
            resource_base_path: 资源基础路径
            resource_id: 资源ID
            resource_type: 资源类型

        Returns:
            处理后的Markdown内容，如果失败返回None
        """
        try:
            if not markdown_path.exists():
                self.logger.error(f"Markdown文件不存在: {markdown_path}")
                return None

            # 读取原始内容
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 复制Markdown文件到静态目录
            relative_path = f"{resource_type}s/{resource_id}/handbook.md"
            markdown_url = await self.process_file(markdown_path, relative_path)

            if not markdown_url:
                return None

            # 构建资源映射表
            resource_mappings = await self._build_resource_mappings(
                resource_base_path, resource_id, resource_type
            )

            # 重写链接
            rewriter = MarkdownLinkRewriter(self.base_url)
            rewritten_content = rewriter.rewrite_links(content, resource_mappings)

            # 保存重写后的内容
            rewritten_path = self.static_root / relative_path
            with open(rewritten_path, 'w', encoding='utf-8') as f:
                f.write(rewritten_content)

            self.logger.debug(f"Markdown链接重写完成: {markdown_path}")

            return markdown_url

        except Exception as e:
            self.logger.error(f"处理Markdown文件失败 {markdown_path}: {e}")
            return None

    async def _build_resource_mappings(
        self,
        resource_base_path: Path,
        resource_id: str,
        resource_type: str
    ) -> Dict[str, str]:
        """
        构建资源路径映射表

        Args:
            resource_base_path: 资源基础路径
            resource_id: 资源ID
            resource_type: 资源类型

        Returns:
            相对路径 -> 访问URL的映射字典
        """
        mappings = {}

        # 常见的资源目录
        resource_dirs = ['assets', 'datasets', 'images', 'files']

        for dir_name in resource_dirs:
            dir_path = resource_base_path / dir_name
            if dir_path.exists():
                for file_path in dir_path.rglob('*'):
                    if file_path.is_file():
                        # 计算相对路径
                        try:
                            relative_path = file_path.relative_to(resource_base_path)
                            # 构建静态文件路径
                            static_relative_path = f"{resource_type}s/{resource_id}/{relative_path}"
                            # 生成URL
                            url = urljoin(self.base_url + "/", static_relative_path)
                            # 添加到映射表
                            mappings[str(relative_path)] = url
                        except ValueError:
                            # 如果无法计算相对路径，跳过
                            continue

        return mappings

    async def cleanup_resource_files(self, resource_id: str):
        """
        清理资源的静态文件

        Args:
            resource_id: 资源ID
        """
        try:
            # 查找并删除资源相关的所有文件
            resource_patterns = [
                f"trainings/{resource_id}/**/*",
                f"practices/{resource_id}/**/*"
            ]

            for pattern in resource_patterns:
                for file_path in self.static_root.glob(pattern):
                    if file_path.is_file():
                        file_path.unlink()
                        self.logger.debug(f"删除文件: {file_path}")
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                        self.logger.debug(f"删除目录: {file_path}")

        except Exception as e:
            self.logger.error(f"清理资源文件失败 {resource_id}: {e}")

    def calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """
        计算文件哈希值

        Args:
            file_path: 文件路径

        Returns:
            文件的SHA256哈希值
        """
        try:
            if not file_path.exists():
                return None

            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)

            return hash_sha256.hexdigest()

        except Exception as e:
            self.logger.error(f"计算文件哈希失败 {file_path}: {e}")
            return None

    async def get_file_info(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            文件信息字典
        """
        try:
            if not file_path.exists():
                return None

            stat = file_path.stat()
            return {
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'hash': self.calculate_file_hash(file_path),
                'exists': True
            }

        except Exception as e:
            self.logger.error(f"获取文件信息失败 {file_path}: {e}")
            return None

    def ensure_directory_structure(self):
        """确保目录结构存在"""
        dirs_to_create = [
            self.static_root / "trainings",
            self.static_root / "practices",
            self.static_root / "temp"
        ]

        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)


class MarkdownLinkRewriter:
    """Markdown链接重写器"""

    def __init__(self, base_url: str):
        """
        初始化重写器

        Args:
            base_url: 基础URL
        """
        self.base_url = base_url

    def rewrite_links(self, markdown_content: str, resource_mappings: Dict[str, str]) -> str:
        """
        重写Markdown内容中的相对链接

        Args:
            markdown_content: 原始Markdown内容
            resource_mappings: 相对路径 -> 绝对URL的映射

        Returns:
            重写后的Markdown内容
        """
        import re

        def replace_link(match):
            link_text = match.group(1)
            link_url = match.group(2)

            # 检查是否是相对路径且在映射中
            if not link_url.startswith(('http://', 'https://', 'mailto:', '#', 'mailto:')):
                # 清理链接URL（移除开头的./或/）
                clean_url = link_url.lstrip('./')

                # 直接路径匹配
                if clean_url in resource_mappings:
                    return f'[{link_text}]({resource_mappings[clean_url]})'

                # 尝试 assets/ 开头的路径
                if clean_url.startswith('assets/') and clean_url in resource_mappings:
                    return f'[{link_text}]({resource_mappings[clean_url]})'

                # 尝试文件名匹配
                file_name = Path(clean_url).name
                for mapped_path, url in resource_mappings.items():
                    if Path(mapped_path).name == file_name:
                        return f'[{link_text}]({url})'

            return match.group(0)  # 返回原始匹配

        # 匹配Markdown链接的正则表达式
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        rewritten_content = re.sub(link_pattern, replace_link, markdown_content)

        return rewritten_content

    def extract_links(self, markdown_content: str) -> List[str]:
        """
        提取Markdown内容中的所有链接

        Args:
            markdown_content: Markdown内容

        Returns:
            链接URL列表
        """
        import re

        links = []
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'

        for match in re.finditer(link_pattern, markdown_content):
            link_url = match.group(2)
            links.append(link_url)

        return links




