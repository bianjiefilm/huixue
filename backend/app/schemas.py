

# ==================== P3 成绩系统 Schemas ====================

class SubmitGradeRequest(BaseModel):
    """
    提交成绩请求
    """
    student_id: int = Field(..., description="学生ID")
    overall_score: float = Field(..., ge=0, le=100, description="总分")
    teacher_penalties: Optional[float] = Field(0, ge=0, le=100, description="教师扣分")
    teacher_feedback: Optional[str] = Field("", description="教师反馈")
    is_excellent_work: Optional[bool] = Field(False, description="是否优秀作业")
    
    class Config:
        schema_extra = {
            "example": {
                "student_id": 10,
                "overall_score": 85,
                "teacher_penalties": 5,
                "teacher_feedback": "代码规范性好，但逻辑有误。",
                "is_excellent_work": False
            }
        }


class GradeResponse(BaseModel):
    """
    成绩响应
    """
    overall_score: Optional[float]
    teacher_feedback: Optional[str]
    graded_at: Optional[str]
    status: str
    is_required: bool


class StudentGradesResponse(BaseModel):
    """
    学生成绩单响应
    """
    classroom_name: str
    courses: List[GradeResponse]
    class_average: Optional[float]
    student_rank: int


class CourseStatResponse(BaseModel):
    """
    课程统计响应
    """
    course_name: str
    completion_rate: float
    average_score: float


class AnalyticsOverviewResponse(BaseModel):
    """
    学情分析总览响应
    """
    completion_by_course: List[Dict[str, Any]]
    average_scores: List[Dict[str, Any]]
    top_performers: List[Dict[str, Any]]
    struggling_students: List[Dict[str, Any]]

