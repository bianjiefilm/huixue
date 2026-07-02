"""
Classroom related Pydantic schemas with validation
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, validator, Field
from app.core.validators import SafeString, SafeText, PositiveInt, PageNumber, PageSize
from enum import Enum


class ClassroomStatus(str, Enum):
    """Classroom status enum"""
    ONGOING = "ongoing"
    UPCOMING = "upcoming"  
    ENDED = "ended"


class ClassroomBase(BaseModel):
    """Base classroom schema"""
    name: SafeString = Field(..., description="课堂名称")
    description: Optional[SafeText] = Field(None, description="课堂描述")
    # teacher_id moved to query parameter in endpoint, kept optional for backward compatibility
    teacher_id: Optional[PositiveInt] = Field(None, description="教师ID (推荐通过查询参数传递)")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    credit: Optional[int] = Field(None, description="学分")
    cover_url: Optional[str] = Field(None, description="封面URL")
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('结束日期必须晚于开始日期')
        return v


class ClassroomCreate(ClassroomBase):
    """Schema for creating a classroom"""
    max_students: Optional[PositiveInt] = Field(50, description="最大学生数")
    is_public: bool = Field(True, description="是否公开")


class ClassroomUpdate(BaseModel):
    """Schema for updating a classroom"""
    name: Optional[SafeString] = None
    description: Optional[SafeText] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_students: Optional[PositiveInt] = None
    is_public: Optional[bool] = None
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v <= values['start_date']:
            raise ValueError('结束日期必须晚于开始日期')
        return v


class ClassroomInDB(ClassroomBase):
    """Schema for classroom in database"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str
    student_count: int = 0
    
    class Config:
        orm_mode = True


class ClassroomResponse(BaseModel):
    """Response schema for single classroom"""
    code: str = "0000"
    message: str = "success"
    data: ClassroomInDB


class ClassroomListResponse(BaseModel):
    """Response schema for classroom list"""
    code: str = "0000"
    message: str = "success"
    data: dict


class ClassroomQueryParams(BaseModel):
    """Query parameters for classroom list"""
    teacher_id: Optional[PositiveInt] = Field(None, description="教师ID")
    status: Optional[ClassroomStatus] = Field(None, description="课堂状态")
    page: PageNumber = Field(1, description="页码")
    page_size: PageSize = Field(20, description="每页数量")
    search: Optional[SafeString] = Field(None, description="搜索关键词")


class AddStudentRequest(BaseModel):
    """Request to add students to classroom (batch)"""
    student_ids: List[PositiveInt] = Field(..., description="学生ID列表")
    
    
class RemoveStudentRequest(BaseModel):
    """Request to remove student from classroom"""
    student_id: PositiveInt = Field(..., description="学生ID")


class ClassroomStatistics(BaseModel):
    """Classroom statistics"""
    total_students: int
    active_students: int
    completed_courses: int
    average_score: float
    attendance_rate: float


class ClassroomDetailResponse(BaseModel):
    """Classroom detail response schema for API"""
    id: int
    name: str
    description: Optional[str] = None
    teacher_id: int
    start_date: datetime
    end_date: datetime
    credit: Optional[int] = None
    cover_url: Optional[str] = None
    status: str = "ongoing"
    student_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Pydantic V2 (orm_mode in V1)