"""
测试数据库管理工具
提供数据清理、恢复、备份机制
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import models


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.backup_dir = Path(__file__).parent.parent.parent / "test_backups"
        self.backup_dir.mkdir(exist_ok=True)

    def backup_database(self, backup_name: str = None) -> str:
        """备份数据库"""
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        backup_path = self.backup_dir / backup_name
        
        # 备份关键表数据
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "users": self._backup_table("users"),
            "classrooms": self._backup_table("classrooms"),
            "practices": self._backup_table("practices"),
            "tasks": self._backup_table("tasks"),
            "task_tests": self._backup_table("task_tests"),
            "classroom_students": self._backup_table("classroom_students"),
            "classroom_practices": self._backup_table("classroom_practices"),
            "task_evaluation_results": self._backup_table("task_evaluation_results")
        }
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
        
        return str(backup_path)

    def _backup_table(self, table_name: str) -> list:
        """备份单个表"""
        try:
            result = self.db_session.execute(text(f"SELECT * FROM {table_name}"))
            columns = result.keys()
            rows = []
            for row in result:
                rows.append(dict(zip(columns, row)))
            return rows
        except Exception as e:
            print(f"备份表 {table_name} 失败: {e}")
            return []

    def restore_database(self, backup_path: str):
        """恢复数据库"""
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # 清理现有数据
        self.cleanup_test_data()
        
        # 恢复数据
        for table_name, rows in backup_data.items():
            if table_name == "timestamp":
                continue
            self._restore_table(table_name, rows)

    def _restore_table(self, table_name: str, rows: list):
        """恢复单个表"""
        if not rows:
            return
        
        try:
            # 获取表模型
            model_map = {
                "users": models.User,
                "classrooms": models.Classroom,
                "practices": models.Practice,
                "tasks": models.Task,
                "task_tests": models.TaskTest,
                "classroom_students": models.ClassroomStudent,
                "classroom_practices": models.ClassroomPractice,
                "task_evaluation_results": models.TaskEvaluationResult
            }
            
            model = model_map.get(table_name)
            if not model:
                return
            
            # 批量插入数据
            for row in rows:
                # 过滤掉None值
                row = {k: v for k, v in row.items() if v is not None}
                instance = model(**row)
                self.db_session.add(instance)
            
            self.db_session.commit()
        except Exception as e:
            print(f"恢复表 {table_name} 失败: {e}")
            self.db_session.rollback()

    def cleanup_test_data(self, prefix: str = "test_"):
        """清理测试数据"""
        try:
            # 删除测试用户的评测结果
            self.db_session.query(models.TaskEvaluationResult).filter(
                models.TaskEvaluationResult.user_id.in_(
                    self.db_session.query(models.User.id).filter(
                        models.User.username.like(f"{prefix}%")
                    )
                )
            ).delete(synchronize_session=False)
            
            # 删除测试任务测试用例
            self.db_session.query(models.TaskTest).filter(
                models.TaskTest.task_id.like(f"task_{prefix}%")
            ).delete(synchronize_session=False)
            
            # 删除测试任务
            self.db_session.query(models.Task).filter(
                models.Task.id.like(f"task_{prefix}%")
            ).delete(synchronize_session=False)
            
            # 删除课堂实践关联
            self.db_session.query(models.ClassroomPractice).filter(
                models.ClassroomPractice.practice_id.in_(
                    self.db_session.query(models.Practice.id).filter(
                        models.Practice.title.like(f"%{prefix}%")
                    )
                )
            ).delete(synchronize_session=False)
            
            # 删除测试实践
            self.db_session.query(models.Practice).filter(
                models.Practice.title.like(f"%{prefix}%")
            ).delete(synchronize_session=False)
            
            # 删除课堂学生关联
            self.db_session.query(models.ClassroomStudent).filter(
                models.ClassroomStudent.classroom_id.in_(
                    self.db_session.query(models.Classroom.id).filter(
                        models.Classroom.name.like(f"%{prefix}%")
                    )
                )
            ).delete(synchronize_session=False)
            
            # 删除测试课堂
            self.db_session.query(models.Classroom).filter(
                models.Classroom.name.like(f"%{prefix}%")
            ).delete(synchronize_session=False)
            
            # 删除测试用户
            self.db_session.query(models.User).filter(
                models.User.username.like(f"{prefix}%")
            ).delete(synchronize_session=False)
            
            self.db_session.commit()
        except Exception as e:
            print(f"清理测试数据失败: {e}")
            self.db_session.rollback()

    def cleanup_evaluation_results(self, user_id: Optional[int] = None, task_id: Optional[str] = None):
        """清理评测结果"""
        query = self.db_session.query(models.TaskEvaluationResult)
        
        if user_id:
            query = query.filter(models.TaskEvaluationResult.user_id == user_id)
        if task_id:
            query = query.filter(models.TaskEvaluationResult.task_id == task_id)
        
        query.delete(synchronize_session=False)
        self.db_session.commit()

    def create_snapshot(self) -> str:
        """创建数据快照"""
        return self.backup_database(f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    def restore_snapshot(self, snapshot_path: str):
        """恢复数据快照"""
        self.restore_database(snapshot_path)

    def get_table_counts(self) -> Dict[str, int]:
        """获取各表记录数"""
        tables = [
            "users", "classrooms", "practices", "tasks", 
            "task_tests", "task_evaluation_results"
        ]
        
        counts = {}
        for table in tables:
            try:
                result = self.db_session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                counts[table] = result.scalar()
            except Exception as e:
                counts[table] = 0
        
        return counts


