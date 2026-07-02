"""
单一来源事实 - V3.0 资源同步服务模型

定义了ziyuan目录中metadata.json的标准结构和验证模型。
支持实训资源和实践资源的统一管理。
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field, validator, model_validator, field_validator
from datetime import datetime
from pathlib import Path
import hashlib
import json


# ==================== 基础枚举类型 ====================

class ResourceType(str):
    """资源类型枚举"""
    TRAINING = "training"  # 实训资源
    PRACTICE = "practice"  # 实践资源


class TrainingType(str):
    """实训类型枚举"""
    DRAG_DROP = "drag_and_drop"  # 拖拽式实训 (BI/AI)
    CODING = "coding"           # 编码式实训 (Jupyter)


class Difficulty(str):
    """难度等级枚举"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class EnvironmentType(str):
    """环境类型枚举"""
    JUPYTER = "JUPYTER"        # Jupyter环境
    HUIXUE_BI = "HUIXUE_BI"      # BI分析环境
    TEMPO_AI = "TEMPO_AI"      # AI设计器环境
    VDI = "VDI"                # 虚拟桌面
    CLI = "CLI"                # 命令行环境


class AssetType(str):
    """资源类型枚举"""
    HANDBOOK = "handbook"      # 实验手册
    COVER = "cover"           # 封面图片
    DATASET = "dataset"       # 数据集
    SQL_SCRIPT = "sql_script" # SQL脚本
    BI_TEMPLATE = "bi_template" # BI仪表盘模板
    AI_MODEL = "ai_model"     # AI模型文件
    OTHER = "other"           # 其他文件


# ==================== 数据模型 ====================

class EnvironmentConfig(BaseModel):
    """环境配置模型"""
    env_type: EnvironmentType = Field(..., description="环境类型")
    docker_image_name: str = Field(..., description="Docker镜像名称")

    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True


class DataSource(BaseModel):
    """数据源配置模型"""
    type: str = Field(..., description="数据源类型: sql, csv, api")
    table_name: Optional[str] = Field(None, description="目标表名")
    file_path: Optional[str] = Field(None, description="文件路径")
    record_count: Optional[int] = Field(None, description="记录数量")
    is_production_data: bool = Field(False, description="是否为生产数据")

    class Config:
        arbitrary_types_allowed = True


class ContentResource(BaseModel):
    """内容资源模型"""
    name: str = Field(..., description="资源名称")
    path: str = Field(..., description="相对路径")
    type: Optional[AssetType] = Field(None, description="资源类型")
    description: Optional[str] = Field(None, description="资源描述")
    data_source: Optional[DataSource] = Field(None, description="数据源配置")

    class Config:
        arbitrary_types_allowed = True


class AssignmentNode(BaseModel):
    """作业节点模型"""
    node_name: str = Field(..., description="节点名称")
    tool_type: Literal["BI", "AI"] = Field(..., description="工具类型")

    class Config:
        arbitrary_types_allowed = True


class ContentManifest(BaseModel):
    """内容清单模型"""
    datasets: List[ContentResource] = Field(default_factory=list, description="数据集列表")
    sql_scripts: List[ContentResource] = Field(default_factory=list, description="SQL脚本列表")
    bi_templates: List[ContentResource] = Field(default_factory=list, description="BI模板列表")
    ai_models: List[ContentResource] = Field(default_factory=list, description="AI模型列表")

    class Config:
        arbitrary_types_allowed = True


# ==================== 主元数据模型 ====================

class ResourceMetadata(BaseModel):
    """资源元数据模型 - V3.0 统一标准"""

    # 基础标识信息
    id: str = Field(..., description="全局唯一ID", min_length=1, max_length=100)
    version: str = Field("1.0.0", description="内容版本号", pattern=r'^\d+\.\d+\.\d+$')
    title: str = Field(..., description="资源标题", min_length=1, max_length=200)

    # 资源类型和分类
    resource_type: ResourceType = Field(..., description="资源类型")
    training_type: Optional[TrainingType] = Field(None, description="实训类型(仅实训资源)")
    intro: str = Field(..., description="简介", min_length=1, max_length=1000)
    industry: str = Field(..., description="所属行业", min_length=1, max_length=100)
    difficulty: Difficulty = Field(..., description="难度等级")

    @field_validator('resource_type', mode='before')
    @classmethod
    def validate_resource_type(cls, v):
        if isinstance(v, str):
            return ResourceType(v)
        return v

    @field_validator('training_type', mode='before')
    @classmethod
    def validate_training_type(cls, v):
        if isinstance(v, str):
            return TrainingType(v)
        return v

    @field_validator('difficulty', mode='before')
    @classmethod
    def validate_difficulty(cls, v):
        if isinstance(v, str):
            return Difficulty(v)
        return v
    course_hours: int = Field(..., description="课程学时", ge=1, le=100)

    # 内容资源指针
    handbook_content_path: str = Field(..., description="手册文件相对路径")
    cover_url_path: Optional[str] = Field(None, description="封面图片相对路径")

    # 环境配置
    environment_config: EnvironmentConfig = Field(..., description="环境配置")

    @field_validator('environment_config', mode='before')
    @classmethod
    def validate_environment_config(cls, v):
        if isinstance(v, dict):
            # 转换env_type字符串为枚举
            if 'env_type' in v and isinstance(v['env_type'], str):
                v['env_type'] = EnvironmentType(v['env_type'])
        return v

    # 内容资源清单
    content_resources: ContentManifest = Field(default_factory=ContentManifest, description="内容资源清单")

    # 作业配置
    assignment_nodes: List[AssignmentNode] = Field(default_factory=list, description="作业节点列表")
    require_design_files: bool = Field(False, description="是否需要提交设计文件")
    require_experiment_report: bool = Field(True, description="是否需要提交实验报告")

    # 时间戳（可选，用于版本控制）
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    @validator('id')
    def validate_id_format(cls, v):
        """验证ID格式"""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('ID只能包含字母、数字、下划线和连字符')
        return v


    @model_validator(mode='after')
    def validate_business_rules(self):
        """验证业务规则"""
        # 验证实训类型
        if self.resource_type == ResourceType.TRAINING and not self.training_type:
            raise ValueError('实训资源必须指定training_type')
        if self.resource_type == ResourceType.PRACTICE and self.training_type:
            raise ValueError('实践资源不能指定training_type')

        # 验证内容路径
        handbook_path = self.handbook_content_path
        if handbook_path and not Path(handbook_path).suffix.lower() in ['.md', '.markdown']:
            raise ValueError('handbook_content_path必须指向markdown文件')

        cover_path = self.cover_url_path
        if cover_path and not Path(cover_path).suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
            raise ValueError('cover_url_path必须指向图片文件')

        return self

    def calculate_checksum(self) -> str:
        """计算元数据的校验和"""
        # 将模型序列化为JSON并计算MD5
        data = self.dict(exclude={'created_at', 'updated_at'})
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode('utf-8')).hexdigest()

    def get_resource_paths(self) -> List[str]:
        """获取所有资源文件路径"""
        paths = []

        # 基础资源
        if self.handbook_content_path:
            paths.append(self.handbook_content_path)
        if self.cover_url_path:
            paths.append(self.cover_url_path)

        # 内容资源清单中的文件
        for resource_list in [
            self.content_resources.datasets,
            self.content_resources.sql_scripts,
            self.content_resources.bi_templates,
            self.content_resources.ai_models
        ]:
            for resource in resource_list:
                paths.append(resource.path)

        return paths

    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# ==================== 同步相关模型 ====================

class SyncActionType(str):
    """同步动作类型"""
    CREATE = "create"      # 创建
    UPDATE = "update"      # 更新
    DELETE = "delete"      # 删除


class ResourceManifest(BaseModel):
    """资源清单模型"""
    metadata: ResourceMetadata
    base_path: Path
    last_modified: datetime
    checksum: str
    resource_files: Dict[str, Dict[str, Any]]  # path -> file_info

    @classmethod
    def from_metadata(cls, metadata: ResourceMetadata, base_path: Path) -> ResourceManifest:
        """从元数据创建资源清单"""
        checksum = metadata.calculate_checksum()
        last_modified = datetime.now()

        # 收集资源文件信息
        resource_files = {}
        for file_path in metadata.get_resource_paths():
            full_path = base_path / file_path
            if full_path.exists():
                stat = full_path.stat()
                resource_files[file_path] = {
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'exists': True
                }
            else:
                resource_files[file_path] = {
                    'exists': False,
                    'error': 'File not found'
                }

        return cls(
            metadata=metadata,
            base_path=base_path,
            last_modified=last_modified,
            checksum=checksum,
            resource_files=resource_files
        )


class SyncAction(BaseModel):
    """同步动作模型"""
    action_type: SyncActionType
    resource_id: str
    resource_type: ResourceType
    manifest: Optional[ResourceManifest] = None  # CREATE/UPDATE时使用
    reason: Optional[str] = None  # 动作原因

    @field_validator('action_type', mode='before')
    @classmethod
    def validate_action_type(cls, v):
        if isinstance(v, str):
            return SyncActionType(v)
        return v

    @field_validator('resource_type', mode='before')
    @classmethod
    def validate_resource_type_sync(cls, v):
        if isinstance(v, str):
            return ResourceType(v)
        return v

    class Config:
        arbitrary_types_allowed = True

    def __str__(self) -> str:
        return f"{self.action_type} {self.resource_type}:{self.resource_id}"


class SyncPlan(BaseModel):
    """同步计划模型"""
    actions: List[SyncAction] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    summary: Dict[str, int] = Field(default_factory=dict)  # action_type -> count

    class Config:
        arbitrary_types_allowed = True

    def add_action(self, action: SyncAction):
        """添加同步动作"""
        self.actions.append(action)
        self.summary[action.action_type] = self.summary.get(action.action_type, 0) + 1

    def get_summary_text(self) -> str:
        """获取摘要文本"""
        parts = []
        for action_type, count in self.summary.items():
            parts.append(f"{action_type}: {count}")
        return ", ".join(parts)


class SyncResult(BaseModel):
    """同步结果模型"""
    success: bool = False
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def add_error(self, action: SyncAction, error: str):
        """添加错误"""
        self.failed_actions += 1
        self.errors.append({
            'action': str(action),
            'resource_id': action.resource_id,
            'error': error,
            'timestamp': datetime.now()
        })

    @property
    def duration_seconds(self) -> float:
        """执行时长（秒）"""
        if not self.completed_at:
            return 0.0
        return (self.completed_at - self.started_at).total_seconds()


class ValidationError(Exception):
    """验证错误"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


# ==================== 兼容性类型 ====================

# 为了向后兼容保留旧的类型名
TrainingMetadata = ResourceMetadata
TrainingType = TrainingType
Difficulty = Difficulty
