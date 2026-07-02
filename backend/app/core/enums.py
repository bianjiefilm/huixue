"""
统一枚举定义模块
所有枚举类型的单一事实来源 (Single Source of Truth)

创建日期：2024年1月
目的：解决枚举在多个文件中重复定义的问题
"""

import enum
from enum import Enum


# ==================== 实训相关枚举 ====================

class TrainingTypeEnum(str, Enum):
    """实训类型枚举"""
    DRAG_DROP = "DRAG_DROP"          # 拖拽式实训
    CODING = "CODING"                # 编码式实训
    DATA_ANALYSIS = "DATA_ANALYSIS"  # 数据分析实训
    JUPYTER = "JUPYTER"              # Jupyter实训
    BI = "BI"                        # BI实训


class TrainingPublishStatusEnum(str, Enum):
    """实训发布状态枚举"""
    EDITING = "EDITING"      # 编辑中
    PENDING_REVIEW = "PENDING_REVIEW"  # 待审核
    PUBLISHED = "PUBLISHED"  # 已发布
    REJECTED = "REJECTED"    # 已拒绝


class TrainingVisibilityEnum(str, Enum):
    """实训可见性枚举"""
    PRIVATE = "PRIVATE"  # 仅自己可见
    PUBLIC = "PUBLIC"    # 公开发布


class DifficultyLevelEnum(str, Enum):
    """难度等级枚举"""
    beginner = "beginner"        # 初级
    intermediate = "intermediate"  # 中级
    advanced = "advanced"        # 高级


# ==================== 用户相关枚举 ====================

class UserTypeEnum(str, Enum):
    """用户类型枚举"""
    STUDENT = "student"    # 学生
    TEACHER = "teacher"    # 教师
    ADMIN = "admin"        # 管理员


class RoleEnum(str, Enum):
    """角色枚举"""
    STUDENT = "student"    # 学生
    TEACHER = "teacher"    # 教师
    ASSISTANT = "assistant"  # 助教
    ADMIN = "admin"        # 管理员


class UserStatusEnum(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"      # 正常
    INACTIVE = "inactive"  # 停用
    LOCKED = "locked"      # 锁定


# ==================== 组织相关枚举 ====================

class OrganizationTypeEnum(str, Enum):
    """组织类型枚举"""
    SCHOOL = "school"          # 学校
    CAMPUS = "campus"          # 校区
    COLLEGE = "college"        # 学院
    DEPARTMENT = "department"  # 系/部
    MAJOR = "major"            # 专业
    CLASS = "class"            # 班级
    OTHER = "other"            # 其他


# ==================== 课程相关枚举 ====================

class CourseTypeEnum(str, Enum):
    """课程类型枚举"""
    THEORY = "theory"          # 理论课
    PRACTICE = "practice"      # 实践课
    HYBRID = "hybrid"          # 混合式课程


class ResourceTypeEnum(str, Enum):
    """资源类型枚举"""
    VIDEO = "video"            # 视频
    DOCUMENT = "document"      # 文档
    IMAGE = "image"            # 图片
    AUDIO = "audio"            # 音频
    ARCHIVE = "archive"        # 压缩包
    OTHER = "other"            # 其他


class RequestStatusEnum(str, Enum):
    """申请状态枚举"""
    PENDING = "PENDING"      # 待审核
    APPROVED = "APPROVED"    # 已通过
    REJECTED = "REJECTED"    # 已拒绝
    CANCELLED = "CANCELLED"  # 已撤销


class RequestTypeEnum(str, Enum):
    """申请类型枚举"""
    PUBLISH = "PUBLISH"      # 发布申请
    UNPUBLISH = "UNPUBLISH"  # 下架申请
    UPDATE = "UPDATE"        # 更新申请


# ==================== 作业相关枚举 ====================

class HomeworkStatusEnum(str, Enum):
    """作业状态枚举"""
    NOT_STARTED = "not_started"  # 未开始
    IN_PROGRESS = "in_progress"  # 进行中
    SUBMITTED = "submitted"       # 已提交
    GRADED = "graded"            # 已评分


class SubmissionStatusEnum(str, Enum):
    """提交状态枚举"""
    DRAFT = "draft"              # 草稿
    SUBMITTED = "submitted"      # 已提交
    REVIEWING = "reviewing"      # 评审中
    APPROVED = "approved"        # 已通过
    REJECTED = "rejected"        # 已拒绝

# ==================== 统计相关枚举 ====================

class TimeRangeEnum(str, Enum):
    """时间范围枚举"""
    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    THIS_YEAR = "this_year"
    ALL_TIME = "all_time"

class UserGroupEnum(str, Enum):
    """用户群体枚举"""
    STUDENT = "student"
    TEACHER = "teacher"
    ALL = "all"

# ==================== 导出所有枚举 ====================

__all__ = [
    # 实训相关
    'TrainingTypeEnum',
    'TrainingPublishStatusEnum',
    'TrainingVisibilityEnum',
    'DifficultyLevelEnum',
    
    # 用户相关
    'UserTypeEnum',
    'RoleEnum',
    'UserStatusEnum',
    
    # 组织相关
    'OrganizationTypeEnum',
    
    # 课程相关
    'CourseTypeEnum',
    'ResourceTypeEnum',
    'RequestStatusEnum',
    'RequestTypeEnum',
    
    # 作业相关
    'HomeworkStatusEnum',
    'SubmissionStatusEnum',
    
    # 统计相关
    'TimeRangeEnum',
    'UserGroupEnum',
]
