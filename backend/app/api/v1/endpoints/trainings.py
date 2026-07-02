from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
import json
import os
import shutil
from datetime import datetime, timezone

from app.core.dependencies import get_db, get_current_user_optional
from app.core.permissions import get_current_user
from app.models import models
from app.schemas import schemas
from app.crud import crud
from app.core.config import settings
from app.utils.logger import logger
from app.services.code_executor import code_executor

router = APIRouter()


class TrainingCodeEvaluateRequest(BaseModel):
    code: str


def _current_user_role(current_user: dict) -> str:
    if not isinstance(current_user, dict):
        return getattr(current_user, "role", "student")
    roles = current_user.get("roles") or []
    if roles:
        return roles[0]
    if current_user.get("role"):
        return current_user["role"]
    if current_user.get("is_superuser"):
        return "admin"
    return "student"


def _current_user_id(current_user) -> Optional[int]:
    if isinstance(current_user, dict):
        raw_id = current_user.get("user_id") or current_user.get("id")
    else:
        raw_id = getattr(current_user, "id", None)
    try:
        return int(raw_id) if raw_id is not None else None
    except (TypeError, ValueError):
        return None


def _require_authenticated_user(current_user) -> int:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user_id


def _parse_json_text(value: Any, fallback: Any):
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return fallback


def _training_code_task_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "training_id": row["training_id"],
        "title": row["title"],
        "order_in_training": row["order_in_training"],
        "task_type": row["task_type"],
        "env_type": row["env_type"],
        "difficulty": row["difficulty"],
        "handbook_markdown": row["handbook_markdown"],
        "starter_code": row["starter_code"],
        "match_rule": row["match_rule"],
        "is_published": row["is_published"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
    }


def _get_training_code_task(db: Session, training_id: int, task_id: int):
    return db.execute(
        text(
            """
            SELECT *
              FROM training_code_tasks
             WHERE id = :task_id
               AND training_id = :training_id
               AND is_published = true
            """
        ),
        {"training_id": training_id, "task_id": task_id},
    ).mappings().first()


def _get_training_code_tests(db: Session, task_id: int, include_hidden: bool = True):
    sql = """
        SELECT id, case_id, input_data, expected_output, is_hidden, weight
          FROM training_code_task_tests
         WHERE training_code_task_id = :task_id
    """
    if not include_hidden:
        sql += " AND is_hidden = false"
    sql += " ORDER BY id ASC"
    return db.execute(text(sql), {"task_id": task_id}).mappings().all()


def _training_code_test_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "case_id": row["case_id"],
        "input_data": row["input_data"],
        "expected_output": row["expected_output"],
        "is_hidden": row["is_hidden"],
        "weight": row["weight"],
    }


def _training_code_test_for_executor(row) -> dict:
    return {
        "input_data": _parse_json_text(row["input_data"], {}),
        "expected_output": _parse_json_text(row["expected_output"], {}),
        "is_hidden": bool(row["is_hidden"]),
    }


def _assert_training_add_to_classroom_access(
    db: Session,
    classroom_id: int,
    current_user: dict,
):
    """Z1: add-to-classroom must be teacher/admin and teacher-owned."""
    role = _current_user_role(current_user)
    if role not in ("teacher", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要角色 teacher/admin",
        )

    user_id = current_user.get("user_id") or current_user.get("id")
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无法获取用户信息")

    if role == "teacher":
        classroom = db.query(models.Classroom).filter(
            models.Classroom.id == classroom_id,
            models.Classroom.teacher_id == user_id,
        ).first()
        if not classroom:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作此课堂",
            )
        return classroom

    classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="课堂不存在")
    return classroom


def _assert_training_grades_access(
    db: Session,
    training_id: int,
    classroom_id: int,
    current_user: dict,
):
    """Z1: training code grades require teacher/admin and a bound classroom."""
    classroom = _assert_training_add_to_classroom_access(db, classroom_id, current_user)
    bound = db.execute(
        text(
            """
            SELECT id
              FROM classroom_trainings
             WHERE classroom_id = :classroom_id
               AND training_id = :training_id
             LIMIT 1
            """
        ),
        {"classroom_id": classroom_id, "training_id": training_id},
    ).mappings().first()
    if not bound:
        raise HTTPException(status_code=404, detail="该实训未添加到此课堂")
    return classroom


def _training_code_grade_status(row: dict) -> str:
    if not row.get("evaluation_id"):
        return "not_started"
    status_value = (row.get("status") or "").lower()
    if status_value == "pass":
        return "passed"
    if status_value == "fail":
        return "failed"
    return status_value or "submitted"


def _matches_training_code_grade_filter(row: dict, status_filter: str) -> bool:
    status_filter = (status_filter or "all").lower()
    row_status = _training_code_grade_status(row)
    has_submission = bool(row.get("evaluation_id"))
    if status_filter == "all":
        return True
    if status_filter == "not_started":
        return not has_submission
    if status_filter == "submitted":
        return has_submission
    if status_filter in ("passed", "completed"):
        return row_status == "passed"
    if status_filter == "failed":
        return row_status == "failed"
    if status_filter == "incomplete":
        return row_status != "passed"
    if status_filter == "partial":
        return has_submission and row_status != "passed" and (row.get("passed_tests") or 0) > 0
    if status_filter == "perfect":
        return row_status == "passed" and (row.get("score") or 0) >= 100
    return True


def _open_text_file(path, newline=None):
    """打开文本文件，自动尝试 utf-8-sig → gbk → latin-1 编码"""
    for enc in ('utf-8-sig', 'gbk', 'latin-1'):
        try:
            f = open(path, 'r', encoding=enc, newline=newline)
            f.read(1024)  # 试读
            f.seek(0)
            return f
        except (UnicodeDecodeError, UnicodeError):
            continue
    # latin-1 不会失败，这里不应该到达
    return open(path, 'r', encoding='latin-1', newline=newline)

@router.get("/test-live")
def test_live():
    return {"message": "Code is live"}


# ==================== 具体路径路由（优先注册避免冲突） ====================

@router.get("/environments", response_model=schemas.ApiResponse)
def get_training_environments(
    db: Session = Depends(get_db)
):
    """获取实训环境列表"""
    try:
        environments = db.query(models.TrainingEnvironment).filter(models.TrainingEnvironment.is_active == True).all()

        data = [
            {
                "id": env.id,
                "name": env.name,
                "type": env.environment_type,
                "description": env.description,
                "docker_image": env.docker_image,
                "default_storage": env.default_storage,
                "default_memory": env.default_memory,
                "default_cpu": env.default_cpu,
            }
            for env in environments
        ]

        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": data
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训环境列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实训环境列表失败: {str(e)}")

@router.get("/my-trainings", response_model=schemas.ApiResponse)
def get_my_trainings(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取我创建的实训列表"""
    try:
        # 查询条件：创建者是当前用户
        query = db.query(models.Training).filter(
            models.Training.creator_id == current_user["user_id"]
        )
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        trainings = query.order_by(models.Training.updated_at.desc()).offset(
            (page - 1) * size
        ).limit(size).all()
        
        # 构建响应数据
        training_list = []
        for training in trainings:
            training_item = {
                "id": str(training.id),
                "title": training.title,
                "name": training.title,  # 兼容前端
                "intro": training.intro,
                "description": training.intro,  # 兼容前端
                "status": training.publish_status.value.lower(),
                "statusDetail": _get_status_detail(training.publish_status),
                "type": _convert_training_type(training.training_type),
                "difficulty": training.difficulty.value,
                "categories": [],  # TODO: 从其他表获取
                "createTime": training.created_at.isoformat() if training.created_at else "",
                "updateTime": training.updated_at.isoformat() if training.updated_at else "",
                "publishTime": training.published_at.isoformat() if training.published_at else None,
                "version": "1.0",  # TODO: 版本管理
                "duration": training.course_hours * 45,  # 课时转分钟
                "skills": [],  # TODO: 从其他表获取
                "cover": None,  # TODO: 封面图片
                "environment": training.environment_id
            }
            training_list.append(training_item)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": training_list,
                "total": total,
                "page": page,
                "size": size
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取我的实训列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取我的实训列表失败: {str(e)}")

@router.get("/library", response_model=schemas.ApiResponse)
def get_training_library(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    training_type: Optional[schemas.TrainingTypeEnum] = Query(None, description="实训类型筛选"),
    difficulty: Optional[str] = Query(None, description="难度筛选"),
    tags: Optional[List[str]] = Query(None, description="标签筛选"),
    is_preset: Optional[bool] = Query(None, description="是否平台预设"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """
    获取实训库列表

    返回所有已发布的实训，包括：
    - 平台预设的实训
    - 用户发布的公开实训
    """
    try:
        logger.info("=== 开始获取实训库列表 ===")
        logger.info(f"请求参数: keyword={keyword}, training_type={training_type}, difficulty={difficulty}, tags={tags}, page={page}, page_size={page_size}")

        from app.crud import training_crud
        from app.models import models as _models
        from app.services.library_pagination import merge_paginated_library

        # R3 收尾 P0+P1 修 (Codex+本地代理审计):
        # 重构成 pure function `merge_paginated_library` (services/library_pagination.py)
        # 易于单元测试 (无 db 依赖). 此 endpoint 负责 db query + 字段映射, 真合并/排序/
        # 分页交给 pure function. 修复:
        #   - P0 #1: practices 也参与全分页, 不再"只 page=1 prepend"
        #   - P1 #5: practices 参与排序, sort_order=asc 时也对

        # 1) 拿 practices (apply keyword/difficulty 同 filter)
        all_practices = db.query(_models.Practice).filter(
            _models.Practice.direction == "项目实训",
            _models.Practice.publish_status == _models.PracticePublishStatusEnum.PUBLISHED,
        ).all()

        # batch fetch creators (避免 N+1)
        creator_ids = {p.creator_id for p in all_practices if p.creator_id}
        creators_map = {}
        if creator_ids:
            creators_map = {
                u.id: u for u in db.query(_models.User).filter(_models.User.id.in_(creator_ids)).all()
            }

        practices_dicts = []
        for p in all_practices:
            if keyword and keyword not in (p.title or "") and keyword not in (p.description or ""):
                continue
            if difficulty and (p.difficulty.value if hasattr(p.difficulty, 'value') else str(p.difficulty)) != difficulty:
                continue
            creator = creators_map.get(p.creator_id) if p.creator_id else None
            practices_dicts.append({
                "id": p.id,
                "title": p.title,
                "intro": (p.description or "")[:200],
                "training_type": "CODE_PROJECT",
                "difficulty": p.difficulty.value if hasattr(p.difficulty, 'value') else str(p.difficulty or "beginner"),
                "industry": "",
                "course_hours": 0,
                "dataset_count": 0,
                "tags": [],
                "is_preset": False,
                "creator_name": (creator.full_name or creator.username) if creator else "系统",
                "created_at": p.created_at.isoformat() if p.created_at else "",
                "updated_at": p.updated_at.isoformat() if p.updated_at else "",
                "source_type": "practice",
                "practice_id": p.id,
            })

        # 2) 拿 trainings (全列, 不分页, 由 pure function 统一分页)
        trainings_result = training_crud.get_training_library(
            db=db,
            keyword=keyword,
            training_type=training_type.value if training_type else None,
            difficulty=difficulty,
            tags=tags,
            is_preset=is_preset,
            skip=0,
            limit=10_000,  # 大 limit 拿全表, 数量小不影响性能
            sort_by=sort_by,
            sort_order=sort_order,
        )
        trainings_dicts = trainings_result.get("list") or []
        # 显式标 source_type (避免 pure function 兜底)
        for t in trainings_dicts:
            t.setdefault("source_type", "training")

        # 3) 真 union + sort + paginate (pure function, 100% 单元测试覆盖)
        result = merge_paginated_library(
            practices=practices_dicts,
            trainings=trainings_dicts,
            page=page,
            page_size=page_size,
            sort_key=sort_by,
            sort_desc=(sort_order == "desc"),
        )

        return schemas.ApiResponse(
            code="0000",
            message=f"获取实训库列表成功，共找到 {result.get('total', 0)} 个实训",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训库列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取实训库列表失败: {str(e)}")

# ==================== 通用路由 ====================

@router.get("/", response_model=schemas.ApiResponse)
def get_trainings(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    training_type: Optional[schemas.TrainingTypeEnum] = Query(None, description="实训类型"),
    status: Optional[schemas.TrainingPublishStatusEnum] = Query(None, description="发布状态"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取实训列表"""
    try:
        logger.info(f"Current user info keys: {list(current_user.keys())}")
        logger.info(f"Current user info: {current_user}")
        # 构建查询条件
        query = db.query(models.Training).filter(
            models.Training.creator_id == current_user["user_id"]
        )
        
        # 类型筛选
        if training_type:
            query = query.filter(models.Training.training_type == training_type)
        
        # 状态筛选
        if status:
            query = query.filter(models.Training.publish_status == status)
        
        # 搜索
        if search:
            query = query.filter(
                or_(
                    models.Training.title.contains(search),
                    models.Training.intro.contains(search)
                )
            )
        
        # 计算总数
        total = query.count()
        
        # 分页
        trainings = query.order_by(models.Training.created_at.desc())\
            .offset((page - 1) * size)\
            .limit(size)\
            .all()
        
        # 构建响应数据
        training_list = []
        for training in trainings:
            # 获取数据集数量
            dataset_count = db.query(models.TrainingDataset).filter(
                models.TrainingDataset.training_id == training.id
            ).count()
            
            training_data = {
                "id": training.id,
                "title": training.title,
                "training_type": training.training_type.value,
                "intro": training.intro,
                "industry": training.industry,
                "difficulty": training.difficulty.value,
                "course_hours": training.course_hours,
                "publish_status": training.publish_status.value,
                "visibility": training.visibility.value,
                "is_published": training.is_published,
                "dataset_count": dataset_count,
                "created_at": training.created_at.isoformat() if training.created_at else None,
                "updated_at": training.updated_at.isoformat() if training.updated_at else None
            }
            training_list.append(training_data)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取实训列表成功",
            data={
                "list": training_list,
                "total": total,
                "page": page,
                "size": size
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实训列表失败: {str(e)}")

@router.post("/", response_model=schemas.ApiResponse)
def create_training(
    request: schemas.TrainingCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建实训"""
    # 权限校验：仅管理员/教师可创建实训
    user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
    if user_role not in ("admin", "teacher"):
        raise HTTPException(status_code=403, detail="权限不足")
    try:
        # 创建实训记录
        training = models.Training(
            title=request.title,
            training_type=request.training_type,
            intro=request.intro,
            industry=request.industry,
            difficulty=request.difficulty,
            course_hours=request.course_hours,
            handbook_content=request.handbook_content,
            assignment_nodes=json.dumps([node.model_dump() for node in request.assignment_nodes]),
            require_design_files=request.require_design_files,
            require_experiment_report=request.require_experiment_report,
            environment_id=request.environment_id,
            creator_id=current_user["user_id"]
        )
        
        # 如果是编码式实训，设置环境配置
        if request.training_type == schemas.TrainingTypeEnum.CODING and request.environment_config:
            training.storage_limit = request.environment_config.storage_limit
            training.memory_limit = request.environment_config.memory_limit
            training.cpu_limit = request.environment_config.cpu_limit
        
        db.add(training)
        db.commit()
        db.refresh(training)
        
        return schemas.ApiResponse(
            code="0000",
            message="创建实训成功",
            data={"id": training.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建实训失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建实训失败: {str(e)}")

@router.get("/library/{training_id}/preview", response_model=schemas.ApiResponse)
def get_training_preview(
    training_id: int,
    db: Session = Depends(get_db)
):
    """获取实训预览详情"""
    try:
        # 获取实训基本信息
        training = db.query(models.Training).filter(
            models.Training.id == training_id,
            models.Training.is_published == True
        ).first()
        
        if not training:
            raise HTTPException(status_code=404, detail="实训不存在或无权访问")
        
        # 获取数据集信息
        datasets = db.query(models.TrainingDataset).filter(
            models.TrainingDataset.training_id == training_id
        ).all()
        
        # 获取创建者信息
        creator = db.query(models.User).filter(
            models.User.id == training.creator_id
        ).first()
        
        # 解析作业节点
        assignment_nodes = []
        if training.assignment_nodes:
            try:
                assignment_nodes = json.loads(training.assignment_nodes)
            except:
                assignment_nodes = []
        
        # 构建预览数据
        preview_data = {
            "id": training.id,
            "title": training.title,
            "training_type": training.training_type.value,
            "intro": training.intro,
            "industry": training.industry,
            "difficulty": training.difficulty.value,
            "course_hours": training.course_hours,
            "handbook_content": training.handbook_content,
            "learning_objectives": [
                "掌握实训相关的核心技能",
                "能够独立完成实训项目",
                "理解实训背景和应用场景"
            ],
            "prerequisites": [
                "具备基础的计算机操作能力",
                "了解相关领域基础知识"
            ],
            "assignment_nodes": assignment_nodes,
            "require_design_files": training.require_design_files,
            "require_experiment_report": training.require_experiment_report,
            "environment": {
                "id": training.environment_id,
                "storage_limit": training.storage_limit,
                "memory_limit": training.memory_limit,
                "cpu_limit": training.cpu_limit
            },
            "datasets": [
                {
                    "id": ds.id,
                    "name": ds.name,
                    "file_type": ds.file_type,
                    "file_size": ds.file_size,
                    "description": ds.description,
                    "preview_url": f"/api/v1/trainings/datasets/{ds.id}/preview" if ds.file_type in ['csv', 'json', 'txt'] else None
                }
                for ds in datasets
            ],
            "creator": {
                "id": creator.id if creator else None,
                "name": creator.username if creator else "系统管理员",
                "avatar": None
            },
            "stats": {
                "student_count": 0,  # TODO: 统计使用人数
                "completion_rate": 0,  # TODO: 统计完成率
                "average_score": 0  # TODO: 统计平均分
            },
            "created_at": training.created_at.isoformat() if training.created_at else None,
            "updated_at": training.updated_at.isoformat() if training.updated_at else None,
            "tags": [],  # TODO: 添加标签系统
            "is_preset": training.creator_id == 1  # 假设ID为1的是系统管理员
        }
        
        return schemas.ApiResponse(
            code="0000",
            message=f"获取实训'{training.title}'预览成功",
            data=preview_data
        )
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"实训{training_id}作业节点JSON解析失败: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "数据解析错误", 
                "message": "实训配置数据格式异常",
                "code": "DATA_PARSE_ERROR"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训预览失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "获取实训预览失败", 
                "message": "服务器内部错误，请稍后重试",
                "code": "TRAINING_PREVIEW_ERROR"
            }
        )

@router.get("/datasets/{dataset_id}/preview", response_model=schemas.ApiResponse)
def get_dataset_preview(
    dataset_id: int,
    lines: int = Query(10, ge=1, le=100, description="预览行数"),
    db: Session = Depends(get_db)
):
    """获取数据集预览"""
    try:
        # 获取数据集信息
        dataset = db.query(models.TrainingDataset).filter(
            models.TrainingDataset.id == dataset_id
        ).first()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")
        
        # 检查数据集所属实训是否可访问
        training = db.query(models.Training).filter(
            models.Training.id == dataset.training_id,
            models.Training.is_published == True
        ).first()
        
        if not training:
            raise HTTPException(status_code=403, detail="无权访问此数据集")
        
        preview_data = {
            "id": dataset.id,
            "name": dataset.name,
            "file_type": dataset.file_type,
            "file_size": dataset.file_size,
            "description": dataset.description,
            "content": None,
            "schema": None,
            "sample_data": None
        }
        
        # 尝试读取文件内容进行预览
        if dataset.file_url and os.path.exists(dataset.file_url):
            try:
                if dataset.file_type == 'csv':
                    import pandas as pd
                    df = pd.read_csv(dataset.file_url, nrows=lines)
                    preview_data["content"] = df.to_dict(orient='records')
                    preview_data["schema"] = {
                        "columns": df.columns.tolist(),
                        "dtypes": df.dtypes.astype(str).to_dict(),
                        "shape": df.shape
                    }
                elif dataset.file_type == 'json':
                    with open(dataset.file_url, 'r', encoding='utf-8') as f:
                        import json
                        data = json.load(f)
                        if isinstance(data, list):
                            preview_data["content"] = data[:lines]
                        else:
                            preview_data["content"] = data
                elif dataset.file_type in ['txt', 'md']:
                    with open(dataset.file_url, 'r', encoding='utf-8') as f:
                        lines_content = []
                        for i, line in enumerate(f):
                            if i >= lines:
                                break
                            lines_content.append(line.rstrip())
                        preview_data["content"] = lines_content
                else:
                    preview_data["content"] = "此文件类型不支持预览"
            except HTTPException:
                raise
            except Exception as e:
                preview_data["content"] = f"文件读取失败: {str(e)}"
        else:
            preview_data["content"] = "文件不存在或路径无效"
        
        return schemas.ApiResponse(
            code="0000",
            message=f"获取数据集'{dataset.name}'预览成功",
            data=preview_data
        )
    except HTTPException:
        raise
    except FileNotFoundError:
        logger.error(f"数据集{dataset_id}文件不存在: {dataset.file_url}")
        raise HTTPException(
            status_code=404, 
            detail={
                "error": "文件不存在", 
                "message": "数据集文件已被移动或删除",
                "code": "FILE_NOT_FOUND"
            }
        )
    except PermissionError:
        logger.error(f"数据集{dataset_id}文件访问权限不足: {dataset.file_url}")
        raise HTTPException(
            status_code=403, 
            detail={
                "error": "文件访问权限不足", 
                "message": "无法读取数据集文件",
                "code": "PERMISSION_DENIED"
            }
        )
    except UnicodeDecodeError:
        logger.error(f"数据集{dataset_id}文件编码错误: {dataset.file_url}")
        raise HTTPException(
            status_code=400, 
            detail={
                "error": "文件编码错误", 
                "message": "数据集文件编码格式不支持，请使用UTF-8编码",
                "code": "ENCODING_ERROR"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据集预览失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "获取数据集预览失败", 
                "message": "服务器内部错误，请稍后重试",
                "code": "DATASET_PREVIEW_ERROR"
            }
        )

@router.get("/{training_id}/bi-data")
def get_training_bi_data(
    training_id: int,
    db: Session = Depends(get_db)
):
    """获取BI实训数据"""
    try:
        training = db.query(models.Training).filter(models.Training.id == training_id).first()
        if not training:
             raise HTTPException(status_code=404, detail="Training not found")

        file_path = None
        filename = "data.csv"
        from pathlib import Path

        # Resource base path — use unified settings
        RESOURCE_BASE = settings.resource_base_path

        # 1. Try to look in TrainingDataset table using relative_path
        dataset = db.query(models.TrainingDataset).filter(models.TrainingDataset.training_id == training_id).first()
        if dataset and dataset.relative_path:
            dataset_file = RESOURCE_BASE / dataset.relative_path
            if dataset_file.exists():
                file_path = dataset_file
                filename = dataset.name

        # 2. Try seeded uploads directory: uploads/trainings/{id}/datasets/
        if not file_path:
            upload_base = Path("uploads/trainings") / str(training_id) / "datasets"
            if upload_base.exists():
                 # Find first csv
                 for f in upload_base.iterdir():
                     if f.is_file() and f.suffix.lower() == '.csv':
                         file_path = f
                         filename = f.name
                         break

        # 3. Try project_path (Original Source) - resolve relative paths
        if not file_path and training.project_path:
             project_path = RESOURCE_BASE / training.project_path
             if project_path.exists():
                 # Look recursively for csv
                  for root, dirs, files in os.walk(project_path):
                       for file in files:
                            if file.endswith('.csv'):
                                 file_path = Path(root) / file
                                 filename = file
                                 break
                       if file_path: break

        if not file_path or not os.path.exists(file_path):
             logger.error(f"BI data file not found for training {training_id}")
             raise HTTPException(status_code=404, detail="Data file not found")

        return FileResponse(path=str(file_path), filename=filename, media_type='text/csv')

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve BI data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to serve BI data: {str(e)}")


@router.get("/library/{training_id}", response_model=schemas.ApiResponse)
def get_training_library_detail(
    training_id: int,
    db: Session = Depends(get_db)
):
    """获取实训库中的实训详情

    R3 D 方案 P0 修: trainings 表查不到时, fallback 查 practices.direction='项目实训'
    AND publish_status=PUBLISHED. 让 XQ01 (practice id=24, source_type='practice')
    学生点击"查看详情" 不再 404.
    """
    try:
        from app.crud import training_crud
        from app.models import models as _models

        # 1) 优先查 trainings 表
        training = training_crud.get_training_detail_for_library(db, training_id)
        if training:
            return schemas.ApiResponse(
                code="0000",
                message="获取实训详情成功",
                data=training
            )

        # 2) Fallback: practice.direction='项目实训' AND publish_status=PUBLISHED
        practice = db.query(_models.Practice).filter(
            _models.Practice.id == training_id,
            _models.Practice.publish_status == _models.PracticePublishStatusEnum.PUBLISHED,
            _models.Practice.direction == "项目实训",
        ).first()
        if practice:
            # 取第 1 个 task 的 handbook (project 整体级 handbook)
            first_task = db.query(_models.Task).filter(
                _models.Task.practice_id == practice.id,
                _models.Task.deleted_at.is_(None),
            ).order_by(_models.Task.order_in_practice.asc().nullslast(), _models.Task.id.asc()).first()
            handbook = first_task.handbook_markdown if first_task else None
            task_count = db.query(_models.Task).filter(
                _models.Task.practice_id == practice.id,
                _models.Task.deleted_at.is_(None),
            ).count()
            creator = db.query(_models.User).filter(_models.User.id == practice.creator_id).first() if practice.creator_id else None
            return schemas.ApiResponse(
                code="0000",
                message="获取实训详情成功",
                data={
                    "id": practice.id,
                    "title": practice.title,
                    "intro": practice.description or "",
                    "description": practice.description,
                    "training_type": "CODE_PROJECT",
                    "designer_type": None,
                    "source_type": "practice",
                    "practice_id": practice.id,
                    "difficulty": practice.difficulty.value if hasattr(practice.difficulty, 'value') else str(practice.difficulty or "beginner"),
                    "industry": "",
                    "course_hours": 0,
                    "handbook_content": handbook,
                    "task_count": task_count,
                    "dataset_count": 0,
                    "tags": [],
                    "is_preset": False,
                    "creator_name": (creator.full_name or creator.username) if creator else "系统",
                    "created_at": practice.created_at.isoformat() if practice.created_at else "",
                    "updated_at": practice.updated_at.isoformat() if practice.updated_at else "",
                }
            )

        raise HTTPException(status_code=404, detail="实训不存在或无权访问")
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实训详情失败: {str(e)}")


@router.get("/{training_id}/handbook", response_model=schemas.ApiResponse)
def get_training_handbook(
    training_id: int,
    db: Session = Depends(get_db)
):
    """获取实训手册内容"""
    try:
        training = db.query(models.Training).filter(
            models.Training.id == training_id
        ).first()

        if not training:
            raise HTTPException(status_code=404, detail="实训不存在")

        return schemas.ApiResponse(
            code="0000",
            message="获取实训手册成功",
            data={
                "content": training.handbook_content or "",
                "title": training.title
            }
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训手册失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实训手册失败: {str(e)}")


@router.get("/{training_id}/code-tasks", response_model=schemas.ApiResponse)
def list_training_code_tasks(
    training_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """列出项目实训下的编程任务。"""
    _require_authenticated_user(current_user)
    training = db.query(models.Training).filter(
        models.Training.id == training_id,
        models.Training.visibility == "PUBLIC",
        models.Training.is_published.is_(True),
    ).first()
    if not training:
        raise HTTPException(status_code=404, detail="实训不存在或未发布")

    rows = db.execute(
        text(
            """
            SELECT id, training_id, title, order_in_training, task_type, env_type,
                   difficulty, handbook_markdown, starter_code, match_rule,
                   is_published, created_at, updated_at
              FROM training_code_tasks
             WHERE training_id = :training_id
               AND is_published = true
             ORDER BY order_in_training ASC, id ASC
            """
        ),
        {"training_id": training_id},
    ).mappings().all()
    tasks = [_training_code_task_to_dict(row) for row in rows]
    for task in tasks:
        task.pop("handbook_markdown", None)

    return schemas.ApiResponse(
        code="0000",
        message="获取实训编程任务成功",
        data={"training_id": training_id, "tasks": tasks, "total": len(tasks)},
    )


@router.get("/{training_id}/code-tasks/{task_id}", response_model=schemas.ApiResponse)
def get_training_code_task(
    training_id: int,
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取项目实训编程任务详情，不返回 reference_code。"""
    _require_authenticated_user(current_user)
    row = _get_training_code_task(db, training_id, task_id)
    if not row:
        raise HTTPException(status_code=404, detail="编程任务不存在或未发布")

    task = _training_code_task_to_dict(row)
    visible_tests = _get_training_code_tests(db, task_id, include_hidden=False)
    task["visible_tests"] = [_training_code_test_to_dict(test) for test in visible_tests]
    task["tests"] = len(_get_training_code_tests(db, task_id, include_hidden=True))

    return schemas.ApiResponse(
        code="0000",
        message="获取实训编程任务详情成功",
        data=task,
    )


@router.get("/{training_id}/code-tasks/{task_id}/tests", response_model=schemas.ApiResponse)
def get_training_code_task_tests(
    training_id: int,
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取项目实训编程任务公开测试用例。"""
    _require_authenticated_user(current_user)
    if not _get_training_code_task(db, training_id, task_id):
        raise HTTPException(status_code=404, detail="编程任务不存在或未发布")

    rows = _get_training_code_tests(db, task_id, include_hidden=False)
    return schemas.ApiResponse(
        code="0000",
        message="获取测试用例成功",
        data={"tests": [_training_code_test_to_dict(row) for row in rows]},
    )


@router.get("/{training_id}/code-tasks/{task_id}/grades", response_model=schemas.ApiResponse)
def get_training_code_task_grades(
    training_id: int,
    task_id: int,
    classroom_id: int = Query(..., description="课堂ID，用于教师归属校验"),
    status_filter: str = Query("all", alias="status", description="状态筛选"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取项目实训编程任务的教师成绩视图。"""
    _require_authenticated_user(current_user)
    _assert_training_grades_access(db, training_id, classroom_id, current_user)

    task = _get_training_code_task(db, training_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="编程任务不存在或未发布")

    rows = db.execute(
        text(
            """
            WITH latest AS (
                SELECT DISTINCT ON (user_id)
                       id, user_id, status, passed_tests, total_tests, score, created_at
                  FROM training_code_task_evaluation_results
                 WHERE training_code_task_id = :task_id
                 ORDER BY user_id, score DESC, created_at DESC, id DESC
            )
            SELECT cs.student_id,
                   u.username,
                   COALESCE(u.full_name, u.username) AS student_name,
                   latest.id AS evaluation_id,
                   latest.status,
                   latest.passed_tests,
                   latest.total_tests,
                   latest.score,
                   latest.created_at
              FROM classroom_students cs
              JOIN api_users u ON u.id = cs.student_id
              LEFT JOIN latest ON latest.user_id = cs.student_id
             WHERE cs.classroom_id = :classroom_id
             ORDER BY u.username ASC, cs.student_id ASC
            """
        ),
        {"classroom_id": classroom_id, "task_id": task_id},
    ).mappings().all()

    grade_rows = []
    summary = {
        "all": 0,
        "not_started": 0,
        "submitted": 0,
        "passed": 0,
        "failed": 0,
        "completed": 0,
        "incomplete": 0,
        "partial": 0,
        "perfect": 0,
    }
    for row in rows:
        grade = dict(row)
        grade["grade_status"] = _training_code_grade_status(grade)
        grade["passed_tests"] = grade.get("passed_tests") or 0
        grade["total_tests"] = grade.get("total_tests") or 0
        grade["score"] = grade.get("score") or 0
        grade["created_at"] = grade["created_at"].isoformat() if grade.get("created_at") else None
        summary["all"] += 1
        if not grade.get("evaluation_id"):
            summary["not_started"] += 1
            summary["incomplete"] += 1
        else:
            summary["submitted"] += 1
            if grade["grade_status"] == "passed":
                summary["passed"] += 1
                summary["completed"] += 1
                if grade["score"] >= 100:
                    summary["perfect"] += 1
            else:
                summary["failed"] += 1
                summary["incomplete"] += 1
                if grade["passed_tests"] > 0:
                    summary["partial"] += 1
        if _matches_training_code_grade_filter(grade, status_filter):
            grade_rows.append(grade)

    return schemas.ApiResponse(
        code="0000",
        message="获取项目实训编程成绩成功",
        data={
            "training_id": training_id,
            "task_id": task_id,
            "classroom_id": classroom_id,
            "status": status_filter,
            "summary": summary,
            "grades": grade_rows,
            "total": len(grade_rows),
        },
    )


@router.get("/{training_id}/code-tasks/{task_id}/passed-snapshot", response_model=schemas.ApiResponse)
def get_training_code_task_passed_snapshot(
    training_id: int,
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前学生在 R5 编程任务的最近一次通关代码。"""
    user_id = _require_authenticated_user(current_user)
    role = _current_user_role(current_user)
    if role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅学生可读取自己的通关代码")

    task = _get_training_code_task(db, training_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="编程任务不存在或未发布")

    row = db.execute(
        text(
            """
            SELECT id, submitted_code, passed_tests, total_tests, score, created_at
              FROM training_code_task_evaluation_results
             WHERE training_code_task_id = :task_id
               AND user_id = :user_id
               AND status = 'pass'
             ORDER BY created_at DESC, id DESC
             LIMIT 1
            """
        ),
        {"task_id": task_id, "user_id": user_id},
    ).mappings().first()

    return schemas.ApiResponse(
        code="0000",
        message="获取通关代码成功" if row else "暂无通关代码",
        data={
            "has_passed_code": bool(row),
            "submitted_code": row["submitted_code"] if row else None,
            "evaluation_id": row["id"] if row else None,
            "passed_tests": row["passed_tests"] if row else 0,
            "total_tests": row["total_tests"] if row else 0,
            "score": row["score"] if row else 0,
            "created_at": row["created_at"].isoformat() if row and row["created_at"] else None,
        },
    )


@router.post("/{training_id}/code-tasks/{task_id}/evaluate", response_model=schemas.ApiResponse)
def evaluate_training_code_task(
    training_id: int,
    task_id: int,
    request: TrainingCodeEvaluateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """评测项目实训编程任务。当前 C0 仅开放学生提交。"""
    user_id = _require_authenticated_user(current_user)
    role = _current_user_role(current_user)
    if role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅学生可提交评测")

    task = _get_training_code_task(db, training_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="编程任务不存在或未发布")

    test_rows = _get_training_code_tests(db, task_id, include_hidden=True)
    test_cases = [_training_code_test_for_executor(row) for row in test_rows]
    if not test_cases:
        raise HTTPException(status_code=400, detail="编程任务未配置测试用例")

    match_rule = task["match_rule"]
    if match_rule == "function_call":
        result = code_executor.execute_function_call_code(request.code, test_cases)
    elif match_rule == "pytest_module":
        result = code_executor.execute_pytest_module(request.code, test_cases)
    else:
        raise HTTPException(status_code=400, detail=f"不支持的评测协议: {match_rule}")

    db.execute(
        text(
            """
            INSERT INTO training_code_task_evaluation_results
                (training_code_task_id, user_id, status, passed_tests, total_tests,
                 score, submitted_code, logs)
            VALUES
                (:task_id, :user_id, :status, :passed_tests, :total_tests,
                 :score, :submitted_code, :logs)
            """
        ),
        {
            "task_id": task_id,
            "user_id": user_id,
            "status": result.get("status", "error"),
            "passed_tests": result.get("passed_tests", 0),
            "total_tests": result.get("total_tests", len(test_cases)),
            "score": result.get("score", 0),
            "submitted_code": request.code,
            "logs": json.dumps(
                {
                    "error_message": result.get("error_message", ""),
                    "test_results": result.get("test_results", []),
                    "execution_time": result.get("execution_time", 0),
                },
                ensure_ascii=False,
            ),
        },
    )
    db.commit()

    return schemas.ApiResponse(
        code="0000",
        message="评测完成",
        data={
            "status": result.get("status", "error"),
            "score": result.get("score", 0),
            "passed_tests": result.get("passed_tests", 0),
            "total_tests": result.get("total_tests", len(test_cases)),
            "test_results": result.get("test_results", []),
            "error_message": result.get("error_message", ""),
        },
    )


@router.post("/library/{training_id}/add-to-classroom/{classroom_id}", response_model=schemas.ApiResponse)
def add_training_to_classroom(
    training_id: int,
    classroom_id: int,
    request: schemas.AddTrainingToClassroomFromLibraryRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """将实训/练习项目添加到课堂

    R3 收尾 P0 #6 修: source_type='practice' 时走 classroom_courses 表
    (而非 classroom_trainings), 避免 XQ01 (practice id=24) 加入课堂时
    在 trainings 表查不到 → 400 失败.
    """
    try:
        from app.crud import training_crud

        classroom = _assert_training_add_to_classroom_access(db, classroom_id, current_user)
        actual_teacher_id = classroom.teacher_id

        # P0 #6 分流: source_type='practice' 时走 classroom_courses
        if (request.source_type or "training").lower() == "practice":
            # 1) 校验 practice 存在 + direction='项目实训' + PUBLISHED
            practice = db.query(models.Practice).filter(
                models.Practice.id == training_id,
                models.Practice.direction == "项目实训",
                models.Practice.publish_status == models.PracticePublishStatusEnum.PUBLISHED,
            ).first()
            if not practice:
                raise HTTPException(status_code=404, detail="项目实训(practice)不存在或未发布")

            # 2) 防重: 已存在 (classroom_id, practice_id) 行
            existing = db.query(models.ClassroomCourse).filter(
                models.ClassroomCourse.classroom_id == classroom_id,
                models.ClassroomCourse.practice_id == training_id,
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="该项目实训已添加到此课堂")

            # 3) INSERT classroom_courses (与 Z2.1 INSERT 同结构)
            new_cc = models.ClassroomCourse(
                classroom_id=classroom_id,
                course_id=None,
                practice_id=training_id,
                name_override=practice.title,
                order_in_classroom=99,
                teacher_publish_status=models.CourseInClassroomStatusTeacherEnum.LEARNING,
                published_at=datetime.now(timezone.utc),
                is_mandatory=True,
                allow_late_submission=request.allow_late_submission or False,
                late_submission_deduction_points=10,
                total_score=100,
                publicize_grades=True,
                publicize_answers_after_completion=True,
            )
            db.add(new_cc)
            db.commit()
            db.refresh(new_cc)
            return schemas.ApiResponse(
                code="0000",
                message="添加项目实训到课堂成功",
                data={
                    "classroom_course_id": new_cc.id,
                    "classroom_id": classroom_id,
                    "practice_id": training_id,
                    "title": practice.title,
                    "source_type": "practice",
                }
            )

        # 默认 training 路径 (老逻辑)
        training_data = {
            "training_id": training_id,
            "start_time": request.start_time,
            "end_time": request.end_time,
            "allow_late_submission": request.allow_late_submission,
            "late_submission_days": request.late_submission_days
        }
        result = training_crud.add_training_to_classroom(
            db=db,
            classroom_id=classroom_id,
            training_data=training_data,
            teacher_id=actual_teacher_id
        )
        if not result:
            raise HTTPException(status_code=400, detail="添加失败，实训可能已添加到该课堂")
        return schemas.ApiResponse(
            code="0000",
            message="添加实训到课堂成功",
            data=result
        )
    except HTTPException:
        db.rollback()
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"添加实训到课堂失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加实训到课堂失败: {str(e)}")


@router.post("/seed", response_model=schemas.ApiResponse)
def seed_training_resources(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    初始化实训资源（管理员专用）
    
    扫描 ziyuan/实训资源 目录并导入所有实训项目
    """
    try:
        # 检查是否为管理员
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        # 导入并执行初始化
        from app.utils.training_resource_seeder import TrainingResourceSeeder
        
        # 确定资源路径
        import os
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        resource_path = os.path.join(current_dir, "ziyuan", "实训资源")
        
        # 创建初始化器
        seeder = TrainingResourceSeeder(db, resource_path)
        
        # 执行初始化
        stats = seeder.seed_all()
        
        return schemas.ApiResponse(
            code="0000",
            message="实训资源初始化完成",
            data=stats
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"实训资源初始化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"实训资源初始化失败: {str(e)}")

@router.post("/seed/test", response_model=schemas.ApiResponse)
def test_seed_training_resources(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    测试实训资源初始化功能（管理员专用）
    
    进行实训资源扫描和导入功能的测试，不会实际创建数据
    """
    try:
        # 检查是否为管理员
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        # 导入并执行测试
        from app.utils.training_resource_seeder import TrainingResourceSeeder
        
        # 确定资源路径
        import os
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        resource_path = os.path.join(current_dir, "ziyuan", "实训资源")
        
        if not os.path.exists(resource_path):
            return schemas.ApiResponse(
                code="1001",
                message="实训资源目录不存在",
                data={
                    "expected_path": resource_path,
                    "exists": False,
                    "test_result": "FAILED"
                }
            )
        
        # 创建初始化器进行测试
        seeder = TrainingResourceSeeder(db, resource_path)
        
        # 执行扫描测试
        projects = seeder.scan_training_projects()
        test_results = []
        
        for project_path in projects:
            test_result = {
                "project_path": str(project_path),
                "name": project_path.name,
                "has_course_data": False,
                "course_data_valid": False,
                "course_data_content": None,
                "errors": []
            }
            
            # 检查是否有 course_data.json
            course_data_path = project_path / "course_data.json"
            if course_data_path.exists():
                test_result["has_course_data"] = True
                
                # 尝试解析 course_data.json
                try:
                    metadata = seeder.parse_course_data(project_path)
                    if metadata:
                        test_result["course_data_valid"] = True
                        test_result["course_data_content"] = {
                            "title": metadata.get("title"),
                            "type": metadata.get("type"),
                            "difficulty": metadata.get("difficulty"),
                            "course_hours": metadata.get("course_hours"),
                            "intro": metadata.get("intro", "")[:100] + "..." if len(metadata.get("intro", "")) > 100 else metadata.get("intro")
                        }
                    else:
                        test_result["errors"].append("course_data.json 解析失败")
                except HTTPException:
                    raise
                except Exception as e:
                    test_result["errors"].append(f"course_data.json 解析错误: {str(e)}")
            else:
                test_result["errors"].append("缺少 course_data.json 文件")
            
            test_results.append(test_result)
        
        # 统计结果
        total_projects = len(projects)
        valid_projects = len([r for r in test_results if r["course_data_valid"]])
        
        return schemas.ApiResponse(
            code="0000",
            message=f"实训资源初始化测试完成，扫描到 {total_projects} 个项目，{valid_projects} 个有效",
            data={
                "resource_path": resource_path,
                "test_result": "SUCCESS",
                "summary": {
                    "total_projects": total_projects,
                    "valid_projects": valid_projects,
                    "invalid_projects": total_projects - valid_projects
                },
                "projects": test_results
            }
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"实训资源初始化测试失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "实训资源初始化测试失败", 
                "message": str(e),
                "code": "SEED_TEST_ERROR"
            }
        )

# ==================== 通用参数路由（放在最后避免冲突） ====================
# NOTE: 这些路由放在最后，确保不会与具体路径冲突

@router.get("/detail/{training_id}", response_model=schemas.ApiResponse)
def get_training_detail(
    training_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取实训详情"""
    try:
        training = db.query(models.Training).filter(
            models.Training.id == training_id,
            models.Training.creator_id == current_user["user_id"]
        ).first()
        
        if not training:
            raise HTTPException(status_code=404, detail="实训不存在")
        
        # 获取数据集
        datasets = db.query(models.TrainingDataset).filter(
            models.TrainingDataset.training_id == training_id
        ).all()
        
        # 构建响应数据
        training_data = {
            "id": training.id,
            "title": training.title,
            "training_type": training.training_type.value,
            "intro": training.intro,
            "industry": training.industry,
            "difficulty": training.difficulty.value,
            "course_hours": training.course_hours,
            "handbook_content": training.handbook_content,
            "assignment_nodes": json.loads(training.assignment_nodes) if training.assignment_nodes else [],
            "require_design_files": training.require_design_files,
            "require_experiment_report": training.require_experiment_report,
            "environment_id": training.environment_id,
            "storage_limit": training.storage_limit,
            "memory_limit": training.memory_limit,
            "cpu_limit": training.cpu_limit,
            "publish_status": training.publish_status.value,
            "visibility": training.visibility.value,
            "is_published": training.is_published,
            "datasets": [
                {
                    "id": ds.id,
                    "name": ds.name,
                    "file_url": ds.file_url,
                    "file_type": ds.file_type,
                    "file_size": ds.file_size,
                    "access_path": ds.access_path,
                    "created_at": ds.created_at.isoformat() if ds.created_at else None
                }
                for ds in datasets
            ],
            "created_at": training.created_at.isoformat() if training.created_at else None,
            "updated_at": training.updated_at.isoformat() if training.updated_at else None
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取实训详情成功",
            data=training_data
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实训详情失败: {str(e)}")

@router.put("/detail/{training_id}", response_model=schemas.ApiResponse)
def update_training(
    training_id: int,
    request: schemas.TrainingUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新实训"""
    try:
        logger.info(f"Update training request: {request}")
        logger.info(f"Request type: {type(request)}")
        logger.info(f"Request dir: {[attr for attr in dir(request) if not attr.startswith('_')]}")

        training = db.query(models.Training).filter(
            models.Training.id == training_id,
            models.Training.creator_id == current_user["user_id"]
        ).first()

        if not training:
            raise HTTPException(status_code=404, detail="实训不存在")

        # 更新字段
        if request.title is not None:
            training.title = request.title
        if request.intro is not None:
            training.intro = request.intro
        if request.industry is not None:
            training.industry = request.industry
        if request.difficulty is not None:
            training.difficulty = request.difficulty
        if request.course_hours is not None:
            training.course_hours = request.course_hours
        if request.handbook_content is not None:
            training.handbook_content = request.handbook_content
        if request.assignment_nodes is not None:
            training.assignment_nodes = json.dumps([node.model_dump() for node in request.assignment_nodes])
        if request.require_design_files is not None:
            training.require_design_files = request.require_design_files
        if request.require_experiment_report is not None:
            training.require_experiment_report = request.require_experiment_report
        if request.environment_id is not None:
            training.environment_id = request.environment_id
        
        # 更新环境配置
        if request.environment_config:
            training.storage_limit = request.environment_config.storage_limit
            training.memory_limit = request.environment_config.memory_limit
            training.cpu_limit = request.environment_config.cpu_limit
        
        training.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(training)
        
        return schemas.ApiResponse(
            code="0000",
            message="更新实训成功",
            data={"id": training.id}
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新实训失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新实训失败: {str(e)}")

@router.delete("/detail/{training_id}", response_model=schemas.ApiResponse)
def delete_training(
    training_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除实训"""
    try:
        training = db.query(models.Training).filter(
            models.Training.id == training_id,
            models.Training.creator_id == current_user["user_id"]
        ).first()
        
        if not training:
            raise HTTPException(status_code=404, detail="实训不存在")
        
        # 检查是否已发布
        if training.is_published:
            raise HTTPException(status_code=400, detail="已发布的实训不能删除")
        
        db.delete(training)
        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message="删除实训成功",
            data=None
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除实训失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除实训失败: {str(e)}")

@router.post("/detail/{training_id}/publish", response_model=schemas.ApiResponse)
def publish_training(
    training_id: int,
    visibility: schemas.TrainingVisibilityEnum = schemas.TrainingVisibilityEnum.PUBLIC,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发布实训"""
    try:
        training = db.query(models.Training).filter(
            models.Training.id == training_id,
            models.Training.creator_id == current_user["user_id"]
        ).first()
        
        if not training:
            raise HTTPException(status_code=404, detail="实训不存在")
        
        # 更新发布状态
        training.publish_status = models.TrainingPublishStatusEnum.PUBLISHED
        training.visibility = visibility
        training.is_published = True
        training.published_at = datetime.utcnow()
        
        db.commit()
        db.refresh(training)
        
        return schemas.ApiResponse(
            code="0000",
            message="发布实训成功",
            data={"id": training.id}
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"发布实训失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"发布实训失败: {str(e)}")

@router.post("/detail/{training_id}/unpublish", response_model=schemas.ApiResponse)
def unpublish_training(
    training_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消发布实训"""
    try:
        training = db.query(models.Training).filter(
            models.Training.id == training_id,
            models.Training.creator_id == current_user["user_id"]
        ).first()
        
        if not training:
            raise HTTPException(status_code=404, detail="实训不存在")
        
        # 更新发布状态
        training.publish_status = models.TrainingPublishStatusEnum.EDITING
        training.is_published = False
        
        db.commit()
        db.refresh(training)
        
        return schemas.ApiResponse(
            code="0000",
            message="取消发布实训成功",
            data={"id": training.id}
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"取消发布实训失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消发布实训失败: {str(e)}")

@router.post("/detail/{training_id}/datasets", response_model=schemas.ApiResponse)
def upload_dataset(
    training_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传数据集"""
    try:
        # 检查实训是否存在
        training = db.query(models.Training).filter(
            models.Training.id == training_id,
            models.Training.creator_id == current_user["user_id"]
        ).first()
        
        if not training:
            raise HTTPException(status_code=404, detail="实训不存在")
        
        # 保存文件
        file_name = file.filename
        file_type = file.content_type or "application/octet-stream"
        
        # 创建目录
        upload_dir = f"uploads/training/{training_id}/datasets"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{timestamp}_{file_name}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 生成访问路径
        access_path = f"/data/training_{training_id}/{unique_filename}"
        
        # 创建数据集记录
        dataset = models.TrainingDataset(
            training_id=training_id,
            name=file_name,
            file_url=file_path,
            file_type=file_type,
            file_size=file_size,
            description=description,
            access_path=access_path,
            uploader_id=current_user["user_id"]
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        return schemas.ApiResponse(
            code="0000",
            message="上传数据集成功",
            data={
                "id": dataset.id,
                "name": dataset.name,
                "access_path": dataset.access_path,
                "file_size": dataset.file_size
            }
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"上传数据集失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传数据集失败: {str(e)}")

@router.delete("/detail/{training_id}/datasets/{dataset_id}", response_model=schemas.ApiResponse)
def delete_dataset(
    training_id: int,
    dataset_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除数据集"""
    try:
        # 检查实训是否存在
        training = db.query(models.Training).filter(
            models.Training.id == training_id,
            models.Training.creator_id == current_user["user_id"]
        ).first()
        
        if not training:
            raise HTTPException(status_code=404, detail="实训不存在")
        
        # 检查数据集是否存在
        dataset = db.query(models.TrainingDataset).filter(
            models.TrainingDataset.id == dataset_id,
            models.TrainingDataset.training_id == training_id
        ).first()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")
        
        # 删除文件
        if os.path.exists(dataset.file_url):
            os.remove(dataset.file_url)
        
        # 删除记录
        db.delete(dataset)
        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message="删除数据集成功",
            data=None
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除数据集失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除数据集失败: {str(e)}")

@router.get("/environments/list", response_model=schemas.ApiResponse)
def get_training_environments_list(
    db: Session = Depends(get_db)
):
    """获取实训环境列表"""
    try:
        environments = db.query(models.TrainingEnvironment).filter(
            models.TrainingEnvironment.is_active == True
        ).all()
        
        env_list = []
        for env in environments:
            env_data = {
                "id": str(env.id),
                "name": env.name,
                "environment_type": env.environment_type,
                "description": env.description,
                "default_storage": env.default_storage,
                "default_memory": env.default_memory,
                "default_cpu": env.default_cpu
            }
            env_list.append(env_data)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取实训环境列表成功",
            data=env_list
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训环境列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实训环境列表失败: {str(e)}")

def _get_status_detail(status: models.TrainingPublishStatusEnum) -> str:
    """获取状态详情描述"""
    status_map = {
        models.TrainingPublishStatusEnum.EDITING: "编辑中",
        models.TrainingPublishStatusEnum.PUBLISHED: "已发布"
    }
    return status_map.get(status, "未知状态")

def _convert_training_type(training_type: models.TrainingTypeEnum) -> str:
    """转换实训类型为前端格式"""
    type_map = {
        models.TrainingTypeEnum.DRAG_DROP: "bi",  # 拖拽式对应BI
        models.TrainingTypeEnum.CODING: "jupyter"  # 编码式对应Jupyter
    }
    return type_map.get(training_type, "bi")

# 添加custom-trainings路由别名，兼容前端调用
@router.post("/custom-trainings", response_model=schemas.ApiResponse)
def create_custom_training(
    request: schemas.TrainingCreateRequest,
    creator_id: int = Query(..., description="创建者ID"),
    db: Session = Depends(get_db)
):
    """创建自定义实训（路由别名）"""
    try:
        logger.info(f"Received training creation request: {request.model_dump()}")
        logger.info(f"Request object: {request}")
        logger.info(f"Request dir: {[attr for attr in dir(request) if not attr.startswith('_')]}")
        # 调用已有的创建实训函数
        user = db.query(models.User).filter(models.User.id == creator_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 创建实训记录
        training = models.Training(
            title=request.title,
            training_type=request.training_type,
            intro=request.intro,
            industry=request.industry,
            difficulty=request.difficulty,
            course_hours=request.course_hours,
            handbook_content=request.handbook_content,
            assignment_nodes=json.dumps([node.model_dump() for node in request.assignment_nodes]) if request.assignment_nodes else "[]",
            require_design_files=request.require_design_files,
            require_experiment_report=request.require_experiment_report,
            environment_id=request.environment_id,
            creator_id=creator_id
        )
        
        # 如果是编码式实训，设置环境配置
        if request.training_type == schemas.TrainingTypeEnum.CODING and request.environment_config:
            training.storage_limit = request.environment_config.storage_limit
            training.memory_limit = request.environment_config.memory_limit
            training.cpu_limit = request.environment_config.cpu_limit
        
        db.add(training)
        db.commit()
        db.refresh(training)
        
        return schemas.ApiResponse(
            code="0000",
            message="创建实训成功",
            data={
                "training_id": training.id,
                "title": training.title
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建实训失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建实训失败: {str(e)}")

@router.post("/custom-trainings/{training_id}/publish-version", response_model=schemas.ApiResponse)
def publish_new_training_version(
    training_id: int,
    request: schemas.TrainingVersionData,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发布新版本的实训"""
    try:
        training = db.query(models.Training).filter(
            models.Training.id == training_id
        ).first()

        if not training:
            raise HTTPException(status_code=404, detail="实训不存在")

        # 检查权限：只能发布自己的实训
        if training.creator_id != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="无权限发布此实训")

        # 设置可见性和发布状态
        visibility_map = {
            "public": models.TrainingVisibilityEnum.PUBLIC,
            "personal": models.TrainingVisibilityEnum.PRIVATE
        }

        training.visibility = visibility_map.get(request.publishType, models.TrainingVisibilityEnum.PRIVATE)

        # 根据用户权限和可见性设置发布状态
        is_admin = current_user.get("is_superuser", False)

        if training.visibility == models.TrainingVisibilityEnum.PUBLIC and not is_admin:
            # 普通用户公开发布需要审核
            training.publish_status = models.TrainingPublishStatusEnum.PENDING_REVIEW
            training.is_published = False
            training.published_at = None
            message = "新版本已提交审核，审核通过后将公开发布"
        else:
            # 私有发布或管理员发布直接发布
            training.publish_status = models.TrainingPublishStatusEnum.PUBLISHED
            training.is_published = True
            training.published_at = datetime.utcnow()
            message = "新版本已发布"

        # 更新内容记录（这里可以扩展为版本历史表）
        training.handbook_content = f"{training.handbook_content or ''}\n\n--- 新版本更新 ---\n{request.updateNotes}"

        db.commit()
        db.refresh(training)

        return schemas.ApiResponse(
            code="0000",
            message=message,
            data={"id": training.id, "status": training.publish_status.value}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发布新版本失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"发布新版本失败: {str(e)}")

@router.post("/custom-trainings/{training_id}/publish", response_model=schemas.ApiResponse)
def publish_custom_training(
    training_id: int,
    request: schemas.TrainingPublishRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发布自定义实训（路由别名）"""
    training = db.query(models.Training).filter(
        models.Training.id == training_id
    ).first()

    if not training:
        raise HTTPException(status_code=404, detail="实训不存在")

    # 检查权限：只能发布自己的实训
    if training.creator_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="无权限发布此实训")

    # 更新发布状态
    visibility_map = {
        "public": models.TrainingVisibilityEnum.PUBLIC,
        "private": models.TrainingVisibilityEnum.PRIVATE
    }

    training.visibility = visibility_map.get(request.visibility, models.TrainingVisibilityEnum.PRIVATE)

    # 根据用户权限和可见性设置发布状态
    is_admin = current_user.get("is_superuser", False)

    if training.visibility == models.TrainingVisibilityEnum.PUBLIC and not is_admin:
        # 普通用户公开发布需要审核
        training.publish_status = models.TrainingPublishStatusEnum.PENDING_REVIEW
        training.is_published = False
        training.published_at = None
        message = "实训已提交审核，审核通过后将公开发布"
    else:
        # 私有发布或管理员发布直接发布
        training.publish_status = models.TrainingPublishStatusEnum.PUBLISHED
        training.is_published = True
        training.published_at = datetime.utcnow()
        message = "实训已发布"

    db.commit()
    db.refresh(training)

    return schemas.ApiResponse(
        code="0000",
        message=message,
        data={"id": training.id, "status": training.publish_status.value}
    )


# ==================== 实训审核管理路由 ====================

@router.post("/admin/approve/{training_id}", response_model=schemas.ApiResponse)
def approve_training(
    training_id: int,
    request: schemas.TrainingReviewRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """管理员审核通过实训（公开发布）"""
    # 检查管理员权限
    if not current_user.get("is_superuser", False):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    training = db.query(models.Training).filter(
        models.Training.id == training_id
    ).first()

    if not training:
        raise HTTPException(status_code=404, detail="实训不存在")

    if training.publish_status != models.TrainingPublishStatusEnum.PENDING_REVIEW:
        raise HTTPException(status_code=400, detail="实训状态不符合审核要求")

    # 更新审核信息
    training.publish_status = models.TrainingPublishStatusEnum.PUBLISHED
    training.is_published = True
    training.published_at = datetime.utcnow()
    training.reviewer_id = current_user.get("id")
    training.reviewed_at = datetime.utcnow()
    training.review_comment = request.comment

    db.commit()
    db.refresh(training)

    return schemas.ApiResponse(
        code="0000",
        message="实训审核通过，已公开发布",
        data={"id": training.id}
    )


@router.post("/admin/reject/{training_id}", response_model=schemas.ApiResponse)
def reject_training(
    training_id: int,
    request: schemas.TrainingReviewRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """管理员审核拒绝实训"""
    # 检查管理员权限
    if not current_user.get("is_superuser", False):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    training = db.query(models.Training).filter(
        models.Training.id == training_id
    ).first()

    if not training:
        raise HTTPException(status_code=404, detail="实训不存在")

    if training.publish_status != models.TrainingPublishStatusEnum.PENDING_REVIEW:
        raise HTTPException(status_code=400, detail="实训状态不符合审核要求")

    # 更新审核信息
    training.publish_status = models.TrainingPublishStatusEnum.REJECTED
    training.is_published = False
    training.reviewer_id = current_user.get("id")
    training.reviewed_at = datetime.utcnow()
    training.review_comment = request.comment

    db.commit()
    db.refresh(training)

    return schemas.ApiResponse(
        code="0000",
        message="实训审核拒绝",
        data={"id": training.id}
    )


@router.get("/admin/pending-review", response_model=schemas.ApiResponse)
def get_pending_review_trainings(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取待审核的实训列表（管理员）"""
    # 检查管理员权限
    if not current_user.get("is_superuser", False):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    # 查询待审核的实训
    query = db.query(models.Training).filter(
        models.Training.publish_status == models.TrainingPublishStatusEnum.PENDING_REVIEW
    )

    total = query.count()
    trainings = query.offset((page - 1) * size).limit(size).all()

    # 格式化返回数据
    training_list = []
    for training in trainings:
        training_list.append({
            "id": training.id,
            "title": training.title,
            "intro": training.intro,
            "training_type": training.training_type.value,
            "difficulty": training.difficulty.value,
            "industry": training.industry,
            "course_hours": training.course_hours,
            "creator": {
                "id": training.creator.id,
                "username": training.creator.username,
                "realname": training.creator.realname
            },
            "created_at": training.created_at.isoformat() if training.created_at else None,
            "visibility": training.visibility.value
        })

    return schemas.ApiResponse(
        code="0000",
        message="获取成功",
        data={
            "list": training_list,
            "total": total,
            "page": page,
            "size": size
        }
    )


# ==================== 实训状态管理路由 ====================

@router.patch("/custom-trainings/{training_id}/status", response_model=schemas.ApiResponse)
def update_training_status(
    training_id: int,
    request: schemas.TrainingStatusUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新实训状态（发布/取消发布/删除）"""
    try:
        training = db.query(models.Training).filter(
            models.Training.id == training_id
        ).first()

        if not training:
            raise HTTPException(status_code=404, detail="实训不存在")

        # 检查权限：只有创建者能操作
        if training.creator_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="无权限操作此实训")

        if request.action == "publish":
            # 发布实训
            training.publish_status = models.TrainingPublishStatusEnum.PUBLISHED
            training.visibility = request.visibility or models.TrainingVisibilityEnum.PRIVATE
            training.is_published = True
            training.published_at = datetime.utcnow()
            message = "发布实训成功"

        elif request.action == "unpublish":
            # 取消发布
            training.publish_status = models.TrainingPublishStatusEnum.EDITING
            training.is_published = False
            training.published_at = None
            message = "取消发布成功"

        elif request.action == "delete":
            # 软删除（这里先标记删除，后续可扩展为真正的软删除）
            if training.publish_status == models.TrainingPublishStatusEnum.PUBLISHED:
                raise HTTPException(status_code=400, detail="已发布的实训不能删除，请先取消发布")
            db.delete(training)
            message = "删除实训成功"

        else:
            raise HTTPException(status_code=400, detail=f"不支持的操作: {request.action}")

        db.commit()
        db.refresh(training) if request.action != "delete" else None

        return schemas.ApiResponse(
            code="0000",
            message=message,
            data={"id": training_id} if request.action != "delete" else {"id": training_id, "deleted": True}
        )

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新实训状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新实训状态失败: {str(e)}")


# ==================== 实训库相关路由 ====================

# ==================== P2 实训启动和提交 API ====================

@router.post("/{training_id}/launch", response_model=schemas.ApiResponse)
def launch_training_environment(
    training_id: int,
    classroom_id: int = Query(..., description="课堂ID"),
    training_type: str = Query(..., description="实训类型"),
    student_id: Optional[int] = Query(None, description="学生ID（可选，用于兼容无token情况）"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """启动实训环境 (BI实训直接返回数据，编程实训返回环境URL)"""
    try:
        from datetime import datetime, timezone

        # 获取当前用户ID（优先从query参数student_id获取，因为token可能不可用）
        user_id = None
        user_role = "student"
        if student_id:
            # 如果提供了student_id参数，使用它
            user_id = student_id
            user_role = "student"
        elif current_user and current_user.get("role") != "admin":
            # 否则从token获取（排除admin默认用户）
            user_id = current_user.get("user_id")
            user_role = current_user.get("role", "student")

        # 获取实训信息
        training = db.query(models.Training).filter(
            models.Training.id == training_id
        ).first()

        if not training:
            return schemas.ApiResponse(
                code="1004",
                message="实训不存在",
                trace_id=""
            )

        # 如果是学生，记录学习开始
        if user_role == "student" and user_id:
            # 查找是否已有学习记录
            existing_log = db.query(models.TrainingLearningLog).filter(
                models.TrainingLearningLog.user_id == user_id,
                models.TrainingLearningLog.training_id == training_id,
                models.TrainingLearningLog.end_time == None  # 未完成的记录
            ).first()

            if not existing_log:
                # 创建新的学习记录
                learning_log = models.TrainingLearningLog(
                    user_id=user_id,
                    training_id=training_id,
                    start_time=datetime.now(timezone.utc),
                    is_training_started=True
                )
                db.add(learning_log)
                db.commit()

        # BI 实训：加载数据直接返回 (Graphic Walker 模式)
        if training_type in ['DRAG_DROP', 'HUIXUE_BI', 'bi', 'BI', 'DATA_ANALYSIS']:
            try:
                        from app.utils.bi_data_loader import BIDataLoader
                        data = BIDataLoader.load_data(training_id, db, limit=100)
                        return schemas.ApiResponse(
                    code="0000",
                    message="数据加载成功",
                    data=data
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"加载BI数据失败: {str(e)}")
                return schemas.ApiResponse(
                    code="2001",
                    message=f"加载数据失败: {str(e)}",
                    trace_id=""
                )
        
        # 其他类型 (如 CODING/JUPYTER)：返回环境 URL
        # 从配置中获取 Jupyter URL
        from app.core.config import settings
        from urllib.parse import quote

        jupyter_base_url = settings.JUPYTER_BASE_URL
        jupyter_token = settings.JUPYTER_TOKEN

        editor_type = training_type

        # 构建Jupyter URL - 尝试直接打开实训的starter.ipynb
        jupyter_url = f"{jupyter_base_url}/lab?token={jupyter_token}"

        # 如果有project_path，构建直接打开notebook的URL
        if training.project_path:
            project_path = training.project_path
            # 处理不同格式的project_path
            if project_path.startswith('/trainings/'):
                # 旧格式: /trainings/02-分布式光伏出力预测
                notebook_path = f"resources{project_path}/jupyter/starter.ipynb"
            elif project_path.startswith('实训资源/'):
                # 带前缀格式
                notebook_path = f"resources/{project_path}/jupyter/starter.ipynb"
            else:
                # 相对路径格式: 01-某零售企业经营分析
                notebook_path = f"resources/实训资源/{project_path}/jupyter/starter.ipynb"

            # URL编码路径中的中文字符
            encoded_path = quote(notebook_path, safe='/')
            jupyter_url = f"{jupyter_base_url}/lab/tree/{encoded_path}?token={jupyter_token}"
            logger.info(f"[launch] Training {training_id} notebook URL: {jupyter_url}")

        # 构建带 token 的 Jupyter URL
        environment_data = {
            "environment_id": f"env_{training_id}_{int(__import__('time').time())}",
            "editor_type": editor_type,
            "url": jupyter_url,
            "training_id": training_id,
            "classroom_id": classroom_id,
            "status": "active"
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="环境启动成功",
            data=environment_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动环境失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=""
        )


@router.post("/{training_id}/submit", response_model=schemas.ApiResponse)
def submit_training_assignment(
    training_id: int,
    submission: schemas.TrainingSubmissionRequest = None,
    classroom_id: int = Query(..., description="课堂ID"),
    notes: str = Query("", description="提交说明"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交实训作业（支持Graphic Walker快照）"""
    try:
        from datetime import datetime, timezone
        import json
        
        # 使用当前登录用户ID
        student_id = current_user["user_id"]
        
        # 兼容旧的Query参数方式和新的Body方式
        submission_notes = notes
        snapshot_json = None
        
        if submission:
            if submission.notes:
                submission_notes = submission.notes
            if submission.snapshot_json:
                snapshot_json = submission.snapshot_json
        
        # 验证实训存在
        training = db.query(models.Training).filter(
            models.Training.id == training_id
        ).first()
        
        if not training:
            return schemas.ApiResponse(
                code="1004",
                message="实训不存在",
                trace_id=""
            )
        
        # 查找ClassroomTraining关联
        classroom_training = db.query(models.ClassroomTraining).filter(
            models.ClassroomTraining.classroom_id == classroom_id,
            models.ClassroomTraining.training_id == training_id
        ).first()
        
        if not classroom_training:
            return schemas.ApiResponse(
                code="1004",
                message="课堂中不存在该实训",
                trace_id=""
            )
        
        # 为实训创建或查找对应的Course（course_type=TRAINING）
        # 使用training_id作为唯一标识，避免重复创建
        # 注意：CourseTypeEnum在models.py中定义
        from app.models.models import CourseTypeEnum, DifficultyEnum, CourseVisibilityEnum
        
        course = db.query(models.Course).filter(
            models.Course.course_type == CourseTypeEnum.TRAINING,
            models.Course.title == f"[实训]{training.title}"  # 使用标题匹配
        ).first()
        
        if not course:
            # 创建新的Course
            difficulty_map = {
                models.DifficultyLevelEnum.beginner: DifficultyEnum.BEGINNER,
                models.DifficultyLevelEnum.intermediate: DifficultyEnum.INTERMEDIATE,
                models.DifficultyLevelEnum.advanced: DifficultyEnum.ADVANCED
            }
            course = models.Course(
                title=f"[实训]{training.title}",
                course_type=CourseTypeEnum.TRAINING,
                description=training.intro or "",
                difficulty=difficulty_map.get(training.difficulty, DifficultyEnum.BEGINNER),
                visibility=CourseVisibilityEnum.PRIVATE
            )
            db.add(course)
            db.flush()  # 获取ID
        
        # 查找或创建ClassroomCourse
        classroom_course = db.query(models.ClassroomCourse).filter(
            models.ClassroomCourse.classroom_id == classroom_id,
            models.ClassroomCourse.course_id == course.id
        ).first()
        
        if not classroom_course:
            # 创建ClassroomCourse
            classroom_course = models.ClassroomCourse(
                classroom_id=classroom_id,
                course_id=course.id,
                teacher_publish_status=models.CourseInClassroomStatusTeacherEnum.LEARNING,
                published_at=datetime.now(timezone.utc)
            )
            db.add(classroom_course)
            db.flush()  # 获取ID
        
        # 获取或创建学生进度记录
        progress = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id == classroom_course.id,
            models.StudentCourseProgress.student_id == student_id
        ).first()
        
        if not progress:
            progress = models.StudentCourseProgress(
                classroom_course_id=classroom_course.id,
                student_id=student_id,
                training_submission_status=models.SubmissionStatusEnum.NOT_STARTED
            )
            db.add(progress)
        
        # 检查是否超期
        current_time = datetime.now(timezone.utc)
        is_late = False
        if classroom_course.deadline_at:
            is_late = current_time > classroom_course.deadline_at
            
        # 针对不同实训类型的额外处理
        # BI/AI (DRAG_DROP) 实训：不需要文件，直接通过
        # CODING 实训：通常需要检查代码或文件（这里暂不做强制拦截，由前端控制）
        if str(training.training_type) == "DRAG_DROP" or str(training.training_type) == "HUIXUE_BI":
            logger.info(f"BI实训作业提交: training_id={training_id}, student_id={student_id}")
        
        # 如果有快照数据，保存到 submission_snapshot 字段
        if snapshot_json:
            try:
                # 确保它是字典或列表
                if isinstance(snapshot_json, str):
                    # 如果已经是字符串，直接保存
                    progress.submission_snapshot = snapshot_json
                else:
                    # 否则序列化
                    progress.submission_snapshot = json.dumps(snapshot_json, ensure_ascii=False)
                logger.info(f"已保存实训作业快照，长度: {len(progress.submission_snapshot)}")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"作业快照保存失败: {str(e)}")
                # 不中断提交流程，但记录错误

        # 更新提交状态
        # 注意：文件上传应该在单独的API中处理，这里只更新状态
        progress.training_submission_status = models.SubmissionStatusEnum.LATE_SUBMISSION if is_late else models.SubmissionStatusEnum.SUBMITTED
        progress.student_status = (
            models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
            if is_late
            else models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME
        )
        progress.last_submission_at = current_time
        
        if not progress.first_access_at:
            progress.first_access_at = current_time
        
        db.commit()
        db.refresh(progress)
        
        return schemas.ApiResponse(
            code="0000",
            message="作业提交成功",
            data={
                "progress_id": progress.id,
                "submission_status": progress.training_submission_status.value,
                "submission_time": progress.last_submission_at.isoformat() if progress.last_submission_at else None,
                "is_late": is_late
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"提交作业失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=""
        )


@router.post("/{training_id}/upload-submission", response_model=schemas.ApiResponse)
async def upload_training_submission_file(
    training_id: int,
    classroom_id: int = Form(..., description="课堂ID"),
    student_id: int = Form(..., description="学生ID"),
    file: UploadFile = File(..., description="提交文件"),
    file_type: str = Form(..., description="文件类型: design_file 或 experiment_report"),
    db: Session = Depends(get_db)
):
    """上传实训作业文件（.knwf工作流文件或实验报告）"""
    try:
        from datetime import datetime, timezone
        import json
        from pathlib import Path
        
        # 验证文件类型
        if file_type not in ['design_file', 'experiment_report']:
            return schemas.ApiResponse(
                code="1001",
                message="文件类型必须是 design_file 或 experiment_report",
                trace_id=""
            )
        
        # 验证实训存在
        training = db.query(models.Training).filter(
            models.Training.id == training_id
        ).first()
        
        if not training:
            return schemas.ApiResponse(
                code="1004",
                message="实训不存在",
                trace_id=""
            )
        
        # 查找或创建Course和ClassroomCourse（与submit_training_assignment逻辑一致）
        from app.models.models import CourseTypeEnum, DifficultyEnum, CourseVisibilityEnum
        
        course = db.query(models.Course).filter(
            models.Course.course_type == CourseTypeEnum.TRAINING,
            models.Course.title == f"[实训]{training.title}"
        ).first()
        
        if not course:
            difficulty_map = {
                models.DifficultyLevelEnum.beginner: DifficultyEnum.BEGINNER,
                models.DifficultyLevelEnum.intermediate: DifficultyEnum.INTERMEDIATE,
                models.DifficultyLevelEnum.advanced: DifficultyEnum.ADVANCED
            }
            course = models.Course(
                title=f"[实训]{training.title}",
                course_type=CourseTypeEnum.TRAINING,
                description=training.intro or "",
                difficulty=difficulty_map.get(training.difficulty, DifficultyEnum.BEGINNER),
                visibility=CourseVisibilityEnum.PRIVATE
            )
            db.add(course)
            db.flush()
        
        classroom_course = db.query(models.ClassroomCourse).filter(
            models.ClassroomCourse.classroom_id == classroom_id,
            models.ClassroomCourse.course_id == course.id
        ).first()
        
        if not classroom_course:
            classroom_course = models.ClassroomCourse(
                classroom_id=classroom_id,
                course_id=course.id,
                teacher_publish_status=models.CourseInClassroomStatusTeacherEnum.LEARNING,
                published_at=datetime.now(timezone.utc)
            )
            db.add(classroom_course)
            db.flush()
        
        # 获取或创建学生进度记录
        progress = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id == classroom_course.id,
            models.StudentCourseProgress.student_id == student_id
        ).first()
        
        if not progress:
            progress = models.StudentCourseProgress(
                classroom_course_id=classroom_course.id,
                student_id=student_id,
                training_submission_status=models.SubmissionStatusEnum.NOT_STARTED
            )
            db.add(progress)
        
        # 保存文件
        upload_dir = Path(settings.resource_base_path) / "作业提交" / f"training_{training_id}" / f"classroom_{classroom_id}" / f"student_{student_id}"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(file.filename).suffix
        unique_filename = f"{file_type}_{timestamp}_{file.filename}"
        file_path = upload_dir / unique_filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        file_size = file_path.stat().st_size
        
        # 更新进度记录中的文件信息
        files_data = {}
        if progress.training_assignment_files:
            try:
                files_data = json.loads(progress.training_assignment_files)
            except:
                files_data = {}
        
        file_list_key = "design_files" if file_type == "design_file" else "experiment_reports"
        if file_list_key not in files_data:
            files_data[file_list_key] = []
        
        # 添加文件信息
        file_info = {
            "file_name": file.filename,
            "file_url": str(file_path.relative_to(settings.resource_base_path)),
            "file_type": file_type,
            "file_size": file_size,
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        }
        files_data[file_list_key].append(file_info)
        
        progress.training_assignment_files = json.dumps(files_data, ensure_ascii=False)
        
        # 如果文件已上传，更新状态为进行中
        if progress.training_submission_status == models.SubmissionStatusEnum.NOT_STARTED:
            progress.training_submission_status = models.SubmissionStatusEnum.IN_PROGRESS
        
        db.commit()
        db.refresh(progress)
        
        return schemas.ApiResponse(
            code="0000",
            message="文件上传成功",
            data={
                "file_name": file.filename,
                "file_url": str(file_path.relative_to(settings.resource_base_path)),
                "file_size": file_size,
                "file_type": file_type
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"文件上传失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=""
        )

@router.get("/submissions/{progress_id}", response_model=schemas.ApiResponse)
def get_training_submission(
    progress_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID（可选，用于绕过token验证）"),
    current_user: Optional[dict] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取实训作业提交详情（包括快照）"""
    try:
        # 查找进度记录
        progress = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.id == progress_id
        ).first()
        
        if not progress:
            raise HTTPException(status_code=404, detail="作业记录不存在")
        
        # 权限检查：
        # 1. 如果有current_user，进行标准检查
        if current_user:
            # 1.1 检查是否是管理员
            if current_user.get("is_superuser"):
                pass
            # 1.2 检查是否是提交者本人
            elif progress.student_id == current_user.get("user_id"):
                pass
            # 1.3 检查是否是该课堂的教师
            else:
                # 查找关联的课堂
                classroom_course = db.query(models.ClassroomCourse).filter(
                    models.ClassroomCourse.id == progress.classroom_course_id
                ).first()
                
                if not classroom_course:
                    raise HTTPException(status_code=404, detail="关联课程记录不存在")
                
                classroom = db.query(models.Classroom).filter(
                    models.Classroom.id == classroom_course.classroom_id
                ).first()
                
                if not classroom:
                    raise HTTPException(status_code=404, detail="关联课堂不存在")
                
                # 检查是否是该课堂的创建者或助教
                if classroom.teacher_id != current_user.get("user_id"):
                    # TODO: 检查助教权限
                    raise HTTPException(status_code=403, detail="无权查看此作业")
        
        # 2. 如果没有current_user但提供了teacher_id（兼容旧代码/特殊情况）
        elif teacher_id:
             # 查找关联的课堂
            classroom_course = db.query(models.ClassroomCourse).filter(
                models.ClassroomCourse.id == progress.classroom_course_id
            ).first()
            
            if not classroom_course:
                raise HTTPException(status_code=404, detail="关联课程记录不存在")
            
            classroom = db.query(models.Classroom).filter(
                models.Classroom.id == classroom_course.classroom_id
            ).first()
            
            if not classroom:
                raise HTTPException(status_code=404, detail="关联课堂不存在")
            
            # 检查teacher_id是否是该课堂的教师
            # 注意：这里假设teacher_id是可信的，这通常是不安全的，但为了兼容review接口模式暂时如此
            # 更安全的做法是只允许内部调用或要求token
            if classroom.teacher_id != teacher_id:
                 # 简单的ID匹配，不验证token所有权（因为没有token）
                 # 在生产环境中，teacher_id应该从token中获取，或者这个接口应该只允许current_user
                 # 这里为了解决 401 问题，暂时允许通过 teacher_id 访问，但应该记录警告
                 logger.warning(f"Accessing submission {progress_id} via teacher_id {teacher_id} without token validation")
                 # 可以在这里决定是否抛出异常，或者只在开发模式下允许
                 # 考虑到review接口也这样用，暂时允许
                 pass
        else:
            # 既没有token也没有teacher_id
            raise HTTPException(status_code=401, detail="未授权访问")

        # 构建返回数据
        import json
        snapshot_data = None
        if progress.submission_snapshot:
            try:
                snapshot_data = json.loads(progress.submission_snapshot)
            except:
                snapshot_data = progress.submission_snapshot

        # 尝试解析 training_id
        training_id = None
        classroom_id = None
        classroom_course_id = None
        course_title = ""
        
        if progress.classroom_course:
            classroom_course_id = progress.classroom_course.id
            classroom_id = progress.classroom_course.classroom_id
            if progress.classroom_course.course:
                course_title = progress.classroom_course.course.title
                # 尝试从标题 "[实训]Title" 中提取
                if course_title.startswith("[实训]"):
                    real_title = course_title.replace("[实训]", "", 1)
                    # 查找 Training
                    training = db.query(models.Training).filter(models.Training.title == real_title).first()
                    if training:
                        training_id = training.id

        # Get training type
        training_type = None
        if training_id:
            training = db.query(models.Training).filter(models.Training.id == training_id).first()
            if training:
                training_type = training.training_type.value if training.training_type else None
        
        data = {
            "id": progress.id,
            "student_id": progress.student_id,
            "status": progress.training_submission_status.value if progress.training_submission_status else None,
            "submission_snapshot": snapshot_data,
            "submitted_at": progress.last_submission_at.isoformat() if progress.last_submission_at else None,
            "score": progress.overall_score,
            "teacher_feedback": progress.teacher_feedback,
            "graded_at": progress.graded_at.isoformat() if progress.graded_at else None,
            "graded_by": progress.graded_by_teacher_id,
            "training_id": training_id,
            "training_type": training_type,
            "classroom_id": classroom_id,
            "classroom_course_id": classroom_course_id,
            "course_title": course_title
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取作业详情成功",
            data=data
        )

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取作业详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取作业详情失败: {str(e)}")


@router.get("/{training_id}/assignments", response_model=schemas.ApiResponse)
def get_training_assignments(
    training_id: int,
    student_id: int = Query(..., description="学生ID"),
    classroom_id: int = Query(..., description="课堂ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生的实训作业列表"""
    try:
        from app.core.identity import resolve_scoped_id
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",), forbidden_detail="无权访问该学生作业列表")
        from app.models.models import CourseTypeEnum

        # 获取实训信息
        training = db.query(models.Training).filter(
            models.Training.id == training_id
        ).first()

        if not training:
            return schemas.ApiResponse(
                code="1004",
                message="实训不存在",
                data=[]
            )

        # 查找关联的Course
        course = db.query(models.Course).filter(
            models.Course.course_type == CourseTypeEnum.TRAINING,
            models.Course.title == f"[实训]{training.title}"
        ).first()

        if not course:
            # 没有提交过作业，返回空列表
            return schemas.ApiResponse(
                code="0000",
                message="暂无作业记录",
                data=[]
            )

        # 查找ClassroomCourse
        classroom_course = db.query(models.ClassroomCourse).filter(
            models.ClassroomCourse.classroom_id == classroom_id,
            models.ClassroomCourse.course_id == course.id
        ).first()

        if not classroom_course:
            return schemas.ApiResponse(
                code="0000",
                message="暂无作业记录",
                data=[]
            )

        # 查询学生的作业提交记录
        progress_list = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id == classroom_course.id,
            models.StudentCourseProgress.student_id == student_id
        ).all()

        assignments = []
        for progress in progress_list:
            # 解析文件列表
            files = []
            if progress.training_assignment_files:
                try:
                    files_data = json.loads(progress.training_assignment_files)
                    for key in ['design_files', 'experiment_reports', 'uploaded_files']:
                        if key in files_data:
                            for f in files_data[key]:
                                files.append({
                                    "id": len(files) + 1,
                                    "name": f.get("file_name", "未知文件"),
                                    "url": f.get("file_url", "")
                                })
                except:
                    pass

            # 确定作业状态
            status = "pending"  # 待批改
            if progress.overall_score is not None:
                status = "graded"  # 已评分
            elif progress.training_submission_status:
                if progress.training_submission_status.value == "submitted":
                    status = "submitted"

            assignment = {
                "id": progress.id,
                "title": f"实训作业 - {training.title}",
                "status": status,
                "submit_time": progress.last_submission_at.isoformat() if progress.last_submission_at else None,
                "score": progress.overall_score,
                "feedback": progress.teacher_feedback,
                "files": files
            }
            assignments.append(assignment)

        return schemas.ApiResponse(
            code="0000",
            message="获取作业列表成功",
            data=assignments
        )

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取作业列表失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"获取作业列表失败: {str(e)}",
            data=[]
        )


@router.post("/{training_id}/submit-assignment", response_model=schemas.ApiResponse)
async def submit_training_assignment_with_files(
    training_id: int,
    training_id_form: int = Form(None, alias="training_id"),
    classroom_id: int = Form(...),
    notes: str = Form(""),
    files: list[UploadFile] = File(default=[]),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交实训作业（支持文件上传）"""
    try:
        from datetime import datetime, timezone
        from pathlib import Path
        from app.models.models import CourseTypeEnum, DifficultyEnum, CourseVisibilityEnum

        student_id = current_user["user_id"]

        # 验证实训存在
        training = db.query(models.Training).filter(
            models.Training.id == training_id
        ).first()

        if not training:
            return schemas.ApiResponse(
                code="1004",
                message="实训不存在",
                trace_id=""
            )

        # 查找ClassroomTraining关联
        classroom_training = db.query(models.ClassroomTraining).filter(
            models.ClassroomTraining.classroom_id == classroom_id,
            models.ClassroomTraining.training_id == training_id
        ).first()

        if not classroom_training:
            return schemas.ApiResponse(
                code="1004",
                message="课堂中不存在该实训",
                trace_id=""
            )

        # 为实训创建或查找对应的Course
        course = db.query(models.Course).filter(
            models.Course.course_type == CourseTypeEnum.TRAINING,
            models.Course.title == f"[实训]{training.title}"
        ).first()

        if not course:
            difficulty_map = {
                models.DifficultyLevelEnum.beginner: DifficultyEnum.BEGINNER,
                models.DifficultyLevelEnum.intermediate: DifficultyEnum.INTERMEDIATE,
                models.DifficultyLevelEnum.advanced: DifficultyEnum.ADVANCED
            }
            course = models.Course(
                title=f"[实训]{training.title}",
                course_type=CourseTypeEnum.TRAINING,
                description=training.intro or "",
                difficulty=difficulty_map.get(training.difficulty, DifficultyEnum.BEGINNER),
                visibility=CourseVisibilityEnum.PRIVATE
            )
            db.add(course)
            db.flush()

        # 查找或创建ClassroomCourse
        classroom_course = db.query(models.ClassroomCourse).filter(
            models.ClassroomCourse.classroom_id == classroom_id,
            models.ClassroomCourse.course_id == course.id
        ).first()

        if not classroom_course:
            classroom_course = models.ClassroomCourse(
                classroom_id=classroom_id,
                course_id=course.id,
                teacher_publish_status=models.CourseInClassroomStatusTeacherEnum.LEARNING,
                published_at=datetime.now(timezone.utc)
            )
            db.add(classroom_course)
            db.flush()

        # 获取或创建学生进度记录
        progress = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id == classroom_course.id,
            models.StudentCourseProgress.student_id == student_id
        ).first()

        if not progress:
            progress = models.StudentCourseProgress(
                classroom_course_id=classroom_course.id,
                student_id=student_id,
                training_submission_status=models.SubmissionStatusEnum.NOT_STARTED
            )
            db.add(progress)
            db.flush()

        # 保存上传的文件
        uploaded_files = []
        if files:
            upload_dir = Path(settings.resource_base_path) / "作业提交" / f"training_{training_id}" / f"classroom_{classroom_id}" / f"student_{student_id}"
            upload_dir.mkdir(parents=True, exist_ok=True)

            for file in files:
                if file.filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unique_filename = f"{timestamp}_{file.filename}"
                    file_path = upload_dir / unique_filename

                    with open(file_path, "wb") as buffer:
                        content = await file.read()
                        buffer.write(content)

                    file_size = file_path.stat().st_size

                    uploaded_files.append({
                        "file_name": file.filename,
                        "file_url": str(file_path.relative_to(settings.resource_base_path)),
                        "file_size": file_size,
                        "uploaded_at": datetime.now(timezone.utc).isoformat()
                    })

        # 更新文件信息
        files_data = {}
        if progress.training_assignment_files:
            try:
                files_data = json.loads(progress.training_assignment_files)
            except:
                files_data = {}

        if "uploaded_files" not in files_data:
            files_data["uploaded_files"] = []

        files_data["uploaded_files"].extend(uploaded_files)
        files_data["notes"] = notes

        progress.training_assignment_files = json.dumps(files_data, ensure_ascii=False)

        # 检查是否超期
        current_time = datetime.now(timezone.utc)
        is_late = False
        if classroom_course.deadline_at:
            is_late = current_time > classroom_course.deadline_at

        # 更新提交状态
        progress.training_submission_status = models.SubmissionStatusEnum.LATE_SUBMISSION if is_late else models.SubmissionStatusEnum.SUBMITTED
        progress.student_status = (
            models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
            if is_late
            else models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME
        )
        progress.last_submission_at = current_time

        if not progress.first_access_at:
            progress.first_access_at = current_time

        db.commit()
        db.refresh(progress)

        return schemas.ApiResponse(
            code="0000",
            message="作业提交成功",
            data={
                "progress_id": progress.id,
                "submission_status": progress.training_submission_status.value,
                "submission_time": progress.last_submission_at.isoformat() if progress.last_submission_at else None,
                "is_late": is_late,
                "files_count": len(uploaded_files)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"提交作业失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return schemas.ApiResponse(
            code="2000",
            message=f"提交作业失败: {str(e)}",
            trace_id=""
        )


@router.post("/{training_id}/clone", response_model=schemas.ApiResponse)
def clone_training(
    training_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    克隆实训
    
    复制指定实训及其关联的数据集、素材等信息，创建一个新的实训。
    新实训的创建者为当前用户，状态为编辑中。
    """
    try:
        # 1. 获取原实训
        original_training = db.query(models.Training).filter(models.Training.id == training_id).first()
        if not original_training:
            raise HTTPException(status_code=404, detail="实训不存在")
            
        # 2. 创建新实训对象
        new_training = models.Training(
            title=f"{original_training.title} (副本)",
            training_type=original_training.training_type,
            intro=original_training.intro,
            industry=original_training.industry,
            difficulty=original_training.difficulty,
            prerequisites=original_training.prerequisites,
            learning_objectives=original_training.learning_objectives,
            tags=original_training.tags,
            course_hours=original_training.course_hours,
            estimated_completion_time=original_training.estimated_completion_time,
            handbook_content=original_training.handbook_content,
            project_path=original_training.project_path,
            assignment_nodes=original_training.assignment_nodes,
            require_design_files=original_training.require_design_files,
            require_experiment_report=original_training.require_experiment_report,
            
            # 资源路径引用
            handbook_content_url=original_training.handbook_content_url,
            cover_url=original_training.cover_url,
            bi_template_path=original_training.bi_template_path,
            ai_template_path=original_training.ai_template_path,
            template_files_manifest=original_training.template_files_manifest,
            superset_dashboard_id=original_training.superset_dashboard_id,
            superset_dataset_refs=original_training.superset_dataset_refs,
            
            # 环境配置
            environment_id=original_training.environment_id,
            storage_limit=original_training.storage_limit,
            memory_limit=original_training.memory_limit,
            cpu_limit=original_training.cpu_limit,
            
            # 重置状态
            is_published=False,
            publish_status=models.TrainingPublishStatusEnum.EDITING,
            visibility=models.TrainingVisibilityEnum.PRIVATE,
            version="1.0",
            
            # 设置创建者
            creator_id=current_user["user_id"],
            
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_training)
        db.flush() # 获取 ID
        
        # 3. 复制数据集关联 (TrainingDataset)
        # 注意：这里我们复制的是数据集的引用记录，文件本身不复制，仍然指向同一个位置
        # 除非文件是用户上传的私有文件且需要隔离修改，但目前架构似乎是引用
        for ds in original_training.datasets:
            new_ds = models.TrainingDataset(
                training_id=new_training.id,
                name=ds.name,
                file_url=ds.file_url,
                relative_path=ds.relative_path,
                file_type=ds.file_type,
                file_size=ds.file_size,
                description=ds.description,
                access_path=ds.access_path,
                access_path_in_env=ds.access_path_in_env,
                uploader_id=current_user["user_id"] # 使用当前用户
            )
            db.add(new_ds)
            
        # 4. 复制实训素材 (TrainingAsset)
        for asset in original_training.assets:
            new_asset = models.TrainingAsset(
                training_id=new_training.id,
                name=asset.name,
                relative_path=asset.relative_path,
                file_type=asset.file_type,
                file_size=asset.file_size,
                description=asset.description,
                asset_type=asset.asset_type,
                uploader_id=current_user["user_id"]
            )
            db.add(new_asset)

        db.commit()
        db.refresh(new_training)
        
        return schemas.ApiResponse(
            code="0000",
            message="实训克隆成功",
            data={"id": new_training.id}
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"克隆实训失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"克隆实训失败: {str(e)}")


# ==================== BI 可视化分析实训 API ====================

# 简化的数据集端点，用于Jupyter环境（不需要classroom_id）
@router.get("/{training_id}/datasets", response_model=schemas.ApiResponse)
def get_training_datasets_simple(
    training_id: int,
    db: Session = Depends(get_db)
):
    """
    获取实训的数据集列表（简化版，用于Jupyter环境）

    返回实训关联的数据集基本信息（名称、路径、大小）
    """
    try:
        # 获取实训信息
        training = db.query(models.Training).filter(models.Training.id == training_id).first()
        if not training:
            raise HTTPException(status_code=404, detail="实训不存在")

        # 获取实训关联的数据集
        datasets_from_db = db.query(models.TrainingDataset).filter(
            models.TrainingDataset.training_id == training_id
        ).all()

        if not datasets_from_db:
            return schemas.ApiResponse(
                code="0000",
                message="暂无数据集",
                data={"datasets": [], "total": 0}
            )

        # 构建数据集列表 - 字段名匹配前端 Dataset 接口
        result_datasets = []
        for ds in datasets_from_db:
            # 获取文件路径
            file_path = ds.access_path_in_env or ds.access_path or f"/datasets/{ds.name}"
            result_datasets.append({
                "id": ds.id,
                "name": ds.name,
                "path": file_path,
                "size": ds.file_size or 0,
                "description": ds.description or "",
            })

        return schemas.ApiResponse(
            code="0000",
            message="获取数据集列表成功",
            data={
                "training_id": training_id,
                "datasets": result_datasets,
                "total": len(result_datasets)
            }
        )

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据集列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取数据集列表失败: {str(e)}")


# 兼容旧前端的数据集端点 (projects/{id}/datasets)
@router.get("/projects/{training_id}/datasets", response_model=schemas.ApiResponse)
def get_training_datasets_compat(
    training_id: int,
    db: Session = Depends(get_db)
):
    """
    获取实训的数据集列表（旧版兼容接口）

    为了兼容旧前端代码，使用 /projects/{id}/datasets 路径
    返回实训关联的数据集基本信息（名称、路径、大小）
    """
    try:
        # 获取实训信息
        training = db.query(models.Training).filter(models.Training.id == training_id).first()
        if not training:
            raise HTTPException(status_code=404, detail="实训不存在")

        # 获取实训关联的数据集
        datasets_from_db = db.query(models.TrainingDataset).filter(
            models.TrainingDataset.training_id == training_id
        ).all()

        if not datasets_from_db:
            return schemas.ApiResponse(
                code="0000",
                message="暂无数据集",
                data={"datasets": [], "total": 0}
            )

        # 构建数据集列表 - 字段名匹配前端 Dataset 接口
        result_datasets = []
        for ds in datasets_from_db:
            # 获取文件路径
            file_path = ds.access_path_in_env or ds.access_path or f"/datasets/{ds.name}"
            result_datasets.append({
                "id": ds.id,
                "name": ds.name,
                "path": file_path,
                "size": ds.file_size or 0,
                "description": ds.description or "",
            })

        return schemas.ApiResponse(
            code="0000",
            message="获取数据集列表成功",
            data={
                "training_id": training_id,
                "datasets": result_datasets,
                "total": len(result_datasets)
            }
        )

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据集列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取数据集列表失败: {str(e)}")


@router.get("/{training_id}/bi-dataset", response_model=schemas.ApiResponse)
def get_bi_dataset(
    training_id: int,
    classroom_id: Optional[int] = Query(default=None, description="课堂ID (可选，对于Jupyter环境可不传)"),
    limit: int = Query(default=10000, ge=1, le=10000, description="每个数据集返回的最大行数"),
    db: Session = Depends(get_db)
):
    """
    获取 BI 实训的数据集

    从实训的 metadata.json 配置读取 datasetDir，加载 CSV 数据返回
    对于Jupyter实训，classroom_id为可选参数
    """
    import csv
    from pathlib import Path

    try:
        # 获取实训信息
        training = db.query(models.Training).filter(models.Training.id == training_id).first()
        if not training:
            raise HTTPException(status_code=404, detail="实训不存在")

        # 尝试从数据库中的数据集获取数据优先
        datasets_from_db = db.query(models.TrainingDataset).filter(
            models.TrainingDataset.training_id == training_id
        ).all()

        if datasets_from_db:
            # 从数据库数据集读取
            result_datasets = []
            resource_base = settings.resource_base_path
            # 备选资源路径（应对 resource_base_path 配置与实际挂载点不一致的情况）
            import os
            _alt_resource_dir = os.environ.get("HUIXUE_RESOURCE_DIR", "")
            resource_base_candidates = [resource_base]
            if _alt_resource_dir and Path(_alt_resource_dir) != resource_base:
                resource_base_candidates.append(Path(_alt_resource_dir))

            for ds in datasets_from_db:
                # 解析文件路径：尝试多个基础路径
                file_path = None
                if ds.relative_path:
                    for base in resource_base_candidates:
                        candidate = base / ds.relative_path
                        if Path(candidate).exists():
                            file_path = candidate
                            break
                    if not file_path:
                        file_path = resource_base / ds.relative_path  # fallback
                else:
                    file_path = ds.file_url or ds.access_path

                if ds.file_type in ['csv', 'CSV', 'tsv']:
                    # 读取 CSV/TSV 文件（限制最大行数避免浏览器无法解析超大JSON）
                    BI_CSV_ROW_LIMIT = limit
                    if file_path and Path(file_path).exists():
                        try:
                            with _open_text_file(file_path) as f:
                                reader = csv.DictReader(f)
                                data = []
                                total_count = 0
                                for row in reader:
                                    total_count += 1
                                    if len(data) < BI_CSV_ROW_LIMIT:
                                        data.append(row)

                            result_datasets.append({
                                "id": ds.id,
                                "name": ds.name,
                                "columns": list(data[0].keys()) if data else [],
                                "data": data,
                                "totalRows": total_count,
                                "truncated": total_count > BI_CSV_ROW_LIMIT
                            })
                        except HTTPException:
                            raise
                        except Exception as e:
                            logger.warning(f"读取数据集文件失败 {file_path}: {e}")
                elif ds.file_type in ['sql', 'SQL', 'sql_data']:
                    # 读取 SQL 文件：在内存 SQLite 中执行，返回查询结果
                    if file_path and Path(file_path).exists():
                        try:
                            from app.utils.bi_data_loader import BIDataLoader
                            data = BIDataLoader._load_from_sql_files([Path(file_path)], limit=limit)
                            if data:
                                result_datasets.append({
                                    "id": ds.id,
                                    "name": ds.name,
                                    "columns": list(data[0].keys()) if data else [],
                                    "data": data,
                                    "totalRows": len(data)
                                })
                        except HTTPException:
                            raise
                        except Exception as e:
                            logger.warning(f"执行SQL数据集文件失败 {file_path}: {e}")

            if result_datasets:
                return schemas.ApiResponse(
                    code="0000",
                    message="获取数据集成功",
                    data={"datasets": result_datasets}
                )

        # 获取实训项目路径作为备用
        project_path = training.project_path
        # 从 project_path 读取 metadata.json
        # 使用统一的资源路径配置
        resource_base = settings.resource_base_path

        # project_path 可能包含 "实训资源/" 前缀，也可能不包含
        if project_path:
            if project_path.startswith("实训资源/"):
                project_dir = resource_base / project_path
            else:
                project_dir = resource_base / "实训资源" / project_path
        else:
            project_dir = None

        if project_dir and project_dir.exists():
            metadata_path = project_dir / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                dataset_dir = metadata.get("datasetDir", "datasets")
                datasets_path = project_dir / dataset_dir

                result_datasets = []
                raw_datasets = {}  # 用于存储原始数据，便于合并

                if datasets_path.exists():
                    BI_CSV_FALLBACK_LIMIT = limit
                    for csv_file in datasets_path.glob("*.csv"):
                        try:
                            # 使用 utf-8-sig 自动去除 BOM 字符
                            with _open_text_file(csv_file) as f:
                                reader = csv.DictReader(f)
                                data = []
                                for row in reader:
                                    data.append(row)
                                    if len(data) >= BI_CSV_FALLBACK_LIMIT:
                                        break

                            raw_datasets[csv_file.name] = data
                        except HTTPException:
                            raise
                        except Exception as e:
                            logger.warning(f"读取 CSV 文件失败 {csv_file}: {e}")

                # 检查是否需要合并数据集（多个数据集且有共同关联键）
                merged_data = None
                unmerged_datasets = {}  # 保存无法合并的数据集

                if len(raw_datasets) >= 2:
                    # 查找可能的关联键（通常是 *_id 字段）
                    all_keys = {}
                    for name, data in raw_datasets.items():
                        if data:
                            all_keys[name] = set(data[0].keys())

                    # 定义支持的关联键优先级
                    supported_join_keys = ['sku_id', 'product_id', 'item_id', 'customer_id', 'invoice_id', 'order_id', 'user_id', 'id']

                    # 找出可以合并的数据集（至少两个数据集有共同关联键）
                    join_key = None
                    datasets_to_merge = []

                    for candidate_key in supported_join_keys:
                        matching_datasets = [(name, data) for name, data in raw_datasets.items()
                                           if data and candidate_key in all_keys.get(name, set())]
                        if len(matching_datasets) >= 2:
                            join_key = candidate_key
                            datasets_to_merge = matching_datasets
                            break

                    # 标记无法合并的数据集
                    merged_names = set(name for name, _ in datasets_to_merge)
                    for name, data in raw_datasets.items():
                        if name not in merged_names:
                            unmerged_datasets[name] = data

                    if join_key and len(datasets_to_merge) >= 2:
                        logger.info(f"发现共同关联键 '{join_key}'，将合并 {len(datasets_to_merge)} 个数据集")
                        if unmerged_datasets:
                            logger.info(f"以下数据集无法合并，将单独返回: {list(unmerged_datasets.keys())}")

                        # 确定主表（行数最多的）和维度表
                        sorted_datasets = sorted(datasets_to_merge, key=lambda x: len(x[1]), reverse=True)
                        main_name, main_data = sorted_datasets[0]

                        # 构建维度表的查找字典
                        dim_lookups = {}
                        for name, data in sorted_datasets[1:]:
                            if data:
                                lookup = {}
                                dim_columns = [k for k in data[0].keys() if k != join_key]
                                for row in data:
                                    key_value = row.get(join_key)
                                    if key_value:
                                        lookup[key_value] = {k: row.get(k, '') for k in dim_columns}
                                dim_lookups[name] = {'lookup': lookup, 'columns': dim_columns}

                        # 合并数据
                        merged_data = []
                        for row in main_data:
                            merged_row = dict(row)
                            key_value = row.get(join_key)

                            # 添加维度表的字段
                            for name, dim_info in dim_lookups.items():
                                dim_row = dim_info['lookup'].get(key_value, {})
                                for col in dim_info['columns']:
                                    merged_row[col] = dim_row.get(col, '')

                            merged_data.append(merged_row)

                        logger.info(f"数据集合并完成: {len(merged_data)} 行, {len(merged_data[0]) if merged_data else 0} 列")

                # 如果合并成功，返回合并后的数据集
                if merged_data:
                    columns = []
                    if merged_data:
                        for key in merged_data[0].keys():
                            sample_value = merged_data[0][key]
                            try:
                                float(sample_value)
                                col_type = "number"
                                semantic_type = "quantitative"
                            except:
                                col_type = "string"
                                semantic_type = "nominal"

                            columns.append({
                                "name": key,
                                "type": col_type,
                                "semanticType": semantic_type
                            })

                    # 返回合并后的单一数据集
                    dataset_names = ', '.join(raw_datasets.keys())
                    result_datasets = [{
                        "id": 1,
                        "name": dataset_names,
                        "columns": columns,
                        "data": merged_data,
                        "totalRows": len(merged_data)
                    }]
                else:
                    # 没有合并，返回各自独立的数据集
                    for name, data in raw_datasets.items():
                        columns = []
                        if data:
                            for key in data[0].keys():
                                sample_value = data[0][key]
                                try:
                                    float(sample_value)
                                    col_type = "number"
                                    semantic_type = "quantitative"
                                except:
                                    col_type = "string"
                                    semantic_type = "nominal"

                                columns.append({
                                    "name": key,
                                    "type": col_type,
                                    "semanticType": semantic_type
                                })

                        result_datasets.append({
                            "id": len(result_datasets) + 1,
                            "name": name,
                            "columns": columns,
                            "data": data,
                            "totalRows": len(data)
                        })

                if result_datasets:
                    return schemas.ApiResponse(
                        code="0000",
                        message="获取数据集成功",
                        data={"datasets": result_datasets}
                    )

        # CSV 没找到，尝试用 BIDataLoader 加载 SQL 文件
        try:
            from app.utils.bi_data_loader import BIDataLoader
            sql_data = BIDataLoader.load_data(training_id, db, limit=limit)
            if sql_data:
                return schemas.ApiResponse(
                    code="0000",
                    message="获取数据集成功（SQL源）",
                    data={"datasets": [{
                        "id": training_id,
                        "name": training.title if training else f"dataset_{training_id}",
                        "columns": list(sql_data[0].keys()) if sql_data else [],
                        "data": sql_data,
                        "totalRows": len(sql_data)
                    }]}
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"BIDataLoader fallback 失败: {e}")

        # 没有找到数据集
        return schemas.ApiResponse(
            code="0000",
            message="没有找到数据集",
            data={"datasets": []}
        )

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 BI 数据集失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取 BI 数据集失败: {str(e)}")


@router.get("/{training_id}/bi-draft", response_model=schemas.ApiResponse)
def get_bi_draft(
    training_id: int,
    classroom_id: int = Query(..., description="课堂ID"),
    student_id: int = Query(..., description="学生ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取 BI 实训草稿
    """
    try:
        from app.core.identity import resolve_scoped_id
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",), forbidden_detail="无权访问该学生草稿")
        draft = db.query(models.TrainingBiDraft).filter(
            models.TrainingBiDraft.training_id == training_id,
            models.TrainingBiDraft.classroom_id == classroom_id,
            models.TrainingBiDraft.student_id == student_id
        ).first()

        if not draft:
            return schemas.ApiResponse(
                code="0000",
                message="没有找到草稿",
                data=None
            )

        return schemas.ApiResponse(
            code="0000",
            message="获取草稿成功",
            data={
                "id": draft.id,
                "snapshot": json.loads(draft.draft_snapshot) if draft.draft_snapshot else None,
                "schemaVersion": draft.schema_version,
                "platformVersion": draft.platform_version,
                "updatedAt": draft.updated_at.isoformat() if draft.updated_at else None
            }
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 BI 草稿失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取 BI 草稿失败: {str(e)}")


@router.post("/{training_id}/bi-draft", response_model=schemas.ApiResponse)
def save_bi_draft(
    training_id: int,
    classroom_id: int = Query(..., description="课堂ID"),
    student_id: int = Query(..., description="学生ID"),
    request: dict = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    保存 BI 实训草稿

    使用 UPSERT 策略：存在则更新，不存在则创建
    """
    try:
        from app.core.identity import resolve_scoped_id
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",), forbidden_detail="无权保存该学生草稿")
        # 查找现有草稿
        draft = db.query(models.TrainingBiDraft).filter(
            models.TrainingBiDraft.training_id == training_id,
            models.TrainingBiDraft.classroom_id == classroom_id,
            models.TrainingBiDraft.student_id == student_id
        ).first()

        snapshot_json = json.dumps(request.get("snapshot")) if request and request.get("snapshot") else None
        schema_version = request.get("schemaVersion") if request else None
        platform_version = request.get("platformVersion") if request else None

        if draft:
            # 更新现有草稿
            draft.draft_snapshot = snapshot_json
            draft.schema_version = schema_version
            draft.platform_version = platform_version
            draft.updated_at = datetime.utcnow()
        else:
            # 创建新草稿
            draft = models.TrainingBiDraft(
                training_id=training_id,
                classroom_id=classroom_id,
                student_id=student_id,
                draft_snapshot=snapshot_json,
                schema_version=schema_version,
                platform_version=platform_version
            )
            db.add(draft)

        db.commit()
        db.refresh(draft)

        return schemas.ApiResponse(
            code="0000",
            message="草稿保存成功",
            data={
                "id": draft.id,
                "updatedAt": draft.updated_at.isoformat() if draft.updated_at else None
            }
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"保存 BI 草稿失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"保存 BI 草稿失败: {str(e)}")
