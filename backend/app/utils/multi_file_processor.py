#!/usr/bin/env python3
"""
多文件处理器 - 处理不同类型的教学文件并生成完整的课程包
"""

import logging
import threading
from typing import List, Dict, Any, Tuple, Optional
from app.utils.file_parser import FileParser
from app.utils.llm_client import LLMClient
from app.utils.task_manager import task_manager, TaskStatus
from app.utils.database_mapper import persist_course_package_to_db
from app.core.database import get_db
from app.schemas.generation import (
    FullCourseManifest, ProcessedFileResult, FullPackageResponse, 
    MetadataResponse, Category, Config, GeneratedLevel, OutlineItem,
    PracticeContent, EvaluationAssetResponse
)

logger = logging.getLogger(__name__)

class MultiFileProcessor:
    """多文件处理器"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.file_parser = FileParser()
    
    def process_full_course_package_async(self, task_id: str, manifest: FullCourseManifest, file_data: Dict[str, bytes], current_user_id: Optional[int] = None):
        """异步处理完整课程包"""
        def worker():
            try:
                logger.info(f"开始处理课程包任务: {task_id}")
                task_manager.update_task(task_id, TaskStatus.PROCESSING, progress=0)
                
                # 步骤1: 解析所有文件 (10%)
                parsed_files = self._parse_all_files(manifest, file_data)
                task_manager.update_task(task_id, TaskStatus.PROCESSING, progress=10)
                
                # 步骤2: 生成课程元数据 (20%)
                metadata = self._generate_course_metadata(manifest, parsed_files)
                task_manager.update_task(task_id, TaskStatus.PROCESSING, progress=20)
                
                # 步骤3: 处理每个文件 (20% - 85%)
                processed_files = self._process_individual_files(task_id, manifest, parsed_files)
                
                # 步骤4: 生成最终结果 (90%)
                result = FullPackageResponse(
                    metadata=metadata,
                    processed_files=processed_files
                )
                task_manager.update_task(task_id, TaskStatus.PROCESSING, progress=90)
                
                # 步骤5: 持久化到数据库 (90% - 100%)
                db_result = None
                if current_user_id:
                    try:
                        db_result = self._persist_to_database(result, current_user_id)
                        logger.info(f"数据库持久化结果: {db_result}")
                    except Exception as e:
                        logger.warning(f"数据库持久化失败: {str(e)}")
                
                # 将数据库结果添加到响应中
                if db_result:
                    # 创建扩展的结果对象
                    extended_result = {
                        "course_package": result,
                        "database_result": db_result
                    }
                    task_manager.update_task(task_id, TaskStatus.SUCCESS, progress=100, result=extended_result)
                else:
                    task_manager.update_task(task_id, TaskStatus.SUCCESS, progress=100, result=result)
                
                logger.info(f"课程包处理完成: {task_id}")
                
            except Exception as e:
                logger.error(f"课程包处理失败 {task_id}: {str(e)}")
                task_manager.update_task(task_id, TaskStatus.ERROR, error_message=str(e))
        
        # 在新线程中运行处理任务
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
    
    def _parse_all_files(self, manifest: FullCourseManifest, file_data: Dict[str, bytes]) -> Dict[str, Tuple[str, str]]:
        """解析所有文件，返回文件名到(文本内容, 文件类型)的映射"""
        parsed_files = {}
        
        for file_item in manifest.files:
            form_field_name = file_item.form_field_name
            if form_field_name not in file_data:
                logger.warning(f"文件 {form_field_name} 在上传数据中未找到")
                continue
            
            try:
                file_content = file_data[form_field_name]
                filename = file_item.original_filename
                
                # 根据文件扩展名选择解析方法
                if filename.lower().endswith('.pdf'):
                    text_content = self.file_parser.extract_text_from_pdf(file_content)
                elif filename.lower().endswith(('.docx', '.doc')):
                    text_content = self.file_parser.extract_text_from_docx(file_content)
                else:
                    # 尝试作为文本文件读取
                    text_content = file_content.decode('utf-8', errors='ignore')
                
                parsed_files[filename] = (text_content, file_item.file_type)
                logger.info(f"成功解析文件: {filename} ({len(text_content)} 字符)")
                
            except Exception as e:
                logger.error(f"解析文件 {filename} 失败: {str(e)}")
                parsed_files[filename] = ("", file_item.file_type)
        
        return parsed_files
    
    def _generate_course_metadata(self, manifest: FullCourseManifest, parsed_files: Dict[str, Tuple[str, str]]) -> MetadataResponse:
        """生成课程元数据"""
        try:
            # 合并所有文件的文本内容
            all_text = "\n\n".join([content for content, _ in parsed_files.values() if content])
            
            # 生成文件清单字符串
            file_manifest = "\n".join([
                f"- {filename} ({file_type})" 
                for filename, (_, file_type) in parsed_files.items()
            ])
            
            # 调用LLM生成元数据
            metadata_dict = self.llm_client.generate_course_metadata(
                manifest.course_title,
                all_text[:3000],  # 限制长度避免token过多
                file_manifest
            )
            
            # 转换为响应模型
            return MetadataResponse(
                practice_name=metadata_dict["practice_name"],
                practice_type=metadata_dict["practice_type"],
                introduction=metadata_dict["introduction"],
                difficulty=metadata_dict["difficulty"],
                category=Category(
                    primary=metadata_dict["category"]["primary"],
                    secondary=metadata_dict["category"]["secondary"]
                ),
                environment_id=metadata_dict["environment_id"],
                config=Config(
                    allow_skip=metadata_dict["config"]["allow_skip"],
                    editor_enabled=metadata_dict["config"]["editor_enabled"],
                    shell_enabled=metadata_dict["config"]["shell_enabled"],
                    repo_visible=metadata_dict["config"]["repo_visible"]
                )
            )
            
        except Exception as e:
            logger.error(f"生成课程元数据失败: {str(e)}")
            # 返回默认元数据
            return MetadataResponse(
                practice_name=manifest.course_title,
                practice_type="在线编码实践",
                introduction=f"本课程《{manifest.course_title}》旨在帮助学习者掌握相关技能。",
                difficulty="初级",
                category=Category(primary="计算机基础", secondary=["程序设计"]),
                environment_id="python-3.9-standard",
                config=Config(
                    allow_skip=True,
                    editor_enabled=True,
                    shell_enabled=True,
                    repo_visible=True
                )
            )
    
    def _process_individual_files(self, task_id: str, manifest: FullCourseManifest, parsed_files: Dict[str, Tuple[str, str]]) -> List[ProcessedFileResult]:
        """处理每个文件"""
        processed_files = []
        total_files = len(parsed_files)
        
        for i, (filename, (text_content, file_type)) in enumerate(parsed_files.items()):
            try:
                logger.info(f"处理文件: {filename} (类型: {file_type})")
                
                if file_type == "teaching_content":
                    # 教学内容文件：生成关卡
                    levels = self._process_teaching_content(text_content, filename)
                    processed_files.append(ProcessedFileResult(
                        original_filename=filename,
                        file_type=file_type,
                        levels=levels,
                        exam_questions=None,
                        processing_status="SUCCESS"
                    ))
                    
                elif file_type == "teaching_plan":
                    # 教学方案文件：生成考核试题
                    exam_questions = self._process_teaching_plan(text_content)
                    processed_files.append(ProcessedFileResult(
                        original_filename=filename,
                        file_type=file_type,
                        levels=None,
                        exam_questions=exam_questions,
                        processing_status="SUCCESS"
                    ))
                    
                elif file_type == "ideological_elements":
                    # 思政元素文件：生成相关考核试题
                    exam_questions = self._process_ideological_elements(text_content)
                    processed_files.append(ProcessedFileResult(
                        original_filename=filename,
                        file_type=file_type,
                        levels=None,
                        exam_questions=exam_questions,
                        processing_status="SUCCESS"
                    ))
                
                # 更新进度 (20% - 85%)
                progress = 20 + int((i + 1) / total_files * 65)
                task_manager.update_task(task_id, TaskStatus.PROCESSING, progress=progress)
                
            except Exception as e:
                logger.error(f"处理文件 {filename} 失败: {str(e)}")
                processed_files.append(ProcessedFileResult(
                    original_filename=filename,
                    file_type=file_type,
                    levels=None,
                    exam_questions=None,
                    processing_status="ERROR",
                    error_message=str(e)
                ))
        
        return processed_files
    
    def _process_teaching_content(self, text_content: str, filename: str) -> List[GeneratedLevel]:
        """处理教学内容文件，生成关卡"""
        try:
            # 1. 生成关卡提纲
            outline_data = self.llm_client.generate_course_outline(text_content, filename)
            
            levels = []
            for outline_item_dict in outline_data:
                try:
                    # 2. 为每个提纲项生成关卡内容
                    content = self.llm_client.generate_level_content(text_content, outline_item_dict)
                    
                    # 3. 如果是实践题，生成评测资源
                    evaluation_assets = None
                    if outline_item_dict.get('suggested_type') == '实践题' and isinstance(content, dict):
                        try:
                            eval_assets_dict = self.llm_client.generate_evaluation_assets(
                                content.get('task_markdown', ''),
                                content.get('answer_markdown', '')
                            )
                            evaluation_assets = EvaluationAssetResponse(
                                judge_script=eval_assets_dict['judge_script'],
                                test_cases=eval_assets_dict['test_cases']
                            )
                        except Exception as e:
                            logger.warning(f"生成评测资源失败: {str(e)}")
                    
                    # 构建OutlineItem
                    outline_item = OutlineItem(
                        level_title=outline_item_dict.get('level_title', ''),
                        core_knowledge=outline_item_dict.get('core_knowledge', ''),
                        suggested_type=outline_item_dict.get('suggested_type', '实践题'),
                        difficulty=outline_item_dict.get('difficulty', '中级')
                    )
                    
                    # 构建关卡内容
                    if isinstance(content, dict) and 'task_markdown' in content:
                        level_content = PracticeContent(
                            task_markdown=content['task_markdown'],
                            answer_markdown=content['answer_markdown']
                        )
                    else:
                        level_content = content
                    
                    levels.append(GeneratedLevel(
                        outline_item=outline_item,
                        content=level_content,
                        evaluation_assets=evaluation_assets
                    ))
                    
                except Exception as e:
                    logger.error(f"生成关卡失败: {str(e)}")
                    continue
            
            return levels
            
        except Exception as e:
            logger.error(f"处理教学内容失败: {str(e)}")
            return []
    
    def _process_teaching_plan(self, text_content: str) -> List[Dict[str, Any]]:
        """处理教学方案文件，生成考核试题"""
        try:
            return self.llm_client.generate_exam_questions(text_content, 3, 2, 2)
        except Exception as e:
            logger.error(f"处理教学方案失败: {str(e)}")
            return []
    
    def _process_ideological_elements(self, text_content: str) -> List[Dict[str, Any]]:
        """处理思政元素文件，生成相关考核试题"""
        try:
            return self.llm_client.generate_exam_questions(text_content, 2, 1, 2)
        except Exception as e:
            logger.error(f"处理思政元素失败: {str(e)}")
            return []
    
    def _persist_to_database(self, course_data: FullPackageResponse, current_user_id: int) -> Dict[str, Any]:
        """持久化课程包数据到数据库"""
        logger.info("开始持久化课程包到数据库")
        
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 调用数据库映射器持久化数据
            db_result = persist_course_package_to_db(db, course_data, current_user_id)
            
            logger.info(f"数据库持久化完成: {db_result['message']}")
            return db_result
            
        except Exception as e:
            logger.error(f"数据库持久化过程中出错: {str(e)}")
            return {
                "success": False,
                "message": f"数据库持久化失败: {str(e)}",
                "practice_id": None,
                "task_ids": [],
                "test_paper_id": None,
                "question_ids": []
            }
        finally:
            # 确保数据库连接关闭
            try:
                db.close()
            except:
                pass

# 全局处理器实例
multi_file_processor = MultiFileProcessor() 