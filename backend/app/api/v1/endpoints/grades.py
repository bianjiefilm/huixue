"""
成绩管理端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import uuid
import logging
from datetime import datetime, timezone, timedelta

# 修正的导入路径
from app.core.database import get_db, engine, Base
from app.core.security import get_current_user
from app.core.identity import resolve_scoped_id, require_owner_or_admin
from app.models import models as db_models  # 避免与FastAPI的models冲突
from app.crud import crud
from app.schemas import schemas

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/grades",
    tags=['grades']
)

@router.get("/classrooms/{classroom_id}/courses/{classroom_course_id}/grades", response_model=schemas.ApiResponse)
def get_course_grades(
    classroom_id: int,
    classroom_course_id: int,
    status: Optional[str] = Query(None, description="作业状态筛选：not_started, not_completed, completed_on_time, completed_late（实践课程）或 not_started, not_submitted, submitted, late_submitted（实训课程）"),
    keyword: Optional[str] = Query(None, description="学生姓名或学号搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取课程成绩列表 (Phase C: Z1 安全 + 融合 fc 自动评测数据)"""
    try:
        # Z1: JWT 覆盖 query teacher_id, role 校验, 防教师 A 冒充 B
        role = (current_user.get("roles") or ["student"])[0]
        jwt_uid = current_user["id"]
        if role not in ("teacher", "admin"):
            raise HTTPException(status_code=403, detail=f"需要角色 ('teacher','admin'), 当前角色 {role}")
        if role != "admin":
            if teacher_id is not None and teacher_id != jwt_uid:
                raise HTTPException(status_code=403, detail="path teacher_id 与 JWT 不符")
        # 内部 effective teacher_id = jwt_uid (admin 可代理任意, 但仍以 jwt_uid 校验权限)
        effective_teacher_id = jwt_uid if role != "admin" else (teacher_id or jwt_uid)

        # 检查权限 (传 effective_teacher_id, 不信任 query)
        if not crud.check_classroom_teacher_permission(db, classroom_id, effective_teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课程")
        
        skip = (page - 1) * page_size
        grade_list, total = crud.get_course_grades(
            db, classroom_id, classroom_course_id, effective_teacher_id, status, keyword, skip, page_size
        )
        
        if grade_list is None:
            raise HTTPException(status_code=404, detail="课程不存在")
        
        # 构建统计信息
        stats = {
            "total_students": total,
            "not_started": 0,
            "in_progress": 0,
            "completed": 0,
            "late_completed": 0
        }
        
        # 统计各状态学生数量
        for grade in grade_list:
            status_key = grade["assignment_status"]
            if status_key == "not_started":
                stats["not_started"] += 1
            elif status_key in ["not_completed", "not_submitted"]:
                stats["in_progress"] += 1
            elif status_key in ["completed_on_time", "submitted"]:
                stats["completed"] += 1
            elif status_key in ["completed_late", "late_submitted"]:
                stats["late_completed"] += 1
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": grade_list,
                "meta": meta,
                "stats": stats
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课程成绩列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取课程成绩列表失败: {str(e)}")


@router.get("/classroom-courses/{classroom_course_id}/statistics", response_model=schemas.ApiResponse)
def get_course_grade_statistics(
    classroom_course_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课程成绩统计信息"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课程成绩")
        statistics = crud.get_course_grade_statistics(db, classroom_course_id, teacher_id)
        
        if statistics is None:
            raise HTTPException(status_code=404, detail="课程不存在或无权限访问")
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data=statistics
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课程成绩统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取课程成绩统计失败: {str(e)}")


@router.patch("/student-progress/{progress_id}/penalty", response_model=schemas.ApiResponse)
def update_student_penalty(
    progress_id: int,
    request: schemas.PenaltyUpdateRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新学生奖惩扣分"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权修改该学生成绩")
        updated_progress = crud.update_student_penalty(
            db, progress_id, teacher_id, request.penalty_score, request.reason
        )
        
        if updated_progress is None:
            raise HTTPException(status_code=404, detail="学生进度记录不存在或无权限访问")
        
        return schemas.ApiResponse(
            code="0000",
            message="奖惩调整成功",
            data={
                "id": updated_progress.id,
                "penalty_score": updated_progress.teacher_penalties,
                "final_score": updated_progress.final_calculated_score
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新学生奖惩扣分失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新学生奖惩扣分失败: {str(e)}")


@router.patch("/classroom-courses/{classroom_course_id}/batch-penalty", response_model=schemas.ApiResponse)
def batch_update_student_penalty(
    classroom_course_id: int,
    request: schemas.BatchPenaltyUpdateRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量更新学生奖惩扣分"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权修改该学生成绩")
        if not request.student_ids:
            raise HTTPException(status_code=400, detail="学生ID列表不能为空")
        
        updated_records = crud.batch_update_student_penalty(
            db, classroom_course_id, teacher_id, request.student_ids, request.penalty_score, request.reason
        )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功更新 {len(updated_records)} 名学生的奖惩扣分",
            data={
                "updated_count": len(updated_records),
                "penalty_score": request.penalty_score
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量更新学生奖惩扣分失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量更新学生奖惩扣分失败: {str(e)}")


@router.get("/classroom-courses/{classroom_course_id}/assignments", response_model=schemas.ApiResponse)
def get_training_assignments(
    classroom_course_id: int,
    keyword: Optional[str] = Query(None, description="学生姓名或学号搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取实训作业列表"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该实训作业")
        skip = (page - 1) * page_size
        assignment_list, total = crud.get_training_assignments(
            db, classroom_course_id, teacher_id, keyword, skip, page_size
        )
        
        if assignment_list is None:
            raise HTTPException(status_code=404, detail="课程不存在、不是实训课程或无权限访问")
        
        # 构建统计信息
        stats = {
            "total_students": total,
            "not_started": 0,
            "not_submitted": 0,
            "submitted": 0,
            "late_submitted": 0,
            "graded": 0,
            "not_graded": 0
        }
        
        # 统计各状态学生数量
        for assignment in assignment_list:
            submission_status = assignment["submission_status"]
            grading_status = assignment["grading_status"]
            
            if submission_status == db_models.SubmissionStatusEnum.NOT_STARTED:
                stats["not_started"] += 1
            elif submission_status == db_models.SubmissionStatusEnum.IN_PROGRESS:
                stats["not_submitted"] += 1
            elif submission_status == db_models.SubmissionStatusEnum.SUBMITTED:
                stats["submitted"] += 1
            elif submission_status == db_models.SubmissionStatusEnum.LATE_SUBMISSION:
                stats["late_submitted"] += 1
            
            if grading_status == db_models.GradingStatusEnum.GRADED:
                stats["graded"] += 1
            else:
                stats["not_graded"] += 1
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": assignment_list,
                "meta": meta,
                "stats": stats
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训作业列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实训作业列表失败: {str(e)}")


@router.post("/classroom-courses/{classroom_course_id}/students/{student_id}/grade", response_model=schemas.ApiResponse)
def grade_training_assignment(
    classroom_course_id: int,
    student_id: int,
    request: schemas.TrainingGradingRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """实训作业点评"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权点评该学生作业")
        if request.score < 0 or request.score > 100:
            raise HTTPException(status_code=400, detail="评分必须在0-100之间")
        
        graded_progress = crud.grade_training_assignment(
            db, classroom_course_id, student_id, teacher_id, 
            request.score, request.feedback, request.is_excellent
        )
        
        if graded_progress is None:
            raise HTTPException(status_code=404, detail="学生作业不存在、未提交或无权限访问")
        
        return schemas.ApiResponse(
            code="0000",
            message="作业点评成功",
            data={
                "student_id": student_id,
                "score": graded_progress.overall_score,
                "final_score": graded_progress.final_calculated_score,
                "feedback": graded_progress.teacher_feedback,
                "is_excellent": graded_progress.is_excellent_work,
                "graded_at": graded_progress.graded_at
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"实训作业点评失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"实训作业点评失败: {str(e)}")


@router.get("/classroom-courses/{classroom_course_id}/export-grades", response_model=schemas.ApiResponse)
def export_course_grades(
    classroom_course_id: int,
    format: str = Query("excel", description="导出格式：excel, csv"),
    include_details: bool = Query(True, description="是否包含详细信息"),
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出课程成绩"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权导出该课程成绩")
        # 获取课堂课程信息以获取classroom_id
        classroom_course = db.query(db_models.ClassroomCourse).filter(
            db_models.ClassroomCourse.id == classroom_course_id
        ).first()
        
        if not classroom_course:
            raise HTTPException(status_code=404, detail="课程不存在")
        
        # 检查教师权限
        if not crud.check_classroom_teacher_permission(db, classroom_course.classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课程")
        
        # 获取所有成绩数据
        grade_list, total = crud.get_course_grades(
            db, classroom_course.classroom_id, classroom_course_id, teacher_id, None, None, 0, 1000
        )
        
        if grade_list is None:
            raise HTTPException(status_code=404, detail="课程不存在或无权限访问")
        
        # 这里应该实现实际的导出逻辑，生成Excel或CSV文件
        # 为了演示，我们返回数据结构
        export_data = {
            "format": format,
            "total_records": len(grade_list),
            "export_time": datetime.now(timezone.utc),
            "include_details": include_details,
            "download_url": f"/api/v1/downloads/grades-{classroom_course_id}-{int(datetime.now().timestamp())}.{format}"
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="成绩导出准备完成",
            data=export_data
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出课程成绩失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出课程成绩失败: {str(e)}")

# 学生端API：查看自己的作业详情

@router.get("/classroom-courses/{classroom_course_id}/students/{student_id}/assignment", response_model=schemas.ApiResponse)
def get_student_assignment_detail(
    classroom_course_id: int,
    student_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """教师查看学生作业详情（实训课程）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该学生作业详情")
        # 获取课程信息
        classroom_course = db.query(db_models.ClassroomCourse).options(
            joinedload(db_models.ClassroomCourse.course),
            joinedload(db_models.ClassroomCourse.classroom)
        ).filter(
            db_models.ClassroomCourse.id == classroom_course_id
        ).first()
        
        if not classroom_course:
            raise HTTPException(status_code=404, detail="课程不存在")
        
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_course.classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课程")
        
        # 只能查看实训课程
        if classroom_course.course.course_type != db_models.CourseTypeEnum.TRAINING:
            raise HTTPException(status_code=400, detail="只能查看实训课程的作业详情")
        
        # 获取学生进度记录
        progress = db.query(db_models.StudentCourseProgress).options(
            joinedload(db_models.StudentCourseProgress.student),
            joinedload(db_models.StudentCourseProgress.graded_by_teacher)
        ).filter(
            db_models.StudentCourseProgress.classroom_course_id == classroom_course_id,
            db_models.StudentCourseProgress.student_id == student_id
        ).first()
        
        if not progress:
            raise HTTPException(status_code=404, detail="学生作业记录不存在")
        
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
        
        # 构建作业详情
        assignment_detail = {
            "student_id": progress.student.id,
            "student_name": progress.student.full_name or progress.student.username,
            "student_number": progress.student.username,
            "avatar_url": None,
            "submission_status": progress.training_submission_status.value,
            "submission_time": progress.last_submission_at,
            "design_files": design_files,
            "experiment_reports": experiment_reports,
            "grading_status": "GRADED" if progress.graded_at else "NOT_GRADED",
            "score": progress.overall_score if progress.graded_at else None,
            "final_score": progress.final_calculated_score if progress.graded_at else None,
            "penalty_score": progress.teacher_penalties,
            "teacher_feedback": progress.teacher_feedback,
            "is_excellent": progress.is_excellent_work,
            "graded_at": progress.graded_at,
            "graded_by_teacher_name": progress.graded_by_teacher.full_name if progress.graded_by_teacher else None,
            "can_grade": progress.training_submission_status in [
                db_models.SubmissionStatusEnum.SUBMITTED,
                db_models.SubmissionStatusEnum.LATE_SUBMISSION
            ]
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


@router.get("/classroom-courses/{classroom_course_id}/excellent-works", response_model=schemas.ApiResponse)
def get_excellent_works(
    classroom_course_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: Optional[int] = Query(None, description="教师ID（可选，用于权限验证）"),
    student_id: Optional[int] = Query(None, description="学生ID（可选，学生查看时使用）"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取优秀作业列表"""
    try:
        # 获取课程信息
        classroom_course = db.query(db_models.ClassroomCourse).options(
            joinedload(db_models.ClassroomCourse.course),
            joinedload(db_models.ClassroomCourse.classroom)
        ).filter(
            db_models.ClassroomCourse.id == classroom_course_id
        ).first()

        if not classroom_course:
            raise HTTPException(status_code=404, detail="课程不存在")

        # 权限检查（教师或学生都可以查看；强制以 JWT 身份为准）
        role = (current_user.get("roles") or ["student"])[0]
        jwt_uid = current_user["id"]
        if role in ("teacher", "admin"):
            effective_teacher_id = jwt_uid if role != "admin" else (teacher_id or jwt_uid)
            if not crud.check_classroom_teacher_permission(db, classroom_course.classroom_id, effective_teacher_id):
                raise HTTPException(status_code=403, detail="无权限访问此课程")
        elif role == "student":
            student_in_classroom = db.query(db_models.ClassroomStudent).filter(
                db_models.ClassroomStudent.classroom_id == classroom_course.classroom_id,
                db_models.ClassroomStudent.student_id == jwt_uid
            ).first()
            if not student_in_classroom:
                raise HTTPException(status_code=403, detail="无权限访问此课程")
        else:
            raise HTTPException(status_code=403, detail="无权限访问此课程")
        
        # 查询优秀作业
        skip = (page - 1) * page_size
        query = db.query(db_models.StudentCourseProgress).options(
            joinedload(db_models.StudentCourseProgress.student),
            joinedload(db_models.StudentCourseProgress.graded_by_teacher)
        ).filter(
            db_models.StudentCourseProgress.classroom_course_id == classroom_course_id,
            db_models.StudentCourseProgress.is_excellent_work == True,
            db_models.StudentCourseProgress.graded_at.isnot(None)
        )
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        excellent_works = query.order_by(
            db_models.StudentCourseProgress.graded_at.desc()
        ).offset(skip).limit(page_size).all()
        
        # 构建响应数据
        excellent_list = []
        for progress in excellent_works:
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
            
            excellent_work = {
                "id": progress.id,
                "student_id": progress.student.id,
                "student_name": progress.student.full_name or progress.student.username,
                "student_number": progress.student.username,
                "avatar_url": None,
                "submission_time": progress.last_submission_at,
                "score": progress.overall_score,
                "final_score": progress.final_calculated_score,
                "teacher_feedback": progress.teacher_feedback,
                "graded_at": progress.graded_at,
                "graded_by_teacher_name": progress.graded_by_teacher.full_name if progress.graded_by_teacher else None,
                "design_files": design_files,
                "experiment_reports": experiment_reports,
                # 对于学生查看，可能需要隐藏一些敏感信息
                "can_view_details": True
            }
            
            excellent_list.append(excellent_work)
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": excellent_list,
                "meta": meta,
                "course_info": {
                    "course_name": classroom_course.course.title,
                    "course_type": classroom_course.course.course_type.value,
                    "classroom_name": classroom_course.classroom.name
                }
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取优秀作业列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取优秀作业列表失败: {str(e)}")


@router.get("/classrooms/{classroom_id}/excellent-works", response_model=schemas.ApiResponse)
def get_classroom_excellent_works(
    classroom_id: int,
    course_type: Optional[str] = Query(None, description="课程类型筛选：PRACTICE, TRAINING"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: Optional[int] = Query(None, description="教师ID（可选）"),
    student_id: Optional[int] = Query(None, description="学生ID（可选）"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课堂所有优秀作业列表"""
    try:
        # 权限检查（强制以 JWT 身份为准）
        role = (current_user.get("roles") or ["student"])[0]
        jwt_uid = current_user["id"]
        if role in ("teacher", "admin"):
            effective_teacher_id = jwt_uid if role != "admin" else (teacher_id or jwt_uid)
            if not crud.check_classroom_teacher_permission(db, classroom_id, effective_teacher_id):
                raise HTTPException(status_code=403, detail="无权限访问此课堂")
        elif role == "student":
            student_in_classroom = db.query(db_models.ClassroomStudent).filter(
                db_models.ClassroomStudent.classroom_id == classroom_id,
                db_models.ClassroomStudent.student_id == jwt_uid
            ).first()
            if not student_in_classroom:
                raise HTTPException(status_code=403, detail="无权限访问此课堂")
        else:
            raise HTTPException(status_code=403, detail="无权限访问此课堂")
        
        # 构建查询
        skip = (page - 1) * page_size
        query = db.query(db_models.StudentCourseProgress).options(
            joinedload(db_models.StudentCourseProgress.student),
            joinedload(db_models.StudentCourseProgress.graded_by_teacher),
            joinedload(db_models.StudentCourseProgress.classroom_course),
            joinedload(db_models.StudentCourseProgress.classroom_course, db_models.ClassroomCourse.course)
        ).join(
            db_models.ClassroomCourse,
            db_models.StudentCourseProgress.classroom_course_id == db_models.ClassroomCourse.id
        ).filter(
            db_models.ClassroomCourse.classroom_id == classroom_id,
            db_models.StudentCourseProgress.is_excellent_work == True,
            db_models.StudentCourseProgress.graded_at.isnot(None)
        )
        
        # 课程类型筛选
        if course_type:
            try:
                course_type_enum = db_models.CourseTypeEnum(course_type)
                query = query.join(
                    db_models.Course,
                    db_models.ClassroomCourse.course_id == db_models.Course.id
                ).filter(
                    db_models.Course.course_type == course_type_enum
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的课程类型")
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        excellent_works = query.order_by(
            db_models.StudentCourseProgress.graded_at.desc()
        ).offset(skip).limit(page_size).all()
        
        # 构建响应数据
        excellent_list = []
        for progress in excellent_works:
            excellent_work = {
                "id": progress.id,
                "classroom_course_id": progress.classroom_course_id,
                "course_name": progress.classroom_course.course.title,
                "course_type": progress.classroom_course.course.course_type.value,
                "student_id": progress.student.id,
                "student_name": progress.student.full_name or progress.student.username,
                "student_number": progress.student.username,
                "avatar_url": None,
                "submission_time": progress.last_submission_at,
                "score": progress.overall_score,
                "final_score": progress.final_calculated_score,
                "teacher_feedback": progress.teacher_feedback,
                "graded_at": progress.graded_at,
                "graded_by_teacher_name": progress.graded_by_teacher.full_name if progress.graded_by_teacher else None
            }
            
            excellent_list.append(excellent_work)
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": excellent_list,
                "meta": meta
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课堂优秀作业列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取课堂优秀作业列表失败: {str(e)}")

