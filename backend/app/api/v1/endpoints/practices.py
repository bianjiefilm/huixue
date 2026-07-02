"""
实践管理端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, File, Form, UploadFile, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict, Any
import uuid
import logging
from datetime import datetime, timezone, timedelta
import json
from pydantic import ValidationError, BaseModel

# 修正的导入路径
from app.core.database import get_db, engine, Base
from app.models import models as db_models  # 避免与FastAPI的models冲突
from app.crud import crud
from app.core.security import get_current_user
from app.core.identity import resolve_scoped_id, require_authenticated
from app.crud import practice_review
from app.crud.crud_stage_preparation import (
    get_repository_files_list,
    get_repository_file_content,
    save_repository_file_content,
    create_repository_file,
    commit_repository_changes,
    get_practice_datasets_list,
    upload_practice_dataset_file,
    get_practice_dataset_by_id,
    delete_practice_dataset_by_id,
    format_file_size
)
from app.schemas import schemas
from app.crud import my_practices_crud

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    tags=['practices']
)

@router.get("/practices", response_model=schemas.ApiResponse)
def get_practices(
    keyword: Optional[str] = Query(None, description="模糊搜索关键字"),
    direction: Optional[str] = Query(None, description="一级方向"),
    category: Optional[str] = Query(None, description="二级分类"),
    difficulty: Optional[str] = Query(None, description="难度级别"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    查询微型实验列表
    按照架构澄清方案，此API只返回practices表记录（微型实验）
    """
    try:
        skip = (page - 1) * page_size
        practices, total = crud.get_practices(
            db=db,
            skip=skip,
            limit=page_size,
            keyword=keyword,
            direction=direction,
            category=category,
            difficulty=difficulty
        )
        
        practice_list = [schemas.PracticeResponse.model_validate(practice) for practice in practices]
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": [practice.model_dump() for practice in practice_list],
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
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


@router.get("/practices/{practice_id}", response_model=schemas.ApiResponse)
def get_practice_detail(practice_id: int, db: Session = Depends(get_db)):
    """实践详情 - 包含任务列表、技能标签和推荐实践"""
    try:
        # 获取实践详情
        practice = crud.get_practice_detail(db, practice_id=practice_id)
        if practice is None:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 转换为Response Model
        practice_data = schemas.PracticeDetailResponse.model_validate(practice)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=practice_data.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.post("/practices/{practice_id}/clone", response_model=schemas.ApiResponse)
def clone_practice(
    practice_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    克隆实践
    
    复制指定实践及其关联的技能、任务等信息，创建一个新的实践。
    新实践的创建者为当前用户，状态为编辑中。
    """
    try:
        # 1. 获取原实践
        original_practice = db.query(db_models.Practice).filter(db_models.Practice.id == practice_id).first()
        if not original_practice:
            raise HTTPException(status_code=404, detail="实践不存在")
            
        # 2. 创建新实践对象
        new_practice = db_models.Practice(
            title=f"{original_practice.title} (副本)",
            description=original_practice.description,
            intro=original_practice.intro,
            direction=original_practice.direction,
            category=original_practice.category,
            difficulty=original_practice.difficulty,
            summary=original_practice.summary,
            coin=original_practice.coin,
            task_count=original_practice.task_count,
            practice_type=original_practice.practice_type,
            categories=original_practice.categories,
            environment_id=original_practice.environment_id,
            storage_limit=original_practice.storage_limit,
            memory_limit=original_practice.memory_limit,
            cpu_limit=original_practice.cpu_limit,
            persistent_path=original_practice.persistent_path,
            enable_code_editor=original_practice.enable_code_editor,
            enable_terminal=original_practice.enable_terminal,
            repo_visibility=original_practice.repo_visibility,
            allow_skip_levels=original_practice.allow_skip_levels,
            
            # 重置状态
            is_published=False,
            publish_status=db_models.PracticePublishStatusEnum.EDITING,
            visibility=db_models.PracticeVisibilityEnum.PRIVATE,
            
            # 设置创建者
            creator_id=current_user["user_id"],
            
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(new_practice)
        db.flush() # 获取 ID
        
        # 3. 复制关联的技能
        for skill in original_practice.skills:
            new_skill = db_models.PracticeSkill(
                practice_id=new_practice.id,
                skill_name=skill.skill_name
            )
            db.add(new_skill)
            
        # 4. 复制关联的任务 (Task)
        # 注意：使用 relationships 'tasks'
        for task in original_practice.tasks:
            new_task = db_models.Task(
                practice_id=new_practice.id,
                title=task.title,
                task_type=task.task_type,
                order_in_practice=task.order_in_practice,
                coin=task.coin,
                env_type=task.env_type,
                difficulty=task.difficulty,
                skills=task.skills,
                handbook_markdown=task.handbook_markdown,
                answer_content_markdown=task.answer_content_markdown,
                evaluation_script_path=task.evaluation_script_path,
                evaluation_command=task.evaluation_command,
                evaluation_timeout_seconds=task.evaluation_timeout_seconds,
                student_task_file_paths=task.student_task_file_paths,
                enable_page_preview=task.enable_page_preview,
                preview_html_file=task.preview_html_file,
                question_data=task.question_data,
                # Let autoincrement generate the id (Task.id is Integer, not UUID)
            )
            db.add(new_task)
            
        # 5. 复制代码仓库配置
        for repo in original_practice.code_repositories:
            new_repo = db_models.PracticeCodeRepository(
                practice_id=new_practice.id,
                repository_url=repo.repository_url,
                branch_name=repo.branch_name,
                is_enabled=repo.is_enabled
            )
            db.add(new_repo)
            
        # 6. 复制数据集配置
        for ds in original_practice.datasets:
            new_ds = db_models.PracticeDataset(
                practice_id=new_practice.id,
                name=ds.name,
                file_url=ds.file_url,
                file_type=ds.file_type,
                file_size=ds.file_size,
                description=ds.description,
                access_url=ds.access_url,
                uploader_id=current_user["user_id"] # 使用当前用户作为uploader，虽然文件没变
            )
            db.add(new_ds)

        db.commit()
        db.refresh(new_practice)
        
        return schemas.ApiResponse(
            code="0000",
            message="实践克隆成功",
            data={"id": new_practice.id}
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"克隆实践失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"克隆实践失败: {str(e)}")


@router.get("/direction-categories", response_model=schemas.ApiResponse)
def get_direction_categories(db: Session = Depends(get_db)):
    """获取方向分类列表 - 返回前端期望的格式"""
    try:
        # 查询direction_categories表
        from sqlalchemy import text
        result = db.execute(text("SELECT id, name, parent_id, sort_order FROM direction_categories WHERE is_active = true ORDER BY sort_order"))
        rows = list(result)
        
        # 构建前端期望的格式: {primary_categories: [...], secondary_categories: {...}}
        primary_categories = []
        secondary_categories = {}
        
        for row in rows:
            name = row[1]
            parent_id = row[2]
            
            if parent_id is None:
                # 一级分类
                primary_categories.append(name)
                secondary_categories[name] = []
            else:
                # 二级分类 - 找到父级名称
                parent_result = db.execute(text(f"SELECT name FROM direction_categories WHERE id = {parent_id}"))
                parent_row = parent_result.fetchone()
                if parent_row:
                    parent_name = parent_row[0]
                    if parent_name not in secondary_categories:
                        secondary_categories[parent_name] = []
                    secondary_categories[parent_name].append(name)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "primary_categories": primary_categories,
                "secondary_categories": secondary_categories
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取方向分类失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/practice-environments", response_model=schemas.ApiResponse)
def get_practice_environments(db: Session = Depends(get_db)):
    """获取实践环境列表 - 返回前端期望的格式"""
    try:
        # 先查询practice_environments表
        from sqlalchemy import text
        result = db.execute(text("SELECT id, name, environment_type, description FROM practice_environments WHERE is_active = true"))
        environments = [{"id": row[0], "name": row[1], "environment_type": row[2], "description": row[3] or ""} for row in result]
        
        # 如果practice_environments表为空，回退到practice_environment_configs表
        if not environments:
            result = db.execute(text("SELECT id, name, environment_type FROM practice_environment_configs WHERE is_active = true"))
            environments = [{"id": row[0], "name": row[1], "environment_type": row[2], "description": ""} for row in result]
        
        # 前端期望格式: data.environments
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={"environments": environments}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实践环境失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/custom-practices", response_model=schemas.ApiResponse)
def create_custom_practice(
    creator_id: int = Query(..., description="创建者ID"),
    practice_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建自定义实践课程"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        logger.info(f"创建自定义实践: creator_id={creator_id}, data={practice_data}")

        # 验证创建者是否存在
        creator = db.query(db_models.User).filter(db_models.User.id == creator_id).first()
        if not creator:
            return schemas.ApiResponse(
                code="1001",
                message="创建者不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 映射难度
        difficulty_map = {
            "beginner": db_models.DifficultyLevelEnum.beginner,
            "intermediate": db_models.DifficultyLevelEnum.intermediate,
            "advanced": db_models.DifficultyLevelEnum.advanced,
            "BEGINNER": db_models.DifficultyLevelEnum.beginner,
            "INTERMEDIATE": db_models.DifficultyLevelEnum.intermediate,
            "ADVANCED": db_models.DifficultyLevelEnum.advanced,
        }
        raw_difficulty = practice_data.get("difficulty", "beginner")
        difficulty_enum = difficulty_map.get(raw_difficulty, db_models.DifficultyLevelEnum.beginner)
        
        # 创建新的实践记录
        new_practice = db_models.Practice(
            title=practice_data.get("title", ""),
            description=practice_data.get("description", ""),
            difficulty=difficulty_enum,
            direction=practice_data.get("direction", ""),
            category=practice_data.get("category", "在线编码实践"),
            coin=practice_data.get("coin", 0),
            environment_id=str(practice_data.get("environment_id", "")),
            storage_limit=f"{practice_data.get('storage_limit', 50)}Mi",
            memory_limit=f"{practice_data.get('memory_limit', 1024)}Mi",
            cpu_limit=str(practice_data.get("cpu_limit", 1.0)),
            practice_type=practice_data.get("practice_type", "online_coding"),
            creator_id=creator_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            visibility=db_models.PracticeVisibilityEnum.PRIVATE,
            publish_status=db_models.PracticePublishStatusEnum.EDITING
        )
        
        db.add(new_practice)
        db.commit()
        db.refresh(new_practice)
        
        logger.info(f"实践创建成功: id={new_practice.id}, title={new_practice.title}")
        
        return schemas.ApiResponse(
            code="0000",
            message="实践创建成功",
            data={
                "practice_id": new_practice.id,
                "title": new_practice.title
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建实践失败: {str(e)}", exc_info=True)
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/custom-practices", response_model=schemas.ApiResponse)
def get_custom_practices(
    creator_id: int = Query(..., description="创建者ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户创建的自定义实践列表"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        skip = (page - 1) * page_size
        
        query = db.query(db_models.Practice).filter(
            db_models.Practice.created_by == creator_id,
            db_models.Practice.is_preset == False
        )
        
        total = query.count()
        practices = query.order_by(db_models.Practice.created_at.desc()).offset(skip).limit(page_size).all()
        
        practice_list = [{
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "difficulty": p.difficulty,
            "direction": p.direction,
            "category": p.category,
            "status": p.status or "DRAFT",
            "visibility": p.visibility or "PRIVATE",
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "task_count": p.task_count or 0,
            "coin": p.coin or 0
        } for p in practices]
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": practice_list,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取自定义实践列表失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/custom-practices/{practice_id}/stages", response_model=schemas.ApiResponse)
def create_practice_stage(
    practice_id: int,
    creator_id: int = Query(..., description="创建者ID"),
    stage_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """为实践添加关卡/任务"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        # 验证实践是否存在且属于该创建者
        practice = db.query(db_models.Practice).filter(
            db_models.Practice.id == practice_id
        ).first()
        
        if not practice:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 获取当前最大顺序
        max_order = db.query(func.max(db_models.Task.order_in_practice)).filter(
            db_models.Task.practice_id == practice_id
        ).scalar() or 0
        
        # 创建新任务 (id 由数据库自动生成)
        new_task = db_models.Task(
            practice_id=practice_id,
            title=stage_data.get("title", f"关卡{max_order + 1}"),
            task_type=stage_data.get("task_type", "PRACTICE"),
            order_in_practice=max_order + 1,
            coin=stage_data.get("coin", 10),
            difficulty=stage_data.get("difficulty", "BEGINNER"),
            skills=json.dumps(stage_data.get("skills", [])),
            handbook_markdown=stage_data.get("handbook_markdown", ""),
            answer_content_markdown=stage_data.get("answer_content_markdown", ""),
            env_type=stage_data.get("env_type", "JUPYTER")
        )
        
        db.add(new_task)
        
        # 更新实践的任务数量
        practice.task_count = (practice.task_count or 0) + 1
        
        db.commit()
        db.refresh(new_task)
        
        return schemas.ApiResponse(
            code="0000",
            message="关卡创建成功",
            data={
                "task_id": new_task.id,
                "order": new_task.order_in_practice,
                "title": new_task.title
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建关卡失败: {str(e)}", exc_info=True)
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/custom-practices/{practice_id}/publish", response_model=schemas.ApiResponse)
def publish_practice(
    practice_id: int,
    publish_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发布实践课程"""
    try:
        user_id, role = require_authenticated(current_user)

        practice = db.query(db_models.Practice).filter(
            db_models.Practice.id == practice_id
        ).first()

        if not practice:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在",
                trace_id=str(uuid.uuid4())
            )

        if role != "admin" and practice.creator_id != user_id:
            raise HTTPException(status_code=403, detail="无权限操作此实践")

        # 映射可见性
        visibility_str = publish_data.get("visibility", "PRIVATE").upper()
        if visibility_str == "PRIVATE":
            practice.visibility = db_models.PracticeVisibilityEnum.PRIVATE
            # 私有发布：直接设为已发布状态
            practice.publish_status = db_models.PracticePublishStatusEnum.PUBLISHED
            practice.is_published = True
            practice.published_at = datetime.now(timezone.utc)
            message = "实践课程发布成功！现在可以在课堂中使用该实践课程"
        else:
            practice.visibility = db_models.PracticeVisibilityEnum.PUBLIC
            # 公开发布：需要审核，设为待审核状态
            practice.publish_status = db_models.PracticePublishStatusEnum.PENDING_REVIEW
            practice.is_published = False
            practice.submitted_for_review_at = datetime.now(timezone.utc)
            message = "实践课程已提交审核！等待管理员审批通过后即可公开使用"

            # 创建审批申请记录
            course_request = db_models.CourseRequest(
                course_id=practice_id,  # 使用practice_id
                course_type=db_models.CourseTypeEnum.PRACTICE,
                applicant_id=practice.creator_id or 1,  # 使用创建者ID，如果没有则默认1
                request_type=db_models.CourseRequestTypeEnum.PUBLISH,
                status=db_models.CourseRequestStatusEnum.PENDING,
                application_reason="申请公开发布此实践课程",
                applied_at=datetime.now(timezone.utc)
            )
            db.add(course_request)

        practice.updated_at = datetime.now(timezone.utc)

        db.commit()

        return schemas.ApiResponse(
            code="0000",
            message=message,
            data={
                "practice_id": practice_id,
                "status": practice.publish_status.value if practice.publish_status else "PUBLISHED",
                "visibility": practice.visibility.value if practice.visibility else "PRIVATE"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"发布实践失败: {str(e)}", exc_info=True)
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/practices/{practice_id}/stages/management", response_model=schemas.ApiResponse)
def get_practice_stages_management(
    practice_id: int,
    creator_id: int = Query(None, description="创建者ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取实践关卡列表（管理视图）"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        tasks = db.query(db_models.Task).filter(
            db_models.Task.practice_id == practice_id
        ).order_by(db_models.Task.order_in_practice).all()
        
        stages = [{
            "id": t.id,
            "title": t.title,
            "order": t.order_in_practice,
            "task_type": t.task_type.value if hasattr(t.task_type, 'value') else str(t.task_type),
            "difficulty": t.difficulty,
            "coin": t.coin or 0,
            "skills": json.loads(t.skills) if t.skills else []
        } for t in tasks]
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={"stages": stages, "total": len(stages)}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取关卡列表失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/custom-practices/{practice_id}", response_model=schemas.ApiResponse)
def get_custom_practice_detail(
    practice_id: int,
    creator_id: int = Query(None, description="创建者ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取自定义实践详情"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        practice = db.query(db_models.Practice).filter(
            db_models.Practice.id == practice_id
        ).first()
        
        if not practice:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "id": practice.id,
                "title": practice.title,
                "description": practice.description or "",
                "direction": practice.direction or "",
                "category": practice.category or "",
                "difficulty": practice.difficulty.value if hasattr(practice.difficulty, 'value') else str(practice.difficulty),
                "environment_id": practice.environment_id,
                "storage_limit": practice.storage_limit,
                "memory_limit": practice.memory_limit,
                "cpu_limit": practice.cpu_limit,
                "practice_type": practice.practice_type or "online_coding",
                "publish_status": practice.publish_status.value if hasattr(practice.publish_status, 'value') else str(practice.publish_status or "EDITING"),
                "visibility": practice.visibility.value if hasattr(practice.visibility, 'value') else str(practice.visibility or "PRIVATE"),
                "task_count": practice.task_count or 0,
                "creator_id": practice.creator_id
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实践详情失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/practices/{practice_id}/config", response_model=schemas.ApiResponse)
def get_practice_config(
    practice_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取实践配置"""
    try:
        user_id, role = require_authenticated(current_user)

        practice = db.query(db_models.Practice).filter(
            db_models.Practice.id == practice_id
        ).first()

        if not practice:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在",
                trace_id=str(uuid.uuid4())
            )

        if role != "admin" and practice.creator_id != user_id:
            raise HTTPException(status_code=403, detail="无权限访问此实践配置")

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "enable_code_editor": practice.enable_code_editor if hasattr(practice, 'enable_code_editor') else True,
                "enable_terminal": practice.enable_terminal if hasattr(practice, 'enable_terminal') else True,
                "repo_visibility": practice.repo_visibility or "visible",
                "allow_skip_levels": practice.allow_skip_levels if hasattr(practice, 'allow_skip_levels') else True
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实践配置失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.patch("/practices/{practice_id}/config", response_model=schemas.ApiResponse)
def update_practice_config(
    practice_id: int,
    config: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新实践配置"""
    try:
        user_id, role = require_authenticated(current_user)

        practice = db.query(db_models.Practice).filter(
            db_models.Practice.id == practice_id
        ).first()

        if not practice:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在",
                trace_id=str(uuid.uuid4())
            )

        if role != "admin" and practice.creator_id != user_id:
            raise HTTPException(status_code=403, detail="无权限修改此实践配置")

        # 更新配置字段
        if "editor" in config:
            practice.enable_code_editor = config["editor"]
        if "shell" in config:
            practice.enable_terminal = config["shell"]
        if "repoVisible" in config:
            practice.repo_visibility = "visible" if config["repoVisible"] else "hidden"
        if "allowSkip" in config:
            practice.allow_skip_levels = config["allowSkip"]

        db.commit()

        return schemas.ApiResponse(
            code="0000",
            message="配置保存成功",
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新实践配置失败: {str(e)}")
        db.rollback()
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.patch("/practices/{practice_id}/basic-info", response_model=schemas.ApiResponse)
def update_practice_basic_info(
    practice_id: int,
    basic_info: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新实践课程基础信息

    支持更新：名称(name)、类型(type)、难度(difficulty)、介绍(introduction)
    仅编辑中状态的实践可以更新基础信息
    """
    try:
        user_id, role = require_authenticated(current_user)

        # 验证实践是否存在
        practice = db.query(db_models.Practice).filter(
            db_models.Practice.id == practice_id
        ).first()

        if not practice:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在",
                trace_id=str(uuid.uuid4())
            )

        if role != "admin" and practice.creator_id != user_id:
            raise HTTPException(status_code=403, detail="无权限修改此实践")

        # 检查状态（草稿或编辑中状态才能编辑）
        if practice.publish_status not in [
            db_models.PracticePublishStatusEnum.EDITING,
            db_models.PracticePublishStatusEnum.DRAFT
        ]:
            return schemas.ApiResponse(
                code="2003",
                message="只有编辑中或草稿状态的实践才能修改基础信息",
                trace_id=str(uuid.uuid4())
            )

        # 更新字段
        if "name" in basic_info and basic_info["name"]:
            practice.title = basic_info["name"]

        if "introduction" in basic_info:
            practice.intro = basic_info["introduction"]
            practice.description = basic_info["introduction"]

        if "type" in basic_info:
            # 映射实践类型
            type_map = {
                "code": "online_coding",
                "desktop": "cloud_desktop"
            }
            practice.practice_type = type_map.get(basic_info["type"], "online_coding")

        if "difficulty" in basic_info:
            # 映射难度级别
            difficulty_map = {
                "easy": db_models.DifficultyLevelEnum.beginner,
                "beginner": db_models.DifficultyLevelEnum.beginner,
                "intermediate": db_models.DifficultyLevelEnum.intermediate,
                "advanced": db_models.DifficultyLevelEnum.advanced
            }
            raw_difficulty = basic_info["difficulty"]
            practice.difficulty = difficulty_map.get(raw_difficulty, db_models.DifficultyLevelEnum.beginner)

        practice.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(practice)

        logger.info(f"实践基础信息更新成功: practice_id={practice_id}")

        return schemas.ApiResponse(
            code="0000",
            message="基础信息保存成功",
            data={
                "id": practice.id,
                "title": practice.title,
                "difficulty": practice.difficulty.value if hasattr(practice.difficulty, 'value') else str(practice.difficulty),
                "practice_type": practice.practice_type
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新实践基础信息失败: {str(e)}", exc_info=True)
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


# ==================== 数据集管理API ====================

@router.get("/practices/{practice_id}/datasets", response_model=schemas.ApiResponse)
def get_practice_datasets(
    practice_id: int,
    creator_id: int = Query(..., description="创建者ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取实践数据集列表"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        datasets = db.query(db_models.PracticeDataset).filter(
            db_models.PracticeDataset.practice_id == practice_id
        ).order_by(db_models.PracticeDataset.created_at.desc()).all()

        dataset_list = []
        for ds in datasets:
            # 格式化文件大小
            file_size = ds.file_size or 0
            if file_size < 1024:
                file_size_display = f"{file_size} B"
            elif file_size < 1024 * 1024:
                file_size_display = f"{file_size / 1024:.2f} KB"
            else:
                file_size_display = f"{file_size / (1024 * 1024):.2f} MB"

            dataset_list.append({
                "id": ds.id,
                "name": ds.name,
                "file_size": ds.file_size,
                "file_size_display": file_size_display,
                "file_type": ds.file_type,
                "access_url": ds.access_url or f"/data/dataset/{ds.name}",
                "created_at": ds.created_at.isoformat() if ds.created_at else None
            })

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={"datasets": dataset_list}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据集列表失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/practices/{practice_id}/datasets/upload", response_model=schemas.ApiResponse)
async def upload_practice_dataset(
    practice_id: int,
    file: UploadFile = File(...),
    creator_id: int = Form(...),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传数据集文件"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        import os
        from datetime import datetime

        # 创建上传目录
        upload_dir = f"uploads/practices/{practice_id}/datasets"
        os.makedirs(upload_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(upload_dir, file.filename)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # 获取文件类型
        file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''

        # 创建数据库记录
        new_dataset = db_models.PracticeDataset(
            practice_id=practice_id,
            name=file.filename,
            file_url=file_path,
            file_size=len(content),
            file_type=file_ext,
            access_url=f"/data/dataset/{file.filename}",
            description=description,
            uploader_id=creator_id,
            created_at=datetime.now()
        )
        db.add(new_dataset)
        db.commit()
        db.refresh(new_dataset)

        # 格式化文件大小
        file_size = len(content)
        if file_size < 1024:
            file_size_display = f"{file_size} B"
        elif file_size < 1024 * 1024:
            file_size_display = f"{file_size / 1024:.2f} KB"
        else:
            file_size_display = f"{file_size / (1024 * 1024):.2f} MB"

        return schemas.ApiResponse(
            code="0000",
            message="上传成功",
            data={
                "id": new_dataset.id,
                "name": new_dataset.name,
                "file_size": new_dataset.file_size,
                "file_size_display": file_size_display,
                "file_type": new_dataset.file_type,
                "access_url": new_dataset.access_url,
                "created_at": new_dataset.created_at.isoformat() if new_dataset.created_at else None
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传数据集失败: {str(e)}")
        db.rollback()
        return schemas.ApiResponse(
            code="2000",
            message=f"上传失败: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/practices/{practice_id}/datasets/{dataset_id}/copy-url", response_model=schemas.ApiResponse)
def get_dataset_copy_url(
    practice_id: int,
    dataset_id: int,
    creator_id: int = Query(..., description="创建者ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取数据集复制地址（容器内路径）"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        dataset = db.query(db_models.PracticeDataset).filter(
            db_models.PracticeDataset.id == dataset_id,
            db_models.PracticeDataset.practice_id == practice_id
        ).first()

        if not dataset:
            return schemas.ApiResponse(
                code="1002",
                message="数据集不存在",
                trace_id=str(uuid.uuid4())
            )

        # 返回容器内部路径
        access_url = f"/data/dataset/{dataset.name}"

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={"access_url": access_url}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据集地址失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.delete("/practices/{practice_id}/datasets/{dataset_id}", response_model=schemas.ApiResponse)
def delete_practice_dataset(
    practice_id: int,
    dataset_id: int,
    creator_id: int = Query(..., description="创建者ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除数据集"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        import os

        dataset = db.query(db_models.PracticeDataset).filter(
            db_models.PracticeDataset.id == dataset_id,
            db_models.PracticeDataset.practice_id == practice_id
        ).first()

        if not dataset:
            return schemas.ApiResponse(
                code="1002",
                message="数据集不存在",
                trace_id=str(uuid.uuid4())
            )

        # 删除文件
        if dataset.file_url and os.path.exists(dataset.file_url):
            os.remove(dataset.file_url)

        # 删除数据库记录
        db.delete(dataset)
        db.commit()

        return schemas.ApiResponse(
            code="0000",
            message="删除成功",
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除数据集失败: {str(e)}")
        db.rollback()
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/my-practices", response_model=schemas.ApiResponse)
def get_my_practices(
    creator_id: int = Query(..., description="创建者ID"),
    keyword: Optional[str] = Query(None, description="搜索关键字"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取我创建的实践列表"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        skip = (page - 1) * page_size

        practices, total = my_practices_crud.get_my_practices_enhanced(
            db=db,
            creator_id=creator_id,
            keyword=keyword,
            skip=skip,
            limit=page_size
        )

        # 序列化日期字段
        practice_list = []
        for p in practices:
            item = dict(p)
            if item.get("created_at"):
                item["created_at"] = item["created_at"].isoformat() if hasattr(item["created_at"], 'isoformat') else str(item["created_at"])
            if item.get("updated_at"):
                item["updated_at"] = item["updated_at"].isoformat() if hasattr(item["updated_at"], 'isoformat') else str(item["updated_at"])
            if item.get("published_at"):
                item["published_at"] = item["published_at"].isoformat() if hasattr(item["published_at"], 'isoformat') else str(item["published_at"])
            practice_list.append(item)

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": practice_list,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取我创建的实践列表失败: {str(e)}", exc_info=True)
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.patch("/my-practices/{practice_id}/status", response_model=schemas.ApiResponse)
def update_my_practice_status(
    practice_id: int,
    creator_id: int = Query(..., description="创建者ID"),
    action: str = Body(..., embed=True, description="操作类型: start_edit, cancel_edit, publish, offline, delete"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新我创建的实践状态"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        result, message = my_practices_crud.update_practice_status(
            db=db,
            practice_id=practice_id,
            creator_id=creator_id,
            action=action
        )

        if result is None:
            return schemas.ApiResponse(
                code="2001",
                message=message
            )

        # 如果是删除操作，直接返回成功
        if isinstance(result, dict) and result.get("deleted"):
            return schemas.ApiResponse(
                code="0000",
                message=message
            )

        # 返回更新后的状态
        status = my_practices_crud._determine_practice_status(result)
        return schemas.ApiResponse(
            code="0000",
            message=message,
            data={
                "id": result.id,
                "status": status,
                "publish_status": result.publish_status.value if result.publish_status else None,
                "is_published": result.is_published
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新实践状态失败: {str(e)}", exc_info=True)
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/practices/{practice_id}/repo/init", response_model=schemas.ApiResponse)
def init_practice_repository(
    practice_id: int,
    creator_id: int = Query(..., description="创建者ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """初始化实践代码仓库"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        # 验证实践是否存在
        practice = db.query(db_models.Practice).filter(
            db_models.Practice.id == practice_id
        ).first()

        if not practice:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在",
                trace_id=str(uuid.uuid4())
            )

        # 验证创建者权限
        if practice.creator_id != creator_id:
            return schemas.ApiResponse(
                code="1003",
                message="无权限操作此实践",
                trace_id=str(uuid.uuid4())
            )

        # 检查是否已有仓库
        existing_repo = db.query(db_models.PracticeCodeRepository).filter(
            db_models.PracticeCodeRepository.practice_id == practice_id
        ).first()

        if existing_repo:
            # 如果已存在，启用它
            existing_repo.is_enabled = True
            db.commit()
            return schemas.ApiResponse(
                code="0000",
                message="代码仓库已启用",
                data={
                    "repo_id": existing_repo.id,
                    "practice_id": practice_id,
                    "is_enabled": True
                }
            )

        # 创建新的代码仓库记录
        new_repo = db_models.PracticeCodeRepository(
            practice_id=practice_id,
            repository_url=f"/practices/{practice_id}/repo",
            branch_name="main",
            is_enabled=True
        )

        db.add(new_repo)
        db.commit()
        db.refresh(new_repo)

        logger.info(f"代码仓库初始化成功: practice_id={practice_id}, repo_id={new_repo.id}")

        return schemas.ApiResponse(
            code="0000",
            message="代码仓库初始化成功",
            data={
                "repo_id": new_repo.id,
                "practice_id": practice_id,
                "is_enabled": True,
                "branch_name": "main"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"初始化代码仓库失败: {str(e)}", exc_info=True)
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/practices/{practice_id}/repo/status", response_model=schemas.ApiResponse)
def get_repo_status(
    practice_id: int,
    creator_id: int = Query(..., description="创建者ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取代码仓库状态"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        # 验证实践是否存在
        practice = db.query(db_models.Practice).filter(
            db_models.Practice.id == practice_id
        ).first()

        if not practice:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在",
                trace_id=str(uuid.uuid4())
            )

        # 查找仓库记录
        repo = db.query(db_models.PracticeCodeRepository).filter(
            db_models.PracticeCodeRepository.practice_id == practice_id
        ).first()

        if repo and repo.is_enabled:
            return schemas.ApiResponse(
                code="0000",
                message="仓库已启用",
                data={
                    "repo_id": repo.id,
                    "practice_id": practice_id,
                    "is_enabled": True,
                    "branch_name": repo.branch_name or "main",
                    "repository_url": repo.repository_url
                }
            )
        else:
            return schemas.ApiResponse(
                code="0000",
                message="仓库未启用",
                data={
                    "is_enabled": False
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取仓库状态失败: {str(e)}", exc_info=True)
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/practices/{practice_id}/repo/files", response_model=schemas.ApiResponse)
def get_repo_files(
    practice_id: int,
    path: str = Query("", description="文件路径，空表示根目录"),
    creator_id: int = Query(..., description="创建者ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取代码仓库文件列表"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        # 验证实践和仓库
        repo = db.query(db_models.PracticeCodeRepository).filter(
            db_models.PracticeCodeRepository.practice_id == practice_id,
            db_models.PracticeCodeRepository.is_enabled == True
        ).first()

        if not repo:
            return schemas.ApiResponse(
                code="1002",
                message="代码仓库未开启",
                trace_id=str(uuid.uuid4())
            )

        # 获取文件列表
        query = db.query(db_models.PracticeRepoFile).filter(
            db_models.PracticeRepoFile.repo_id == repo.id
        )

        if path:
            query = query.filter(db_models.PracticeRepoFile.parent_path == path)
        else:
            query = query.filter(
                (db_models.PracticeRepoFile.parent_path == None) |
                (db_models.PracticeRepoFile.parent_path == "")
            )

        files = query.all()

        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "files": [
                    {
                        "id": f.id,
                        "file_path": f.file_path,
                        "file_name": f.file_name,
                        "is_directory": f.is_directory,
                        "parent_path": f.parent_path,
                        "updated_at": f.updated_at.isoformat() if f.updated_at else None
                    }
                    for f in files
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取代码仓库文件列表失败: {str(e)}", exc_info=True)
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


class RepoFileCreateRequest(BaseModel):
    file_path: str
    content: str = ""
    is_directory: bool = False
    creator_id: int


@router.post("/practices/{practice_id}/repo/files", response_model=schemas.ApiResponse)
def create_or_update_repo_file(
    practice_id: int,
    request: RepoFileCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建或更新代码仓库文件"""
    try:
        path = request.file_path
        content = request.content
        is_directory = request.is_directory
        # 【IDOR 修复】creator_id 不能信任 body，必须与 JWT 身份核对
        creator_id = resolve_scoped_id(current_user, request.creator_id, allowed_roles=("teacher", "admin"))

        # 验证实践和仓库
        repo = db.query(db_models.PracticeCodeRepository).filter(
            db_models.PracticeCodeRepository.practice_id == practice_id,
            db_models.PracticeCodeRepository.is_enabled == True
        ).first()

        if not repo:
            return schemas.ApiResponse(
                code="1002",
                message="代码仓库未开启",
                trace_id=str(uuid.uuid4())
            )

        # 解析文件路径
        path = path.strip("/")
        if not path:
            return schemas.ApiResponse(
                code="1003",
                message="文件路径不能为空",
                trace_id=str(uuid.uuid4())
            )

        # 获取文件名和父路径
        parts = path.rsplit("/", 1)
        if len(parts) == 1:
            file_name = parts[0]
            parent_path = ""
        else:
            parent_path, file_name = parts

        # 检查文件是否已存在
        existing_file = db.query(db_models.PracticeRepoFile).filter(
            db_models.PracticeRepoFile.repo_id == repo.id,
            db_models.PracticeRepoFile.file_path == path
        ).first()

        if existing_file:
            # 更新现有文件
            existing_file.content = content
            db.commit()
            db.refresh(existing_file)

            return schemas.ApiResponse(
                code="0000",
                message="文件更新成功",
                data={
                    "id": existing_file.id,
                    "file_path": existing_file.file_path,
                    "file_name": existing_file.file_name,
                    "is_directory": existing_file.is_directory
                }
            )
        else:
            # 创建新文件
            new_file = db_models.PracticeRepoFile(
                repo_id=repo.id,
                file_path=path,
                file_name=file_name,
                content=content if not is_directory else None,
                is_directory=is_directory,
                parent_path=parent_path if parent_path else None
            )

            db.add(new_file)
            db.commit()
            db.refresh(new_file)

            return schemas.ApiResponse(
                code="0000",
                message="文件创建成功",
                data={
                    "id": new_file.id,
                    "file_path": new_file.file_path,
                    "file_name": new_file.file_name,
                    "is_directory": new_file.is_directory
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建/更新代码仓库文件失败: {str(e)}", exc_info=True)
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/practices/{practice_id}/repo/files/{file_id}", response_model=schemas.ApiResponse)
def get_repo_file_content(
    practice_id: int,
    file_id: int,
    creator_id: int = Query(..., description="创建者ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取代码仓库文件内容"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        # 验证实践和仓库
        repo = db.query(db_models.PracticeCodeRepository).filter(
            db_models.PracticeCodeRepository.practice_id == practice_id,
            db_models.PracticeCodeRepository.is_enabled == True
        ).first()

        if not repo:
            return schemas.ApiResponse(
                code="1002",
                message="代码仓库未开启",
                trace_id=str(uuid.uuid4())
            )

        # 获取文件
        file = db.query(db_models.PracticeRepoFile).filter(
            db_models.PracticeRepoFile.id == file_id,
            db_models.PracticeRepoFile.repo_id == repo.id
        ).first()

        if not file:
            return schemas.ApiResponse(
                code="1003",
                message="文件不存在",
                trace_id=str(uuid.uuid4())
            )

        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "id": file.id,
                "file_path": file.file_path,
                "file_name": file.file_name,
                "content": file.content or "",
                "is_directory": file.is_directory,
                "updated_at": file.updated_at.isoformat() if file.updated_at else None
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取代码仓库文件内容失败: {str(e)}", exc_info=True)
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.delete("/practices/{practice_id}/repo/files/{file_id}", response_model=schemas.ApiResponse)
def delete_repo_file(
    practice_id: int,
    file_id: int,
    creator_id: int = Query(..., description="创建者ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除代码仓库文件"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        # 验证实践和仓库
        repo = db.query(db_models.PracticeCodeRepository).filter(
            db_models.PracticeCodeRepository.practice_id == practice_id,
            db_models.PracticeCodeRepository.is_enabled == True
        ).first()

        if not repo:
            return schemas.ApiResponse(
                code="1002",
                message="代码仓库未开启",
                trace_id=str(uuid.uuid4())
            )

        # 获取文件
        file = db.query(db_models.PracticeRepoFile).filter(
            db_models.PracticeRepoFile.id == file_id,
            db_models.PracticeRepoFile.repo_id == repo.id
        ).first()

        if not file:
            return schemas.ApiResponse(
                code="1003",
                message="文件不存在",
                trace_id=str(uuid.uuid4())
            )

        # 如果是目录，需要删除所有子文件
        if file.is_directory:
            db.query(db_models.PracticeRepoFile).filter(
                db_models.PracticeRepoFile.repo_id == repo.id,
                db_models.PracticeRepoFile.parent_path.like(f"{file.file_path}%")
            ).delete(synchronize_session=False)

        db.delete(file)
        db.commit()

        return schemas.ApiResponse(
            code="0000",
            message="文件删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除代码仓库文件失败: {str(e)}", exc_info=True)
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )
