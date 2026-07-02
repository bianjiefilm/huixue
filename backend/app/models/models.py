from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum, ARRAY, UniqueConstraint, Float, LargeBinary, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import uuid
from app.core.database import Base
# ML 工作流模型

# 枚举类型定义 - 匹配数据库中的实际枚举
class DifficultyEnum(enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"

class DifficultyLevelEnum(enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class CourseTypeEnum(enum.Enum):
    COURSE_MATERIAL = "COURSE_MATERIAL"
    PRACTICE = "PRACTICE"
    TRAINING = "TRAINING"

class CourseVisibilityEnum(enum.Enum):
    PRIVATE = "PRIVATE"
    PUBLIC_SELF = "PUBLIC_SELF"
    PUBLIC_PLATFORM = "PUBLIC_PLATFORM"

# 考试状态枚举
class ExamStatusEnum(enum.Enum):
    UNPUBLISHED = "UNPUBLISHED"  # 未发布
    SCHEDULED = "SCHEDULED"      # 已安排
    ONGOING = "ONGOING"          # 进行中
    GRADING = "GRADING"          # 阅卷中
    COMPLETED = "COMPLETED"      # 已完成

# 题目类型枚举
class QuestionTypeEnum(enum.Enum):
    SINGLE_CHOICE = "SINGLE_CHOICE"    # 单选题
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE" # 多选题
    TRUE_FALSE = "TRUE_FALSE"          # 判断题
    SHORT_ANSWER = "SHORT_ANSWER"      # 简答题

# 任务类型枚举 - 匹配数据库中的实际枚举值
class TaskTypeEnum(enum.Enum):
    PRACTICE = "PRACTICE"
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE = "TRUE_FALSE"
    CODE = "CODE"  # 代码练习题
    SHORT_ANSWER = "SHORT_ANSWER"  # 简答题
    FILL_BLANK = "FILL_BLANK"  # 填空题

# 任务状态枚举
class TaskStatusEnum(enum.Enum):
    NOT_STARTED = "未开始"
    IN_PROGRESS = "进行中"
    COMPLETED = "已完成"

# 课程在课堂中的教师端状态枚举
class CourseInClassroomStatusTeacherEnum(enum.Enum):
    UNPUBLISHED = "UNPUBLISHED"  # 未发布
    LEARNING = "LEARNING"        # 学习中
    MAKEUP = "MAKEUP"           # 补交中
    COMPLETED = "COMPLETED"     # 已完成

# 课程在课堂中的学生端状态枚举
class CourseInClassroomStatusStudentEnum(enum.Enum):
    NOT_YET_PUBLISHED = "NOT_YET_PUBLISHED"  # 未发布（学生看不到）
    NOT_STARTED = "NOT_STARTED"              # 未开始
    LEARNING = "LEARNING"                    # 学习中
    PENDING_MAKEUP = "PENDING_MAKEUP"        # 待补交
    COMPLETED_ON_TIME = "COMPLETED_ON_TIME"  # 按时完成
    COMPLETED_LATE = "COMPLETED_LATE"        # 补交完成

# 实训课程提交状态枚举
class SubmissionStatusEnum(enum.Enum):
    NOT_STARTED = "NOT_STARTED"      # 未开始
    IN_PROGRESS = "IN_PROGRESS"      # 进行中
    SUBMITTED = "SUBMITTED"          # 已提交
    LATE_SUBMISSION = "LATE_SUBMISSION"  # 迟交
    GRADED = "GRADED"                # 已评分
    PASSED = "PASSED"                # 通过
    FAILED = "FAILED"                # 失败

# 点评状态枚举
class GradingStatusEnum(enum.Enum):
    NOT_GRADED = "NOT_GRADED"  # 未点评
    GRADED = "GRADED"          # 已点评

# 实践发布状态枚举
class PracticePublishStatusEnum(enum.Enum):
    DRAFT = "DRAFT"              # 草稿（兼容旧数据）
    EDITING = "EDITING"          # 编辑中
    PENDING_REVIEW = "PENDING_REVIEW"  # 待审核
    PUBLISHED = "PUBLISHED"      # 已发布
    REJECTED = "REJECTED"        # 审核未通过

# 实践可见性枚举
class PracticeVisibilityEnum(enum.Enum):
    PRIVATE = "PRIVATE"          # 仅自己可见
    PUBLIC = "PUBLIC"            # 公开发布


# ==================== 资源同步服务枚举 ====================


class User(Base):
    __tablename__ = "api_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    total_coins = Column(Integer, default=0)  # 用户累计金币
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Post(Base):
    __tablename__ = "api_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    author_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# 课程教材模型 - 使用现有数据库结构
class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    course_type = Column(Enum(CourseTypeEnum, name="course_type_enum"), nullable=False)
    description = Column(Text, nullable=True)
    cover_url = Column(Text, nullable=True)
    difficulty = Column(Enum(DifficultyEnum, name="difficulty_enum"), nullable=True)
    direction = Column(Text, nullable=True, index=True)  # 方向标签
    categories = Column(Text, nullable=True)   # 分类标签数组，存储为JSON字符串
    source = Column(String, nullable=True)  # 来源（出版社等）
    practice_task_count = Column(Integer, default=0)  # 实验数量
    outline_url = Column(Text, nullable=True)  # 教学大纲URL
    teaching_syllabus = Column(Text, nullable=True)  # 教学大纲内容（Markdown格式）
    repo_template_path = Column(Text, nullable=True)  # 代码仓库模板路径
    material_resources_count = Column(Integer, default=0)  # 教学资源数量
    material_assessments_count = Column(Integer, default=0)  # 考核数量
    visibility = Column(Enum(CourseVisibilityEnum, name="course_visibility_enum"), default=CourseVisibilityEnum.PRIVATE)
    # 课程元数据（用于内置或采购课程）
    teaching_team_name = Column(String, nullable=True)  # 开课团队名称
    teaching_team_logo = Column(String, nullable=True)  # 团队logo URL
    teaching_team_description = Column(Text, nullable=True)  # 团队描述
    lead_teacher_name = Column(String, nullable=True)  # 推荐教师姓名
    lead_teacher_title = Column(String, nullable=True)  # 教师职称
    lead_teacher_university = Column(String, nullable=True)  # 教师所属大学
    lead_teacher_department = Column(String, nullable=True)  # 教师所属院系
    lead_teacher_avatar = Column(String, nullable=True)  # 教师头像URL
    lead_teacher_intro = Column(Text, nullable=True)  # 教师简介
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    chapters = relationship("Chapter", back_populates="course", cascade="all, delete-orphan")
    resources = relationship("CourseResource", back_populates="course", cascade="all, delete-orphan")
    assessments = relationship("CourseAssessment", back_populates="course", cascade="all, delete-orphan")
    classrooms = relationship("Classroom", foreign_keys="Classroom.source_course_id")
    course_practices = relationship("Practice", foreign_keys="Practice.parent_course_id", back_populates="parent_course", order_by="Practice.order_index")

# 课程章节模型
class Chapter(Base):
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(200), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    experiment_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    course = relationship("Course", back_populates="chapters")

# 课程教学资源模型
class CourseResource(Base):
    __tablename__ = "course_resources"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    resource_type = Column(String(50), nullable=False)  # pdf, ppt, video, code等
    can_download = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    course = relationship("Course", back_populates="resources")

# 课程考核模型
class CourseAssessment(Base):
    __tablename__ = "course_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    assessment_type = Column(String(50), nullable=False)  # exam, quiz, assignment等
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    course = relationship("Course", back_populates="assessments")

# 微型实验模型
class Practice(Base):
    __tablename__ = "practices"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)
    direction = Column(String(100), nullable=False, index=True)  # 方向
    category = Column(String(100), nullable=False, index=True)   # 分类
    difficulty = Column(Enum(DifficultyLevelEnum, name="difficultylevel"), nullable=False, default=DifficultyLevelEnum.beginner)
    parent_course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)  # 所属课程
    summary = Column(Text, nullable=True)  # 实践介绍
    coin = Column(Integer, default=0)  # 金币总数
    task_count = Column(Integer, default=0)  # 任务数量
    order_index = Column(Integer, default=0)  # 排序索引（用于控制实践在列表中的显示顺序）
    
    # 自定义实践新增字段
    practice_type = Column(String(50), default="online_coding")  # online_coding, cloud_desktop
    intro = Column(Text, nullable=True)  # 实践介绍（详细）
    categories = Column(Text, nullable=True)  # 方向分类（JSON格式，最多3个二级分类）
    environment_id = Column(String(100), nullable=True)  # 实践环境ID
    
    # 高级配置
    storage_limit = Column(String(20), default="1Gi")  # 存储空间限制
    memory_limit = Column(String(20), default="1Gi")   # 内存限制
    cpu_limit = Column(String(20), default="1")        # CPU限制
    persistent_path = Column(String(500), nullable=True)  # 持久化路径
    
    # 配置选项
    enable_code_editor = Column(Boolean, default=True)    # 开启代码编辑器
    enable_terminal = Column(Boolean, default=True)       # 开启命令行
    repo_visibility = Column(String(20), default="visible")  # 代码仓库可见性：visible/hidden
    allow_skip_levels = Column(Boolean, default=True)     # 允许跳关
    
    # 状态和发布
    is_published = Column(Boolean, default=False)         # 是否已发布（保留兼容性）
    publish_status = Column(Enum(PracticePublishStatusEnum, name="practice_publish_status_enum"), default=PracticePublishStatusEnum.EDITING)  # 发布状态
    visibility = Column(Enum(PracticeVisibilityEnum, name="practice_visibility_enum"), default=PracticeVisibilityEnum.PRIVATE)  # 可见性
    published_at = Column(DateTime(timezone=True), nullable=True)  # 发布时间
    submitted_for_review_at = Column(DateTime(timezone=True), nullable=True)  # 提交审核时间
    reviewed_at = Column(DateTime(timezone=True), nullable=True)  # 审核时间
    reviewed_by = Column(Integer, ForeignKey("api_users.id"), nullable=True)  # 审核人
    review_comments = Column(Text, nullable=True)  # 审核意见

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 并发控制
    version = Column(Integer, default=1)  # 乐观锁版本号
    creator_id = Column(Integer, ForeignKey("api_users.id"), nullable=True)  # 创建者

    # 关系
    tasks = relationship("Task", back_populates="practice", cascade="all, delete-orphan")
    skills = relationship("PracticeSkill", back_populates="practice", cascade="all, delete-orphan")
    parent_course = relationship("Course", back_populates="course_practices")  # 关联到父课程
    creator = relationship("User", foreign_keys=[creator_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])  # 审核人
    code_repositories = relationship("PracticeCodeRepository", back_populates="practice", cascade="all, delete-orphan")
    datasets = relationship("PracticeDataset", back_populates="practice", cascade="all, delete-orphan")


# 操作审计日志模型
class AuditLog(Base):
    """操作审计日志"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # 用户信息
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False, index=True)
    username = Column(String(100), nullable=False)
    role = Column(String(50), default="user")

    # 操作信息
    operation = Column(String(50), nullable=False, index=True)  # read/write/admin
    resource_type = Column(String(50), nullable=False, index=True)  # practice/task/user等
    resource_id = Column(Integer, nullable=True, index=True)
    action = Column(String(100), nullable=False)  # 具体操作

    # 详细信息
    details = Column(Text, nullable=True)  # JSON格式的详细信息

    # 请求信息
    ip_address = Column(String(45), nullable=True, index=True)  # 支持IPv6
    user_agent = Column(Text, nullable=True)

    # 结果
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # 关联用户
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_operation', 'operation', 'action'),
    )

# 任务模型 - 使用现有的tasks表
class Task(Base):
    __tablename__ = "tasks"  # 使用现有的tasks表

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    practice_id = Column(Integer, ForeignKey("practices.id"), nullable=False)
    title = Column(String(200), nullable=False)
    task_type = Column(Enum(TaskTypeEnum, name="task_type_enum"), nullable=False)
    order_in_practice = Column(Integer, default=0)
    coin = Column(Integer, default=0)
    env_type = Column(String(50), nullable=True)
    difficulty = Column(String(50), nullable=True)
    skills = Column(Text, nullable=True)  # 存储为JSON字符串
    handbook_markdown = Column(Text, nullable=True)
    answer_content_markdown = Column(Text, nullable=True)
    evaluation_script_path = Column(Text, nullable=True)
    evaluation_command = Column(Text, nullable=True)
    evaluation_timeout_seconds = Column(Integer, default=300)  # 默认5分钟，适配CPU深度学习
    student_task_file_paths = Column(Text, nullable=True)  # 存储为JSON字符串
    
    # 页面预览相关字段
    enable_page_preview = Column(Boolean, default=False)  # 是否启用页面实时预览
    preview_html_file = Column(String(500), nullable=True)  # 预览HTML文件路径
    
    question_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    practice = relationship("Practice", back_populates="tasks")

# 实践技能标签模型
class PracticeSkill(Base):
    __tablename__ = "practice_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    practice_id = Column(Integer, ForeignKey("practices.id"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    practice = relationship("Practice", back_populates="skills")

# 课堂状态枚举 - 匹配数据库中的实际枚举值
class ClassroomStatusEnum(enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    ONGOING = "ONGOING"
    ENDED = "ENDED"

# 课堂模型 - 匹配实际数据库结构
class Classroom(Base):
    __tablename__ = "classrooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)  # 课堂描述
    source_course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)  # 使用source_course_id
    teacher_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)  # 修复外键指向api_users表
    credit = Column(Integer, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    academic_year = Column(String(50), nullable=True)  # 学年
    semester = Column(String(50), nullable=True)  # 学期，自动计算
    status = Column(Enum(ClassroomStatusEnum, name="classroom_status_enum"), default=ClassroomStatusEnum.NOT_STARTED)
    student_count = Column(Integer, default=0)  # 学生数量
    sync_resources_from_source = Column(Boolean, default=False)  # 是否同步教学资源
    sync_assessments_from_source = Column(Boolean, default=False)  # 是否同步课程考核
    
    # 新增字段 - 根据需求文档
    experiments_count = Column(Integer, default=0)  # 实验数：课堂内实践、实训课程数之和
    experiment_levels_count = Column(Integer, default=0)  # 实验关卡：实践课程关卡之和
    coins_count = Column(Integer, default=0)  # 金币数：实践课程金币数之和
    finished_experiments_count = Column(Integer, default=0)  # 已完成实验数
    cover_url = Column(String(500), nullable=True)  # 课堂封面图片URL
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # 软删除
    
    # 关系
    course = relationship("Course", foreign_keys=[source_course_id], overlaps="classrooms")
    # teacher = relationship("User")  # 暂时移除 

# 课堂学生关联表
class ClassroomStudent(Base):
    __tablename__ = "classroom_students"
    
    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    classroom = relationship("Classroom")
    student = relationship("User", foreign_keys=[student_id])

# 课堂实践关联表
class ClassroomPractice(Base):
    __tablename__ = "classroom_practices"
    
    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    practice_id = Column(Integer, ForeignKey("practices.id"), nullable=False)
    sync_doc = Column(Boolean, default=False)  # 是否同步实验文档
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    classroom = relationship("Classroom")
    practice = relationship("Practice")

# 课堂实训关联模型
class ClassroomTraining(Base):
    __tablename__ = "classroom_trainings"
    
    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    training_id = Column(Integer, ForeignKey("trainings.id"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    order_index = Column(Integer, default=0)  # 排序索引
    
    # 关系
    classroom = relationship("Classroom")
    training = relationship("Training")

# 实训学习会话（记录进度）
class TrainingSession(Base):
    __tablename__ = "training_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    classroom_training_id = Column(Integer, ForeignKey("classroom_trainings.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    progress_percentage = Column(Integer, default=0)
    last_active_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    classroom_training = relationship("ClassroomTraining")
    student = relationship("User")

# 实训提交记录（记录成绩和提交物）
class TrainingSubmission(Base):
    __tablename__ = "training_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("training_sessions.id"), nullable=False, unique=True)
    submission_time = Column(DateTime(timezone=True), server_default=func.now())
    teacher_score = Column(Float, nullable=True)
    auto_score = Column(Float, nullable=True)
    content = Column(Text, nullable=True)  # JSON or text payload
    
    # 关系
    session = relationship("TrainingSession")


# 代码快照模型 - 用于保存学生代码版本
class TaskCodeSnapshot(Base):
    __tablename__ = "task_code_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)  # 引用tasks表
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    repo_hash = Column(String(64), nullable=False)  # git hash或自定义hash
    files = Column(Text, nullable=False)  # JSON格式存储文件内容
    snapshot_type = Column(String(20), default="manual")  # manual, auto, pass
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    task = relationship("Task", foreign_keys=[task_id])
    user = relationship("User", foreign_keys=[user_id])

# 任务评测结果模型 - 扩展现有的student_task_attempts
class TaskEvaluationResult(Base):
    __tablename__ = "task_evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)  # 引用tasks表
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    submission_code = Column(Text, nullable=True)  # 提交的代码
    repo_hash = Column(String(64), nullable=True)  # 代码仓库hash
    status = Column(String(20), nullable=False)  # pass, fail, error, timeout
    score = Column(Integer, default=0)  # 得分
    total_tests = Column(Integer, default=0)  # 总测试数
    passed_tests = Column(Integer, default=0)  # 通过测试数
    execution_time = Column(Integer, nullable=True)  # 执行时间(ms)
    error_message = Column(Text, nullable=True)  # 错误信息
    test_results = Column(Text, nullable=True)  # JSON格式的详细测试结果
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    task = relationship("Task", foreign_keys=[task_id])
    user = relationship("User", foreign_keys=[user_id])

# 测试用例模型 - 基于现有的task_tests表
class TaskTest(Base):
    __tablename__ = "task_tests"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)  # 引用tasks表
    case_id = Column(String(100), nullable=False)  # 测试用例ID
    input_data = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=True)
    is_hidden = Column(Boolean, default=False)
    description = Column(Text, nullable=True)  # 测试用例描述
    match_rule = Column(String(50), default="EXACT_MATCH")  # EXACT_MATCH, REGEX, CUSTOM
    test_order = Column(Integer, default=0)  # 测试顺序
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    task = relationship("Task", foreign_keys=[task_id])

# 实践环境会话模型 - 用于跟踪在线环境状态
class PracticeEnvironmentSession(Base):
    __tablename__ = "practice_environment_sessions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)  # 引用tasks表
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    env_type = Column(String(50), nullable=False)  # online-code, html, cli, vdi
    session_id = Column(String(100), nullable=False)  # 环境会话ID
    container_id = Column(String(100), nullable=True)  # 容器ID
    status = Column(String(20), default="active")  # active, expired, terminated
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    task = relationship("Task", foreign_keys=[task_id])
    user = relationship("User", foreign_keys=[user_id])

# 环境会话模型 - 用于实践课程的环境管理
class EnvironmentSession(Base):
    __tablename__ = "environment_sessions"

    id = Column(String(50), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    practice_id = Column(Integer, ForeignKey("practices.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    environment_type = Column(String(50), nullable=False)  # code, desktop, command-line
    status = Column(String(20), default="active")  # active, stopped
    url = Column(String(500), nullable=True)  # 环境访问URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    stopped_at = Column(DateTime(timezone=True), nullable=True)

    # 关系
    practice = relationship("Practice", foreign_keys=[practice_id])
    user = relationship("User", foreign_keys=[user_id])

# 课堂课程模型 - 课程在课堂中的实例
class ClassroomCourse(Base):
    __tablename__ = "classroom_courses"
    
    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)  # 关联courses表（课程资源/实训），可为空
    practice_id = Column(Integer, ForeignKey("practices.id"), nullable=True)  # 关联practices表（实践课程）
    classroom_chapter_id = Column(Integer, ForeignKey("classroom_chapters.id"), nullable=True)  # 所属课堂章节
    classroom_chapter_title = Column(String(255), nullable=True)  # 课堂章节标题（兼容旧数据）
    name_override = Column(String(255), nullable=True)  # 课程在课堂中的自定义名称
    order_in_classroom = Column(Integer, default=0)  # 在课堂中的顺序
    teacher_publish_status = Column(
        Enum(CourseInClassroomStatusTeacherEnum, name="course_in_classroom_status_teacher_enum"), 
        default=CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    )
    published_at = Column(DateTime(timezone=True), nullable=True)  # 发布时间
    deadline_at = Column(DateTime(timezone=True), nullable=True)  # 截止时间
    makeup_deadline_at = Column(DateTime(timezone=True), nullable=True)  # 补交截止时间
    is_mandatory = Column(Boolean, default=True)  # 是否必修
    allow_late_submission = Column(Boolean, default=True)  # 是否允许迟交
    late_submission_deduction_points = Column(Integer, default=0)  # 迟交扣分
    total_score = Column(Integer, default=100)  # 总分
    publicize_grades = Column(Boolean, default=False)  # 是否公开成绩
    publicize_answers_after_completion = Column(Boolean, default=False)  # 完成后是否公开答案
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    classroom = relationship("Classroom")
    course = relationship("Course")
    practice = relationship("Practice")  # 关联实践课程
    classroom_chapter = relationship("ClassroomChapter")

# 学生课程进度模型
class StudentCourseProgress(Base):
    __tablename__ = "student_course_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    classroom_course_id = Column(Integer, ForeignKey("classroom_courses.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    student_status = Column(
        Enum(CourseInClassroomStatusStudentEnum, name="course_in_classroom_status_student_enum"),
        default=CourseInClassroomStatusStudentEnum.NOT_STARTED
    )
    overall_score = Column(Integer, default=0)  # 总分
    teacher_penalties = Column(Integer, default=0)  # 教师扣分
    final_calculated_score = Column(Integer, default=0)  # 最终计算分数
    first_access_at = Column(DateTime(timezone=True), nullable=True)  # 首次访问时间
    last_submission_at = Column(DateTime(timezone=True), nullable=True)  # 最后提交时间
    total_time_spent_seconds = Column(Integer, default=0)  # 总学习时间（秒）
    completed_task_count = Column(Integer, default=0)  # 已完成任务数
    # 实训课程作业相关字段
    training_assignment_files = Column(Text, nullable=True)  # 实训作业文件（JSON格式）
    training_submission_status = Column(
        Enum(SubmissionStatusEnum, name="submission_status_enum"), 
        default=SubmissionStatusEnum.NOT_STARTED
    )  # 实训提交状态
    teacher_feedback = Column(Text, nullable=True)  # 教师反馈
    is_excellent_work = Column(Boolean, default=False)  # 是否优秀作业
    graded_by_teacher_id = Column(Integer, ForeignKey("api_users.id"), nullable=True)  # 评分教师
    graded_at = Column(DateTime(timezone=True), nullable=True)  # 评分时间
    submission_snapshot = Column(Text, nullable=True) # Added for Graphic Walker snapshot
    
    # 关系
    classroom_course = relationship("ClassroomCourse")
    student = relationship("User", foreign_keys=[student_id])
    graded_by_teacher = relationship("User", foreign_keys=[graded_by_teacher_id])


# 学生实践进度模型 - 独立于课堂的学习进度
class StudentPracticeProgress(Base):
    __tablename__ = "student_practice_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    practice_id = Column(Integer, ForeignKey("practices.id"), nullable=False)
    completed_task_count = Column(Integer, default=0)  # 已完成关卡数
    total_coins_earned = Column(Integer, default=0)    # 在该实践中获得的总金币
    first_access_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    is_completed = Column(Boolean, default=False)      # 是否完成该实践
    
    # 关系
    student = relationship("User")
    practice = relationship("Practice")
    
    __table_args__ = (
        UniqueConstraint('student_id', 'practice_id', name='uq_student_practice'),
    )


# 课堂章节模型 - 用于课堂内的章节组织
class ClassroomChapter(Base):
    __tablename__ = "classroom_chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    title = Column(String(255), nullable=False)  # 章节标题
    order_index = Column(Integer, default=0)  # 章节排序
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    classroom = relationship("Classroom") 

# ==================== 考试阅卷相关模型 ====================

# 试卷模型
class TestPaper(Base):
    __tablename__ = "test_papers"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    creator_id = Column(Integer, ForeignKey("api_users.id"), nullable=True)
    difficulty = Column(Enum(DifficultyEnum, name="difficulty_enum"), default=DifficultyEnum.INTERMEDIATE)
    total_score = Column(Integer, default=100)
    estimated_duration_minutes = Column(Integer, nullable=True)
    is_shared = Column(Boolean, default=False)
    direction = Column(Text, nullable=True)
    category = Column(Text, nullable=True)
    composition_method = Column(String(50), default="MANUAL_SELECTION")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    questions = relationship("TestPaperQuestion", back_populates="test_paper")
    exams = relationship("ClassroomExam", back_populates="test_paper")

# 题目模型
class Question(Base):
    __tablename__ = "questions"
    
    id = Column(String(50), primary_key=True, index=True)  # TEXT类型，支持如'sc_001'等字符串ID
    content = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionTypeEnum, name="question_type_enum"), nullable=False)
    options = Column(Text, nullable=True)  # JSON格式存储选项
    correct_answers = Column(Text, nullable=True)  # JSON格式存储正确答案
    explanation = Column(Text, nullable=True)
    difficulty = Column(Enum(DifficultyEnum, name="difficulty_enum"), default=DifficultyEnum.INTERMEDIATE)
    creator_id = Column(Integer, ForeignKey("api_users.id"), nullable=True)
    is_shared = Column(Boolean, default=False)
    tags = Column(Text, nullable=True)  # 存储为JSON字符串
    direction = Column(Text, nullable=True)
    category = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    creator = relationship("User", foreign_keys=[creator_id])
    test_paper_questions = relationship("TestPaperQuestion", back_populates="question")

# 试卷题目关联模型
class TestPaperQuestion(Base):
    __tablename__ = "test_paper_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    test_paper_id = Column(Integer, ForeignKey("test_papers.id"), nullable=False)
    question_id = Column(String(50), ForeignKey("questions.id"), nullable=False)  # 匹配Question.id的String类型
    score_for_question = Column(Integer, nullable=False)
    order_in_paper = Column(Integer, default=0)
    section_title = Column(String(255), nullable=True)
    
    # 关系
    test_paper = relationship("TestPaper", back_populates="questions")
    question = relationship("Question", back_populates="test_paper_questions")

# 试卷模板模型
class PaperTemplate(Base):
    __tablename__ = "paper_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # 模板名称
    description = Column(Text, nullable=True)  # 模板描述
    creator_id = Column(Integer, ForeignKey("api_users.id"), nullable=True)  # 创建者ID，NULL表示系统内置
    is_system_template = Column(Boolean, default=False)  # 是否为系统内置模板
    is_active = Column(Boolean, default=True)  # 是否可用
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    creator = relationship("User", foreign_keys=[creator_id])
    question_configs = relationship("PaperTemplateQuestionConfig", back_populates="template", cascade="all, delete-orphan")

# 试卷模板题目配置模型
class PaperTemplateQuestionConfig(Base):
    __tablename__ = "paper_template_question_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("paper_templates.id"), nullable=False)
    question_type = Column(Enum(QuestionTypeEnum, name="question_type_enum"), nullable=False)  # 题目类型
    question_count = Column(Integer, nullable=False)  # 题目数量
    score_per_question = Column(Integer, nullable=False)  # 每题分数
    difficulty = Column(Enum(DifficultyEnum, name="difficulty_enum"), nullable=True)  # 难度要求
    order_index = Column(Integer, default=0)  # 排序索引
    
    # 关系
    template = relationship("PaperTemplate", back_populates="question_configs")

# 课堂考试模型
class ClassroomExam(Base):
    __tablename__ = "classroom_exams"
    
    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    test_paper_id = Column(Integer, ForeignKey("test_papers.id"), nullable=False)
    title = Column(String(255), nullable=False)
    exam_start_time = Column(DateTime(timezone=True), nullable=False)
    exam_end_time = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    pass_mark = Column(Integer, nullable=True)
    shuffle_questions = Column(Boolean, default=False)
    shuffle_options = Column(Boolean, default=False)
    status = Column(Enum(ExamStatusEnum, name="exam_status_enum"), default=ExamStatusEnum.UNPUBLISHED)
    created_by_teacher_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    classroom = relationship("Classroom")
    test_paper = relationship("TestPaper", back_populates="exams")
    student_attempts = relationship("StudentExamAttempt", back_populates="exam")

# 学生考试答题记录模型
class StudentExamAttempt(Base):
    __tablename__ = "student_exam_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    classroom_exam_id = Column(Integer, ForeignKey("classroom_exams.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    attempt_start_time = Column(DateTime(timezone=True), nullable=True)
    attempt_submission_time = Column(DateTime(timezone=True), nullable=True)
    actual_duration_seconds = Column(Integer, nullable=True)
    total_score_achieved = Column(Integer, nullable=True)
    is_graded = Column(Boolean, default=False)
    teacher_overall_comments = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # 关系
    exam = relationship("ClassroomExam", back_populates="student_attempts")
    student = relationship("User", foreign_keys=[student_id])
    answers = relationship("StudentExamAnswer", back_populates="attempt")

# 学生答题详情模型
class StudentExamAnswer(Base):
    __tablename__ = "student_exam_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    student_exam_attempt_id = Column(Integer, ForeignKey("student_exam_attempts.id"), nullable=False)
    question_id = Column(String(50), ForeignKey("questions.id"), nullable=False)  # 匹配Question.id的String类型
    answer_data = Column(Text, nullable=True)  # JSON格式存储答案
    score_awarded = Column(Integer, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    teacher_comments = Column(Text, nullable=True)
    
    # 关系
    attempt = relationship("StudentExamAttempt", back_populates="answers")
    question = relationship("Question") 

# 课堂教学资源模型 [已移除]
# class ClassroomResource(Base):
#     __tablename__ = "classroom_resources"
#     
#     id = Column(Integer, primary_key=True, index=True)
#     classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
#     title = Column(String(255), nullable=False)  # 资源标题
#     url = Column(String(500), nullable=False)  # 资源URL
#     resource_type = Column(String(50), nullable=False)  # video, ppt, pdf, document
#     file_size = Column(Integer, nullable=True)  # 文件大小（字节）
#     uploader_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)  # 上传者
#     view_count = Column(Integer, default=0)  # 查看次数
#     download_count = Column(Integer, default=0)  # 下载次数
#     is_active = Column(Boolean, default=True)  # 是否有效
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())
#     
#     # 关系
#     classroom = relationship("Classroom")
#     uploader = relationship("User", foreign_keys=[uploader_id])
#
# 教学资源模块模型
class ResourceModule(Base):
    __tablename__ = "resource_modules"

    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    name = Column(String(255), nullable=False)  # 模块名称
    description = Column(Text, nullable=True)  # 模块描述
    order_index = Column(Integer, default=0)  # 排序索引
    created_by = Column(Integer, ForeignKey("api_users.id"), nullable=False)  # 创建者
    is_active = Column(Boolean, default=True)  # 是否有效
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    classroom = relationship("Classroom")
    creator = relationship("User", foreign_keys=[created_by])
    files = relationship("ResourceFile", back_populates="module", cascade="all, delete-orphan")

# 教学资源文件模型
class ResourceFile(Base):
    __tablename__ = "resource_files"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("resource_modules.id"), nullable=False)
    name = Column(String(255), nullable=False)  # 文件名
    url = Column(String(500), nullable=False)  # 文件URL
    file_type = Column(String(50), nullable=False)  # pdf, doc, docx, ppt, pptx, mp4
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    duration_seconds = Column(Integer, nullable=True)  # 视频时长（秒）
    uploader_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)  # 上传者
    view_count = Column(Integer, default=0)  # 查看次数
    download_count = Column(Integer, default=0)  # 下载次数
    is_active = Column(Boolean, default=True)  # 是否有效
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    module = relationship("ResourceModule", back_populates="files")
    uploader = relationship("User", foreign_keys=[uploader_id])

# 课堂云盘文件模型
class ClassroomCloudFile(Base):
    __tablename__ = "classroom_cloud_files"
    
    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    name = Column(String(255), nullable=False)  # 文件名
    file_type = Column(String(50), nullable=False)  # 文件类型
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    folder_path = Column(String(500), default="")  # 文件夹路径
    url = Column(String(500), nullable=False)  # 文件URL
    uploader_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)  # 上传者
    is_shared = Column(Boolean, default=True)  # 是否共享给学生
    download_count = Column(Integer, default=0)  # 下载次数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    classroom = relationship("Classroom")
    uploader = relationship("User", foreign_keys=[uploader_id])

# 学生资源学习记录模型 [已移除]
# class StudentResourceLearning(Base):
#     __tablename__ = "student_resource_learning"
#     
#     id = Column(Integer, primary_key=True, index=True)
#     student_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
#     # 兼容原有的classroom_resources
#     resource_id = Column(Integer, ForeignKey("classroom_resources.id"), nullable=True)
#     # 新增对resource_files的支持
#     resource_file_id = Column(Integer, ForeignKey("resource_files.id"), nullable=True)
#     learning_duration_seconds = Column(Integer, default=0)  # 学习时长（秒）
#     last_position = Column(Integer, default=0)  # 最后学习位置（视频秒数等）
#     is_completed = Column(Boolean, default=False)  # 是否完成学习
#     first_access_at = Column(DateTime(timezone=True), server_default=func.now())
#     last_access_at = Column(DateTime(timezone=True), onupdate=func.now())
#     
#     # 关系
#     student = relationship("User", foreign_keys=[student_id])
#     # resource = relationship("ClassroomResource", foreign_keys=[resource_id])
#     # resource_file = relationship("ResourceFile", foreign_keys=[resource_file_id])

# 考试分数段设置模型
class ExamScoreRange(Base):
    __tablename__ = "exam_score_ranges"
    
    id = Column(Integer, primary_key=True, index=True)
    classroom_exam_id = Column(Integer, ForeignKey("classroom_exams.id"), nullable=False)
    min_score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    label = Column(String(100), nullable=True)  # 自定义标签
    order_index = Column(Integer, default=0)  # 排序
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    exam = relationship("ClassroomExam") 

# 实践代码仓库模型
class PracticeCodeRepository(Base):
    __tablename__ = "practice_code_repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    practice_id = Column(Integer, ForeignKey("practices.id"), nullable=False)
    repository_url = Column(String(500), nullable=False)  # 代码仓库地址
    branch_name = Column(String(100), default="main")     # 分支名称
    is_enabled = Column(Boolean, default=False)           # 是否开启
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    practice = relationship("Practice", back_populates="code_repositories")

# 实践代码仓库文件模型
class PracticeRepoFile(Base):
    __tablename__ = "practice_repo_files"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("practice_code_repositories.id"), nullable=False)
    file_path = Column(String(500), nullable=False)      # 文件路径，如 src/main.py
    file_name = Column(String(255), nullable=False)      # 文件名
    content = Column(Text, nullable=True)                 # 文件内容
    is_directory = Column(Boolean, default=False)        # 是否是目录
    parent_path = Column(String(500), nullable=True)     # 父目录路径
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    repository = relationship("PracticeCodeRepository", backref="files")

# 实践数据集模型
class PracticeDataset(Base):
    __tablename__ = "practice_datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    practice_id = Column(Integer, ForeignKey("practices.id"), nullable=False)
    name = Column(String(255), nullable=False)             # 数据集名称
    file_url = Column(String(500), nullable=False)         # 文件URL
    file_type = Column(String(50), nullable=False)         # 文件类型
    file_size = Column(Integer, nullable=False)            # 文件大小（字节）
    description = Column(Text, nullable=True)              # 描述
    access_url = Column(String(500), nullable=True)        # 访问地址（用于代码中引用）
    uploader_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    practice = relationship("Practice", back_populates="datasets")
    uploader = relationship("User", foreign_keys=[uploader_id])

# 实践环境配置模型
class PracticeEnvironment(Base):
    __tablename__ = "practice_environments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)             # 环境名称
    environment_type = Column(String(50), nullable=False)  # 环境类型：python, java, nodejs等
    docker_image = Column(String(200), nullable=False)     # Docker镜像
    description = Column(Text, nullable=True)              # 环境描述
    config = Column(Text, nullable=True)                   # 环境配置JSON
    status = Column(String(20), default="active")          # 环境状态
    max_sessions = Column(Integer, default=10)             # 最大会话数
    session_timeout = Column(Integer, default=1800)        # 会话超时时间(秒)
    default_storage = Column(String(20), default="1Gi")    # 默认存储
    default_memory = Column(String(20), default="1Gi")     # 默认内存
    default_cpu = Column(String(20), default="1")          # 默认CPU
    is_active = Column(Boolean, default=True)              # 是否可用
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) 

# 从统一的枚举模块导入
from app.core.enums import (
    TrainingTypeEnum,
    TrainingPublishStatusEnum,
    TrainingVisibilityEnum
)

# 实训模型
class Training(Base):
    __tablename__ = "trainings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)  # 实训名称
    training_type = Column(Enum(TrainingTypeEnum, name="training_type_enum"), nullable=False)  # 实训类型
    intro = Column(Text, nullable=True)  # 实训简介
    industry = Column(String(100), nullable=True)  # 所属行业
    difficulty = Column(Enum(DifficultyLevelEnum, name="difficultylevel"), nullable=False, default=DifficultyLevelEnum.beginner)  # 难易度
    prerequisites = Column(Text, nullable=True)  # 先修要求（JSON数组）
    learning_objectives = Column(Text, nullable=True)  # 学习目标（JSON数组）
    tags = Column(Text, nullable=True)  # 标签（JSON数组）
    course_hours = Column(Integer, default=0)  # 实验课时
    estimated_completion_time = Column(String(100), nullable=True)  # 预计完成时间
    handbook_content = Column(Text, nullable=True)  # 实训手册内容（富文本HTML）
    project_path = Column(String(500), nullable=True)  # 项目路径（用于BI/编程实训的数据/代码加载）
    designer_type = Column(String(20), nullable=True)  # 查看实训入口类型：BI / AI / JUPYTER
    
    # 项目作业节点配置（JSON格式存储）
    assignment_nodes = Column(Text, nullable=True)  # 作业节点配置
    require_design_files = Column(Boolean, default=False)  # 是否需要提交设计文件
    require_experiment_report = Column(Boolean, default=False)  # 是否需要提交实验报告
    
    # 对象存储文件路径字段
    handbook_content_url = Column(String(500), nullable=True)  # 手册内容URL
    cover_url = Column(String(500), nullable=True)  # 封面图片URL
    bi_template_path = Column(String(500), nullable=True)  # BI模板文件在对象存储中的相对路径
    ai_template_path = Column(String(500), nullable=True)  # AI模板文件在对象存储中的相对路径
    template_files_manifest = Column(Text, nullable=True)  # 模板文件清单（JSON格式）
    superset_dashboard_id = Column(String(100), nullable=True)  # Superset仪表盘ID
    superset_dataset_refs = Column(Text, nullable=True)  # Superset数据集引用（JSON）
    
    # 编码式实训特有字段
    environment_id = Column(String(100), nullable=True)  # 实训环境ID
    storage_limit = Column(String(20), default="1Gi")  # 存储空间限制
    memory_limit = Column(String(20), default="1Gi")   # 内存限制
    cpu_limit = Column(String(20), default="1")        # CPU限制
    
    # 状态和发布
    publish_status = Column(Enum(TrainingPublishStatusEnum, name="training_publish_status_enum"), default=TrainingPublishStatusEnum.EDITING)  # 发布状态
    visibility = Column(Enum(TrainingVisibilityEnum, name="training_visibility_enum"), default=TrainingVisibilityEnum.PRIVATE)  # 可见性
    is_published = Column(Boolean, default=False)  # 是否已发布
    published_at = Column(DateTime(timezone=True), nullable=True)  # 发布时间

    # 审核相关字段
    reviewer_id = Column(Integer, ForeignKey("api_users.id"), nullable=True)  # 审核人ID
    reviewed_at = Column(DateTime(timezone=True), nullable=True)  # 审核时间
    review_comment = Column(Text, nullable=True)  # 审核意见
    
    # 创建者信息
    creator_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    creator = relationship("User", foreign_keys=[creator_id])
    # 同步相关字段
    version = Column(String(50), nullable=True)  # 版本号
    last_synced_at = Column(DateTime(timezone=True), nullable=True)  # 最后同步时间

    # 关系
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    datasets = relationship("TrainingDataset", back_populates="training", cascade="all, delete-orphan")
    assets = relationship("TrainingAsset", back_populates="training", cascade="all, delete-orphan")

# 实训数据集模型
class TrainingDataset(Base):
    __tablename__ = "training_datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey("trainings.id"), nullable=False)
    name = Column(String(255), nullable=False)  # 数据集名称
    file_url = Column(String(500), nullable=False)  # 文件URL（保留兼容性）
    relative_path = Column(String(500), nullable=True)  # 文件在对象存储中的相对路径
    file_type = Column(String(50), nullable=False)  # 文件类型：sql_schema, sql_data, csv, excel等
    file_size = Column(Integer, nullable=True)  # 文件大小（字节）
    description = Column(Text, nullable=True)  # 描述
    access_path = Column(String(500), nullable=True)  # 访问路径（用于Jupyter中引用）
    access_path_in_env = Column(String(500), nullable=True)  # 在实验环境中的访问路径
    uploader_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    training = relationship("Training", back_populates="datasets")
    uploader = relationship("User", foreign_keys=[uploader_id])

# 实训环境模型
class TrainingEnvironment(Base):
    __tablename__ = "training_environments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 环境名称
    environment_type = Column(String(50), nullable=False)  # 环境类型：python, java, nodejs等
    docker_image = Column(String(200), nullable=False)  # Docker镜像
    description = Column(Text, nullable=True)  # 环境描述
    default_storage = Column(String(20), default="1Gi")  # 默认存储
    default_memory = Column(String(20), default="1Gi")  # 默认内存
    default_cpu = Column(String(20), default="1")  # 默认CPU
    is_active = Column(Boolean, default=True)  # 是否可用
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# 实训Jupyter文件模型
class TrainingJupyterFile(Base):
    __tablename__ = "training_jupyter_files"
    
    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey("trainings.id"), nullable=False)
    file_name = Column(String(255), nullable=False)  # 文件名
    file_content = Column(Text, nullable=True)  # 文件内容（JSON格式的notebook）
    file_path = Column(String(500), nullable=True)  # 文件路径
    is_main_file = Column(Boolean, default=False)  # 是否为主文件
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    training = relationship("Training")

# BI 实训草稿模型
class TrainingBiDraft(Base):
    __tablename__ = "training_bi_drafts"

    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey("trainings.id"), nullable=False)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    draft_snapshot = Column(Text, nullable=True)  # JSON 格式的 Graphic-Walker spec
    schema_version = Column(String(50), nullable=True)  # 如 "gwalk-v0.4.77"
    platform_version = Column(String(50), nullable=True)  # 平台版本
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 唯一约束：每个学生在每个课堂的每个实训只能有一个草稿
    __table_args__ = (
        UniqueConstraint('training_id', 'classroom_id', 'student_id', name='unique_bi_draft'),
        Index('idx_bi_draft_student', 'student_id'),
        Index('idx_bi_draft_training', 'training_id'),
    )

    # 关系
    training = relationship("Training")
    student = relationship("User", foreign_keys=[student_id])

# ==================== 优秀作业点赞和收藏相关模型 [已移除] ====================

# 优秀作业点赞模型
# class ExcellentWorkLike(Base):
#     __tablename__ = "excellent_work_likes"
#     
#     id = Column(Integer, primary_key=True, index=True)
#     student_progress_id = Column(Integer, ForeignKey("student_course_progress.id"), nullable=False)  # 优秀作业ID
#     user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)  # 点赞用户ID
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     
#     # 关系
#     student_progress = relationship("StudentCourseProgress")
#     user = relationship("User", foreign_keys=[user_id])
#     
#     # 唯一约束：同一用户对同一作业只能点赞一次
#     __table_args__ = (
#         UniqueConstraint('student_progress_id', 'user_id', name='unique_excellent_work_like'),
#     )
#
# # 优秀作业收藏模型
# class ExcellentWorkFavorite(Base):
#     __tablename__ = "excellent_work_favorites"
#     
#     id = Column(Integer, primary_key=True, index=True)
#     student_progress_id = Column(Integer, ForeignKey("student_course_progress.id"), nullable=False)  # 优秀作业ID
#     user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)  # 收藏用户ID
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     
#     # 关系
#     student_progress = relationship("StudentCourseProgress")
#     user = relationship("User", foreign_keys=[user_id])
#     
#     # 唯一约束：同一用户对同一作业只能收藏一次
#     __table_args__ = (
#         UniqueConstraint('student_progress_id', 'user_id', name='unique_excellent_work_favorite'),
#     )
#
# # 优秀作业浏览记录模型（用于统计阅读量）
# class ExcellentWorkView(Base):
#     __tablename__ = "excellent_work_views"
#     
#     id = Column(Integer, primary_key=True, index=True)
#     student_progress_id = Column(Integer, ForeignKey("student_course_progress.id"), nullable=False)  # 优秀作业ID
#     user_id = Column(Integer, ForeignKey("api_users.id"), nullable=True)  # 浏览用户ID（可为空，支持匿名浏览）
#     ip_address = Column(String(45), nullable=True)  # IP地址
#     user_agent = Column(Text, nullable=True)  # 用户代理
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     
#     # 关系
#     student_progress = relationship("StudentCourseProgress")
#     user = relationship("User", foreign_keys=[user_id])

# ==================== 组织架构和用户管理相关模型 ====================

# 组织类型枚举
class OrganizationTypeEnum(enum.Enum):
    SCHOOL = "SCHOOL"        # 学校
    COLLEGE = "COLLEGE"      # 学院
    MAJOR = "MAJOR"          # 专业
    GRADE = "GRADE"          # 年级
    CLASS = "CLASS"          # 班级

# 用户类型枚举
class UserTypeEnum(enum.Enum):
    TEACHER = "TEACHER"      # 教师
    STUDENT = "STUDENT"      # 学生
    ADMIN = "ADMIN"          # 管理员

# 用户状态枚举
class UserStatusEnum(enum.Enum):
    ACTIVE = "ACTIVE"        # 启用
    INACTIVE = "INACTIVE"    # 停用

# 性别枚举
class GenderEnum(enum.Enum):
    MALE = "MALE"           # 男
    FEMALE = "FEMALE"       # 女
    OTHER = "OTHER"         # 其他

# 学校信息模型
class School(Base):
    __tablename__ = "schools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # 学校名称
    short_name = Column(String(100), nullable=True)  # 学校简称
    code = Column(String(50), nullable=True)  # 学校编码
    logo_url = Column(String(500), nullable=True)  # 学校LOGO URL
    logo_data = Column(LargeBinary, nullable=True)  # Logo二进制数据
    motto = Column(String(500), nullable=True)  # 校训
    description = Column(Text, nullable=True)  # 学校描述
    address = Column(String(500), nullable=True)  # 学校地址
    website = Column(String(255), nullable=True)  # 学校官网
    phone = Column(String(50), nullable=True)  # 联系电话
    email = Column(String(100), nullable=True)  # 联系邮箱
    is_active = Column(Boolean, default=True)  # 是否启用
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    organizations = relationship("Organization", back_populates="school", cascade="all, delete-orphan")

# 组织架构模型
class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)  # 父级组织ID
    name = Column(String(255), nullable=False)  # 组织名称
    code = Column(String(100), nullable=True)  # 组织编码
    short_name = Column(String(100), nullable=True)  # 组织简称
    org_type = Column(Enum(OrganizationTypeEnum, name="organization_type_enum"), nullable=False)  # 组织类型
    level = Column(Integer, default=1)  # 组织层级（1-学校，2-学院，3-专业，4-年级，5-班级）
    order_index = Column(Integer, default=0)  # 排序索引
    description = Column(Text, nullable=True)  # 组织描述
    responsible_person = Column(String(100), nullable=True)  # 负责人
    contact_phone = Column(String(50), nullable=True)  # 联系电话
    contact_email = Column(String(100), nullable=True)  # 联系邮箱
    is_active = Column(Boolean, default=True)  # 是否启用
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    school = relationship("School", back_populates="organizations")
    parent = relationship("Organization", remote_side=[id])
    children = relationship("Organization", back_populates="parent")
    users = relationship("UserProfile", back_populates="organization")

# 用户详细信息模型（扩展User模型）
class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False, unique=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)  # 所属组织
    user_type = Column(Enum(UserTypeEnum, name="user_type_enum"), nullable=False)  # 用户类型
    employee_id = Column(String(50), nullable=True, unique=True)  # 工号/学号
    real_name = Column(String(100), nullable=False)  # 真实姓名
    gender = Column(Enum(GenderEnum, name="gender_enum"), nullable=True)  # 性别
    birth_date = Column(DateTime(timezone=True), nullable=True)  # 出生日期
    id_card = Column(String(20), nullable=True)  # 身份证号
    phone = Column(String(20), nullable=True)  # 手机号
    avatar_url = Column(String(500), nullable=True)  # 头像URL
    
    # 教师特有字段
    title = Column(String(100), nullable=True)  # 职称
    department = Column(String(100), nullable=True)  # 部门
    research_direction = Column(Text, nullable=True)  # 研究方向
    
    # 学生特有字段
    admission_year = Column(Integer, nullable=True)  # 入学年份
    graduation_year = Column(Integer, nullable=True)  # 毕业年份
    student_status = Column(String(50), nullable=True)  # 学籍状态
    
    # 状态和权限
    status = Column(Enum(UserStatusEnum, name="user_status_enum"), default=UserStatusEnum.ACTIVE)  # 用户状态
    is_admin = Column(Boolean, default=False)  # 是否管理员
    last_login_at = Column(DateTime(timezone=True), nullable=True)  # 最后登录时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    school = relationship("School")
    organization = relationship("Organization", back_populates="users")

# 管理员角色模型
class AdminRole(Base):
    __tablename__ = "admin_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    granted_by = Column(Integer, ForeignKey("api_users.id"), nullable=False)  # 授权人
    granted_at = Column(DateTime(timezone=True), server_default=func.now())  # 授权时间
    is_active = Column(Boolean, default=True)  # 是否有效
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    school = relationship("School")
    granter = relationship("User", foreign_keys=[granted_by])
    
    # 唯一约束：同一用户在同一学校只能有一个管理员角色
    __table_args__ = (
        UniqueConstraint('user_id', 'school_id', name='unique_admin_role'),
    )

# 组织导入记录模型
class OrganizationImportRecord(Base):
    __tablename__ = "organization_import_records"
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    file_name = Column(String(255), nullable=False)  # 导入文件名
    file_url = Column(String(500), nullable=True)  # 文件URL
    total_count = Column(Integer, default=0)  # 总记录数
    success_count = Column(Integer, default=0)  # 成功导入数
    failed_count = Column(Integer, default=0)  # 失败数
    error_file_url = Column(String(500), nullable=True)  # 错误文件URL
    status = Column(String(50), default="PROCESSING")  # 导入状态：PROCESSING, SUCCESS, FAILED
    imported_by = Column(Integer, ForeignKey("api_users.id"), nullable=False)  # 导入人
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)  # 完成时间
    
    # 关系
    school = relationship("School")
    importer = relationship("User", foreign_keys=[imported_by])

# 用户导入记录模型
class UserImportRecord(Base):
    __tablename__ = "user_import_records"
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    user_type = Column(Enum(UserTypeEnum, name="user_type_enum"), nullable=False)  # 导入的用户类型
    file_name = Column(String(255), nullable=False)  # 导入文件名
    file_url = Column(String(500), nullable=True)  # 文件URL
    total_count = Column(Integer, default=0)  # 总记录数
    success_count = Column(Integer, default=0)  # 成功导入数
    failed_count = Column(Integer, default=0)  # 失败数
    error_file_url = Column(String(500), nullable=True)  # 错误文件URL
    status = Column(String(50), default="PROCESSING")  # 导入状态：PROCESSING, SUCCESS, FAILED
    imported_by = Column(Integer, ForeignKey("api_users.id"), nullable=False)  # 导入人
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)  # 完成时间
    
    # 关系
    school = relationship("School")
    importer = relationship("User", foreign_keys=[imported_by])

# 用户调动记录模型
class UserTransferRecord(Base):
    __tablename__ = "user_transfer_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    from_organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)  # 原组织
    to_organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)  # 目标组织
    transfer_reason = Column(Text, nullable=True)  # 调动原因
    transferred_by = Column(Integer, ForeignKey("api_users.id"), nullable=False)  # 操作人
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    from_organization = relationship("Organization", foreign_keys=[from_organization_id])
    to_organization = relationship("Organization", foreign_keys=[to_organization_id])
    operator = relationship("User", foreign_keys=[transferred_by]) 

# 课程申请类型枚举
class CourseRequestTypeEnum(enum.Enum):
    PUBLISH = "PUBLISH"          # 申请公开发布
    UNPUBLISH = "UNPUBLISH"      # 申请撤销公开

# 课程申请状态枚举
class CourseRequestStatusEnum(enum.Enum):
    PENDING = "PENDING"          # 待审批
    APPROVED = "APPROVED"        # 已同意
    REJECTED = "REJECTED"        # 已驳回
    CANCELLED = "CANCELLED"      # 用户撤销

# 课程发布状态枚举
class CoursePublishStatusEnum(enum.Enum):
    UNPUBLISHED = "UNPUBLISHED"  # 未发布
    PERSONAL = "PERSONAL"        # 个人发布
    PUBLIC = "PUBLIC"            # 公开发布

# 课程来源枚举
class CourseSourceEnum(enum.Enum):
    TEACHER = "TEACHER"          # 教师创建
    ADMIN = "ADMIN"              # 管理员导入

# 课程申请记录模型
class CourseRequest(Base):
    __tablename__ = "course_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)  # 课程ID
    course_type = Column(Enum(CourseTypeEnum, name="course_type_enum"), nullable=False)  # 课程类型
    applicant_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)  # 申请人ID
    request_type = Column(Enum(CourseRequestTypeEnum, name="course_request_type_enum"), nullable=False)  # 申请类型
    status = Column(Enum(CourseRequestStatusEnum, name="course_request_status_enum"), default=CourseRequestStatusEnum.PENDING)  # 申请状态
    
    # 申请信息
    application_reason = Column(Text, nullable=True)  # 申请理由
    applied_at = Column(DateTime(timezone=True), server_default=func.now())  # 申请时间
    
    # 审批信息
    reviewer_id = Column(Integer, ForeignKey("api_users.id"), nullable=True)  # 审批人ID
    review_comments = Column(Text, nullable=True)  # 审批意见
    reviewed_at = Column(DateTime(timezone=True), nullable=True)  # 审批时间
    
    # 撤销信息
    cancelled_reason = Column(Text, nullable=True)  # 撤销原因
    cancelled_at = Column(DateTime(timezone=True), nullable=True)  # 撤销时间
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    course = relationship("Course", foreign_keys=[course_id])
    applicant = relationship("User", foreign_keys=[applicant_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

# 扩展Course模型，添加发布状态相关字段
# 注意：这里我们需要在现有的Course模型中添加字段，但为了不破坏现有结构，
# 我们可以通过数据库迁移的方式添加这些字段
# 这里先定义新的字段，实际使用时需要确保数据库表结构已更新

# 为了兼容现有代码，我们在Course模型中添加新字段的注释
# 新增字段（需要通过数据库迁移添加）：
# publish_status = Column(Enum(CoursePublishStatusEnum, name="course_publish_status_enum"), default=CoursePublishStatusEnum.UNPUBLISHED)  # 发布状态
# source = Column(Enum(CourseSourceEnum, name="course_source_enum"), default=CourseSourceEnum.TEACHER)  # 课程来源
# creator_id = Column(Integer, ForeignKey("api_users.id"), nullable=True)  # 创建者ID
# published_at = Column(DateTime(timezone=True), nullable=True)  # 公开发布时间
# unpublished_at = Column(DateTime(timezone=True), nullable=True)  # 下架时间 

# ==================== 教学资源管理相关模型 ====================

class EnvironmentTypeEnum(enum.Enum):
    NORMAL = "normal"        # 普通实践环境
    JUPYTER = "jupyter"      # Jupyter环境
    DESKTOP = "desktop"      # 云桌面环境


# 实践环境配置模型
class PracticeEnvironmentConfig(Base):
    __tablename__ = "practice_environment_configs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # 环境名称
    environment_type = Column(String(20), default="normal")  # 环境类型: normal, jupyter, desktop
    
    # 资源配额配置 (MB)
    storage_min = Column(Integer, default=256)
    storage_max = Column(Integer, default=2048)
    storage_default = Column(Integer, default=512)
    
    memory_min = Column(Integer, default=128)
    memory_max = Column(Integer, default=1024)
    memory_default = Column(Integer, default=256)
    
    cpu_min = Column(Integer, default=1)
    cpu_max = Column(Integer, default=4)
    cpu_default = Column(Integer, default=1)
    
    # Docker镜像配置
    docker_image = Column(String(255), nullable=True)
    docker_port = Column(Integer, default=8888)
    
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# 系统设置模型
class SystemSetting(Base):
    __tablename__ = "system_settings"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)  # 设置键
    value = Column(Text, nullable=True)                                 # 设置值
    value_type = Column(String(50), default="string")                   # 值类型：string, boolean, integer, json
    description = Column(Text, nullable=True)                           # 设置描述
    category = Column(String(50), default="general")                    # 分类
    is_system = Column(Boolean, default=False)                          # 是否为系统设置
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# 容器进程模型
class ContainerProcess(Base):
    __tablename__ = "container_processes"
    
    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String(100), unique=True, nullable=False, index=True)  # 容器ID
    container_name = Column(String(200), nullable=True)                          # 容器名称
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)        # 用户ID
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)         # 课程ID
    training_id = Column(Integer, ForeignKey("trainings.id"), nullable=True)     # 实训ID
    environment_type = Column(String(50), nullable=False)                        # 实验类型：普通实践、jupyter、云桌面
    
    # 资源使用情况
    cpu_usage = Column(Float, default=0.0)                              # CPU使用率
    memory_usage = Column(Float, default=0.0)                           # 内存使用率（MB）
    memory_limit = Column(Float, default=1024.0)                        # 内存限制（MB）
    
    # 时间信息
    start_time = Column(DateTime(timezone=True), nullable=False)         # 开始时间
    last_activity = Column(DateTime(timezone=True), nullable=True)       # 最后活动时间
    
    # 状态信息
    status = Column(String(20), default="running")                       # 状态：running, stopped, error
    ip_address = Column(String(45), nullable=True)                       # IP地址
    port = Column(Integer, nullable=True)                                # 端口
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    course = relationship("Course", foreign_keys=[course_id])
    training = relationship("Training", foreign_keys=[training_id])

# 服务器节点模型
class ServerNode(Base):
    __tablename__ = "server_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    node_name = Column(String(100), nullable=False, index=True)          # 节点名称
    node_type = Column(String(50), nullable=False)                       # 节点类型：application, compute
    ip_address = Column(String(45), nullable=False)                      # IP地址
    
    # 硬件资源信息
    total_cpu_cores = Column(Integer, default=0)                         # 总CPU核心数
    total_memory_gb = Column(Float, default=0.0)                         # 总内存（GB）
    total_storage_gb = Column(Float, default=0.0)                        # 总存储（GB）
    
    # 当前使用情况
    cpu_usage_percent = Column(Float, default=0.0)                       # CPU使用率
    memory_usage_percent = Column(Float, default=0.0)                    # 内存使用率
    storage_usage_percent = Column(Float, default=0.0)                   # 存储使用率
    
    # 状态信息
    status = Column(String(20), default="online")                        # 状态：online, offline, error
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)      # 最后心跳时间
    
    is_active = Column(Boolean, default=True)                            # 是否启用
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# 资源监控记录模型
class ResourceMonitorRecord(Base):
    __tablename__ = "resource_monitor_records"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("server_nodes.id"), nullable=False)
    
    # 监控数据
    cpu_usage_percent = Column(Float, nullable=False)                    # CPU使用率
    memory_usage_percent = Column(Float, nullable=False)                 # 内存使用率
    storage_usage_percent = Column(Float, nullable=False)                # 存储使用率
    
    # 详细信息
    cpu_load_1min = Column(Float, nullable=True)                         # 1分钟负载
    cpu_load_5min = Column(Float, nullable=True)                         # 5分钟负载
    cpu_load_15min = Column(Float, nullable=True)                        # 15分钟负载
    
    memory_used_gb = Column(Float, nullable=True)                        # 已用内存（GB）
    memory_available_gb = Column(Float, nullable=True)                   # 可用内存（GB）
    
    storage_used_gb = Column(Float, nullable=True)                       # 已用存储（GB）
    storage_available_gb = Column(Float, nullable=True)                  # 可用存储（GB）
    
    # 网络信息
    network_in_mbps = Column(Float, nullable=True)                       # 网络入流量（Mbps）
    network_out_mbps = Column(Float, nullable=True)                      # 网络出流量（Mbps）
    
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    node = relationship("ServerNode")

# 容器操作日志模型
class ContainerOperationLog(Base):
    __tablename__ = "container_operation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String(100), nullable=False, index=True)       # 容器ID
    operation_type = Column(String(50), nullable=False)                  # 操作类型：start, stop, restart, delete
    operator_id = Column(Integer, ForeignKey("api_users.id"), nullable=True)  # 操作者ID
    operator_type = Column(String(20), default="manual")                 # 操作类型：manual, auto, system
    
    # 操作详情
    operation_reason = Column(Text, nullable=True)                       # 操作原因
    operation_result = Column(String(20), nullable=False)                # 操作结果：success, failed
    error_message = Column(Text, nullable=True)                          # 错误信息
    
    # 时间信息
    operation_time = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    operator = relationship("User", foreign_keys=[operator_id])

# 为了兼容现有代码，我们在Course模型中添加新字段的注释
# 新增字段（需要通过数据库迁移添加）：
# publish_status = Column(Enum(CoursePublishStatusEnum, name="course_publish_status_enum"), default=CoursePublishStatusEnum.UNPUBLISHED)  # 发布状态
# source = Column(Enum(CourseSourceEnum, name="course_source_enum"), default=CourseSourceEnum.TEACHER)  # 课程来源
# creator_id = Column(Integer, ForeignKey("api_users.id"), nullable=True)  # 创建者ID
# published_at = Column(DateTime(timezone=True), nullable=True)  # 公开发布时间
# unpublished_at = Column(DateTime(timezone=True), nullable=True)  # 下架时间 

# 使用日志统计分析相关模型

class UserLoginLog(Base):
    """用户登录日志"""
    __tablename__ = "user_login_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    login_time = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])

class CourseAccessLog(Base):
    """课程访问日志"""
    __tablename__ = "course_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    access_time = Column(DateTime(timezone=True), server_default=func.now())
    access_source = Column(String(50), nullable=True)  # 访问来源：course_practice, course_add, my_practices
    ip_address = Column(String(45), nullable=True)
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    course = relationship("Course", foreign_keys=[course_id])

class PracticeAccessLog(Base):
    """实践访问日志"""
    __tablename__ = "practice_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    practice_id = Column(Integer, ForeignKey("practices.id"), nullable=False)
    access_time = Column(DateTime(timezone=True), server_default=func.now())
    access_source = Column(String(50), nullable=True)  # 访问来源：course_practice, course_add, my_practices, my_classroom
    ip_address = Column(String(45), nullable=True)
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    practice = relationship("Practice", foreign_keys=[practice_id])

class PracticeLearningLog(Base):
    """实践学习日志"""
    __tablename__ = "practice_learning_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    practice_id = Column(Integer, ForeignKey("practices.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, default=0)  # 学习时长（秒）
    is_challenge_started = Column(Boolean, default=False)  # 是否点击了开始挑战
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    practice = relationship("Practice", foreign_keys=[practice_id])

class TrainingAccessLog(Base):
    """实训访问日志"""
    __tablename__ = "training_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    training_id = Column(Integer, ForeignKey("trainings.id"), nullable=False)
    access_time = Column(DateTime(timezone=True), server_default=func.now())
    access_source = Column(String(50), nullable=True)  # 访问来源：course_practice, course_add, my_practices, my_classroom
    ip_address = Column(String(45), nullable=True)
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    training = relationship("Training", foreign_keys=[training_id])

class TrainingLearningLog(Base):
    """实训学习日志"""
    __tablename__ = "training_learning_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    training_id = Column(Integer, ForeignKey("trainings.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, default=0)  # 学习时长（秒）
    is_training_started = Column(Boolean, default=False)  # 是否点击了开始实训
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    training = relationship("Training", foreign_keys=[training_id])

class ClassroomCreationLog(Base):
    """课堂创建日志"""
    __tablename__ = "classroom_creation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)  # 引用的课程
    created_time = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    teacher = relationship("User", foreign_keys=[teacher_id])
    classroom = relationship("Classroom", foreign_keys=[classroom_id])
    course = relationship("Course", foreign_keys=[course_id])

class CourseAddToClassroomLog(Base):
    """课程添加到课堂日志"""
    __tablename__ = "course_add_to_classroom_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    added_time = Column(DateTime(timezone=True), server_default=func.now())
    add_source = Column(String(50), nullable=True)  # 添加来源：course_practice, course_add, my_practices
    
    # 关系
    teacher = relationship("User", foreign_keys=[teacher_id])
    course = relationship("Course", foreign_keys=[course_id])
    classroom = relationship("Classroom", foreign_keys=[classroom_id])



# class DataPlaygroundProjectLog(Base):
#     """数据游乐场项目创建日志 [已移除]"""
#     __tablename__ = "data_playground_project_logs"
#     
#     id = Column(Integer, primary_key=True, index=True)
#     student_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
#     project_name = Column(String(255), nullable=False)
#     created_time = Column(DateTime(timezone=True), server_default=func.now())
#     
#     # 关系
#     student = relationship("User", foreign_keys=[student_id])


class CloudDiskFile(Base):
    """课堂云盘文件"""
    __tablename__ = "cloud_disk_files"
    
    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    uploader_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # 相对于 ziyuan 目录的路径
    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    folder_path = Column(String(500), default="")  # 文件夹路径
    is_shared = Column(Boolean, default=False)  # 是否共享给学生
    url = Column(String(500), nullable=True)  # 文件访问URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    classroom = relationship("Classroom", foreign_keys=[classroom_id])
    uploader = relationship("User", foreign_keys=[uploader_id])

# 实训支持性素材模型
class TrainingAsset(Base):
    __tablename__ = "training_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey("trainings.id"), nullable=False)
    name = Column(String(255), nullable=False)  # 素材名称
    relative_path = Column(String(500), nullable=False)  # 文件在对象存储中的相对路径
    file_type = Column(String(50), nullable=False)  # 文件MIME类型：image/png, video/mp4等
    file_size = Column(Integer, nullable=True)  # 文件大小（字节）
    description = Column(Text, nullable=True)  # 描述
    asset_type = Column(String(100), nullable=True)  # 资源类型：bi_template, ai_model等
    uploader_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    training = relationship("Training", back_populates="assets")
    uploader = relationship("User", foreign_keys=[uploader_id])

# ==================== AI助教相关模型 ====================

# AI配置模型
class AIConfig(Base):
    __tablename__ = "ai_config"
    
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), default="deepseek")  # AI服务提供商: deepseek/gemini/custom
    endpoint = Column(Text, nullable=False)  # API端点
    api_key = Column(Text, nullable=False)  # API密钥（应加密存储）
    model_name = Column(String(100), nullable=False)  # 模型名称
    max_tokens = Column(Integer, default=2000)  # 最大token数
    temperature = Column(Float, default=0.7)  # 温度参数
    is_active = Column(Boolean, default=True)  # 是否激活
    features = Column(JSON, default={  # 功能开关
        "grading": True,  # 批阅助手
        "content_generation": True,  # 内容生成
        "code_help": False,  # 代码辅导
        "concept_explain": False  # 概念解释
    })
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# AI使用日志模型
class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    user_role = Column(String(20), nullable=False)  # teacher/student/admin
    feature_type = Column(String(50), nullable=False)  # grading/content/code_help/concept
    prompt_tokens = Column(Integer, default=0)  # 提示词token数
    completion_tokens = Column(Integer, default=0)  # 完成token数
    total_tokens = Column(Integer, default=0)  # 总token数
    cost_estimate = Column(Float, default=0.0)  # 估算成本
    request_data = Column(Text, nullable=True)  # 请求内容（可选存储）
    response_data = Column(Text, nullable=True)  # 响应内容（可选存储）
    error_message = Column(Text, nullable=True)  # 错误信息
    response_time = Column(Float, nullable=True)  # 响应时间（秒）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])

# AI模型库模型
class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # 使用UUID作为主键
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    name = Column(String(255), nullable=False)  # 模型名称
    model_type = Column(String(50), nullable=False)  # 模型类型: regression/classification/clustering/custom
    description = Column(Text, nullable=True)  # 模型描述
    tags = Column(JSON, default=list)  # 标签列表
    config = Column(JSON, default=dict)  # 模型配置
    version = Column(Integer, default=1)  # 版本号
    is_published = Column(Boolean, default=False)  # 是否公开
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    user = relationship("User", foreign_keys=[user_id])

# 流水线运行记录模型
class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline_id = Column(String(36), nullable=False)  # 关联的流水线ID
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    status = Column(String(20), default="pending")  # pending/running/completed/failed
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    node_outputs = Column(JSON, default=dict)  # 各节点输出
    metrics = Column(JSON, default=dict)  # 评估指标
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    user = relationship("User", foreign_keys=[user_id])

# 节点执行记录模型
class NodeExecution(Base):
    __tablename__ = "node_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("pipeline_runs.id"), nullable=False)
    node_id = Column(String(100), nullable=False)  # 节点ID
    node_type = Column(String(50), nullable=False)  # 节点类型: data_source/data_processing/model_train/evaluation
    status = Column(String(20), default="pending")
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    execution_time = Column(Float, nullable=True)  # 执行时间（秒）
    memory_usage = Column(Float, nullable=True)  # 内存使用（MB）
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    run = relationship("PipelineRun", backref="node_executions")

# ==================== 资源同步服务枚举 ====================
