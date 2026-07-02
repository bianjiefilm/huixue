#!/usr/bin/env python3
"""
对象存储服务
使用本地ziyuan目录作为对象存储路径
"""

import os
import shutil
import hashlib
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ObjectStorage:
    """本地对象存储服务，基于ziyuan目录"""
    
    def __init__(self, base_path: str = None):
        # 默认使用项目根目录下的ziyuan文件夹
        if base_path is None:
            current_dir = Path(__file__).parent.parent.parent  # 回到project root
            base_path = current_dir / "ziyuan"
        
        self.base_path = Path(base_path)
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保必要的目录结构存在"""
        # 注意：不再预创建实训项目的子目录结构
        # 实训项目应该直接在ziyuan/实训资源/下，每个项目一个独立目录
        # 包含自己的配置文件和资源文件
        logger.info("对象存储初始化完成，不预创建目录结构")
    
    def save_file(self, file_content: bytes, filename: str,
                  category: str = "templates", training_id: Optional[int] = None) -> Dict[str, Any]:
        """
        保存文件到对象存储

        Args:
            file_content: 文件内容（字节）
            filename: 原始文件名
            category: 文件分类（templates, datasets, notebooks, assets）
            training_id: 实训ID（可选）

        Returns:
            包含文件信息的字典
        """
        try:
            # 生成唯一的文件ID
            file_id = str(uuid.uuid4())

            # 计算文件哈希
            file_hash = hashlib.md5(file_content).hexdigest()

            # 获取文件扩展名
            file_extension = Path(filename).suffix.lower()

            # 构建存储路径 - 直接保存到实训资源项目的对应目录中
            if training_id:
                storage_dir = self.base_path / "实训资源" / f"training_{training_id}" / category
            else:
                # 如果没有指定training_id，使用临时存储目录
                storage_dir = self.base_path / "temp" / category

            storage_dir.mkdir(parents=True, exist_ok=True)

            # 生成存储文件名：timestamp_uuid_original_name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stored_filename = f"{timestamp}_{file_id}_{filename}"
            file_path = storage_dir / stored_filename

            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_content)

            # 生成访问URL
            relative_path = file_path.relative_to(self.base_path)
            access_url = f"/api/v1/storage/{relative_path}"

            file_info = {
                "file_id": file_id,
                "original_filename": filename,
                "stored_filename": stored_filename,
                "file_path": str(file_path),
                "relative_path": str(relative_path),
                "access_url": access_url,
                "file_size": len(file_content),
                "file_hash": file_hash,
                "file_extension": file_extension,
                "category": category,
                "training_id": training_id,
                "created_at": datetime.now().isoformat()
            }

            logger.info(f"文件保存成功: {filename} -> {stored_filename}")
            return file_info

        except Exception as e:
            logger.error(f"保存文件失败: {filename}, 错误: {str(e)}")
            raise Exception(f"文件保存失败: {str(e)}")
    
    def save_training_files(self, parsed_files: Dict[str, Any], training_id: int) -> Dict[str, Any]:
        """
        批量保存实训相关文件

        慧学平台的实训项目配置结构（JSON字符串）。遵循如下规范：
        1. 直接在ziyuan/实训资源/下有独立的目录
        2. 目录中直接包含配置文件和资源文件
        3. 不需要额外的子目录结构

        Args:
            parsed_files: 解析后的文件数据
            training_id: 实训ID

        Returns:
            保存结果统计
        """
        saved_files = {
            "bi_templates": [],
            "ai_templates": [],
            "assets": [],
            "total_count": 0,
            "total_size": 0
        }

        try:
            # 获取实训项目目录
            training_dir = self.base_path / "实训资源" / f"training_{training_id}"

            for form_field_name, file_info in parsed_files.items():
                file_type = file_info.get('type')
                filename = file_info.get('filename')
                content = file_info.get('content')

                # 跳过文本文件（SQL和Jupyter，这些直接存数据库）
                if file_type in ['sql_schema', 'sql_data', 'jupyter_notebook']:
                    continue

                # 确保content是字节类型
                if isinstance(content, str):
                    content = content.encode('utf-8')

                # 根据文件类型确定存储位置和分类
                if file_type == 'bi_template':
                    # BI模板文件直接保存到export/app-bi目录
                    storage_list = saved_files["bi_templates"]
                    file_path = training_dir / "export" / "app-bi" / filename
                elif file_type == 'ai_template':
                    # AI模板文件直接保存到export/app-ai目录
                    storage_list = saved_files["ai_templates"]
                    file_path = training_dir / "export" / "app-ai" / filename
                elif file_type == 'supporting_asset':
                    # 支持性素材保存到assets目录
                    storage_list = saved_files["assets"]
                    file_path = training_dir / "assets" / filename
                else:
                    logger.warning(f"未知文件类型: {file_type}, 跳过文件: {filename}")
                    continue

                # 创建目录
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # 保存文件
                with open(file_path, 'wb') as f:
                    f.write(content)

                file_size = len(content)
                file_info_result = {
                    "original_filename": filename,
                    "file_path": str(file_path),
                    "relative_path": str(file_path.relative_to(self.base_path)),
                    "file_size": file_size,
                    "file_extension": Path(filename).suffix.lower()
                }

                storage_list.append(file_info_result)
                saved_files["total_count"] += 1
                saved_files["total_size"] += file_size

            logger.info(f"实训文件批量保存完成: training_id={training_id}, 总数={saved_files['total_count']}")
            return saved_files

        except Exception as e:
            logger.error(f"批量保存实训文件失败: training_id={training_id}, 错误: {str(e)}")
            raise
    
    def get_file(self, relative_path: str) -> Optional[bytes]:
        """
        获取文件内容
        
        Args:
            relative_path: 相对路径
            
        Returns:
            文件内容（字节）或None
        """
        try:
            file_path = self.base_path / relative_path
            
            if not file_path.exists():
                logger.warning(f"文件不存在: {file_path}")
                return None
            
            with open(file_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"读取文件失败: {relative_path}, 错误: {str(e)}")
            return None
    
    def delete_file(self, relative_path: str) -> bool:
        """
        删除文件
        
        Args:
            relative_path: 相对路径
            
        Returns:
            删除是否成功
        """
        try:
            file_path = self.base_path / relative_path
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"文件删除成功: {relative_path}")
                return True
            else:
                logger.warning(f"文件不存在，无需删除: {relative_path}")
                return True
                
        except Exception as e:
            logger.error(f"删除文件失败: {relative_path}, 错误: {str(e)}")
            return False
    
    def list_training_files(self, training_id: int) -> Dict[str, Any]:
        """
        列出特定实训的所有文件

        注意：现在实训项目直接在ziyuan/实训资源/training_{training_id}/目录下

        Args:
            training_id: 实训ID

        Returns:
            文件列表
        """
        try:
            training_dir = self.base_path / "实训资源" / f"training_{training_id}"

            if not training_dir.exists():
                return {"files": [], "total_count": 0, "total_size": 0}

            files = []
            total_size = 0

            for file_path in training_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    relative_path = file_path.relative_to(self.base_path)
                    file_size = file_path.stat().st_size

                    files.append({
                        "filename": file_path.name,
                        "relative_path": str(relative_path),
                        "access_url": f"/api/v1/storage/{relative_path}",
                        "file_size": file_size,
                        "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })

                    total_size += file_size

            return {
                "files": files,
                "total_count": len(files),
                "total_size": total_size
            }

        except Exception as e:
            logger.error(f"列出实训文件失败: training_id={training_id}, 错误: {str(e)}")
            return {"files": [], "total_count": 0, "total_size": 0}
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            stats = {
                "categories": {
                    "课程资源": {"file_count": 0, "total_size": 0},
                    "实训资源": {"file_count": 0, "total_size": 0}
                },
                "total_files": 0,
                "total_size": 0
            }

            # 统计课程资源
            course_dir = self.base_path / "课程资源"
            if course_dir.exists():
                files = list(course_dir.rglob("*"))
                file_count = len([f for f in files if f.is_file()])
                total_size = sum(f.stat().st_size for f in files if f.is_file())

                stats["categories"]["课程资源"] = {
                    "file_count": file_count,
                    "total_size": total_size
                }
                stats["total_files"] += file_count
                stats["total_size"] += total_size

            # 统计实训资源
            training_dir = self.base_path / "实训资源"
            if training_dir.exists():
                files = list(training_dir.rglob("*"))
                file_count = len([f for f in files if f.is_file()])
                total_size = sum(f.stat().st_size for f in files if f.is_file())

                stats["categories"]["实训资源"] = {
                    "file_count": file_count,
                    "total_size": total_size
                }
                stats["total_files"] += file_count
                stats["total_size"] += total_size

            return stats

        except Exception as e:
            logger.error(f"获取存储统计失败: {str(e)}")
            return {"categories": {}, "total_files": 0, "total_size": 0}

# 全局对象存储实例
object_storage = ObjectStorage() 