"""
权限检查工具

用于验证用户是否有权访问特定资源
"""

from typing import Optional
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class PermissionChecker:
    """权限检查器"""
    
    @staticmethod
    def check_teacher_owns_classroom(
        user_id: int,
        user_role: str,
        classroom_id: int,
        db = None
    ) -> bool:
        """
        检查教师是否拥有该课堂
        """
        if user_role == "admin":
            return True
        
        if user_role != "teacher":
            return False
        
        if db is None:
            return False
        
        try:
            from app.models import Classroom
            
            classroom = db.query(Classroom).filter(
                Classroom.id == classroom_id,
                Classroom.teacher_id == user_id
            ).first()
            
            return classroom is not None
        except Exception as e:
            logger.error(f"检查教师课堂所有权失败: {str(e)}")
            return False
    
    @staticmethod
    def check_student_in_classroom(
        user_id: int,
        classroom_id: int,
        db = None
    ) -> bool:
        """
        检查学生是否在该课堂中
        """
        if db is None:
            return False
        
        try:
            from app.models import ClassroomStudent
            
            relationship = db.query(ClassroomStudent).filter(
                ClassroomStudent.classroom_id == classroom_id,
                ClassroomStudent.student_id == user_id
            ).first()
            
            return relationship is not None
        except Exception as e:
            logger.error(f"检查学生课堂成员资格失败: {str(e)}")
            return False
    
    @staticmethod
    def check_can_grade_student(
        teacher_id: int,
        student_id: int,
        classroom_id: int,
        db = None
    ) -> bool:
        """
        检查教师是否可以评分学生
        
        要求:
        1. 教师拥有该课堂
        2. 学生在该课堂中
        """
        if db is None:
            return False
        
        try:
            # 检查教师是否拥有课堂
            if not PermissionChecker.check_teacher_owns_classroom(
                teacher_id, "teacher", classroom_id, db
            ):
                return False
            
            # 检查学生是否在课堂中
            if not PermissionChecker.check_student_in_classroom(
                student_id, classroom_id, db
            ):
                return False
            
            return True
        except Exception as e:
            logger.error(f"检查评分权限失败: {str(e)}")
            return False
    
    @staticmethod
    def check_can_view_grades(
        user_id: int,
        user_role: str,
        target_classroom_id: int,
        target_student_id: Optional[int] = None,
        db = None
    ) -> bool:
        """
        检查用户是否可以查看成绩
        
        要求:
        - 管理员: 可以查看所有
        - 教师: 可以查看自己课堂的成绩
        - 学生: 只能查看自己的成绩
        """
        if user_role == "admin":
            return True
        
        if user_role == "teacher":
            return PermissionChecker.check_teacher_owns_classroom(
                user_id, user_role, target_classroom_id, db
            )
        
        if user_role == "student":
            if target_student_id and target_student_id != user_id:
                # 学生试图查看他人成绩，需要检查权限设置
                # 暂时拒绝
                return False
            return PermissionChecker.check_student_in_classroom(
                user_id, target_classroom_id, db
            )
        
        return False
    
    @staticmethod
    def require_teacher(user_role: str):
        """要求用户是教师"""
        if user_role not in ["teacher", "admin"]:
            raise HTTPException(status_code=403, detail="仅教师和管理员可以访问")
    
    @staticmethod
    def require_admin(user_role: str):
        """要求用户是管理员"""
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="仅管理员可以访问")

