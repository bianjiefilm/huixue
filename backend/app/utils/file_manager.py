#!/usr/bin/env python3
"""
轻量级文件管理器
提供安全、可监控、可审计的文件操作统一接口
"""

import os
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class FileManager:
    """轻量级文件管理器，提供安全、监控、可审计的文件操作"""

    # 配置参数
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_TOTAL_SIZE_PER_USER = 50 * 1024 * 1024 * 1024  # 50GB
    ALLOWED_BASE_DIRS = {
        'classroom_disk': '课堂云盘',
        'training_dataset': '实训资源',
        'homework_submission': '作业提交',
        'teaching_resource': '教学资源'
    }

    def __init__(self, base_path: str = "ziyuan"):
        self.base_path = Path(base_path)

    def validate_path_safety(self, operation: str, entity_id: int, sub_path: str = "") -> Path:
        """验证路径安全性，返回安全的完整路径"""
        if operation not in self.ALLOWED_BASE_DIRS:
            raise ValueError(f"不支持的操作类型: {operation}")

        # 强制转换entity_id为整数，防止路径遍历
        try:
            safe_id = int(entity_id)
        except (ValueError, TypeError):
            raise ValueError(f"无效的实体ID: {entity_id}")

        # 构建安全路径
        base_dir = self.base_path / self.ALLOWED_BASE_DIRS[operation]
        if sub_path:
            # 安全化子路径，移除危险字符
            safe_sub_path = self._sanitize_path(sub_path)
            full_path = base_dir / f"{operation}_{safe_id}" / safe_sub_path
        else:
            full_path = base_dir / f"{operation}_{safe_id}"

        return full_path

    def _sanitize_path(self, path: str) -> str:
        """路径安全过滤"""
        import re
        # 移除危险字符，只保留字母数字和安全符号
        safe_path = re.sub(r'[^\w\-_\./]', '', path)
        # 防止路径遍历
        safe_path = safe_path.replace('..', '').replace('//', '/')
        # 限制长度
        return safe_path[:200] if len(safe_path) > 200 else safe_path

    def check_quota(self, user_id: int, file_size: int, operation: str) -> bool:
        """检查存储配额"""
        # 计算用户总使用量
        user_usage = self._calculate_user_usage(user_id)
        if user_usage + file_size > self.MAX_TOTAL_SIZE_PER_USER:
            return False

        # 检查单文件大小
        if file_size > self.MAX_FILE_SIZE:
            return False

        return True

    def _calculate_user_usage(self, user_id: int) -> int:
        """计算用户存储使用量（简化实现）"""
        # TODO: 这里应该从数据库查询用户存储使用量
        # 暂时返回0，实际实现需要查询相关表的file_size总和
        return 0

    @contextmanager
    def safe_file_operation(self, operation: str, entity_id: int, sub_path: str = ""):
        """安全的文件操作上下文管理器"""
        full_path = self.validate_path_safety(operation, entity_id, sub_path)

        try:
            yield full_path
            # 记录成功操作
            logger.info(f"文件操作成功: {operation} {entity_id} {sub_path}")
        except Exception as e:
            logger.error(f"文件操作失败: {operation} {entity_id} {sub_path}, 错误: {str(e)}")
            raise

    def create_directory(self, operation: str, entity_id: int, sub_path: str = "") -> Path:
        """安全创建目录"""
        with self.safe_file_operation(operation, entity_id, sub_path) as path:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"目录创建成功: {path}")
            return path

    def save_file(self, operation: str, entity_id: int, file_content: bytes,
                 filename: str, user_id: int, sub_path: str = "") -> Dict[str, Any]:
        """安全保存文件"""
        # 检查配额
        if not self.check_quota(user_id, len(file_content), operation):
            raise ValueError("存储配额不足或文件过大")

        # 安全化文件名
        safe_filename = self._sanitize_path(filename)

        with self.safe_file_operation(operation, entity_id, sub_path) as dir_path:
            file_path = dir_path / safe_filename

            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_content)

            result = {
                'file_path': str(file_path),
                'relative_path': str(file_path.relative_to(self.base_path)),
                'file_size': len(file_content),
                'filename': safe_filename
            }

            logger.info(f"文件保存成功: {file_path}, 大小: {len(file_content)} bytes")
            return result

    def delete_entity_files(self, operation: str, entity_id: int) -> bool:
        """删除实体所有相关文件（带回收站机制）"""
        try:
            full_path = self.validate_path_safety(operation, entity_id)

            if full_path.exists():
                # 移动到回收站
                trash_path = self._move_to_trash(full_path)
                logger.info(f"文件移动到回收站: {full_path} -> {trash_path}")

                # 记录清理任务（可以后续实现定时清理）
                self._schedule_cleanup(trash_path, entity_id)

            return True
        except Exception as e:
            logger.error(f"删除实体文件失败: {operation} {entity_id}, 错误: {str(e)}")
            return False

    def _move_to_trash(self, source_path: Path) -> Path:
        """移动到回收站"""
        trash_dir = self.base_path / "trash"
        trash_dir.mkdir(exist_ok=True)

        timestamp = int(time.time())
        trash_name = f"{source_path.name}_{timestamp}"
        trash_path = trash_dir / trash_name

        shutil.move(str(source_path), str(trash_path))
        return trash_path

    def _schedule_cleanup(self, trash_path: Path, entity_id: int):
        """记录清理任务（简化实现）"""
        # 这里可以写入数据库或文件，记录待清理的项目
        cleanup_record = {
            'trash_path': str(trash_path),
            'entity_id': entity_id,
            'created_at': time.time()
        }
        # 实际实现中应该持久化存储
        logger.info(f"记录清理任务: {cleanup_record}")

    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储使用统计"""
        try:
            stats = {
                "categories": {},
                "total_files": 0,
                "total_size": 0,
                "quotas": {
                    "max_file_size": self.MAX_FILE_SIZE,
                    "max_user_total": self.MAX_TOTAL_SIZE_PER_USER
                }
            }

            # 统计各个类别的存储使用
            for category_key, category_name in self.ALLOWED_BASE_DIRS.items():
                category_dir = self.base_path / category_name

                if category_dir.exists():
                    files = list(category_dir.rglob("*"))
                    file_count = len([f for f in files if f.is_file()])
                    total_size = sum(f.stat().st_size for f in files if f.is_file())

                    stats["categories"][category_key] = {
                        "file_count": file_count,
                        "total_size": total_size,
                        "total_size_mb": round(total_size / (1024 * 1024), 2)
                    }

                    stats["total_files"] += file_count
                    stats["total_size"] += total_size

            stats["total_size_mb"] = round(stats["total_size"] / (1024 * 1024), 2)
            return stats

        except Exception as e:
            logger.error(f"获取存储统计失败: {str(e)}")
            return {"error": str(e)}

# 全局文件管理器实例
file_manager = FileManager()

