#!/usr/bin/env python3
"""
数据库映射工具类
处理AI生成的数据到数据库的映射和持久化
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.models import (
    Practice, Task, TaskTest, Question, TestPaper, TestPaperQuestion, User
)
from app.schemas.generation import FullPackageResponse
from app.utils.enum_mappers import (
    map_difficulty as _map_difficulty,
    map_task_type as _map_task_type,
    map_question_type as _map_question_type,
)

logger = logging.getLogger(__name__)

class DatabaseMapper:
    """数据库映射器"""
    
    def __init__(self, db: Session, current_user_id: int):
        self.db = db
        self.current_user_id = current_user_id
    
    def persist_course_package(self, course_data: FullPackageResponse) -> Dict[str, Any]:
        """
        持久化完整的课程包数据到数据库
        返回创建的各个实体的ID
        """
        try:
            result = {
                "practice_id": None,
                "task_ids": [],
                "test_paper_id": None,
                "question_ids": [],
                "success": False,
                "message": "",
                "details": {}
            }
            
            logger.info("开始持久化课程包数据到数据库")
            
            # 1. 持久化课程元数据
            practice_id = self._persist_practice_metadata(course_data.metadata)
            result["practice_id"] = practice_id
            result["details"]["practice"] = {"id": practice_id, "title": course_data.metadata.practice_name}
            
            # 2. 持久化关卡数据
            task_ids = self._persist_levels_data(practice_id, course_data.processed_files)
            result["task_ids"] = task_ids
            result["details"]["tasks"] = [{"id": tid, "order": i} for i, tid in enumerate(task_ids)]
            
            # 3. 持久化考核试题
            test_paper_id, question_ids = self._persist_exam_questions(course_data)
            result["test_paper_id"] = test_paper_id
            result["question_ids"] = question_ids
            if test_paper_id:
                result["details"]["test_paper"] = {
                    "id": test_paper_id, 
                    "question_count": len(question_ids)
                }
            
            # 4. 更新课程的任务计数
            self._update_practice_task_count(practice_id, len(task_ids))
            
            # 提交事务
            self.db.commit()
            
            result["success"] = True
            result["message"] = f"课程包持久化成功：课程ID={practice_id}, 关卡数={len(task_ids)}, 试题数={len(question_ids)}"
            
            logger.info(f"课程包持久化完成: {result['message']}")
            return result
            
        except Exception as e:
            logger.error(f"课程包持久化失败: {str(e)}")
            self.db.rollback()
            result["success"] = False
            result["message"] = f"持久化失败: {str(e)}"
            return result
    
    def _persist_practice_metadata(self, metadata) -> int:
        """持久化课程元数据到practices表"""
        logger.info("持久化课程元数据")
        
        # 映射数据
        practice_data = {
            "title": metadata.practice_name,
            "intro": metadata.introduction,
            "difficulty": self._map_difficulty(metadata.difficulty),
            "direction": metadata.category.primary,
            "category": metadata.category.secondary[0] if metadata.category.secondary else "程序设计",  # 必需字段
            "categories": json.dumps(metadata.category.secondary, ensure_ascii=False),
            "practice_type": "在线编码实践",
            "environment_id": metadata.environment_id,
            "allow_skip_levels": metadata.config.allow_skip,
            "enable_code_editor": metadata.config.editor_enabled,
            "enable_terminal": metadata.config.shell_enabled,
            "repo_visibility": "可见" if metadata.config.repo_visible else "不可见",
            "creator_id": self.current_user_id,
            "publish_status": "DRAFT",
            "visibility": "PRIVATE",
            "task_count": 0,  # 稍后更新
            "coin": 0,  # 默认值
            "storage_limit": "1Gi",  # 默认值
            "memory_limit": "1Gi",  # 默认值
            "cpu_limit": "1",  # 默认值
            "current_version": "1.0.0",  # 默认版本
            "has_unpublished_changes": False,
            "is_published": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # 创建Practice对象
        practice = Practice(**practice_data)
        
        self.db.add(practice)
        self.db.flush()  # 获取ID但不提交
        
        logger.info(f"课程元数据已创建，ID: {practice.id}")
        return practice.id
    
    def _persist_levels_data(self, practice_id: int, processed_files: List) -> List[int]:
        """持久化关卡数据到tasks和task_tests表"""
        logger.info("持久化关卡数据")
        
        task_ids = []
        order_index = 0
        
        for file_result in processed_files:
            if not file_result.levels:
                continue
                
            for level in file_result.levels:
                try:
                    # 持久化关卡基本信息
                    task_id = self._persist_single_task(practice_id, level, order_index)
                    task_ids.append(task_id)
                    
                    # 持久化评测资源（如果存在）
                    if level.evaluation_assets:
                        self._persist_evaluation_assets(task_id, level.evaluation_assets)
                    
                    order_index += 1
                    
                except Exception as e:
                    logger.error(f"持久化关卡失败: {str(e)}")
                    continue
        
        logger.info(f"关卡数据持久化完成，共创建 {len(task_ids)} 个关卡")
        return task_ids
    
    def _persist_single_task(self, practice_id: int, level, order_index: int) -> int:
        """持久化单个关卡"""
        outline = level.outline_item
        content = level.content
        
        # 映射任务类型
        task_type = self._map_task_type(outline.suggested_type)
        
        # 准备任务数据
        task_data = {
            "practice_id": practice_id,
            "title": outline.level_title,
            "task_type": task_type,
            "difficulty": self._map_difficulty(outline.difficulty),
            "order_in_practice": order_index,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # 根据内容类型设置不同字段
        if hasattr(content, 'task_markdown'):
            # 实践题
            task_data.update({
                "handbook_markdown": content.task_markdown,
                "answer_content_markdown": content.answer_markdown,
                "question_data": None
            })
        elif isinstance(content, list):
            # 选择题或判断题
            task_data.update({
                "handbook_markdown": None,
                "answer_content_markdown": None,
                "question_data": json.dumps(content, ensure_ascii=False)
            })
        
        # 创建Task对象
        task = Task(**task_data)
        
        self.db.add(task)
        self.db.flush()
        
        logger.info(f"关卡已创建：{outline.level_title}, ID: {task.id}")
        return task.id
    
    def _persist_evaluation_assets(self, task_id: int, evaluation_assets):
        """持久化评测资源"""
        logger.info(f"持久化关卡 {task_id} 的评测资源")
        
        # 更新tasks表的评测脚本字段
        # 注意：这里假设数据库有evaluation_script_content字段
        # 如果没有，需要考虑其他存储方案
        try:
            self.db.execute(
                text("UPDATE tasks SET evaluation_script_path = :script WHERE id = :task_id"),
                {
                    "script": f"judge_scripts/task_{task_id}.py",
                    "task_id": task_id
                }
            )
        except Exception as e:
            logger.warning(f"更新评测脚本路径失败: {str(e)}")
        
        # 持久化测试用例
        for i, test_case in enumerate(evaluation_assets.test_cases):
            task_test_data = {
                "task_id": task_id,
                "input_data": test_case.get("input", ""),
                "expected_output": test_case.get("expected_output", ""),
                "is_hidden": test_case.get("is_hidden", False),
                "match_rule": test_case.get("match_rule", "exact"),
                "order_index": i,
                "created_at": datetime.now()
            }
            
            task_test = TaskTest(**task_test_data)
            self.db.add(task_test)
        
        logger.info(f"评测资源持久化完成，共 {len(evaluation_assets.test_cases)} 个测试用例")
    
    def _persist_exam_questions(self, course_data: FullPackageResponse) -> tuple[Optional[int], List[int]]:
        """持久化考核试题"""
        logger.info("持久化考核试题")
        
        # 收集所有试题
        all_questions = []
        for file_result in course_data.processed_files:
            if file_result.exam_questions:
                all_questions.extend(file_result.exam_questions)
        
        if not all_questions:
            logger.info("没有考核试题需要持久化")
            return None, []
        
        # 创建试卷
        test_paper_data = {
            "title": f"[自动生成] {course_data.metadata.practice_name} 配套测验",
            "creator_id": self.current_user_id,
            "is_shared": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        test_paper = TestPaper(**test_paper_data)
        self.db.add(test_paper)
        self.db.flush()
        
        test_paper_id = test_paper.id
        logger.info(f"试卷已创建，ID: {test_paper_id}")
        
        # 持久化试题
        question_ids = []
        for i, question_data in enumerate(all_questions):
            try:
                question_id = self._persist_single_question(question_data)
                question_ids.append(question_id)
                
                # 关联试题到试卷
                self._link_question_to_paper(test_paper_id, question_id, i)
                
            except Exception as e:
                logger.error(f"持久化试题失败: {str(e)}")
                continue
        
        logger.info(f"考核试题持久化完成：试卷ID={test_paper_id}, 试题数={len(question_ids)}")
        return test_paper_id, question_ids
    
    def _persist_single_question(self, question_data: Dict) -> int:
        """持久化单个试题"""
        question_db_data = {
            "content": question_data.get("question_stem", ""),
            "question_type": self._map_question_type(question_data.get("question_type", "")),
            "options": json.dumps(question_data.get("options", []), ensure_ascii=False),
            "correct_answers": json.dumps(question_data.get("correct_answer", []), ensure_ascii=False),
            "explanation": question_data.get("analysis", ""),
            "creator_id": self.current_user_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        question = Question(**question_db_data)
        self.db.add(question)
        self.db.flush()
        
        return question.id
    
    def _link_question_to_paper(self, test_paper_id: int, question_id: int, order_index: int):
        """关联试题到试卷"""
        link_data = {
            "test_paper_id": test_paper_id,
            "question_id": question_id,
            "score_for_question": 5,  # 默认分数
            "order_in_paper": order_index
            # 注意：TestPaperQuestion可能没有created_at字段
        }
        
        link = TestPaperQuestion(**link_data)
        self.db.add(link)
    
    def _update_practice_task_count(self, practice_id: int, task_count: int):
        """更新课程的任务计数"""
        self.db.execute(
            text("UPDATE practices SET task_count = :count WHERE id = :practice_id"),
            {"count": task_count, "practice_id": practice_id}
        )
    
    # 映射工具方法（委托给纯函数）
    def _map_difficulty(self, ai_difficulty: str) -> str:
        return _map_difficulty(ai_difficulty)

    def _map_task_type(self, ai_type: str) -> str:
        return _map_task_type(ai_type)

    def _map_question_type(self, ai_type: str) -> str:
        return _map_question_type(ai_type)

# 便捷函数
def persist_course_package_to_db(
    db: Session, 
    course_data: FullPackageResponse, 
    current_user_id: int
) -> Dict[str, Any]:
    """
    便捷函数：持久化课程包到数据库
    """
    mapper = DatabaseMapper(db, current_user_id)
    return mapper.persist_course_package(course_data) 