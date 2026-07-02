from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field

# School schemas
class SchoolBase(BaseModel):
    name: str = Field(..., description="学校名称")
    short_name: Optional[str] = Field(None, description="学校简称")
    motto: Optional[str] = Field(None, description="校训")
    code: Optional[str] = Field(None, description="学校编码")
    description: Optional[str] = Field(None, description="学校描述")

class SchoolCreate(SchoolBase):
    pass

class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    motto: Optional[str] = None
    description: Optional[str] = None

class SchoolResponse(SchoolBase):
    id: int
    logo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# College schemas
class CollegeBase(BaseModel):
    name: str = Field(..., description="学院名称")
    code: str = Field(..., description="学院编码")
    description: Optional[str] = Field(None, description="学院描述")
    principal: Optional[str] = Field(None, description="负责人")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    contact_email: Optional[str] = Field(None, description="联系邮箱")

class CollegeCreate(CollegeBase):
    school_id: int

class CollegeUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    principal: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

class CollegeResponse(CollegeBase):
    id: int
    school_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Major schemas
class MajorBase(BaseModel):
    name: str = Field(..., description="专业名称")
    code: str = Field(..., description="专业编码")
    description: Optional[str] = Field(None, description="专业描述")
    principal: Optional[str] = Field(None, description="负责人")
    degree_type: Optional[str] = Field(None, description="学位类型")

class MajorCreate(MajorBase):
    college_id: int

class MajorUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    principal: Optional[str] = None
    degree_type: Optional[str] = None

class MajorResponse(MajorBase):
    id: int
    college_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Grade schemas
class GradeBase(BaseModel):
    year: int = Field(..., description="入学年份")
    name: Optional[str] = Field(None, description="年级名称")

class GradeCreate(GradeBase):
    major_id: int

class GradeUpdate(BaseModel):
    year: Optional[int] = None
    name: Optional[str] = None

class GradeResponse(GradeBase):
    id: int
    major_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Class schemas
class ClassBase(BaseModel):
    name: str = Field(..., description="班级名称")
    code: str = Field(..., description="班级编码")
    class_teacher: Optional[str] = Field(None, description="班主任")

class ClassCreate(ClassBase):
    grade_id: int

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    class_teacher: Optional[str] = None

class ClassResponse(ClassBase):
    id: int
    grade_id: int
    student_count: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Teacher schemas
class TeacherBase(BaseModel):
    job_number: str = Field(..., description="工号")
    name: str = Field(..., description="姓名")
    gender: Optional[str] = Field(None, description="性别")
    phone: Optional[str] = Field(None, description="联系电话")
    email: Optional[str] = Field(None, description="邮箱")
    id_card: Optional[str] = Field(None, description="身份证号")
    title: Optional[str] = Field(None, description="职称")
    department: Optional[str] = Field(None, description="部门")

class TeacherCreate(TeacherBase):
    school_id: int
    college_id: Optional[int] = None
    birth_date: Optional[datetime] = None
    hire_date: Optional[datetime] = None

class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    id_card: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    college_id: Optional[int] = None
    birth_date: Optional[datetime] = None
    hire_date: Optional[datetime] = None

class TeacherResponse(TeacherBase):
    id: int
    school_id: Optional[int] = None
    college_id: Optional[int] = None
    birth_date: Optional[datetime] = None
    hire_date: Optional[datetime] = None
    is_admin: Optional[bool] = False
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Student schemas
class StudentBase(BaseModel):
    student_number: str = Field(..., description="学号")
    name: str = Field(..., description="姓名")
    gender: Optional[str] = Field(None, description="性别")
    phone: Optional[str] = Field(None, description="联系电话")
    email: Optional[str] = Field(None, description="邮箱")
    id_card: Optional[str] = Field(None, description="身份证号")
    entrance_year: Optional[int] = Field(None, description="入学年份")
    graduation_year: Optional[int] = Field(None, description="毕业年份")
    student_status: Optional[str] = Field("在校", description="学籍状态")

class StudentCreate(StudentBase):
    school_id: int
    college_id: Optional[int] = None
    major_id: Optional[int] = None
    grade_id: Optional[int] = None
    class_id: Optional[int] = None
    birth_date: Optional[datetime] = None

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    id_card: Optional[str] = None
    college_id: Optional[int] = None
    major_id: Optional[int] = None
    grade_id: Optional[int] = None
    class_id: Optional[int] = None
    entrance_year: Optional[int] = None
    graduation_year: Optional[int] = None
    student_status: Optional[str] = None
    birth_date: Optional[datetime] = None

class StudentResponse(StudentBase):
    id: int
    school_id: Optional[int] = None
    college_id: Optional[int] = None
    major_id: Optional[int] = None
    grade_id: Optional[int] = None
    class_id: Optional[int] = None
    birth_date: Optional[datetime] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Organization tree schemas
class OrganizationTreeNode(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    type: str  # school, college, major, grade, class
    parent_id: Optional[int] = None
    is_active: bool
    has_children: bool
    children: List['OrganizationTreeNode'] = []

    class Config:
        from_attributes = True

# Batch operation schemas
class BatchStatusUpdate(BaseModel):
    ids: List[int]
    is_active: bool

class BatchDelete(BaseModel):
    ids: List[int]

class BatchTransfer(BaseModel):
    user_ids: List[int]
    target_organization_id: int
    target_type: str  # college, major, grade, class

# Import schemas
class ImportResult(BaseModel):
    success_count: int
    error_count: int
    errors: List[dict] = []
    file_url: Optional[str] = None

class AdminAuth(BaseModel):
    teacher_ids: List[int]

# Response schemas
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int

# Update the forward reference
OrganizationTreeNode.model_rebuild() 