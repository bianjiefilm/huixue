"""
课程管理端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import uuid
import logging
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# 修正的导入路径
from app.core.database import get_db, engine, Base
from app.core.dependencies import get_current_user_optional
from app.core.security import get_current_user
from app.core.identity import resolve_scoped_id, require_owner_or_admin
from app.models import models as db_models  # 避免与FastAPI的models冲突
from app.crud import crud
from app.schemas import schemas

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    tags=['courses']
)

@router.get("/courses", response_model=schemas.ApiResponse)
def get_courses(
    keyword: Optional[str] = Query(None, description="模糊搜索关键字"),
    direction: Optional[List[str]] = Query(None, description="方向标签，可多选"),
    category: Optional[List[str]] = Query(None, description="分类标签，可多选"),
    difficulty: Optional[str] = Query(None, description="难度级别"),
    course_type: Optional[str] = Query(None, description="课程类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    查询课程教材列表
    按照架构澄清方案，此API专门返回courses表记录（完整教学课程）
    """
    try:
        skip = (page - 1) * page_size
        # 处理课程类型枚举
        course_type_enum = None
        if course_type:
            try:
                course_type_enum = db_models.CourseTypeEnum(course_type)
            except ValueError:
                # 尝试忽略大小写或直接返回空
                pass

        courses, total = crud.get_courses(
            db=db,
            skip=skip,
            limit=page_size,
            keyword=keyword,
            directions=direction,
            categories=category,
            difficulty=difficulty,
            course_type=course_type_enum
        )

        course_list = [schemas.CourseResponse.model_validate(course) for course in courses]

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": [course.model_dump() for course in course_list],
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

# 获取课程筛选标签（用于课程选择页面）

@router.get("/courses/filter-tags", response_model=schemas.ApiResponse)
def get_course_filter_tags(
    course_type: Optional[str] = Query(None, description="课程类型：practice, training, course_material"),
    db: Session = Depends(get_db)
):
    """获取课程筛选标签（用于课程选择页面）"""
    try:
        filter_tags = crud.get_course_filter_tags_for_selection(db, course_type)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=filter_tags
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 获取课程库中的课程（用于添加课程时选择）

@router.get("/courses/library", response_model=schemas.ApiResponse)
def get_course_library(
    course_type: Optional[str] = Query(None, description="课程类型：practice, training, course_material"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    direction: Optional[str] = Query(None, description="方向标签"),
    category: Optional[str] = Query(None, description="分类标签"),
    difficulty: Optional[str] = Query(None, description="难度级别"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取课程库中的课程列表（用于课程选择）"""
    try:
        skip = (page - 1) * page_size
        courses, total = crud.get_courses_for_library(
            db=db,
            course_type=course_type,
            keyword=keyword,
            direction=direction,
            category=category,
            difficulty=difficulty,
            skip=skip,
            limit=page_size
        )

        # 获取筛选标签
        filter_tags = crud.get_course_filter_tags_for_selection(db, course_type)

        # 转换为响应格式（直接使用统一格式的数据）
        course_list = []
        for course in courses:
            course_list.append(course)

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": course_list,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                },
                "filter_tags": filter_tags
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


@router.get("/courses/{course_id}", response_model=schemas.ApiResponse)
def get_course_detail(
    course_id: int,
    include_resources: bool = Query(True, description="是否包含教学资源列表"),
    resource_page: int = Query(1, ge=1, description="资源列表页码"),
    resource_page_size: int = Query(50, ge=1, le=200, description="资源列表每页数量"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """课程教材详情"""
    try:
        course = crud.get_course(db, course_id=course_id)
        if course is None:
            return schemas.ApiResponse(
                code="1002",
                message="资源不存在",
                trace_id=str(uuid.uuid4())
            )

        # 调试信息
        logger.info(f"Course loaded: {course.title} (ID: {course.id})")
        logger.info(f"Course practices count: {len(course.course_practices) if course.course_practices else 0}")
        if course.course_practices:
            for i, practice in enumerate(course.course_practices):
                logger.info(f"Practice {i+1}: {practice.title} (tasks: {len(practice.tasks) if practice.tasks else 0})")

        # 手动转换资源为字典列表，避免 Pydantic 验证错误
        resources_data = []
        if course.resources:
            for r in course.resources:
                resources_data.append({
                    "id": r.id,
                    "title": r.title,
                    "url": r.url,
                    "resource_type": r.resource_type,
                    "can_download": r.can_download,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                })

        # 手动转换章节为字典列表
        chapters_data = []
        if course.chapters:
            for ch in course.chapters:
                chapters_data.append({
                    "id": ch.id,
                    "title": ch.title,
                    "order_index": ch.order_index,
                    "experiment_count": ch.experiment_count or 0
                })

        # 手动转换考核为字典列表
        assessments_data = []
        if course.assessments:
            for a in course.assessments:
                assessments_data.append({
                    "id": a.id,
                    "title": a.title,
                    "url": a.url,
                    "assessment_type": a.assessment_type,
                    "created_at": a.created_at.isoformat() if a.created_at else None
                })

        # 构建课程详情字典，然后验证
        course_dict = {
            "id": course.id,
            "title": course.title,
            "course_type": course.course_type.value if course.course_type else None,
            "description": course.description,
            "cover_url": course.cover_url,
            "difficulty": course.difficulty.value if course.difficulty else None,
            "direction": course.direction,
            "categories": course.categories,
            "source": course.source,
            "practice_task_count": course.practice_task_count,
            "material_resources_count": course.material_resources_count or len(resources_data),
            "material_assessments_count": course.material_assessments_count or len(assessments_data),
            "visibility": course.visibility.value if course.visibility else None,
            "resources": resources_data,
            "chapters": chapters_data,
            "assessments": assessments_data,
            "practices": [],
            "created_at": course.created_at,
            "updated_at": course.updated_at
        }

        course_detail = schemas.CourseDetailResponse.model_validate(course_dict)

        # 手动设置practices，因为Pydantic可能没有正确处理关系
        if course.course_practices:
            practices_data = []
            for practice in course.course_practices:
                practice_dict = schemas.PracticeDetailResponse.model_validate(practice).model_dump()
                practices_data.append(practice_dict)
            course_detail.practices = practices_data
        
        # 根据用户角色设置资源下载权限
        # 学生不允许下载教学资源，只能在线预览
        is_student = current_user and current_user.get("role") == "student"
        
        data = course_detail.model_dump()
        
        # 处理资源列表分页和URL转换
        if data.get('resources') and include_resources:
            resources = data['resources']

            # 计算分页
            total_resources = len(resources)
            start_idx = (resource_page - 1) * resource_page_size
            end_idx = start_idx + resource_page_size

            # 分页切片
            paginated_resources = resources[start_idx:end_idx]

            # 转换URL为抽象的resource_id路径，隐藏内部结构
            for resource in paginated_resources:
                resource['url'] = f"/api/v1/files/resources/{resource['id']}"

            # 构建分页信息
            resource_pagination = {
                "page": resource_page,
                "page_size": resource_page_size,
                "total": total_resources,
                "total_pages": (total_resources + resource_page_size - 1) // resource_page_size,
                "has_next": end_idx < total_resources,
                "has_prev": resource_page > 1
            }

            # 替换资源列表为分页结果，并添加分页信息
            data['resources'] = paginated_resources
            data['resource_pagination'] = resource_pagination

        elif not include_resources:
            # 如果不包含资源，移除资源列表
            data.pop('resources', None)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=data
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/courses/{course_id}/outline", response_model=schemas.ApiResponse)
def get_course_outline(course_id: int, db: Session = Depends(get_db)):
    """获取课程教学大纲"""
    try:
        outline = crud.get_course_outline(db, course_id=course_id)
        if outline is None:
            return schemas.ApiResponse(
                code="1002",
                message="教学大纲不存在",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=outline
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/courses/{course_id}/modules", response_model=schemas.ApiResponse)
def get_course_modules(course_id: int, db: Session = Depends(get_db)):
    """获取课程章节列表（用于按课表添加课程功能）"""
    try:
        # 获取课程
        course = db.query(db_models.Course).filter(db_models.Course.id == course_id).first()
        if course is None:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在",
                trace_id=str(uuid.uuid4())
            )

        # 获取课程章节
        chapters = db.query(db_models.Chapter).filter(
            db_models.Chapter.course_id == course_id
        ).order_by(db_models.Chapter.order_index).all()

        # 构建返回数据
        modules_list = []
        for chapter in chapters:
            modules_list.append({
                "id": str(chapter.id),
                "name": chapter.title,
                "lesson_count": chapter.experiment_count or 0,
                "order_index": chapter.order_index
            })

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": modules_list,
                "course_title": course.title,
                "total": len(modules_list)
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


@router.get("/courses/{course_id}/assessments", response_model=schemas.ApiResponse)
def get_course_assessments(course_id: int, db: Session = Depends(get_db)):
    """获取课程考核"""
    try:
        assessments = crud.get_course_assessments(db, course_id=course_id)
        assessment_list = [schemas.CourseAssessmentResponse.model_validate(assessment) for assessment in assessments]
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=[assessment.model_dump() for assessment in assessment_list]
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.3 微型实验库

@router.get("/filter-tags/courses", response_model=schemas.ApiResponse)
def get_course_filter_tags(db: Session = Depends(get_db)):
    """获取课程筛选标签"""
    try:
        tags = crud.get_filter_tags(db)
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=tags
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/statistics", response_model=schemas.ApiResponse)
def get_statistics(db: Session = Depends(get_db)):
    """获取统计信息"""
    try:
        stats = crud.get_statistics(db)
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=stats
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/hands-on-library", response_model=schemas.ApiResponse)
def get_hands_on_library(
    keyword: Optional[str] = Query(None, description="模糊搜索关键字"),
    direction: Optional[str] = Query(None, description="方向标签"),
    category: Optional[str] = Query(None, description="分类标签"),
    difficulty: Optional[str] = Query(None, description="难度级别"),
    source: Optional[str] = Query(None, description="资源来源：practice(微型实验) 或 training(项目实训)，不传则返回所有"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取动手实践库
    按照架构澄清方案，此API聚合practices和trainings表数据，返回统一的practice-like格式
    
    注意：
    - source=practice: 只返回微型实验（practices表）
    - source=training: 只返回项目实训（trainings表）
    - source为空: 返回所有（practices + trainings）
    """
    try:
        skip = (page - 1) * page_size

        # 获取practices数据
        practices_query = db.query(db_models.Practice)
        # 只查询已发布的practices
        practices_query = practices_query.filter(
            db_models.Practice.is_published == True,
            db_models.Practice.visibility == db_models.PracticeVisibilityEnum.PUBLIC
        )
        if keyword:
            practices_query = practices_query.filter(
                or_(
                    db_models.Practice.title.ilike(f"%{keyword}%"),
                    db_models.Practice.description.ilike(f"%{keyword}%")
                )
            )
        if direction:
            practices_query = practices_query.filter(db_models.Practice.direction == direction)
        if category:
            practices_query = practices_query.filter(db_models.Practice.category == category)
        if difficulty:
            practices_query = practices_query.filter(db_models.Practice.difficulty == difficulty)

        practices = practices_query.all() if source != 'training' else []

        # 获取trainings数据并转换为practice-like格式
        trainings_query = db.query(db_models.Training)
        # 只查询已发布的trainings
        trainings_query = trainings_query.filter(
            db_models.Training.is_published == True
        )
        if keyword:
            trainings_query = trainings_query.filter(
                or_(
                    db_models.Training.title.ilike(f"%{keyword}%"),
                    db_models.Training.intro.ilike(f"%{keyword}%")
                )
            )
        if category:
            trainings_query = trainings_query.filter(db_models.Training.industry == category)
        if difficulty:
            trainings_query = trainings_query.filter(db_models.Training.difficulty == difficulty)

        trainings = trainings_query.all() if source != 'practice' else []

        # 将Training对象转换为Practice-like对象
        from types import SimpleNamespace
        practices_from_trainings = []
        for training in trainings:
            practice_like = SimpleNamespace(
                id=training.id + 10000,  # 避免ID冲突
                title=training.title,
                description=training.intro,
                cover_url=f'https://picsum.photos/300/200?random={training.id + 100}',
                direction=training.industry or '数据分析',
                category=training.training_type.value if hasattr(training.training_type, 'value') else 'CODING',
                difficulty=training.difficulty.value if hasattr(training.difficulty, 'value') else 'intermediate',
                parent_course_id=None,
                summary=training.intro,
                coin=100,
                task_count=4,
                created_at=training.created_at,
                updated_at=training.updated_at if hasattr(training, 'updated_at') else training.created_at,
                _source='training',
                _training_id=training.id
            )
            practices_from_trainings.append(practice_like)

        # 合并两个列表
        all_practices = practices + practices_from_trainings
        total = len(all_practices)

        # 应用分页
        if skip >= total:
            paginated_practices = []
        else:
            end_index = min(skip + page_size, total)
            paginated_practices = all_practices[skip:end_index]

        # 转换为响应格式
        practice_list = []
        for practice in paginated_practices:
            # 处理difficulty枚举值
            difficulty_value = practice.difficulty
            if hasattr(difficulty_value, 'value'):
                difficulty_value = difficulty_value.value
            elif isinstance(difficulty_value, str):
                difficulty_value = difficulty_value
            else:
                difficulty_value = str(difficulty_value)
            
            practice_data = {
                "id": practice.id,
                "title": practice.title,
                "description": practice.description or "",
                "cover_url": practice.cover_url or "",
                "direction": practice.direction,
                "category": practice.category,
                "difficulty": difficulty_value,
                "summary": getattr(practice, 'summary', practice.description) or "",
                "coin": getattr(practice, 'coin', 0),
                "task_count": getattr(practice, 'task_count', 0),
                "_source": getattr(practice, '_source', 'practice')
            }
            practice_list.append(practice_data)

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
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 原有用户和文章API ====================

# 用户相关API

@router.post("/classrooms/{classroom_id}/courses", response_model=schemas.ApiResponse)
def add_course_to_classroom(
    classroom_id: int,
    course_id: int = Query(..., description="课程ID"),
    classroom_chapter_title: Optional[str] = Query(None, description="课堂章节标题"),
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加课程到课堂"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        classroom_course = crud.add_course_to_classroom(
            db=db,
            classroom_id=classroom_id,
            course_id=course_id,
            teacher_id=teacher_id,
            classroom_chapter_title=classroom_chapter_title
        )
        
        if classroom_course is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        course_data = schemas.ClassroomCourseResponse.model_validate(classroom_course)
        
        return schemas.ApiResponse(
            code="0000",
            message="课程添加成功",
            data=course_data.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/classrooms/{classroom_id}/courses/publish", response_model=schemas.ApiResponse)
def publish_classroom_courses(
    classroom_id: int,
    request: schemas.CourseBatchOperationRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量发布课程"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        success = crud.publish_classroom_courses(
            db=db,
            classroom_id=classroom_id,
            course_ids=request.course_ids,
            teacher_id=teacher_id,
            deadline_at=request.deadline_at,
            is_mandatory=request.is_mandatory
        )

        if not success:
            return schemas.ApiResponse(
                code="1001",
                message="发布失败，课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )

        return schemas.ApiResponse(
            code="0000",
            message="课程发布成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/courses/{course_id}/detail", response_model=schemas.ApiResponse)
def get_course_detail_for_classroom(
    course_id: int,
    user_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    user_role: Optional[str] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 role 为准"),
    classroom_id: Optional[int] = Query(None, description="课堂ID（从课堂进入时必填）"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    4.1.4 课程详情API
    
    功能简介：用户可点击课程名称进入课程详情页面，对于实践和实训课程，
    课程详情页都包含课程的一些基本信息，包括课程标题，课程状态，完成该课程
    可获得的金币数，各状态下的学生人数，课程难易程度，课程起止时间，以及课
    程剩余时间。
    
    支持：
    - 4.1.4.1 教师端实践详情
    - 4.1.4.2 学生端实践详情  
    - 4.1.4.3 教师端实训详情
    - 4.1.4.4 学生端实训详情
    """
    try:
        # 安全: JWT 中 user_id / role 强制覆盖 query 参数 (防止任意 user_id 横向越权)
        # query.user_id / query.user_role 仅作向后兼容保留, 不参与查询
        user_id = current_user["id"]
        user_role = (current_user.get("roles") or ["student"])[0]

        # 验证课程是否存在
        course = crud.get_course(db, course_id=course_id)
        practice = None
        training = None
        classroom_course = None
        classroom_training = None

        is_practice = False
        is_training = False
        target_course_id = course_id

        # P0-1 修复: classroom_id 已传时, 无条件优先查 classroom_courses 行.
        # 若行内 practice_id 非空, 切换到 practice 模式 (用 practice_id 路由 tasks 查询).
        # 历史 bug: classroom_courses 同时持有 course_id 和 practice_id (两表 id 可能恰好相同),
        # 老代码只在 course 找不到时才查 classroom_course, 导致 course_id 命中 courses 表后
        # target_course_id 一直 = course_id, 但 tasks 表用 practice_id 关联 → 返回 tasks=[].
        if classroom_id:
            # URL 可能传 classroom_course.id / courses.id / practices.id, 三种都接受
            # 优先匹配 practice_id (有 practice_id 的行能正确路由 tasks 查询);
            # 同 classroom_id+course_id 多行匹配时, 用 id desc 取最新行保证 .first() 确定性
            classroom_course = db.query(db_models.ClassroomCourse).filter(
                db_models.ClassroomCourse.classroom_id == classroom_id,
                or_(
                    db_models.ClassroomCourse.id == course_id,
                    db_models.ClassroomCourse.course_id == course_id,
                    db_models.ClassroomCourse.practice_id == course_id,
                )
            ).order_by(
                db_models.ClassroomCourse.practice_id.desc().nullslast(),
                db_models.ClassroomCourse.id.desc(),
            ).first()

            if classroom_course:
                # 优先用 practice_id (tasks 表按 practice_id 关联, 必须用 practice_id 才能查到 tasks)
                if classroom_course.practice_id:
                    is_practice = True
                    target_course_id = classroom_course.practice_id
                    practice = db.query(db_models.Practice).filter(
                        db_models.Practice.id == target_course_id
                    ).first()
                    # 若 row 同时有 course_id, 保留 course 对象 (banner / TRAINING 分支可能用)
                    if not course and classroom_course.course_id:
                        course = crud.get_course(db, course_id=classroom_course.course_id)
                elif classroom_course.course_id:
                    target_course_id = classroom_course.course_id
                    if not course:
                        course = crud.get_course(db, course_id=target_course_id)
            else:
                # classroom_course 没匹配到, 尝试 classroom_training
                classroom_training = db.query(db_models.ClassroomTraining).filter(
                    (db_models.ClassroomTraining.id == course_id) | (db_models.ClassroomTraining.training_id == course_id),
                    db_models.ClassroomTraining.classroom_id == classroom_id
                ).first()
                if classroom_training:
                    is_training = True
                    target_course_id = classroom_training.training_id
                    training = db.query(db_models.Training).filter(db_models.Training.id == target_course_id).first()

        if not course and not practice and not training:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在",
                trace_id=str(uuid.uuid4())
            )

        # 如果指定了课堂ID且尚未查到classroom_course，验证课程是否在该课堂中
        if classroom_id and not classroom_course and not classroom_training:
            if is_practice:
                classroom_course = db.query(db_models.ClassroomCourse).filter(
                    db_models.ClassroomCourse.classroom_id == classroom_id,
                    db_models.ClassroomCourse.practice_id == target_course_id
                ).first()
            elif is_training:
                classroom_training = db.query(db_models.ClassroomTraining).filter(
                    db_models.ClassroomTraining.classroom_id == classroom_id,
                    db_models.ClassroomTraining.training_id == target_course_id
                ).first()
            else:
                classroom_course = db.query(db_models.ClassroomCourse).filter(
                    db_models.ClassroomCourse.classroom_id == classroom_id,
                    db_models.ClassroomCourse.course_id == target_course_id
                ).first()

            if not classroom_course and not classroom_training:
                return schemas.ApiResponse(
                    code="1002",
                    message="课程不在指定课堂中",
                    trace_id=str(uuid.uuid4())
                )
        
        # 获取Banner信息
        banner_data = crud.get_course_detail_banner(
            db=db, 
            course_id=target_course_id, 
            classroom_id=classroom_id,
            user_id=user_id,
            is_practice=is_practice,
            is_training=is_training
        )
        
        # 获取任务列表及进度
        tasks_data = crud.get_course_tasks_with_progress(
            db=db,
            course_id=target_course_id,
            user_id=user_id,
            user_role=user_role
        )
        
        # 获取技能标签及点亮状态
        skills_data = crud.get_course_skills_with_progress(
            db=db,
            course_id=target_course_id,
            user_id=user_id,
            user_role=user_role
        )
        
        # 获取学习统计
        learning_stats = crud.get_course_learning_stats(
            db=db,
            course_id=target_course_id,
            user_id=user_id if user_role == "student" else None
        )
        
        # 构建响应数据
        response_data = {
            "banner": banner_data,
            "tasks": tasks_data,
            "skills": skills_data,
            "learning_stats": learning_stats
        }
        
        # 实训课程特有功能
        if course and getattr(course, "course_type", None) == db_models.CourseTypeEnum.TRAINING:
            # 获取目录章节
            chapters = [
                {
                    "id": chapter.id,
                    "title": chapter.title,
                    "order_index": chapter.order_index,
                    "experiment_count": chapter.experiment_count,
                    "created_at": chapter.created_at
                }
                for chapter in course.chapters
            ]
            response_data["chapters"] = chapters
            
            # 学生端：获取作业列表
            if user_role == "student":
                assignments = crud.get_course_assignments(
                    db=db,
                    course_id=target_course_id,
                    classroom_id=classroom_id,
                    user_id=user_id
                )
                response_data["assignments"] = assignments
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/courses/{course_id}/skills", response_model=schemas.ApiResponse)
def get_course_skill_tags(
    course_id: int,
    user_id: Optional[int] = Query(None, description="用户ID"),
    user_role: str = Query("student", description="用户角色：teacher, student"),
    db: Session = Depends(get_db)
):
    """
    获取课程技能标签
    
    返回课程的所有技能标签及其点亮状态
    """
    try:
        # 验证课程是否存在
        course = crud.get_course(db, course_id=course_id)
        if not course:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 获取技能标签
        skills_data = crud.get_course_skills_with_progress(
            db=db,
            course_id=course_id,
            user_id=user_id,
            user_role=user_role
        )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=skills_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/courses/{course_id}/progress", response_model=schemas.ApiResponse)
def get_course_learning_progress(
    course_id: int,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    获取课程学习进度
    
    返回用户在该课程中的学习统计信息
    """
    try:
        # 验证课程是否存在
        course = crud.get_course(db, course_id=course_id)
        if not course:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 获取学习统计
        learning_stats = crud.get_course_learning_stats(
            db=db,
            course_id=course_id,
            user_id=user_id
        )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=learning_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/organization-tree", response_model=schemas.ApiResponse)
async def get_organization_tree(db: Session = Depends(get_db)):
    """获取组织架构树"""
    try:
        organization_tree = crud.get_organization_tree(db)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={"organization_tree": organization_tree}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取组织架构树失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取组织架构树失败: {str(e)}")


@router.get("/classrooms/{classroom_id}/courses/available", response_model=schemas.ApiResponse)
def get_available_courses_for_classroom(
    classroom_id: int,
    course_type: Optional[str] = Query(None, description="课程类型：practice, training, course_material"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    direction: Optional[str] = Query(None, description="方向标签"),
    category: Optional[str] = Query(None, description="分类标签"),
    difficulty: Optional[str] = Query(None, description="难度级别"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取可添加到课堂的课程列表"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="无权限访问该课堂",
                trace_id=str(uuid.uuid4())
            )
        
        skip = (page - 1) * page_size
        courses, total = crud.get_courses_for_selection(
            db=db,
            classroom_id=classroom_id,
            course_type=course_type,
            keyword=keyword,
            direction=direction,
            category=category,
            difficulty=difficulty,
            skip=skip,
            limit=page_size,
            teacher_id=teacher_id
        )

        # 获取筛选标签
        filter_tags = crud.get_course_filter_tags_for_selection(db, course_type)

        # 转换为响应格式（支持Course和Practice两种类型）
        course_list = []
        for item in courses:
            # 判断是Course还是Practice
            if isinstance(item, db_models.Practice):
                # Practice对象，手动构建响应
                course_data = {
                    "id": item.id,
                    "title": item.title,
                    "cover_url": item.cover_url,
                    "direction": item.direction,
                    "category": item.category,
                    "difficulty": item.difficulty.value if item.difficulty else None,
                    "description": item.description,
                    "course_type": "PRACTICE",
                    "source": "practice",  # 标识来自practices表
                    "visibility": item.visibility.value if item.visibility else "PRIVATE",
                    "creator_id": item.creator_id
                }
                course_list.append(course_data)
            else:
                # Course对象，使用原有逻辑
                course_data = schemas.CourseSelectionResponse.model_validate(item)
                course_list.append(course_data.model_dump())
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": course_list,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                },
                "filter_tags": filter_tags
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


@router.post("/classrooms/{classroom_id}/courses/add-by-timetable", response_model=schemas.ApiResponse)
def add_courses_by_timetable(
    classroom_id: int,
    request: schemas.AddCoursesByTimetableRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """按课表添加课程"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        result = crud.add_courses_by_timetable(
            db=db,
            classroom_id=classroom_id,
            source_course_id=request.source_course_id,
            teacher_id=teacher_id,
            selected_modules=request.selected_modules
        )
        
        if result is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限，或源课程不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 转换课程数据
        course_list = []
        for course in result["added_courses"]:
            course_data = schemas.ClassroomCourseResponse.model_validate(course)
            course_list.append(course_data.model_dump())
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功按课表添加 {result['total_added']} 个课程模块",
            data={
                "added_courses": course_list,
                "source_course": {
                    "id": result["source_course"].id,
                    "title": result["source_course"].title,
                    "course_type": result["source_course"].course_type.value
                },
                "selected_modules": result["selected_modules"],
                "total_added": result["total_added"],
                "message": f"已从课表 '{result['source_course'].title}' 添加 {result['total_added']} 个模块"
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

# 4.5.2 添加实践课程

@router.post("/classrooms/{classroom_id}/courses/add-practice", response_model=schemas.ApiResponse)
def add_practice_courses_to_classroom(
    classroom_id: int,
    request: schemas.AddPracticeCoursesRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加实践课程到课堂"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        added_courses = crud.add_practice_courses_to_classroom(
            db=db,
            classroom_id=classroom_id,
            practice_ids=request.course_ids,  # 前端传递course_ids，对应practices表的ID
            teacher_id=teacher_id,
            chapter_id=request.chapter_id
        )
        
        if added_courses is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        # 构建响应，手动添加 teacher_id
        course_list = []
        for course in added_courses:
            course_dict = {
                "id": course.id,
                "course_id": course.course_id,
                "classroom_id": course.classroom_id,
                "teacher_id": teacher_id,
                "deadline_at": course.deadline_at,
                "is_mandatory": course.is_mandatory,
                "status": course.teacher_publish_status.value if course.teacher_publish_status else "UNPUBLISHED",
                "teacher_publish_status": course.teacher_publish_status.value if course.teacher_publish_status else None
            }
            course_list.append(course_dict)
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功添加 {len(added_courses)} 个实践课程",
            data={
                "added_courses": course_list,
                "success_count": len(added_courses)
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

# 4.5.3 添加实训课程

@router.post("/classrooms/{classroom_id}/courses/add-training", response_model=schemas.ApiResponse)
def add_training_courses_to_classroom(
    classroom_id: int,
    request: schemas.AddTrainingCoursesRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加实训课程到课堂"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        added_courses = crud.add_training_courses_to_classroom(
            db=db,
            classroom_id=classroom_id,
            course_ids=request.course_ids,
            teacher_id=teacher_id,
            chapter_id=request.chapter_id
        )
        
        if added_courses is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        course_list = [schemas.ClassroomCourseResponse.model_validate(course).model_dump() 
                      for course in added_courses]
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功添加 {len(added_courses)} 个实训课程",
            data={
                "added_courses": course_list,
                "success_count": len(added_courses)
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

# 4.6 课程发布相关API


@router.post("/classrooms/{classroom_id}/courses/{course_id}/publish", response_model=schemas.ApiResponse)
def publish_single_course(
    classroom_id: int,
    course_id: int,
    request: schemas.CoursePublishSettings,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发布单个课程"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        # 验证截止时间格式和业务规则
        classroom = db.query(db_models.Classroom).filter(db_models.Classroom.id == classroom_id).first()
        if not classroom:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 检查截止时间是否超过课堂结束时间
        if request.deadline_at.date() > classroom.end_date:
            return schemas.ApiResponse(
                code="1003",
                message="课程截止时间不能超过课堂结束时间",
                trace_id=str(uuid.uuid4())
            )
        
        # 如果课堂剩余时间少于7天，使用课堂结束时间作为默认截止时间
        remaining_days = (classroom.end_date - datetime.now(timezone.utc).date()).days
        if remaining_days < 7 and request.deadline_at.date() > classroom.end_date:
            request.deadline_at = classroom.end_date
        
        settings = request.model_dump()
        classroom_course = crud.publish_single_course(
            db=db,
            classroom_id=classroom_id,
            course_id=course_id,
            teacher_id=teacher_id,
            settings=settings
        )
        
        if classroom_course is None:
            return schemas.ApiResponse(
                code="1001",
                message="课程不存在、已发布或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        course_data = schemas.ClassroomCourseResponse.model_validate(classroom_course)
        
        return schemas.ApiResponse(
            code="0000",
            message="课程发布成功",
            data=course_data.model_dump()
        )
    except ValueError as ve:
        return schemas.ApiResponse(
            code="1003",
            message=str(ve),
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


@router.post("/classrooms/{classroom_id}/courses/publish-batch", response_model=schemas.ApiResponse)
def publish_batch_courses(
    classroom_id: int,
    request: schemas.PublishBatchCoursesRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """一键发布（批量发布课程）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        # 验证截止时间
        classroom = db.query(db_models.Classroom).filter(db_models.Classroom.id == classroom_id).first()
        if not classroom:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        
        if request.settings.deadline_at.date() > classroom.end_date:
            return schemas.ApiResponse(
                code="1003",
                message="课程截止时间不能超过课堂结束时间",
                trace_id=str(uuid.uuid4())
            )
        
        settings = request.settings.model_dump()
        updated_count = crud.publish_batch_courses(
            db=db,
            classroom_id=classroom_id,
            course_ids=request.course_ids,
            teacher_id=teacher_id,
            settings=settings
        )
        
        if updated_count is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功发布 {updated_count} 个课程",
            data={
                "success_count": updated_count,
                "failed_count": len(request.course_ids) - updated_count
            }
        )
    except ValueError as ve:
        return schemas.ApiResponse(
            code="1003",
            message=str(ve),
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


@router.post("/classrooms/{classroom_id}/courses/publish-chapter", response_model=schemas.ApiResponse)
def publish_chapter_courses(
    classroom_id: int,
    request: schemas.PublishChapterCoursesRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """按章节发布课程（一键发布同章节下的所有未发布课程）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        # 验证截止时间
        classroom = db.query(db_models.Classroom).filter(db_models.Classroom.id == classroom_id).first()
        if not classroom:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        
        if request.settings.deadline_at.date() > classroom.end_date:
            return schemas.ApiResponse(
                code="1003",
                message="课程截止时间不能超过课堂结束时间",
                trace_id=str(uuid.uuid4())
            )
        
        settings = request.settings.model_dump()
        updated_count = crud.publish_chapter_courses(
            db=db,
            classroom_id=classroom_id,
            chapter_title=request.chapter_title,
            teacher_id=teacher_id,
            settings=settings
        )
        
        if updated_count is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功发布章节 '{request.chapter_title}' 下的 {updated_count} 个课程",
            data={
                "success_count": updated_count,
                "chapter_title": request.chapter_title,
                "message": f"章节 '{request.chapter_title}' 下的课程已成功发布" if updated_count > 0 else f"章节 '{request.chapter_title}' 下没有需要发布的课程"
            }
        )
    except ValueError as ve:
        return schemas.ApiResponse(
            code="1003",
            message=str(ve),
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


@router.post("/classrooms/{classroom_id}/courses/publish-all", response_model=schemas.ApiResponse)
def publish_all_courses(
    classroom_id: int,
    request: schemas.PublishAllCoursesRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """全部发布（发布课堂中所有未发布的课程）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        # 验证截止时间
        classroom = db.query(db_models.Classroom).filter(db_models.Classroom.id == classroom_id).first()
        if not classroom:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        
        if request.settings.deadline_at.date() > classroom.end_date:
            return schemas.ApiResponse(
                code="1003",
                message="课程截止时间不能超过课堂结束时间",
                trace_id=str(uuid.uuid4())
            )
        
        settings = request.settings.model_dump()
        updated_count = crud.publish_all_courses(
            db=db,
            classroom_id=classroom_id,
            teacher_id=teacher_id,
            settings=settings
        )
        
        if updated_count is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功发布 {updated_count} 个课程",
            data={
                "success_count": updated_count,
                "message": "所有未发布的课程已成功发布" if updated_count > 0 else "没有需要发布的课程"
            }
        )
    except ValueError as ve:
        return schemas.ApiResponse(
            code="1003",
            message=str(ve),
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

# 增强版课堂课程列表（带统计信息）

@router.patch("/classroom-courses/{classroom_course_id}/title", response_model=schemas.ApiResponse)
def rename_classroom_course(
    classroom_course_id: int,
    title: str = Query(..., description="新课程标题"),
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重命名课堂中的课程"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        classroom_course = crud.rename_classroom_course(db, classroom_course_id, title, teacher_id)
        
        if classroom_course is None:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        course_data = schemas.ClassroomCourseResponse.model_validate(classroom_course)
        
        return schemas.ApiResponse(
            code="0000",
            message="课程重命名成功",
            data=course_data.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.7.1.6 课程设置

@router.patch("/classroom-courses/{classroom_course_id}/settings", response_model=schemas.ApiResponse)
def update_course_settings(
    classroom_course_id: int,
    settings: schemas.CourseSettingsUpdate,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新课程设置"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        # 验证截止时间不能早于当前时间（如果课程已发布）
        classroom_course = db.query(db_models.ClassroomCourse).filter(
            db_models.ClassroomCourse.id == classroom_course_id
        ).first()
        
        if classroom_course and classroom_course.teacher_publish_status != db_models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED:
            if settings.deadline_at and settings.deadline_at < datetime.now(timezone.utc):
                return schemas.ApiResponse(
                    code="1003",
                    message="已发布课程的截止时间不能早于当前时间",
                    trace_id=str(uuid.uuid4())
                )
        
        updated_course = crud.update_course_settings(
            db, 
            classroom_course_id, 
            settings.model_dump(exclude_unset=True), 
            teacher_id
        )
        
        if updated_course is None:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        course_data = schemas.ClassroomCourseResponse.model_validate(updated_course)
        
        return schemas.ApiResponse(
            code="0000",
            message="课程设置更新成功",
            data=course_data.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.7.1.7 课程删除

@router.get("/classroom-courses/{classroom_course_id}/settings", response_model=schemas.ApiResponse)
def get_course_settings(
    classroom_course_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课程设置详情"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        classroom_course = db.query(db_models.ClassroomCourse).options(
            joinedload(db_models.ClassroomCourse.course),
            joinedload(db_models.ClassroomCourse.practice)
        ).filter(
            db_models.ClassroomCourse.id == classroom_course_id
        ).first()
        
        if not classroom_course:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_course.classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="无权限访问",
                trace_id=str(uuid.uuid4())
            )
        
        # 确定课程类型（支持 course 和 practice 两种类型）
        if classroom_course.course:
            course_type = classroom_course.course.course_type.value if classroom_course.course.course_type else "PRACTICE"
        elif classroom_course.practice:
            course_type = "PRACTICE"
        else:
            course_type = "UNKNOWN"

        # 构建设置数据
        settings_data = {
            "id": classroom_course.id,
            "classroom_course_id": classroom_course.id,
            "deadline_at": classroom_course.deadline_at,
            "is_mandatory": classroom_course.is_mandatory,
            "allow_late_submission": classroom_course.allow_late_submission,
            "late_submission_deduction_points": classroom_course.late_submission_deduction_points,
            "total_score": classroom_course.total_score,
            "publicize_grades": classroom_course.publicize_grades,
            "publicize_answers_after_completion": classroom_course.publicize_answers_after_completion,
            "course_type": course_type,
            "published_at": classroom_course.published_at,
            "status": classroom_course.teacher_publish_status.value if classroom_course.teacher_publish_status else "UNPUBLISHED"
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=settings_data
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 成绩查看和作业点评相关API ====================


@router.post("/classroom-courses/{classroom_course_id}/submit-assignment", response_model=schemas.ApiResponse)
def submit_training_assignment(
    classroom_course_id: int,
    request: schemas.AssignmentSubmissionRequest,
    student_id: int = Query(..., description="学生ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """学生提交实训作业"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",), forbidden_detail="无权提交他人作业")
        if not request.design_files and not request.experiment_reports:
            raise HTTPException(status_code=400, detail="至少需要提交一个文件")
        
        # 转换文件格式
        design_files = [file.dict() for file in request.design_files]
        experiment_reports = [file.dict() for file in request.experiment_reports]
        
        submitted_progress = crud.submit_training_assignment(
            db, classroom_course_id, student_id, design_files, experiment_reports
        )
        
        if submitted_progress is None:
            raise HTTPException(status_code=404, detail="课程不存在")
        
        return schemas.ApiResponse(
            code="0000",
            message="作业提交成功",
            data={
                "student_id": student_id,
                "submission_status": submitted_progress.training_submission_status.value,
                "submission_time": submitted_progress.last_submission_at,
                "design_files_count": len(design_files),
                "experiment_reports_count": len(experiment_reports)
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"学生提交实训作业失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"学生提交实训作业失败: {str(e)}")


@router.get("/classroom-courses/{classroom_course_id}/my-assignment", response_model=schemas.ApiResponse)
def get_my_assignment_detail(
    classroom_course_id: int,
    student_id: int = Query(..., description="学生ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """学生查看自己的作业详情"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",), forbidden_detail="无权查看他人作业")
        # 获取学生进度记录
        progress = db.query(db_models.StudentCourseProgress).options(
            joinedload(db_models.StudentCourseProgress.classroom_course),
            joinedload(db_models.StudentCourseProgress.graded_by_teacher)
        ).filter(
            db_models.StudentCourseProgress.classroom_course_id == classroom_course_id,
            db_models.StudentCourseProgress.student_id == student_id
        ).first()
        
        if not progress:
            # 如果没有进度记录，返回初始状态
            classroom_course = db.query(db_models.ClassroomCourse).options(
                joinedload(db_models.ClassroomCourse.course)
            ).filter(
                db_models.ClassroomCourse.id == classroom_course_id
            ).first()
            
            if not classroom_course:
                raise HTTPException(status_code=404, detail="课程不存在")
            
            return schemas.ApiResponse(
                code="0000",
                message="获取成功",
                data={
                    "submission_status": "NOT_STARTED",
                    "submission_time": None,
                    "design_files": [],
                    "experiment_reports": [],
                    "grading_status": "NOT_GRADED",
                    "score": None,
                    "teacher_feedback": None,
                    "is_excellent": False,
                    "graded_at": None,
                    "can_submit": True
                }
            )
        
        # 解析作业文件
        design_files = []
        experiment_reports = []
        
        if progress.training_assignment_files:
            try:
                import json
                files_data = json.loads(progress.training_assignment_files)
                design_files = files_data.get("design_files", [])
                experiment_reports = files_data.get("experiment_reports", [])
            except:
                pass
        
        # 判断是否可以继续提交（点评前可以重复提交）
        can_submit = not progress.graded_at
        
        assignment_detail = {
            "submission_status": progress.training_submission_status.value,
            "submission_time": progress.last_submission_at,
            "design_files": design_files,
            "experiment_reports": experiment_reports,
            "grading_status": "GRADED" if progress.graded_at else "NOT_GRADED",
            "score": progress.final_calculated_score if progress.graded_at else None,
            "teacher_feedback": progress.teacher_feedback,
            "is_excellent": progress.is_excellent_work,
            "graded_at": progress.graded_at,
            "graded_by_teacher_name": progress.graded_by_teacher.full_name if progress.graded_by_teacher else None,
            "can_submit": can_submit
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data=assignment_detail
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生作业详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取学生作业详情失败: {str(e)}")

# ==================== 考试阅卷相关API ====================


# ==================== 教学资源文件服务API ====================

@router.get("/files/resources/{resource_id}")
def get_resource_file(resource_id: int, db: Session = Depends(get_db)):
    """
    根据抽象的resource_id提供教学资源文件访问

    此端点隐藏了ziyuan的内部结构，只通过resource_id提供访问，
    增强了安全性并提供了更好的抽象层。
    """
    try:
        # 查询资源信息
        resource = db.query(db_models.CourseResource).filter(
            db_models.CourseResource.id == resource_id
        ).first()

        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")

        # 获取资源在ziyuan中的实际路径
        ziyuan_base = Path("ziyuan")

        # 尝试多种可能的路径格式
        possible_paths = []

        # 如果resource.url包含ziyuan路径，直接使用
        if hasattr(resource, 'url') and resource.url:
            if 'ziyuan/' in resource.url:
                rel_path = resource.url.split('ziyuan/')[1]
                possible_paths.append(ziyuan_base / rel_path)
            elif resource.url.startswith('/'):
                # 处理绝对路径
                possible_paths.append(Path(resource.url[1:]))  # 去掉开头的/
            else:
                # 处理相对路径
                possible_paths.append(ziyuan_base / resource.url)

        # 如果上面的方法都不行，尝试基于course_id和文件名构建路径
        if not possible_paths:
            course = db.query(db_models.Course).filter(
                db_models.Course.id == resource.course_id
            ).first()

            if course and hasattr(course, 'title'):
                # 尝试课程资源目录
                course_dir = ziyuan_base / "课程资源" / course.title
                possible_paths.append(course_dir / resource.title)

                # 尝试其他常见目录结构
                possible_paths.append(ziyuan_base / "课程资源" / course.title / "assets" / resource.title)
                possible_paths.append(ziyuan_base / "实训资源" / course.title / resource.title)

        # 查找实际存在的文件
        actual_file_path = None
        for path in possible_paths:
            if path.exists() and path.is_file():
                actual_file_path = path
                break

        if not actual_file_path:
            logger.error(f"资源文件不存在: resource_id={resource_id}, 尝试的路径: {[str(p) for p in possible_paths]}")
            raise HTTPException(status_code=404, detail="资源文件不存在")

        # 检查文件是否可读
        if not os.access(actual_file_path, os.R_OK):
            logger.error(f"资源文件无读取权限: {actual_file_path}")
            raise HTTPException(status_code=403, detail="无权访问此资源")

        # 返回文件
        from fastapi.responses import FileResponse

        # 根据文件扩展名设置媒体类型
        content_type = "application/octet-stream"  # 默认
        file_ext = actual_file_path.suffix.lower()

        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.json': 'application/json'
        }

        if file_ext in content_types:
            content_type = content_types[file_ext]

        # 对于内联预览的文件，使用inline disposition
        disposition = "inline" if file_ext in ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.txt', '.md', '.json'] else "attachment"

        # 为中文文件名进行URL编码
        from urllib.parse import quote
        encoded_filename = quote(resource.title.encode('utf-8'), safe='')

        return FileResponse(
            path=str(actual_file_path),
            media_type=content_type,
            filename=resource.title,
            headers={"Content-Disposition": f'{disposition}; filename*=UTF-8\'\'{encoded_filename}'}
        )

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取资源文件失败: resource_id={resource_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.get("/courses/{course_id}/resource-statistics", response_model=schemas.ApiResponse)
def get_course_resource_statistics(course_id: int, db: Session = Depends(get_db)):
    """
    获取课程资源统计信息

    提供课程教学资源的详细统计数据，包括：
    - 各类资源数量统计
    - 文件大小统计
    - 下载次数统计
    """
    try:
        # 验证课程存在
        course = crud.get_course(db, course_id=course_id)
        if course is None:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在",
                trace_id=str(uuid.uuid4())
            )

        # 获取资源统计数据
        resources = db.query(db_models.CourseResource).filter(
            db_models.CourseResource.course_id == course_id
        ).all()

        # 计算统计信息
        statistics = {
            "total_count": len(resources),
            "total_size": sum(getattr(r, 'file_size', 0) or 0 for r in resources),
            "by_type": {},
            "by_downloadable": {
                "downloadable": 0,
                "preview_only": 0
            },
            "download_stats": {
                "total_downloads": sum(getattr(r, 'download_count', 0) or 0 for r in resources),
                "avg_downloads_per_resource": 0
            }
        }

        # 按类型统计
        type_counts = {}
        downloadable_count = 0
        preview_only_count = 0

        for resource in resources:
            # 类型统计
            res_type = getattr(resource, 'resource_type', 'unknown')
            type_counts[res_type] = type_counts.get(res_type, 0) + 1

            # 下载权限统计
            if getattr(resource, 'can_download', True):
                downloadable_count += 1
            else:
                preview_only_count += 1

        statistics["by_type"] = type_counts
        statistics["by_downloadable"]["downloadable"] = downloadable_count
        statistics["by_downloadable"]["preview_only"] = preview_only_count

        # 计算平均下载次数
        if statistics["total_count"] > 0:
            statistics["download_stats"]["avg_downloads_per_resource"] = round(
                statistics["download_stats"]["total_downloads"] / statistics["total_count"], 2
            )

        # 便捷统计（前端常用）
        statistics["quick_stats"] = {
            "pdf_count": type_counts.get('pdf', 0),
            "ppt_count": type_counts.get('ppt', 0) + type_counts.get('pptx', 0),
            "video_count": sum(type_counts.get(t, 0) for t in ['mp4', 'avi', 'mov', 'video']),
            "document_count": sum(type_counts.get(t, 0) for t in ['doc', 'docx', 'txt', 'md', 'markdown']),
            "spreadsheet_count": sum(type_counts.get(t, 0) for t in ['xls', 'xlsx']),
            "image_count": sum(type_counts.get(t, 0) for t in ['jpg', 'jpeg', 'png', 'gif']),
            "other_count": sum(count for t, count in type_counts.items()
                             if t not in ['pdf', 'ppt', 'pptx', 'mp4', 'avi', 'mov', 'video',
                                        'doc', 'docx', 'txt', 'md', 'markdown',
                                        'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif'])
        }

        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data=statistics
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课程资源统计失败: course_id={course_id}, error={str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


# ==================== 教学资源文件服务API ====================


