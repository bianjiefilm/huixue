"""
考试管理端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import uuid
import logging
from datetime import datetime, timezone, timedelta
import io
import urllib.parse

# 修正的导入路径
from app.core.database import get_db, engine, Base
from app.core.security import get_current_user
from app.core.identity import resolve_scoped_id, require_authenticated
from app.models import models as db_models  # 避免与FastAPI的models冲突
from app.crud import crud
from app.schemas import schemas

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/api/v1",
    tags=['exams']
)

# ==================== 课程考核管理API ====================

@router.get("/exams", response_model=schemas.ApiResponse)
def get_teacher_exams(
    teacher_id: int = Query(..., description="教师ID"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="考试状态筛选"),
    classroom_id: Optional[int] = Query(None, description="课堂ID筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取教师的所有考试列表

    支持按关键词、状态、课堂筛选
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        skip = (page - 1) * page_size
        
        # 查询教师所有课堂的考试
        query = db.query(db_models.ClassroomExam).join(
            db_models.Classroom,
            db_models.ClassroomExam.classroom_id == db_models.Classroom.id
        ).filter(
            db_models.Classroom.teacher_id == teacher_id,
            db_models.Classroom.deleted_at.is_(None)
        )
        
        # 关键词搜索
        if keyword:
            query = query.filter(db_models.ClassroomExam.title.contains(keyword))
        
        # 状态筛选
        if status:
            try:
                status_enum = db_models.ExamStatusEnum(status)
                query = query.filter(db_models.ClassroomExam.status == status_enum)
            except ValueError:
                pass
        
        # 课堂筛选
        if classroom_id:
            query = query.filter(db_models.ClassroomExam.classroom_id == classroom_id)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        exams = query.order_by(
            db_models.ClassroomExam.created_at.desc()
        ).offset(skip).limit(page_size).all()
        
        # 构建返回数据
        exam_list = []
        for exam in exams:
            # 获取课堂信息
            classroom = db.query(db_models.Classroom).filter(
                db_models.Classroom.id == exam.classroom_id
            ).first()
            
            # 获取试卷信息
            test_paper = db.query(db_models.TestPaper).filter(
                db_models.TestPaper.id == exam.test_paper_id
            ).first()
            
            # 统计答卷情况
            attempt_count = db.query(db_models.StudentExamAttempt).filter(
                db_models.StudentExamAttempt.classroom_exam_id == exam.id
            ).count()
            
            graded_count = db.query(db_models.StudentExamAttempt).filter(
                db_models.StudentExamAttempt.classroom_exam_id == exam.id,
                db_models.StudentExamAttempt.is_graded == True
            ).count()
            
            exam_list.append({
                "id": exam.id,
                "title": exam.title,
                "classroom_id": exam.classroom_id,
                "classroom_name": classroom.name if classroom else "",
                "test_paper_id": exam.test_paper_id,
                "test_paper_title": test_paper.title if test_paper else "",
                "status": exam.status.value if exam.status else "UNPUBLISHED",
                "exam_start_time": exam.exam_start_time.isoformat() if exam.exam_start_time else None,
                "exam_end_time": exam.exam_end_time.isoformat() if exam.exam_end_time else None,
                "duration_minutes": exam.duration_minutes,
                "pass_mark": exam.pass_mark,
                "attempt_count": attempt_count,
                "graded_count": graded_count,
                "created_at": exam.created_at.isoformat() if exam.created_at else None
            })
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": exam_list,
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
        logger.error(f"获取教师考试列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取考试列表失败: {str(e)}")


@router.get("/classrooms/{classroom_id}/test-papers", response_model=schemas.ApiResponse)
def get_test_papers_for_selection(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    keyword: Optional[str] = Query(None, description="试卷名称搜索"),
    difficulty: Optional[str] = Query(None, description="难度筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取可选择的试卷列表（用于创建考试时选择试卷）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课堂")
        
        skip = (page - 1) * page_size
        paper_list, total = crud.get_test_papers_for_selection(
            db, teacher_id, keyword, difficulty, skip, page_size
        )
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": paper_list,
                "meta": meta
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取试卷列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取试卷列表失败: {str(e)}")


@router.post("/classrooms/{classroom_id}/exams", response_model=schemas.ApiResponse)
def create_classroom_exam(
    classroom_id: int,
    request: schemas.ExamCreateRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建考试"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        exam = crud.create_classroom_exam(
            db, classroom_id, teacher_id, request.title, request.test_paper_id
        )
        
        if exam is None:
            raise HTTPException(status_code=404, detail="试卷不存在或无权限访问")
        
        return schemas.ApiResponse(
            code="0000",
            message="考试创建成功",
            data={
                "exam_id": exam.id,
                "title": exam.title,
                "status": exam.status.value,
                "test_paper_id": exam.test_paper_id
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建考试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建考试失败: {str(e)}")


@router.get("/classrooms/{classroom_id}/exams", response_model=schemas.ApiResponse)
def get_classroom_exams(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课堂考试列表"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        skip = (page - 1) * page_size
        result = crud.get_classroom_exams(db, classroom_id, teacher_id, skip, page_size)
        
        if result[0] is None:
            raise HTTPException(status_code=403, detail="无权限访问此课堂")
        
        exam_list, total, stats = result
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": exam_list,
                "meta": meta,
                "stats": stats
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取考试列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取考试列表失败: {str(e)}")


@router.get("/classrooms/{classroom_id}/exams/student", response_model=schemas.ApiResponse)
def get_classroom_exams_for_student(
    classroom_id: int,
    student_id: int = Query(..., description="学生ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生视角的课堂考试列表"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))
        # 验证学生是否在该课堂
        is_student_in_classroom = db.query(db_models.ClassroomStudent).filter(
            db_models.ClassroomStudent.classroom_id == classroom_id,
            db_models.ClassroomStudent.student_id == student_id
        ).first() is not None
        
        if not is_student_in_classroom:
            raise HTTPException(status_code=403, detail="您不是该课堂的学生")
        
        skip = (page - 1) * page_size
        
        # 查询已发布的考试（学生只能看到非UNPUBLISHED状态的考试）
        exams = db.query(db_models.ClassroomExam).options(
            joinedload(db_models.ClassroomExam.test_paper)
        ).filter(
            db_models.ClassroomExam.classroom_id == classroom_id,
            db_models.ClassroomExam.status != db_models.ExamStatusEnum.UNPUBLISHED
        ).order_by(db_models.ClassroomExam.created_at.desc()).offset(skip).limit(page_size).all()
        
        total = db.query(db_models.ClassroomExam).filter(
            db_models.ClassroomExam.classroom_id == classroom_id,
            db_models.ClassroomExam.status != db_models.ExamStatusEnum.UNPUBLISHED
        ).count()
        
        exam_list = []
        for exam in exams:
            # 检查学生是否已提交
            attempt = db.query(db_models.StudentExamAttempt).filter(
                db_models.StudentExamAttempt.classroom_exam_id == exam.id,
                db_models.StudentExamAttempt.student_id == student_id
            ).first()
            
            exam_list.append({
                "id": exam.id,
                "title": exam.title,
                "exam_start_time": exam.exam_start_time.isoformat() if exam.exam_start_time else None,
                "exam_end_time": exam.exam_end_time.isoformat() if exam.exam_end_time else None,
                "duration_minutes": exam.duration_minutes,
                "pass_mark": exam.pass_mark,
                "status": exam.status.value if exam.status else None,
                "test_paper_name": exam.test_paper.title if exam.test_paper else None,
                "student_submitted": attempt is not None,
                "student_score": attempt.total_score_achieved if attempt else None,
                "is_graded": attempt.is_graded if attempt else False
            })
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": exam_list,
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
        logger.error(f"获取学生考试列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取考试列表失败: {str(e)}")


@router.patch("/exams/{exam_id}/publish", response_model=schemas.ApiResponse)
def publish_exam(
    exam_id: int,
    request: schemas.ExamPublishRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发布考试"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud.publish_classroom_exam(
            db, exam_id, teacher_id,
            request.exam_start_time,
            request.exam_end_time,
            request.duration_minutes,
            request.pass_mark,
            request.shuffle_questions,
            request.shuffle_options
        )
        
        if result is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return schemas.ApiResponse(
            code="0000",
            message="考试发布成功",
            data={
                "exam_id": result.id,
                "title": result.title,
                "status": result.status.value,
                "exam_start_time": result.exam_start_time,
                "exam_end_time": result.exam_end_time
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发布考试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"发布考试失败: {str(e)}")


@router.patch("/exams/{exam_id}", response_model=schemas.ApiResponse)
def update_exam(
    exam_id: int,
    request: schemas.ExamUpdateRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新考试信息（设置）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 过滤掉None值
        update_data = {k: v for k, v in request.model_dump().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供要更新的数据")
        
        result = crud.update_classroom_exam(db, exam_id, teacher_id, **update_data)
        
        if result is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return schemas.ApiResponse(
            code="0000",
            message="考试信息更新成功",
            data={
                "exam_id": result.id,
                "title": result.title,
                "status": result.status.value
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新考试信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新考试信息失败: {str(e)}")


@router.patch("/exams/{exam_id}/rename", response_model=schemas.ApiResponse)
def rename_exam(
    exam_id: int,
    request: schemas.ExamRenameRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重命名考试"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud.rename_classroom_exam(db, exam_id, teacher_id, request.title)
        
        if result is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return schemas.ApiResponse(
            code="0000",
            message="考试重命名成功",
            data={
                "exam_id": result.id,
                "title": result.title
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重命名考试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重命名考试失败: {str(e)}")


@router.delete("/exams/{exam_id}", response_model=schemas.ApiResponse)
def delete_exam(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除考试"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud.delete_classroom_exam(db, exam_id, teacher_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return schemas.ApiResponse(
            code="0000",
            message="考试删除成功",
            data=result
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除考试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除考试失败: {str(e)}")


@router.get("/exams/{exam_id}/detail", response_model=schemas.ApiResponse)
def get_exam_detail(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取考试详情"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud.get_classroom_exam_detail(db, exam_id, teacher_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data=result
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取考试详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取考试详情失败: {str(e)}")

# ==================== 考试阅卷相关API ====================

@router.get("/exams/{exam_id}/papers", response_model=schemas.ApiResponse)
def get_unmarked_students(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    unmarked: bool = Query(False, description="是否只显示未阅卷的"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取考试的待阅卷学生列表

    从课程考核中进入阅卷：在课程考核页面中，对于考试中或者已完成的考试，
    点击"阅卷"按钮，可跳转至未阅卷学生试卷详情页中，进行阅卷
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud.get_exam_unmarked_students(db, exam_id, teacher_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        # 如果只显示未阅卷的，过滤已阅卷的学生
        if unmarked:
            result["students"] = [s for s in result["students"] if s["status"] == "submitted"]
            result["unmarked_count"] = len(result["students"])
        
        return {
            "code": "0000",
            "message": "获取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取待阅卷学生列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/exams/{exam_id}/papers/{student_id}", response_model=schemas.ExamPaperDetail)
def get_exam_paper_detail(
    exam_id: int,
    student_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取学生试卷详情（用于阅卷）

    从考试详情中进入阅卷：
    1. 在考试详情页面中，点击右上角"阅卷"按钮，可跳转至未阅卷学生试卷详情页中，进行阅卷
    2. 在考试详情页面中，点击列表中对应学生后方的"阅卷"按钮，可跳转至该学生试卷详情页中，进行阅卷
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud.get_student_exam_paper(db, exam_id, student_id, teacher_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="试卷不存在或无权限访问")
        
        return {
            "code": "0000",
            "message": "获取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生试卷详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/exams/{exam_id}/papers/{student_id}/marks", response_model=schemas.EnhancedSubmitMarksResponse)
def submit_marks(
    exam_id: int,
    student_id: int,
    request: schemas.SubmitMarksRequest,
    teacher_id: int = Query(..., description="教师ID"),
    auto_next: bool = Query(False, description="是否自动跳转到下一份试卷"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    提交试卷评分
    
    试卷评阅：
    1. 试卷评阅时区分主观题和客观题，简答题属于主观题，除简答外的单选、多选、判断题属于客观题；
       主观题需要教师进行评分，客观题自动判题得分，点击左侧题目标号可跳转至对应题目处
    2. 对于主观题，教师可根据题目总分及学生答题情况赋予对应的分值，可选填教师评语；
       左侧悬浮窗及试题底色都通过颜色区分试题状态，可快速找到未评分题目进行评分
    3. 所有主观题目完成评分后，点击右侧悬浮栏中"提交评分"按钮即可提交评分，完成试卷评阅
    
    批量阅卷模式：设置auto_next=true时，提交评分后会自动返回下一份待阅卷试卷的信息
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        marks_data = {
            "marks": [mark.model_dump() for mark in request.marks],
            "overall_comments": request.overall_comments
        }
        
        result = crud.submit_exam_marks(db, exam_id, student_id, teacher_id, marks_data)
        
        if result is None:
            raise HTTPException(status_code=404, detail="试卷不存在或无权限访问")
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # 批量阅卷模式：自动获取下一份待阅卷试卷
        next_student = None
        if auto_next:
            next_student = crud.get_next_unmarked_student(db, exam_id, student_id, teacher_id)
        
        response_data = result.copy()
        if next_student:
            response_data["next_student"] = next_student
        
        return {
            "code": "0000",
            "message": "评分提交成功",
            "data": response_data
        }
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交试卷评分失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/exams/{exam_id}/papers/{student_id}/view")
def view_exam_paper(
    exam_id: int,
    student_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查看学生试卷（只读模式）

    查看学生试卷：在考试详情页中，点击学生列表中对应学生后的"查看试卷"按钮，
    即可查看该学生的试卷答题情况
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud.get_student_exam_paper(db, exam_id, student_id, teacher_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="试卷不存在或无权限访问")
        
        # 添加只读标识
        result["readonly"] = True
        
        return {
            "code": "0000",
            "message": "获取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查看学生试卷失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/exams/{exam_id}/grading-progress", response_model=schemas.GradingProgressResponse)
def get_grading_progress(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取阅卷进度信息

    返回考试的整体阅卷进度，包括已阅卷数量、未阅卷数量等统计信息
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud.get_exam_grading_progress(db, exam_id, teacher_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        return {
            "code": "0000",
            "message": "获取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取阅卷进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/exams/{exam_id}/statistics", response_model=schemas.ExamStatistics)
def get_exam_statistics(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取考试统计信息
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud.get_exam_statistics(db, exam_id, teacher_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        return {
            "code": "0000",
            "message": "获取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取考试统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/exams/{exam_id}/auto-grade")
def auto_grade_exam(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    自动评分客观题

    对考试中的单选题、多选题、判断题进行自动评分
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 检查教师权限
        exam = db.query(db_models.ClassroomExam).filter(
            db_models.ClassroomExam.id == exam_id
        ).first()
        
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        
        if not crud.check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此考试")
        
        success = crud.auto_grade_objective_questions(db, exam_id)
        
        if success:
            return {
                "code": "0000",
                "message": "客观题自动评分完成",
                "data": {"success": True}
            }
        else:
            raise HTTPException(status_code=500, detail="自动评分失败")
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"自动评分客观题失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/exams/{exam_id}/batch-auto-grade", response_model=schemas.BatchAutoGradeResponse)
def batch_auto_grade_objective_questions(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量自动评分所有客观题

    对考试中所有已提交的试卷进行客观题自动评分
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 检查教师权限
        exam = db.query(db_models.ClassroomExam).filter(
            db_models.ClassroomExam.id == exam_id
        ).first()
        
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        
        if not crud.check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此考试")
        
        result = crud.batch_auto_grade_objective_questions(db, exam_id)
        
        return {
            "code": "0000",
            "message": "批量自动评分完成",
            "data": result
        }
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量自动评分失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

# ==================== 考试完成情况查看API ====================

@router.get("/exams/{exam_id}/scores", response_model=schemas.ApiResponse)
def get_exam_scores(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    sort_field: str = Query("score", description="排序字段: score, duration, submission_time, student_name"),
    sort_order: str = Query("desc", description="排序方向: asc, desc"),
    keyword: Optional[str] = Query(None, description="搜索学生姓名或学号"),
    status_filter: Optional[str] = Query(None, description="状态筛选: submitted, graded, not_submitted"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取考试成绩统计"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        skip = (page - 1) * page_size
        scores, total, extra_data = crud.get_exam_scores_with_students(
            db, exam_id, teacher_id, sort_field, sort_order, keyword, status_filter, skip, page_size
        )
        
        if scores is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "exam_info": extra_data["exam_info"],
                "students": scores,
                "meta": meta,
                "statistics": extra_data["statistics"]
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取考试成绩统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取考试成绩统计失败: {str(e)}")


@router.get("/exams/{exam_id}/distribution", response_model=schemas.ApiResponse)
def get_exam_score_distribution(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取考试成绩分布"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud.get_exam_score_distribution(db, exam_id, teacher_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data=result
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取考试成绩分布失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取考试成绩分布失败: {str(e)}")


@router.patch("/exams/{exam_id}/distribution", response_model=schemas.ApiResponse)
def update_exam_score_ranges(
    exam_id: int,
    request: schemas.UpdateScoreRangesRequest,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新考试分数段设置"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        ranges = [range_obj.dict() for range_obj in request.ranges]
        result = crud.update_exam_score_ranges(
            db, exam_id, teacher_id, ranges, request.enable_custom_labels
        )
        
        if result is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return schemas.ApiResponse(
            code="0000",
            message="分数段设置更新成功",
            data={"success": True}
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新分数段设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新分数段设置失败: {str(e)}")


@router.get("/exams/{exam_id}/questions/stats", response_model=schemas.ApiResponse)
def get_exam_question_analysis(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取考试试题分析"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        skip = (page - 1) * page_size
        questions, total, extra_data = crud.get_exam_question_analysis(
            db, exam_id, teacher_id, skip, page_size
        )
        
        if questions is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "exam_info": extra_data["exam_info"],
                "questions": questions,
                "meta": meta,
                "overall_statistics": extra_data["overall_statistics"]
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取试题分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取试题分析失败: {str(e)}")


@router.get("/exams/{exam_id}/scores/export")
def export_exam_scores(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    sort_field: str = Query("score", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    export_format: str = Query("xlsx", description="导出格式: xlsx, csv"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出考试成绩"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud.export_exam_scores(
            db, exam_id, teacher_id, sort_field, sort_order, keyword, status_filter, export_format
        )
        
        if result is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        file_content, filename, content_type = result
        
        from fastapi.responses import StreamingResponse
        
        # 对文件名进行URL编码以支持中文
        encoded_filename = urllib.parse.quote(filename.encode('utf-8'))
        
        return StreamingResponse(
            io.BytesIO(file_content.read()),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出考试成绩失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出考试成绩失败: {str(e)}")


# ==================== 学生考试作答API ====================

@router.get("/classroom-exams/{exam_id}", response_model=schemas.ApiResponse)
def get_exam_for_student(
    exam_id: int,
    student_id: int = Query(..., description="学生ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取考试信息（学生视角）
    """
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))
        exam = db.query(db_models.ClassroomExam).filter(
            db_models.ClassroomExam.id == exam_id
        ).first()
        
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        
        # 获取试卷信息
        test_paper = db.query(db_models.TestPaper).filter(
            db_models.TestPaper.id == exam.test_paper_id
        ).first()
        
        # 检查学生是否已提交
        attempt = db.query(db_models.StudentExamAttempt).filter(
            db_models.StudentExamAttempt.classroom_exam_id == exam_id,
            db_models.StudentExamAttempt.student_id == student_id
        ).first()
        
        # 判断是否已提交：通过 attempt_submission_time 是否有值
        is_submitted = attempt is not None and attempt.attempt_submission_time is not None
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "id": exam.id,
                "title": exam.title,
                "exam_start_time": exam.exam_start_time.isoformat() if exam.exam_start_time else None,
                "exam_end_time": exam.exam_end_time.isoformat() if exam.exam_end_time else None,
                "duration_minutes": exam.duration_minutes,
                "pass_mark": exam.pass_mark,
                "status": exam.status.value if exam.status else None,
                "test_paper_name": test_paper.title if test_paper else None,
                "student_submitted": is_submitted,
                "student_score": attempt.total_score_achieved if attempt and attempt.is_graded else None
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取考试信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取考试信息失败: {str(e)}")


@router.get("/classroom-exams/{exam_id}/questions", response_model=schemas.ApiResponse)
def get_exam_questions(
    exam_id: int,
    student_id: int = Query(..., description="学生ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取考试试题（学生作答用）
    """
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))
        exam = db.query(db_models.ClassroomExam).filter(
            db_models.ClassroomExam.id == exam_id
        ).first()
        
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        
        # 检查考试状态
        now = datetime.now(timezone.utc)
        if exam.status != db_models.ExamStatusEnum.ONGOING:
            raise HTTPException(status_code=400, detail="考试未在进行中")
        
        # 检查学生是否已提交
        attempt = db.query(db_models.StudentExamAttempt).filter(
            db_models.StudentExamAttempt.classroom_exam_id == exam_id,
            db_models.StudentExamAttempt.student_id == student_id
        ).first()
        
        # 判断是否已提交
        is_submitted = attempt is not None and attempt.attempt_submission_time is not None
        if is_submitted:
            raise HTTPException(status_code=400, detail="您已提交本次考试")
        
        # 获取试卷问题
        paper_questions = db.query(db_models.TestPaperQuestion).filter(
            db_models.TestPaperQuestion.test_paper_id == exam.test_paper_id
        ).order_by(db_models.TestPaperQuestion.order_in_paper).all()
        
        questions = []
        for pq in paper_questions:
            question = db.query(db_models.Question).filter(
                db_models.Question.id == pq.question_id
            ).first()
            
            if question:
                # 解析选项（存储为JSON字符串）
                options = []
                if question.options:
                    import json
                    try:
                        options = json.loads(question.options) if isinstance(question.options, str) else question.options
                    except:
                        options = []
                
                questions.append({
                    "id": str(question.id),
                    "question_type": question.question_type,
                    "content": question.content,
                    "options": options,
                    "score": pq.score_for_question
                })
        
        # 获取已保存的答案
        saved_answers = {}
        if attempt:
            student_answers = db.query(db_models.StudentExamAnswer).filter(
                db_models.StudentExamAnswer.student_exam_attempt_id == attempt.id
            ).all()
            for sa in student_answers:
                saved_answers[str(sa.question_id)] = sa.answer_data
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "questions": questions,
                "saved_answers": saved_answers
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取试题失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取试题失败: {str(e)}")


@router.post("/classroom-exams/{exam_id}/save-answers", response_model=schemas.ApiResponse)
def save_exam_answers(
    exam_id: int,
    request_body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    保存学生答案（临时保存，不提交）
    """
    try:
        student_id = request_body.get("student_id")
        answers = request_body.get("answers", {})

        if not student_id:
            raise HTTPException(status_code=400, detail="缺少学生ID")

        # 【IDOR 修复】student_id 不能信任 body，必须与 JWT 身份核对
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))

        exam = db.query(db_models.ClassroomExam).filter(
            db_models.ClassroomExam.id == exam_id
        ).first()
        
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        
        # 获取或创建答卷记录
        attempt = db.query(db_models.StudentExamAttempt).filter(
            db_models.StudentExamAttempt.classroom_exam_id == exam_id,
            db_models.StudentExamAttempt.student_id == student_id
        ).first()
        
        if not attempt:
            attempt = db_models.StudentExamAttempt(
                classroom_exam_id=exam_id,
                student_id=student_id,
                attempt_start_time=datetime.now(timezone.utc),
                is_graded=False
            )
            db.add(attempt)
            db.flush()
        
        # 检查是否已提交
        if attempt.attempt_submission_time is not None:
            raise HTTPException(status_code=400, detail="试卷已提交，无法修改")
        
        # 保存或更新答案
        for question_id, answer in answers.items():
            import json
            answer_str = json.dumps(answer, ensure_ascii=False) if isinstance(answer, (list, dict)) else str(answer) if answer else ""
            
            existing = db.query(db_models.StudentExamAnswer).filter(
                db_models.StudentExamAnswer.student_exam_attempt_id == attempt.id,
                db_models.StudentExamAnswer.question_id == question_id
            ).first()
            
            if existing:
                existing.answer_data = answer_str
            else:
                new_answer = db_models.StudentExamAnswer(
                    student_exam_attempt_id=attempt.id,
                    question_id=question_id,
                    answer_data=answer_str
                )
                db.add(new_answer)
        
        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message="保存成功",
            data=None
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存答案失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存答案失败: {str(e)}")


@router.post("/classroom-exams/{exam_id}/submit", response_model=schemas.ApiResponse)
def submit_exam(
    exam_id: int,
    request_body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    提交考试试卷
    """
    try:
        import json

        student_id = request_body.get("student_id")
        answers = request_body.get("answers", {})

        if not student_id:
            raise HTTPException(status_code=400, detail="缺少学生ID")

        # 【IDOR 修复】student_id 不能信任 body，必须与 JWT 身份核对
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))

        exam = db.query(db_models.ClassroomExam).filter(
            db_models.ClassroomExam.id == exam_id
        ).first()
        
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        
        # 获取或创建答卷记录
        attempt = db.query(db_models.StudentExamAttempt).filter(
            db_models.StudentExamAttempt.classroom_exam_id == exam_id,
            db_models.StudentExamAttempt.student_id == student_id
        ).first()
        
        if not attempt:
            attempt = db_models.StudentExamAttempt(
                classroom_exam_id=exam_id,
                student_id=student_id,
                attempt_start_time=datetime.now(timezone.utc),
                is_graded=False
            )
            db.add(attempt)
            db.flush()
        
        # 检查是否已提交
        if attempt.attempt_submission_time is not None:
            raise HTTPException(status_code=400, detail="试卷已提交，请勿重复提交")
        
        # 保存所有答案
        for question_id, answer in answers.items():
            answer_str = json.dumps(answer, ensure_ascii=False) if isinstance(answer, (list, dict)) else str(answer) if answer else ""
            
            existing = db.query(db_models.StudentExamAnswer).filter(
                db_models.StudentExamAnswer.student_exam_attempt_id == attempt.id,
                db_models.StudentExamAnswer.question_id == question_id
            ).first()
            
            if existing:
                existing.answer_data = answer_str
            else:
                new_answer = db_models.StudentExamAnswer(
                    student_exam_attempt_id=attempt.id,
                    question_id=question_id,
                    answer_data=answer_str
                )
                db.add(new_answer)
        
        # 自动评分（客观题）
        total_score = 0
        auto_graded = True
        
        paper_questions = db.query(db_models.TestPaperQuestion).filter(
            db_models.TestPaperQuestion.test_paper_id == exam.test_paper_id
        ).all()
        
        for pq in paper_questions:
            question = db.query(db_models.Question).filter(
                db_models.Question.id == pq.question_id
            ).first()
            
            if not question:
                continue
            
            student_answer = answers.get(str(question.id), "")
            
            # 获取学生答案记录
            seq = db.query(db_models.StudentExamAnswer).filter(
                db_models.StudentExamAnswer.student_exam_attempt_id == attempt.id,
                db_models.StudentExamAnswer.question_id == question.id
            ).first()
            
            # 获取题目类型（兼容枚举和字符串）
            q_type = question.question_type.value if hasattr(question.question_type, 'value') else str(question.question_type)

            if q_type in ['SINGLE_CHOICE', 'MULTIPLE_CHOICE', 'TRUE_FALSE']:
                # 客观题自动评分
                correct_answers = json.loads(question.correct_answers) if question.correct_answers else []

                # 标准化答案格式（处理JSON字符串、列表、布尔值等）
                if isinstance(student_answer, list):
                    student_ans_set = set(str(a) for a in student_answer)
                elif isinstance(student_answer, str) and student_answer.startswith('['):
                    try:
                        parsed = json.loads(student_answer)
                        if isinstance(parsed, list):
                            student_ans_set = set(str(a) for a in parsed)
                        else:
                            student_ans_set = {student_answer}
                    except (json.JSONDecodeError, ValueError):
                        student_ans_set = {student_answer}
                elif student_answer is not None and student_answer != "":
                    student_ans_set = {str(student_answer)}
                else:
                    student_ans_set = set()

                correct_ans_set = set(str(a) for a in correct_answers)
                
                if student_ans_set == correct_ans_set:
                    total_score += pq.score_for_question
                    if seq:
                        seq.score_awarded = pq.score_for_question
                        seq.is_correct = True
                else:
                    if seq:
                        seq.score_awarded = 0
                        seq.is_correct = False
            else:
                # 主观题需要人工评分
                auto_graded = False
                if seq:
                    seq.score_awarded = None
                    seq.is_correct = None
        
        # 更新答卷状态
        attempt.attempt_submission_time = datetime.now(timezone.utc)
        attempt.total_score_achieved = total_score
        attempt.is_graded = auto_graded  # 如果全是客观题则自动评分完成
        
        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message="提交成功",
            data={
                "score": total_score if auto_graded else None,
                "is_graded": auto_graded,
                "message": "试卷提交成功" if auto_graded else "试卷已提交，等待教师评阅"
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交试卷失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"提交试卷失败: {str(e)}")


# ==================== 教师阅卷API ====================

@router.get("/classroom-exams/{exam_id}/students", response_model=schemas.ApiResponse)
def get_exam_student_submissions(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取考试的学生提交列表（教师阅卷用）
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        exam = db.query(db_models.ClassroomExam).filter(
            db_models.ClassroomExam.id == exam_id
        ).first()
        
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        
        # 验证请求者是否为该课堂的教师
        classroom = db.query(db_models.Classroom).filter(
            db_models.Classroom.id == exam.classroom_id
        ).first()
        
        if not classroom or classroom.teacher_id != teacher_id:
            raise HTTPException(status_code=403, detail="仅课堂教师可以访问")
        
        # 获取所有学生提交
        attempts = db.query(db_models.StudentExamAttempt).filter(
            db_models.StudentExamAttempt.classroom_exam_id == exam_id,
            db_models.StudentExamAttempt.attempt_submission_time.isnot(None)  # 已提交的
        ).all()
        
        student_list = []
        for attempt in attempts:
            # 获取学生信息
            student = db.query(db_models.User).filter(
                db_models.User.id == attempt.student_id
            ).first()
            
            student_list.append({
                "attempt_id": attempt.id,
                "student_id": attempt.student_id,
                "student_name": student.full_name if student else "未知",
                "student_username": student.username if student else "",
                "submit_time": attempt.attempt_submission_time.isoformat() if attempt.attempt_submission_time else None,
                "score": attempt.total_score_achieved,
                "is_graded": attempt.is_graded
            })
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": student_list,
                "total": len(student_list)
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生提交列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取学生提交列表失败: {str(e)}")


@router.get("/classroom-exams/{exam_id}/student/{student_id}/paper", response_model=schemas.ApiResponse)
def get_student_exam_paper(
    exam_id: int,
    student_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取学生答卷详情（教师阅卷用）
    """
    try:
        import json

        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))

        exam = db.query(db_models.ClassroomExam).filter(
            db_models.ClassroomExam.id == exam_id
        ).first()
        
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        
        # 验证请求者是否为该课堂的教师
        classroom = db.query(db_models.Classroom).filter(
            db_models.Classroom.id == exam.classroom_id
        ).first()
        
        if not classroom or classroom.teacher_id != teacher_id:
            raise HTTPException(status_code=403, detail="仅课堂教师可以查看学生答卷")
        
        # 获取学生答卷
        attempt = db.query(db_models.StudentExamAttempt).filter(
            db_models.StudentExamAttempt.classroom_exam_id == exam_id,
            db_models.StudentExamAttempt.student_id == student_id
        ).first()
        
        if not attempt:
            raise HTTPException(status_code=404, detail="学生答卷不存在")
        
        # 获取试卷问题和学生答案
        paper_questions = db.query(db_models.TestPaperQuestion).filter(
            db_models.TestPaperQuestion.test_paper_id == exam.test_paper_id
        ).order_by(db_models.TestPaperQuestion.order_in_paper).all()
        
        questions = []
        for pq in paper_questions:
            question = db.query(db_models.Question).filter(
                db_models.Question.id == pq.question_id
            ).first()
            
            if not question:
                continue
            
            # 获取学生答案
            student_answer_record = db.query(db_models.StudentExamAnswer).filter(
                db_models.StudentExamAnswer.student_exam_attempt_id == attempt.id,
                db_models.StudentExamAnswer.question_id == question.id
            ).first()
            
            # 解析选项
            options = []
            if question.options:
                try:
                    options = json.loads(question.options) if isinstance(question.options, str) else question.options
                except:
                    options = []
            
            # 解析正确答案
            correct_answer = []
            if question.correct_answers:
                try:
                    correct_answer = json.loads(question.correct_answers) if isinstance(question.correct_answers, str) else question.correct_answers
                except:
                    correct_answer = []
            
            # 解析学生答案
            student_answer = None
            if student_answer_record and student_answer_record.answer_data:
                try:
                    student_answer = json.loads(student_answer_record.answer_data) if isinstance(student_answer_record.answer_data, str) else student_answer_record.answer_data
                except:
                    student_answer = student_answer_record.answer_data
            
            questions.append({
                "id": str(question.id),
                "question_type": question.question_type,
                "content": question.content,
                "options": options,
                "correct_answer": correct_answer,
                "student_answer": student_answer,
                "max_score": pq.score_for_question,
                "score_awarded": student_answer_record.score_awarded if student_answer_record else None,
                "is_correct": student_answer_record.is_correct if student_answer_record else None
            })
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "attempt_id": attempt.id,
                "submit_time": attempt.attempt_submission_time.isoformat() if attempt.attempt_submission_time else None,
                "total_score": attempt.total_score_achieved,
                "is_graded": attempt.is_graded,
                "questions": questions
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生答卷失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取学生答卷失败: {str(e)}")


@router.get("/classroom-exams/{exam_id}/my-result", response_model=schemas.ApiResponse)
def get_my_exam_result(
    exam_id: int,
    student_id: int = Query(..., description="学生ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    学生查看自己的考试成绩
    """
    try:
        import json

        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))

        exam = db.query(db_models.ClassroomExam).filter(
            db_models.ClassroomExam.id == exam_id
        ).first()
        
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        
        # 获取学生答卷
        attempt = db.query(db_models.StudentExamAttempt).filter(
            db_models.StudentExamAttempt.classroom_exam_id == exam_id,
            db_models.StudentExamAttempt.student_id == student_id
        ).first()
        
        if not attempt:
            return schemas.ApiResponse(
                code="0000",
                message="暂无考试记录",
                data=None
            )
        
        # 获取试卷总分
        paper = db.query(db_models.TestPaper).filter(
            db_models.TestPaper.id == exam.test_paper_id
        ).first()
        total_score = paper.total_score if paper else 30
        
        # 获取试卷问题和学生答案
        paper_questions = db.query(db_models.TestPaperQuestion).filter(
            db_models.TestPaperQuestion.test_paper_id == exam.test_paper_id
        ).order_by(db_models.TestPaperQuestion.order_in_paper).all()
        
        questions = []
        for pq in paper_questions:
            question = db.query(db_models.Question).filter(
                db_models.Question.id == pq.question_id
            ).first()
            
            if not question:
                continue
            
            # 获取学生答案
            student_answer_record = db.query(db_models.StudentExamAnswer).filter(
                db_models.StudentExamAnswer.student_exam_attempt_id == attempt.id,
                db_models.StudentExamAnswer.question_id == question.id
            ).first()
            
            # 解析选项
            options = []
            if question.options:
                try:
                    options = json.loads(question.options) if isinstance(question.options, str) else question.options
                except:
                    options = []
            
            # 解析正确答案
            correct_answer = []
            if question.correct_answers:
                try:
                    correct_answer = json.loads(question.correct_answers) if isinstance(question.correct_answers, str) else question.correct_answers
                except:
                    correct_answer = []
            
            # 解析学生答案
            student_answer = None
            if student_answer_record and student_answer_record.answer_data:
                try:
                    student_answer = json.loads(student_answer_record.answer_data) if isinstance(student_answer_record.answer_data, str) else student_answer_record.answer_data
                except:
                    student_answer = student_answer_record.answer_data
            
            questions.append({
                "id": str(question.id),
                "question_type": question.question_type,
                "content": question.content,
                "options": options,
                "correct_answer": correct_answer,
                "student_answer": student_answer,
                "max_score": pq.score_for_question,
                "score_awarded": student_answer_record.score_awarded if student_answer_record else None,
                "is_correct": student_answer_record.is_correct if student_answer_record else None
            })
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "attempt_id": attempt.id,
                "submit_time": attempt.attempt_submission_time.isoformat() if attempt.attempt_submission_time else None,
                "score": attempt.total_score_achieved,
                "total_score": total_score,
                "is_graded": attempt.is_graded,
                "questions": questions
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生成绩失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取学生成绩失败: {str(e)}")


