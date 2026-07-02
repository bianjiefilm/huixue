"""
P3 成绩系统 API 端点

包括：
- 教师评分
- 学生成绩查询
- 学情分析
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.crud.grading_crud import GradingCRUD
from app import schemas
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def _require_role(current_user: dict, allowed: tuple) -> str:
    """Z1: 从 JWT 取 role, 检查是否在 allowed 列表"""
    role = (current_user.get("roles") or ["student"])[0]
    if role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"需要角色 {allowed}, 当前角色 {role}",
        )
    return role


def _assert_path_id_matches_jwt(path_id: int, current_user: dict, allow_admin: bool = True):
    """Z1: 校验 path 中的 user_id (teacher_id / student_id) 等于 JWT user_id.
    admin 总是可以代理任意 user_id (allow_admin=True)."""
    role = (current_user.get("roles") or ["student"])[0]
    jwt_id = current_user.get("id")
    if allow_admin and role == "admin":
        return
    if path_id != jwt_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="path 中 user_id 与 JWT 不符, 禁止代理他人身份",
        )


# ==================== 教师评分 API ====================

@router.get("/teachers/{teacher_id}/classrooms/{classroom_id}/courses/{course_id}/submissions")
def get_submissions(
    teacher_id: int,
    classroom_id: int,
    course_id: int,
    status: str = Query("all", description="submitted|pending|graded|all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取待评分列表 (Z1: teacher/admin only, path teacher_id 必须 = JWT user_id 或 admin)"""
    try:
        _require_role(current_user, ("teacher", "admin"))
        _assert_path_id_matches_jwt(teacher_id, current_user)

        result = GradingCRUD.get_student_submissions(
            db, course_id, status, page, page_size
        )
        
        return schemas.ApiResponse(
            code="0000",
            message="获取待评分列表成功",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取待评分列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teachers/{teacher_id}/classrooms/{classroom_id}/courses/{course_id}/grade")
def submit_grade(
    teacher_id: int,
    classroom_id: int,
    course_id: int,
    request: schemas.SubmitGradeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """提交成绩和反馈 (Z1: teacher/admin only)"""
    try:
        _require_role(current_user, ("teacher", "admin"))
        _assert_path_id_matches_jwt(teacher_id, current_user)

        progress = GradingCRUD.submit_grade(
            db=db,
            student_id=request.student_id,
            classroom_course_id=course_id,
            overall_score=request.overall_score,
            teacher_penalties=request.teacher_penalties or 0,
            teacher_feedback=request.teacher_feedback or "",
            graded_by_teacher_id=teacher_id,
            is_excellent_work=request.is_excellent_work or False
        )
        
        final_score = progress.overall_score - progress.teacher_penalties
        
        return schemas.ApiResponse(
            code="0000",
            message="评分成功",
            data={
                "student_course_progress_id": progress.id,
                "overall_score": progress.overall_score,
                "teacher_penalties": progress.teacher_penalties,
                "final_score": final_score,
                "graded_at": progress.graded_at.isoformat() if progress.graded_at else None,
                "feedback_saved": True
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交成绩失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/teachers/{teacher_id}/classrooms/{classroom_id}/courses/{course_id}/grade/{student_id}")
def update_grade(
    teacher_id: int,
    classroom_id: int,
    course_id: int,
    student_id: int,
    request: schemas.SubmitGradeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """修改已评分的成绩 (Z1: teacher/admin only)"""
    try:
        _require_role(current_user, ("teacher", "admin"))
        _assert_path_id_matches_jwt(teacher_id, current_user)

        progress = GradingCRUD.submit_grade(
            db=db,
            student_id=student_id,
            classroom_course_id=course_id,
            overall_score=request.overall_score,
            teacher_penalties=request.teacher_penalties or 0,
            teacher_feedback=request.teacher_feedback or "",
            graded_by_teacher_id=teacher_id,
            is_excellent_work=request.is_excellent_work or False
        )
        
        final_score = progress.overall_score - progress.teacher_penalties
        
        return schemas.ApiResponse(
            code="0000",
            message="成绩修改成功",
            data={
                "student_course_progress_id": progress.id,
                "overall_score": progress.overall_score,
                "teacher_penalties": progress.teacher_penalties,
                "final_score": final_score,
                "graded_at": progress.graded_at.isoformat() if progress.graded_at else None,
                "feedback_saved": True
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改成绩失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 学生成绩查询 API ====================

@router.get("/students/{student_id}/classrooms/{classroom_id}/grades")
def get_grades(
    student_id: int,
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取学生成绩单 (Z1: 学生只能看自己, teacher/admin 可看任意)"""
    try:
        role = (current_user.get("roles") or ["student"])[0]
        if role == "student":
            # 学生只能看自己
            _assert_path_id_matches_jwt(student_id, current_user, allow_admin=False)
        elif role not in ("teacher", "admin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

        grades = GradingCRUD.get_student_grades(db, student_id, classroom_id)
        
        if not grades:
            raise HTTPException(status_code=404, detail="课堂不存在")
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成绩单成功",
            data=grades
        )
    except HTTPException as e:
        raise e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取成绩单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classrooms/{classroom_id}/grade-rankings")
def get_rankings(
    classroom_id: int,
    course_id: Optional[int] = Query(None),
    sort_by: str = Query("score", regex="^(score|name)$"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取排名列表 (Z1: teacher/admin only)"""
    try:
        _require_role(current_user, ("teacher", "admin"))

        rankings = GradingCRUD.get_rankings(db, classroom_id, course_id)
        
        # 排序
        if sort_by == "name":
            rankings.sort(key=lambda x: x["student_name"])
        
        # 限制数量
        rankings = rankings[:limit]
        
        return schemas.ApiResponse(
            code="0000",
            message="获取排名成功",
            data=rankings
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取排名失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 学情分析 API ====================

@router.get("/teachers/{teacher_id}/classrooms/{classroom_id}/analytics/overview")
def get_analytics_overview(
    teacher_id: int,
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取班级学情总览 (Z1: teacher/admin only)"""
    try:
        _require_role(current_user, ("teacher", "admin"))
        _assert_path_id_matches_jwt(teacher_id, current_user)

        analytics = GradingCRUD.get_classroom_analytics(db, classroom_id)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取学情总览成功",
            data=analytics
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学情总览失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teachers/{teacher_id}/classrooms/{classroom_id}/analytics/course-stats")
def get_course_stats(
    teacher_id: int,
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取课程统计 (Z1: teacher/admin only)"""
    try:
        _require_role(current_user, ("teacher", "admin"))
        _assert_path_id_matches_jwt(teacher_id, current_user)

        stats = GradingCRUD.get_course_stats(db, classroom_id)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取课程统计成功",
            data=stats
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课程统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
