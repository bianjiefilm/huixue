"""
课堂管理端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import uuid
import logging
from datetime import datetime, timezone, timedelta

# 修正的导入路径
from app.core.database import get_db, engine, Base
from app.models import models as db_models  # 避免与FastAPI的models冲突
from app.crud import crud
from app.schemas import schemas
from app.schemas.classroom_schemas import (
    ClassroomQueryParams, ClassroomCreate, ClassroomUpdate,
    ClassroomResponse, ClassroomListResponse, AddStudentRequest
)
from app.api.deps import get_current_user_role
from app.core.permissions import Permission, Role, PermissionChecker
from app.core.security import get_current_user
from app.core.identity import resolve_scoped_id, require_owner_or_admin
from app.core.validators import sanitize_html
from app.utils.file_manager import file_manager

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    tags=['classrooms']
)


def _get_training_classroom_course(db: Session, classroom_id: int, training_id: int):
    """Return the classroom course row used by BI/training grading.

    ClassroomTraining stores the product training id, while submissions are
    recorded against StudentCourseProgress.classroom_course_id.
    """
    classroom_training = db.query(db_models.ClassroomTraining).filter(
        db_models.ClassroomTraining.classroom_id == classroom_id,
        db_models.ClassroomTraining.training_id == training_id,
    ).first()
    if not classroom_training:
        return None

    training = db.query(db_models.Training).filter(
        db_models.Training.id == training_id
    ).first()
    if not training:
        return None

    return db.query(db_models.ClassroomCourse).join(
        db_models.Course,
        db_models.ClassroomCourse.course_id == db_models.Course.id,
    ).filter(
        db_models.ClassroomCourse.classroom_id == classroom_id,
        db_models.Course.course_type == db_models.CourseTypeEnum.TRAINING,
        db_models.Course.title.in_([
            training.title,
            f"[实训]{training.title}",
            f"【实训】{training.title}",
        ]),
    ).first()


def _is_ended(classroom) -> bool:
    """检查课堂是否已结束。兼容 SQLite(存字符串) 和 PostgreSQL(存枚举)"""
    s = classroom.status
    return s == db_models.ClassroomStatusEnum.ENDED or (isinstance(s, str) and s == "ENDED")


def _jwt_user_id_and_role(current_user: dict) -> tuple[Optional[int], str]:
    """Extract the authenticated identity from the JWT dependency payload."""
    if not current_user:
        return None, ""

    if isinstance(current_user, dict):
        user_id = current_user.get("user_id") or current_user.get("id")
        role = current_user.get("role")
        if not role:
            roles = current_user.get("roles") or []
            role = roles[0] if roles else None
        if current_user.get("is_superuser"):
            role = role or "admin"
    else:
        user_id = getattr(current_user, "id", None)
        role = getattr(current_user, "role", None)
        if getattr(current_user, "is_superuser", False):
            role = role or "admin"

    return user_id, (role or "").lower()


def _require_classroom_detail_access(
    db: Session,
    classroom,
    user_id: Optional[int],
    role: str,
) -> None:
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证")

    if role == "admin":
        return

    if role == "teacher":
        if classroom.teacher_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此课堂")
        return

    if role == "student":
        student_in_classroom = db.query(db_models.ClassroomStudent).filter(
            db_models.ClassroomStudent.classroom_id == classroom.id,
            db_models.ClassroomStudent.student_id == user_id
        ).first()
        if not student_in_classroom:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此课堂")
        return

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此课堂")


@router.get("/classrooms", response_model=schemas.ApiResponse)
def get_classrooms(
    params: ClassroomQueryParams = Depends(),
    user_role: str = Query("teacher", description="兼容旧前端参数；授权以JWT角色为准"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取课堂列表
    - 如果指定teacher_id且不指定status，返回按状态分组的课堂列表
    - 如果同时指定teacher_id和status，返回指定状态的课堂列表  
    - 如果不指定teacher_id，返回所有课堂的分页列表
    """
    try:
        jwt_user_id, jwt_role = _jwt_user_id_and_role(current_user)
        requested_teacher_id = params.teacher_id

        if jwt_user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证")

        if jwt_role == "admin":
            teacher_id = requested_teacher_id
        elif jwt_role == "teacher":
            if requested_teacher_id is not None and requested_teacher_id != jwt_user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看其他教师课堂")
            teacher_id = jwt_user_id
        elif jwt_role == "student":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="学生请使用学生课堂接口")
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问课堂列表")
        
        if teacher_id and not params.status:
            # 按状态分组返回课堂列表
            classrooms_by_status = crud.get_classrooms_by_status(db, teacher_id)
            return schemas.ApiResponse(
                code="0000",
                message="success",
                data=classrooms_by_status.model_dump()
            )
        elif teacher_id and params.status:
            # 返回指定状态的课堂
            classrooms_by_status = crud.get_classrooms_by_status(db, teacher_id)
            
            if params.status == "ongoing":
                filtered_classrooms = classrooms_by_status.ongoing
            elif params.status == "upcoming":
                filtered_classrooms = classrooms_by_status.upcoming
            elif params.status == "ended":
                filtered_classrooms = classrooms_by_status.ended
            else:
                return schemas.ApiResponse(
                    code="1001",
                    message="无效的状态参数",
                    trace_id=str(uuid.uuid4())
                )
            
            # 分页处理
            skip = (params.page - 1) * params.page_size
            total = len(filtered_classrooms)
            paginated_classrooms = filtered_classrooms[skip:skip + params.page_size]
            
            return schemas.ApiResponse(
                code="0000",
                message="success",
                data={
                    "list": [classroom.model_dump() for classroom in paginated_classrooms],
                    "meta": {
                        "total": total,
                        "page": params.page,
                        "page_size": params.page_size
                    }
                }
            )
        else:
            # 原有逻辑：返回所有课堂的分页列表
            skip = (params.page - 1) * params.page_size
            classrooms, total = crud.get_classrooms(
                db=db,
                teacher_id=teacher_id,
                skip=skip,
                limit=params.page_size
            )
            
            classroom_list = [schemas.ClassroomDetailResponse.model_validate(classroom) for classroom in classrooms]
            
            return schemas.ApiResponse(
                code="0000",
                message="success",
                data={
                    "list": [classroom.model_dump() for classroom in classroom_list],
                    "meta": {
                        "total": total,
                        "page": params.page,
                        "page_size": params.page_size
                    }
                }
            )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/classrooms/{classroom_id}", response_model=schemas.ApiResponse)
def get_classroom_detail(
    classroom_id: int,
    enhanced: bool = Query(False, description="是否返回增强版详情"),
    user_id: Optional[int] = Query(None, description="兼容旧前端参数；授权以JWT用户为准"),
    user_role: str = Query("teacher", description="兼容旧前端参数；授权以JWT角色为准"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    课堂详情
    - enhanced=true: 返回包含统计信息的增强版详情
    - enhanced=false: 返回基础详情
    """
    try:
        # 权限检查：检查课堂是否存在
        classroom = crud.get_classroom(db, classroom_id=classroom_id)
        if classroom is None:
            raise HTTPException(status_code=404, detail="课堂不存在")

        jwt_user_id, jwt_role = _jwt_user_id_and_role(current_user)
        _require_classroom_detail_access(db, classroom, jwt_user_id, jwt_role)
        
        if enhanced:
            try:
                classroom_detail = crud.get_classroom_detail_enhanced(db, classroom_id)
                return schemas.ApiResponse(
                    code="0000",
                    message="success",
                    data=classroom_detail.model_dump()
                )
            except HTTPException:
                raise
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                return schemas.ApiResponse(
                    code="2000",
                    message=f"增强版详情获取失败: {str(e)}",
                    data={"error_details": error_details},
                    trace_id=str(uuid.uuid4())
                )
        else:
            classroom = crud.get_classroom(db, classroom_id=classroom_id)
            if classroom is None:
                return schemas.ApiResponse(
                    code="1002",
                    message="课堂不存在",
                    trace_id=str(uuid.uuid4())
                )
            
            classroom_detail = schemas.ClassroomDetailResponse.model_validate(classroom)
            
            return schemas.ApiResponse(
                code="0000",
                message="success",
                data=classroom_detail.model_dump()
            )
    except HTTPException:
        # 重新抛出HTTP异常，保持正确的状态码
        raise
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/classrooms", response_model=schemas.ApiResponse)
def create_classroom(
    classroom: schemas.ClassroomCreate,
    teacher_id: Optional[int] = Query(None, description="教师ID（向后兼容，优先使用token中的user_id）"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建课堂"""
    # ── RBAC: 仅教师或管理员可创建 ──
    user_roles = current_user.get("roles", [])
    if not any(r in ("teacher", "admin") for r in user_roles) and not current_user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅教师或管理员可创建课堂")
    try:
        # 优先使用 token 中的 user_id；管理员可代操作
        actual_teacher_id = current_user["user_id"]
        if teacher_id and teacher_id != actual_teacher_id and current_user.get("is_superuser"):
            actual_teacher_id = teacher_id
        db_classroom = crud.create_classroom(db=db, classroom=classroom, teacher_id=actual_teacher_id)
        
        if db_classroom is None:
            # 检查具体错误原因
            existing = crud.get_classrooms(db, teacher_id=teacher_id)
            for existing_classroom, _ in [existing]:
                for c in existing_classroom:
                    if c.name == classroom.name:
                        return schemas.ApiResponse(
                            code="1005",
                            message="课堂名称已存在",
                            trace_id=str(uuid.uuid4())
                        )
            
            return schemas.ApiResponse(
                code="1006",
                message="业务校验失败：结束日期必须晚于开始日期",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="课堂创建成功",
            data={"classroom_id": db_classroom.id}
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.put("/classrooms/{classroom_id}", response_model=schemas.ApiResponse)
def update_classroom(
    classroom_id: int,
    classroom_update: schemas.ClassroomUpdateRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID（向后兼容）"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """编辑课堂"""
    # ── RBAC: 仅教师或管理员可编辑 ──
    user_roles = current_user.get("roles", [])
    if not any(r in ("teacher", "admin") for r in user_roles) and not current_user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅教师或管理员可编辑课堂")
    try:
        actual_teacher_id = current_user["user_id"]
        if teacher_id and teacher_id != actual_teacher_id and current_user.get("is_superuser"):
            actual_teacher_id = teacher_id

        # ── Lifecycle Guard: 已结束课堂不可编辑 ──
        classroom_obj = crud.get_classroom(db, classroom_id)
        if classroom_obj and _is_ended(classroom_obj):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已结束的课堂不可修改")

        if not crud.check_classroom_teacher_permission(db, classroom_id, actual_teacher_id):
            return schemas.ApiResponse(
                code="1003",
                message="无权编辑此课堂",
                trace_id=str(uuid.uuid4())
            )
        
        result = crud.update_classroom(db, classroom_id, classroom_update, actual_teacher_id)
        
        if result is None:
            return schemas.ApiResponse(
                code="1003",
                message="权限不足或课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        elif isinstance(result, str):
            # 返回的是错误消息
            return schemas.ApiResponse(
                code="1006",
                message=result,
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="课堂更新成功",
            data={"classroom_id": result.id}
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.delete("/classrooms/{classroom_id}", response_model=schemas.ApiResponse)
def delete_classroom(
    classroom_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID（向后兼容）"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除课堂（软删除）"""
    # ── RBAC: 仅教师或管理员可删除 ──
    user_roles = current_user.get("roles", [])
    if not any(r in ("teacher", "admin") for r in user_roles) and not current_user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅教师或管理员可删除课堂")
    try:
        actual_teacher_id = current_user["user_id"]
        if teacher_id and teacher_id != actual_teacher_id and current_user.get("is_superuser"):
            actual_teacher_id = teacher_id
        if not crud.check_teacher_classroom_permission(db, classroom_id, actual_teacher_id):
            return schemas.ApiResponse(
                code="1003",
                message="权限不足或课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        
        classroom = crud.get_classroom(db, classroom_id)
        if not classroom:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )

        # ── Lifecycle Guard: 已结束课堂不可删除 ──
        if _is_ended(classroom):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已结束的课堂不可删除")
        
        # 检查是否已经是软删除状态
        if classroom.deleted_at:
            return schemas.ApiResponse(
                code="1007",
                message="课堂已删除",
                trace_id=str(uuid.uuid4())
            )

        # 检查是否有已完成的课程
        classroom_courses = crud.get_classroom_course_status_summary(db, classroom_id)
        if classroom_courses.get('completed', 0) > 0:
            return schemas.ApiResponse(
                code="1006",
                message="课堂内有已完成的课程，无法删除",
                trace_id=str(uuid.uuid4())
            )

        # 删除课堂相关文件（移到回收站）
        file_manager.delete_entity_files("classroom_disk", classroom_id)

        # 执行软删除
        classroom.deleted_at = datetime.now(timezone.utc)
        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message="课堂删除成功"
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/my-classrooms", response_model=schemas.ApiResponse)
def get_my_classrooms(
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """我的课堂 - 按状态分组显示"""
    user_id = current_user.get("user_id") if isinstance(current_user, dict) else None
    role = (current_user.get("role") if isinstance(current_user, dict) else None)
    if role is None and isinstance(current_user, dict):
        roles = current_user.get("roles") or []
        role = roles[0] if roles else None
    role = role or "student"

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    if role not in ("teacher", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"需要角色 ('teacher', 'admin'), 当前角色 {role}",
        )

    if role == "admin":
        effective_teacher_id = teacher_id or user_id
    else:
        if teacher_id is not None and teacher_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="query teacher_id 与 JWT 不符",
            )
        effective_teacher_id = user_id

    try:
        classrooms_by_status = crud.get_classrooms_by_status(db, effective_teacher_id)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=classrooms_by_status.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 筛选标签和统计

@router.get("/classrooms/{classroom_id}/courses", response_model=schemas.ApiResponse)
def get_classroom_courses(
    classroom_id: int,
    status: Optional[str] = Query(None, description="状态筛选：all, unpublished, learning, makeup, completed"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: Optional[int] = Query(None, description="教师ID（用于权限验证）"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课堂中的课程列表（支持状态筛选）"""
    try:
        # 先获取课堂信息以拿到 teacher_id
        classroom = crud.get_classroom(db, classroom_id=classroom_id)
        if not classroom:
            return schemas.ApiResponse(
                code="404",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )

        jwt_user_id, jwt_role = _jwt_user_id_and_role(current_user)
        _require_classroom_detail_access(db, classroom, jwt_user_id, jwt_role)

        skip = (page - 1) * page_size
        courses, total = crud.get_classroom_courses_with_stats(
            db=db,
            classroom_id=classroom_id,
            status=status,
            keyword=keyword,
            skip=skip,
            limit=page_size
        )

        # 获取状态统计
        summary = crud.get_classroom_course_status_summary(db, classroom_id)

        # 转换为响应格式
        course_list = []
        for classroom_course in courses:
            # 注入 teacher_id
            classroom_course['teacher_id'] = classroom.teacher_id
            
            course_data = schemas.ClassroomCourseDetailResponse.model_validate(classroom_course)
            course_list.append(course_data.model_dump())
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "courses": course_list,
                "summary": summary,
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


@router.delete("/classrooms/{classroom_id}/courses", response_model=schemas.ApiResponse)
def remove_courses_from_classroom(
    classroom_id: int,
    request: schemas.CourseBatchOperationRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """批量删除课程（仅限未发布的课程）"""
    try:
        success = crud.delete_classroom_courses(
            db=db,
            classroom_id=classroom_id,
            course_ids=request.course_ids,
            teacher_id=teacher_id
        )
        
        if not success:
            return schemas.ApiResponse(
                code="1001",
                message="删除失败，课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="课程删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/classrooms/{classroom_id}/courses/summary", response_model=schemas.ApiResponse)
def get_classroom_courses_summary(
    classroom_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID（用于权限验证）"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课堂课程状态统计"""
    try:
        classroom = crud.get_classroom(db, classroom_id=classroom_id)
        if not classroom:
            return schemas.ApiResponse(
                code="404",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )

        jwt_user_id, jwt_role = _jwt_user_id_and_role(current_user)
        _require_classroom_detail_access(db, classroom, jwt_user_id, jwt_role)

        summary = crud.get_classroom_course_status_summary(db, classroom_id)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=summary
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 学生端课程状态API

@router.get("/classrooms/{classroom_id}/courses/enhanced", response_model=schemas.ApiResponse)
def get_classroom_courses_enhanced(
    classroom_id: int,
    status: Optional[str] = Query(None, description="状态筛选：all, unpublished, learning, makeup, completed"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: Optional[int] = Query(None, description="教师ID（用于权限验证）"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取带统计信息的课堂课程列表"""
    try:
        classroom = crud.get_classroom(db, classroom_id=classroom_id)
        if not classroom:
            return schemas.ApiResponse(
                code="404",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )

        jwt_user_id, jwt_role = _jwt_user_id_and_role(current_user)
        _require_classroom_detail_access(db, classroom, jwt_user_id, jwt_role)

        skip = (page - 1) * page_size
        courses, total = crud.get_classroom_courses_with_stats(
            db=db,
            classroom_id=classroom_id,
            status=status,
            keyword=keyword,
            skip=skip,
            limit=page_size
        )
        
        # 获取状态统计
        summary = crud.get_classroom_course_status_summary(db, classroom_id)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": courses,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                },
                "summary": summary
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


@router.post("/classrooms/{classroom_id}/courses/add-training", response_model=schemas.ApiResponse)
def add_training_to_classroom(
    classroom_id: int,
    request: schemas.AddTrainingCoursesRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID（向后兼容）"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加实训项目到课堂"""
    # ── RBAC ──
    user_roles = current_user.get("roles", [])
    if not any(r in ("teacher", "admin") for r in user_roles) and not current_user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅教师或管理员可添加课程")
    try:
        actual_teacher_id = current_user["user_id"]
        if teacher_id and teacher_id != actual_teacher_id and current_user.get("is_superuser"):
            actual_teacher_id = teacher_id

        # ── Lifecycle Guard ──
        classroom = crud.get_classroom(db, classroom_id)
        if classroom and _is_ended(classroom):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已结束的课堂不可添加课程")

        # 检查权限
        if not crud.check_teacher_classroom_permission(db, classroom_id, actual_teacher_id):
            return schemas.ApiResponse(
                code="1003",
                message="权限不足或课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 添加实训项目
        success_count = 0
        for training_id in request.course_ids:
            result = crud.add_training_to_classroom(
                db=db,
                classroom_id=classroom_id,
                training_id=training_id
            )
            if result:
                success_count += 1
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功添加 {success_count} 个实训项目",
            data={"success_count": success_count}
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/classrooms/{classroom_id}/chapters", response_model=schemas.ApiResponse)
def get_classroom_chapters(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课堂章节列表（用于一键发布）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        chapters = crud.get_classroom_chapters(db, classroom_id, teacher_id)
        
        if chapters is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "chapters": chapters,
                "total_chapters": len(chapters),
                "publishable_chapters": len([c for c in chapters if c["can_publish"]])
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

# ==================== 课堂管理API ====================


@router.get("/classrooms/{classroom_id}/management", response_model=schemas.ApiResponse)
def get_classroom_management(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课堂管理页面数据（包含目录结构、统计信息等）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        management_data = crud.get_classroom_management_data(db, classroom_id, teacher_id)
        
        if management_data is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=management_data
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/classrooms/{classroom_id}/catalog", response_model=schemas.ApiResponse)
def get_classroom_catalog(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课堂目录结构（章节和课程的层级关系）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        catalog = crud.get_classroom_catalog(db, classroom_id, teacher_id)
        
        if catalog is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={"catalog": catalog}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.7.1.1.1 添加章节

@router.post("/classrooms/{classroom_id}/chapters", response_model=schemas.ApiResponse)
def create_classroom_chapter(
    classroom_id: int,
    title: str = Query(..., description="章节标题"),
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加课堂章节"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        chapter = crud.create_classroom_chapter(db, classroom_id, title, teacher_id)
        
        if chapter is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        chapter_data = schemas.ClassroomChapterResponse.model_validate(chapter)
        
        return schemas.ApiResponse(
            code="0000",
            message="章节添加成功",
            data=chapter_data.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.7.1.1.2 重命名章节

@router.patch("/chapters/{chapter_id}", response_model=schemas.ApiResponse)
def update_chapter(
    chapter_id: int,
    title: str = Query(..., description="新章节标题"),
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重命名课堂章节"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        chapter = crud.update_classroom_chapter(db, chapter_id, title, teacher_id)
        
        if chapter is None:
            return schemas.ApiResponse(
                code="1002",
                message="章节不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        chapter_data = schemas.ClassroomChapterResponse.model_validate(chapter)
        
        return schemas.ApiResponse(
            code="0000",
            message="章节重命名成功",
            data=chapter_data.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.7.1.1.3 删除章节

@router.delete("/chapters/{chapter_id}", response_model=schemas.ApiResponse)
def delete_chapter(
    chapter_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除课堂章节（同时删除章节下的课程）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        success = crud.delete_classroom_chapter(db, chapter_id, teacher_id)
        
        if not success:
            return schemas.ApiResponse(
                code="1002",
                message="章节不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="章节删除成功",
            data={"message": "章节及其下的课程已删除"}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.7.1.4 调整排序

@router.patch("/classrooms/{classroom_id}/order", response_model=schemas.ApiResponse)
def update_classroom_order(
    classroom_id: int,
    request: schemas.CourseOrderRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """调整课程和章节的排序"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        success = crud.update_course_order(db, classroom_id, request.items, teacher_id)
        
        if not success:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="排序调整成功",
            data={"message": "课程和章节排序已更新"}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.7.1.5 课程重命名

@router.patch("/classroom-courses/{classroom_course_id}/rename", response_model=schemas.ApiResponse)
def rename_classroom_course(
    classroom_course_id: int,
    name: str = Query(..., description="新课程名称"),
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重命名课堂中的课程"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        # 检查权限并重命名
        success = crud.rename_classroom_course(db, classroom_course_id, name, teacher_id)
        
        if not success:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="课程重命名成功",
            data={"message": "课程名称已更新"}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 删除课程

@router.delete("/classroom-courses/{classroom_course_id}", response_model=schemas.ApiResponse)
def delete_classroom_course(
    classroom_course_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除课堂中的课程"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        success = crud.delete_classroom_course(db, classroom_course_id, teacher_id)
        
        if not success:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在、无权限或课程已完成无法删除",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="课程删除成功",
            data={"message": "课程已从课堂中删除"}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 获取课程设置详情


# ==================== 课堂实训相关路由 ====================

@router.get("/classrooms/{classroom_id}/trainings", response_model=schemas.ApiResponse)
def get_classroom_trainings(
    classroom_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    student_id: Optional[int] = Query(None, description="学生ID"),
    db: Session = Depends(get_db)
):
    """
    获取课堂中的实训列表
    
    - 教师查看时提供 teacher_id
    - 学生查看时提供 student_id
    """
    try:
        from app.crud import training_crud
        
        # 确定用户角色
        if teacher_id:
            user_id = teacher_id
            user_role = "teacher"
        elif student_id:
            user_id = student_id
            user_role = "student"
        else:
            return schemas.ApiResponse(
                code="1001",
                message="缺少必要参数：teacher_id 或 student_id",
                trace_id=str(uuid.uuid4())
            )
        
        # 获取课堂实训列表
        trainings = training_crud.get_classroom_trainings(
            db=db,
            classroom_id=classroom_id,
            user_id=user_id,
            user_role=user_role
        )
        
        if trainings is None:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在或无权限访问",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="获取课堂实训列表成功",
            data={
                "list": trainings,
                "total": len(trainings)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课堂实训列表失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/classrooms/{classroom_id}/trainings", response_model=schemas.ApiResponse)
def add_training_to_classroom(
    classroom_id: int,
    request: schemas.AddTrainingToClassroomRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """将实训添加到课堂（支持批量添加）"""
    try:
        from app.crud import training_crud

        results = []
        failed_count = 0

        # 批量添加实训
        for training_id in request.training_ids:
            # 准备数据
            training_data = {
                "training_id": training_id,
                "start_time": getattr(request, 'start_time', None),
                "end_time": getattr(request, 'end_time', None),
                "allow_late_submission": getattr(request, 'allow_late_submission', False),
                "late_submission_days": getattr(request, 'late_submission_days', 0)
            }

            # 添加实训到课堂
            result = training_crud.add_training_to_classroom(
                db=db,
                classroom_id=classroom_id,
                training_data=training_data,
                teacher_id=teacher_id
            )

            if result:
                results.append(result)
            else:
                failed_count += 1

        if len(results) == 0:
            return schemas.ApiResponse(
                code="1003",
                message="添加失败，请检查权限、实训是否存在或是否已添加",
                trace_id=str(uuid.uuid4())
            )

        return schemas.ApiResponse(
            code="0000",
            message=f"成功添加 {len(results)} 个实训项目" + (f"，{failed_count} 个失败" if failed_count > 0 else ""),
            data=results
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加实训到课堂失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.put("/classrooms/{classroom_id}/trainings/{training_id}", response_model=schemas.ApiResponse)
def update_classroom_training(
    classroom_id: int,
    training_id: int,
    request: schemas.AddTrainingToClassroomRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新课堂中的实训设置"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        # 检查课堂权限
        classroom = db.query(db_models.Classroom).filter(
            db_models.Classroom.id == classroom_id,
            db_models.Classroom.teacher_id == teacher_id
        ).first()
        
        if not classroom:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        # 查找课堂实训记录
        classroom_training = db.query(db_models.ClassroomTraining).filter(
            db_models.ClassroomTraining.classroom_id == classroom_id,
            db_models.ClassroomTraining.training_id == training_id
        ).first()
        
        if not classroom_training:
            return schemas.ApiResponse(
                code="1004",
                message="课堂中不存在该实训",
                trace_id=str(uuid.uuid4())
            )
        
        # 更新设置
        classroom_training.start_time = request.start_time
        classroom_training.end_time = request.end_time
        classroom_training.allow_late_submission = request.allow_late_submission
        classroom_training.late_submission_days = request.late_submission_days
        
        db.commit()
        db.refresh(classroom_training)
        
        return schemas.ApiResponse(
            code="0000",
            message="更新实训设置成功",
            data={
                "id": classroom_training.id,
                "start_time": classroom_training.start_time,
                "end_time": classroom_training.end_time,
                "allow_late_submission": classroom_training.allow_late_submission,
                "late_submission_days": classroom_training.late_submission_days
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新实训设置失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.delete("/classrooms/{classroom_id}/trainings/{training_id}", response_model=schemas.ApiResponse)
def remove_training_from_classroom(
    classroom_id: int,
    training_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从课堂中移除实训"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        # 检查课堂权限
        classroom = db.query(db_models.Classroom).filter(
            db_models.Classroom.id == classroom_id,
            db_models.Classroom.teacher_id == teacher_id
        ).first()
        
        if not classroom:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        # 查找并删除课堂实训记录
        classroom_training = db.query(db_models.ClassroomTraining).filter(
            db_models.ClassroomTraining.classroom_id == classroom_id,
            db_models.ClassroomTraining.training_id == training_id
        ).first()
        
        if not classroom_training:
            return schemas.ApiResponse(
                code="1004",
                message="课堂中不存在该实训",
                trace_id=str(uuid.uuid4())
            )
        
        # 暂时跳过会话检查（TrainingSession模型不存在）
        # active_sessions = db.query(db_models.TrainingSession).filter(
        #     db_models.TrainingSession.classroom_training_id == classroom_training.id,
        #     db_models.TrainingSession.is_active == True
        # ).count()

        # if active_sessions > 0:
        #     return schemas.ApiResponse(
        #         code="1005",
        #         message="有学生正在进行该实训，无法删除",
        #         trace_id=str(uuid.uuid4())
        #     )
        
        # 删除记录
        db.delete(classroom_training)
        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message="移除实训成功",
            data={"message": "实训已从课堂中移除"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除实训失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/storage/stats", response_model=schemas.ApiResponse)
def get_storage_stats(
):
    """获取存储使用统计（管理员功能）"""
    try:
        # 权限检查：只有管理员可以查看存储统计
        if user_role != Role.ADMIN:
            return schemas.ApiResponse(
                code="1003",
                message="权限不足，需要管理员权限",
                trace_id=str(uuid.uuid4())
            )

        # 获取存储统计
        stats = file_manager.get_storage_stats()

        return schemas.ApiResponse(
            code="0000",
            message="获取存储统计成功",
            data=stats,
            trace_id=str(uuid.uuid4())
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取存储统计失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


# ==================== 学生管理相关路由 ====================

@router.get("/classrooms/{classroom_id}/students", response_model=schemas.ApiResponse)
def get_classroom_students(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    keyword: Optional[str] = Query(None, description="关键词搜索（姓名/学号）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课堂学生列表"""
    try:
        # 验证课堂是否存在
        classroom = db.query(db_models.Classroom).filter(
            db_models.Classroom.id == classroom_id
        ).first()

        if not classroom:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )

        jwt_user_id, jwt_role = _jwt_user_id_and_role(current_user)
        _require_classroom_detail_access(db, classroom, jwt_user_id, jwt_role)

        # 查询课堂学生
        query = db.query(db_models.ClassroomStudent).filter(
            db_models.ClassroomStudent.classroom_id == classroom_id
        )
        
        # 获取总数
        total = query.count()
        
        # 分页
        skip = (page - 1) * page_size
        classroom_students = query.offset(skip).limit(page_size).all()
        
        # 获取学生详细信息。classroom_students.student_id points to api_users.id.
        students = []
        for cs in classroom_students:
            user = db.query(db_models.User).filter(
                db_models.User.id == cs.student_id
            ).first()

            if user:
                display_name = user.full_name or user.username or f"学生{cs.student_id}"
                student_info = {
                    "id": cs.id,
                    "student_id": user.id,
                    "realname": display_name,
                    "xuehao": user.username or str(user.id),
                    "email": user.email,
                    "class_name": "",
                    "joined_at": cs.joined_at.isoformat() if cs.joined_at else None
                }

                # 如果有关键词搜索，过滤结果
                if keyword:
                    if keyword.lower() not in student_info["realname"].lower() and \
                       keyword not in student_info["xuehao"]:
                        continue

                students.append(student_info)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=students,
            trace_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课堂学生列表失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/classrooms/{classroom_id}/students", response_model=schemas.ApiResponse)
def add_students_to_classroom(
    classroom_id: int,
    request: Optional[AddStudentRequest] = None,
    teacher_id: Optional[int] = Query(None, description="教师ID（向后兼容）"),
    uids: Optional[List[int]] = Query(None, description="学生ID列表（向后兼容）"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加学生到课堂（支持 JSON body 或 query param）"""
    # ── RBAC: 仅教师或管理员可添加学生 ──
    user_roles = current_user.get("roles", [])
    if not any(r in ("teacher", "admin") for r in user_roles) and not current_user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅教师或管理员可添加学生")
    try:
        # ── 解析学生ID列表: JSON body 优先，否则用 query param ──
        student_ids = None
        if request and hasattr(request, 'student_ids') and request.student_ids:
            student_ids = request.student_ids
        elif uids:
            student_ids = uids

        # 首先检查课堂是否存在
        classroom = db.query(db_models.Classroom).filter(
            db_models.Classroom.id == classroom_id
        ).first()
        if not classroom:
            raise HTTPException(status_code=404, detail="课堂不存在")

        # ── Lifecycle Guard: 已结束课堂不可添加学生 ──
        if _is_ended(classroom):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已结束的课堂不可添加学生")

        # 检查教师权限（必须是课堂的创建者）
        actual_teacher_id = current_user["user_id"]
        if classroom.teacher_id != actual_teacher_id and not current_user.get("is_superuser"):
            raise HTTPException(status_code=403, detail="无权限操作此课堂")

        # 验证学生ID列表
        if not student_ids:
            raise HTTPException(status_code=400, detail="学生ID列表不能为空")

        added_count = 0
        for uid in student_ids:
            # 检查用户是否存在于api_users表中，如果不存在则创建
            existing_user = db.query(db_models.User).filter(
                db_models.User.id == uid
            ).first()

            if not existing_user:
                # 创建占位用户（硬编码测试用户场景）
                # 检查是否是与硬编码测试用户ID匹配
                user_mapping = {
                    29: ("teacher1", "teacher1@test.com", "教师"),
                    30: ("student1", "student1@test.com", "学生"),
                }

                if uid in user_mapping:
                    username, email, name = user_mapping[uid]
                    # 生成一个随机密码哈希
                    import bcrypt
                    password_hash = bcrypt.hashpw(b'temp_password', bcrypt.gensalt()).decode()

                    new_user = db_models.User(
                        id=uid,
                        username=username,
                        email=email,
                        full_name=name,
                        hashed_password=password_hash,
                        is_active=True,
                        is_superuser=False,
                        total_coins=0
                    )
                    db.add(new_user)
                    db.flush()  # 确保用户被插入并获取ID
                    logger.info(f"自动创建用户: id={uid}, username={username}")

            # 检查是否已存在于课堂
            existing = db.query(db_models.ClassroomStudent).filter(
                db_models.ClassroomStudent.classroom_id == classroom_id,
                db_models.ClassroomStudent.student_id == uid
            ).first()

            if not existing:
                new_cs = db_models.ClassroomStudent(
                    classroom_id=classroom_id,
                    student_id=uid,
                    joined_at=datetime.now(timezone.utc)
                )
                db.add(new_cs)
                added_count += 1

        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功添加 {added_count} 名学生",
            data={"added_count": added_count},
            trace_id=str(uuid.uuid4())
        )
    
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"添加学生失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.delete("/classrooms/{classroom_id}/students", response_model=schemas.ApiResponse)
def remove_students_from_classroom(
    classroom_id: int,
    request: Request,
    ids: Optional[str] = Query(None, description="[向后兼容] 学生UID列表，逗号分隔"),
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db)
):
    """从课堂移除学生"""
    try:
        student_ids = []
        if ids:
            student_ids = [int(id.strip()) for id in ids.split(",") if id.strip()]
        
        # 尝试从body解析（可能由于FastAPI DELETE body问题，通过普通Depends/Request拿）
        try:
            body = request.json()
            import asyncio
            if asyncio.iscoroutine(body):
                import nest_asyncio
                nest_asyncio.apply()
                body_data = asyncio.run(body)
            else:
                body_data = body
            if isinstance(body_data, dict) and "student_ids" in body_data:
                student_ids = body_data["student_ids"]
        except Exception:
            pass

        if not student_ids:
            return schemas.ApiResponse(code="4000", message="缺失 student_ids", trace_id=str(uuid.uuid4()))

        deleted_count = db.query(db_models.ClassroomStudent).filter(
            db_models.ClassroomStudent.classroom_id == classroom_id,
            db_models.ClassroomStudent.student_id.in_(student_ids)
        ).delete(synchronize_session=False)
        
        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功移除 {deleted_count} 名学生",
            data={"deleted_count": deleted_count},
            trace_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"移除学生失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


# ==================== 成绩管理相关路由 ====================

@router.get("/classrooms/{classroom_id}/courses/{classroom_course_id}/grades", response_model=schemas.ApiResponse)
def get_course_grades(
    classroom_id: int,
    classroom_course_id: int,
    teacher_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    course_type: Optional[str] = Query(None, description="课程类型: training=实训, practice=实践"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取课程成绩列表 (Phase C-2: Z1 + 融合 fc 自动评测)"""
    try:
        # Z1: JWT 覆盖 query teacher_id, role 校验
        role = (current_user.get("roles") or ["student"])[0]
        jwt_uid = current_user["id"]
        if role not in ("teacher", "admin"):
            raise HTTPException(status_code=403, detail=f"需要角色 ('teacher','admin'), 当前角色 {role}")
        if role != "admin" and teacher_id is not None and teacher_id != jwt_uid:
            raise HTTPException(status_code=403, detail="path teacher_id 与 JWT 不符")

        skip = (page - 1) * page_size

        # 如果是实训类型，classroom_course_id 实际上是 classroom_training_id
        if course_type == "training":
            # 获取课堂实训信息
            classroom_training = db.query(db_models.ClassroomTraining).filter(
                db_models.ClassroomTraining.id == classroom_course_id,
                db_models.ClassroomTraining.classroom_id == classroom_id
            ).first()

            if not classroom_training:
                return schemas.ApiResponse(
                    code="1001",
                    message="实训不存在",
                    trace_id=str(uuid.uuid4())
                )

            # 获取课堂学生列表
            classroom_students = db.query(db_models.ClassroomStudent).filter(
                db_models.ClassroomStudent.classroom_id == classroom_id
            ).all()

            # 查找实训对应的Course和ClassroomCourse
            # 提交时创建了一个类型为TRAINING的Course，我们需要找到它
            training = db.query(db_models.Training).filter(
                db_models.Training.id == classroom_training.training_id
            ).first()

            actual_classroom_course_id = None
            if training:
                # 查找关联的Course（类型为TRAINING，标题为"[实训]xxx"）
                from app.models.models import CourseTypeEnum
                course = db.query(db_models.Course).filter(
                    db_models.Course.course_type == CourseTypeEnum.TRAINING,
                    db_models.Course.title == f"[实训]{training.title}"
                ).first()

                if course:
                    # 查找ClassroomCourse
                    cc = db.query(db_models.ClassroomCourse).filter(
                        db_models.ClassroomCourse.classroom_id == classroom_id,
                        db_models.ClassroomCourse.course_id == course.id
                    ).first()
                    if cc:
                        actual_classroom_course_id = cc.id

            # 查找或创建学生进度记录
            grade_list = []
            for cs in classroom_students:
                student = db.query(db_models.User).filter(db_models.User.id == cs.student_id).first()
                if not student:
                    continue

                # 查找现有进度记录
                # 使用实际的classroom_course_id（如果找到），否则回退到传入的ID
                lookup_id = actual_classroom_course_id if actual_classroom_course_id else classroom_course_id
                progress = db.query(db_models.StudentCourseProgress).filter(
                    db_models.StudentCourseProgress.classroom_course_id == lookup_id,
                    db_models.StudentCourseProgress.student_id == cs.student_id
                ).first()

                if progress:
                    grade_data = {
                        "id": progress.id,
                        "numericStudentId": cs.student_id,
                        "studentId": student.username,
                        "name": student.full_name or student.username,
                        "avatar": getattr(student, 'avatar', None),
                        "status": progress.student_status.value if progress.student_status else "NOT_STARTED",
                        "submissionStatus": progress.training_submission_status.value if progress.training_submission_status else None,
                        "completedTasks": progress.completed_task_count or 0,
                        "totalTasks": 0,
                        "taskScore": progress.overall_score,
                        "penalty": progress.teacher_penalties,
                        "finalScore": progress.final_calculated_score,
                        "submittedAt": progress.last_submission_at.isoformat() if progress.last_submission_at else None,
                        "totalTime": progress.total_time_spent_seconds,
                        "commentStatus": "commented" if progress.graded_at else "not_commented",
                        "score": progress.overall_score if progress.graded_at else None,
                        "canEditPenalty": False,
                        "teacherFeedback": progress.teacher_feedback,
                        "isExcellentWork": progress.is_excellent_work
                    }
                else:
                    # 没有进度记录，返回未开始状态
                    grade_data = {
                        "id": f"temp_{cs.student_id}",
                        "numericStudentId": cs.student_id,
                        "studentId": student.username,
                        "name": student.full_name or student.username,
                        "avatar": getattr(student, 'avatar', None),
                        "status": "NOT_STARTED",
                        "submissionStatus": None,
                        "completedTasks": 0,
                        "totalTasks": 0,
                        "taskScore": None,
                        "penalty": 0,
                        "finalScore": None,
                        "submittedAt": None,
                        "totalTime": 0,
                        "commentStatus": "not_commented",
                        "score": None,
                        "canEditPenalty": False,
                        "teacherFeedback": None,
                        "isExcellentWork": False
                    }
                grade_list.append(grade_data)

            # 状态筛选
            if status and status != "all":
                grade_list = [g for g in grade_list if g["status"].lower() == status.lower() or
                             (g.get("submissionStatus") and g["submissionStatus"].lower() == status.lower())]

            # 关键词搜索
            if keyword:
                keyword_lower = keyword.lower()
                grade_list = [g for g in grade_list if keyword_lower in g["name"].lower() or keyword_lower in g["studentId"].lower()]

            total = len(grade_list)
            grade_list = grade_list[skip:skip + page_size]

            return schemas.ApiResponse(
                code="0000",
                message="获取成绩列表成功",
                data={
                    "grades": grade_list,
                    "total": total,
                    "page": page,
                    "page_size": page_size
                },
                trace_id=str(uuid.uuid4())
            )

        # 原有的课程成绩逻辑 (Phase C-2: PRACTICE 课程返 dict, TRAINING 仍是 SCP object)
        grades, total = crud.get_course_grades_with_stats(
            db=db,
            classroom_course_id=classroom_course_id,
            status=status,
            keyword=keyword,
            skip=skip,
            limit=page_size
        )

        # 格式化响应
        grade_list = []
        for grade in grades:
            if isinstance(grade, dict):
                # PRACTICE 课程 dict (Phase C-2 融合 SCP+TER)
                user = grade["student"]
                # id fallback: auto-only 学生无 SCP 行 (id=None) 时用负 student_id 占位,
                # frontend grade.id.toString() 不会 crash (canEditPenalty=false 仍然防止误操作)
                _grade_id = grade["id"] if grade["id"] is not None else -grade["student_id"]
                grade_data = {
                    "id": _grade_id,
                    "numericStudentId": grade["student_id"],
                    "studentId": user.username if user else "未知",
                    "name": user.full_name if user else "未知学生",
                    "status": grade["student_status_value"],
                    "submissionStatus": grade["training_submission_status_value"],
                    "completedTasks": grade["completed_task_count"] or 0,
                    "totalTasks": grade["total_tasks"],
                    "taskScore": grade["task_score_v"],
                    "penalty": grade["teacher_penalties"],
                    "finalScore": grade["current_score"],
                    "submittedAt": grade["last_submission_at"].isoformat() if grade["last_submission_at"] else None,
                    "totalTime": grade["total_time_spent_seconds"],
                    "commentStatus": "commented" if grade["graded_at"] else "not_commented",
                    "score": grade["current_score"] if grade["graded_at"] else (grade["auto_score"] if grade["auto_completed_tasks"] > 0 else None),
                    "canEditPenalty": grade["student_status_value"] == "COMPLETED_LATE",
                    "teacherFeedback": grade["teacher_feedback"],
                    "isExcellentWork": grade["is_excellent_work"],
                    # Phase C-2 新字段 (frontend 可选用)
                    "autoCompletedTasks": grade["auto_completed_tasks"],
                    "autoScore": grade["auto_score"],
                    "lastEvaluationAt": grade["last_evaluation_at"].isoformat() if grade["last_evaluation_at"] else None,
                    "derivedStatus": grade["derived_status"],
                }
            else:
                # TRAINING (老逻辑, SCP object)
                # 获取课程信息以获取总任务数 (TRAINING 路径需要 lookup)
                classroom_course = db.query(db_models.ClassroomCourse).filter(
                    db_models.ClassroomCourse.id == classroom_course_id
                ).first()
                total_tasks = 0
                if classroom_course and classroom_course.course:
                    practice = db.query(db_models.Practice).filter(
                        db_models.Practice.parent_course_id == classroom_course.course_id
                    ).first()
                    if practice:
                        total_tasks = practice.task_count or 0
                    elif classroom_course.course.course_type == db_models.CourseTypeEnum.PRACTICE:
                        total_tasks = classroom_course.course.practice_task_count or 0

                grade_data = {
                    "id": grade.id,
                    "numericStudentId": grade.student_id,
                    "studentId": grade.student.username if grade.student else "未知",
                    "name": grade.student.full_name if grade.student else "未知学生",
                    "status": grade.student_status.value if grade.student_status else None,
                    "submissionStatus": grade.training_submission_status.value if grade.training_submission_status else None,
                    "completedTasks": grade.completed_task_count or 0,
                    "totalTasks": total_tasks,
                    "taskScore": grade.overall_score,
                    "penalty": grade.teacher_penalties,
                    "finalScore": grade.final_calculated_score,
                    "submittedAt": grade.last_submission_at.isoformat() if grade.last_submission_at else None,
                    "totalTime": grade.total_time_spent_seconds,
                    "commentStatus": "commented" if grade.graded_at else "not_commented",
                    "score": grade.overall_score if grade.graded_at else None,
                    "canEditPenalty": (grade.student_status.value == "COMPLETED_LATE") if grade.student_status else False,
                    "teacherFeedback": grade.teacher_feedback,
                    "isExcellentWork": grade.is_excellent_work
                }
            grade_list.append(grade_data)

        return schemas.ApiResponse(
            code="0000",
            message="获取成绩列表成功",
            data={
                "grades": grade_list,
                "total": total,
                "page": page,
                "page_size": page_size
            },
            trace_id=str(uuid.uuid4())
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取成绩列表失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.patch("/grades/{grade_id}", response_model=schemas.ApiResponse)
def update_grade_penalty(
    grade_id: int,
    penalty: int = Query(..., description="奖惩分数"),
    teacher_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """更新成绩奖惩分数 (Codex 审计 P0 修: 加 Z1 JWT + classroom 教师权限校验)

    老逻辑: query teacher_id 为 required, 但端点无 Depends(get_current_user),
    任何匿名用户都能 PATCH 任意 grade_id 改 SCP 行的 teacher_penalties +
    final_calculated_score, 完全绕过权限. 严重数据完整性漏洞.

    修复: 加 JWT, role 限 teacher/admin, 校验 path teacher_id == JWT user_id
    (admin 例外), 进一步通过 classroom 关系校验调用方是该班教师.
    """
    try:
        # Z1: JWT 校验
        role = (current_user.get("roles") or ["student"])[0]
        jwt_uid = current_user["id"]
        if role not in ("teacher", "admin"):
            raise HTTPException(status_code=403, detail=f"需要角色 ('teacher','admin'), 当前角色 {role}")
        if role != "admin" and teacher_id is not None and teacher_id != jwt_uid:
            raise HTTPException(status_code=403, detail="path teacher_id 与 JWT 不符")
        effective_teacher_id = jwt_uid if role != "admin" else (teacher_id or jwt_uid)

        # 获取成绩记录
        grade = db.query(db_models.StudentCourseProgress).filter(
            db_models.StudentCourseProgress.id == grade_id
        ).first()

        if not grade:
            return schemas.ApiResponse(
                code="1001",
                message="成绩记录不存在",
                trace_id=str(uuid.uuid4())
            )

        # 校验调用方是该 grade 所属课堂的教师 (admin 跳过)
        if role != "admin":
            cc = db.query(db_models.ClassroomCourse).filter(
                db_models.ClassroomCourse.id == grade.classroom_course_id
            ).first()
            if not cc:
                raise HTTPException(status_code=404, detail="课程不存在")
            if not crud.check_classroom_teacher_permission(db, cc.classroom_id, effective_teacher_id):
                raise HTTPException(status_code=403, detail="无权限修改此课堂成绩")

        # 更新奖惩分数
        grade.teacher_penalties = penalty
        if grade.overall_score is not None:
            grade.final_calculated_score = grade.overall_score - penalty

        db.commit()

        return schemas.ApiResponse(
            code="0000",
            message="更新奖惩分数成功",
            data={
                "id": grade.id,
                "penalty": grade.teacher_penalties,
                "final_score": grade.final_calculated_score
            },
            trace_id=str(uuid.uuid4())
        )
    except HTTPException:
        db.rollback()
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新奖惩分数失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/training-submissions/{submission_id}/review", response_model=schemas.ApiResponse)
def review_training_submission(
    submission_id: int,
    score: int = Query(..., description="评分分数"),
    comment: str = Query("", description="评语"),
    is_excellent: bool = Query(False, description="是否评为优秀作业"),
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """点评实训作业"""
    try:
        # Z1: JWT 校验（沿用 update_grade_penalty 的模式）
        role = (current_user.get("roles") or ["student"])[0]
        jwt_uid = current_user["id"]
        if role not in ("teacher", "admin"):
            raise HTTPException(status_code=403, detail=f"需要角色 ('teacher','admin'), 当前角色 {role}")
        if role != "admin" and teacher_id is not None and teacher_id != jwt_uid:
            raise HTTPException(status_code=403, detail="path teacher_id 与 JWT 不符")
        effective_teacher_id = jwt_uid if role != "admin" else (teacher_id or jwt_uid)

        # 获取学生进度记录（用submission_id作为grade_id）
        grade = db.query(db_models.StudentCourseProgress).filter(
            db_models.StudentCourseProgress.id == submission_id
        ).first()

        if not grade:
            return schemas.ApiResponse(
                code="1001",
                message="作业记录不存在",
                trace_id=str(uuid.uuid4())
            )

        # 校验调用方是该 grade 所属课堂的教师 (admin 跳过)
        if role != "admin":
            cc = db.query(db_models.ClassroomCourse).filter(
                db_models.ClassroomCourse.id == grade.classroom_course_id
            ).first()
            if not cc:
                raise HTTPException(status_code=404, detail="课程不存在")
            if not crud.check_classroom_teacher_permission(db, cc.classroom_id, effective_teacher_id):
                raise HTTPException(status_code=403, detail="无权限点评此作业")

        # 更新点评信息
        grade.overall_score = score
        grade.final_calculated_score = score
        grade.teacher_feedback = comment
        grade.is_excellent_work = is_excellent
        grade.graded_by_teacher_id = effective_teacher_id
        grade.graded_at = datetime.now()
        grade.student_status = (
            db_models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
            if grade.training_submission_status == db_models.SubmissionStatusEnum.LATE_SUBMISSION
            else db_models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME
        )

        db.commit()

        return schemas.ApiResponse(
            code="0000",
            message="作业点评成功",
            data={
                "id": grade.id,
                "score": grade.overall_score,
                "comment": grade.teacher_feedback,
                "is_excellent": grade.is_excellent_work,
                "graded_at": grade.graded_at.isoformat()
            },
            trace_id=str(uuid.uuid4())
        )
    except HTTPException:
        db.rollback()
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"作业点评失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/classrooms/{classroom_id}/trainings/{training_id}/details", response_model=schemas.ApiResponse)
def get_training_details(
    classroom_id: int,
    training_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    student_id: Optional[int] = Query(None, description="学生ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课堂实训详情（包括学生进度）"""
    try:
        from app.crud import training_crud

        jwt_user_id, jwt_role = _jwt_user_id_and_role(current_user)
        if jwt_user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证")

        # 确定用户角色（以 JWT 身份为准，忽略/校验客户端传入的 teacher_id/student_id）
        if jwt_role == "admin":
            if teacher_id:
                user_id, user_role = teacher_id, "teacher"
            elif student_id:
                user_id, user_role = student_id, "student"
            else:
                user_id, user_role = jwt_user_id, "teacher"
        elif jwt_role == "teacher":
            if teacher_id is not None and teacher_id != jwt_user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问其他教师的实训详情")
            user_id, user_role = jwt_user_id, "teacher"
        elif jwt_role == "student":
            if student_id is not None and student_id != jwt_user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问其他学生的实训详情")
            user_id, user_role = jwt_user_id, "student"
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问实训详情")

        # 获取实训详情
        training_detail = training_crud.get_training_details(
            db=db,
            classroom_id=classroom_id,
            training_id=training_id,
            user_id=user_id,
            user_role=user_role
        )
        
        if training_detail is None:
            return schemas.ApiResponse(
                code="1002",
                message="实训不存在或无权限访问",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="获取实训详情成功",
            data=training_detail
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训详情失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


# ==================== 实训提交与进度 API ====================
from pydantic import BaseModel
from typing import Optional, Dict, Any

class TrainingSubmissionIn(BaseModel):
    student_id: int
    score: Optional[float] = None
    completed: Optional[bool] = False
    report: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

@router.post("/classrooms/{classroom_id}/trainings/{training_id}/submission", response_model=schemas.ApiResponse)
def submit_training_progress(
    classroom_id: int,
    training_id: int,
    payload: TrainingSubmissionIn,
    db: Session = Depends(get_db)
):
    """提交课堂实训的学习进度/作业"""
    try:
        # 1. Verify ClassroomTraining exists
        ct = db.query(db_models.ClassroomTraining).filter(
            db_models.ClassroomTraining.classroom_id == classroom_id,
            db_models.ClassroomTraining.training_id == training_id
        ).first()
        
        if not ct:
            return schemas.ApiResponse(code="4040", message="未找到对应的课堂实训关联", trace_id=str(uuid.uuid4()))
            
        # 2. Find or Create Session
        session = db.query(db_models.TrainingSession).filter(
            db_models.TrainingSession.classroom_training_id == ct.id,
            db_models.TrainingSession.student_id == payload.student_id
        ).first()
        
        if not session:
            session = db_models.TrainingSession(
                classroom_training_id=ct.id,
                student_id=payload.student_id,
                progress_percentage=0
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            
        # Update progress
        if payload.completed:
            session.progress_percentage = 100
        elif payload.score is not None:
            session.progress_percentage = min(100, max(0, int(payload.score)))
            
        import datetime
        session.last_active_time = datetime.datetime.utcnow()
        db.commit()
        
        # 3. Handle Submission (if completed or has report)
        if payload.completed or payload.report or payload.data:
            submission = db.query(db_models.TrainingSubmission).filter(
                db_models.TrainingSubmission.session_id == session.id
            ).first()
            
            import json
            content_str = json.dumps(payload.data) if payload.data else payload.report
            
            if not submission:
                submission = db_models.TrainingSubmission(
                    session_id=session.id,
                    auto_score=payload.score,
                    content=content_str
                )
                db.add(submission)
            else:
                submission.auto_score = payload.score
                submission.content = content_str
                submission.submission_time = datetime.datetime.utcnow()
                
            db.commit()
            
        return schemas.ApiResponse(code="0000", message="提交成功", data={"session_id": session.id})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"实训提交失败: {str(e)}")
        db.rollback()
        return schemas.ApiResponse(
            code="5000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== BI 实训评阅 API ====================

@router.get("/classrooms/{classroom_id}/trainings/{training_id}/submission/{student_id}", response_model=schemas.ApiResponse)
def get_training_submission(
    classroom_id: int,
    training_id: int,
    student_id: int,
    db: Session = Depends(get_db)
):
    """获取学生的实训提交详情（教师阅卷用）"""
    try:
        # 先查找对应的 classroom_course_id
        # 通过 ClassroomCourse 关联 classroom_id 和 training (通过 course)
        classroom_course = db.query(db_models.ClassroomCourse).join(
            db_models.Course, db_models.ClassroomCourse.course_id == db_models.Course.id
        ).filter(
            db_models.ClassroomCourse.classroom_id == classroom_id,
            db_models.Course.course_type == db_models.CourseTypeEnum.TRAINING,
            db_models.Course.title.contains(f"[实训]")
        ).first()

        # 如果没找到，尝试直接通过 classroom_course_id 和 student_id 查询
        progress = None
        if classroom_course:
            progress = db.query(db_models.StudentCourseProgress).filter(
                db_models.StudentCourseProgress.classroom_course_id == classroom_course.id,
                db_models.StudentCourseProgress.student_id == student_id
            ).first()

        # 如果还没找到，尝试直接查询所有该学生的进度记录
        if not progress:
            progress = db.query(db_models.StudentCourseProgress).filter(
                db_models.StudentCourseProgress.student_id == student_id,
                db_models.StudentCourseProgress.training_submission_status != None
            ).first()

        if not progress:
            return schemas.ApiResponse(
                code="1001",
                message="未找到学生提交记录",
                data=None
            )

        # 获取学生信息
        student = db.query(db_models.User).filter(db_models.User.id == student_id).first()
        student_name = student.full_name if student else f"学生 {student_id}"

        # 解析提交快照
        snapshot = None
        schema_version = None
        thumbnail = None
        notes = None

        if progress.submission_snapshot:
            try:
                import json
                snapshot_data = json.loads(progress.submission_snapshot)
                snapshot = snapshot_data.get("snapshot")
                schema_version = snapshot_data.get("schemaVersion")
                thumbnail = snapshot_data.get("thumbnail")
                notes = snapshot_data.get("notes")
            except:
                pass

        return schemas.ApiResponse(
            code="0000",
            message="获取提交详情成功",
            data={
                "id": progress.id,
                "studentId": student_id,
                "studentName": student_name,
                "status": progress.student_status.value if progress.student_status else "NOT_STARTED",
                "snapshot": snapshot,
                "schemaVersion": schema_version,
                "thumbnail": thumbnail,
                "notes": notes,
                "submittedAt": progress.last_submission_at.isoformat() if progress.last_submission_at else None,
                "score": progress.overall_score,
                "teacherFeedback": progress.teacher_feedback,
                "gradedAt": progress.graded_at.isoformat() if progress.graded_at else None
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训提交详情失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/classrooms/{classroom_id}/trainings/{training_id}/grade/{student_id}", response_model=schemas.ApiResponse)
def grade_training_submission(
    classroom_id: int,
    training_id: int,
    student_id: int,
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """评分实训提交"""
    try:
        from datetime import datetime

        classroom = crud.get_classroom(db, classroom_id=classroom_id)
        if not classroom:
            return schemas.ApiResponse(code="1001", message="课堂不存在", data=None)
        jwt_user_id, jwt_role = _jwt_user_id_and_role(current_user)
        _require_classroom_detail_access(db, classroom, jwt_user_id, jwt_role)
        if jwt_role == "student":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权评分实训提交")

        classroom_course = _get_training_classroom_course(
            db=db,
            classroom_id=classroom_id,
            training_id=training_id,
        )
        if not classroom_course:
            return schemas.ApiResponse(
                code="1001",
                message="未找到对应的实训课程",
                data=None
            )

        # 查询学生进度
        progress = db.query(db_models.StudentCourseProgress).filter(
            db_models.StudentCourseProgress.classroom_course_id == classroom_course.id,
            db_models.StudentCourseProgress.student_id == student_id
        ).first()

        if not progress:
            return schemas.ApiResponse(
                code="1001",
                message="未找到学生提交记录",
                data=None
            )

        # 更新评分
        score = request.get("score")
        feedback = request.get("feedback", "")

        if score is None or not isinstance(score, (int, float)) or score < 0 or score > 100:
            return schemas.ApiResponse(
                code="1002",
                message="分数无效，必须在 0-100 之间",
                data=None
            )

        progress.overall_score = score
        progress.final_calculated_score = score - (progress.teacher_penalties or 0)
        progress.teacher_feedback = feedback
        progress.graded_at = datetime.utcnow()
        progress.graded_by_teacher_id = jwt_user_id if jwt_role == "teacher" else request.get("teacher_id")
        if progress.student_status not in [
            db_models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME,
            db_models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE,
        ]:
            progress.student_status = db_models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME

        db.commit()

        return schemas.ApiResponse(
            code="0000",
            message="评分成功",
            data={
                "id": progress.id,
                "score": progress.overall_score,
                "feedback": progress.teacher_feedback,
                "gradedAt": progress.graded_at.isoformat() if progress.graded_at else None
            }
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"评分实训提交失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/classrooms/{classroom_id}/trainings/{training_id}/grades", response_model=schemas.ApiResponse)
def get_training_grades(
    classroom_id: int,
    training_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    keyword: Optional[str] = Query(None, description="学生姓名或学号搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取实训成绩列表"""
    try:
        from app.crud import training_crud

        classroom = crud.get_classroom(db, classroom_id=classroom_id)
        if not classroom:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在",
                data={"list": [], "total": 0, "stats": {}}
            )
        jwt_user_id, jwt_role = _jwt_user_id_and_role(current_user)
        _require_classroom_detail_access(db, classroom, jwt_user_id, jwt_role)
        if jwt_role == "student":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看实训成绩列表")

        # 查找 ClassroomTraining 记录
        ct = db.query(db_models.ClassroomTraining).filter(
            db_models.ClassroomTraining.classroom_id == classroom_id,
            db_models.ClassroomTraining.training_id == training_id
        ).first()

        if not ct:
            return schemas.ApiResponse(
                code="1001",
                message="实训不存在或未添加到课堂",
                data={"list": [], "total": 0, "stats": {}}
            )

        # 获取该课堂的所有学生
        students_in_classroom = db.query(db_models.ClassroomStudent).filter(
            db_models.ClassroomStudent.classroom_id == classroom_id
        ).all()
        student_ids = [s.student_id for s in students_in_classroom]

        # 获取该实训对应的 ClassroomCourse (类型为 TRAINING)
        classroom_course = db.query(db_models.ClassroomCourse).join(
            db_models.Course, db_models.ClassroomCourse.course_id == db_models.Course.id
        ).filter(
            db_models.ClassroomCourse.classroom_id == classroom_id,
            db_models.Course.course_type == db_models.CourseTypeEnum.TRAINING
        ).first()

        skip = (page - 1) * page_size

        # 统计
        stats = {
            "total_students": len(student_ids),
            "not_started": 0,
            "not_submitted": 0,
            "submitted": 0,
            "late_submitted": 0,
            "graded": 0,
            "not_graded": 0
        }

        if not student_ids:
            return schemas.ApiResponse(
                code="0000",
                message="获取成功",
                data={"list": [], "total": 0, "stats": stats}
            )

        # 查询学生进度（包含提交状态）
        query = db.query(db_models.StudentCourseProgress).filter(
            db_models.StudentCourseProgress.classroom_course_id == classroom_course.id if classroom_course else False,
            db_models.StudentCourseProgress.student_id.in_(student_ids)
        )

        if keyword:
            # 通过学生姓名过滤
            student_map = {s.id: s for s in students_in_classroom}
            student_users = db.query(db_models.User).filter(
                db_models.User.id.in_(student_ids)
            ).all()
            matching_ids = [u.id for u in student_users if keyword.lower() in (u.full_name or "").lower()]
            query = query.filter(db_models.StudentCourseProgress.student_id.in_(matching_ids))

        all_progress = query.all()

        # 统计
        for p in all_progress:
            status = p.training_submission_status
            if status == db_models.SubmissionStatusEnum.NOT_STARTED:
                stats["not_started"] += 1
            elif status == db_models.SubmissionStatusEnum.IN_PROGRESS:
                stats["not_submitted"] += 1
            elif status == db_models.SubmissionStatusEnum.SUBMITTED:
                stats["submitted"] += 1
            elif status == db_models.SubmissionStatusEnum.LATE_SUBMISSION:
                stats["late_submitted"] += 1
            if p.overall_score is not None and p.overall_score > 0:
                stats["graded"] += 1
            else:
                stats["not_graded"] += 1

        # 分页
        total = len(all_progress)
        paginated = all_progress[skip:skip + page_size]

        # 获取学生信息
        student_user_ids = [p.student_id for p in paginated]
        student_users_map = {}
        if student_user_ids:
            users = db.query(db_models.User).filter(db_models.User.id.in_(student_user_ids)).all()
            student_users_map = {u.id: u for u in users}

        grade_list = []
        for p in paginated:
            user = student_users_map.get(p.student_id)
            grade_list.append({
                "id": p.id,
                "student_id": p.student_id,
                "student_name": user.full_name if user else f"学生 {p.student_id}",
                "student_no": user.username if user else "",
                "submission_status": p.training_submission_status.value if p.training_submission_status else "not_started",
                "overall_score": p.overall_score,
                "teacher_feedback": p.teacher_feedback,
                "is_excellent_work": p.is_excellent_work,
                "first_access_at": p.first_access_at.isoformat() if p.first_access_at else None,
                "last_submission_at": p.last_submission_at.isoformat() if p.last_submission_at else None,
                "graded_at": p.graded_at.isoformat() if p.graded_at else None,
                "training_assignment_files": p.training_assignment_files,
            })

        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": grade_list,
                "total": total,
                "stats": stats,
                "meta": {"page": page, "page_size": page_size}
            }
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训成绩失败: {str(e)}")
        import traceback; traceback.print_exc()
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/classrooms/{classroom_id}/trainings/{training_id}/homework", response_model=schemas.ApiResponse)
def get_training_homework(
    classroom_id: int,
    training_id: int,
    keyword: Optional[str] = Query(None, description="学生姓名或学号搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取实训作业提交列表"""
    try:
        classroom = crud.get_classroom(db, classroom_id=classroom_id)
        if not classroom:
            return schemas.ApiResponse(code="1001", message="课堂不存在", data={"list": [], "total": 0})
        jwt_user_id, jwt_role = _jwt_user_id_and_role(current_user)
        _require_classroom_detail_access(db, classroom, jwt_user_id, jwt_role)
        if jwt_role == "student":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看实训作业列表")

        classroom_course = _get_training_classroom_course(
            db=db,
            classroom_id=classroom_id,
            training_id=training_id,
        )

        if not classroom_course:
            return schemas.ApiResponse(
                code="1001",
                message="未找到对应的实训课程",
                data={"list": [], "total": 0}
            )

        # 获取该课堂的所有学生
        students_in_classroom = db.query(db_models.ClassroomStudent).filter(
            db_models.ClassroomStudent.classroom_id == classroom_id
        ).all()
        student_ids = [s.student_id for s in students_in_classroom]

        if not student_ids:
            return schemas.ApiResponse(
                code="0000",
                message="获取成功",
                data={"list": [], "total": 0}
            )

        skip = (page - 1) * page_size

        # 查询有提交记录的学生进度
        query = db.query(db_models.StudentCourseProgress).filter(
            db_models.StudentCourseProgress.classroom_course_id == classroom_course.id,
            db_models.StudentCourseProgress.student_id.in_(student_ids),
            db_models.StudentCourseProgress.training_submission_status.in_([
                db_models.SubmissionStatusEnum.SUBMITTED,
                db_models.SubmissionStatusEnum.LATE_SUBMISSION
            ])
        )

        all_progress = query.all()
        total = len(all_progress)
        paginated = all_progress[skip:skip + page_size]

        # 获取学生信息
        student_user_ids = [p.student_id for p in paginated]
        student_users_map = {}
        if student_user_ids:
            users = db.query(db_models.User).filter(db_models.User.id.in_(student_user_ids)).all()
            student_users_map = {u.id: u for u in users}

        homework_list = []
        for p in paginated:
            user = student_users_map.get(p.student_id)
            # 解析作业文件
            files = []
            if p.training_assignment_files:
                import json as json_mod
                try:
                    files = json_mod.loads(p.training_assignment_files)
                except:
                    files = []

            homework_list.append({
                "id": p.id,
                "student_id": p.student_id,
                "student_name": user.full_name if user else f"学生 {p.student_id}",
                "student_no": user.username if user else "",
                "submission_status": p.training_submission_status.value if p.training_submission_status else "submitted",
                "overall_score": p.overall_score,
                "teacher_feedback": p.teacher_feedback,
                "is_excellent_work": p.is_excellent_work,
                "first_access_at": p.first_access_at.isoformat() if p.first_access_at else None,
                "last_submission_at": p.last_submission_at.isoformat() if p.last_submission_at else None,
                "graded_at": p.graded_at.isoformat() if p.graded_at else None,
                "files": files,
                "training_assignment_files": p.training_assignment_files,
            })

        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": homework_list,
                "total": total,
                "meta": {"page": page, "page_size": page_size}
            }
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训作业列表失败: {str(e)}")
        import traceback; traceback.print_exc()
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )
