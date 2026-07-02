"""
资源同步服务的数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Literal
from pydantic import BaseModel, Field, validator
import hashlib
import json


class ResourceType(str, Enum):
    """资源类型枚举"""
    PRACTICE = "practice"
    TRAINING = "training"


class TrainingType(str, Enum):
    """实训类型枚举"""
    DRAG_AND_DROP = "drag_and_drop"
    CODING = "coding"


class Difficulty(str, Enum):
    """难度级别枚举"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ToolType(str, Enum):
    """工具类型枚举"""
    BI = "BI"
    AI = "AI"


class ValidationError(Exception):
    """验证错误"""
    pass


class MetadataModel(BaseModel):
    """元数据基础模型"""
    schema_version: str = Field(..., description="模式版本", example="1.0.0")
    id: str = Field(..., description="全局唯一ID", min_length=1, max_length=100)
    title: str = Field(..., description="标题", min_length=1, max_length=200)
    intro: str = Field(..., description="简介", min_length=10, max_length=2000)
    industry: str = Field(..., description="行业", min_length=1, max_length=50)
    difficulty: Difficulty = Field(..., description="难度级别")
    course_hours: int = Field(..., description="课程学时", ge=1, le=100)
    estimated_completion_time: str = Field(..., description="预计完成时间", example="2-3周")
    prerequisites: List[str] = Field(default_factory=list, description="先修要求")
    learning_objectives: List[str] = Field(default_factory=list, description="学习目标")
    tags: List[str] = Field(default_factory=list, description="标签")
    max_students: int = Field(default=50, description="最大学生数", ge=1, le=500)
    is_active: bool = Field(default=True, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    checksum: Optional[str] = Field(None, description="校验和")
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="验证规则")

    @validator('id')
    def validate_id(cls, v):
        """验证ID格式"""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('ID只能包含字母、数字、横线和下划线')
        return v

    @validator('updated_at', always=True)
    def set_updated_at(cls, v, values):
        """自动设置更新时间"""
        return datetime.now()

    def calculate_checksum(self) -> str:
        """计算校验和"""
        # 排除checksum和时间字段
        data = self.dict(exclude={'checksum', 'created_at', 'updated_at'})
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

    def validate_checksum(self) -> bool:
        """验证校验和"""
        if not self.checksum:
            return False
        return self.checksum == self.calculate_checksum()

    def validate_file_dependencies(self, base_path: str) -> List[str]:
        """验证文件依赖"""
        from pathlib import Path

        missing_files = []
        rules = self.validation_rules.get('file_dependencies', [])

        base_path_obj = Path(base_path)
        for rule in rules:
            if not (base_path_obj / rule).exists():
                missing_files.append(rule)

        return missing_files


class PracticeMetadata(MetadataModel):
    """实践课程元数据"""
    resource_type: Literal[ResourceType.PRACTICE] = Field(default=ResourceType.PRACTICE)

    handbook_content_path: str = Field(..., description="手册内容路径")
    cover_url_path: str = Field(..., description="封面图片路径")

    # 实践特定字段
    repo_template_path: Optional[str] = Field(None, description="代码仓库模板路径")
    test_cases_path: Optional[str] = Field(None, description="测试用例路径")

    require_experiment_report: bool = Field(default=True, description="是否需要实验报告")

    # 关联的实践资源路径（从metadata.json读取的字符串列表）
    practices: List[str] = Field(default_factory=list, description="关联的实践资源路径")

    # 教学资源列表
    resources: List[Dict[str, Any]] = Field(default_factory=list, description="教学资源列表")

    # 题库数据（运行时动态添加）
    question_bank: Optional[Dict[str, Any]] = Field(None, description="题库数据")

    # 考试配置（运行时动态添加）
    exam_configurations: Optional[Dict[str, Any]] = Field(None, description="考试配置")


class TrainingMetadata(MetadataModel):
    """实训课程元数据"""
    resource_type: Literal[ResourceType.TRAINING] = Field(default=ResourceType.TRAINING)

    training_type: TrainingType = Field(..., description="实训类型")

    handbook_content_path: str = Field(..., description="手册内容路径")
    cover_url_path: Optional[str] = Field(None, description="封面图片路径")

    assignment_nodes: List[Dict[str, Any]] = Field(default_factory=list, description="作业节点")
    require_design_files: bool = Field(default=False, description="是否需要设计文件")
    require_experiment_report: bool = Field(default=True, description="是否需要实验报告")

    # 实训特定字段
    jupyter_notebooks_path: Optional[str] = Field(None, description="Jupyter笔记本路径")
    datasets_path: Optional[str] = Field(None, description="数据集路径")


class FileDependency(BaseModel):
    """文件依赖"""
    path: str
    type: str  # 'required', 'optional'
    description: str = ""


class ResourceManifest(BaseModel):
    """资源清单"""
    metadata: Union[PracticeMetadata, TrainingMetadata]
    base_path: str
    files: Dict[str, FileDependency] = Field(default_factory=dict)
    practices: List[Dict[str, Any]] = Field(default_factory=list)  # 关联的实践资源
    last_modified: datetime = Field(default_factory=datetime.now)
    discovered_at: datetime = Field(default_factory=datetime.now)


class SyncAction(BaseModel):
    """同步动作"""
    action_type: str  # 'create', 'update', 'delete', 'soft_delete'
    resource_id: str
    resource_type: ResourceType
    manifest: Optional[ResourceManifest] = None
    changes: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None


class SyncPlan(BaseModel):
    """同步计划"""
    created_at: datetime = Field(default_factory=datetime.now)
    actions: List[SyncAction] = Field(default_factory=list)

    def add_action(self, action: SyncAction):
        """添加动作"""
        self.actions.append(action)

    def get_actions_by_type(self, action_type: str) -> List[SyncAction]:
        """按类型获取动作"""
        return [a for a in self.actions if a.action_type == action_type]


class SyncResult(BaseModel):
    """同步结果"""
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    success: bool = False
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    def add_error(self, action: SyncAction, error: str):
        """添加错误"""
        self.failed_actions += 1
        self.errors.append({
            'action': action.dict(),
            'error': error,
            'timestamp': datetime.now()
        })

    def add_success(self, action: SyncAction):
        """添加成功"""
        self.successful_actions += 1

    def complete(self):
        """完成同步"""
        self.completed_at = datetime.now()
        self.total_actions = len(self.errors) + self.successful_actions
        self.success = self.failed_actions == 0


# 变更类型
class Change(BaseModel):
    """变更基类"""
    pass


class ResourceState(BaseModel):
    """资源状态"""
    id: str
    resource_type: ResourceType
    checksum: Optional[str] = None
    last_modified: datetime
    metadata: Dict[str, Any]
    files: Dict[str, Any] = Field(default_factory=dict)


class VersionChange(Change):
    """版本变更"""
    field: str = Field(..., description="变更字段")
    old_value: Optional[Any] = Field(None, description="旧值")
    new_value: Optional[Any] = Field(None, description="新值")


class MetadataChange(Change):
    """元数据变更"""
    field: str = Field(..., description="变更字段")
    old_value: Optional[Any] = Field(None, description="旧值")
    new_value: Optional[Any] = Field(None, description="新值")


class FileDependencyChange(Change):
    """文件依赖变更"""
    added_files: List[str] = Field(default_factory=list, description="新增文件")
    removed_files: List[str] = Field(default_factory=list, description="删除文件")


class HealthStatus(BaseModel):
    """健康状态"""
    timestamp: datetime = Field(default_factory=datetime.now)
    overall_health: str  # 'healthy', 'warning', 'critical'
    success_rate: float
    total_operations: int
    last_sync_time: Optional[datetime] = None
    details: Dict[str, Any] = Field(default_factory=dict)
