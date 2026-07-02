"""
课程资源API
支持直接通过课程ID获取资源，解决Course-Classroom关联问题
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models import models
from app.schemas import schemas
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/courses/{course_id}/classroom", response_model=schemas.ApiResponse)
def get_course_classroom(
    course_id: int,
    db: Session = Depends(get_db)
):
    """获取课程关联的课堂"""
    try:
        # 查找课程
        course = db.query(models.Course).filter(
            models.Course.id == course_id
        ).first()

        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        # 查找关联的课堂（通过课堂名称匹配）
        classroom = db.query(models.Classroom).filter(
            models.Classroom.name.like(f"{course.title}%")
        ).first()

        if not classroom:
            # 如果没有找到课堂，返回默认课堂ID
            logger.warning(f"课程 {course.title} 没有关联的课堂，使用默认课堂")
            return schemas.ApiResponse(
                code="0000",
                message="未找到关联课堂，使用默认课堂",
                data={"classroom_id": 1}
            )

        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "classroom_id": classroom.id,
                "classroom_name": classroom.name,
                "course_title": course.title
            }
        )

    except Exception as e:
        logger.error(f"获取课程课堂失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/courses/{course_id}/resource-modules", response_model=schemas.ApiResponse)
def get_course_resource_modules(
    course_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db)
):
    """直接通过课程ID获取教学资源模块"""
    try:
        # 查找课程
        course = db.query(models.Course).filter(
            models.Course.id == course_id
        ).first()

        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        # 查找关联的课堂
        classroom = db.query(models.Classroom).filter(
            models.Classroom.name.like(f"{course.title}%")
        ).first()

        if not classroom:
            logger.warning(f"课程 {course.title} 没有关联的课堂")
            return schemas.ApiResponse(
                code="0000",
                message="课程暂无教学资源",
                data={"modules": []}
            )

        # 获取模块列表
        modules_query = db.query(models.ResourceModule).filter(
            models.ResourceModule.classroom_id == classroom.id
        )

        if teacher_id:
            modules_query = modules_query.filter(
                models.ResourceModule.teacher_id == teacher_id
            )

        modules = modules_query.order_by(models.ResourceModule.order_index).all()

        # 格式化返回数据
        modules_data = []
        for module in modules:
            # 统计模块下的文件数量
            file_count = db.query(func.count(models.ResourceFile.id)).filter(
                models.ResourceFile.module_id == module.id
            ).scalar()

            modules_data.append({
                "id": module.id,
                "name": module.name,
                "description": module.description,
                "file_count": file_count,
                "order_num": module.order_index,
                "created_at": module.created_at.isoformat() if module.created_at else None
            })

        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "modules": modules_data,
                "course_id": course_id,
                "classroom_id": classroom.id,
                "total_modules": len(modules_data)
            }
        )

    except Exception as e:
        logger.error(f"获取课程资源模块失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/courses/{course_id}/resource-files", response_model=schemas.ApiResponse)
def get_course_resource_files(
    course_id: int,
    module_id: Optional[int] = Query(None, description="模块ID，不指定则返回所有模块的文件"),
    file_type: Optional[str] = Query(None, description="文件类型过滤"),
    db: Session = Depends(get_db)
):
    """获取课程的资源文件列表"""
    try:
        # 查找课程
        course = db.query(models.Course).filter(
            models.Course.id == course_id
        ).first()

        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        # 查找关联的课堂
        classroom = db.query(models.Classroom).filter(
            models.Classroom.name.like(f"{course.title}%")
        ).first()

        if not classroom:
            return schemas.ApiResponse(
                code="0000",
                message="课程暂无资源文件",
                data={"files": [], "total_files": 0}
            )

        # 构建查询
        files_query = db.query(models.ResourceFile).join(
            models.ResourceModule,
            models.ResourceFile.module_id == models.ResourceModule.id
        ).filter(
            models.ResourceModule.classroom_id == classroom.id
        )

        # 应用过滤条件
        if module_id:
            files_query = files_query.filter(
                models.ResourceFile.module_id == module_id
            )

        if file_type:
            files_query = files_query.filter(
                models.ResourceFile.file_type == file_type
            )

        files = files_query.order_by(
            models.ResourceModule.order_index,
            models.ResourceFile.created_at
        ).all()

        # 格式化返回数据
        files_data = []
        for file in files:
            files_data.append({
                "id": file.id,
                "file_name": file.file_name,
                "file_type": file.file_type,
                "file_url": file.file_url,
                "file_size": file.file_size,
                "module_id": file.module_id,
                "module_name": file.module.name if file.module else None,
                "created_at": file.created_at.isoformat() if file.created_at else None
            })

        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "files": files_data,
                "total_files": len(files_data),
                "course_id": course_id,
                "classroom_id": classroom.id
            }
        )

    except Exception as e:
        logger.error(f"获取课程资源文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/courses/{course_id}/resource-summary", response_model=schemas.ApiResponse)
def get_course_resource_summary(
    course_id: int,
    db: Session = Depends(get_db)
):
    """获取课程资源概要统计"""
    try:
        # 查找课程
        course = db.query(models.Course).filter(
            models.Course.id == course_id
        ).first()

        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        # 查找关联的课堂
        classroom = db.query(models.Classroom).filter(
            models.Classroom.name.like(f"{course.title}%")
        ).first()

        if not classroom:
            return schemas.ApiResponse(
                code="0000",
                message="课程暂无资源",
                data={
                    "course_id": course_id,
                    "course_title": course.title,
                    "total_modules": 0,
                    "total_files": 0,
                    "file_types": {}
                }
            )

        # 统计模块数量
        total_modules = db.query(func.count(models.ResourceModule.id)).filter(
            models.ResourceModule.classroom_id == classroom.id
        ).scalar()

        # 统计文件数量
        total_files = db.query(func.count(models.ResourceFile.id)).join(
            models.ResourceModule,
            models.ResourceFile.module_id == models.ResourceModule.id
        ).filter(
            models.ResourceModule.classroom_id == classroom.id
        ).scalar()

        # 按文件类型统计
        file_type_stats = db.query(
            models.ResourceFile.file_type,
            func.count(models.ResourceFile.id).label('count')
        ).join(
            models.ResourceModule,
            models.ResourceFile.module_id == models.ResourceModule.id
        ).filter(
            models.ResourceModule.classroom_id == classroom.id
        ).group_by(models.ResourceFile.file_type).all()

        file_types = {stat.file_type: stat.count for stat in file_type_stats}

        # 统计实践和任务数量
        practice_count = db.query(func.count(models.Practice.id)).filter(
            models.Practice.course_id == course_id
        ).scalar()

        task_count = db.query(func.count(models.Task.id)).join(
            models.Practice,
            models.Task.practice_id == models.Practice.id
        ).filter(
            models.Practice.course_id == course_id
        ).scalar()

        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "course_id": course_id,
                "course_title": course.title,
                "classroom_id": classroom.id,
                "total_modules": total_modules,
                "total_files": total_files,
                "practice_count": practice_count,
                "task_count": task_count,
                "file_types": file_types,
                "database_stats": {
                    "material_resources_count": course.material_resources_count,
                    "material_assessments_count": course.material_assessments_count,
                    "practice_task_count": course.practice_task_count
                }
            }
        )

    except Exception as e:
        logger.error(f"获取课程资源概要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))