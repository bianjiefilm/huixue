# app/crud/crud_teaching_resources.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone

from app.models import models
from app.schemas import schemas
from .crud import check_classroom_teacher_permission  # 从 crud.py 导入权限检查函数

def get_teaching_resources_by_classroom(db: Session, classroom_id: int) -> List[models.ResourceModule]:
    """获取指定课堂的所有教学资源模块，并预加载文件和上传者信息。"""
    return db.query(models.ResourceModule).options(
        joinedload(models.ResourceModule.files).options(
            joinedload(models.ResourceFile.uploader)
        )
    ).filter(
        models.ResourceModule.classroom_id == classroom_id,
        models.ResourceModule.is_active == True
    ).order_by(models.ResourceModule.order_index).all()

def create_teaching_resource_module(db: Session, classroom_id: int, teacher_id: int, module_data: schemas.TeachingResourceModuleCreateRequest) -> Optional[models.ResourceModule]:
    """在课堂内创建新的教学资源模块。"""
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return None

    max_order = db.query(func.max(models.ResourceModule.order_index)).filter(
        models.ResourceModule.classroom_id == classroom_id
    ).scalar() or 0
    
    db_module = models.ResourceModule(
        classroom_id=classroom_id,
        name=module_data.name,
        description=module_data.description,
        order_index=max_order + 1,
        created_by=teacher_id,
        is_active=True
    )
    db.add(db_module)
    db.commit()
    db.refresh(db_module)
    return db_module

def create_teaching_resource_file(db: Session, module_id: int, teacher_id: int, file_data: schemas.TeachingResourceFileCreateRequest) -> Optional[models.ResourceFile]:
    """将文件元数据添加到指定模块下。"""
    module = db.query(models.ResourceModule).filter(models.ResourceModule.id == module_id).first()
    if not module or not check_classroom_teacher_permission(db, module.classroom_id, teacher_id):
        return None
        
    db_file = models.ResourceFile(
        module_id=module_id,
        name=file_data.name,
        url=file_data.url,
        file_type=file_data.file_type,
        file_size=file_data.file_size,
        duration_seconds=file_data.duration_seconds,
        uploader_id=teacher_id,
        is_active=True
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def record_learning_duration(db: Session, file_id: int, student_id: int, record_data: schemas.LearningRecordCreateRequest) -> Optional[models.StudentResourceLearning]:
    """记录或更新学生的学习时长。"""
    learning_record = db.query(models.StudentResourceLearning).filter(
        models.StudentResourceLearning.resource_file_id == file_id,
        models.StudentResourceLearning.student_id == student_id
    ).first()
    
    if learning_record:
        # 更新记录
        learning_record.learning_duration_seconds += record_data.learning_duration_seconds
        learning_record.last_position = record_data.last_position
        learning_record.is_completed = record_data.is_completed
        learning_record.last_access_at = datetime.now(timezone.utc)
    else:
        # 创建新记录
        learning_record = models.StudentResourceLearning(
            resource_file_id=file_id,
            student_id=student_id,
            learning_duration_seconds=record_data.learning_duration_seconds,
            last_position=record_data.last_position,
            is_completed=record_data.is_completed,
            last_access_at=datetime.now(timezone.utc)
        )
        db.add(learning_record)
        
    db.commit()
    db.refresh(learning_record)
    return learning_record

def check_classroom_student_permission(db: Session, classroom_id: int, student_id: int) -> bool:
    """检查学生是否有权限访问该课堂的资源"""
    enrollment = db.query(models.ClassroomStudent).filter(
        models.ClassroomStudent.classroom_id == classroom_id,
        models.ClassroomStudent.student_id == student_id,
        models.ClassroomStudent.status == "active"
    ).first()
    return enrollment is not None