from pydantic import BaseModel, Field
from typing import List, Union, Dict, Any, Optional, Literal
from enum import Enum


class LevelTypeEnum(str, Enum):
    """关卡类型枚举"""
    PRACTICE = "实践题"
    JUDGMENT = "判断题"
    CHOICE = "选择题"


class DifficultyEnum(str, Enum):
    """难度枚举"""
    BEGINNER = "初级"
    INTERMEDIATE = "中级"
    ADVANCED = "高级"


class OutlineItem(BaseModel):
    """关卡提纲项"""
    level_title: str = Field(..., description="建议的关卡标题")
    core_knowledge: str = Field(..., description="该关卡的核心知识点")
    suggested_type: str = Field(..., description="建议的关卡类型 (实践题, 判断题, 选择题)")
    difficulty: str = Field(..., description="评估的难度 (初级, 中级, 高级)")


class OutlineResponse(BaseModel):
    """生成提纲响应"""
    filename: str = Field(..., description="上传的原始文件名")
    outline: List[OutlineItem] = Field(..., description="生成的关卡提纲列表")


class PracticeContent(BaseModel):
    """实践题内容模型"""
    task_markdown: str = Field(..., description="Markdown格式的任务描述文件内容")
    answer_markdown: str = Field(..., description="Markdown格式的参考答案文件内容")


class LevelGenerationRequest(BaseModel):
    """关卡生成请求"""
    background_context: str = Field(..., description="从PDF或DOCX中提取的完整章节文本内容")
    current_task: OutlineItem = Field(..., description="当前需要生成的具体关卡提纲项")


class LevelGenerationResponse(BaseModel):
    level_title: str = Field(..., description="关卡标题")
    content: Union[List[Dict[str, Any]], PracticeContent] = Field(..., description="关卡内容，可能是题目列表或实践内容")
    level_type: str = Field(..., description="关卡类型")
    
    class Config:
        json_encoders = {
            # 如果需要特殊编码可以在这里添加
        }

# 新增的API 3.1: 课程元数据生成相关模型
class MetadataGenerationRequest(BaseModel):
    course_title: str = Field(..., description="课程的正式名称，如 'Python程序设计'")
    syllabus_text: str = Field(..., description="教学方案或课程大纲的完整文本内容")
    file_manifest: str = Field(..., description="课程目录的文件清单，纯文本格式")

class Category(BaseModel):
    primary: str
    secondary: List[str]

class Config(BaseModel):
    allow_skip: bool
    editor_enabled: bool
    shell_enabled: bool
    repo_visible: bool

class MetadataResponse(BaseModel):
    practice_name: str
    practice_type: str
    introduction: str
    difficulty: str
    category: Category
    environment_id: str
    config: Config

# 新增的API 3.2: 评测资源生成相关模型
class EvaluationAssetRequest(BaseModel):
    task_markdown: str = Field(..., description="Markdown格式的关卡任务描述")
    answer_code: str = Field(..., description="参考答案中的Python代码部分")

class EvaluationAssetResponse(BaseModel):
    judge_script: str = Field(..., description="生成的 judge.py 文件的代码内容")
    test_cases: List[Dict[str, Any]] = Field(..., description="生成的 tests.json 的内容 (JSON数组)")

# 新增的API 3.3: 考核试题生成相关模型
class QuestionGenerationRequest(BaseModel):
    content_text: str = Field(..., description="教学章节的完整文本内容")
    num_single_choice: int = Field(3, description="要生成的单选题数量")
    num_multiple_choice: int = Field(4, description="要生成的多选题数量")
    num_true_false: int = Field(3, description="要生成的判断题数量")

class QuestionGenerationResponse(BaseModel):
    questions: List[Dict[str, Any]] = Field(..., description="生成的试题列表，每个元素都是一个完整的试题对象")

# 多文件批量处理相关模型
class FileManifestItem(BaseModel):
    """单个文件的清单项"""
    form_field_name: str = Field(..., description="在表单中对应的文件字段名，如 'file_1'")
    original_filename: str = Field(..., description="文件的原始名称，如 '第1章 Python概述.pdf'")
    file_type: Literal['teaching_content', 'teaching_plan', 'ideological_elements'] = Field(..., description="文件类型：teaching_content=教学内容, teaching_plan=教学方案, ideological_elements=思政元素")

class FullCourseManifest(BaseModel):
    """完整课程包的清单"""
    course_title: str = Field(..., description="整个课程的名称，如 'Python程序设计'")
    files: List[FileManifestItem] = Field(..., description="所有上传文件的清单列表")

class GeneratedLevel(BaseModel):
    """生成的关卡信息"""
    outline_item: OutlineItem = Field(..., description="关卡提纲项")
    content: Union[PracticeContent, List[Dict[str, Any]]] = Field(..., description="关卡内容")
    evaluation_assets: Optional[EvaluationAssetResponse] = Field(None, description="评测资源（仅实践题有）")

class ProcessedFileResult(BaseModel):
    """单个文件的处理结果"""
    original_filename: str = Field(..., description="原始文件名")
    file_type: str = Field(..., description="文件类型")
    levels: Optional[List[GeneratedLevel]] = Field(None, description="生成的关卡列表（教学内容文件）")
    exam_questions: Optional[List[Dict[str, Any]]] = Field(None, description="生成的考核试题（教学方案文件）")
    processing_status: str = Field(..., description="处理状态：SUCCESS/ERROR")
    error_message: Optional[str] = Field(None, description="错误信息（如果有）")

class FullPackageResponse(BaseModel):
    """完整课程包生成结果"""
    metadata: MetadataResponse = Field(..., description="课程元数据")
    processed_files: List[ProcessedFileResult] = Field(..., description="各文件处理结果")

class TaskCreateResponse(BaseModel):
    """任务创建响应"""
    task_id: str = Field(..., description="任务ID")
    message: str = Field(..., description="响应消息")

class DatabasePersistResult(BaseModel):
    """数据库持久化结果"""
    success: bool = Field(..., description="持久化是否成功")
    message: str = Field(..., description="持久化消息")
    practice_id: Optional[int] = Field(None, description="创建的课程ID")
    task_ids: List[int] = Field([], description="创建的关卡ID列表")
    test_paper_id: Optional[int] = Field(None, description="创建的试卷ID")
    question_ids: List[int] = Field([], description="创建的试题ID列表")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")

class ExtendedTaskResult(BaseModel):
    """扩展的任务结果（包含数据库持久化信息）"""
    course_package: FullPackageResponse = Field(..., description="课程包生成结果")
    database_result: Optional[DatabasePersistResult] = Field(None, description="数据库持久化结果")

class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str = Field(..., description="任务ID")
    status: Literal['PENDING', 'PROCESSING', 'SUCCESS', 'ERROR'] = Field(..., description="任务状态")
    progress: Optional[int] = Field(None, description="进度百分比 (0-100)")
    result: Optional[Union[FullPackageResponse, ExtendedTaskResult, Dict[str, Any]]] = Field(None, description="完成结果（仅成功时）")
    error_message: Optional[str] = Field(None, description="错误信息（仅失败时）")

# 异步任务相关模型
class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class TaskTypeEnum(str, Enum):
    """任务类型枚举"""
    OUTLINE = "outline"
    LEVEL = "level"


class GenerationTaskCreate(BaseModel):
    """创建生成任务请求"""
    task_type: TaskTypeEnum = Field(..., description="任务类型")
    # 对于outline任务，只需要文件
    # 对于level任务，还需要background_context和current_task


class GenerationTaskResponse(BaseModel):
    """生成任务响应"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    result: Optional[Union[OutlineResponse, LevelGenerationResponse]] = Field(None, description="任务结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: str = Field(..., description="创建时间")
    completed_at: Optional[str] = Field(None, description="完成时间")


# ==================== 实训资源生成API数据模型 ====================

class TrainingFileManifestItem(BaseModel):
    """实训文件清单项"""
    form_field_name: str = Field(..., description="在表单中对应的文件字段名")
    original_filename: str = Field(..., description="文件的原始名称")
    file_type: Literal[
        'sql_schema',           # 数据库结构定义 (create.sql)
        'sql_data',             # 数据库数据 (insert.sql)
        'bi_template',          # BI 设计器模板 (.tpo)
        'ai_template',          # AI 机器学习模板 (.tapp)
        'jupyter_notebook',     # 编码式实训的 .ipynb 文件
        'supporting_asset'      # 其他支持性素材 (图片, 视频等)
    ] = Field(..., description="文件类型")


class FullTrainingManifest(BaseModel):
    """完整实训包的清单和生成参数"""
    training_title: str = Field(..., description="实训的正式名称，如 '某零售企业经营分析'")
    analysis_goals: List[str] = Field(..., description="手动提供的核心分析目标清单", example=["分析总体销售趋势", "分析各产品线贡献度"])
    training_type: Literal['拖拽式', '编码式'] = Field(..., description="实训类型")
    files: List[TrainingFileManifestItem] = Field(..., description="所有上传文件的清单列表")


class TrainingMetadata(BaseModel):
    """实训元数据模型"""
    training_name: str = Field(..., description="实训名称")
    introduction: str = Field(..., description="实训介绍")
    industry: str = Field(..., description="所属行业")
    difficulty: str = Field(..., description="难度等级")
    duration_hours: int = Field(..., description="持续时间（小时）")
    training_type: str = Field(..., description="实训类型")
    homework_nodes: List[Dict[str, Any]] = Field(..., description="作业节点配置")
    require_report: bool = Field(..., description="是否需要实验报告")


class FullTrainingPackageResponse(BaseModel):
    """完整实训包生成结果"""
    metadata: TrainingMetadata = Field(..., description="由AI根据SQL和文件清单生成的元数据")
    handbook_markdown: str = Field(..., description="Markdown格式的实训手册初稿")


class TrainingTaskCreateResponse(BaseModel):
    """实训任务创建响应"""
    task_id: str = Field(..., description="任务ID")
    message: str = Field(..., description="响应消息")


class TrainingDatabasePersistResult(BaseModel):
    """实训数据库持久化结果"""
    success: bool
    message: str
    training_id: Optional[int] = None
    dataset_ids: Optional[List[int]] = None
    jupyter_file_ids: Optional[List[int]] = None
    asset_ids: Optional[List[int]] = None  # 新增：支持性素材ID列表
    details: Optional[Dict[str, Any]] = None


class ExtendedTrainingTaskResult(BaseModel):
    """扩展的实训任务结果（包含数据库持久化信息）"""
    training_package: FullTrainingPackageResponse = Field(..., description="实训包生成结果")
    database_result: Optional[TrainingDatabasePersistResult] = Field(None, description="数据库持久化结果")


class TrainingTaskStatusResponse(BaseModel):
    """实训任务状态响应"""
    task_id: str = Field(..., description="任务ID")
    status: Literal['PENDING', 'PROCESSING', 'SUCCESS', 'ERROR'] = Field(..., description="任务状态")
    progress: Optional[int] = Field(None, description="进度百分比 (0-100)")
    result: Optional[Union[FullTrainingPackageResponse, ExtendedTrainingTaskResult, Dict[str, Any]]] = Field(None, description="完成结果（仅成功时）")
    error_message: Optional[str] = Field(None, description="错误信息（仅失败时）") 