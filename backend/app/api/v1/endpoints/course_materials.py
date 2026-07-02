"""
课程教材API接口
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.core.database import get_db
from app.models.models import Course, CourseAssessment, Chapter, Practice, Task
from app.schemas.schemas import CourseResponse

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/coursematerial",
    tags=["course-materials"]
)

@router.get("/lists")
async def get_course_materials(
    limit: int = Query(6, ge=1, le=100),
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    categories: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取课程教材列表"""
    logger.info(f"Fetching course materials - page: {page}, limit: {limit}, search: {search}")
    
    # 计算偏移量
    offset = (page - 1) * limit
    
    # 构建查询 — 返回所有类型的课程（PRACTICE / COURSE_MATERIAL / TRAINING）
    query = db.query(Course)
    
    # 搜索过滤
    if search:
        query = query.filter(Course.title.contains(search))
    
    # 方向过滤
    if direction:
        query = query.filter(Course.direction.contains(direction))
    
    # 难度过滤
    if difficulty:
        query = query.filter(Course.difficulty == difficulty)
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    courses = query.offset(offset).limit(limit).all()
    
    logger.info(f"Found {len(courses)} course materials, total: {total}")
    
    # 转换为响应格式
    course_list = []
    for course in courses:
        course_list.append({
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "cover_url": course.cover_url,
            "difficulty": course.difficulty.value if hasattr(course.difficulty, 'value') else course.difficulty,
            "direction": course.direction,
            "categories": course.categories,
            "source": course.source,
            "practice_task_count": course.practice_task_count,
            "material_resources_count": course.material_resources_count,
            "material_assessments_count": course.material_assessments_count,
            "created_at": course.created_at,
            "updated_at": course.updated_at
        })
    
    return {
        "code": 1,
        "data": {
            "list": course_list,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        },
        "msg": "success"
    }

@router.get("/{course_id}")
async def get_course_material_detail(course_id: int, db: Session = Depends(get_db)):
    """获取课程教材详情"""
    logger.info(f"Fetching course material detail for ID: {course_id}")
    
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return {
            "code": 0,
            "data": None,
            "msg": "Course not found"
        }
    
    # 获取教学大纲内容：优先从数据库读取，否则回退到文件系统
    teaching_syllabus = course.teaching_syllabus
    if not teaching_syllabus:
        syllabus_path = settings.resource_base_path / "课程资源" / course.title / "01-课程文档" / "教学大纲.md"
        if syllabus_path.exists():
            with open(syllabus_path, 'r', encoding='utf-8') as f:
                teaching_syllabus = f.read()
    
    # 获取章节数据（暂时不加载CourseResource，因为模型不存在）
    chapters = db.query(Chapter).filter(Chapter.course_id == course_id).order_by(Chapter.order_index).all()
    
    # 构建章节列表（无资源）
    chapter_list = []
    for chapter in chapters:
        chapter_list.append({
            "id": chapter.id,
            "title": chapter.title,  # 前端使用 title 字段
            "name": chapter.title,   # 保持向后兼容
            "description": "",
            "order_index": chapter.order_index or 0,
            "experiment_count": chapter.experiment_count or 0,
            "resources": {},
            "children": []
        })
    
    # 获取课程教学资源
    from app.models.models import CourseResource
    course_resources = db.query(CourseResource).filter(CourseResource.course_id == course_id).all()
    resource_list = [
        {
            "id": r.id,
            "title": r.title,
            "url": r.url,
            "resource_type": r.resource_type,
            "can_download": r.can_download,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in course_resources
    ]
    
    # 获取课程考核列表（格式化显示）
    assessments = db.query(CourseAssessment).filter(CourseAssessment.course_id == course_id).all()
    exam_list = format_assessments(assessments)

    # 获取实践列表
    practices_data = get_course_practices(db, course_id)
    
    course_detail = {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "cover_url": course.cover_url,
        "difficulty": course.difficulty.value if course.difficulty else None,
        "direction": course.direction,
        "categories": course.categories,
        "source": course.source,
        "practice_task_count": course.practice_task_count,
        "outline_url": course.outline_url,
        "material_resources_count": course.material_resources_count,
        "material_assessments_count": course.material_assessments_count,
        "visibility": course.visibility.value if course.visibility else None,
        "created_at": course.created_at,
        "updated_at": course.updated_at,
        # 新增的详细内容
        "teaching_syllabus": teaching_syllabus,
        "chapter_list": chapter_list,
        "resource_list": resource_list,
        "resources": resource_list,  # 前端需要的字段
        "exams": exam_list,  # 格式化的考核数据
        "assessments": exam_list,  # 前端需要的字段名

        # 前端需要的字段 - 正确映射
        "chapters": chapter_list,  # 章节数组
        "chapter_count": len(chapter_list),  # 章节数量统计
        "practices": practices_data,  # 实践列表数组
        "practice_count": len(practices_data),  # 实践数量统计
        "micros": sum(ch.get('experiment_count', 0) for ch in chapter_list),  # 实践数统计
        
        # 保留旧字段保持向后兼容
        "course_practices": practices_data
    }
    
    return {
        "code": 1,
        "data": course_detail,
        "msg": "success"
    }


def format_assessments(assessments: List[CourseAssessment]) -> List[Dict[str, Any]]:
    exam_list = []
    for assessment in assessments:
        atype = assessment.assessment_type or ""

        # 支持英文和中文类型
        if atype in ("midterm_exam", "期中考试"):
            exam_info = {"type": "期中考试", "questions": 32, "score": 100, "duration": "120分钟"}
        elif atype in ("final_exam", "期末考试"):
            exam_info = {"type": "期末考试", "questions": 30, "score": 100, "duration": "150分钟"}
        elif atype in ("question_bank", "题库"):
            exam_info = {"type": "题库", "questions": 150, "score": "—", "duration": "—"}
        elif atype in ("exam_config", "考试配置"):
            exam_info = {"type": "考试配置", "questions": "—", "score": "—", "duration": "—"}
        elif atype in ("unit_test", "单元测验"):
            exam_info = {"type": "单元测验", "questions": 20, "score": 100, "duration": "60分钟"}
        elif atype in ("project", "项目评估"):
            exam_info = {"type": "项目评估", "questions": "—", "score": 100, "duration": "—"}
        else:
            exam_info = {"type": atype or "实验考试", "questions": "—", "score": 100, "duration": "120分钟"}

        exam_list.append({
            "id": assessment.id,
            "title": assessment.title,
            "url": assessment.url,
            "type": exam_info["type"],
            "assessment_type": exam_info["type"],  # 前端统计需要此字段
            "questions": exam_info["questions"],
            "score": exam_info["score"],
            "duration": exam_info["duration"],
            "status": "可用",
            "created_at": assessment.created_at.isoformat() if assessment.created_at else None
        })

    return exam_list

def get_course_practices(db: Session, course_id: int):
    """获取课程包含的实践列表"""
    practices = db.query(Practice).filter(Practice.parent_course_id == course_id).all()
    
    practice_list = []
    for practice in practices:
        # 统计该实践的关卡数和金币数
        tasks = db.query(Task).filter(Task.practice_id == practice.id).all()
        total_coin = sum(task.coin for task in tasks)
        
        practice_list.append({
            "id": practice.id,
            "title": practice.title,
            "description": practice.description,
            "summary": practice.summary or practice.description,
            "difficulty": practice.difficulty.value if practice.difficulty else "beginner",
            "task_count": len(tasks),
            "coin": total_coin,
            "cover_url": practice.cover_url,
            "direction": practice.direction,
            "category": practice.category
        })
    
    return practice_list