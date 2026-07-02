from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ==================== 枚举类型 ====================

class CourseTypeEnum(str, Enum):
    PRACTICE = "PRACTICE"
    TRAINING = "TRAINING"

class RequestTypeEnum(str, Enum):
    PUBLISH = "PUBLISH"
    UNPUBLISH = "UNPUBLISH"

class RequestStatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class DifficultyEnum(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"

class SortOrderEnum(str, Enum):
    ASC = "asc"
    DESC = "desc"


# ==================== 分类树结构 ====================

class CategoryNode(BaseModel):
    key: str
    title: str
    children: Optional[List['CategoryNode']] = None

# 解决循环引用
CategoryNode.model_rebuild()

class CategoryTreeResponse(BaseModel):
    categories: List[CategoryNode]


# ==================== 实践课程管理 ====================

class PracticeCourseBase(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    direction: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    task_count: int = 0
    coin: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PracticeCourseCreator(BaseModel):
    id: int
    full_name: Optional[str] = None
    username: str

class PracticeCourseItem(PracticeCourseBase):
    creator: Optional[PracticeCourseCreator] = None
    publish_status: str
    visibility: str
    can_unpublish: bool = True
    can_publish: bool = False

class PracticeCourseDetail(PracticeCourseBase):
    intro: Optional[str] = None
    summary: Optional[str] = None
    practice_type: Optional[str] = None
    environment_id: Optional[str] = None
    storage_limit: Optional[str] = None
    memory_limit: Optional[str] = None
    cpu_limit: Optional[str] = None
    creator: Optional[PracticeCourseCreator] = None
    can_unpublish: bool = True

class PracticeCourseListResponse(BaseModel):
    items: List[PracticeCourseItem]
    total: int
    page: int
    page_size: int
    total_pages: int

class PracticeCourseQuery(BaseModel):
    category: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_field: str = Field("updated_at", pattern="^(title|created_at|updated_at)$")
    sort_order: SortOrderEnum = SortOrderEnum.DESC


# ==================== 实训课程管理 ====================

class TrainingCourseBase(BaseModel):
    id: int
    title: str
    intro: Optional[str] = None
    cover_url: Optional[str] = None
    industry: Optional[str] = None
    difficulty: Optional[str] = None
    course_hours: int = 0
    training_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TrainingCourseCreator(BaseModel):
    id: int
    full_name: Optional[str] = None
    username: str

class TrainingCourseItem(TrainingCourseBase):
    creator: Optional[TrainingCourseCreator] = None
    publish_status: str
    visibility: str
    can_unpublish: bool = True
    can_publish: bool = False

class TrainingCourseDetail(TrainingCourseBase):
    handbook_content: Optional[str] = None
    assignment_nodes: Optional[str] = None
    require_design_files: bool = False
    require_experiment_report: bool = False
    environment_id: Optional[str] = None
    storage_limit: Optional[str] = None
    memory_limit: Optional[str] = None
    cpu_limit: Optional[str] = None
    creator: Optional[TrainingCourseCreator] = None
    can_unpublish: bool = True

class TrainingCourseListResponse(BaseModel):
    items: List[TrainingCourseItem]
    total: int
    page: int
    page_size: int
    total_pages: int

class TrainingCourseQuery(BaseModel):
    category: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_field: str = Field("updated_at", pattern="^(title|created_at|updated_at)$")
    sort_order: SortOrderEnum = SortOrderEnum.DESC


# ==================== 课程操作 ====================

class CourseActionRequest(BaseModel):
    course_id: int
    action: str = Field(..., pattern="^(unpublish|publish)$")
    reason: Optional[str] = None

class CourseActionResponse(BaseModel):
    success: bool
    message: str


# ==================== 课程审批 ====================

class CourseRequestBase(BaseModel):
    id: int
    course_id: int
    course_type: CourseTypeEnum
    request_type: RequestTypeEnum
    status: RequestStatusEnum
    application_reason: Optional[str] = None
    applied_at: datetime
    review_comments: Optional[str] = None
    reviewed_at: Optional[datetime] = None

class CourseRequestCourse(BaseModel):
    id: int
    title: str

class CourseRequestUser(BaseModel):
    id: int
    full_name: Optional[str] = None
    username: str

class CourseRequestItem(CourseRequestBase):
    course: CourseRequestCourse
    applicant: CourseRequestUser
    reviewer: Optional[CourseRequestUser] = None
    course_type_text: str
    request_type_text: str
    status_text: str
    can_approve: bool = False
    can_reject: bool = False
    can_view_detail: bool = True

class CourseRequestDetail(CourseRequestBase):
    course: CourseRequestCourse
    applicant: CourseRequestUser
    reviewer: Optional[CourseRequestUser] = None
    course_type_text: str
    request_type_text: str
    status_text: str
    cancelled_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    can_approve: bool = False
    can_reject: bool = False

class CourseRequestListResponse(BaseModel):
    items: List[CourseRequestItem]
    total: int
    page: int
    page_size: int
    total_pages: int

class CourseRequestQuery(BaseModel):
    status: Optional[RequestStatusEnum] = None
    course_type: Optional[CourseTypeEnum] = None
    request_type: Optional[RequestTypeEnum] = None
    course_name: Optional[str] = None
    applicant_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_field: str = Field("applied_at", pattern="^(course_name|applicant_name|request_type|status|applied_at|reviewed_at)$")
    sort_order: SortOrderEnum = SortOrderEnum.DESC

class CourseRequestApprovalRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    review_comments: Optional[str] = None

class CourseRequestSubmitRequest(BaseModel):
    course_id: int
    course_type: CourseTypeEnum
    request_type: RequestTypeEnum
    application_reason: Optional[str] = None

class CourseRequestCancelRequest(BaseModel):
    cancel_reason: Optional[str] = None


# ==================== 统计信息 ====================

class CourseStatistics(BaseModel):
    total_practice_courses: int
    total_training_courses: int
    pending_requests: int
    approved_requests_today: int
    rejected_requests_today: int

class ApprovalStatistics(BaseModel):
    pending_practice_requests: int
    pending_training_requests: int
    total_pending_requests: int
    approved_requests_this_month: int
    rejected_requests_this_month: int
    avg_approval_time_hours: float 
