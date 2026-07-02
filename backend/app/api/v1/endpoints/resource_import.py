"""
资源导入API端点 - 简化版本
删除所有同步服务相关代码，只保留基础功能
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import (
    Training, Practice, Task, Question, User,
    Course
)
# 不需要额外的 schema 和 crud 导入
from app.core.dependencies import get_current_user
from app.services.resource_scanner import IntelligentResourceScanner
# 同步服务相关模块已删除，不再需要导入

router = APIRouter(prefix="/resource-import", tags=["resource-import"])

# 基础资源路径 - 使用ziyuan_data目录 (从backend目录再往上一级)
BASE_RESOURCE_PATH = Path(__file__).parent.parent.parent.parent.parent.parent / "ziyuan_data"

logger = logging.getLogger(__name__)


@router.post("/scan/trainings")
async def scan_training_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """扫描实训资源目录 - 使用智能扫描器动态发现资源"""
    # 处理用户权限 - current_user可能是字典或对象
    user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
    if user_role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="权限不足")

    try:
        scanner = IntelligentResourceScanner(BASE_RESOURCE_PATH)
        resources = scanner.scan_all_resources()

        # 返回扫描结果统计
        return {
            "code": "0000",
            "msg": "资源扫描完成",
            "data": {
                "trainings": len(resources.get("trainings", [])),
                "courses": len(resources.get("courses", [])),
                "total": len(resources.get("trainings", [])) + len(resources.get("courses", [])),
                "resources": resources
            }
        }
    except Exception as e:
        logger.error(f"扫描实训资源失败: {e}")
        return {
            "code": "2000",
            "msg": f"扫描实训资源失败: {str(e)}"
        }


@router.post("/scan/practices")
async def scan_practice_resources(
    course_name: str = Query(..., description="课程名称"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """扫描课程下的实践/微型实验资源"""
    import json

    # 处理用户权限
    user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
    if user_role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="权限不足")

    try:
        # 构建课程资源路径
        course_path = BASE_RESOURCE_PATH / "课程资源" / course_name

        practices = []

        if course_path.exists():
            # 检查是否使用 chapters/sections 结构
            chapters_path = course_path / "chapters"

            if chapters_path.exists():
                # 新结构: course/chapters/chapter-name/sections/section-name
                for chapter_dir in sorted(chapters_path.iterdir()):
                    if chapter_dir.is_dir():
                        chapter_name = chapter_dir.name
                        sections_path = chapter_dir / "sections"

                        if sections_path.exists():
                            for section_dir in sorted(sections_path.iterdir()):
                                if section_dir.is_dir():
                                    section_name = section_dir.name

                                    # 检查是否为实践类型 (通过section.json或目录名判断)
                                    is_practice = False
                                    section_json = section_dir / "section.json"

                                    if section_json.exists():
                                        try:
                                            with open(section_json, 'r', encoding='utf-8') as f:
                                                section_data = json.load(f)
                                                if section_data.get("type") == "practice":
                                                    is_practice = True
                                        except:
                                            pass

                                    # 也检查目录名是否包含实践相关关键词
                                    if "实战" in section_name or "实践" in section_name or "练习" in section_name:
                                        is_practice = True

                                    if is_practice:
                                        practices.append({
                                            "name": f"{chapter_name} - {section_name}",
                                            "chapter": chapter_name,
                                            "section": section_name,
                                            "path": str(section_dir.relative_to(BASE_RESOURCE_PATH)),
                                            "type": "practice",
                                            "has_config": section_json.exists()
                                        })
            else:
                # 旧结构: course/chapter-name/section-name/微型实验
                for chapter_dir in sorted(course_path.iterdir()):
                    if chapter_dir.is_dir() and chapter_dir.name.startswith(tuple("0123456789")):
                        chapter_name = chapter_dir.name

                        for section_dir in sorted(chapter_dir.iterdir()):
                            if section_dir.is_dir():
                                section_name = section_dir.name

                                micro_practice_dir = section_dir / "微型实验"
                                practice_dir = section_dir / "实践"

                                target_dir = None
                                if micro_practice_dir.exists():
                                    target_dir = micro_practice_dir
                                elif practice_dir.exists():
                                    target_dir = practice_dir

                                if target_dir:
                                    stages = []
                                    for item in sorted(target_dir.iterdir()):
                                        if item.is_dir():
                                            stages.append({
                                                "name": item.name,
                                                "path": str(item.relative_to(BASE_RESOURCE_PATH))
                                            })

                                    if stages:
                                        practices.append({
                                            "name": f"{chapter_name} - {section_name}",
                                            "chapter": chapter_name,
                                            "section": section_name,
                                            "path": str(target_dir.relative_to(BASE_RESOURCE_PATH)),
                                            "stages": stages,
                                            "type": "micro_practice"
                                        })

        return {
            "code": "0000",
            "msg": "扫描完成",
            "data": {
                "course_name": course_name,
                "practices": practices,
                "total": len(practices)
            }
        }
    except Exception as e:
        logger.error(f"扫描实践资源失败: {e}")
        return {
            "code": "2000",
            "msg": f"扫描实践资源失败: {str(e)}"
        }


@router.post("/import/training")
async def import_training_resource(
    resource_path: str = Form(..., description="资源路径"),
    force_update: bool = Form(False, description="是否强制更新"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导入单个实训资源"""
    user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
    if user_role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="权限不足")

    try:
        scanner = IntelligentResourceScanner(BASE_RESOURCE_PATH)
        resources = scanner.scan_all_resources()

        # 查找指定的资源
        target_resource = None
        for training in resources.get("trainings", []):
            if training["path"] == resource_path:
                target_resource = training
                break

        if not target_resource:
            return {
                "code": "1002",
                "msg": "未找到指定的资源"
            }

        # 检查是否已存在
        existing = db.query(Training).filter(Training.title == target_resource["title"]).first()
        if existing and not force_update:
            return {
                "code": "1001",
                "msg": "资源已存在，如需更新请设置force_update=true"
            }

        # 创建或更新实训记录
        if existing:
            # 更新现有记录
            existing.intro = target_resource.get("intro", "")
            existing.industry = target_resource.get("industry", "")
            existing.training_type = target_resource.get("training_type", "CODING")
            existing.difficulty = target_resource.get("difficulty", "intermediate")
            existing.course_hours = target_resource.get("course_hours", 4)
            existing.updated_at = datetime.now()
        else:
            # 创建新记录
            new_training = Training(
                title=target_resource["title"],
                intro=target_resource.get("intro", ""),
                industry=target_resource.get("industry", ""),
                training_type=target_resource.get("training_type", "CODING"),
                difficulty=target_resource.get("difficulty", "intermediate"),
                course_hours=target_resource.get("course_hours", 4),
                creator_id=current_user.get("id") if isinstance(current_user, dict) else current_user.id,
                publish_status="PUBLISHED",
                visibility="PUBLIC"
            )
            db.add(new_training)

        db.commit()

        return {
            "code": "0000",
            "msg": f"实训资源导入{'更新' if existing else '创建'}成功",
            "data": {
                "title": target_resource["title"],
                "action": "updated" if existing else "created"
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"导入实训资源失败: {e}")
        return {
            "code": "2000",
            "msg": f"导入实训资源失败: {str(e)}"
        }


@router.post("/import/course")
async def import_course_resource(
    resource_path: str = Form(..., description="资源路径"),
    force_update: bool = Form(False, description="是否强制更新"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导入单个课程资源"""
    user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
    if user_role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="权限不足")

    try:
        scanner = IntelligentResourceScanner(BASE_RESOURCE_PATH)
        resources = scanner.scan_all_resources()

        # 查找指定的资源
        target_resource = None
        for course in resources.get("courses", []):
            if course["path"] == resource_path:
                target_resource = course
                break

        if not target_resource:
            return {
                "code": "1002",
                "msg": "未找到指定的资源"
            }

        # 检查是否已存在
        existing = db.query(Practice).filter(Practice.title == target_resource["title"]).first()
        if existing and not force_update:
            return {
                "code": "1001",
                "msg": "资源已存在，如需更新请设置force_update=true"
            }

        # 创建或更新课程记录
        if existing:
            # 更新现有记录
            existing.description = target_resource.get("description", "")
            existing.direction = target_resource.get("direction", "编程语言")
            existing.category = target_resource.get("category", "Python基础")
            existing.difficulty = target_resource.get("difficulty", "beginner")
            existing.updated_at = datetime.now()
        else:
            # 创建新记录
            new_practice = Practice(
                title=target_resource["title"],
                description=target_resource.get("description", ""),
                cover_url=target_resource.get("cover_url", ""),
                difficulty=target_resource.get("difficulty", "beginner"),
                direction=target_resource.get("direction", "编程语言"),
                category=target_resource.get("category", "Python基础"),
                creator_id=current_user.get("id") if isinstance(current_user, dict) else current_user.id,
                publish_status="PUBLISHED",
                visibility="PUBLIC"
            )
            db.add(new_practice)

        db.commit()

        return {
            "code": "0000",
            "msg": f"课程资源导入{'更新' if existing else '创建'}成功",
            "data": {
                "title": target_resource["title"],
                "action": "updated" if existing else "created"
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"导入课程资源失败: {e}")
        return {
            "code": "2000",
            "msg": f"导入课程资源失败: {str(e)}"
        }


@router.post("/upload")
async def upload_resource_file(
    file: UploadFile = File(...),
    resource_type: str = Form(..., description="资源类型: training/course"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传资源文件 (简化版本)"""
    user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
    if user_role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="权限不足")

    try:
        # 保存上传的文件
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        return {
            "code": "0000",
            "msg": "文件上传成功",
            "data": {
                "file_path": str(file_path),
                "resource_type": resource_type
            }
        }
    except Exception as e:
        logger.error(f"上传文件失败: {e}")
        return {
            "code": "2000",
            "msg": f"上传文件失败: {str(e)}"
        }