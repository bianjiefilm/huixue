#!/usr/bin/env python3
"""
实训包处理器
负责处理实训资源的多文件上传、AI生成和数据库持久化
"""

import os
import json
import logging
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.utils.file_parser import FileParser
from app.utils.llm_client import LLMClient
from app.utils.task_manager import task_manager, TaskStatus
from app.schemas.generation import (
    FullTrainingManifest, TrainingMetadata, FullTrainingPackageResponse,
    ExtendedTrainingTaskResult, TrainingDatabasePersistResult
)

logger = logging.getLogger(__name__)

class TrainingPackageProcessor:
    """实训包处理器"""
    
    def __init__(self):
        self.llm_client = LLMClient()
    
    def process_full_training_package_async(self, task_id: str, manifest: FullTrainingManifest, 
                                          file_data: Dict[str, bytes], user_id: int):
        """
        异步处理完整实训包生成任务
        
        Args:
            task_id: 任务ID
            manifest: 实训清单
            file_data: 文件数据字典
            user_id: 用户ID
        """
        
        def worker():
            try:
                logger.info(f"开始处理实训包生成任务: {task_id}")
                task_manager.update_task(task_id, TaskStatus.PROCESSING, progress=10)
                
                # 第一步：解析文件内容
                logger.info("步骤1: 解析上传文件")
                parsed_files = {}
                sql_content = ""
                
                for file_item in manifest.files:
                    form_field_name = file_item.form_field_name
                    file_content = file_data.get(form_field_name)
                    
                    if not file_content:
                        logger.warning(f"文件 {form_field_name} 内容为空")
                        continue
                    
                    # 根据文件类型解析
                    if file_item.file_type in ['sql_schema', 'sql_data']:
                        # SQL文件直接读取文本
                        text_content = file_content.decode('utf-8', errors='ignore')
                        parsed_files[form_field_name] = {
                            'type': file_item.file_type,
                            'filename': file_item.original_filename,
                            'content': text_content
                        }
                        sql_content += f"\n-- {file_item.original_filename}\n{text_content}\n"
                    
                    elif file_item.file_type == 'jupyter_notebook':
                        # Jupyter notebook文件
                        try:
                            notebook_content = file_content.decode('utf-8', errors='ignore')
                            parsed_files[form_field_name] = {
                                'type': file_item.file_type,
                                'filename': file_item.original_filename,
                                'content': notebook_content
                            }
                        except Exception as e:
                            logger.error(f"解析Jupyter文件 {file_item.original_filename} 失败: {e}")
                    
                    elif file_item.file_type in ['bi_template', 'ai_template']:
                        # 模板文件，暂存原始内容（后续可能需要保存到文件系统）
                        parsed_files[form_field_name] = {
                            'type': file_item.file_type,
                            'filename': file_item.original_filename,
                            'content': file_content,  # 保持二进制格式
                            'size': len(file_content)
                        }
                    
                    elif file_item.file_type == 'supporting_asset':
                        # 支持性素材
                        parsed_files[form_field_name] = {
                            'type': file_item.file_type,
                            'filename': file_item.original_filename,
                            'content': file_content,
                            'size': len(file_content)
                        }
                
                task_manager.update_task(task_id, TaskStatus.PROCESSING, progress=30)
                
                # 第二步：生成实训元数据
                logger.info("步骤2: 生成实训元数据")
                try:
                    metadata_dict = self.llm_client.generate_training_metadata(
                        training_title=manifest.training_title,
                        analysis_goals=manifest.analysis_goals,
                        training_type=manifest.training_type,
                        sql_content=sql_content
                    )
                    
                    # 转换为Schema模型
                    metadata = TrainingMetadata(**metadata_dict)
                    
                except Exception as e:
                    logger.error(f"生成实训元数据失败: {e}")
                    # 使用默认元数据
                    metadata = TrainingMetadata(
                        training_name=manifest.training_title,
                        introduction=f"本实训项目基于真实业务场景，主要分析目标：{'; '.join(manifest.analysis_goals)}",
                        industry="综合",
                        difficulty="中级",
                        duration_hours=8,
                        training_type=manifest.training_type,
                        homework_nodes=[{
                            "name": f"{manifest.training_title}作战室",
                            "tool": "BI" if manifest.training_type == "拖拽式" else "Jupyter",
                            "require_design_file": manifest.training_type == "拖拽式"
                        }],
                        require_report=True
                    )
                
                task_manager.update_task(task_id, TaskStatus.PROCESSING, progress=60)
                
                # 第三步：生成实训手册
                logger.info("步骤3: 生成实训手册")
                try:
                    handbook_markdown = self.llm_client.generate_training_handbook(
                        training_title=manifest.training_title,
                        analysis_goals=manifest.analysis_goals,
                        sql_content=sql_content,
                        metadata_intro=metadata.introduction
                    )
                except Exception as e:
                    logger.error(f"生成实训手册失败: {e}")
                    # 使用默认手册
                    handbook_markdown = f"# 实训手册：{manifest.training_title}\n\n## 项目背景\n\n{metadata.introduction}\n\n## 操作步骤\n\n请按照实训要求完成数据分析任务。"
                
                task_manager.update_task(task_id, TaskStatus.PROCESSING, progress=80)
                
                # 第四步：组装完整结果
                logger.info("步骤4: 组装实训包结果")
                training_package = FullTrainingPackageResponse(
                    metadata=metadata,
                    handbook_markdown=handbook_markdown
                )
                
                # 第五步：数据库持久化
                logger.info("步骤5: 数据库持久化")
                try:
                    from app.utils.training_database_mapper import persist_training_package_to_db
                    from app.core.database import get_db
                    
                    # 获取数据库会话
                    db = next(get_db())
                    
                    db_result = persist_training_package_to_db(
                        db=db,
                        training_data=training_package,
                        manifest=manifest,
                        parsed_files=parsed_files,
                        user_id=user_id
                    )
                    
                    # 构建扩展结果
                    extended_result = ExtendedTrainingTaskResult(
                        training_package=training_package,
                        database_result=db_result
                    )
                    
                    task_manager.update_task(task_id, TaskStatus.SUCCESS, progress=100, result=extended_result)
                    logger.info(f"实训包生成任务完成: {task_id}")
                    
                except Exception as e:
                    logger.error(f"数据库持久化失败: {e}")
                    # 即使数据库持久化失败，也返回生成的内容
                    task_manager.update_task(task_id, TaskStatus.SUCCESS, progress=100, result=training_package)
                    logger.info(f"实训包生成任务完成（数据库持久化失败）: {task_id}")
                
            except Exception as e:
                logger.error(f"处理实训包生成任务失败: {task_id}, 错误: {str(e)}")
                task_manager.update_task(task_id, TaskStatus.ERROR, error_message=str(e))
        
        # 启动异步处理线程
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

# 全局实训包处理器实例
training_package_processor = TrainingPackageProcessor() 