from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from datetime import datetime, date

# Import enums
from app.core.enums import (
    TrainingTypeEnum,
    TrainingPublishStatusEnum,
    TrainingVisibilityEnum,
    DifficultyLevelEnum,
    UserTypeEnum,
    RoleEnum,
    UserStatusEnum,
    OrganizationTypeEnum,
    CourseTypeEnum,
    ResourceTypeEnum,
    RequestStatusEnum,
    RequestTypeEnum,
    HomeworkStatusEnum,
    SubmissionStatusEnum,
    TimeRangeEnum,
    UserGroupEnum,
)

# Import from other schema files to re-export
from .classroom_schemas import *

# ==================== Basic Schemas ====================

class ApiResponse(BaseModel):
    code: str
    message: str
    data: Optional[Any] = None
    trace_id: Optional[str] = ""

class MessageResponse(BaseModel):
    message: str

# ==================== Token Schemas ====================

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# ==================== User Schemas ====================

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_superuser: bool = False
    
    class Config:
        from_attributes = True

# ==================== Post Schemas (Fix for crash) ====================

class PostBase(BaseModel):
    title: str
    content: Optional[str] = None

class PostCreate(PostBase):
    author_id: int

class PostUpdate(PostBase):
    pass

class Post(PostBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ==================== Training Schemas ====================

class TrainingBase(BaseModel):
    title: str
    description: Optional[str] = None

class TrainingSubmissionRequest(BaseModel):
    # BI Training fields
    snapshot_json: Optional[Any] = None
    notes: Optional[str] = None
    
    # Coding/Jupyter Training fields
    submission_type: Optional[str] = None
    notebook_content: Optional[str] = None
    project_files: Optional[List[str]] = None
    summary: Optional[str] = None
    
    class Config:
        extra = "allow"

class TrainingSubmissionResponse(BaseModel):
    id: int
    status: str
    submission_time: str
    
class TrainingCreateRequest(BaseModel):
    title: str
    training_type: TrainingTypeEnum
    description: Optional[str] = None
    intro: Optional[str] = None
    industry: Optional[str] = None
    difficulty: Optional[str] = None
    course_hours: Optional[int] = None
    handbook_content: Optional[str] = None
    assignment_nodes: Optional[List[Any]] = None
    require_design_files: Optional[bool] = False
    require_experiment_report: Optional[bool] = False
    environment_id: Optional[str] = None
    environment_config: Optional[Dict] = None

class TrainingUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    training_type: Optional[str] = None
    intro: Optional[str] = None
    industry: Optional[str] = None
    difficulty: Optional[str] = None
    course_hours: Optional[int] = None
    handbook_content: Optional[str] = None
    assignment_nodes: Optional[List[Any]] = None
    require_design_files: Optional[bool] = None
    require_experiment_report: Optional[bool] = None
    environment_id: Optional[str] = None
    environment_config: Optional[Dict] = None

class AddTrainingToClassroomRequest(BaseModel):
    training_ids: List[int]

class AddTrainingToClassroomFromLibraryRequest(BaseModel):
    start_time: str
    end_time: str
    allow_late_submission: Optional[bool] = False
    late_submission_days: Optional[int] = 0
    source_type: Optional[str] = "training"  # 'training' | 'practice' (XQ01 类项目实训)

class TrainingVersionData(BaseModel):
    version_name: str
    description: Optional[str] = None

class TrainingPublishRequest(BaseModel):
    status: TrainingPublishStatusEnum

class TrainingReviewRequest(BaseModel):
    comment: Optional[str] = None

class TrainingStatusUpdateRequest(BaseModel):
    status: str

class TrainingResponse(TrainingBase):
    id: int
    class Config:
        from_attributes = True

# ==================== Practice Schemas ====================

class PracticeSkillResponse(BaseModel):
    """技能标签响应"""
    id: int
    skill_name: str
    
    class Config:
        from_attributes = True

class TaskSimpleResponse(BaseModel):
    """任务简单响应（用于列表展示）"""
    id: int
    title: str
    order_in_practice: Optional[int] = 0
    coin: Optional[int] = 0
    difficulty: Optional[str] = None
    task_type: Optional[str] = None
    
    class Config:
        from_attributes = True

class PracticeBase(BaseModel):
    title: str
    description: Optional[str] = None

class PracticeResponse(PracticeBase):
    id: int
    task_count: Optional[int] = 0
    stage_count: Optional[int] = 0  # alias for task_count for frontend compatibility

    class Config:
        from_attributes = True

    @root_validator(pre=False, skip_on_failure=True)
    def set_stage_count_from_task_count(cls, values):
        # 设置 stage_count 为 task_count 的别名
        task_count = values.get('task_count', 0) or 0
        if not values.get('stage_count'):
            values['stage_count'] = task_count
        return values

class PracticeDetailResponse(PracticeResponse):
    """实践详情响应 - 包含任务列表和技能标签"""
    tasks: List[TaskSimpleResponse] = []
    skills: List[PracticeSkillResponse] = []
    coin: Optional[int] = 0
    difficulty: Optional[str] = None
    direction: Optional[str] = None
    category: Optional[str] = None
    
    class Config:
        from_attributes = True

class AddPracticeToClassroomRequest(BaseModel):
    practice_ids: List[int]

class CustomPracticeCreateRequest(BaseModel):
    title: str

class CustomPracticeUpdateRequest(BaseModel):
    title: Optional[str] = None

class PracticeStageCreateRequest(BaseModel):
    name: str

class PracticeCodeRepositoryBase(BaseModel):
    repo_url: str

class PracticeConfigBase(BaseModel):
    config: Dict

class PracticePublishRequest(BaseModel):
    status: str

class PracticeStatusUpdateRequest(BaseModel):
    status: str

# ==================== Challenge/Task Schemas ====================

class TaskBase(BaseModel):
    title: str

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: str
    class Config:
        from_attributes = True

class TaskEvaluationRequest(BaseModel):
    answer: Optional[str] = None
    code: Optional[str] = None
    repo_hash: Optional[str] = None
    codeRepoHash: Optional[str] = None  # Alternate field name
    files: Optional[Dict[str, str]] = None
    class Config:
        extra = "allow"

class CodeSnapshotRequest(BaseModel):
    repo_hash: Optional[str] = None
    files: Optional[Dict[str, str]] = None
    class Config:
        extra = "allow"

# ==================== Classroom Helper Schemas ====================

class ClassroomCardResponse(BaseModel):
    """课堂卡片响应模型"""
    id: int
    name: str
    description: Optional[str] = None
    status: str
    teacher_id: int
    teacher_name: Optional[str] = None
    teacher_avatar: Optional[str] = None
    credit: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    semester: Optional[str] = None
    academic_year: Optional[str] = None
    student_count: Optional[int] = 0
    cover_url: Optional[str] = None
    created_at: Optional[datetime] = None
    # 统计字段
    total_courses: Optional[int] = 0
    completed_courses: Optional[int] = 0
    average_progress: Optional[float] = 0.0
    
    class Config:
        from_attributes = True

class ClassroomsByStatusResponse(BaseModel):
    ongoing: List[ClassroomCardResponse]
    upcoming: List[ClassroomCardResponse]
    ended: List[ClassroomCardResponse]
    total_count: Optional[int] = 0
    ongoing_count: Optional[int] = 0
    upcoming_count: Optional[int] = 0
    ended_count: Optional[int] = 0

class ClassroomDetailEnhancedResponse(ClassroomInDB):
    source_course_id: Optional[int] = None
    credit: Optional[float] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    status_cn: Optional[str] = None
    teacher_name: Optional[str] = None
    teacher_avatar: Optional[str] = None
    sync_resources_from_source: bool = False
    sync_assessments_from_source: bool = False
    deleted_at: Optional[datetime] = None
    course_list: List[Any] = []
    practice_list: List[Dict[str, Any]] = []
    # Statistics fields
    total_students: Optional[int] = 0
    active_students: Optional[int] = 0
    completed_courses: Optional[int] = 0
    average_score: Optional[float] = 0.0
    attendance_rate: Optional[float] = 0.0
    
    class Config:
        from_attributes = True

# ==================== Course Operation Schemas ====================

class CourseBatchOperationRequest(BaseModel):
    course_ids: List[int]
    operation: Optional[str] = "publish"
    deadline_at: Optional[str] = None
    is_mandatory: Optional[bool] = True

class AddCoursesByTimetableRequest(BaseModel):
    timetable_url: Optional[str] = None
    file_url: Optional[str] = None
    classroom_id: int
    source_course_id: Optional[int] = None
    selected_modules: Optional[List[Dict[str, Any]]] = None

class AddPracticeCoursesRequest(BaseModel):
    course_ids: List[int]
    chapter_id: Optional[int] = None

class AddTrainingCoursesRequest(BaseModel):
    course_ids: List[int]
    chapter_id: Optional[int] = None

class CourseOrderItem(BaseModel):
    course_id: int
    order_index: int

class CourseOrderRequest(BaseModel):
    orders: List[CourseOrderItem]

class AddStudentsRequest(BaseModel):
    student_ids: List[int]

class RemoveStudentsRequest(BaseModel):
    student_ids: List[int]

class ExcellentWorkRequest(BaseModel):
    is_excellent: bool

class PenaltyUpdateRequest(BaseModel):
    late_submission_deduction_points: int

class BatchPenaltyUpdateRequest(BaseModel):
    course_ids: List[int]
    late_submission_deduction_points: int

class TrainingGradingRequest(BaseModel):
    score: int
    feedback: Optional[str] = None
    is_excellent: Optional[bool] = False
    comment: Optional[str] = None


# ==================== Grading Schemas ====================

class SubmitGradeRequest(BaseModel):
    student_id: int
    overall_score: float
    teacher_penalties: Optional[float] = 0
    teacher_feedback: Optional[str] = ""
    is_excellent_work: Optional[bool] = False

# ==================== Course Publish & Settings Schemas ====================

class CoursePublishSettings(BaseModel):
    deadline_at: datetime
    is_mandatory: Optional[bool] = True
    allow_late_submission: Optional[bool] = False
    late_submission_deduction_points: Optional[int] = 0
    total_score: Optional[float] = 100.0
    publicize_grades: Optional[bool] = True
    publicize_answers_after_completion: Optional[bool] = False

class PublishBatchCoursesRequest(BaseModel):
    course_ids: List[int]
    settings: CoursePublishSettings

class PublishChapterCoursesRequest(BaseModel):
    chapter_title: str
    settings: CoursePublishSettings

class PublishAllCoursesRequest(BaseModel):
    settings: CoursePublishSettings

class CourseSettingsUpdate(BaseModel):
    deadline_at: Optional[datetime] = None
    is_mandatory: Optional[bool] = None
    allow_late_submission: Optional[bool] = None
    late_submission_deduction_points: Optional[int] = None
    total_score: Optional[float] = None
    publicize_grades: Optional[bool] = None
    publicize_answers_after_completion: Optional[bool] = None

class AssignmentFile(BaseModel):
    file_url: str
    file_name: str
    file_size: Optional[int] = 0

class AssignmentSubmissionRequest(BaseModel):
    design_files: List[AssignmentFile] = []
    experiment_reports: List[AssignmentFile] = []
    notes: Optional[str] = None

class CourseSelectionResponse(BaseModel):
    id: int
    title: str
    cover_url: Optional[str] = None
    direction: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    description: Optional[str] = None
    course_type: Optional[str] = None

    @property
    def difficulty_text(self) -> str:
        """返回难度的中文文本"""
        difficulty_map = {
            'beginner': '初级',
            'easy': '初级',
            'intermediate': '中级',
            'medium': '中级',
            'advanced': '高级',
            'hard': '高级'
        }
        return difficulty_map.get(self.difficulty, self.difficulty or '未知')

    @property
    def type_text(self) -> str:
        """返回课程类型的中文文本"""
        type_map = {
            'PRACTICE': '实践课程',
            'practice': '实践课程',
            'TRAINING': '实训课程',
            'training': '实训课程',
            'COURSE_MATERIAL': '课程资料',
            'course_material': '课程资料'
        }
        return type_map.get(self.course_type, self.course_type or '课程')

    def model_dump(self, **kwargs):
        """覆盖 model_dump 以包含计算字段"""
        data = super().model_dump(**kwargs)
        data['difficulty_text'] = self.difficulty_text
        data['type_text'] = self.type_text
        return data

    class Config:
        from_attributes = True

class CourseResponse(CourseSelectionResponse):
    pass

class CourseDetailResponse(CourseResponse):
    description: Optional[str] = None
    resources: Optional[List[Dict[str, Any]]] = None
    practices: Optional[List[Dict[str, Any]]] = None
    chapters: Optional[List[Dict[str, Any]]] = None
    assignments: Optional[List[Dict[str, Any]]] = None
    assessments: Optional[List[Dict[str, Any]]] = None
    
class CourseAssessmentResponse(BaseModel):
    id: int
    title: str
    url: Optional[str] = None
    assessment_type: Optional[str] = None

    class Config:
        from_attributes = True

class ClassroomCourseResponse(BaseModel):
    id: int
    course_id: int
    classroom_id: int
    teacher_id: Optional[int] = None
    deadline_at: Optional[datetime] = None
    is_mandatory: bool = True
    status: str = "UNPUBLISHED"
    teacher_publish_status: Optional[Any] = None
    
    class Config:
        from_attributes = True

class ClassroomCourseDetailResponse(BaseModel):
    id: int
    course_id: Optional[int] = None  # 可为空（实践课程使用practice_id）
    practice_id: Optional[int] = None  # 实践课程ID
    classroom_id: int
    teacher_id: Optional[int] = None
    deadline_at: Optional[datetime] = None
    is_mandatory: bool = True
    status: str = "UNPUBLISHED"
    teacher_publish_status: Optional[Any] = None
    source_type: Optional[str] = None  # "course" 或 "practice"

    # Course info
    course_name: Optional[str] = None
    course_cover: Optional[str] = None
    
    # Statistics
    student_count: Optional[int] = 0
    not_started_count: Optional[int] = 0
    learning_count: Optional[int] = 0
    completed_count: Optional[int] = 0
    studentCount: Optional[int] = 0
    notStartedCount: Optional[int] = 0
    learningCount: Optional[int] = 0
    completedCount: Optional[int] = 0
    status_cn: Optional[str] = None
    remaining_days: Optional[int] = None
    is_overdue: Optional[bool] = False
    classroom_chapter_title: Optional[str] = None
    
    class Config:
        from_attributes = True

class ClassroomChapterResponse(BaseModel):
    id: int
    title: str
    order_index: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CourseManagementStatsResponse(BaseModel):
    total_courses: int
    total_requests: int
    pending_requests: int
    published_courses: int

# ==================== Stage Schemas ====================

class StageTaskEditRequest(BaseModel):
    title: str
    description: Optional[str] = None
    class Config:
        extra = "allow"

class StageTaskSettingsRequest(BaseModel):
    class Config:
        extra = "allow"

class StageTestCasesRequest(BaseModel):
    test_cases: List[Dict[str, Any]]

class TaskTestResponse(BaseModel):
    id: Optional[int] = None
    input: Optional[str] = None
    output: Optional[str] = None
    class Config:
        from_attributes = True
        extra = "allow"

class StageAnswerRequest(BaseModel):
    class Config:
        extra = "allow"

class StageCreateCompleteRequest(BaseModel):
    title: str
    description: Optional[str] = None
    class Config:
        extra = "allow"

class StageResponse(BaseModel):
    id: int
    title: str
    class Config:
        from_attributes = True
        extra = "allow"

class StageUpdateRequest(BaseModel):
    class Config:
        extra = "allow"

class BatchStageDeleteRequest(BaseModel):
    stage_ids: List[int]

class StageOrderItem(BaseModel):
    stage_id: int
    order_index: int

class StageOrderUpdateRequest(BaseModel):
    stage_orders: List[StageOrderItem]

class StageQuestionTaskSettingsRequest(BaseModel):
    class Config:
        extra = "allow"

class StageQuestionCreateCompleteRequest(BaseModel):
    class Config:
        extra = "allow"

class StageSandboxTestRequest(BaseModel):
    class Config:
        extra = "allow"

class StageSandboxTestResponse(BaseModel):
    class Config:
        extra = "allow"

class StageDeleteValidationResponse(BaseModel):
    can_delete: bool
    reason: Optional[str] = None
    class Config:
        extra = "allow"

class ApplyTemplateRequest(BaseModel):
    template_id: int
    customize_data: Optional[Dict[str, Any]] = None

# ==================== Exam Schemas ====================

class ExamCreateRequest(BaseModel):
    title: str
    test_paper_id: int

class ExamPublishRequest(BaseModel):
    exam_start_time: Optional[datetime] = None
    exam_end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    pass_mark: Optional[float] = None
    shuffle_questions: Optional[bool] = False
    shuffle_options: Optional[bool] = False

class ExamUpdateRequest(BaseModel):
    title: Optional[str] = None
    exam_start_time: Optional[datetime] = None
    exam_end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    pass_mark: Optional[float] = None
    shuffle_questions: Optional[bool] = None
    shuffle_options: Optional[bool] = None
    class Config:
        extra = "allow"

class ExamRenameRequest(BaseModel):
    title: str

class ExamPaperDetail(BaseModel):
    code: str = "0000"
    message: str = "success"
    data: Dict[str, Any]

class MarkItem(BaseModel):
    question_id: int
    score: float
    comment: Optional[str] = None

class SubmitMarksRequest(BaseModel):
    marks: List[MarkItem]
    overall_comments: Optional[str] = None

class EnhancedSubmitMarksResponse(BaseModel):
    code: str = "0000"
    message: str = "success"
    data: Dict[str, Any]

class GradingProgressResponse(BaseModel):
    code: str = "0000"
    message: str = "success"
    data: Dict[str, Any]

class ExamStatistics(BaseModel):
    code: str = "0000"
    message: str = "success"
    data: Dict[str, Any]

class BatchAutoGradeResponse(BaseModel):
    code: str = "0000"
    message: str = "success"
    data: Dict[str, Any]

class ScoreRangeItem(BaseModel):
    min_score: float
    max_score: float
    label: Optional[str] = None
    color: Optional[str] = None

class UpdateScoreRangesRequest(BaseModel):
    ranges: List[ScoreRangeItem]
    enable_custom_labels: bool = False
    
# ==================== Resource Schemas ====================

class CloudFilesBatchRequest(BaseModel):
    action: str
    file_ids: List[int]

class CourseResourceResponse(BaseModel):
    id: int
    title: str
    url: str
    resource_type: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ExportAnalyticsRequest(BaseModel):
    course_type: str
    export_format: str
    selected_student_ids: Optional[List[int]] = None

# ==================== Session/Environment Schemas ====================

class FontSizeRequest(BaseModel):
    size: int

class ResetFileRequest(BaseModel):
    path: str

class TogglePreviewRequest(BaseModel):
    enabled: bool

class PreviewSizeRequest(BaseModel):
    width: int
    height: int

class ClipboardRequest(BaseModel):
    content: str

class FullscreenRequest(BaseModel):
    enabled: bool

class TrainingSessionCreateRequest(BaseModel):
    classroom_training_id: int
    student_id: int

class TrainingProgressUpdateRequest(BaseModel):
    progress_percentage: float
    current_step: Optional[str] = None
    completed_tasks: Optional[List[str]] = None

# ==================== Excellent Works Schemas ====================

class LikeRequest(BaseModel):
    action: str  # 'like' or 'unlike'

class FavoriteRequest(BaseModel):
    action: str  # 'favorite' or 'unfavorite'

# ==================== Paper Library Schemas ====================

class PaperCreateRequest(BaseModel):
    title: str
    direction: Optional[str] = None
    difficulty: Optional[str] = None
    composition_method: Optional[str] = None
    description: Optional[str] = None
    
class PaperCopyRequest(BaseModel):
    new_title: str

class PaperUpdateRequest(BaseModel):
    title: Optional[str] = None
    direction: Optional[str] = None
    difficulty: Optional[str] = None
    description: Optional[str] = None

class CreateExamFromPaperRequest(BaseModel):
    exam_title: str
    classroom_id: int

class PaperExportRequest(BaseModel):
    format: str
    include_answers: bool = False

class PaperTemplateCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    direction: Optional[str] = None
    question_configs: List[Dict[str, Any]]
    class Config:
        extra = "allow"

class TemplateCompositionRequest(BaseModel):
    template_id: int
    paper_title: str
    description: Optional[str] = None
    difficulty: Optional[str] = None
    direction: Optional[str] = None
    source: Optional[str] = None

class PaperQuestionAddRequest(BaseModel):
    question_ids: List[int]
    scores: Optional[Dict[str, float]] = None

class PaperQuestionRemoveRequest(BaseModel):
    question_ids: List[int]

class PaperQuestionUpdateRequest(BaseModel):
    score: Optional[float] = None
    order_index: Optional[int] = None

class PaperQuestionScoreUpdateRequest(BaseModel):
    score: float

class PaperBatchScoreUpdateRequest(BaseModel):
    question_type: str
    score_per_question: float

class PaperQuestionOrderUpdateRequest(BaseModel):
    question_orders: List[Dict[str, int]]

class PaperSectionOrderUpdateRequest(BaseModel):
    section_orders: List[Dict[str, int]]

class PaperBasicInfoUpdateRequest(BaseModel):
    title: Optional[str] = None
    direction: Optional[str] = None
    difficulty: Optional[str] = None
    description: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    
# ==================== Question Library Schemas ====================

class QuestionCreateRequest(BaseModel):
    content: str
    question_type: str
    options: Optional[List[Dict[str, Any]]] = None
    correct_answers: Optional[List[str]] = None
    explanation: Optional[str] = None
    difficulty: Optional[str] = None
    direction: Optional[str] = None
    category: Optional[str] = None
    score: Optional[float] = None
    class Config:
        extra = "allow"

class QuestionUpdateRequest(BaseModel):
    content: Optional[str] = None
    options: Optional[List[Dict[str, Any]]] = None
    correct_answers: Optional[List[str]] = None
    explanation: Optional[str] = None
    difficulty: Optional[str] = None
    direction: Optional[str] = None
    category: Optional[str] = None
    score: Optional[float] = None
    class Config:
        extra = "allow"

class QuestionBatchDeleteRequest(BaseModel):
    question_ids: List[int]

# ==================== Organization Schemas ====================

class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int

class SchoolCreate(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None

class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None

class SchoolResponse(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class LogoUploadRequest(BaseModel):
    file_url: str

class LogoUploadResponse(BaseModel):
    logo_url: str
    message: str

class OrganizationCreate(BaseModel):
    name: str
    school_id: int
    org_type: str
    parent_id: Optional[int] = None
    code: Optional[str] = None
    order_index: Optional[int] = 0

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    order_index: Optional[int] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None

class OrganizationSearchRequest(BaseModel):
    keyword: Optional[str] = None
    org_type: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    page: int = 1
    page_size: int = 20

class OrganizationResponse(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    org_type: str
    level: int
    is_active: bool
    parent_id: Optional[int] = None
    school_id: int
    children_count: Optional[int] = 0
    user_count: Optional[int] = 0
    class Config:
        from_attributes = True

class OrganizationListResponse(BaseModel):
    list: List[OrganizationResponse]
    meta: PaginationMeta

class OrganizationTreeNode(BaseModel):
    id: int
    label: str
    org_type: str
    children: Optional[List['OrganizationTreeNode']] = None
    class Config:
        from_attributes = True

class OrganizationSelectorNode(BaseModel):
    id: int
    name: str
    org_type: OrganizationTypeEnum
    level: int
    selectable: bool
    children: Optional[List['OrganizationSelectorNode']] = None

class OrganizationSelectorResponse(BaseModel):
    tree: List[OrganizationSelectorNode]

class OrganizationStatsResponse(BaseModel):
    total_organizations: int
    organization_types: Dict[str, int]
    active_organizations: int
    inactive_organizations: int

class UserStatsResponse(BaseModel):
    total_users: int
    user_types: Dict[str, int]
    active_users: int
    inactive_users: int

class UserProfileCreate(BaseModel):
    user_id: int
    school_id: int
    organization_id: Optional[int] = None
    user_type: str
    real_name: str
    employee_id: str
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    id_card: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    research_direction: Optional[str] = None
    admission_year: Optional[int] = None
    graduation_year: Optional[int] = None
    student_status: Optional[str] = None

class UserProfileUpdate(BaseModel):
    organization_id: Optional[int] = None
    real_name: Optional[str] = None
    employee_id: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    id_card: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    research_direction: Optional[str] = None
    admission_year: Optional[int] = None
    graduation_year: Optional[int] = None
    student_status: Optional[str] = None
    status: Optional[str] = None

class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    school_id: int
    organization_id: Optional[int] = None
    user_type: str
    real_name: str
    employee_id: str
    gender: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    admission_year: Optional[int] = None
    graduation_year: Optional[int] = None
    student_status: Optional[str] = None
    status: str
    is_admin: bool
    last_login_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class TeacherCreate(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    real_name: str
    employee_id: str
    organization_id: Optional[int] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    id_card: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    research_direction: Optional[str] = None

class TeacherUpdate(BaseModel):
    full_name: Optional[str] = None
    real_name: Optional[str] = None
    organization_id: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    research_direction: Optional[str] = None

class TeacherResponse(UserProfileResponse):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    organization_name: Optional[str] = None

class TeacherListResponse(BaseModel):
    list: List[TeacherResponse]
    meta: PaginationMeta
    
class StudentCreate(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    real_name: str
    employee_id: str
    organization_id: Optional[int] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    id_card: Optional[str] = None
    phone: Optional[str] = None
    admission_year: Optional[int] = None
    graduation_year: Optional[int] = None
    student_status: Optional[str] = None

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    real_name: Optional[str] = None
    organization_id: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    student_status: Optional[str] = None

class StudentResponse(UserProfileResponse):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    organization_name: Optional[str] = None

class StudentListResponse(BaseModel):
    list: List[StudentResponse]
    meta: PaginationMeta
    
class UserSearchRequest(BaseModel):
    keyword: Optional[str] = None
    user_type: Optional[UserTypeEnum] = None
    organization_id: Optional[int] = None
    status: Optional[UserStatusEnum] = None
    page: int = 1
    page_size: int = 20

class AdminRoleCreate(BaseModel):
    user_id: int
    school_id: int

class AdminRoleResponse(BaseModel):
    id: int
    user_id: int
    school_id: int
    user_name: str
    user_real_name: str
    created_at: datetime
    class Config:
        from_attributes = True

class AdminRoleListResponse(BaseModel):
    list: List[AdminRoleResponse]
    meta: PaginationMeta
    
class BatchOperationRequest(BaseModel):
    action: str  # enable, disable, delete
    ids: List[int]

class BatchDeleteRequest(BaseModel):
    ids: List[int]

class BatchTransferRequest(BaseModel):
    user_ids: List[int]
    target_organization_id: int
    transfer_reason: Optional[str] = None

class ImportRequest(BaseModel):
    file_name: str
    file_url: str

class ImportResponse(BaseModel):
    import_id: int
    status: str
    message: str

class ImportResultResponse(BaseModel):
    id: int
    status: str
    total_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    error_log_url: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class ExportStatisticsRequest(BaseModel):
    export_type: str  # course, practice, training, teacher, student
    export_format: str = "xlsx"  # xlsx, csv
    time_range: TimeRangeEnum = TimeRangeEnum.TODAY
    user_group: Optional[UserGroupEnum] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    course_name: Optional[str] = None
    practice_name: Optional[str] = None
    training_name: Optional[str] = None
    name: Optional[str] = None
    employee_id: Optional[str] = None
    student_id: Optional[str] = None
    college: Optional[str] = None
    major: Optional[str] = None

# ==================== Teaching Resource Schemas ====================

class TeachingResourceFile(BaseModel):
    id: int
    name: str
    url: str
    file_type: str
    file_size: Optional[int] = 0
    duration_seconds: Optional[int] = 0
    uploader_name: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class TeachingResourceModule(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    order_index: int
    files: List[TeachingResourceFile] = []
    class Config:
        from_attributes = True

class TeachingResourceModuleCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

class TeachingResourceModuleCreateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    order_index: int
    created_at: datetime
    class Config:
        from_attributes = True

class TeachingResourceFileCreateRequest(BaseModel):
    name: str
    url: str
    file_type: str
    file_size: Optional[int] = 0
    duration_seconds: Optional[int] = 0

class TeachingResourceFileCreateResponse(BaseModel):
    id: int
    name: str
    url: str
    file_type: str
    class Config:
        from_attributes = True

class LearningRecordCreateRequest(BaseModel):
    learning_duration_seconds: int = 0
    last_position: Optional[int] = 0
    is_completed: Optional[bool] = False

class LearningRecordResponse(BaseModel):
    id: int
    learning_duration_seconds: int
    last_position: int
    is_completed: bool
    last_access_at: datetime
    class Config:
        from_attributes = True

# Aliases
ClassroomUpdateRequest = ClassroomUpdate
PostResponse = Post

# ==================== Environment Schemas ====================

class ExtendTimeRequest(BaseModel):
    """延时请求"""
    minutes: int = Field(default=30, description="延长时间（分钟）")
