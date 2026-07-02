"""
资源管理端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
import uuid
import logging
from datetime import datetime, timezone, timedelta

# 修正的导入路径
from app.core.database import get_db, engine, Base
from app.models import models as db_models  # 避免与FastAPI的models冲突
from app.crud import crud
from app.schemas import schemas
from app.core.security import get_current_user
from app.core.identity import resolve_scoped_id, require_authenticated


def check_classroom_student_permission(db: Session, classroom_id: int, student_id: int) -> bool:
    """检查学生是否有权限访问该课堂的资源"""
    enrollment = db.query(db_models.ClassroomStudent).filter(
        db_models.ClassroomStudent.classroom_id == classroom_id,
        db_models.ClassroomStudent.student_id == student_id
    ).first()
    return enrollment is not None

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    tags=['resources']
)

@router.get("/courses/{course_id}/resources", response_model=schemas.ApiResponse)
def get_course_resources(course_id: int, db: Session = Depends(get_db)):
    """获取课程教学资源"""
    try:
        resources = crud.get_course_resources(db, course_id=course_id)
        resource_list = [schemas.CourseResourceResponse.model_validate(resource) for resource in resources]
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=[resource.model_dump() for resource in resource_list]
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/classrooms/{classroom_id}/resources", response_model=schemas.ApiResponse)
def get_classroom_resources(
    classroom_id: int,
    resource_type: Optional[str] = Query(None, description="资源类型筛选：video, ppt, pdf, document"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取课堂教学资源列表（已弃用，请使用 /classrooms/{classroom_id}/resource-modules）"""
    # BUG-006 fix: ClassroomResource 模型已弃用，返回空列表并提示使用新端点
    return schemas.ApiResponse(
        code="0000",
        message="此端点已弃用，请使用 /api/v1/classrooms/{classroom_id}/resource-modules",
        data={
            "list": [],
            "meta": {
                "total": 0,
                "page": page,
                "page_size": page_size
            }
        }
    )


@router.post("/classrooms/{classroom_id}/resources", response_model=schemas.ApiResponse)
def upload_classroom_resource(
    classroom_id: int,
    title: str = Query(..., description="资源标题"),
    resource_type: str = Query(..., description="资源类型：video, ppt, pdf, document"),
    url: str = Query(..., description="资源URL"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """上传教学资源"""
    try:
        resource = crud.create_classroom_resource(
            db, classroom_id, title, url, resource_type, teacher_id
        )
        
        if resource is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        resource_data = {
            "id": resource.id,
            "title": resource.title,
            "url": resource.url,
            "resource_type": resource.resource_type,
            "upload_time": resource.created_at
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="资源上传成功",
            data=resource_data
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.delete("/classrooms/{classroom_id}/resources/{resource_id}", response_model=schemas.ApiResponse)
def delete_classroom_resource(
    classroom_id: int,
    resource_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """删除教学资源"""
    try:
        success = crud.delete_classroom_resource(db, classroom_id, resource_id, teacher_id)
        
        if not success:
            return schemas.ApiResponse(
                code="1002",
                message="资源不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="资源删除成功",
            data={"message": "教学资源已删除"}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 课堂云盘API ====================


@router.get("/classrooms/{classroom_id}/cloud-disk", response_model=schemas.ApiResponse)
def get_cloud_disk_files(
    classroom_id: int,
    folder_path: str = Query("", description="文件夹路径"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    file_type: Optional[str] = Query(None, description="文件类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    user_role: str = Query("teacher", description="[已忽略，真实角色来自 token]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课堂云盘文件列表"""
    try:
        # 【IDOR 修复】角色与身份一律以 JWT 为准，忽略客户端传入的 teacher_id/user_role
        real_user_id, real_role = require_authenticated(current_user)
        if user_role != real_role:
            logger.warning(
                f"[IDOR] 攻击探测：客户端伪造 user_role={user_role}，真实角色={real_role}，"
                f"classroom_id={classroom_id}，real_user_id={real_user_id}"
            )
        teacher_id = real_user_id
        is_teacher = real_role == "teacher"
        if is_teacher:
            if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
                return schemas.ApiResponse(
                    code="1001",
                    message="课堂不存在或无权限",
                    trace_id=str(uuid.uuid4())
                )
        else:
            # 学生权限检查
            if not check_classroom_student_permission(db, classroom_id, teacher_id):
                return schemas.ApiResponse(
                    code="1001",
                    message="您不是该课堂的学生",
                    trace_id=str(uuid.uuid4())
                )
        
        skip = (page - 1) * page_size
        files, total = crud.get_classroom_cloud_files(
            db, classroom_id, folder_path, keyword, file_type, skip, page_size
        )

        # 构建响应数据，学生只能看到共享文件
        file_list = []
        for file in files:
            # 学生只能看到is_shared=True的文件
            file_is_shared = getattr(file, 'is_shared', True)
            if not is_teacher and not file_is_shared:
                continue

            file_data = {
                "id": file.id,
                "name": file.name,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "folder_path": file.folder_path,
                "url": file.url,
                "upload_time": file.created_at,
                "uploader_name": getattr(file, 'uploader_name', '教师'),
                "download_count": getattr(file, 'download_count', 0),
                "is_shared": file_is_shared
            }
            file_list.append(file_data)

        # 学生视角需要重新计算总数
        if not is_teacher:
            total = len(file_list)
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": file_list,
                "meta": meta,
                "current_path": folder_path
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/classrooms/{classroom_id}/cloud-disk/upload", response_model=schemas.ApiResponse)
def upload_cloud_disk_file(
    classroom_id: int,
    file_name: str = Query(..., description="文件名"),
    file_type: str = Query(..., description="文件类型"),
    file_size: int = Query(..., description="文件大小（字节）"),
    folder_path: str = Query("", description="上传到的文件夹路径"),
    url: str = Query(..., description="文件URL"),
    is_shared: bool = Query(True, description="是否共享给学生"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """上传文件到课堂云盘"""
    try:
        file = crud.upload_classroom_cloud_file(
            db, classroom_id, file_name, file_type, file_size, 
            folder_path, url, is_shared, teacher_id
        )
        
        if file is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        file_data = {
            "id": file.id,
            "name": file.name,
            "file_type": file.file_type,
            "file_size": file.file_size,
            "folder_path": file.folder_path,
            "url": file.url,
            "upload_time": file.created_at,
            "is_shared": file.is_shared
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="文件上传成功",
            data=file_data
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 课堂云盘增强功能 ====================

@router.get("/classrooms/{classroom_id}/cloud-disk/{file_id}/preview", response_model=schemas.ApiResponse)
def preview_cloud_disk_file(
    classroom_id: int,
    file_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """预览云盘文件"""
    try:
        preview_info = crud.get_cloud_file_preview_info(db, classroom_id, file_id, teacher_id)
        
        if not preview_info:
            return schemas.ApiResponse(
                code="1002",
                message="文件不存在或无权限访问",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=preview_info
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.post("/classrooms/{classroom_id}/cloud-disk/{file_id}/download", response_model=schemas.ApiResponse)
def download_cloud_disk_file(
    classroom_id: int,
    file_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """下载云盘文件（更新下载次数）"""
    try:
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        # 更新下载次数
        file = crud.update_cloud_file_download_count(db, file_id)
        
        if not file:
            return schemas.ApiResponse(
                code="1002",
                message="文件不存在",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="下载成功",
            data={
                "file_id": file.id,
                "file_name": file.name,
                "download_url": file.url,
                "download_count": file.download_count
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.post("/classrooms/{classroom_id}/cloud-disk/batch", response_model=schemas.ApiResponse)
def batch_cloud_disk_operation(
    classroom_id: int,
    request: schemas.CloudFilesBatchRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """批量操作云盘文件（删除或下载）"""
    try:
        if request.action == "delete":
            # 批量删除
            deleted_count = crud.batch_delete_cloud_files(
                db, classroom_id, request.file_ids, teacher_id
            )
            
            if deleted_count == 0:
                return schemas.ApiResponse(
                    code="1002",
                    message="没有文件被删除，请检查文件是否存在或权限",
                    trace_id=str(uuid.uuid4())
                )
            
            return schemas.ApiResponse(
                code="0000",
                message=f"成功删除 {deleted_count} 个文件",
                data={"deleted_count": deleted_count}
            )
        
        elif request.action == "download":
            # 批量下载（返回文件列表，前端处理压缩下载）
            files = db.query(db_models.ClassroomCloudFile).filter(
                db_models.ClassroomCloudFile.classroom_id == classroom_id,
                db_models.ClassroomCloudFile.id.in_(request.file_ids)
            ).all()
            
            if not files:
                return schemas.ApiResponse(
                    code="1002",
                    message="没有找到要下载的文件",
                    trace_id=str(uuid.uuid4())
                )
            
            # 更新下载次数
            for file in files:
                crud.update_cloud_file_download_count(db, file.id)
            
            file_list = [
                {
                    "id": file.id,
                    "name": file.name,
                    "url": file.url,
                    "file_size": file.file_size
                }
                for file in files
            ]
            
            return schemas.ApiResponse(
                code="0000",
                message="批量下载文件列表获取成功",
                data={
                    "files": file_list,
                    "total_files": len(file_list)
                }
            )
        
        else:
            return schemas.ApiResponse(
                code="1003",
                message="不支持的操作类型",
                trace_id=str(uuid.uuid4())
            )
    
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.delete("/classrooms/{classroom_id}/cloud-disk/{file_id}", response_model=schemas.ApiResponse)
def delete_cloud_disk_file(
    classroom_id: int,
    file_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """删除单个云盘文件"""
    try:
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        # 删除文件
        file = db.query(db_models.ClassroomCloudFile).filter(
            db_models.ClassroomCloudFile.id == file_id,
            db_models.ClassroomCloudFile.classroom_id == classroom_id
        ).first()
        
        if not file:
            return schemas.ApiResponse(
                code="1002",
                message="文件不存在",
                trace_id=str(uuid.uuid4())
            )
        
        db.delete(file)
        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message="文件删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 教学资源模块API ====================

@router.get("/classrooms/{classroom_id}/resource-modules", response_model=schemas.ApiResponse)
def get_classroom_resource_modules(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取课堂教学资源模块列表"""
    try:
        modules = crud.get_classroom_resource_modules(db, classroom_id, teacher_id)

        module_list = []
        for module in modules:
            # 获取模块内的文件列表
            files = db.query(db_models.ResourceFile).filter(
                db_models.ResourceFile.module_id == module.id,
                db_models.ResourceFile.is_active == True
            ).all()

            file_list = []
            for file in files:
                uploader = db.query(db_models.User).filter(
                    db_models.User.id == file.uploader_id
                ).first()

                file_data = {
                    "id": file.id,
                    "name": file.name,
                    "url": file.url,
                    "file_type": file.file_type.lower() if file.file_type else 'unknown',
                    "file_size": file.file_size,
                    "duration_seconds": file.duration_seconds,
                    "view_count": file.view_count,
                    "download_count": file.download_count,
                    "created_at": file.created_at.isoformat() if file.created_at else None,
                    "uploader_name": uploader.full_name if uploader else "教师"
                }
                file_list.append(file_data)

            module_data = {
                "id": module.id,
                "name": module.name,
                "description": module.description,
                "order_index": module.order_index,
                "file_count": getattr(module, 'file_count', len(file_list)),
                "files": file_list,
                "created_at": module.created_at,
                "updated_at": module.updated_at
            }
            module_list.append(module_data)

        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={"modules": module_list}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.post("/classrooms/{classroom_id}/resource-modules", response_model=schemas.ApiResponse)
def create_resource_module(
    classroom_id: int,
    name: str = Query(..., description="模块名称"),
    description: Optional[str] = Query(None, description="模块描述"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """创建教学资源模块"""
    try:
        module = crud.create_resource_module(
            db, classroom_id, name, teacher_id, description
        )
        
        if module is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        module_data = {
            "id": module.id,
            "name": module.name,
            "description": module.description,
            "order_index": module.order_index,
            "created_at": module.created_at
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="模块创建成功",
            data=module_data
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.put("/resource-modules/{module_id}", response_model=schemas.ApiResponse)
def update_resource_module(
    module_id: int,
    name: Optional[str] = Query(None, description="模块名称"),
    description: Optional[str] = Query(None, description="模块描述"),
    order_index: Optional[int] = Query(None, description="排序索引"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """更新教学资源模块"""
    try:
        module = crud.update_resource_module(
            db, module_id, teacher_id, name, description, order_index
        )
        
        if module is None:
            return schemas.ApiResponse(
                code="1002",
                message="模块不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        module_data = {
            "id": module.id,
            "name": module.name,
            "description": module.description,
            "order_index": module.order_index,
            "updated_at": module.updated_at
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="模块更新成功",
            data=module_data
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.delete("/resource-modules/{module_id}", response_model=schemas.ApiResponse)
def delete_resource_module(
    module_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """删除教学资源模块"""
    try:
        success = crud.delete_resource_module(db, module_id, teacher_id)
        
        if not success:
            return schemas.ApiResponse(
                code="1002",
                message="模块不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="模块删除成功",
            data={"message": "教学资源模块已删除"}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/resource-modules/{module_id}/files", response_model=schemas.ApiResponse)
def get_module_files(
    module_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取模块内的文件列表"""
    try:
        files = crud.get_module_files(db, module_id, teacher_id)
        
        file_list = []
        for file in files:
            file_data = {
                "id": file.id,
                "name": file.name,
                "url": file.url,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "duration_seconds": file.duration_seconds,
                "view_count": file.view_count,
                "download_count": file.download_count,
                "created_at": file.created_at,
                "uploader_name": getattr(file, 'uploader_name', '教师')
            }
            file_list.append(file_data)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={"files": file_list}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.post("/resource-modules/{module_id}/files", response_model=schemas.ApiResponse)
def upload_resource_file(
    module_id: int,
    name: str = Query(..., description="文件名"),
    url: str = Query(..., description="文件URL"),
    file_type: str = Query(..., description="文件类型：pdf, doc, docx, ppt, pptx, mp4"),
    file_size: int = Query(..., description="文件大小（字节）"),
    duration_seconds: Optional[int] = Query(None, description="视频时长（秒）"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """上传文件到教学资源模块"""
    try:
        # 验证文件大小（2GB限制）
        max_file_size = 2 * 1024 * 1024 * 1024  # 2GB
        if file_size > max_file_size:
            return schemas.ApiResponse(
                code="1003",
                message="文件大小超过2GB限制",
                trace_id=str(uuid.uuid4())
            )
        
        resource_file = crud.upload_resource_file(
            db, module_id, name, url, file_type, file_size, teacher_id, duration_seconds
        )
        
        if resource_file is None:
            return schemas.ApiResponse(
                code="1001",
                message="模块不存在、无权限或文件类型不支持",
                trace_id=str(uuid.uuid4())
            )
        
        file_data = {
            "id": resource_file.id,
            "name": resource_file.name,
            "url": resource_file.url,
            "file_type": resource_file.file_type,
            "file_size": resource_file.file_size,
            "duration_seconds": resource_file.duration_seconds,
            "created_at": resource_file.created_at
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="文件上传成功",
            data=file_data
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.delete("/resource-files/{file_id}", response_model=schemas.ApiResponse)
def delete_resource_file(
    file_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """删除教学资源文件"""
    try:
        success = crud.delete_resource_file(db, file_id, teacher_id)
        
        if not success:
            return schemas.ApiResponse(
                code="1002",
                message="文件不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="文件删除成功",
            data={"message": "教学资源文件已删除"}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.post("/resource-files/{file_id}/view", response_model=schemas.ApiResponse)
def update_file_view_count(
    file_id: int,
    db: Session = Depends(get_db)
):
    """更新文件查看次数（用于预览时调用）"""
    try:
        success = crud.update_file_view_count(db, file_id)
        
        if not success:
            return schemas.ApiResponse(
                code="1002",
                message="文件不存在",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="查看次数更新成功",
            data={"message": "文件查看次数已更新"}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.post("/resource-files/{file_id}/learning-record", response_model=schemas.ApiResponse)
def record_student_learning(
    file_id: int,
    learning_duration_seconds: int = Query(..., description="学习时长（秒）"),
    last_position: int = Query(0, description="最后学习位置"),
    is_completed: bool = Query(False, description="是否完成学习"),
    student_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """记录学生学习时长"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))
        learning_record = crud.record_student_learning(
            db, student_id, file_id, learning_duration_seconds, last_position, is_completed
        )
        
        record_data = {
            "id": learning_record.id,
            "learning_duration_seconds": learning_record.learning_duration_seconds,
            "last_position": learning_record.last_position,
            "is_completed": learning_record.is_completed,
            "last_access_at": learning_record.last_access_at
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="学习记录更新成功",
            data=record_data
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/classrooms/{classroom_id}/student-learning-records", response_model=schemas.ApiResponse)
def get_student_learning_records(
    classroom_id: int,
    student_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生在某个课堂的学习记录"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))
        records = crud.get_student_learning_records(db, student_id, classroom_id)
        
        record_list = []
        for record in records:
            record_data = {
                "id": record.id,
                "resource_file_id": record.resource_file_id,
                "learning_duration_seconds": record.learning_duration_seconds,
                "last_position": record.last_position,
                "is_completed": record.is_completed,
                "first_access_at": record.first_access_at,
                "last_access_at": record.last_access_at
            }
            record_list.append(record_data)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={"records": record_list}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 教学资源模块API (按照计划规范) ====================

@router.get("/teaching-resources/classrooms/{classroom_id}/modules", response_model=schemas.ApiResponse)
def get_teaching_resource_modules(
    classroom_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    student_id: Optional[int] = Query(None, description="学生ID"),
    db: Session = Depends(get_db)
):
    """
    API 1: 获取课堂的教学资源模块列表
    功能描述: 获取指定课堂下的所有教学资源模块及其文件列表
    """
    try:
        # 检查课堂是否存在
        classroom = db.query(db_models.Classroom).filter(
            db_models.Classroom.id == classroom_id
        ).first()
        
        if not classroom:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 权限验证 - 简化版本，如果是课堂的创建教师则有权限
        if teacher_id:
            if classroom.teacher_id != teacher_id:
                # 不是主教师，检查是否有其他权限
                # 暂时允许所有教师访问（开发环境）
                pass
        elif student_id:
            # 检查学生是否在此课堂中
            student_in_classroom = db.query(db_models.ClassroomStudent).filter(
                db_models.ClassroomStudent.classroom_id == classroom_id,
                db_models.ClassroomStudent.student_id == student_id
            ).first()
            if not student_in_classroom:
                return schemas.ApiResponse(
                    code="1001",
                    message="课堂不存在或无权限",
                    trace_id=str(uuid.uuid4())
                )
        else:
            return schemas.ApiResponse(
                code="1003",
                message="必须提供teacher_id或student_id",
                trace_id=str(uuid.uuid4())
            )
        
        # 获取模块和文件
        modules = db.query(db_models.ResourceModule).filter(
            db_models.ResourceModule.classroom_id == classroom_id,
            db_models.ResourceModule.is_active == True
        ).order_by(db_models.ResourceModule.order_index).all()
        
        module_list = []
        for module in modules:
            # 获取模块内文件
            files = db.query(db_models.ResourceFile).filter(
                db_models.ResourceFile.module_id == module.id,
                db_models.ResourceFile.is_active == True
            ).all()
            
            file_list = []
            for file in files:
                uploader = db.query(db_models.User).filter(
                    db_models.User.id == file.uploader_id
                ).first()
                
                file_data = {
                    "id": file.id,
                    "name": file.name,
                    "url": file.url,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "duration_seconds": file.duration_seconds,
                    "uploader_name": uploader.full_name if uploader else "教师",
                    "created_at": file.created_at.isoformat() if file.created_at else None
                }
                file_list.append(file_data)
            
            module_data = {
                "id": module.id,
                "name": module.name,
                "description": module.description,
                "order_index": module.order_index,
                "files": file_list
            }
            module_list.append(module_data)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={"modules": module_list}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/teaching-resources/classrooms/{classroom_id}/modules", response_model=schemas.ApiResponse)
def create_teaching_resource_module(
    classroom_id: int,
    name: str = Query(..., description="模块名称", max_length=100),
    description: Optional[str] = Query(None, description="模块描述", max_length=500),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """
    API 2: 创建教学资源模块
    功能描述: 教师在课堂内创建一个新的教学资源模块
    """
    try:
        # 数据验证
        if len(name) > 100:
            return schemas.ApiResponse(
                code="1004",
                message="模块名称长度不能超过100个字符",
                trace_id=str(uuid.uuid4())
            )
        
        if description and len(description) > 500:
            return schemas.ApiResponse(
                code="1004",
                message="模块描述长度不能超过500个字符",
                trace_id=str(uuid.uuid4())
            )
        
        # 权限验证
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        # 获取下一个排序索引
        max_order = db.query(func.coalesce(func.max(db_models.ResourceModule.order_index), 0)).filter(
            db_models.ResourceModule.classroom_id == classroom_id
        ).scalar()
        
        # 创建模块
        module = db_models.ResourceModule(
            classroom_id=classroom_id,
            name=name,
            description=description,
            order_index=max_order + 1,
            created_by=teacher_id,
            is_active=True
        )
        
        db.add(module)
        db.commit()
        db.refresh(module)
        
        module_data = {
            "id": module.id,
            "name": module.name,
            "description": module.description,
            "order_index": module.order_index,
            "created_at": module.created_at.isoformat() if module.created_at else None
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="模块创建成功",
            data=module_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/teaching-resources/modules/{module_id}/files", response_model=schemas.ApiResponse)
def upload_teaching_resource_file(
    module_id: int,
    name: str = Query(..., description="文件名"),
    url: str = Query(..., description="文件URL"),
    file_type: str = Query(..., description="文件类型"),
    file_size: int = Query(..., description="文件大小（字节）"),
    duration_seconds: Optional[int] = Query(None, description="视频时长（秒）"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """
    API 3: 上传文件到教学资源模块
    功能描述: 教师上传文件后，将文件的元数据记录到指定模块下
    """
    try:
        # 验证模块存在且有权限
        module = db.query(db_models.ResourceModule).filter(
            db_models.ResourceModule.id == module_id,
            db_models.ResourceModule.is_active == True
        ).first()
        
        if not module:
            return schemas.ApiResponse(
                code="1002",
                message="模块不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 验证教师权限
        if not crud.check_classroom_teacher_permission(db, module.classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="无权限",
                trace_id=str(uuid.uuid4())
            )
        
        # 创建文件记录
        resource_file = db_models.ResourceFile(
            module_id=module_id,
            name=name,
            url=url,
            file_type=file_type,
            file_size=file_size,
            duration_seconds=duration_seconds,
            uploader_id=teacher_id,
            view_count=0,
            download_count=0,
            is_active=True
        )
        
        db.add(resource_file)
        db.commit()
        db.refresh(resource_file)
        
        file_data = {
            "id": resource_file.id,
            "name": resource_file.name,
            "url": resource_file.url,
            "file_type": resource_file.file_type,
            "file_size": resource_file.file_size,
            "duration_seconds": resource_file.duration_seconds,
            "created_at": resource_file.created_at.isoformat() if resource_file.created_at else None
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="文件上传成功",
            data=file_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/teaching-resources/files/{file_id}/learning-record", response_model=schemas.ApiResponse)
def record_teaching_resource_learning(
    file_id: int,
    learning_duration_seconds: int = Query(..., description="本次上报的学习时长（秒）", ge=0),
    last_position: int = Query(0, description="视频播放到的秒数或PDF阅读到的页码", ge=0),
    is_completed: bool = Query(False, description="是否已学完"),
    student_id: int = Query(..., description="学生ID"),
    db: Session = Depends(get_db)
):
    """
    API 4: 记录学生学习时长
    功能描述: 学生在线预览教学资源时，前端定时调用此接口上报学习时长
    """
    try:
        # 数据验证
        if learning_duration_seconds < 0:
            return schemas.ApiResponse(
                code="1005",
                message="学习时长不能为负数",
                trace_id=str(uuid.uuid4())
            )
        
        if last_position < 0:
            return schemas.ApiResponse(
                code="1005",
                message="学习位置不能为负数",
                trace_id=str(uuid.uuid4())
            )
        
        # 验证文件存在
        resource_file = db.query(db_models.ResourceFile).filter(
            db_models.ResourceFile.id == file_id,
            db_models.ResourceFile.is_active == True
        ).first()
        
        if not resource_file:
            return schemas.ApiResponse(
                code="1002",
                message="资源文件不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 查找或创建学习记录
        learning_record = db.query(db_models.StudentResourceLearning).filter(
            db_models.StudentResourceLearning.student_id == student_id,
            db_models.StudentResourceLearning.resource_file_id == file_id
        ).first()
        
        if learning_record:
            # 更新现有记录
            learning_record.learning_duration_seconds += learning_duration_seconds
            learning_record.last_position = last_position
            learning_record.is_completed = is_completed
            learning_record.last_access_at = datetime.now(timezone.utc)
        else:
            # 创建新记录
            learning_record = db_models.StudentResourceLearning(
                student_id=student_id,
                resource_file_id=file_id,
                learning_duration_seconds=learning_duration_seconds,
                last_position=last_position,
                is_completed=is_completed,
                first_access_at=datetime.now(timezone.utc),
                last_access_at=datetime.now(timezone.utc)
            )
            db.add(learning_record)
        
        db.commit()
        db.refresh(learning_record)
        
        record_data = {
            "id": learning_record.id,
            "learning_duration_seconds": learning_record.learning_duration_seconds,
            "last_position": learning_record.last_position,
            "is_completed": learning_record.is_completed,
            "last_access_at": learning_record.last_access_at.isoformat() if learning_record.last_access_at else None
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="学习记录更新成功",
            data=record_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


# ==================== 实训资源API ====================
# Note: /trainings/library endpoint has been moved to trainings.py to avoid route conflicts
# All training-related endpoints should be defined in trainings.py


@router.post("/classrooms/{classroom_id}/trainings", response_model=schemas.ApiResponse)
def add_training_to_classroom(
    classroom_id: int,
    training_id: int = Query(..., description="实训ID"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """
    API 3: 教师将实训添加到课堂
    功能描述: 教师将一个平台实训资源添加到自己的课堂中
    """
    try:
        # 验证教师权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        # 验证实训存在
        training = db.query(db_models.Training).filter(
            db_models.Training.id == training_id,
            db_models.Training.is_published == True
        ).first()
        
        if not training:
            return schemas.ApiResponse(
                code="1002",
                message="实训不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 检查是否已添加
        existing = db.query(db_models.ClassroomCourse).filter(
            db_models.ClassroomCourse.classroom_id == classroom_id,
            db_models.ClassroomCourse.course_id == training_id  # 使用course_id字段
        ).first()
        
        if existing:
            return schemas.ApiResponse(
                code="1003",
                message="实训已添加到课堂",
                trace_id=str(uuid.uuid4())
            )
        
        # 创建关联记录
        classroom_course = db_models.ClassroomCourse(
            classroom_id=classroom_id,
            course_id=training_id,
            order_in_classroom=0,
            teacher_publish_status=db_models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED,
            is_mandatory=True,
            allow_late_submission=True,
            total_score=100
        )
        
        db.add(classroom_course)
        db.commit()
        db.refresh(classroom_course)
        
        return schemas.ApiResponse(
            code="0000",
            message="实训添加成功",
            data={"id": classroom_course.id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


# ==================== 学生实训会话管理API ====================

@router.post("/sessions/trainings/{training_id}/start", response_model=schemas.ApiResponse)
def start_training_session(
    training_id: int,
    student_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    classroom_id: int = Query(..., description="课堂ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API 4: 学生启动实训环境
    功能描述: 这是最核心的交互API。学生点击"开启实训"时调用，后端负责准备好整个隔离的实践环境
    """
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))
        # 验证实训存在
        training = db.query(db_models.Training).filter(
            db_models.Training.id == training_id,
            db_models.Training.is_published == True
        ).first()
        
        if not training:
            return schemas.ApiResponse(
                code="1002",
                message="实训不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 验证学生在课堂中
        student_in_classroom = db.query(db_models.ClassroomStudent).filter(
            db_models.ClassroomStudent.classroom_id == classroom_id,
            db_models.ClassroomStudent.student_id == student_id
        ).first()
        
        if not student_in_classroom:
            return schemas.ApiResponse(
                code="1001",
                message="学生不在此课堂中",
                trace_id=str(uuid.uuid4())
            )
        
        # 检查是否已有活跃会话
        existing_session = db.query(db_models.PracticeEnvironmentSession).filter(
            db_models.PracticeEnvironmentSession.user_id == student_id,
            db_models.PracticeEnvironmentSession.task_id == training_id,  # 复用task_id字段存储training_id
            db_models.PracticeEnvironmentSession.status == "active"
        ).first()
        
        if existing_session:
            # 返回现有会话
            environment_type = "JUPYTER" if training.training_type.value == "CODING" else "BI_DESIGNER"
            access_url = f"https://training.example.com/{environment_type.lower()}?session={existing_session.session_id}"
            
            return schemas.ApiResponse(
                code="0000",
                message="实训环境已存在",
                data={
                    "session_id": existing_session.session_id,
                    "environment_type": environment_type,
                    "status": "running",
                    "access_url": access_url,
                    "expires_at": existing_session.expires_at.isoformat() if existing_session.expires_at else None
                }
            )
        
        # 创建新的实训会话
        session_id = f"session_student{student_id}_training{training_id}_{int(datetime.now().timestamp())}"
        environment_type = "JUPYTER" if training.training_type.value == "CODING" else "BI_DESIGNER"
        
        # 设置过期时间（8小时后）
        expires_at = datetime.now(timezone.utc) + timedelta(hours=8)
        
        # 创建会话记录
        session = db_models.PracticeEnvironmentSession(
            task_id=training_id,  # 复用task_id存储training_id
            user_id=student_id,
            env_type=environment_type.lower(),
            session_id=session_id,
            container_id=f"container_{session_id}",
            status="active",
            expires_at=expires_at
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # 准备实训环境（这里应该调用实际的容器服务，这里模拟）
        access_url = f"https://training.example.com/{environment_type.lower()}?session={session_id}"
        
        # 记录实训学习开始
        training_log = db_models.TrainingLearningLog(
            user_id=student_id,
            training_id=training_id,
            start_time=datetime.now(timezone.utc),
            is_training_started=True
        )
        db.add(training_log)
        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message="实训环境启动成功，正在准备...",
            data={
                "session_id": session_id,
                "environment_type": environment_type,
                "status": "PREPARING",
                "access_url": access_url,
                "expires_at": expires_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/sessions/{session_id}/datasets", response_model=schemas.ApiResponse)
def get_training_session_datasets(
    session_id: str,
    student_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API 5: 获取实训环境中的数据集路径
    功能描述: 在Jupyter环境中，学生需要知道数据集被挂载到了哪个路径
    """
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))
        # 验证会话存在
        session = db.query(db_models.PracticeEnvironmentSession).filter(
            db_models.PracticeEnvironmentSession.session_id == session_id,
            db_models.PracticeEnvironmentSession.user_id == student_id,
            db_models.PracticeEnvironmentSession.status == "active"
        ).first()
        
        if not session:
            return schemas.ApiResponse(
                code="1002",
                message="会话不存在或已过期",
                trace_id=str(uuid.uuid4())
            )
        
        # 获取实训数据集
        training_id = session.task_id  # task_id存储的是training_id
        datasets = db.query(db_models.TrainingDataset).filter(
            db_models.TrainingDataset.training_id == training_id
        ).all()
        
        dataset_list = []
        for dataset in datasets:
            dataset_data = {
                "name": dataset.name,
                "path": dataset.access_path or f"/data/training_{training_id}/{dataset.name}",
                "description": dataset.description or f"数据集: {dataset.name}"
            }
            dataset_list.append(dataset_data)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={"datasets": dataset_list}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/sessions/{session_id}/status", response_model=schemas.ApiResponse)
def get_training_session_status(
    session_id: str,
    student_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取实训会话状态"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))
        session = db.query(db_models.PracticeEnvironmentSession).filter(
            db_models.PracticeEnvironmentSession.session_id == session_id,
            db_models.PracticeEnvironmentSession.user_id == student_id
        ).first()
        
        if not session:
            return schemas.ApiResponse(
                code="1002",
                message="会话不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 检查是否过期
        if session.expires_at:
            now = datetime.now(timezone.utc)
            expires_at = session.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if now > expires_at:
                session.status = "expired"
                db.commit()
        
        status_data = {
            "session_id": session.session_id,
            "status": session.status,
            "env_type": session.env_type,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "expires_at": session.expires_at.isoformat() if session.expires_at else None
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data=status_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/sessions/{session_id}/stop", response_model=schemas.ApiResponse)
def stop_training_session(
    session_id: str,
    student_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """停止实训会话"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))
        session = db.query(db_models.PracticeEnvironmentSession).filter(
            db_models.PracticeEnvironmentSession.session_id == session_id,
            db_models.PracticeEnvironmentSession.user_id == student_id
        ).first()
        
        if not session:
            return schemas.ApiResponse(
                code="1002",
                message="会话不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 更新会话状态
        session.status = "terminated"
        
        # 更新学习记录
        training_log = db.query(db_models.TrainingLearningLog).filter(
            db_models.TrainingLearningLog.user_id == student_id,
            db_models.TrainingLearningLog.training_id == session.task_id,
            db_models.TrainingLearningLog.end_time.is_(None)
        ).first()
        
        if training_log:
            training_log.end_time = datetime.now(timezone.utc)
            if training_log.start_time:
                start_time = training_log.start_time
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                duration = training_log.end_time - start_time
                training_log.duration_seconds = int(duration.total_seconds())
        
        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message="实训会话已停止",
            data={"session_id": session_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


# ==================== 资源初始化管理API ====================

@router.post("/training-resources/seed", response_model=schemas.ApiResponse)
def seed_training_resources_api(
    db: Session = Depends(get_db)
):
    """
    初始化实训资源API
    功能描述: 从 ziyuan/实训资源/ 目录加载实训项目到数据库
    """
    try:
        from app.utils.training_resource_seeder import seed_training_resources
        results = seed_training_resources()
        
        return schemas.ApiResponse(
            code="0000",
            message="实训资源初始化完成",
            data=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"初始化失败: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


# ==================== 学情分析API ====================
