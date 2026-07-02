"""
使用日志统计分析CRUD操作
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, distinct, text
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import io
import base64
from enum import Enum

from app.models import models
from app.schemas.schemas import TimeRangeEnum, UserGroupEnum


def _get_time_range_filter(time_range: TimeRangeEnum, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[datetime, datetime]:
    """
    根据时间范围枚举获取开始和结束时间
    """
    now = datetime.now()
    
    if time_range == TimeRangeEnum.TODAY:
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_range == TimeRangeEnum.YESTERDAY:
        yesterday = now - timedelta(days=1)
        start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_range == TimeRangeEnum.LAST_7_DAYS:
        start_time = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_range == TimeRangeEnum.LAST_30_DAYS:
        start_time = (now - timedelta(days=29)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_range == TimeRangeEnum.CUSTOM:
        if start_date and end_date:
            start_time = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            # 默认为今天
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        # 默认为今天
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return start_time, end_time


def get_course_statistics(
    db: Session,
    time_range: TimeRangeEnum,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    course_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取课程统计分析
    """
    start_time, end_time = _get_time_range_filter(time_range, start_date, end_date)
    
    # 基础查询
    query = db.query(models.Course)
    
    # 课程名称筛选
    if course_name:
        query = query.filter(models.Course.title.like(f"%{course_name}%"))
    
    # 获取总数
    total = query.count()
    
    # 分页
    skip = (page - 1) * page_size
    courses = query.offset(skip).limit(page_size).all()
    
    course_stats = []
    for course in courses:
        # 访问次数
        access_count = db.query(models.CourseAccessLog).filter(
            and_(
                models.CourseAccessLog.course_id == course.id,
                models.CourseAccessLog.access_time >= start_time,
                models.CourseAccessLog.access_time <= end_time
            )
        ).count()
        
        # 访问人数（去重）
        access_users = db.query(models.CourseAccessLog.user_id).filter(
            and_(
                models.CourseAccessLog.course_id == course.id,
                models.CourseAccessLog.access_time >= start_time,
                models.CourseAccessLog.access_time <= end_time
            )
        ).distinct().count()
        
        # 人均访问次数
        avg_access = round(access_count / access_users, 2) if access_users > 0 else 0
        
        # 创建课堂次数
        classroom_count = db.query(models.CourseAddToClassroomLog).filter(
            and_(
                models.CourseAddToClassroomLog.course_id == course.id,
                models.CourseAddToClassroomLog.added_time >= start_time,
                models.CourseAddToClassroomLog.added_time <= end_time
            )
        ).count()
        
        course_stats.append({
            "course_id": course.id,
            "course_name": course.title,
            "access_count": access_count,
            "access_users": access_users,
            "avg_access_per_user": avg_access,
            "classroom_creation_count": classroom_count,
            "course_type": course.course_type.value if course.course_type else "未分类",
            "created_at": course.created_at
        })
    
    return {
        "data": course_stats,
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


def get_practice_statistics(
    db: Session,
    time_range: TimeRangeEnum,
    user_group: Optional[UserGroupEnum] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    practice_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取实践统计分析
    """
    start_time, end_time = _get_time_range_filter(time_range, start_date, end_date)
    
    # 基础查询
    query = db.query(models.Practice)
    
    # 实践名称筛选
    if practice_name:
        query = query.filter(models.Practice.title.like(f"%{practice_name}%"))
    
    # 获取总数
    total = query.count()
    
    # 分页
    skip = (page - 1) * page_size
    practices = query.offset(skip).limit(page_size).all()
    
    practice_stats = []
    for practice in practices:
        # 基础访问统计
        access_query = db.query(models.PracticeAccessLog).filter(
            and_(
                models.PracticeAccessLog.practice_id == practice.id,
                models.PracticeAccessLog.access_time >= start_time,
                models.PracticeAccessLog.access_time <= end_time
            )
        )
        
        # 用户组筛选
        if user_group:
            if user_group == UserGroupEnum.TEACHER:
                # 筛选教师用户
                access_query = access_query.join(models.User).join(models.UserProfile).filter(models.UserProfile.user_type == models.UserTypeEnum.TEACHER)
            elif user_group == UserGroupEnum.STUDENT:
                # 筛选学生用户
                access_query = access_query.join(models.User).join(models.UserProfile).filter(models.UserProfile.user_type == models.UserTypeEnum.STUDENT)
        
        access_count = access_query.count()
        access_users = access_query.with_entities(models.PracticeAccessLog.user_id).distinct().count()
        
        # 学习统计
        learning_query = db.query(models.PracticeLearningLog).filter(
            and_(
                models.PracticeLearningLog.practice_id == practice.id,
                models.PracticeLearningLog.start_time >= start_time,
                models.PracticeLearningLog.start_time <= end_time
            )
        )
        
        if user_group:
            if user_group == UserGroupEnum.TEACHER:
                learning_query = learning_query.join(models.User).join(models.UserProfile).filter(models.UserProfile.user_type == models.UserTypeEnum.TEACHER)
            elif user_group == UserGroupEnum.STUDENT:
                learning_query = learning_query.join(models.User).join(models.UserProfile).filter(models.UserProfile.user_type == models.UserTypeEnum.STUDENT)
        
        learning_count = learning_query.count()
        learning_users = learning_query.with_entities(models.PracticeLearningLog.user_id).distinct().count()
        
        # 平均学习时长
        avg_duration_result = learning_query.with_entities(func.avg(models.PracticeLearningLog.duration_seconds)).scalar()
        avg_duration = round(avg_duration_result / 60, 2) if avg_duration_result else 0  # 转换为分钟
        
        practice_stats.append({
            "practice_id": practice.id,
            "practice_name": practice.title,
            "access_count": access_count,
            "access_users": access_users,
            "learning_count": learning_count,
            "learning_users": learning_users,
            "avg_learning_duration": avg_duration,
            "practice_type": practice.practice_type or "未分类",
            "created_at": practice.created_at
        })
    
    return {
        "data": practice_stats,
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


def get_training_statistics(
    db: Session,
    time_range: TimeRangeEnum,
    user_group: Optional[UserGroupEnum] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    training_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取实训统计分析
    """
    start_time, end_time = _get_time_range_filter(time_range, start_date, end_date)
    
    # 基础查询 - 假设实训数据存储在Training表中
    query = db.query(models.Training)
    
    # 实训名称筛选
    if training_name:
        query = query.filter(models.Training.title.like(f"%{training_name}%"))
    
    # 获取总数
    total = query.count()
    
    # 分页
    skip = (page - 1) * page_size
    trainings = query.offset(skip).limit(page_size).all()
    
    training_stats = []
    for training in trainings:
        # 基础访问统计
        access_query = db.query(models.TrainingAccessLog).filter(
            and_(
                models.TrainingAccessLog.training_id == training.id,
                models.TrainingAccessLog.access_time >= start_time,
                models.TrainingAccessLog.access_time <= end_time
            )
        )
        
        # 用户组筛选
        if user_group:
            if user_group == UserGroupEnum.TEACHER:
                access_query = access_query.join(models.User).join(models.UserProfile).filter(models.UserProfile.user_type == models.UserTypeEnum.TEACHER)
            elif user_group == UserGroupEnum.STUDENT:
                access_query = access_query.join(models.User).join(models.UserProfile).filter(models.UserProfile.user_type == models.UserTypeEnum.STUDENT)
        
        access_count = access_query.count()
        access_users = access_query.with_entities(models.TrainingAccessLog.user_id).distinct().count()
        
        # 学习统计
        learning_query = db.query(models.TrainingLearningLog).filter(
            and_(
                models.TrainingLearningLog.training_id == training.id,
                models.TrainingLearningLog.start_time >= start_time,
                models.TrainingLearningLog.start_time <= end_time
            )
        )
        
        if user_group:
            if user_group == UserGroupEnum.TEACHER:
                learning_query = learning_query.join(models.User).join(models.UserProfile).filter(models.UserProfile.user_type == models.UserTypeEnum.TEACHER)
            elif user_group == UserGroupEnum.STUDENT:
                learning_query = learning_query.join(models.User).join(models.UserProfile).filter(models.UserProfile.user_type == models.UserTypeEnum.STUDENT)
        
        learning_count = learning_query.count()
        learning_users = learning_query.with_entities(models.TrainingLearningLog.user_id).distinct().count()
        
        # 平均学习时长
        avg_duration_result = learning_query.with_entities(func.avg(models.TrainingLearningLog.duration_seconds)).scalar()
        avg_duration = round(avg_duration_result / 60, 2) if avg_duration_result else 0  # 转换为分钟
        
        training_stats.append({
            "training_id": training.id,
            "training_name": training.title,
            "access_count": access_count,
            "access_users": access_users,
            "learning_count": learning_count,
            "learning_users": learning_users,
            "avg_learning_duration": avg_duration,
            "training_type": training.training_type.value if training.training_type else "未分类",
            "created_at": training.created_at
        })
    
    return {
        "data": training_stats,
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


def get_teacher_usage_statistics(
    db: Session,
    time_range: TimeRangeEnum,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    name: Optional[str] = None,
    employee_id: Optional[str] = None,
    college: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取教师使用统计
    """
    start_time, end_time = _get_time_range_filter(time_range, start_date, end_date)
    
    # 基础查询 - 通过UserProfile获取教师用户
    query = db.query(models.User).join(models.UserProfile).filter(
        models.UserProfile.user_type == models.UserTypeEnum.TEACHER
    )
    
    # 筛选条件
    if name:
        query = query.filter(models.UserProfile.real_name.like(f"%{name}%"))
    if employee_id:
        query = query.filter(models.UserProfile.employee_id.like(f"%{employee_id}%"))
    if college:
        # 通过组织关系获取学院信息
        query = query.join(models.Organization).filter(models.Organization.name.like(f"%{college}%"))
    
    # 获取总数
    total = query.count()
    
    # 分页
    skip = (page - 1) * page_size
    teachers = query.offset(skip).limit(page_size).all()
    
    teacher_stats = []
    for teacher in teachers:
        # 创建课堂数
        classroom_count = db.query(models.ClassroomCreationLog).filter(
            and_(
                models.ClassroomCreationLog.teacher_id == teacher.id,
                models.ClassroomCreationLog.created_time >= start_time,
                models.ClassroomCreationLog.created_time <= end_time
            )
        ).count()
        
        # 创建实践数
        practice_count = db.query(models.Practice).filter(
            and_(
                models.Practice.creator_id == teacher.id,
                models.Practice.created_at >= start_time,
                models.Practice.created_at <= end_time
            )
        ).count()
        
        # 发布实践数
        published_practice_count = db.query(models.Practice).filter(
            and_(
                models.Practice.creator_id == teacher.id,
                models.Practice.is_published == True,
                models.Practice.created_at >= start_time,
                models.Practice.created_at <= end_time
            )
        ).count()
        
        # 登录次数
        login_count = db.query(models.UserLoginLog).filter(
            and_(
                models.UserLoginLog.user_id == teacher.id,
                models.UserLoginLog.login_time >= start_time,
                models.UserLoginLog.login_time <= end_time
            )
        ).count()
        
        # 获取教师的UserProfile信息
        teacher_profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == teacher.id).first()
        
        teacher_stats.append({
            "teacher_id": teacher.id,
            "name": teacher_profile.real_name if teacher_profile else teacher.full_name,
            "employee_id": teacher_profile.employee_id if teacher_profile else None,
            "college": teacher_profile.organization.name if teacher_profile and teacher_profile.organization else None,
            "major": None,  # 教师没有专业字段
            "classroom_creation_count": classroom_count,
            "practice_creation_count": practice_count,
            "published_practice_count": published_practice_count,
            "login_count": login_count,
            "last_login": teacher_profile.last_login_at if teacher_profile else None
        })
    
    return {
        "data": teacher_stats,
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


def get_student_usage_statistics(
    db: Session,
    time_range: TimeRangeEnum,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    name: Optional[str] = None,
    student_id: Optional[str] = None,
    college: Optional[str] = None,
    major: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取学生使用统计
    """
    start_time, end_time = _get_time_range_filter(time_range, start_date, end_date)
    
    # 基础查询 - 通过UserProfile获取学生用户
    query = db.query(models.User).join(models.UserProfile).filter(
        models.UserProfile.user_type == models.UserTypeEnum.STUDENT
    )
    
    # 筛选条件
    if name:
        query = query.filter(models.UserProfile.real_name.like(f"%{name}%"))
    if student_id:
        query = query.filter(models.UserProfile.employee_id.like(f"%{student_id}%"))
    
    # 处理组织筛选（避免重复JOIN）
    org_filters = []
    if college:
        org_filters.append(models.Organization.name.like(f"%{college}%"))
    if major:
        org_filters.append(models.Organization.name.like(f"%{major}%"))
    
    if org_filters:
        # 只JOIN一次Organization表，使用OR条件
        query = query.join(models.Organization).filter(or_(*org_filters))
    
    # 获取总数
    total = query.count()
    
    # 分页
    skip = (page - 1) * page_size
    students = query.offset(skip).limit(page_size).all()
    
    student_stats = []
    for student in students:
        # 登录次数
        login_count = db.query(models.UserLoginLog).filter(
            and_(
                models.UserLoginLog.user_id == student.id,
                models.UserLoginLog.login_time >= start_time,
                models.UserLoginLog.login_time <= end_time
            )
        ).count()
        
        # 学习次数（实践学习 + 实训学习 + 教学资源学习）
        practice_learning_count = db.query(models.PracticeLearningLog).filter(
            and_(
                models.PracticeLearningLog.user_id == student.id,
                models.PracticeLearningLog.start_time >= start_time,
                models.PracticeLearningLog.start_time <= end_time
            )
        ).count()
        
        training_learning_count = db.query(models.TrainingLearningLog).filter(
            and_(
                models.TrainingLearningLog.user_id == student.id,
                models.TrainingLearningLog.start_time >= start_time,
                models.TrainingLearningLog.start_time <= end_time
            )
        ).count()
        
        # 移除教学资源学习统计
        # resource_learning_count = db.query(models.StudentResourceLearning).filter(
        #     and_(
        #         models.StudentResourceLearning.student_id == student.id,
        #         models.StudentResourceLearning.first_access_at >= start_time,
        #         models.StudentResourceLearning.first_access_at <= end_time
        #     )
        # ).count()
        
        total_learning_count = practice_learning_count + training_learning_count # + resource_learning_count
        
        # 学习时长（分钟）
        practice_duration = db.query(func.sum(models.PracticeLearningLog.duration_seconds)).filter(
            and_(
                models.PracticeLearningLog.user_id == student.id,
                models.PracticeLearningLog.start_time >= start_time,
                models.PracticeLearningLog.start_time <= end_time
            )
        ).scalar() or 0
        
        training_duration = db.query(func.sum(models.TrainingLearningLog.duration_seconds)).filter(
            and_(
                models.TrainingLearningLog.user_id == student.id,
                models.TrainingLearningLog.start_time >= start_time,
                models.TrainingLearningLog.start_time <= end_time
            )
        ).scalar() or 0
        
        # 移除教学资源学习时长统计
        # resource_duration = db.query(func.sum(models.StudentResourceLearning.learning_duration_seconds)).filter(
        #     and_(
        #         models.StudentResourceLearning.student_id == student.id,
        #         models.StudentResourceLearning.first_access_at >= start_time,
        #         models.StudentResourceLearning.first_access_at <= end_time
        #     )
        # ).scalar() or 0
        
        total_duration = round((practice_duration + training_duration) / 60, 2)  # 转换为分钟
        
        # 获取学生的UserProfile信息
        student_profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == student.id).first()
        
        student_stats.append({
            "student_id": student.id,
            "name": student_profile.real_name if student_profile else student.full_name,
            "student_number": student_profile.employee_id if student_profile else None,
            "college": student_profile.organization.name if student_profile and student_profile.organization else None,
            "major": None,  # 需要通过组织层级获取专业信息
            "class_name": None,  # 需要通过组织层级获取班级信息
            "login_count": login_count,
            "learning_count": total_learning_count,
            "learning_duration": total_duration,
            "last_login": student_profile.last_login_at if student_profile else None
        })
    
    return {
        "data": student_stats,
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


def get_course_detail_statistics(
    db: Session,
    course_id: int,
    time_range: TimeRangeEnum,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    获取课程详细统计（下钻功能）
    """
    start_time, end_time = _get_time_range_filter(time_range, start_date, end_date)
    
    # 获取课程信息
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        return {"error": "课程不存在"}
    
    # 获取访问该课程的用户统计
    access_logs_query = db.query(models.CourseAccessLog).filter(
        and_(
            models.CourseAccessLog.course_id == course_id,
            models.CourseAccessLog.access_time >= start_time,
            models.CourseAccessLog.access_time <= end_time
        )
    ).join(models.User)
    
    # 按用户分组统计
    user_stats_query = db.query(
        models.User.id,
        models.User.full_name,
        models.UserProfile.employee_id,
        models.UserProfile.real_name,
        models.UserProfile.user_type,
        func.count(models.CourseAccessLog.id).label('access_count'),
        func.min(models.CourseAccessLog.access_time).label('first_access'),
        func.max(models.CourseAccessLog.access_time).label('last_access')
    ).join(models.CourseAccessLog).outerjoin(models.UserProfile).filter(
        and_(
            models.CourseAccessLog.course_id == course_id,
            models.CourseAccessLog.access_time >= start_time,
            models.CourseAccessLog.access_time <= end_time
        )
    ).group_by(models.User.id)
    
    # 获取总数
    total = user_stats_query.count()
    
    # 分页
    skip = (page - 1) * page_size
    user_stats = user_stats_query.offset(skip).limit(page_size).all()
    
    user_detail_stats = []
    for stat in user_stats:
        user_detail_stats.append({
            "user_id": stat.id,
            "name": stat.real_name or stat.full_name,
            "user_number": stat.employee_id,
            "college": None,  # 需要通过组织关系获取
            "major": None,   # 需要通过组织关系获取
            "role": stat.user_type.value if stat.user_type else "未知",
            "access_count": stat.access_count,
            "first_access_time": stat.first_access,
            "last_access_time": stat.last_access
        })
    
    return {
        "course_info": {
            "course_id": course.id,
            "course_name": course.title,
            "course_type": course.course_type.value if course.course_type else "未分类"
        },
        "data": user_detail_stats,
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


def export_statistics_data(
    db: Session,
    export_type: str,
    data: Dict[str, Any],
    export_format: str = "xlsx"
) -> str:
    """
    导出统计数据
    """
    try:
        # 将数据转换为DataFrame
        df = pd.DataFrame(data.get("data", []))
        
        if df.empty:
            return ""
        
        # 根据导出类型设置列名映射
        column_mappings = {
            "course": {
                "course_name": "课程名称",
                "access_count": "访问次数",
                "access_users": "访问人数",
                "avg_access_per_user": "人均访问次数",
                "classroom_creation_count": "创建课堂次数",
                "course_type": "课程类型",
                "created_at": "创建时间"
            },
            "practice": {
                "practice_name": "实践名称",
                "access_count": "访问次数",
                "access_users": "访问人数",
                "learning_count": "学习次数",
                "learning_users": "学习人数",
                "avg_learning_duration": "平均学习时长(分钟)",
                "practice_type": "实践类型",
                "created_at": "创建时间"
            },
            "training": {
                "training_name": "实训名称",
                "access_count": "访问次数",
                "access_users": "访问人数",
                "learning_count": "学习次数",
                "learning_users": "学习人数",
                "avg_learning_duration": "平均学习时长(分钟)",
                "training_type": "实训类型",
                "created_at": "创建时间"
            },
            "teacher": {
                "name": "姓名",
                "employee_id": "工号",
                "college": "学院",
                "major": "专业",
                "classroom_creation_count": "创建课堂数",
                "practice_creation_count": "创建实践数",
                "published_practice_count": "发布实践数",
                "login_count": "登录次数",
                "last_login": "最后登录时间"
            },
            "student": {
                "name": "姓名",
                "student_number": "学号",
                "college": "学院",
                "major": "专业",
                "class_name": "班级",
                "login_count": "登录次数",
                "learning_count": "学习次数",
                "learning_duration": "学习时长(分钟)",
                "last_login": "最后登录时间"
            }
        }
        
        # 重命名列
        if export_type in column_mappings:
            df = df.rename(columns=column_mappings[export_type])
        
        # 导出为Excel
        if export_format.lower() == "xlsx":
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='统计数据')
            output.seek(0)
            
            # 转换为base64编码
            excel_data = base64.b64encode(output.getvalue()).decode()
            return excel_data
        
        # 导出为CSV
        elif export_format.lower() == "csv":
            csv_data = df.to_csv(index=False, encoding='utf-8-sig')
            return base64.b64encode(csv_data.encode()).decode()
        
        return ""
        
    except Exception as e:
        print(f"导出数据失败: {str(e)}")
        return "" 