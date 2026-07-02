from sqlalchemy.orm import Session
from sqlalchemy import func, or_ as db_or_
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import json
import logging
from app import models, schemas

logger = logging.getLogger(__name__)


def get_training_environments(db: Session):
    """获取实训环境列表"""
    environments = db.query(models.TrainingEnvironment).filter(
        models.TrainingEnvironment.is_active == True
    ).all()
    
    return [
        {
            "id": str(env.id),
            "name": env.name,
            "environment_type": env.environment_type,
            "description": env.description,
            "default_storage": env.default_storage,
            "default_memory": env.default_memory,
            "default_cpu": env.default_cpu,
            "is_active": env.is_active
        }
        for env in environments
    ]

def create_training(db: Session, training_data: dict, creator_id: int):
    """创建实训"""
    import json
    
    # 创建实训记录
    training = models.Training(
        title=training_data["title"],
        training_type=training_data["training_type"],
        intro=training_data["intro"],
        industry=training_data.get("industry"),
        difficulty=training_data["difficulty"],
        course_hours=training_data["course_hours"],
        handbook_content=training_data.get("handbook_content"),
        assignment_nodes=json.dumps(training_data.get("assignment_nodes", [])),
        require_design_files=training_data["require_design_files"],
        require_experiment_report=training_data["require_experiment_report"],
        environment_id=training_data.get("environment_id"),
        storage_limit=training_data.get("environment_config", {}).get("storage_limit", "1Gi"),
        memory_limit=training_data.get("environment_config", {}).get("memory_limit", "1Gi"),
        cpu_limit=training_data.get("environment_config", {}).get("cpu_limit", "1"),
        creator_id=creator_id
    )
    
    db.add(training)
    db.commit()
    db.refresh(training)
    
    return training

def get_training_detail(db: Session, training_id: int, creator_id: int):
    """获取实训详情"""
    training = db.query(models.Training).filter(
        models.Training.id == training_id,
        models.Training.creator_id == creator_id
    ).first()
    
    if not training:
        return None
    
    # 获取数据集
    datasets = db.query(models.TrainingDataset).filter(
        models.TrainingDataset.training_id == training_id
    ).all()
    
    # 获取创建者信息
    creator = db.query(models.User).filter(models.User.id == creator_id).first()
    
    return {
        "id": training.id,
        "title": training.title,
        "training_type": training.training_type,
        "intro": training.intro,
        "industry": training.industry,
        "difficulty": training.difficulty,
        "course_hours": training.course_hours,
        "handbook_content": training.handbook_content,
        "assignment_nodes": training.assignment_nodes,
        "require_design_files": training.require_design_files,
        "require_experiment_report": training.require_experiment_report,
        "environment_id": training.environment_id,
        "storage_limit": training.storage_limit,
        "memory_limit": training.memory_limit,
        "cpu_limit": training.cpu_limit,
        "publish_status": training.publish_status,
        "visibility": training.visibility,
        "is_published": training.is_published,
        "published_at": training.published_at,
        "creator_id": training.creator_id,
        "creator_name": creator.full_name or creator.username if creator else None,
        "created_at": training.created_at,
        "updated_at": training.updated_at,
        "dataset_count": len(datasets),
        "datasets": [
            {
                "id": dataset.id,
                "name": dataset.name,
                "file_url": dataset.file_url,
                "file_type": dataset.file_type,
                "file_size": dataset.file_size,
                "file_size_display": _format_file_size(dataset.file_size),
                "description": dataset.description,
                "access_path": dataset.access_path,
                "uploader_id": dataset.uploader_id,
                "created_at": dataset.created_at
            }
            for dataset in datasets
        ]
    }

def update_training(db: Session, training_id: int, training_data: dict, creator_id: int):
    """更新实训"""
    import json
    
    training = db.query(models.Training).filter(
        models.Training.id == training_id,
        models.Training.creator_id == creator_id
    ).first()
    
    if not training:
        return None
    
    # 更新字段
    for field, value in training_data.items():
        if field == "assignment_nodes" and value is not None:
            setattr(training, field, json.dumps(value))
        elif field == "environment_config" and value is not None:
            # 更新环境配置相关字段
            setattr(training, "storage_limit", value.get("storage_limit", training.storage_limit))
            setattr(training, "memory_limit", value.get("memory_limit", training.memory_limit))
            setattr(training, "cpu_limit", value.get("cpu_limit", training.cpu_limit))
        elif hasattr(training, field) and value is not None:
            setattr(training, field, value)
    
    db.commit()
    db.refresh(training)
    
    return training

def get_user_trainings(
    db: Session,
    creator_id: int,
    skip: int = 0,
    limit: int = 20,
    keyword: Optional[str] = None,
    training_type: Optional[str] = None,
    publish_status: Optional[str] = None
):
    """获取用户创建的实训列表"""
    query = db.query(models.Training).filter(
        models.Training.creator_id == creator_id
    )
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            models.Training.title.contains(keyword)
        )
    
    # 实训类型筛选
    if training_type:
        query = query.filter(models.Training.training_type == training_type)
    
    # 发布状态筛选
    if publish_status:
        query = query.filter(models.Training.publish_status == publish_status)
    
    # 总数
    total = query.count()
    
    # 分页查询
    trainings = query.order_by(models.Training.created_at.desc()).offset(skip).limit(limit).all()
    
    # 获取数据集数量
    training_ids = [t.id for t in trainings]
    dataset_counts = {}
    if training_ids:
        dataset_query = db.query(
            models.TrainingDataset.training_id,
            func.count(models.TrainingDataset.id).label('count')
        ).filter(
            models.TrainingDataset.training_id.in_(training_ids)
        ).group_by(models.TrainingDataset.training_id).all()
        
        dataset_counts = {item.training_id: item.count for item in dataset_query}
    
    # 构建响应
    training_list = []
    for training in trainings:
        training_list.append({
            "id": training.id,
            "title": training.title,
            "training_type": training.training_type,
            "intro": training.intro,
            "industry": training.industry,
            "difficulty": training.difficulty,
            "course_hours": training.course_hours,
            "publish_status": training.publish_status,
            "visibility": training.visibility,
            "is_published": training.is_published,
            "published_at": training.published_at,
            "creator_id": training.creator_id,
            "created_at": training.created_at,
            "updated_at": training.updated_at,
            "dataset_count": dataset_counts.get(training.id, 0)
        })
    
    return {
        "list": training_list,
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit
    }

def upload_training_dataset(
    db: Session,
    training_id: int,
    dataset_data: dict,
    creator_id: int
):
    """上传实训数据集"""
    # 检查实训是否存在且属于当前用户
    training = db.query(models.Training).filter(
        models.Training.id == training_id,
        models.Training.creator_id == creator_id
    ).first()
    
    if not training:
        return None
    
    # 创建数据集记录
    dataset = models.TrainingDataset(
        training_id=training_id,
        name=dataset_data["name"],
        file_url=dataset_data["file_url"],
        file_type=dataset_data["file_type"],
        file_size=dataset_data["file_size"],
        description=dataset_data.get("description"),
        access_path=f"/datasets/{training_id}/{dataset_data['name']}",
        uploader_id=creator_id
    )
    
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    return {
        "id": dataset.id,
        "name": dataset.name,
        "file_url": dataset.file_url,
        "file_type": dataset.file_type,
        "file_size": dataset.file_size,
        "file_size_display": _format_file_size(dataset.file_size),
        "description": dataset.description,
        "access_path": dataset.access_path,
        "uploader_id": dataset.uploader_id,
        "created_at": dataset.created_at
    }

def delete_training_dataset(
    db: Session,
    training_id: int,
    dataset_id: int,
    creator_id: int
):
    """删除实训数据集"""
    # 检查实训是否存在且属于当前用户
    training = db.query(models.Training).filter(
        models.Training.id == training_id,
        models.Training.creator_id == creator_id
    ).first()
    
    if not training:
        return False
    
    # 删除数据集
    dataset = db.query(models.TrainingDataset).filter(
        models.TrainingDataset.id == dataset_id,
        models.TrainingDataset.training_id == training_id
    ).first()
    
    if dataset:
        db.delete(dataset)
        db.commit()
        return True
    
    return False

def publish_training(
    db: Session,
    training_id: int,
    creator_id: int,
    visibility: str = "PRIVATE"
):
    """发布实训"""
    training = db.query(models.Training).filter(
        models.Training.id == training_id,
        models.Training.creator_id == creator_id
    ).first()
    
    if not training:
        return None
    
    # 更新发布状态
    training.publish_status = models.TrainingPublishStatusEnum.PUBLISHED
    training.visibility = models.TrainingVisibilityEnum(visibility)
    training.is_published = True
    training.published_at = func.now()
    
    db.commit()
    db.refresh(training)
    
    return training

def get_training_jupyter_files(db: Session, training_id: int, creator_id: int):
    """获取实训的Jupyter文件列表"""
    # 检查实训是否存在且属于当前用户
    training = db.query(models.Training).filter(
        models.Training.id == training_id,
        models.Training.creator_id == creator_id
    ).first()
    
    if not training:
        return None
    
    files = db.query(models.TrainingJupyterFile).filter(
        models.TrainingJupyterFile.training_id == training_id
    ).order_by(models.TrainingJupyterFile.is_main_file.desc(), models.TrainingJupyterFile.created_at).all()
    
    return [
        {
            "id": file.id,
            "file_name": file.file_name,
            "file_content": file.file_content,
            "file_path": file.file_path,
            "is_main_file": file.is_main_file,
            "created_at": file.created_at,
            "updated_at": file.updated_at
        }
        for file in files
    ]

def upload_training_jupyter_file(
    db: Session,
    training_id: int,
    file_data: dict,
    creator_id: int
):
    """上传Jupyter文件"""
    # 检查实训是否存在且属于当前用户
    training = db.query(models.Training).filter(
        models.Training.id == training_id,
        models.Training.creator_id == creator_id
    ).first()
    
    if not training:
        return None
    
    # 如果设置为主文件，先取消其他文件的主文件状态
    if file_data.get("is_main_file", False):
        db.query(models.TrainingJupyterFile).filter(
            models.TrainingJupyterFile.training_id == training_id
        ).update({"is_main_file": False})
    
    # 创建文件记录
    jupyter_file = models.TrainingJupyterFile(
        training_id=training_id,
        file_name=file_data["file_name"],
        file_content=file_data["file_content"],
        file_path=f"/jupyter/{training_id}/{file_data['file_name']}",
        is_main_file=file_data.get("is_main_file", False)
    )
    
    db.add(jupyter_file)
    db.commit()
    db.refresh(jupyter_file)
    
    return {
        "id": jupyter_file.id,
        "file_name": jupyter_file.file_name,
        "file_content": jupyter_file.file_content,
        "file_path": jupyter_file.file_path,
        "is_main_file": jupyter_file.is_main_file,
        "created_at": jupyter_file.created_at,
        "updated_at": jupyter_file.updated_at
    }

def delete_training_jupyter_file(
    db: Session,
    training_id: int,
    file_id: int,
    creator_id: int
):
    """删除Jupyter文件"""
    # 检查实训是否存在且属于当前用户
    training = db.query(models.Training).filter(
        models.Training.id == training_id,
        models.Training.creator_id == creator_id
    ).first()
    
    if not training:
        return False
    
    # 删除文件
    jupyter_file = db.query(models.TrainingJupyterFile).filter(
        models.TrainingJupyterFile.id == file_id,
        models.TrainingJupyterFile.training_id == training_id
    ).first()
    
    if jupyter_file:
        db.delete(jupyter_file)
        db.commit()
        return True
    
    return False

def delete_training(db: Session, training_id: int, creator_id: int):
    """删除实训"""
    training = db.query(models.Training).filter(
        models.Training.id == training_id,
        models.Training.creator_id == creator_id
    ).first()
    
    if not training:
        return False
    
    # 删除相关数据集
    db.query(models.TrainingDataset).filter(
        models.TrainingDataset.training_id == training_id
    ).delete()
    
    # 删除相关Jupyter文件
    db.query(models.TrainingJupyterFile).filter(
        models.TrainingJupyterFile.training_id == training_id
    ).delete()
    
    # 删除实训
    db.delete(training)
    db.commit()
    
    return True

def _format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


# ==================== 实训资源库相关功能 ====================

def get_training_library(
    db: Session,
    keyword: Optional[str] = None,
    training_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    tags: Optional[List[str]] = None,
    is_preset: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Dict[str, Any]:
    """
    获取实训库列表（包括平台预设和用户发布的公开实训）
    
    Args:
        db: 数据库会话
        keyword: 搜索关键词
        training_type: 实训类型筛选
        difficulty: 难度筛选
        tags: 标签筛选
        is_preset: 是否只显示平台预设
        skip: 跳过记录数
        limit: 每页记录数
        sort_by: 排序字段
        sort_order: 排序方向
    
    Returns:
        包含实训列表和分页信息的字典
    """
    # 添加调试日志
    from app.utils.logger import logger
    logger.info(f"[DEBUG] get_training_library called with: keyword={keyword}, training_type={training_type}, difficulty={difficulty}, skip={skip}, limit={limit}")

    # 基础筛选：已发布且公开的实训
    query = db.query(models.Training).filter(
        models.Training.is_published == True,
        models.Training.visibility == models.TrainingVisibilityEnum.PUBLIC
    )

    base_count = query.count()
    logger.info(f"[DEBUG] Base query (published + public): {base_count} records")
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            db_or_(
                models.Training.title.contains(keyword),
                models.Training.intro.contains(keyword)  # 使用intro字段而不是description
            )
        )
    
    # 类型筛选
    if training_type:
        logger.info(f"[DEBUG] Applying training_type filter: {training_type} (type: {type(training_type)})")
        # 确保传入的是枚举值
        if isinstance(training_type, str):
            # 将字符串转换为枚举
            try:
                type_enum = models.TrainingTypeEnum[training_type]
                query = query.filter(models.Training.training_type == type_enum)
            except KeyError:
                logger.warning(f"[DEBUG] Invalid training_type: {training_type}")
        else:
            query = query.filter(models.Training.training_type == training_type)
        logger.info(f"[DEBUG] After training_type filter, query count: {query.count()}")
    
    # 难度筛选
    if difficulty:
        logger.info(f"[DEBUG] Applying difficulty filter: {difficulty}")
        query = query.filter(models.Training.difficulty == difficulty)
    
    # 标签筛选 - 暂时跳过，因为Training模型中没有tags字段
    # if tags:
    #     # 使用JSON包含查询
    #     for tag in tags:
    #         query = query.filter(models.Training.tags.contains(f'"{tag}"'))
    
    # 获取总数
    total = query.count()
    
    # 排序 — 加 secondary key (id DESC) 保证多行 created_at 相同时分页稳定
    order_column = getattr(models.Training, sort_by, models.Training.created_at)
    if sort_order == "desc":
        query = query.order_by(order_column.desc(), models.Training.id.desc())
    else:
        query = query.order_by(order_column, models.Training.id.asc())

    # 分页
    trainings = query.offset(skip).limit(limit).all()
    
    # 获取创建者信息和参与人数
    training_list = []
    for training in trainings:
        # 获取创建者
        creator = db.query(models.User).filter(
            models.User.id == training.creator_id
        ).first()
        
        # 获取参与人数（课堂中使用该实训的学生数）
        participant_count = db.query(models.ClassroomTraining).filter(
            models.ClassroomTraining.training_id == training.id
        ).count()
        
        # 解析标签
        try:
            tags_list = json.loads(training.tags) if training.tags else []
        except:
            tags_list = []
        
        # 获取数据集数量
        dataset_count = len(training.datasets) if training.datasets else 0

        training_list.append({
            "id": training.id,
            "title": training.title,
            "intro": training.intro or "",  # 添加intro字段
            "training_type": training.training_type,
            "difficulty": training.difficulty,
            "industry": training.industry or "",  # 添加industry字段
            "course_hours": training.course_hours or 0,  # 使用course_hours而不是estimated_hours
            "dataset_count": dataset_count,  # 添加数据集数量
            "tags": tags_list,
            "is_preset": False,  # 暂时设为False，后续可以根据需要修改
            "creator_name": creator.full_name or creator.username if creator else "系统",
            "created_at": training.created_at.isoformat() if training.created_at else "",
            "updated_at": training.updated_at.isoformat() if training.updated_at else ""  # 添加updated_at字段
        })

    logger.info(f"[DEBUG] Final result: total={total}, list_length={len(training_list)}")
    logger.info(f"[DEBUG] Training list preview: {[t.get('title') for t in training_list[:3]]}")

    result = {
        "list": training_list,
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit
    }

    logger.info(f"[DEBUG] Returning result: {result}")
    return result


def get_training_detail_for_library(
    db: Session,
    training_id: int
) -> Optional[Dict[str, Any]]:
    """
    获取实训详情（用于实训库查看）
    
    Args:
        db: 数据库会话
        training_id: 实训ID
    
    Returns:
        实训详情字典或None
    """
    training = db.query(models.Training).filter(
        models.Training.id == training_id,
        models.Training.is_published == True
        # 注释掉不存在的字段
        # models.Training.is_active == True
    ).first()
    
    if not training:
        return None
    
    # 检查是否可以查看（简化逻辑，只检查可见性）
    # if not training.is_preset and training.visibility != models.TrainingVisibilityEnum.PUBLIC:
    if training.visibility != models.TrainingVisibilityEnum.PUBLIC:
        return None

    # 获取数据集
    datasets = db.query(models.TrainingDataset).filter(
        models.TrainingDataset.training_id == training_id
    ).all()

    # 获取创建者
    creator = db.query(models.User).filter(
        models.User.id == training.creator_id
    ).first()
    
    # 获取统计信息
    classroom_trainings = db.query(models.ClassroomTraining).filter(
        models.ClassroomTraining.training_id == training_id
    ).all()
    
    participant_count = len(classroom_trainings)
    
    # 计算完成率和平均分
    if participant_count > 0:
        # 这里需要根据实际的提交和评分表结构来计算
        # 暂时使用模拟数据
        completion_rate = 0.75
        average_score = 85.5
    else:
        completion_rate = 0.0
        average_score = 0.0
    
    # 解析元数据
    try:
        metadata = json.loads(training.metadata) if training.metadata else {}
    except:
        metadata = {}
    
    # 解析标签
    try:
        tags_list = json.loads(training.tags) if training.tags else []
    except:
        tags_list = []
    
    # 根据training_type确定environment_type
    environment_type_map = {
        models.TrainingTypeEnum.CODING: 'jupyter',
        models.TrainingTypeEnum.JUPYTER: 'jupyter',
        models.TrainingTypeEnum.DRAG_DROP: 'visual',
        models.TrainingTypeEnum.DATA_ANALYSIS: 'visual',
        models.TrainingTypeEnum.BI: 'visual'
    }
    environment_type = environment_type_map.get(training.training_type, 'visual')

    # 生成手册章节（基于手册内容）
    manual_sections = []
    if training.handbook_content:
        # 简单地将手册内容按段落分割成章节
        content_lines = training.handbook_content.split('\n\n')
        for i, line in enumerate(content_lines[:5]):  # 最多5个章节
            if line.strip():
                manual_sections.append({
                    "id": i + 1,
                    "title": f"第{i+1}节",
                    "content": line.strip()
                })

    return {
        "id": training.id,
        "title": training.title,
        "description": training.intro or "",  # 使用intro字段
        "training_type": training.training_type,
        "difficulty": training.difficulty,
        "estimated_hours": training.course_hours or 0,  # 使用course_hours字段
        "tags": tags_list,
        "creator_id": training.creator_id,
        "creator_name": creator.full_name or creator.username if creator else "系统",
        "publish_status": training.publish_status,
        "published_at": training.published_at if hasattr(training, 'published_at') else None,
        "project_path": training.project_path if hasattr(training, 'project_path') else None,
        "designer_type": training.designer_type if hasattr(training, 'designer_type') else None,
        "metadata": metadata,
        "created_at": training.created_at,
        "updated_at": training.updated_at,
        "participant_count": participant_count,
        "completion_rate": completion_rate,
        "average_score": average_score,
        # 前端需要的额外字段
        "goals": ["掌握基本概念", "学会实际操作", "完成项目实践"],
        "requirements": ["具备基本计算机操作能力", "了解相关领域基础知识"],
        "manualSections": manual_sections,
        "challenges": [],
        "isMLProject": training.training_type == models.TrainingTypeEnum.DRAG_DROP,
        "environment_type": environment_type,
        "content": training.handbook_content or "",
        "objectives": ["掌握基本概念", "学会实际操作", "完成项目实践"],
        "industry": training.industry or "通用",
        "trainingType": training.training_type,
        "model_text": "拖拽式" if training.training_type == models.TrainingTypeEnum.DRAG_DROP else "编码式",
        "difficulty_text": "初级" if training.difficulty == "beginner" else "中级" if training.difficulty == "intermediate" else "高级",
        "enrollCount": participant_count,
        "duration": f"{training.course_hours}课时" if training.course_hours else "未设置",
        "createdAt": training.created_at.strftime('%Y-%m-%d') if training.created_at else "",
        "datasets": [
            {
                "id": dataset.id,
                "name": dataset.name,
                "size": dataset.file_size or 0,
                "description": dataset.description or ""
            }
            for dataset in datasets
        ]
    }


def add_training_to_classroom(
    db: Session,
    classroom_id: int,
    training_data: Dict[str, Any],
    teacher_id: int
) -> Optional[Dict[str, Any]]:
    """
    将实训添加到课堂
    
    Args:
        db: 数据库会话
        classroom_id: 课堂ID
        training_data: 实训配置数据
        teacher_id: 教师ID
    
    Returns:
        课堂实训记录或None
    """
    # 检查课堂是否存在且教师有权限
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == teacher_id
    ).first()
    
    if not classroom:
        return None
    
    # 检查实训是否存在且已发布
    training = db.query(models.Training).filter(
        models.Training.id == training_data["training_id"],
        models.Training.is_published == True
    ).first()
    
    if not training:
        return None
    
    # 检查是否已经添加过
    existing = db.query(models.ClassroomTraining).filter(
        models.ClassroomTraining.classroom_id == classroom_id,
        models.ClassroomTraining.training_id == training_data["training_id"]
    ).first()
    
    if existing:
        return None
    
    # 创建课堂实训记录
    classroom_training = models.ClassroomTraining(
        classroom_id=classroom_id,
        training_id=training_data["training_id"]
    )
    
    db.add(classroom_training)
    db.commit()
    db.refresh(classroom_training)
    
    return {
        "id": classroom_training.id,
        "classroom_id": classroom_training.classroom_id,
        "training_id": classroom_training.training_id,
        "training_title": training.title,
        "training_type": training.training_type,
        "difficulty": training.difficulty,
        "estimated_hours": training.course_hours or 0,
        "added_at": classroom_training.added_at
    }


def get_classroom_trainings(
    db: Session,
    classroom_id: int,
    user_id: int,
    user_role: str
) -> List[Dict[str, Any]]:
    """
    获取课堂中的实训列表
    
    Args:
        db: 数据库会话
        classroom_id: 课堂ID
        user_id: 用户ID
        user_role: 用户角色 (teacher/student)
    
    Returns:
        实训列表
    """
    # 检查用户权限
    if user_role == "teacher":
        classroom = db.query(models.Classroom).filter(
            models.Classroom.id == classroom_id
        ).first()
    else:
        # 检查学生是否在课堂中
        student_classroom = db.query(models.ClassroomStudent).filter(
            models.ClassroomStudent.classroom_id == classroom_id,
            models.ClassroomStudent.student_id == user_id
        ).first()
        classroom = db.query(models.Classroom).filter(
            models.Classroom.id == classroom_id
        ).first() if student_classroom else None
    
    if not classroom:
        logger.warning(f"Classroom not found or access denied: classroom_id={classroom_id}, user_id={user_id}, role={user_role}")
        return []
    
    # 获取课堂实训列表
    classroom_trainings = db.query(models.ClassroomTraining).filter(
        models.ClassroomTraining.classroom_id == classroom_id
    ).all()
    
    logger.info(f"Found {len(classroom_trainings)} classroom trainings for classroom_id={classroom_id}")

    result = []
    for ct in classroom_trainings:
        # 使用原始SQL查询避免枚举值映射问题
        from sqlalchemy import text
        try:
            logger.info(f"Querying training details for training_id={ct.training_id}")
            result_row = db.execute(
                text("SELECT id, title, training_type, intro, industry, difficulty, course_hours, handbook_content, require_design_files, require_experiment_report, publish_status FROM trainings WHERE id = :id"),
                {"id": ct.training_id}
            ).first()
            if not result_row:
                logger.warning(f"Training not found for training_id={ct.training_id}")
                continue
            
            logger.info(f"Found training: {result_row[1]} (ID: {result_row[0]})")
            # 手动构建training对象
            class MockTraining:
                def __init__(self, row):
                    self.id = row[0]
                    self.title = row[1]
                    self.training_type = row[2]  # 字符串值
                    self.intro = row[3]
                    self.industry = row[4]
                    self.difficulty = row[5]  # 字符串值，可能是 'BEGINNER'
                    self.course_hours = row[6]
                    self.handbook_content = row[7]
                    self.require_design_files = row[8]
                    self.require_experiment_report = row[9]
                    self.publish_status = row[10]  # 发布状态

            training = MockTraining(result_row)
        except Exception as e:
            logger.error(f"查询Training失败: {e}")
            continue
        
        # 处理 difficulty 枚举值转换（兼容数据库中的大写值）
        difficulty_value = "beginner"
        try:
            # 如果 difficulty 是字符串，直接转换
            if isinstance(training.difficulty, str):
                difficulty_str = training.difficulty.upper()
                difficulty_map = {
                    "BEGINNER": "beginner",
                    "INTERMEDIATE": "intermediate",
                    "ADVANCED": "advanced"
                }
                difficulty_value = difficulty_map.get(difficulty_str, "beginner")
            elif hasattr(training.difficulty, 'value'):
                difficulty_value = training.difficulty.value.lower()
            else:
                difficulty_str = str(training.difficulty).upper()
                difficulty_map = {
                    "BEGINNER": "beginner",
                    "INTERMEDIATE": "intermediate",
                    "ADVANCED": "advanced"
                }
                difficulty_value = difficulty_map.get(difficulty_str, "beginner")
        except Exception as e:
            logger.warning(f"处理 difficulty 枚举值失败: {e}, 使用默认值 beginner")
            difficulty_value = "beginner"
        
        # 处理 training_type 枚举值转换
        training_type_value = str(training.training_type)
        try:
            if isinstance(training.training_type, str):
                training_type_value = training.training_type
            elif hasattr(training.training_type, 'value'):
                training_type_value = training.training_type.value
        except:
            pass
        
        # 根据发布状态确定前端需要的status值
        status_value = "unpublished"
        if training.publish_status:
            publish_status_upper = str(training.publish_status).upper()
            if publish_status_upper in ["PUBLISHED", "PUBLIC"]:
                status_value = "learning"  # 已发布的实训默认为学习中状态

        item = {
            "id": ct.id,
            "classroom_id": ct.classroom_id,
            "training_id": ct.training_id,
            "training_title": training.title,
            "training_type": training_type_value,
            "difficulty": difficulty_value,
            "estimated_hours": training.course_hours or 0,
            "start_time": None,  # ClassroomTraining没有这个字段
            "end_time": None,    # ClassroomTraining没有这个字段
            "allow_late_submission": False,  # ClassroomTraining没有这个字段
            "late_submission_days": 0,       # ClassroomTraining没有这个字段
            "created_at": ct.added_at,  # 使用实际存在的added_at字段
            "status": status_value,  # 添加状态字段
            "publish_status": training.publish_status  # 原始发布状态
        }
        
        # 暂时跳过学生进度检查（TrainingSession和TrainingSubmission模型不存在）
        # if user_role == "student":
        #     session = db.query(models.TrainingSession).filter(
        #         models.TrainingSession.classroom_training_id == ct.id,
        #         models.TrainingSession.student_id == user_id
        #     ).first()
        #
        #     if session:
        #         submission = db.query(models.TrainingSubmission).filter(
        #             models.TrainingSubmission.session_id == session.id
        #         ).first()
        #
        #         item["student_progress"] = {
        #             "session_id": session.id,
        #             "status": "completed" if submission else "in_progress" if session else "not_started",
        #             "progress_percentage": session.progress_percentage if session else 0,
        #             "last_active_time": session.last_active_time if session else None,
        #             "submission_time": submission.submission_time if submission else None,
        #             "score": submission.teacher_score or submission.auto_score if submission else None
        #         }
        #     else:
        #         item["student_progress"] = {
        #             "status": "not_started",
        #             "progress_percentage": 0
        #         }
        
        result.append(item)
    
    return result


def get_training_details(
    db: Session,
    training_id: int,
    user_id: int,
    user_role: str,
    classroom_id: int = None
) -> Optional[Dict[str, Any]]:
    """获取课堂实训详情"""
    import os
    from pathlib import Path
    from sqlalchemy import text

    # 校验 training 是否属于该 classroom (使用 ct_id 查询 classroom_trainings.id)
    if classroom_id is not None:
        ct_check = db.execute(
            text("SELECT 1 FROM classroom_trainings WHERE classroom_id = :cid AND id = :ct_id"),
            {"cid": classroom_id, "ct_id": training_id}
        ).first()
        if not ct_check:
            logger.warning(f"Training {training_id} is not associated with classroom {classroom_id}")
            return None

    # 使用原始SQL查询避免枚举值问题（需要JOIN classroom_trainings获取真实training_id）
    try:
        # 查找ct_id对应的真实training_id
        ct_row = db.execute(
            text("SELECT training_id FROM classroom_trainings WHERE id = :ct_id"),
            {"ct_id": training_id}
        ).first()
        if not ct_row:
            logger.error(f"ClassroomTraining {training_id} not found in DB")
            return None
        real_training_id = ct_row[0]

        result_row = db.execute(
            text("SELECT id, title, training_type, intro, industry, difficulty, course_hours, handbook_content, require_design_files, require_experiment_report FROM trainings WHERE id = :id"),
            {"id": real_training_id}
        ).first()
        if not result_row:
            logger.error(f"Training {real_training_id} not found in DB")
            return None

        # 手动构建training对象
        class MockTraining:
            def __init__(self, row, ct_id, real_tid):
                self.id = ct_id  # ct_id 供前端使用
                self.training_id = real_tid  # 真实training_id供bi-dataset API使用
                self.title = row[1]
                self.training_type = row[2]
                self.intro = row[3]
                self.industry = row[4]
                self.difficulty = row[5]  # 字符串值，可能是 'BEGINNER'
                self.course_hours = row[6]
                self.handbook_content = row[7]
                self.require_design_files = row[8]
                self.require_experiment_report = row[9]
                self.created_at = None  # 添加缺失的属性
                self.updated_at = None

        training = MockTraining(result_row, training_id, real_training_id)
    except Exception as e:
        import traceback
        logger.error(f"查询Training失败: {e}\n{traceback.format_exc()}")
        return None
    
    # SSOT V3.0: 优先从文件系统读取 handbook.md
    handbook_content = training.handbook_content or ""

    # 尝试根据 training_id 或 title 推断项目路径
    project_path = None
    from app.core.config import settings
    resource_base = settings.resource_base_path / "实训资源"
    
    if resource_base.exists():
        # 根据标题查找匹配的目录
        title_slug = training.title.replace(" ", "").replace("-", "")
        for dir_path in resource_base.iterdir():
            if dir_path.is_dir():
                dir_name_slug = dir_path.name.replace(" ", "").replace("-", "")
                if title_slug in dir_name_slug or dir_name_slug in title_slug:
                    project_path = dir_path
                    break
    
    # 如果找到项目路径，尝试读取 handbook.md
    if project_path and project_path.exists():
        handbook_file = project_path / "handbook.md"
        if handbook_file.exists():
            try:
                with open(handbook_file, 'r', encoding='utf-8') as f:
                    handbook_content = f.read()
                    logger.info(f"[SSOT V3.0] 从文件系统读取 handbook.md: {handbook_file}")
            except Exception as e:
                logger.warning(f"[SSOT V3.0] 读取 handbook.md 失败: {e}, 使用数据库内容")
    
    # 处理 difficulty 枚举值转换（兼容数据库中的大写值）
    difficulty_value = "beginner"
    try:
        if hasattr(training.difficulty, 'value'):
            difficulty_value = training.difficulty.value.lower()
        else:
            difficulty_str = str(training.difficulty).upper()
            # 映射大写值到小写
            difficulty_map = {
                "BEGINNER": "beginner",
                "INTERMEDIATE": "intermediate",
                "ADVANCED": "advanced"
            }
            difficulty_value = difficulty_map.get(difficulty_str, "beginner")
    except Exception as e:
        logger.warning(f"处理 difficulty 枚举值失败: {e}, 使用默认值 beginner")
        difficulty_value = "beginner"
    
    # 获取课堂信息
    classroom_info = None
    if classroom_id:
        classroom_row = db.execute(
            text("SELECT id, name, cover_url, start_date, end_date, teacher_id FROM classrooms WHERE id = :id"),
            {"id": classroom_id}
        ).first()
        if classroom_row:
            # 获取教师信息（从api_users表）
            teacher_name = "教师"
            if classroom_row[5]:  # teacher_id
                teacher_row = db.execute(
                    text("SELECT full_name FROM api_users WHERE id = :id"),
                    {"id": classroom_row[5]}
                ).first()
                if teacher_row:
                    teacher_name = teacher_row[0] or "教师"

            classroom_info = {
                "id": classroom_row[0],
                "name": classroom_row[1],
                "cover": classroom_row[2],
                "teacher_name": teacher_name,
                "start_date": str(classroom_row[3]) if classroom_row[3] else None,
                "end_date": str(classroom_row[4]) if classroom_row[4] else None
            }

    # 获取学生学习统计（教师端用）
    stats = {"learning": 0, "completed": 0, "not_started": 0}
    if classroom_id and user_role == "teacher":
        # 获取该课堂的学生总数
        student_count_row = db.execute(
            text("SELECT COUNT(*) FROM classroom_students WHERE classroom_id = :id"),
            {"id": classroom_id}
        ).first()
        total_students = student_count_row[0] if student_count_row else 0

        # 获取正在学习的学生数（有开始时间但没有结束时间）
        learning_row = db.execute(
            text("""
                SELECT COUNT(DISTINCT user_id) FROM training_learning_logs
                WHERE training_id = :training_id AND is_training_started = true AND end_time IS NULL
            """),
            {"training_id": training.training_id}
        ).first()
        stats["learning"] = learning_row[0] if learning_row else 0

        # 获取已完成的学生数（有结束时间）
        completed_row = db.execute(
            text("""
                SELECT COUNT(DISTINCT user_id) FROM training_learning_logs
                WHERE training_id = :training_id AND end_time IS NOT NULL
            """),
            {"training_id": training.training_id}
        ).first()
        stats["completed"] = completed_row[0] if completed_row else 0

        # 未开始 = 总数 - 学习中 - 已完成
        stats["not_started"] = max(0, total_students - stats["learning"] - stats["completed"])

    # 获取学生个人进度（学生端用）
    student_progress = {
        "status": "not_started",
        "completedPercentage": 0,
        "last_activity": None
    }
    if classroom_id and user_role == "student":
        # 获取关联的主 ClassroomTraining (使用 real_training_id)
        ct_row = db.execute(
            text("SELECT id FROM classroom_trainings WHERE classroom_id = :classroom_id AND training_id = :training_id"),
            {"classroom_id": classroom_id, "training_id": training.training_id}
        ).first()
        
        if ct_row:
            session_row = db.execute(
                text("""
                    SELECT id, progress_percentage, last_active_time
                    FROM training_sessions
                    WHERE classroom_training_id = :ct_id AND student_id = :user_id
                """),
                {"ct_id": ct_row[0], "user_id": user_id}
            ).first()

            if session_row:
                s_id, pct, last_time = session_row
                student_progress["completedPercentage"] = pct or 0
                student_progress["last_activity"] = str(last_time) if last_time else None
                
                # 查询 submission 确认是否已提交
                sub_row = db.execute(
                    text("SELECT id FROM training_submissions WHERE session_id = :s_id"),
                    {"s_id": s_id}
                ).first()
                if sub_row or pct >= 100:
                    student_progress["status"] = "completed"
                    student_progress["completedPercentage"] = 100
                else:
                    student_progress["status"] = "in_progress"
        else:
            # Fallback to learning logs if no classroom_training exists (rare)
            progress_row = db.execute(
                text("""
                    SELECT is_training_started, end_time, start_time
                    FROM training_learning_logs
                    WHERE training_id = :training_id AND user_id = :user_id
                    ORDER BY start_time DESC
                    LIMIT 1
                """),
                {"training_id": training_id, "user_id": user_id}
            ).first()

            if progress_row:
                is_started, end_time, start_time = progress_row
                if end_time:
                    student_progress["status"] = "completed"
                    student_progress["completedPercentage"] = 100
                elif is_started:
                    student_progress["status"] = "in_progress"
                    student_progress["completedPercentage"] = 50

                student_progress["last_activity"] = str(start_time) if start_time else None

    return {
        "id": training.id,
        "training_id": training.training_id,
        "title": training.title,
        "training_type": training.training_type.value if hasattr(training.training_type, 'value') else str(training.training_type),
        "difficulty": difficulty_value,
        "industry": training.industry,
        "intro": training.intro,
        "handbook_content": handbook_content,
        "course_hours": training.course_hours or 0,
        "require_design_files": training.require_design_files or False,
        "require_experiment_report": training.require_experiment_report or False,
        "created_at": None,  # created_at 暂时设为 None
        "tasks": [],
        "progress": student_progress,
        "classroom": classroom_info,
        "stats": stats
    } 
