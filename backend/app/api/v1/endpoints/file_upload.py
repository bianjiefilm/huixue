"""
文件上传端点
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
from datetime import datetime
import uuid
from pathlib import Path

from app.core.dependencies import get_db, get_current_user
from app.models import models
from app.schemas import schemas
from app.core.config import settings
from app.utils.logger import logger
from app.utils.file_manager import file_manager

router = APIRouter()

# 基础资源目录 - 使用正确的真实数据路径
BASE_RESOURCE_DIR = settings.resource_base_path

# 验证目录存在（不要自动创建，应该使用真实数据）
if not BASE_RESOURCE_DIR.exists():
    logger.error(f"资源目录不存在: {BASE_RESOURCE_DIR}")
    raise Exception(f"资源目录不存在: {BASE_RESOURCE_DIR}")

# 文件类型映射
FILE_TYPE_MAPPING = {
    '.pdf': 'document',
    '.doc': 'document',
    '.docx': 'document',
    '.xls': 'spreadsheet',
    '.xlsx': 'spreadsheet',
    '.csv': 'spreadsheet',
    '.ppt': 'presentation',
    '.pptx': 'presentation',
    '.jpg': 'image',
    '.jpeg': 'image',
    '.png': 'image',
    '.gif': 'image',
    '.mp4': 'video',
    '.avi': 'video',
    '.mov': 'video',
    '.mp3': 'audio',
    '.wav': 'audio',
    '.zip': 'archive',
    '.rar': 'archive',
    '.7z': 'archive',
    '.txt': 'text',
    '.json': 'text',
    '.xml': 'text',
    '.html': 'text',
    '.py': 'code',
    '.js': 'code',
    '.java': 'code',
    '.cpp': 'code',
    '.c': 'code',
}

def get_file_type(filename: str) -> str:
    """根据文件扩展名获取文件类型"""
    ext = Path(filename).suffix.lower()
    return FILE_TYPE_MAPPING.get(ext, 'other')

@router.post("/upload/classroom-disk", response_model=schemas.ApiResponse)
async def upload_classroom_disk_file(
    file: UploadFile = File(...),
    classroom_id: int = Form(...),
    teacher_id: int = Form(...),
    file_name: str = Form(...),
    folder_path: str = Form(""),
    is_shared: bool = Form(False),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传文件到课堂云盘"""
    try:
        # 验证用户权限
        user_id = current_user.get('id', 1) if isinstance(current_user, dict) else current_user.id
        if user_id != teacher_id:
            raise HTTPException(status_code=403, detail="无权限上传文件")

        # 验证课堂存在性
        classroom = db.query(models.Classroom).filter(
            models.Classroom.id == classroom_id
        ).first()

        if not classroom:
            raise HTTPException(status_code=404, detail="课堂不存在")

        # 读取文件内容
        file_content = await file.read()

        # 生成唯一文件名（避免FileManager重复处理）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_uuid = str(uuid.uuid4())[:8]
        file_extension = Path(file.filename).suffix
        unique_filename = f"{timestamp}_{file_uuid}_{file_name}"
        if not unique_filename.endswith(file_extension):
            unique_filename += file_extension

        # 使用FileManager安全保存文件
        result = file_manager.save_file(
            operation="classroom_disk",
            entity_id=classroom_id,
            file_content=file_content,
            filename=unique_filename,
            user_id=user_id,
            sub_path=folder_path
        )

        # 保存文件记录到数据库 (使用 ClassroomCloudFile 与列表查询一致)
        db_file = models.ClassroomCloudFile(
            classroom_id=classroom_id,
            uploader_id=teacher_id,
            name=file_name,  # ClassroomCloudFile 使用 name 字段
            file_type=get_file_type(file.filename),
            file_size=result['file_size'],
            folder_path=folder_path,
            is_shared=is_shared,
            url=f"/api/v1/files/classroom-disk/{classroom_id}/{unique_filename}"
        )

        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        return schemas.ApiResponse(
            code="0000",
            message="文件上传成功",
            data={
                "id": db_file.id,
                "name": db_file.name,
                "file_size": db_file.file_size,
                "file_type": db_file.file_type,
                "url": db_file.url,
                "created_at": db_file.created_at.isoformat() if db_file.created_at else None
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        # FileManager抛出的业务异常（如配额不足）
        return schemas.ApiResponse(
            code="1001",  # 配额不足或其他业务错误
            message=str(e),
            trace_id=str(uuid.uuid4())
        )
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.post("/upload/training-dataset", response_model=schemas.ApiResponse)
async def upload_training_dataset(
    file: UploadFile = File(...),
    training_id: int = Form(...),
    description: Optional[str] = Form(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传实训数据集"""
    try:
        # 验证实训存在性和权限
        user_id = current_user.get('id', 1) if isinstance(current_user, dict) else current_user.id
        training = db.query(models.Training).filter(
            models.Training.id == training_id,
            models.Training.creator_id == user_id
        ).first()
        
        if not training:
            raise HTTPException(status_code=404, detail="实训不存在或无权限")
        
        # 读取文件内容
        file_content = await file.read()

        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(file.filename).suffix
        unique_filename = f"{timestamp}_{file.filename}"

        # 使用FileManager安全保存文件
        result = file_manager.save_file(
            operation="training_dataset",
            entity_id=training_id,
            file_content=file_content,
            filename=unique_filename,
            user_id=user_id
        )
        
        # 保存数据集记录到数据库
        dataset = models.TrainingDataset(
            training_id=training_id,
            name=file.filename,  # 保存原始文件名
            file_url=f"/api/v1/files/training-dataset/{training_id}/{unique_filename}",
            file_type=file_extension[1:] if file_extension else "",
            file_size=result['file_size'],
            description=description,
            access_path=f"/{unique_filename}",  # 相对于实训项目目录
            uploader_id=user_id
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        return schemas.ApiResponse(
            code="0000",
            message="数据集上传成功",
            data={
                "id": dataset.id,
                "name": dataset.name,
                "file_url": dataset.file_url,
                "file_type": dataset.file_type,
                "file_size": dataset.file_size,
                "description": dataset.description,
                "created_at": dataset.created_at.isoformat() if dataset.created_at else None
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        # FileManager抛出的业务异常（如配额不足）
        return schemas.ApiResponse(
            code="1001",  # 配额不足或其他业务错误
            message=str(e),
            trace_id=str(uuid.uuid4())
        )
    except Exception as e:
        logger.error(f"数据集上传失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据集上传失败: {str(e)}")

@router.post("/upload/homework-submission", response_model=schemas.ApiResponse)
async def upload_homework_submission(
    file: Optional[UploadFile] = File(None),
    homework_id: int = Form(...),
    student_id: int = Form(...),
    submission_type: str = Form(...),  # design_file, report, other
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传作业提交文件（file 字段可选，支持纯文本报告）"""
    try:
        # 验证用户权限
        user_id = current_user.get('id', 1) if isinstance(current_user, dict) else current_user.id
        if user_id != student_id:
            raise HTTPException(status_code=403, detail="无权限上传文件")

        # 创建作业提交目录
        submission_dir = BASE_RESOURCE_DIR / "作业提交" / f"homework_{homework_id}" / f"student_{student_id}"
        submission_dir.mkdir(parents=True, exist_ok=True)

        # 无文件时返回确认响应（不写 DB — 实际记录由前端通过 /submissions 端点处理）
        if file is None:
            logger.info(f"[homework-submission] 收到无附件提交: homework_id={homework_id}, student_id={student_id}, submission_type={submission_type}")
            return schemas.ApiResponse(
                code="0000",
                message="作业提交已收到（无附件）",
                data={
                    "file_name": None,
                    "file_path": None,
                    "file_size": 0,
                    "file_type": None,
                    "url": None,
                    "submission_type": submission_type,
                    "created_at": datetime.now().isoformat()
                }
            )

        # 有文件时保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(file.filename).suffix
        unique_filename = f"{submission_type}_{timestamp}_{file.filename}"

        file_path = submission_dir / unique_filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = file_path.stat().st_size

        return schemas.ApiResponse(
            code="0000",
            message="文件上传成功",
            data={
                "file_name": file.filename,
                "file_path": str(file_path.relative_to(BASE_RESOURCE_DIR)),
                "file_size": file_size,
                "file_type": get_file_type(file.filename),
                "url": f"/api/v1/files/homework/{homework_id}/{student_id}/{unique_filename}",
                "submission_type": submission_type,
                "created_at": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"作业文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"作业文件上传失败: {str(e)}")

@router.post("/upload/teaching-resource", response_model=schemas.ApiResponse)
async def upload_teaching_resource_file(
    file: UploadFile = File(...),
    module_id: int = Form(...),
    teacher_id: int = Form(...),
    file_name: str = Form(...),
    file_type: str = Form(...),
    description: Optional[str] = Form(None),
    duration: Optional[int] = Form(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传教学资源文件"""
    try:
        # 验证用户权限
        user_id = current_user.get('id', 1) if isinstance(current_user, dict) else current_user.id
        if user_id != teacher_id:
            raise HTTPException(status_code=403, detail="无权限上传文件")
        
        # 验证模块存在性
        module = db.query(models.TeachingResourceModule).filter(
            models.TeachingResourceModule.id == module_id
        ).first()
        
        if not module:
            raise HTTPException(status_code=404, detail="教学资源模块不存在")
        
        # 创建教学资源目录
        teaching_resource_dir = BASE_RESOURCE_DIR / "教学资源" / f"module_{module_id}"
        teaching_resource_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_uuid = str(uuid.uuid4())[:8]
        file_extension = Path(file.filename).suffix
        unique_filename = f"{timestamp}_{file_uuid}_{file_name}"
        if not unique_filename.endswith(file_extension):
            unique_filename += file_extension
        
        # 保存文件
        file_path = teaching_resource_dir / unique_filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 获取文件大小
        file_size = file_path.stat().st_size
        
        # 保存教学资源文件记录到数据库
        db_file = models.TeachingResourceFile(
            module_id=module_id,
            name=file_name,
            url=f"/api/v1/files/teaching-resources/教学资源/{unique_filename}",
            file_type=file_type,
            file_size=file_size,
            file_path=str(file_path.relative_to(BASE_RESOURCE_DIR)),
            description=description,
            duration=duration,
            is_preview_only=True
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return schemas.ApiResponse(
            code="0000",
            message="教学资源文件上传成功",
            data={
                "id": db_file.id,
                "name": db_file.name,
                "url": db_file.url,
                "file_type": db_file.file_type,
                "file_size": db_file.file_size,
                "description": db_file.description,
                "duration": db_file.duration,
                "is_preview_only": db_file.is_preview_only,
                "created_at": db_file.created_at.isoformat() if db_file.created_at else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"教学资源文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"教学资源文件上传失败: {str(e)}")