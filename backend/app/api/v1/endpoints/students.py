"""
学生管理端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
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
    tags=['students']
)

@router.get("/classrooms/{classroom_id}/my-courses", response_model=schemas.ApiResponse)
def get_my_courses(
    classroom_id: int,
    status: Optional[str] = Query(None, description="状态筛选：all, not_started, learning, pending_makeup, completed"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    student_id: int = Query(..., description="学生ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生在课堂中的课程列表（学生端）"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",), forbidden_detail="无权访问该学生课程列表")

        # 验证学生是否在课堂中
        student_in_classroom = db.query(db_models.ClassroomStudent).filter(
            db_models.ClassroomStudent.classroom_id == classroom_id,
            db_models.ClassroomStudent.student_id == student_id
        ).first()
        if not student_in_classroom:
            return schemas.ApiResponse(
                code="4003",
                message="学生不在此课堂中",
                trace_id=str(uuid.uuid4())
            )

        # 基础查询：只显示已发布的课程
        query = db.query(db_models.ClassroomCourse).options(
            joinedload(db_models.ClassroomCourse.course),
            joinedload(db_models.ClassroomCourse.practice)
        ).filter(
            db_models.ClassroomCourse.classroom_id == classroom_id,
            db_models.ClassroomCourse.teacher_publish_status != db_models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
        )
        
        # 关键词搜索
        if keyword:
            query = query.outerjoin(db_models.Course).outerjoin(db_models.Practice).filter(
                or_(
                    db_models.Course.title.ilike(f"%{keyword}%"),
                    db_models.Practice.title.ilike(f"%{keyword}%"),
                    db_models.ClassroomCourse.classroom_chapter_title.ilike(f"%{keyword}%")
                )
            )
        
        # 获取学生进度信息
        skip = (page - 1) * page_size
        classroom_courses = query.order_by(
            db_models.ClassroomCourse.order_in_classroom, 
            db_models.ClassroomCourse.id
        ).offset(skip).limit(page_size).all()
        
        # 构建响应数据
        course_list = []
        for classroom_course in classroom_courses:
            # 获取学生进度
            progress = crud.get_student_course_progress(
                db, classroom_course.id, student_id
            )
            
            # 判断这是来源于 course 还是 practice
            is_practice = classroom_course.practice is not None
            source_obj = classroom_course.practice if is_practice else classroom_course.course
            if not source_obj:
                continue
                
            course_type = "PRACTICE" if is_practice else source_obj.course_type
            
            course_data = {
                "id": classroom_course.id,
                "course_id": classroom_course.course_id or classroom_course.practice_id,
                "title": classroom_course.classroom_chapter_title or source_obj.title,
                "course_type": course_type,
                "cover_url": source_obj.cover_url,
                "difficulty": source_obj.difficulty,
                "teacher_status": classroom_course.teacher_publish_status,
                "student_status": progress.student_status if progress else db_models.CourseInClassroomStatusStudentEnum.NOT_STARTED,
                "deadline_at": classroom_course.deadline_at,
                "makeup_deadline_at": classroom_course.makeup_deadline_at,
                "is_mandatory": classroom_course.is_mandatory,
                "total_score": classroom_course.total_score,
                "student_score": progress.final_calculated_score if progress else 0,
                "completed_task_count": progress.completed_task_count if progress else 0,
                "total_time_spent_seconds": progress.total_time_spent_seconds if progress else 0,
                "first_access_at": progress.first_access_at if progress else None,
                "last_submission_at": progress.last_submission_at if progress else None
            }
            
            # 状态筛选
            if status and status != "all":
                student_status = course_data["student_status"]
                if status == "not_started" and student_status != db_models.CourseInClassroomStatusStudentEnum.NOT_STARTED:
                    continue
                elif status == "learning" and student_status != db_models.CourseInClassroomStatusStudentEnum.LEARNING:
                    continue
                elif status == "pending_makeup" and student_status != db_models.CourseInClassroomStatusStudentEnum.PENDING_MAKEUP:
                    continue
                elif status == "completed" and student_status not in [
                    db_models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME,
                    db_models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
                ]:
                    continue
            
            course_list.append(course_data)
        
        total = len(course_list)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "courses": course_list,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}\n\n{error_msg}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 课程详情相关API ====================


@router.get("/classrooms/{classroom_id}/practices", response_model=schemas.ApiResponse)
def get_classroom_practices(
    classroom_id: int,
    student_id: int = Query(..., description="学生ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课堂中的实践课程列表（学生端）"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",), forbidden_detail="无权访问该学生实践列表")
        # 验证学生是否在课堂中
        student_in_classroom = db.query(db_models.ClassroomStudent).filter(
            db_models.ClassroomStudent.classroom_id == classroom_id,
            db_models.ClassroomStudent.student_id == student_id
        ).first()
        
        if not student_in_classroom:
            return schemas.ApiResponse(
                code="4003",
                message="学生不在此课堂中",
                trace_id=str(uuid.uuid4())
            )
        
        # 查询课堂关联的课程（只查询已发布的，不局限于PRACTICE，因为会有单纯的实践和课程中的实践）
        query = db.query(db_models.ClassroomCourse).options(
            joinedload(db_models.ClassroomCourse.course),
            joinedload(db_models.ClassroomCourse.practice)
        ).filter(
            db_models.ClassroomCourse.classroom_id == classroom_id,
            db_models.ClassroomCourse.teacher_publish_status != db_models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
        )
        
        # 分页
        skip = (page - 1) * page_size
        total = query.count()
        classroom_courses = query.offset(skip).limit(page_size).all()
        
        # 构建响应数据
        practice_list = []
        for cc in classroom_courses:
            # 判断逻辑：是否是一个单独添加到课堂的 practice?
            if cc.practice:
                practice = cc.practice
                progress = db.query(db_models.StudentCourseProgress).filter(
                    db_models.StudentCourseProgress.student_id == student_id,
                    db_models.StudentCourseProgress.classroom_course_id == cc.id
                ).first()
                
                difficulty_value = practice.difficulty.value if hasattr(practice.difficulty, 'value') else practice.difficulty
                practice_type_value = practice.practice_type.value if hasattr(practice.practice_type, 'value') else practice.practice_type

                practice_data = {
                    "id": practice.id,
                    "title": practice.title,
                    "description": practice.description,
                    "cover_url": practice.cover_url,
                    "difficulty": difficulty_value,
                    "task_count": practice.task_count or 0,
                    "coin": practice.coin or 0,
                    "practice_type": practice_type_value,
                    "course_id": practice.id,  # 兼容前端统一显示为 course_id
                    "classroom_course_id": cc.id,
                    "status": progress.student_status.value if progress and progress.student_status else "not_started",
                    "completed_tasks": progress.completed_task_count if progress else 0,
                    "score": progress.final_calculated_score if progress else None,
                    "deadline": cc.deadline_at.isoformat() if cc.deadline_at else None
                }
                practice_list.append(practice_data)
                
            elif cc.course:
                # 原有的逻辑，判断course_type是否为PRACTICE（兼容枚举和字符串）
                course_type_value = cc.course.course_type.value if hasattr(cc.course.course_type, 'value') else str(cc.course.course_type)
                if course_type_value == 'PRACTICE':
                    # 获取关联的practice
                    practice = db.query(db_models.Practice).filter(
                        db_models.Practice.parent_course_id == cc.course_id
                    ).first()

                    # 获取学生进度
                    progress = db.query(db_models.StudentCourseProgress).filter(
                        db_models.StudentCourseProgress.student_id == student_id,
                        db_models.StudentCourseProgress.classroom_course_id == cc.id
                    ).first()

                    if practice:
                        difficulty_value = practice.difficulty.value if hasattr(practice.difficulty, 'value') else practice.difficulty
                        practice_type_value = practice.practice_type.value if hasattr(practice.practice_type, 'value') else practice.practice_type

                        practice_data = {
                            "id": practice.id,
                            "title": practice.title,
                            "description": practice.description,
                            "cover_url": practice.cover_url,
                            "difficulty": difficulty_value,
                            "task_count": practice.task_count or 0,
                            "coin": practice.coin or 0,
                            "practice_type": practice_type_value,
                            "course_id": cc.course_id,
                            "classroom_course_id": cc.id,
                            "status": progress.student_status.value if progress and progress.student_status else "not_started",
                            "completed_tasks": progress.completed_task_count if progress else 0,
                            "score": progress.final_calculated_score if progress else None,
                            "deadline": cc.deadline_at.isoformat() if cc.deadline_at else None
                        }
                        practice_list.append(practice_data)
                    else:
                        course = cc.course
                        difficulty_value = course.difficulty.value if hasattr(course.difficulty, 'value') else (course.difficulty or 'beginner')

                        practice_data = {
                            "id": course.id,
                            "title": course.title,
                            "description": course.description,
                            "cover_url": course.cover_url,
                            "difficulty": difficulty_value,
                            "task_count": 0,
                            "coin": 0,
                            "practice_type": "course",
                            "course_id": cc.course_id,
                            "classroom_course_id": cc.id,
                            "status": progress.student_status.value if progress and progress.student_status else "not_started",
                            "completed_tasks": progress.completed_task_count if progress else 0,
                            "score": progress.final_calculated_score if progress else None,
                            "deadline": cc.deadline_at.isoformat() if cc.deadline_at else None
                        }
                        practice_list.append(practice_data)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": practice_list,
                "meta": {
                    "total": len(practice_list),
                    "page": page,
                    "page_size": page_size
                }
            }
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课堂实践列表失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"获取失败: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/classrooms/{classroom_id}/students", response_model=schemas.ApiResponse)
async def get_classroom_students(
    classroom_id: int,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    teacher_id: int = Query(..., description="教师ID，用于权限验证"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课堂学生列表"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        # 检查教师权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课堂")
        
        skip = (page - 1) * page_size
        classroom_students, total = crud.get_classroom_students(
            db, classroom_id, keyword, skip, page_size
        )
        
        # 构建响应数据
        student_list = []
        for cs in classroom_students:
            student_data = {
                "id": cs.student.id,
                "username": cs.student.username,
                "full_name": cs.student.full_name,
                "email": cs.student.email,
                "student_number": cs.student.username,  # 暂时用username作为学号
                "department": None,  # 暂时为空，实际应该从用户扩展信息获取
                "major": None,
                "grade": None,
                "avatar_url": None,
                "joined_at": cs.joined_at
            }
            student_list.append(student_data)
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": student_list,
                "meta": meta
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课堂学生列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取课堂学生列表失败: {str(e)}")


@router.get("/classrooms/{classroom_id}/students/available", response_model=schemas.ApiResponse)
async def get_available_students(
    classroom_id: int,
    keyword: Optional[str] = None,
    department: Optional[str] = None,
    major: Optional[str] = None,
    grade: Optional[str] = None,
    organization_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    teacher_id: int = Query(..., description="教师ID，用于权限验证"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取可添加的学生列表（支持组织筛选，排除已在课堂的学生）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        # 检查教师权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课堂")
        
        skip = (page - 1) * page_size
        students, total = crud.get_students_by_search(
            db=db, 
            keyword=keyword, 
            department=department, 
            major=major, 
            grade=grade, 
            organization_id=organization_id,
            exclude_classroom_id=classroom_id, 
            skip=skip, 
            limit=page_size
        )
        
        # 构建响应数据
        student_list = []
        for student in students:
            student_data = {
                "id": student.id,
                "username": student.username,
                "full_name": student.full_name,
                "email": student.email,
                "student_number": student.username,  # 暂时用username作为学号
                "department": department,  # 使用查询参数
                "major": major,
                "grade": grade,
                "avatar_url": None,
                "joined_at": None
            }
            student_list.append(student_data)
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": student_list,
                "meta": meta
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取可添加学生列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取可添加学生列表失败: {str(e)}")


@router.post("/classrooms/{classroom_id}/students", response_model=schemas.ApiResponse)
async def add_students_to_classroom(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID，用于权限验证"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: schemas.AddStudentsRequest = None
):
    """批量添加学生到课堂"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权操作此课堂")
        # 首先检查课堂是否存在
        classroom = db.query(db_models.Classroom).filter(
            db_models.Classroom.id == classroom_id
        ).first()
        if not classroom:
            raise HTTPException(status_code=404, detail="课堂不存在")

        # 检查教师权限（必须是课堂的创建者）
        if classroom.teacher_id != teacher_id:
            raise HTTPException(status_code=403, detail="无权限操作此课堂")
        
        # 验证请求体
        if not request or not request.student_ids:
            raise HTTPException(status_code=400, detail="学生ID列表不能为空")
        
        result = crud.add_students_to_classroom(db, classroom_id, request.student_ids)
        
        message = f"成功添加 {result['added_count']} 名学生"
        if result['already_exists_count'] > 0:
            message += f"，{result['already_exists_count']} 名学生已在课堂中"
        if result['not_found_count'] > 0:
            message += f"，{result['not_found_count']} 名学生不存在"
        
        return schemas.ApiResponse(
            code="0000",
            message=message,
            data=result
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加学生到课堂失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加学生到课堂失败: {str(e)}")


@router.delete("/classrooms/{classroom_id}/students", response_model=schemas.ApiResponse)
async def remove_students_from_classroom(
    classroom_id: int,
    request: schemas.RemoveStudentsRequest,
    teacher_id: int = Query(..., description="教师ID，用于权限验证"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量从课堂移除学生"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        # 检查教师权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课堂")
        
        if not request.student_ids:
            raise HTTPException(status_code=400, detail="学生ID列表不能为空")
        
        result = crud.remove_students_from_classroom(db, classroom_id, request.student_ids)
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功移除 {result['removed_count']} 名学生",
            data=result
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从课堂移除学生失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"从课堂移除学生失败: {str(e)}")


@router.get("/classrooms/{classroom_id}/students/management", response_model=schemas.ApiResponse)
async def get_student_management(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID，用于权限验证"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生管理页面数据（组织架构树 + 可选学生列表）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权访问该课堂")
        # 检查教师权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课堂")
        
        # 获取组织架构树
        organization_tree = crud.get_organization_tree(db)
        
        # 获取可选学生列表（默认前20个）
        students, total = crud.get_students_by_search(
            db, exclude_classroom_id=classroom_id, skip=0, limit=20
        )
        
        # 构建学生列表
        student_list = []
        for student in students:
            student_data = {
                "id": student.id,
                "username": student.username,
                "full_name": student.full_name,
                "email": student.email,
                "student_number": student.username,
                "department": None,
                "major": None,
                "grade": None,
                "avatar_url": None,
                "joined_at": None
            }
            student_list.append(student_data)
        
        available_students = {
            "list": student_list,
            "meta": {
                "total": total,
                "page": 1,
                "page_size": 20
            }
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "organization_tree": organization_tree,
                "available_students": available_students,
                "selected_students": []
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生管理页面数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取学生管理页面数据失败: {str(e)}")

# ==================== 课程添加和发布API ====================

# 4.5.1 按课表添加课程

@router.patch("/student-progress/{progress_id}/excellent", response_model=schemas.ApiResponse)
def mark_student_excellent(
    progress_id: int,
    request: schemas.ExcellentWorkRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """设置优秀作业"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",), forbidden_detail="无权设置优秀作业")
        updated_progress = crud.set_excellent_work(
            db, progress_id, teacher_id, request.is_excellent
        )
        
        if updated_progress is None:
            raise HTTPException(status_code=404, detail="学生进度记录不存在、未点评或无权限访问")
        
        action = "设置为优秀作业" if request.is_excellent else "取消优秀作业"
        
        return schemas.ApiResponse(
            code="0000",
            message=f"{action}成功",
            data={
                "id": updated_progress.id,
                "is_excellent": updated_progress.is_excellent_work
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置优秀作业失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"设置优秀作业失败: {str(e)}")


@router.get("/user/classrooms", response_model=schemas.ApiResponse)
def get_student_classrooms(
    student_id: int = Query(..., description="学生ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生的课堂列表（按状态分组）"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",), forbidden_detail="无权访问该学生课堂列表")
        # 查询学生加入的所有课堂
        student_classrooms = db.query(db_models.Classroom).join(
            db_models.ClassroomStudent,
            db_models.Classroom.id == db_models.ClassroomStudent.classroom_id
        ).filter(
            db_models.ClassroomStudent.student_id == student_id
        ).all()

        # 按状态分组
        ongoing = []
        upcoming = []
        past = []

        # 使用 timezone-naive datetime 以兼容数据库中的日期
        current_time = datetime.now()

        for classroom in student_classrooms:
            classroom_data = {
                "id": classroom.id,
                "name": classroom.name,
                "teacher_id": classroom.teacher_id,
                "start_date": classroom.start_date.isoformat() if classroom.start_date else None,
                "end_date": classroom.end_date.isoformat() if classroom.end_date else None,
                "status": classroom.status.value if hasattr(classroom.status, 'value') else classroom.status,
                "student_count": classroom.student_count,
                "experiments_count": classroom.experiments_count or 0,
                "experiment_levels_count": classroom.experiment_levels_count or 0,
                "coins_count": classroom.coins_count or 0,
                "finished_experiments_count": classroom.finished_experiments_count or 0,
                "cover_url": classroom.cover_url
            }

            # 安全比较日期（处理 timezone-aware 和 timezone-naive 混合情况）
            try:
                start_date = classroom.start_date
                if start_date and hasattr(start_date, 'tzinfo') and start_date.tzinfo is not None:
                    start_date = start_date.replace(tzinfo=None)

                if classroom.status == db_models.ClassroomStatusEnum.ONGOING:
                    ongoing.append(classroom_data)
                elif start_date and start_date > current_time:
                    upcoming.append(classroom_data)
                else:
                    past.append(classroom_data)
            except Exception:
                # 如果日期比较失败，默认归类到 past
                past.append(classroom_data)

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "ongoing": ongoing,
                "upcoming": upcoming,
                "past": past
            }
        )

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生课堂列表失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


