#!/usr/bin/env python3
"""
对象存储API端点
提供文件上传、下载、管理等服务
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.models import User
from app.schemas.schemas import ApiResponse
from app.utils.object_storage import object_storage

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["对象存储"]
)

@router.get("/{file_path:path}")
async def get_file(file_path: str):
    """
    获取存储文件
    
    Args:
        file_path: 文件相对路径
    """
    try:
        file_content = object_storage.get_file(file_path)
        
        if file_content is None:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 根据文件扩展名设置Content-Type
        content_type = get_content_type(file_path)
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={"Content-Disposition": f"inline; filename={file_path.split('/')[-1]}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件失败: {file_path}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail="文件获取失败")

@router.post("/upload", response_model=ApiResponse)
async def upload_file(
    file: UploadFile = File(...),
    category: str = Query("assets", description="文件分类"),
    training_id: Optional[int] = Query(None, description="关联的实训ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 强制身份验证
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    """
    上传文件到对象存储
    
    Args:
        file: 上传的文件
        category: 文件分类（templates, datasets, notebooks, assets）
        training_id: 关联的实训ID（可选）
    """
    try:
        # 验证文件大小（最大50MB）
        max_size = 50 * 1024 * 1024  # 50MB
        file_content = await file.read()
        
        if len(file_content) > max_size:
            raise HTTPException(status_code=400, detail="文件大小超过50MB限制")
        
        # 验证文件分类
        valid_categories = ["templates", "datasets", "notebooks", "assets"]
        if category not in valid_categories:
            raise HTTPException(status_code=400, detail=f"无效的文件分类，支持的分类: {valid_categories}")
        
        # 保存文件
        file_info = object_storage.save_file(
            file_content=file_content,
            filename=file.filename,
            category=category,
            training_id=training_id
        )
        
        return ApiResponse(
            code="0000",
            message="文件上传成功",
            data=file_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {file.filename}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.get("/trainings/{training_id}/files", response_model=ApiResponse)
async def list_training_files(
    training_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出指定实训的所有文件"""
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        files_info = object_storage.list_training_files(training_id)
        
        return ApiResponse(
            code="0000",
            message="获取实训文件列表成功",
            data=files_info
        )
        
    except Exception as e:
        logger.error(f"获取实训文件列表失败: training_id={training_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail="获取文件列表失败")

@router.delete("/{file_path:path}", response_model=ApiResponse)
async def delete_file(
    file_path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_role("admin", "teacher")),
):
    """
    删除存储文件
    
    Args:
        file_path: 文件相对路径
    """
    try:
        success = object_storage.delete_file(file_path)
        
        if success:
            return ApiResponse(
                code="0000",
                message="文件删除成功"
            )
        else:
            raise HTTPException(status_code=500, detail="文件删除失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {file_path}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail="文件删除失败")

@router.get("/stats", response_model=ApiResponse)
async def get_storage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取存储统计信息"""
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        stats = object_storage.get_storage_stats()
        
        return ApiResponse(
            code="0000",
            message="获取存储统计成功",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"获取存储统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取存储统计失败")

def get_content_type(file_path: str) -> str:
    """根据文件扩展名获取Content-Type"""
    extension = file_path.lower().split('.')[-1]
    
    content_types = {
        # 文档类型
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        
        # 图片类型
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'svg': 'image/svg+xml',
        
        # 文本类型
        'txt': 'text/plain',
        'html': 'text/html',
        'css': 'text/css',
        'js': 'application/javascript',
        'json': 'application/json',
        'xml': 'application/xml',
        'csv': 'text/csv',
        
        # 代码类型
        'py': 'text/x-python',
        'sql': 'text/x-sql',
        'ipynb': 'application/x-ipynb+json',
        
        # 模板类型
        'tpo': 'application/octet-stream',  # BI模板
        'tapp': 'application/octet-stream', # AI模板
        
        # 压缩类型
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed',
        '7z': 'application/x-7z-compressed',
        
        # 视频类型
        'mp4': 'video/mp4',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        
        # 音频类型
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'ogg': 'audio/ogg',
    }
    
    return content_types.get(extension, 'application/octet-stream') 