from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, any_, case, text
from typing import List, Optional, Tuple, Dict
import app.models.models as models
import app.schemas.schemas as schemas
from datetime import datetime, timezone, date, timedelta
import json
import logging
from app.utils.canvas_helpers import calculate_semester as _calculate_semester
from app.utils.eval_helpers import normalize_test_case

logger = logging.getLogger(__name__)

# 用户相关CRUD操作
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    from app.core.security import get_password_hash
    user_dict = user.model_dump()
    password = user_dict.pop('password')
    hashed_password = get_password_hash(password)
    db_user = models.User(**user_dict, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

# 文章相关CRUD操作
def get_post(db: Session, post_id: int):
    return db.query(models.Post).filter(models.Post.id == post_id).first()

def get_posts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Post).offset(skip).limit(limit).all()

def create_post(db: Session, post: schemas.PostCreate):
    db_post = models.Post(**post.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def delete_post(db: Session, post_id: int):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if db_post:
        db.delete(db_post)
        db.commit()
    return db_post

# 课程相关CRUD操作 - 适配现有数据库结构
def get_courses(
    db: Session, 
    skip: int = 0, 
    limit: int = 20,
    keyword: Optional[str] = None,
    directions: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    difficulty: Optional[str] = None,
    course_type: Optional[str] = None
):
    # 基础查询
    query = db.query(models.Course)
    
    # 类型筛选
    if course_type:
        query = query.filter(models.Course.course_type == course_type)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                models.Course.title.ilike(f"%{keyword}%"),
                models.Course.description.ilike(f"%{keyword}%")
            )
        )
    
    # 方向筛选
    if directions:
        query = query.filter(models.Course.direction.in_(directions))
    
    # 分类筛选 - 使用数组查询
    if categories:
        # 检查categories数组是否包含任何指定的分类
        category_conditions = []
        for category in categories:
            category_conditions.append(models.Course.categories.any(category))
        query = query.filter(or_(*category_conditions))
    
    # 难度筛选
    if difficulty:
        query = query.filter(models.Course.difficulty == difficulty)
    
    total = query.count()
    courses = query.offset(skip).limit(limit).all()
    
    return courses, total

def get_course(db: Session, course_id: int):
    return db.query(models.Course).options(
        joinedload(models.Course.chapters),
        joinedload(models.Course.resources),
        joinedload(models.Course.assessments),
        joinedload(models.Course.course_practices).joinedload(models.Practice.tasks)  # 加载关联的微型实验课程及其任务
    ).filter(models.Course.id == course_id).first()

def get_course_outline(db: Session, course_id: int):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if course and course.outline_url:
        return {"url": course.outline_url, "type": "pdf"}
    return None

def get_course_resources(db: Session, course_id: int):
    return db.query(models.CourseResource).filter(
        models.CourseResource.course_id == course_id
    ).all()

def get_course_assessments(db: Session, course_id: int):
    return db.query(models.CourseAssessment).filter(
        models.CourseAssessment.course_id == course_id
    ).all()

# 微型实验相关CRUD操作
def get_practices(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    keyword: Optional[str] = None,
    direction: Optional[str] = None,
    category: Optional[str] = None,
    difficulty: Optional[str] = None
):
    # 查询practices表
    practices_query = db.query(models.Practice).filter(
        models.Practice.is_published.is_(True)
    )

    # 关键词搜索
    if keyword:
        practices_query = practices_query.filter(
            or_(
                models.Practice.title.ilike(f"%{keyword}%"),
                models.Practice.description.ilike(f"%{keyword}%")
            )
        )
    
    # 方向筛选
    if direction:
        practices_query = practices_query.filter(models.Practice.direction == direction)
    
    # 分类筛选
    if category:
        practices_query = practices_query.filter(models.Practice.category == category)
    
    # 难度筛选
    if difficulty:
        practices_query = practices_query.filter(models.Practice.difficulty == difficulty)
    
    
    # 计算总数
    total = practices_query.count()

    # 应用分页
    practices = practices_query.offset(skip).limit(limit).all()

    return practices, total

def get_practice(db: Session, practice_id: int):
    return db.query(models.Practice).filter(models.Practice.id == practice_id).first()

# 获取实践详情（包含任务和技能标签）
def get_practice_detail(db: Session, practice_id: int):
    """
    获取practices表记录的详情
    按照架构澄清方案，此函数只返回practices表记录
    """
    return db.query(models.Practice).options(
        joinedload(models.Practice.tasks),
        joinedload(models.Practice.skills)
    ).filter(models.Practice.id == practice_id).first()

# 获取实践的任务列表
def get_practice_tasks(
    db: Session, 
    practice_id: int, 
    skip: int = 0, 
    limit: int = 20
):
    query = db.query(models.Task).filter(
        models.Task.practice_id == practice_id
    ).order_by(models.Task.order_in_practice)
    
    total = query.count()
    tasks = query.offset(skip).limit(limit).all()
    
    return tasks, total

# 获取推荐实践（基于相同方向和分类）
def get_recommended_practices(
    db: Session,
    practice_id: int,
    limit: int = 5
):
    """
    获取推荐的practices记录
    按照架构澄清方案，此函数只返回practices表记录
    """
    # 获取当前实践的信息
    current_practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id
    ).first()

    if not current_practice:
        return []

    # 查找相同方向或分类的其他实践
    recommended = db.query(models.Practice).filter(
        and_(
            models.Practice.id != practice_id,
            or_(
                models.Practice.direction == current_practice.direction,
                models.Practice.category == current_practice.category
            )
        )
    ).limit(limit).all()

    return recommended

# 课堂相关CRUD操作
def get_classrooms(db: Session, teacher_id: Optional[int] = None, skip: int = 0, limit: int = 20):
    query = db.query(models.Classroom).options(
        joinedload(models.Classroom.course)
        # joinedload(models.Classroom.teacher)  # 暂时移除
    )
    
    if teacher_id:
        query = query.filter(models.Classroom.teacher_id == teacher_id)
    
    total = query.count()
    classrooms = query.offset(skip).limit(limit).all()
    
    return classrooms, total

def get_classroom(db: Session, classroom_id: int):
    return db.query(models.Classroom).options(
        joinedload(models.Classroom.course)
        # joinedload(models.Classroom.teacher)  # 暂时移除
    ).filter(models.Classroom.id == classroom_id).first()

def calculate_semester(start_date: datetime) -> str:
    """根据开始时间自动计算学期 — delegates to pure function"""
    return _calculate_semester(start_date.year, start_date.month)

def create_classroom(db: Session, classroom: schemas.ClassroomCreate, teacher_id: int):
    # 检查课堂名称是否重复（同一教师下）
    existing = db.query(models.Classroom).filter(
        and_(
            models.Classroom.name == classroom.name,
            models.Classroom.teacher_id == teacher_id
        )
    ).first()
    
    if existing:
        return None  # 名称重复
    
    # 检查日期有效性
    if classroom.end_date <= classroom.start_date:
        return None  # 日期无效
    
    # 自动计算学期
    semester = calculate_semester(classroom.start_date)
    
    # 创建课堂数据
    classroom_data = classroom.model_dump()
    # 移除不在模型中的字段
    keys_to_remove = ['teacher_id', 'max_students', 'is_public', 'description']
    for key in keys_to_remove:
        if key in classroom_data:
            del classroom_data[key]
            
    classroom_data['semester'] = semester  # 覆盖前端传入的学期字段
    
    db_classroom = models.Classroom(
        **classroom_data,
        teacher_id=teacher_id
    )
    db.add(db_classroom)
    db.commit()
    db.refresh(db_classroom)
    return db_classroom

# 添加实践到课堂
def add_practice_to_classroom(
    db: Session, 
    classroom_id: int, 
    practice_id: int, 
    sync_doc: bool = False
):
    # 检查课堂是否存在
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id
    ).first()
    if not classroom:
        return None
    
    # 检查实践是否存在
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id
    ).first()
    if not practice:
        return None
    
    # 检查是否已经添加过
    existing = db.query(models.ClassroomPractice).filter(
        and_(
            models.ClassroomPractice.classroom_id == classroom_id,
            models.ClassroomPractice.practice_id == practice_id
        )
    ).first()
    if existing:
        return None  # 已存在
    
    # 创建关联记录
    db_classroom_practice = models.ClassroomPractice(
        classroom_id=classroom_id,
        practice_id=practice_id,
        sync_doc=sync_doc
    )
    db.add(db_classroom_practice)
    db.commit()
    db.refresh(db_classroom_practice)
    return db_classroom_practice

# 获取课堂的实践列表
def get_classroom_practices(db: Session, classroom_id: int):
    logger.info(f"[CRUD] 查询课堂实践列表，classroom_id: {classroom_id}")
    try:
        result = db.query(models.ClassroomPractice).filter(
        models.ClassroomPractice.classroom_id == classroom_id
    ).all()
        logger.info(f"[CRUD] ✅ 查询完成，找到 {len(result)} 个实践")
        return result
    except Exception as e:
        logger.error(f"[CRUD] ❌ 查询课堂实践列表失败: {str(e)}")
        import traceback
        logger.error(f"[CRUD] ❌ 错误堆栈: {traceback.format_exc()}")
        raise

# 添加实训项目到课堂
def add_training_to_classroom(
    db: Session,
    classroom_id: int,
    training_id: int
):
    # 检查课堂是否存在
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id
    ).first()
    if not classroom:
        return None
    
    # 检查实训是否存在
    training = db.query(models.Training).filter(
        models.Training.id == training_id
    ).first()
    if not training:
        return None
    
    # 检查是否已经添加过
    existing = db.query(models.ClassroomTraining).filter(
        and_(
            models.ClassroomTraining.classroom_id == classroom_id,
            models.ClassroomTraining.training_id == training_id
        )
    ).first()
    if existing:
        return None  # 已存在
    
    # 创建关联记录
    db_classroom_training = models.ClassroomTraining(
        classroom_id=classroom_id,
        training_id=training_id,
        added_at=datetime.now(timezone.utc)
    )
    db.add(db_classroom_training)
    db.commit()
    db.refresh(db_classroom_training)
    return db_classroom_training

# 检查教师是否有权限操作课堂
def check_teacher_classroom_permission(db: Session, classroom_id: int, teacher_id: int):
    classroom = db.query(models.Classroom).filter(
        and_(
            models.Classroom.id == classroom_id,
            models.Classroom.teacher_id == teacher_id
        )
    ).first()
    return classroom is not None

# 筛选标签相关操作 - 适配现有数据库结构
def get_filter_tags(db: Session):
    # 获取所有方向
    directions_result = db.query(models.Course.direction).filter(
        models.Course.direction.isnot(None)
    ).distinct().all()
    directions = [d[0] for d in directions_result if d[0]]
    
    # 获取所有分类 - 从categories数组中提取
    categories_result = db.query(models.Course.categories).filter(
        models.Course.categories.isnot(None)
    ).all()
    categories = set()
    for cat_array in categories_result:
        if cat_array[0]:  # cat_array[0] 是categories数组
            categories.update(cat_array[0])
    categories = list(categories)
    
    # 获取所有难度级别 - courses表使用大写
    difficulties = ["BEGINNER", "INTERMEDIATE", "ADVANCED"]
    
    return {
        "directions": directions,
        "categories": categories,
        "difficulties": difficulties
    }

def get_practice_filter_tags(db: Session):
    # 获取微型实验的方向
    directions_result = db.query(models.Practice.direction).distinct().all()
    directions = [d[0] for d in directions_result if d[0]]
    
    # 获取微型实验的分类
    categories_result = db.query(models.Practice.category).distinct().all()
    categories = [c[0] for c in categories_result if c[0]]
    
    # 获取所有难度级别 - practices表使用小写
    difficulties = ["beginner", "intermediate", "advanced"]
    
    return {
        "directions": directions,
        "categories": categories,
        "difficulties": difficulties
    }

# 统计信息
def get_statistics(db: Session):
    total_courses = db.query(models.Course).count()
    total_practices = db.query(models.Practice).count()
    total_classrooms = db.query(models.Classroom).count()
    total_users = db.query(models.User).count()
    
    return {
        "total_courses": total_courses,
        "total_practices": total_practices,
        "total_classrooms": total_classrooms,
        "total_users": total_users
    }

# ==================== 关卡详情相关CRUD操作 ====================

# 获取任务详情（关卡详情）
def get_task_detail(db: Session, task_id: str, user_id: Optional[int] = None):
    """获取任务详情，包含用户完成状态"""
    try:
        task_id_int = int(task_id)
    except (ValueError, TypeError):
        return None
    task = db.query(models.Task).filter(models.Task.id == task_id_int).first()
    if not task:
        return None
    
    # 如果提供了用户ID，查询用户完成状态
    if user_id:
        # 查询是否有任何通过的记录（只要曾经通过就算完成）
        passed_result = db.query(models.TaskEvaluationResult).filter(
            models.TaskEvaluationResult.task_id == task_id,
            models.TaskEvaluationResult.user_id == user_id,
            models.TaskEvaluationResult.status == "pass"
        ).first()
        
        if passed_result:
            task.status = "已完成"
        else:
            # 查询是否有任何提交记录
            any_result = db.query(models.TaskEvaluationResult).filter(
                models.TaskEvaluationResult.task_id == task_id,
                models.TaskEvaluationResult.user_id == user_id
            ).first()
            if any_result:
                task.status = "进行中"
            else:
                task.status = "未开始"
    else:
        task.status = "未开始"
    
    return task

# 获取任务手册
def get_task_handbook(db: Session, task_id: str):
    """获取任务手册内容"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return None
    
    return {
        "markdown": task.handbook_markdown or "",
        "updated_at": task.updated_at
    }

# 获取参考答案
def get_task_answer(db: Session, task_id: str, user_id: int, user_role: str = "student"):
    """获取参考答案，需要权限检查"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return None
    
    # 权限检查：教师/助教可以直接查看，学生需要通关后才能查看
    if user_role in ["teacher", "assistant"]:
        can_view = True
    else:
        # 检查学生是否已通关
        latest_result = db.query(models.TaskEvaluationResult).filter(
            models.TaskEvaluationResult.task_id == task_id,
            models.TaskEvaluationResult.user_id == user_id,
            models.TaskEvaluationResult.status == "pass"
        ).first()
        can_view = latest_result is not None
    
    if not can_view:
        return None
    
    return {
        "content": task.answer_content_markdown or "",
        "updated_at": task.updated_at
    }

# 获取测试集
def get_task_tests(db: Session, task_id: str):
    """获取任务测试集"""
    tests = db.query(models.TaskTest).filter(
        models.TaskTest.task_id == task_id
    ).order_by(models.TaskTest.test_order).all()

    return tests

# 提交评测
def submit_task_evaluation(
    db: Session,
    task_id: str, 
    user_id: int, 
    submission_data: dict
):
    """提交任务评测"""
    print(f">>> submit_task_evaluation 被调用, task_id={task_id}, user_id={user_id}", flush=True)
    # 检查评测冷却时间（5秒）
    import datetime
    five_seconds_ago = datetime.datetime.now() - datetime.timedelta(seconds=5)
    recent_evaluation = db.query(models.TaskEvaluationResult).filter(
        models.TaskEvaluationResult.task_id == task_id,
        models.TaskEvaluationResult.user_id == user_id,
        models.TaskEvaluationResult.created_at > five_seconds_ago
    ).first()
    
    if recent_evaluation:
        raise ValueError("评测冷却中，请5秒后再试")
    
    # 检查用户是否已经完成了该任务（已有pass记录）
    completed_evaluation = db.query(models.TaskEvaluationResult).filter(
        models.TaskEvaluationResult.task_id == task_id,
        models.TaskEvaluationResult.user_id == user_id,
        models.TaskEvaluationResult.status == "pass"
    ).first()
    
    # 获取任务信息
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise ValueError("任务不存在")
    
    # 获取测试用例
    tests = get_task_tests(db, task_id)
    
    # 执行评测逻辑
    evaluation_result = _execute_evaluation(task, tests, submission_data)
    
    # 如果用户已经完成过该任务，且本次评测也通过，则score设为0（不给予重复奖励）
    is_already_completed = completed_evaluation is not None
    if is_already_completed and evaluation_result["status"] == "pass":
        evaluation_result["score"] = 0
        evaluation_result["is_duplicate"] = True  # 标记为重复提交
    
    # 如果是重复提交且失败，添加提示信息
    if is_already_completed and evaluation_result["status"] == "fail":
        # 即使失败，仍然记录评测结果
        logger.info(f"Student {user_id} failed resubmission for task {task_id}, but task was already completed")
    
    # 保存评测结果
    db_result = models.TaskEvaluationResult(
        task_id=task_id,
        user_id=user_id,
        submission_code=submission_data.get("answer") or submission_data.get("code"),
        repo_hash=submission_data.get("repo_hash"),
        status=evaluation_result["status"],
        score=evaluation_result["score"],
        total_tests=evaluation_result["total_tests"],
        passed_tests=evaluation_result["passed_tests"],
        execution_time=evaluation_result.get("execution_time"),
        error_message=evaluation_result.get("error_message"),
        test_results=str(evaluation_result.get("test_results", []))
    )
    
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    
    # 如果通关，保存代码快照（仅首次通过时保存）
    if evaluation_result["status"] == "pass" and submission_data.get("repo_hash") and not is_already_completed:
        files_data = submission_data.get("files", {})
        save_code_snapshot(
            db, task_id, user_id,
            submission_data["repo_hash"],
            files_data,
            "pass"
        )
    
    # 如果首次评测通过，累加金币并更新实践进度
    if evaluation_result["status"] == "pass" and not is_already_completed:
        try:
            # 1. 累加用户金币
            task_coin = task.coin or 0
            if task_coin > 0:
                user = db.query(models.User).filter(models.User.id == user_id).first()
                if user:
                    user.total_coins = (user.total_coins or 0) + task_coin
                    db.commit()
                    logger.info(f"用户 {user_id} 获得 {task_coin} 金币，总金币: {user.total_coins}")
            
            # 2. 更新学生实践进度（独立于课堂）
            practice = db.query(models.Practice).filter(models.Practice.id == task.practice_id).first()
            if practice:
                # 获取或创建实践进度记录
                practice_progress = db.query(models.StudentPracticeProgress).filter(
                    models.StudentPracticeProgress.student_id == user_id,
                    models.StudentPracticeProgress.practice_id == task.practice_id
                ).first()
                
                current_time = datetime.datetime.now(datetime.timezone.utc)
                
                if not practice_progress:
                    # 创建新的实践进度记录
                    practice_progress = models.StudentPracticeProgress(
                        student_id=user_id,
                        practice_id=task.practice_id,
                        completed_task_count=1,
                        total_coins_earned=task_coin,
                        first_access_at=current_time,
                        last_activity_at=current_time
                    )
                    db.add(practice_progress)
                else:
                    # 更新现有记录
                    practice_progress.completed_task_count = (practice_progress.completed_task_count or 0) + 1
                    practice_progress.total_coins_earned = (practice_progress.total_coins_earned or 0) + task_coin
                    practice_progress.last_activity_at = current_time
                
                # 检查是否完成了所有关卡
                total_tasks = practice.task_count or db.query(models.Task).filter(
                    models.Task.practice_id == task.practice_id
                ).count()
                
                if practice_progress.completed_task_count >= total_tasks:
                    practice_progress.is_completed = True
                
                db.commit()
                logger.info(f"用户 {user_id} 完成关卡 {task_id}，实践进度: {practice_progress.completed_task_count}/{total_tasks}")
        except Exception as e:
            logger.error(f"更新金币/实践进度失败: {str(e)}", exc_info=True)
            # 不影响评测结果，继续执行
    
    # 如果评测通过，更新学生课程进度（课堂内）
    if evaluation_result["status"] == "pass":
        try:
            # 获取practice和course信息
            practice = db.query(models.Practice).filter(models.Practice.id == task.practice_id).first()
            if not practice:
                # 如果practice不存在，记录错误但不影响评测结果
                logger.warning(f"Practice ID {task.practice_id} not found for task {task_id}, skipping progress update")
            elif practice and practice.parent_course_id:
                course_id = practice.parent_course_id
                
                # 找到用户所在的classroom中对应的classroom_course_id
                # 通过查找用户所在的classroom（通过ClassroomStudent关系）
                # 获取用户所在的所有classroom
                user_classrooms = db.query(models.ClassroomStudent.classroom_id).filter(
                    models.ClassroomStudent.student_id == user_id
                ).all()
                classroom_ids = [c[0] for c in user_classrooms]
                
                if classroom_ids:
                    classroom_course = db.query(models.ClassroomCourse).filter(
                        models.ClassroomCourse.course_id == course_id,
                        models.ClassroomCourse.classroom_id.in_(classroom_ids)
                    ).first()
                else:
                    classroom_course = None
                
                if classroom_course:
                    # 获取或创建学生课程进度记录
                    progress = get_student_course_progress(db, classroom_course.id, user_id)
                    
                    if not progress:
                        # 创建新的进度记录
                        # 检查是否所有任务都完成了（可能只有一个任务）
                        total_tasks = practice.task_count or 0
                        initial_status = models.CourseInClassroomStatusStudentEnum.LEARNING
                        if total_tasks > 0 and 1 >= total_tasks:
                            # 如果只有一个任务且已完成，状态为已完成
                            # 检查是否在截止时间之前完成
                            current_time = datetime.datetime.now(datetime.timezone.utc)
                            deadline_at = classroom_course.deadline_at
                            
                            if deadline_at and current_time > deadline_at:
                                initial_status = models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
                            else:
                                initial_status = models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME
                        
                        progress = models.StudentCourseProgress(
                            classroom_course_id=classroom_course.id,
                            student_id=user_id,
                            student_status=initial_status,
                            completed_task_count=1,
                            last_submission_at=datetime.datetime.now(datetime.timezone.utc)
                        )
                        db.add(progress)
                    else:
                        # 更新现有记录
                        # 检查该任务是否已经完成过（避免重复计数）
                        task_completed = db.query(models.TaskEvaluationResult).filter(
                            models.TaskEvaluationResult.task_id == task_id,
                            models.TaskEvaluationResult.user_id == user_id,
                            models.TaskEvaluationResult.status == "pass"
                        ).count()
                        
                        # 如果这是第一次完成该任务，增加completed_task_count
                        if task_completed == 1:  # 只有当前这次记录
                            progress.completed_task_count = (progress.completed_task_count or 0) + 1
                        
                        progress.last_submission_at = datetime.datetime.now(datetime.timezone.utc)
                        
                        # 检查是否所有任务都完成了
                        total_tasks = practice.task_count or 0
                        completed_tasks = progress.completed_task_count or 0
                        
                        if total_tasks > 0 and completed_tasks >= total_tasks:
                            # 所有任务都完成了，更新状态为已完成
                            # 检查是否在截止时间之前完成
                            current_time = datetime.datetime.now(datetime.timezone.utc)
                            deadline_at = classroom_course.deadline_at
                            
                            if deadline_at and current_time > deadline_at:
                                progress.student_status = models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
                            else:
                                progress.student_status = models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME
                        elif progress.student_status == models.CourseInClassroomStatusStudentEnum.NOT_STARTED:
                            # 更新状态为学习中（如果还是未开始状态）
                            progress.student_status = models.CourseInClassroomStatusStudentEnum.LEARNING
                    
                    db.commit()
                    db.refresh(progress)
                else:
                    # 记录找不到classroom_course的情况
                    logger.warning(f"ClassroomCourse not found for course_id={course_id}, classroom_ids={classroom_ids}, user_id={user_id}")
            else:
                # 记录practice没有parent_course_id的情况
                logger.warning(f"Practice ID {task.practice_id} has no parent_course_id, skipping progress update")
        except Exception as e:
            # 如果更新进度失败，记录错误但不影响评测结果
            logger.error(f"更新学生课程进度失败: {str(e)}", exc_info=True)
    
    return evaluation_result

def _parse_test_script_output(output: str) -> dict:
    """解析评测脚本的文本输出"""
    import re

    try:
        # 解析得分
        score_match = re.search(r'得分:\s*(\d+)/(\d+)', output)
        if score_match:
            score = int(score_match.group(1))
            max_score = int(score_match.group(2))
        else:
            # 尝试其他格式
            score_match = re.search(r'得分:\s*(\d+)', output)
            if score_match:
                score = int(score_match.group(1))
                max_score = 100
            else:
                score = 0
                max_score = 100

        # 解析通过用例数
        pass_match = re.search(r'通过用例:\s*(\d+)', output)
        if pass_match:
            passed_tests = int(pass_match.group(1))
        else:
            passed_tests = score // 25 if score > 0 else 0  # 假设每个测试用例25分

        # 解析总测试用例数
        total_match = re.search(r'总测试用例:\s*(\d+)', output)
        if total_match:
            total_tests = int(total_match.group(1))
        else:
            total_tests = passed_tests

        # 判断状态
        status = 'pass' if score >= 60 else 'fail'

        # 提取测试结果
        test_results = []
        # 支持多种输出格式
        # 格式1: ✅ 测试用例1 - PASS 或 ❌ 测试用例1 - FAIL
        # 格式2: ✅ 基础测试1：良好成绩班长 - PASS
        # 格式3: ✅ 测试点1: PASS
        test_patterns = [
            r'(✅|❌)\s*测试用例(\d+)\s*-\s*(PASS|FAIL)',
            r'(✅|❌)\s*[^\n]*?\s*-\s*(PASS|FAIL)',
            r'(✅|❌)\s*测试点\s*(\d+)[:\s]*(PASS|FAIL)',
        ]
        
        # 首先尝试找所有PASS/FAIL行
        all_test_lines = re.findall(r'(✅|❌)\s*([^\n]+?)\s*-\s*(PASS|FAIL)', output)
        if all_test_lines:
            for idx, (marker, test_name, result) in enumerate(all_test_lines, 1):
                test_results.append({
                    'case_id': idx,
                    'name': test_name.strip(),
                    'passed': result == 'PASS',
                    'score': (100 // len(all_test_lines)) if result == 'PASS' else 0,
                    'error_message': '' if result == 'PASS' else '测试失败'
                })
        else:
            # 如果没有找到测试结果，根据通过/失败数量生成
            for i in range(passed_tests):
                test_results.append({
                    'case_id': i + 1,
                    'passed': True,
                    'score': 100 // max(total_tests, 1),
                    'error_message': ''
                })
            for i in range(total_tests - passed_tests):
                test_results.append({
                    'case_id': passed_tests + i + 1,
                    'passed': False,
                    'score': 0,
                    'error_message': '测试失败'
                })

        return {
            'status': status,
            'total_score': score,
            'max_score': max_score,
            'test_results': test_results,
            'execution_time': 0,
            'error_message': ''
        }
    except Exception as e:
        return {
            'status': 'fail',
            'total_score': 0,
            'max_score': 100,
            'test_results': [],
            'execution_time': 0,
            'error_message': f'解析评测输出失败: {str(e)}'
        }
def _execute_with_test_script(student_code: str, test_script_path: str, test_cases: list) -> dict:
    """使用评测脚本执行代码评测"""
    import subprocess
    import tempfile
    import json
    import os
    import shutil
    from pathlib import Path
    
    print(f"=== _execute_with_test_script 被调用 ===", flush=True)
    print(f"test_script_path: {test_script_path}", flush=True)
    print(f"student_code 长度: {len(student_code)}", flush=True)
    
    # 资源根目录（ziyuan_data位于项目根目录）
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # backend/../.. = project root
    RESOURCE_ROOT = PROJECT_ROOT / "ziyuan_data" / "课程资源" / "Python程序设计" / "03-微型实验"
    
    # 解析评测脚本的完整路径
    # test_script_path 格式可能是: "关卡1-变量与数据类型操作/test_evaluator.py"
    # 或者 "/full/path/to/test_evaluator.py"
    script_path = Path(test_script_path)
    
    if not script_path.is_absolute():
        # 尝试在资源目录下查找
        # 动态搜索所有实践目录
        possible_paths = []
        
        # 遍历所有实践目录（实践1-xxx, 实践2-xxx, 等）
        if RESOURCE_ROOT.exists():
            for practice_dir in RESOURCE_ROOT.iterdir():
                if practice_dir.is_dir() and practice_dir.name.startswith("实践"):
                    possible_paths.append(practice_dir / test_script_path)
        
        # 也检查其他可能的位置
        possible_paths.extend([
            RESOURCE_ROOT / test_script_path,
            PROJECT_ROOT / test_script_path,
            PROJECT_ROOT / "ziyuan_data" / test_script_path,
        ])
        
        found_path = None
        for p in possible_paths:
            if p.exists():
                found_path = p
                logger.info(f"找到评测脚本: {p}")
                break
        
        if found_path:
            script_path = found_path
        else:
            # 记录日志以便调试
            logger.warning(f"评测脚本未找到: {test_script_path}")
            logger.warning(f"尝试过的路径: {possible_paths}")

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # 写入学生代码到 student.py
            student_file = Path(tmpdir) / "student.py"
            with open(student_file, 'w', encoding='utf-8') as f:
                f.write(student_code)
            
            # 也写入到 solution.py（部分评测脚本可能使用这个名字）
            solution_file = Path(tmpdir) / "solution.py"
            with open(solution_file, 'w', encoding='utf-8') as f:
                f.write(student_code)

            # 写入测试用例
            # 【安全修复 CRIT-2】只把 input_data 写入学生容器，
            # expected_output 保留在 backend 端做比对，防止泄密
            # 如果测试用例都是空的，写入空数组让评测脚本使用内置测试
            has_valid_test_cases = any(
                normalize_test_case(tc).get("input_data")
                for tc in test_cases
            )

            test_data_file = Path(tmpdir) / "test_data.json"
            with open(test_data_file, "w", encoding="utf-8") as f:
                if has_valid_test_cases:
                    # 只写非敏感字段: input_data, is_hidden, match_rule, id
                    safe_cases = []
                    for tc in test_cases:
                        ntc = normalize_test_case(tc)
                        safe_cases.append({
                            "id": ntc.get("id"),
                            "input_data": ntc.get("input_data"),
                            "is_hidden": ntc.get("is_hidden", False),
                            "match_rule": ntc.get("match_rule", "exact"),
                        })
                    json.dump(safe_cases, f, ensure_ascii=False, indent=2)
                else:
                    # 写入空数组，让评测脚本使用内置测试用例
                    json.dump([], f)
            
            # 复制评测脚本到临时目录
            if script_path.exists():
                script_dest = Path(tmpdir) / "test_evaluator.py"
                shutil.copy2(script_path, script_dest)
                
                # 同时复制同目录下的其他依赖文件
                script_dir = script_path.parent
                for item in script_dir.iterdir():
                    if item.is_file() and item.suffix in ['.py', '.json', '.txt', '.csv']:
                        if item.name not in ['student.py', 'solution.py', 'test_data.json']:
                            try:
                                shutil.copy2(item, Path(tmpdir) / item.name)
                            except Exception as copy_err:
                                logger.warning(f"复制文件失败 {item}: {copy_err}")
                
                # 使用复制后的脚本路径
                actual_script_path = script_dest
            else:
                actual_script_path = script_path

            # 运行评测脚本，确保只从临时目录导入
            env = os.environ.copy()
            env['PYTHONPATH'] = tmpdir  # 设置PYTHONPATH只包含临时目录

            # 【改进】使用更严格的超时（10秒，给复杂评测留足时间）
            print(f"执行评测脚本: {actual_script_path}", flush=True)
            print(f"临时目录: {tmpdir}", flush=True)
            print(f"脚本是否存在: {actual_script_path.exists() if hasattr(actual_script_path, 'exists') else 'N/A'}", flush=True)
            
            result = subprocess.run(
                ['python3', str(actual_script_path)],
                cwd=tmpdir,
                env=env,
                capture_output=True,
                text=True,
                timeout=10  # 10秒超时
            )
            
            print(f"评测返回码: {result.returncode}", flush=True)
            print(f"评测stdout: {result.stdout[:500] if result.stdout else 'empty'}", flush=True)
            print(f"评测stderr: {result.stderr[:500] if result.stderr else 'empty'}", flush=True)

            # 【改进】解析评测脚本的输出 - 增强错误检测
            if result.returncode == 0:
                try:
                    # 尝试解析JSON输出（新版本评测脚本）
                    output_data = json.loads(result.stdout.strip())
                    return {
                        'status': output_data.get('status', 'fail'),
                        'total_score': output_data.get('score', 0),
                        'max_score': 100,
                        'test_results': output_data.get('test_results', []),
                        'execution_time': 0,
                        'error_message': ''
                    }
                except json.JSONDecodeError:
                    # 解析文本输出（旧版本评测脚本）
                    return _parse_test_script_output(result.stdout)
            else:
                return {
                    'status': 'fail',
                    'total_score': 0,
                    'max_score': 100,
                    'test_results': [],
                    'execution_time': 0,
                    'error_message': f'评测脚本执行失败: {result.stderr}'
                }

        except subprocess.TimeoutExpired:
            return {
                'status': 'fail',
                'total_score': 0,
                'max_score': 100,
                'test_results': [],
                'execution_time': 0,
                'error_message': f'评测超时（超过5秒）。代码可能包含无限循环或死循环。'
            }
        except Exception as e:
            return {
                'status': 'fail',
                'total_score': 0,
                'max_score': 100,
                'test_results': [],
                'execution_time': 0,
                'error_message': f'评测过程出错: {str(e)}'
            }


def _execute_evaluation(task, tests, submission_data):
    """执行评测逻辑"""
    import json
    import time
    from app.services.code_executor import code_executor
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 检查任务类型（需要处理枚举类型）
        from app.models.models import TaskTypeEnum

        # 处理题目类型的任务（判断题、选择题）
        if task.task_type in [TaskTypeEnum.TRUE_FALSE, TaskTypeEnum.SINGLE_CHOICE, TaskTypeEnum.MULTIPLE_CHOICE]:
            user_answer = submission_data.get("answer")
            if user_answer is None:
                return {
                    "status": "fail",
                    "score": 0,
                    "total_tests": 1,
                    "passed_tests": 0,
                    "error_message": "答案不能为空",
                    "test_results": []
                }

            # 从题目数据中获取正确答案（优先从question_data字段读取，兼容旧数据从student_task_file_paths读取）
            try:
                question_json = task.question_data or task.student_task_file_paths
                if not question_json:
                    return {
                        "status": "fail",
                        "score": 0,
                        "total_tests": 1,
                        "passed_tests": 0,
                        "error_message": "题目数据缺失",
                        "test_results": []
                    }
                question_data = json.loads(question_json)
                
                # 支持多题目模式 - 兼容SSOT-P-v3.0格式（直接数组）和旧格式（包含questions键）
                questions = None
                if isinstance(question_data, list):
                    # SSOT-P-v3.0格式：直接是题目数组
                    questions = question_data
                elif isinstance(question_data, dict) and "questions" in question_data and question_data["questions"]:
                    # 旧格式：包含questions键的对象
                    questions = question_data["questions"]
                
                if questions and len(questions) > 0:
                    
                    # 检查是否是多题目提交（JSON格式的答案数组）
                    try:
                        user_answers_parsed = json.loads(user_answer) if isinstance(user_answer, str) and user_answer.startswith('[') else None
                    except json.JSONDecodeError:
                        user_answers_parsed = None
                    
                    if user_answers_parsed and len(questions) > 1:
                        # 多题目评测模式
                        total_questions = len(questions)
                        passed_questions = 0
                        test_results = []
                        wrong_questions = []
                        question_results = []  # 每道题的详细结果
                        
                        for i, q in enumerate(questions):
                            correct_answer = q.get("correctAnswer", q.get("correct_answer"))
                            q_type = q.get("type", "single")
                            q_content = q.get("content", f"题目{i+1}")
                            q_options = q.get("options", [])
                            q_explanation = q.get("explanation", "")
                            
                            # 找到该题的用户答案
                            user_q_answer = None
                            for ua in user_answers_parsed:
                                if ua.get("questionId") == q.get("id"):
                                    user_q_answer = ua.get("answer")
                                    break
                            
                            # 构建题目结果对象
                            q_result = {
                                "question_id": q.get("id", f"q{i+1}"),
                                "question_index": i,
                                "question_type": q_type,
                                "question_content": q_content,
                                "options": q_options,
                                "user_answer": user_q_answer,
                                "correct_answer": correct_answer,
                                "explanation": q_explanation,
                                "correct": False
                            }
                            
                            if user_q_answer is None:
                                test_results.append({"passed": False, "error_message": f"题目{i+1}未作答"})
                                wrong_questions.append(i+1)
                                question_results.append(q_result)
                                continue
                            
                            # 判断该题是否正确
                            q_correct = False
                            if q_type == "single":
                                # 单选题：比较索引
                                q_correct = int(user_q_answer) == int(correct_answer) if str(user_q_answer).isdigit() else False
                            else:
                                # 多选题：比较索引数组
                                if isinstance(user_q_answer, list) and isinstance(correct_answer, list):
                                    q_correct = set(user_q_answer) == set(correct_answer)
                                else:
                                    q_correct = False
                            
                            q_result["correct"] = q_correct
                            question_results.append(q_result)
                            
                            if q_correct:
                                passed_questions += 1
                                test_results.append({"passed": True, "error_message": ""})
                            else:
                                test_results.append({"passed": False, "error_message": f"题目{i+1}答案错误"})
                                wrong_questions.append(i+1)
                        
                        if passed_questions == total_questions:
                            return {
                                "status": "pass",
                                "score": 100,
                                "total_tests": total_questions,
                                "passed_tests": passed_questions,
                                "error_message": "全部回答正确",
                                "test_results": test_results,
                                "question_results": question_results,  # 新增：每道题详细结果
                                "execution_time": int((time.time() - start_time) * 1000)
                            }
                        else:
                            error_msg = f"题目 {', '.join(map(str, wrong_questions))} 回答错误"
                            return {
                                "status": "fail",
                                "score": int(passed_questions / total_questions * 100),
                                "total_tests": total_questions,
                                "passed_tests": passed_questions,
                                "error_message": error_msg,
                                "test_results": test_results,
                                "question_results": question_results,  # 新增：每道题详细结果
                                "execution_time": int((time.time() - start_time) * 1000)
                            }
                    else:
                        # 单题目模式（取第一道题）
                        q = questions[0]
                        # 兼容SSOT-P-v3.0格式（isCorrect）和旧格式（correctAnswer/correct_answer）
                        correct_answer = q.get("isCorrect", q.get("correctAnswer", q.get("correct_answer")))
                else:
                    # 没有questions数组，直接从question_data获取
                    if isinstance(question_data, dict):
                        correct_answer = question_data.get("isCorrect", question_data.get("correct_answer", question_data.get("correctAnswer")))
                    else:
                        correct_answer = None
            except (json.JSONDecodeError, AttributeError, TypeError) as e:
                logger.error(f"解析题目数据失败: {e}")
                return {
                    "status": "fail",
                    "score": 0,
                    "total_tests": 1,
                    "passed_tests": 0,
                    "error_message": "题目数据错误",
                    "test_results": []
                }

            # 单题目判断答案是否正确
            is_correct = False
            if task.task_type == TaskTypeEnum.TRUE_FALSE:
                # 判断题：用户答案和正确答案比较（处理字符串和布尔值）
                # "可以"、"正确"、"true"等被认为是true；"不可以"、"错误"、"false"等被认为是false
                user_str = str(user_answer).lower()
                user_bool = user_answer if isinstance(user_answer, bool) else user_str in ['true', '1', '正确', '可以', '是', 'yes']

                correct_str = str(correct_answer).lower()
                correct_bool = correct_answer if isinstance(correct_answer, bool) else correct_str in ['true', '1', '正确', '可以', '是', 'yes']

                is_correct = user_bool == correct_bool
            elif task.task_type in [TaskTypeEnum.SINGLE_CHOICE, TaskTypeEnum.MULTIPLE_CHOICE]:
                # 选择题：比较选项索引
                try:
                    if isinstance(correct_answer, list):
                        # 多选题
                        user_list = json.loads(user_answer) if isinstance(user_answer, str) else user_answer
                        if isinstance(user_list, list):
                            is_correct = set(user_list) == set(correct_answer)
                    else:
                        # 单选题
                        is_correct = int(user_answer) == int(correct_answer) if str(user_answer).isdigit() else False
                except (ValueError, TypeError, json.JSONDecodeError):
                    is_correct = False

            if is_correct:
                return {
                    "status": "pass",
                    "score": 100,
                    "total_tests": 1,
                    "passed_tests": 1,
                    "error_message": "回答正确",
                    "test_results": [{"passed": True, "error_message": ""}],
                    "execution_time": int((time.time() - start_time) * 1000)
                }
            else:
                return {
                    "status": "fail",
                    "score": 0,
                    "total_tests": 1,
                    "passed_tests": 0,
                    "error_message": "回答错误",
                    "test_results": [{"passed": False, "error_message": "答案不正确"}],
                    "execution_time": int((time.time() - start_time) * 1000)
                }

        elif task.task_type == TaskTypeEnum.PRACTICE or task.task_type.value == "PRACTICE" or task.task_type == TaskTypeEnum.CODE or task.task_type.value == "CODE":
            print(f">>> 进入 PRACTICE/CODE 评测分支, task_type={task.task_type}", flush=True)
            # 检查是否是HTML类型任务
            env_type = getattr(task, 'env_type', None)
            if env_type and env_type.lower() == 'html':
                # HTML任务评测
                html_content = submission_data.get("answer") or submission_data.get("code", "")
                if not html_content.strip():
                    return {
                        "status": "fail",
                        "score": 0,
                        "total_tests": len(tests),
                        "passed_tests": 0,
                        "error_message": "HTML代码不能为空",
                        "test_results": []
                    }
                
                # 准备测试用例
                test_cases = []
                for test in tests:
                    try:
                        test_case = {
                            'case_id': test.case_id,
                            'input_data': json.loads(test.input_data) if test.input_data else {},
                            'expected_output': json.loads(test.expected_output) if test.expected_output else {},
                            'is_hidden': test.is_hidden,
                            'description': test.description
                        }
                        # 从input_data中提取选择器
                        if test_case['input_data'].get('selector'):
                            test_case['selector'] = test_case['input_data']['selector']
                        if test_case['input_data'].get('check_type'):
                            test_case['check_type'] = test_case['input_data']['check_type']
                        test_cases.append(test_case)
                    except json.JSONDecodeError:
                        test_case = {
                            'case_id': test.case_id,
                            'input_data': {},
                            'expected_output': {},
                            'is_hidden': test.is_hidden
                        }
                        test_cases.append(test_case)
                
                logger.info(f"HTML Task {task.id} evaluation - test_cases_count: {len(test_cases)}")
                
                # 使用HTML评测器
                execution_result = code_executor.execute_html_evaluation(
                    html_content=html_content,
                    test_cases=test_cases
                )
                
                return {
                    "status": execution_result.get("status", "fail"),
                    "score": execution_result.get("score", 0),
                    "total_tests": execution_result.get("total_tests", len(tests)),
                    "passed_tests": execution_result.get("passed_tests", 0),
                    "error_message": execution_result.get("error_message", ""),
                    "test_results": execution_result.get("test_results", []),
                    "execution_time": execution_result.get("execution_time", 0)
                }
            
            # 编程题评测（Python等）
            # 优先使用answer字段，兼容旧版本的code字段
            code = submission_data.get("answer") or submission_data.get("code", "")
            if not code.strip():
                return {
                    "status": "fail",
                    "score": 0,
                    "total_tests": len(tests),
                    "passed_tests": 0,
                    "error_message": "代码不能为空",
                    "test_results": []
                }
            
            # 准备测试用例
            test_cases = []
            for test in tests:
                # match_rule 保留到 test_case dict 用于路由判定
                # ('exact' / 'EXACT_MATCH' / 'CONTAINS' → io_based; 'function_call' → function_call)
                match_rule = (test.match_rule or 'exact')
                try:
                    test_case = {
                        'input_data': json.loads(test.input_data) if test.input_data else {},
                        'expected_output': json.loads(test.expected_output) if test.expected_output else {},
                        'is_hidden': test.is_hidden,
                        'match_rule': match_rule,
                    }
                    test_cases.append(test_case)
                except json.JSONDecodeError:
                    test_case = {
                        'input_data': {},
                        'expected_output': {},
                        'is_hidden': test.is_hidden,
                        'match_rule': match_rule,
                    }
                    test_cases.append(test_case)

            # 判断是否使用基于输入/输出的评测方式
            # 如果任务没有evaluation_script_path，则使用IO模式
            logger.info(f"Task {task.id} evaluation - has_script: {bool(task.evaluation_script_path)}, test_cases_count: {len(test_cases)}")
            logger.info(f"Test cases: {test_cases}")

            if not task.evaluation_script_path:
                # 路由判定: 首条 test_case 的 match_rule 决定走哪个 evaluator.
                # 假设单关 task_tests match_rule 一致 (全 exact 或全 function_call), 不混用.
                # 现存数据 match_rule = NULL / 'exact' / 'EXACT_MATCH' / 'CONTAINS' →
                #   first_rule 不等于 'function_call' → 走 execute_io_based_code (v1 路径不变).
                # 新 v2 重生成 task_tests match_rule='function_call' → 走 execute_function_call_code.
                first_rule = (
                    test_cases[0].get('match_rule', 'exact').lower()
                    if test_cases else 'exact'
                )
                # 已知合法的 io_based 遗留规则(v1数据 NULL/exact/EXACT_MATCH/CONTAINS，
                # 均做字符串精确/包含比较)。慧学AI升级Phase1真实E2E UAT发现:AI生成的
                # 关卡如果被写入一个不在此列表里的占位match_rule(如'manual_review_pending'，
                # 表示"暂不支持自动评测")，会被这里的else分支静默当成io_based执行——
                # 但AI生成的test_cases是{function,args,kwargs}/{result}形状，和io_based
                # 期望的stdin/stdout字符串比较语义完全不兼容，导致学生正确答案也100%判0分，
                # 且不会报错、只会显示"评测不通过"，教师和学生都无法定位真实原因。
                # 因此这里改为显式白名单：只有已知的legacy io_based规则才走该分支，
                # 其他任何未识别的match_rule一律短路返回明确的"暂不支持自动评测"，
                # 不静默误判分数。
                KNOWN_IO_BASED_MATCH_RULES = {'exact', 'exact_match', 'contains'}
                if first_rule == 'function_call':
                    logger.info(f"Using execute_function_call_code for task {task.id}")
                    execution_result = code_executor.execute_function_call_code(
                        student_code=code,
                        test_cases=test_cases
                    )
                elif first_rule == 'pytest_module':
                    # Stage 3 综合关协议: backend 内置 test 模块 + 学生 student.py 跑 pytest
                    logger.info(f"Using execute_pytest_module for task {task.id}")
                    execution_result = code_executor.execute_pytest_module(
                        student_code=code,
                        test_cases=test_cases
                    )
                elif first_rule in KNOWN_IO_BASED_MATCH_RULES:
                    logger.info(f"Using execute_io_based_code for task {task.id}")
                    execution_result = code_executor.execute_io_based_code(
                        student_code=code,
                        test_cases=test_cases
                    )
                else:
                    logger.warning(
                        f"Task {task.id} has unrecognized match_rule='{first_rule}', "
                        f"refusing to auto-grade instead of silently misrouting to io_based"
                    )
                    # status='error' 命中下面第1452行的短路分支，是唯一能让
                    # error_message 真正透传给调用方而不是被静默吞成空字符串的路径。
                    execution_result = {
                        'status': 'error',
                        'error_message': (
                            f"该关卡的评测规则 '{first_rule}' 暂不支持自动评测,"
                            f"请联系教师人工批改或重新生成评测脚本"
                        ),
                        'execution_time': 0,
                    }
            else:
                # 使用评测脚本进行评测
                logger.info(f"Using _execute_with_test_script for task {task.id}")
                execution_result = _execute_with_test_script(
                    student_code=code,
                    test_script_path=task.evaluation_script_path,
                    test_cases=test_cases
                )
            
            # 添加调试日志
            logger.info(f"Execution result: {execution_result}")
            
            # 处理执行结果
            if execution_result.get('status') == 'error':
                return {
                    "status": "fail",
                    "score": 0,
                    "total_tests": len(tests),
                    "passed_tests": 0,
                    "error_message": execution_result.get('error_message', '代码执行错误'),
                    "test_results": [],
                    "execution_time": execution_result.get('execution_time', 0)
                }
            
            # 提取测试结果
            test_results = execution_result.get('test_results', [])
            
            # 优先使用解析的结果，如果没有则根据 test_results 计算
            if test_results:
                passed_count = sum(1 for r in test_results if r.get('passed', False))
            else:
                # 如果 test_results 为空，检查是否有直接的通过计数
                passed_count = execution_result.get('passed_tests', 0)
            
            total_score = execution_result.get('total_score', 0)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # 使用解析的状态，如果有的话
            parsed_status = execution_result.get('status', 'fail')
            if parsed_status == 'pass':
                status = 'pass'
                # 如果状态是pass，使用解析的分数或计算的分数
                score = total_score if total_score > 0 else task.coin
                passed_count = passed_count if passed_count > 0 else len(tests)
            else:
                status = "pass" if passed_count == len(tests) else "fail"
                score = int((passed_count / len(tests)) * task.coin) if tests else 0
            
            return {
                "status": status,
                "score": score,
                "total_tests": len(tests),
                "passed_tests": passed_count,
                "execution_time": execution_time,
                "error_message": execution_result.get('error_message', ''),
                "test_results": test_results
            }
            
        else:
            # 选择题/判断题评测
            answer = submission_data.get("answer", "")
            if not answer:
                return {
                    "status": "fail",
                    "score": 0,
                    "total_tests": 1,
                    "passed_tests": 0,
                    "error_message": "答案不能为空"
                }
            
            # 从question_data中获取正确答案
            question_data = json.loads(task.question_data or "{}")
            correct_answer = question_data.get("correct_answer", "")
            
            passed = answer.strip().upper() == correct_answer.strip().upper()
            
            return {
                "status": "pass" if passed else "fail",
                "score": task.coin if passed else 0,
                "total_tests": 1,
                "passed_tests": 1 if passed else 0,
                "execution_time": int((time.time() - start_time) * 1000),
                "test_results": [{
                    "test_id": 1,
                    "input_data": "题目",
                    "expected_output": correct_answer,
                    "actual_output": answer,
                    "passed": passed,
                    "error_message": None if passed else "答案错误"
                }]
            }
            
    except Exception as e:
        return {
            "status": "error",
            "score": 0,
            "total_tests": len(tests) if tests else 1,
            "passed_tests": 0,
            "error_message": str(e),
            "execution_time": int((time.time() - start_time) * 1000)
        }

# 保存代码快照
def save_code_snapshot(
    db: Session,
    task_id: str, 
    user_id: int, 
    repo_hash: str, 
    files: dict, 
    snapshot_type: str = "manual"
):
    """保存代码快照"""
    import json
    
    snapshot = models.TaskCodeSnapshot(
        task_id=task_id,
        user_id=user_id,
        repo_hash=repo_hash,
        files=json.dumps(files),
        snapshot_type=snapshot_type
    )
    
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    
    return snapshot

# 获取最后通关的代码快照
def get_last_pass_snapshot(db: Session, task_id: str, user_id: int):
    """获取最后一次通关的代码快照"""
    snapshot = db.query(models.TaskCodeSnapshot).filter(
        models.TaskCodeSnapshot.task_id == task_id,
        models.TaskCodeSnapshot.user_id == user_id,
        models.TaskCodeSnapshot.snapshot_type == "pass"
    ).order_by(models.TaskCodeSnapshot.created_at.desc()).first()

    return snapshot

# 获取通关时代的代码快照
def get_passed_code_snapshot(db: Session, task_id: str, user_id: int):
    """获取通关时代的代码快照，用于返回通关时代码功能"""
    # 查找最后一次通关的快照
    snapshot = get_last_pass_snapshot(db, task_id, user_id)

    if not snapshot:
        return None

    import json
    return {
        "id": snapshot.id,
        "task_id": snapshot.task_id,
        "user_id": snapshot.user_id,
        "repo_hash": snapshot.repo_hash,
        "files": json.loads(snapshot.files),
        "snapshot_type": snapshot.snapshot_type,
        "created_at": snapshot.created_at
    }

# 重置代码
def reset_task_code(db: Session, task_id: str, user_id: int, scope: str):
    """重置任务代码"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise ValueError("任务不存在")
    
    if scope == "last-pass":
        # 恢复到最后通关的代码
        snapshot = get_last_pass_snapshot(db, task_id, user_id)
        if not snapshot:
            raise ValueError("没有找到通关代码快照")
        
        import json
        return {
            "message": "已恢复到通关时的代码",
            "files": json.loads(snapshot.files)
        }
    
    elif scope == "all":
        # 重置全部代码到初始状态
        return {
            "message": "已重置全部代码到初始状态",
            "files": {}  # 这里应该返回初始代码
        }
    
    elif scope == "current":
        # 重置当前文件
        return {
            "message": "已重置当前文件到初始状态",
            "files": {}  # 这里应该返回当前文件的初始代码
        }
    
    else:
        raise ValueError("无效的重置范围")

# 实践环境相关操作
def reset_terminal(db: Session, terminal_id: int, user_id: int):
    """重置命令行环境"""
    # 这里应该调用实际的容器重置API
    return {"message": "命令行环境已重置"}

def extend_vdi_session(db: Session, vdi_id: int, user_id: int, minutes: int):
    """延长云桌面会话"""
    if minutes > 30:
        raise ValueError("延时不能超过30分钟")
    
    # 这里应该调用实际的VDI延时API
    return {"message": f"云桌面已延时{minutes}分钟"}

def reset_vdi_environment(db: Session, vdi_id: int, user_id: int):
    """重置云桌面环境"""
    # 这里应该调用实际的VDI重置API
    return {"message": "云桌面环境已重置"}

def reset_vdi_task(db: Session, vdi_id: int, user_id: int):
    """重置云桌面任务"""
    # 这里应该调用实际的VDI任务重置API
    return {"message": "云桌面任务已重置"} 

# 辅助函数：根据时间判断课堂状态
def determine_classroom_status(start_date, end_date) -> models.ClassroomStatusEnum:
    """根据当前时间和课堂起止时间判断课堂状态"""
    from datetime import datetime, timezone, date

    # 获取当前时间（timezone-aware）
    now = datetime.now(timezone.utc)

    # 确保start_date和end_date是timezone-aware datetime对象
    if isinstance(start_date, date) and not isinstance(start_date, datetime):
        # 如果是date对象，转换为当天开始时间
        start_date = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    elif isinstance(start_date, datetime) and start_date.tzinfo is None:
        # 如果是timezone-naive datetime，假设为UTC
        start_date = start_date.replace(tzinfo=timezone.utc)

    if isinstance(end_date, date) and not isinstance(end_date, datetime):
        # 如果是date对象，转换为当天结束时间
        end_date = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
    elif isinstance(end_date, datetime) and end_date.tzinfo is None:
        # 如果是timezone-naive datetime，假设为UTC
        end_date = end_date.replace(tzinfo=timezone.utc)

    # 比较时间
    if now < start_date:
        return models.ClassroomStatusEnum.NOT_STARTED
    elif start_date <= now <= end_date:
        return models.ClassroomStatusEnum.ONGOING
    else:
        return models.ClassroomStatusEnum.ENDED

# 辅助函数：生成学期信息
def generate_semester_info(start_date) -> Tuple[str, str]:
    """
    根据开始时间生成学期和学年信息
    规则：7/1之前是春季，7/1之后是秋季
    """
    from datetime import datetime, date
    
    # 处理start_date - 可能是date或datetime
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    elif isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    year = start_date.year
    month = start_date.month
    day = start_date.day
    
    if month < 7 or (month == 7 and day == 1):
        # 春季学期
        semester = "春"
        academic_year = f"{year-1}-{year}"
    else:
        # 秋季学期
        semester = "秋"
        academic_year = f"{year}-{year+1}"
    
    return semester, academic_year

# 辅助函数：状态转中文
def status_to_chinese(status: models.ClassroomStatusEnum) -> str:
    """将英文状态转换为中文"""
    status_map = {
        models.ClassroomStatusEnum.NOT_STARTED: "未开始",
        models.ClassroomStatusEnum.ONGOING: "正在上课",
        models.ClassroomStatusEnum.ENDED: "历史课堂"
    }
    return status_map.get(status, "未知")

# 计算课堂统计信息
def calculate_classroom_stats(db: Session, classroom_id: int) -> Dict:
    """计算课堂的统计信息"""
    # 获取课堂实例
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id
    ).first()
    
    if not classroom:
        return {
            "experiment_count": 0,
            "level_count": 0, 
            "coin_count": 0,
            "total_courses": 0,
            "finished_courses": 0,
            "progress_text": "0/0 实验"
        }
    
    # 获取课堂中的实践列表
    classroom_practices = db.query(models.ClassroomPractice).filter(
        models.ClassroomPractice.classroom_id == classroom_id
    ).all()
    
    # 获取课堂中的所有课程（实践类型）
    practice_courses = db.query(models.ClassroomCourse).join(
        models.Course
    ).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.Course.course_type == models.CourseTypeEnum.PRACTICE
    ).all()
    
    # 获取课堂中的实训课程
    training_courses = db.query(models.ClassroomCourse).join(
        models.Course
    ).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.Course.course_type == models.CourseTypeEnum.TRAINING
    ).all()
    
    experiment_count = 0  # 实验数（实践+实训）
    level_count = 0  # 关卡数
    coin_count = 0  # 金币数
    
    # 统计实践课程
    for cp in classroom_practices:
        practice = db.query(models.Practice).filter(
            models.Practice.id == cp.practice_id
        ).first()
        
        if practice:
            experiment_count += 1
            level_count += practice.task_count or 0
            coin_count += practice.coin or 0
    
    # 统计实训课程
    experiment_count += len(training_courses)  # 实训也算入实验数
    
    # 计算课程进度
    # 获取课堂中的所有课程（包括实践和其他类型）
    classroom_courses = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id
    ).all()
    
    total_courses = len(classroom_courses)  # 总课程数（包含所有类型）
    finished_courses = 0  # 已完成课程数
    
    # 计算已完成的课程（截止时间早于当前时间的课程）
    current_time = datetime.now(timezone.utc)
    for cc in classroom_courses:
        # 处理deadline_at的时区问题
        deadline = cc.deadline_at
        if deadline and deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        makeup_deadline = cc.makeup_deadline_at
        if makeup_deadline and makeup_deadline.tzinfo is None:
            makeup_deadline = makeup_deadline.replace(tzinfo=timezone.utc)

        if deadline and deadline < current_time:
            finished_courses += 1
        elif makeup_deadline and makeup_deadline < current_time:
            finished_courses += 1
    
    # 计算学生人数（从classroom_students表）
    total_students = db.query(models.ClassroomStudent).filter(
        models.ClassroomStudent.classroom_id == classroom_id
    ).count()

    # 更新课堂模型中的统计字段
    classroom.experiments_count = experiment_count
    classroom.experiment_levels_count = level_count
    classroom.coins_count = coin_count
    classroom.finished_experiments_count = finished_courses
    classroom.student_count = total_students
    
    try:
        db.commit()
    except Exception:
        db.rollback()

    return {
        "experiment_count": experiment_count,
        "level_count": level_count,
        "coin_count": coin_count,
        "total_courses": total_courses,
        "finished_courses": finished_courses,
        "progress_text": f"{finished_courses}/{total_courses} 实验",
        "total_students": total_students,
        "active_students": total_students,
        "completed_courses": finished_courses,
        "average_score": 0.0,
        "attendance_rate": 0.0
    }

# 新增：按状态获取课堂列表
def get_classrooms_by_status(db: Session, teacher_id: int) -> schemas.ClassroomsByStatusResponse:
    """按状态分组获取教师的课堂列表"""
    # 获取教师的所有课堂
    classrooms = db.query(models.Classroom).filter(
        models.Classroom.teacher_id == teacher_id,
        models.Classroom.deleted_at.is_(None)  # 排除软删除的课堂
    ).all()

    
    # 获取教师信息
    teacher = db.query(models.User).filter(models.User.id == teacher_id).first()
    teacher_name = teacher.full_name or teacher.username if teacher else "未知教师"
    
    ongoing = []
    upcoming = []
    ended = []
    
    for classroom in classrooms:
        # 自动更新课堂状态
        current_status = determine_classroom_status(classroom.start_date, classroom.end_date)
        if classroom.status != current_status:
            classroom.status = current_status
            db.commit()
        
        # 生成学期信息
        semester, academic_year = generate_semester_info(classroom.start_date)
        if not classroom.semester:
            classroom.semester = semester
        if not classroom.academic_year:
            classroom.academic_year = academic_year
            db.commit()
        
        # 计算统计信息
        stats = calculate_classroom_stats(db, classroom.id)
        
        # 构建课堂卡片数据
        card_data = {
            "id": classroom.id,
            "name": classroom.name,
            "description": classroom.description,
            "status": classroom.status,
            "status_cn": status_to_chinese(classroom.status),
            "teacher_id": classroom.teacher_id,
            "teacher_name": teacher_name,
            "teacher_avatar": None,  # TODO: 添加教师头像字段
            "credit": classroom.credit,
            "start_date": classroom.start_date,
            "end_date": classroom.end_date,
            "semester": classroom.semester or semester,
            "academic_year": classroom.academic_year or academic_year,
            "student_count": stats.get("total_students", 0),
            "cover_url": classroom.cover_url or "/api/static/images/classroom-default-cover.jpg",  # 课堂封面
            "created_at": classroom.created_at,
            **stats
        }
        
        # 按状态分组
        if classroom.status == models.ClassroomStatusEnum.ONGOING:
            ongoing.append(schemas.ClassroomCardResponse.model_validate(card_data))
        elif classroom.status == models.ClassroomStatusEnum.NOT_STARTED:
            upcoming.append(schemas.ClassroomCardResponse.model_validate(card_data))
        else:  # ENDED
            ended.append(schemas.ClassroomCardResponse.model_validate(card_data))
    
    return schemas.ClassroomsByStatusResponse(
        ongoing=ongoing,
        upcoming=upcoming,
        ended=ended,
        total_count=len(classrooms),
        ongoing_count=len(ongoing),
        upcoming_count=len(upcoming),
        ended_count=len(ended)
    )

# 新增：获取课堂详情（增强版）
def get_classroom_detail_enhanced(db: Session, classroom_id: int) -> Optional[schemas.ClassroomDetailEnhancedResponse]:
    """获取课堂详情（增强版）"""
    classroom = get_classroom(db, classroom_id)
    if not classroom:
        return None
    
    # 获取教师信息
    teacher = db.query(models.User).filter(models.User.id == classroom.teacher_id).first()
    teacher_name = teacher.full_name or teacher.username if teacher else "未知教师"
    
    # 自动更新课堂状态
    current_status = determine_classroom_status(classroom.start_date, classroom.end_date)
    if classroom.status != current_status:
        classroom.status = current_status
        db.commit()
    
    # 生成学期信息
    semester, academic_year = generate_semester_info(classroom.start_date)
    if not classroom.semester:
        classroom.semester = semester
    if not classroom.academic_year:
        classroom.academic_year = academic_year
        db.commit()
    
    # 计算统计信息
    stats = calculate_classroom_stats(db, classroom_id)
    
    # 获取课堂实践列表
    classroom_practices = get_classroom_practices(db, classroom_id)
    practice_list = []
    for cp in classroom_practices:
        practice = get_practice(db, cp.practice_id)
        if practice:
            practice_list.append({
                "id": practice.id,
                "title": practice.title,
                "description": practice.description,
                "difficulty": practice.difficulty,
                "task_count": practice.task_count,
                "coin": practice.coin,
                "sync_doc": cp.sync_doc
            })
            
    # 获取课堂实训列表 (新增)
    classroom_trainings = db.query(models.ClassroomTraining).filter(
        models.ClassroomTraining.classroom_id == classroom_id
    ).all()
    
    course_list = []
    for ct in classroom_trainings:
        training = db.query(models.Training).filter(models.Training.id == ct.training_id).first()
        if training:
            course_list.append({
                "id": str(training.id), # Frontend expects string ID often
                "name": training.title,
                "name_override": training.title,
                "type": "training",
                "status": "learning", # TODO: Get actual status from progress
                "coins": 0,
                "difficulty": 1, # Simple mapping
                "is_required": True,
                "order": ct.order_index or 0,
                "created_at": training.created_at,
                "training_type": training.training_type.value if training.training_type else "bi"
            })

    return schemas.ClassroomDetailEnhancedResponse(
        id=classroom.id,
        name=classroom.name,
        source_course_id=classroom.source_course_id,
        teacher_id=classroom.teacher_id,
        credit=classroom.credit,
        start_date=classroom.start_date,
        end_date=classroom.end_date,
        academic_year=classroom.academic_year,
        semester=classroom.semester,
        status=classroom.status,
        status_cn=status_to_chinese(classroom.status),
        teacher_name=teacher_name,
        teacher_avatar=None,  # TODO: 添加教师头像字段
        student_count=stats.get("total_students", 0),
        sync_resources_from_source=classroom.sync_resources_from_source if classroom.sync_resources_from_source is not None else False,
        sync_assessments_from_source=classroom.sync_assessments_from_source if classroom.sync_assessments_from_source is not None else False,
        created_at=classroom.created_at,
        updated_at=classroom.updated_at,
        deleted_at=classroom.deleted_at,
        course=None,  # 如果需要可以单独查询
        course_list=course_list,
        practice_list=practice_list,
        **stats
    )

# 新增：更新课堂
def update_classroom(db: Session, classroom_id: int, classroom_update: schemas.ClassroomUpdateRequest, teacher_id: int):
    """更新课堂信息"""
    # 检查课堂是否存在且属于该教师
    classroom = db.query(models.Classroom).filter(
        and_(
            models.Classroom.id == classroom_id,
            models.Classroom.teacher_id == teacher_id,
            models.Classroom.deleted_at.is_(None)
        )
    ).first()
    
    if not classroom:
        return None
    
    # 检查是否为历史课堂（历史课堂不允许编辑）
    current_status = determine_classroom_status(classroom.start_date, classroom.end_date)
    if current_status == models.ClassroomStatusEnum.ENDED:
        raise ValueError("历史课堂不允许编辑")
    
    # 检查课堂名称是否重复（排除自己）
    if classroom_update.name and classroom_update.name != classroom.name:
        existing = db.query(models.Classroom).filter(
            and_(
                models.Classroom.name == classroom_update.name,
                models.Classroom.teacher_id == teacher_id,
                models.Classroom.id != classroom_id,
                models.Classroom.deleted_at.is_(None)
            )
        ).first()
        
        if existing:
            raise ValueError("课堂名称已存在")
    
    # 检查日期有效性
    start_date = classroom_update.start_date or classroom.start_date
    end_date = classroom_update.end_date or classroom.end_date
    if end_date <= start_date:
        raise ValueError("结束时间必须晚于开始时间")
    
    # 更新字段
    update_data = classroom_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(classroom, field, value)
    
    # 如果日期发生变化，重新计算学期信息
    if classroom_update.start_date:
        classroom.semester = calculate_semester(classroom.start_date)
    
    # 更新状态
    classroom.status = determine_classroom_status(classroom.start_date, classroom.end_date)
    classroom.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(classroom)
    return classroom

# 新增：软删除课堂
def delete_classroom(db: Session, classroom_id: int, teacher_id: int):
    """删除课堂（软删除）"""
    # 检查权限
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == teacher_id,
        models.Classroom.deleted_at.is_(None)
    ).first()
    
    if not classroom:
        return None
    
    # 软删除
    classroom.deleted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(classroom)
    
    return classroom
# ==================== 课程状态相关CRUD操作 ====================

def get_classroom_courses(
    db: Session, 
    classroom_id: int, 
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    skip: int = 0, 
    limit: int = 20
):
    """获取课堂中的课程列表，支持状态筛选和关键词搜索"""
    query = db.query(models.ClassroomCourse).options(
        joinedload(models.ClassroomCourse.course),
        joinedload(models.ClassroomCourse.classroom)
    ).filter(models.ClassroomCourse.classroom_id == classroom_id)
    
    # 状态筛选
    if status and status != "all":
        if status == "unpublished":
            query = query.filter(models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED)
        elif status == "learning":
            query = query.filter(models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.LEARNING)
        elif status == "makeup":
            query = query.filter(models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.MAKEUP)
        elif status == "completed":
            query = query.filter(models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.COMPLETED)
    
    # 关键词搜索
    if keyword:
        query = query.join(models.Course).filter(
            or_(
                models.Course.title.ilike(f"%{keyword}%"),
                models.ClassroomCourse.classroom_chapter_title.ilike(f"%{keyword}%")
            )
        )
    
    # 排序
    query = query.order_by(models.ClassroomCourse.order_in_classroom, models.ClassroomCourse.id)
    
    total = query.count()
    courses = query.offset(skip).limit(limit).all()
    
    return courses, total

def get_classroom_course_status_summary(db: Session, classroom_id: int):
    """获取课堂课程状态统计（教师端）"""
    # 基础查询
    base_query = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id
    )

    # 统计各状态数量
    total = base_query.count()
    unpublished = base_query.filter(
        models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).count()
    learning = base_query.filter(
        models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.LEARNING
    ).count()
    makeup = base_query.filter(
        models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.MAKEUP
    ).count()
    completed = base_query.filter(
        models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.COMPLETED
    ).count()

    return {
        "total": total,
        "unpublished": unpublished,
        "learning": learning,
        "makeup": makeup,
        "completed": completed
    }

def get_classroom_course_status_summary_for_student(db: Session, classroom_id: int, student_id: int):
    """获取课堂课程状态统计（学生端个性化）"""
    # 查询该课堂中已发布的课程（未发布的课程学生看不到）
    published_courses = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.teacher_publish_status != models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).all()

    # 初始化统计
    total = 0
    not_started = 0
    learning = 0
    pending_makeup = 0
    completed_on_time = 0
    completed_late = 0

    for classroom_course in published_courses:
        # 查询学生的学习进度
        progress = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id == classroom_course.id,
            models.StudentCourseProgress.student_id == student_id
        ).first()

        total += 1

        if not progress:
            # 学生没有进度记录，说明未开始
            not_started += 1
        elif progress.student_status == models.CourseInClassroomStatusStudentEnum.LEARNING:
            # 正在学习
            learning += 1
        elif progress.student_status == models.CourseInClassroomStatusStudentEnum.PENDING_MAKEUP:
            # 待补交
            pending_makeup += 1
        elif progress.student_status == models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME:
            # 按时完成
            completed_on_time += 1
        elif progress.student_status == models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE:
            # 补交完成
            completed_late += 1
        else:
            # 其他状态默认为未开始
            not_started += 1

    return {
        "total": total,
        "not_started": not_started,
        "learning": learning,
        "pending_makeup": pending_makeup,
        "completed_on_time": completed_on_time,
        "completed_late": completed_late,
        "completed": completed_on_time + completed_late  # 总完成数
    }

def add_course_to_classroom(
    db: Session, 
    classroom_id: int, 
    course_id: int, 
    teacher_id: int,
    classroom_chapter_title: Optional[str] = None
):
    """添加课程到课堂"""
    # 检查课堂权限
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == teacher_id
    ).first()
    
    if not classroom:
        return None
    
    # 检查课程是否存在
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        return None
    
    # 检查是否已经添加
    existing = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.course_id == course_id
    ).first()
    
    if existing:
        return existing
    
    # 获取下一个排序位置
    max_order = db.query(func.max(models.ClassroomCourse.order_in_classroom)).filter(
        models.ClassroomCourse.classroom_id == classroom_id
    ).scalar() or 0
    
    # 创建课堂课程记录
    classroom_course = models.ClassroomCourse(
        classroom_id=classroom_id,
        course_id=course_id,
        classroom_chapter_title=classroom_chapter_title or course.title,
        order_in_classroom=max_order + 1,
        teacher_publish_status=models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    )
    
    db.add(classroom_course)
    db.commit()
    db.refresh(classroom_course)
    
    return classroom_course

def publish_classroom_courses(db: Session, classroom_id: int, course_ids: List[int], teacher_id: int,
                              deadline_at: Optional[str] = None, is_mandatory: Optional[bool] = True):
    """批量发布课程

    Args:
        course_ids: 前端传入的是 classroom_course.id 列表，不是 course.id
        deadline_at: 截止时间字符串 (YYYY-MM-DD 格式)
        is_mandatory: 是否必修
    """
    # 检查权限
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == teacher_id
    ).first()

    if not classroom:
        return False

    # 更新课程状态 - 使用 ClassroomCourse.id 而不是 course_id
    current_time = datetime.now(timezone.utc)

    # 准备更新数据
    update_data = {
        models.ClassroomCourse.teacher_publish_status: models.CourseInClassroomStatusTeacherEnum.LEARNING,
        models.ClassroomCourse.published_at: current_time,
        models.ClassroomCourse.is_mandatory: is_mandatory if is_mandatory is not None else True
    }

    # 如果提供了截止时间，解析并添加到更新数据
    if deadline_at:
        try:
            # 支持多种日期格式
            if 'T' in deadline_at:
                deadline_datetime = datetime.fromisoformat(deadline_at.replace('Z', '+00:00'))
            else:
                deadline_datetime = datetime.strptime(deadline_at, '%Y-%m-%d').replace(
                    hour=23, minute=59, second=59, tzinfo=timezone.utc
                )
            update_data[models.ClassroomCourse.deadline_at] = deadline_datetime
        except ValueError:
            pass  # 如果解析失败，不设置截止时间

    updated_count = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.id.in_(course_ids),
        models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).update(update_data, synchronize_session=False)

    db.commit()
    return updated_count > 0

def delete_classroom_courses(db: Session, classroom_id: int, course_ids: List[int], teacher_id: int):
    """批量删除课程

    Args:
        course_ids: 前端传入的是 classroom_course.id 列表，不是 course.id
    """
    # 检查权限
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == teacher_id
    ).first()

    if not classroom:
        return False

    # 只能删除未发布的课程 - 使用 ClassroomCourse.id 而不是 course_id
    deleted_count = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.id.in_(course_ids),
        models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).delete(synchronize_session=False)

    db.commit()
    return deleted_count > 0

def update_classroom_course_status(db: Session, classroom_course_id: int, teacher_id: int):
    """更新课程状态（基于时间和学生完成情况）"""
    # 获取课堂课程信息
    classroom_course = db.query(models.ClassroomCourse).options(
        joinedload(models.ClassroomCourse.classroom)
    ).filter(models.ClassroomCourse.id == classroom_course_id).first()
    
    if not classroom_course or classroom_course.classroom.teacher_id != teacher_id:
        return None
    
    current_time = datetime.now(timezone.utc)
    
    # 如果未发布，不更新状态
    if classroom_course.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED:
        return classroom_course
    
    # 检查是否所有学生都完成了
    total_students = db.query(models.StudentCourseProgress).filter(
        models.StudentCourseProgress.classroom_course_id == classroom_course_id
    ).count()
    
    completed_students = db.query(models.StudentCourseProgress).filter(
        models.StudentCourseProgress.classroom_course_id == classroom_course_id,
        models.StudentCourseProgress.student_status.in_([
            models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME,
            models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
        ])
    ).count()
    
    # 如果所有学生都完成了，状态为已完成
    if total_students > 0 and completed_students == total_students:
        classroom_course.teacher_publish_status = models.CourseInClassroomStatusTeacherEnum.COMPLETED
    # 如果超过截止时间，状态为补交中
    elif classroom_course.deadline_at and current_time > classroom_course.deadline_at:
        classroom_course.teacher_publish_status = models.CourseInClassroomStatusTeacherEnum.MAKEUP
    # 否则为学习中
    else:
        classroom_course.teacher_publish_status = models.CourseInClassroomStatusTeacherEnum.LEARNING
    
    db.commit()
    db.refresh(classroom_course)
    
    return classroom_course

def get_student_course_progress(db: Session, classroom_course_id: int, student_id: int):
    """获取学生课程进度"""
    return db.query(models.StudentCourseProgress).filter(
        models.StudentCourseProgress.classroom_course_id == classroom_course_id,
        models.StudentCourseProgress.student_id == student_id
    ).first()

def update_student_course_progress(
    db: Session, 
    classroom_course_id: int, 
    student_id: int,
    **kwargs
):
    """更新学生课程进度"""
    progress = get_student_course_progress(db, classroom_course_id, student_id)
    
    if not progress:
        # 创建新的进度记录
        progress = models.StudentCourseProgress(
            classroom_course_id=classroom_course_id,
            student_id=student_id,
            **kwargs
        )
        db.add(progress)
    else:
        # 更新现有记录
        for key, value in kwargs.items():
            setattr(progress, key, value)
    
    db.commit()
    db.refresh(progress)
    
    return progress

# 课程详情相关CRUD操作
def get_course_detail_banner(
    db: Session, 
    course_id: int, 
    classroom_id: Optional[int] = None,
    user_id: Optional[int] = None,
    is_practice: bool = False,
    is_training: bool = False
) -> Optional[dict]:
    """获取课程详情页面Banner信息"""
    if is_practice:
        practice = db.query(models.Practice).filter(models.Practice.id == course_id).first()
        if not practice:
            return None
            
        banner_data = {
            "id": practice.id,
            "title": practice.title,
            "course_type": "PRACTICE",
            "coin": practice.coin or 0,
            "difficulty": practice.difficulty.value if hasattr(practice.difficulty, 'value') else practice.difficulty,
            "difficulty_cn": _difficulty_to_chinese(practice.difficulty) if practice.difficulty else None,
            "student_stats": {"total": 0, "not_started": 0, "learning": 0, "completed": 0},
            "classroom": {}
        }
    elif is_training:
        training = db.query(models.Training).filter(models.Training.id == course_id).first()
        if not training:
            return None
            
        banner_data = {
            "id": training.id,
            "title": training.title,
            "course_type": "TRAINING",
            "coin": 0,
            "difficulty": training.difficulty.value if hasattr(training.difficulty, 'value') else training.difficulty,
            "difficulty_cn": _difficulty_to_chinese(training.difficulty) if training.difficulty else None,
            "student_stats": {"total": 0, "not_started": 0, "learning": 0, "completed": 0},
            "classroom": {}
        }
    else:
        course = db.query(models.Course).filter(models.Course.id == course_id).first()
        if not course:
            return None
        
        banner_data = {
            "id": course.id,
            "title": course.title,
            "course_type": course.course_type,
            "coin": 0,  # 默认值，后续根据任务计算
            "difficulty": course.difficulty.value if course.difficulty else None,
            "difficulty_cn": _difficulty_to_chinese(course.difficulty) if course.difficulty else None,
            "student_stats": {"total": 0, "not_started": 0, "learning": 0, "completed": 0},
            "classroom": {}
        }
    
    # 如果从课堂进入，获取课堂相关信息
    if classroom_id:
        classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
        if classroom:
            banner_data["classroom"] = {"id": classroom.id, "name": classroom.name}
            
            # 获取课程在课堂中的状态
            if is_training:
                classroom_training = db.query(models.ClassroomTraining).filter(
                    models.ClassroomTraining.classroom_id == classroom_id,
                    models.ClassroomTraining.training_id == course_id
                ).first()
                if classroom_training:
                    # Traing doesn't have course status yet so we just set some mock values
                    banner_data["status"] = "PUBLISHED"
                    banner_data["status_cn"] = "已发布"
                    banner_data["start_date"] = classroom.start_date
                    banner_data["end_date"] = classroom.end_date
                    banner_data["deadline_at"] = None
                    banner_data["makeup_deadline_at"] = None
                    banner_data["remaining_time"] = None
                    banner_data["student_stats"] = {"total": 0, "not_started": 0, "learning": 0, "completed": 0}
            else:
                # 查找 classroom_course: 先按 course_id 查, 再按 practice_id 查
                classroom_course = db.query(models.ClassroomCourse).filter(
                    models.ClassroomCourse.classroom_id == classroom_id,
                    models.ClassroomCourse.course_id == course_id
                ).first()
                if not classroom_course and is_practice:
                    classroom_course = db.query(models.ClassroomCourse).filter(
                        models.ClassroomCourse.classroom_id == classroom_id,
                        models.ClassroomCourse.practice_id == course_id
                    ).first()
                if classroom_course:
                    banner_data["status"] = classroom_course.teacher_publish_status.value
                    banner_data["status_cn"] = _course_status_to_chinese(classroom_course.teacher_publish_status)
                    banner_data["start_date"] = classroom.start_date
                    banner_data["end_date"] = classroom.end_date
                    banner_data["deadline_at"] = classroom_course.deadline_at
                    banner_data["makeup_deadline_at"] = classroom_course.makeup_deadline_at
                    banner_data["remaining_time"] = _calculate_remaining_time(classroom_course.deadline_at)
                    
                    # 获取学生统计信息
                    student_stats = _get_course_student_stats(db, classroom_course.id)
                    banner_data["student_stats"] = student_stats
    
    # 计算课程总金币数（实践课程：累加所有任务的金币）
    if is_practice or (not is_training and course and hasattr(course, 'course_type') and course.course_type == models.CourseTypeEnum.PRACTICE):
        total_coin = db.query(func.sum(models.Task.coin)).filter(
            models.Task.practice_id == course_id
        ).scalar() or 0
        banner_data["coin"] = int(total_coin)
    
    return banner_data

def get_course_tasks_with_progress(
    db: Session, 
    course_id: int, 
    user_id: Optional[int] = None,
    user_role: str = "student"
) -> List[dict]:
    """获取课程任务列表及进度信息"""
    tasks = []
    
    # 根据课程类型获取任务
    if user_role == "teacher":
        # 教师端：获取所有任务，不显示完成状态
        course_tasks = db.query(models.Task).filter(
            models.Task.practice_id == course_id
        ).order_by(models.Task.order_in_practice).all()
        
        for task in course_tasks:
            # 解析技能标签
            task_skills = []
            if task.skills:
                try:
                    task_skills = json.loads(task.skills) if isinstance(task.skills, str) else task.skills
                except (json.JSONDecodeError, TypeError):
                    task_skills = []

            task_data = {
                "id": task.id,
                "title": task.title,
                "task_type": task.task_type,
                "order_in_practice": task.order_in_practice,
                "coin": task.coin,
                "difficulty": task.difficulty,
                "skills": task_skills,
                "is_completed": False,  # 教师端不显示完成状态
                "completion_status": "可查看",
                "score": None,
                "completion_time": None
            }
            tasks.append(task_data)
    else:
        # 学生端：获取任务及完成状态
        course_tasks = db.query(models.Task).filter(
            models.Task.practice_id == course_id
        ).order_by(models.Task.order_in_practice).all()

        for task in course_tasks:
            # 获取学生的完成状态
            evaluation_result = None
            if user_id:
                evaluation_result = db.query(models.TaskEvaluationResult).filter(
                    models.TaskEvaluationResult.task_id == task.id,
                    models.TaskEvaluationResult.user_id == user_id,
                    models.TaskEvaluationResult.status == "pass"
                ).first()

            # 解析技能标签
            task_skills = []
            if task.skills:
                try:
                    task_skills = json.loads(task.skills) if isinstance(task.skills, str) else task.skills
                except (json.JSONDecodeError, TypeError):
                    task_skills = []

            task_data = {
                "id": task.id,
                "title": task.title,
                "task_type": task.task_type,
                "order_in_practice": task.order_in_practice,
                "coin": task.coin,
                "difficulty": task.difficulty,
                "skills": task_skills,
                "is_completed": evaluation_result is not None,
                "completion_status": "已完成" if evaluation_result else "未开始",
                "score": evaluation_result.score if evaluation_result else None,
                "completion_time": evaluation_result.created_at if evaluation_result else None
            }
            tasks.append(task_data)
    
    return tasks

def get_course_skills_with_progress(
    db: Session, 
    course_id: int, 
    user_id: Optional[int] = None,
    user_role: str = "student"
) -> List[dict]:
    """获取课程技能标签及点亮状态"""
    skills = []
    
    # 获取课程的所有技能标签
    practice_skills = db.query(models.PracticeSkill).filter(
        models.PracticeSkill.practice_id == course_id
    ).all()
    
    for skill in practice_skills:
        skill_data = {
            "skill_name": skill.skill_name,
            "is_unlocked": True if user_role == "teacher" else False,  # 教师端全部点亮
            "related_tasks": []
        }
        
        # 获取关联的任务 (skills存储为JSON字符串，使用LIKE匹配)
        related_tasks = db.query(models.Task.id).filter(
            models.Task.practice_id == course_id,
            models.Task.skills.like(f'%{skill.skill_name}%')
        ).all()
        skill_data["related_tasks"] = [task.id for task in related_tasks]
        
        # 学生端：根据任务完成情况判断是否点亮
        if user_role == "student" and user_id:
            # 检查相关任务是否有完成的
            completed_related_tasks = db.query(models.TaskEvaluationResult).filter(
                models.TaskEvaluationResult.user_id == user_id,
                models.TaskEvaluationResult.task_id.in_(skill_data["related_tasks"]),
                models.TaskEvaluationResult.status == "pass"
            ).count()
            
            skill_data["is_unlocked"] = completed_related_tasks > 0
        
        skills.append(skill_data)
    
    return skills

def get_course_learning_stats(
    db: Session, 
    course_id: int, 
    user_id: Optional[int] = None
) -> dict:
    """获取课程学习统计信息"""
    # 获取总任务数
    total_tasks = db.query(models.Task).filter(
        models.Task.practice_id == course_id
    ).count()
    
    completed_tasks = 0
    if user_id:
        # 获取已完成任务数
        completed_tasks = db.query(models.TaskEvaluationResult).filter(
            models.TaskEvaluationResult.user_id == user_id,
            models.TaskEvaluationResult.status == "pass"
        ).join(models.Task).filter(
            models.Task.practice_id == course_id
        ).count()
    
    progress_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # 计算已获得金币：累加已通关任务的coin值
    earned_coins = 0
    if user_id and completed_tasks > 0:
        coin_result = db.query(func.coalesce(func.sum(models.Task.coin), 0)).filter(
            models.Task.practice_id == course_id,
            models.Task.id.in_(
                db.query(models.TaskEvaluationResult.task_id).filter(
                    models.TaskEvaluationResult.user_id == user_id,
                    models.TaskEvaluationResult.status == "pass"
                ).join(models.Task).filter(
                    models.Task.practice_id == course_id
                )
            )
        ).scalar()
        earned_coins = int(coin_result) if coin_result else 0

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "progress_rate": round(progress_rate, 1),
        "earned_coins": earned_coins
    }

def get_course_assignments(
    db: Session, 
    course_id: int, 
    classroom_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> List[dict]:
    """获取实训课程的作业列表（学生端）"""
    assignments = []
    
    # 实训课程的作业提交功能
    if classroom_id:
        # 这里可以扩展作业提交相关的逻辑
        # 目前返回空列表，后续可以根据需求添加作业表
        pass
    
    return assignments

# 辅助函数
def _difficulty_to_chinese(difficulty) -> str:
    """难度级别转中文"""
    difficulty_map = {
        models.DifficultyEnum.BEGINNER: "初级",
        models.DifficultyEnum.INTERMEDIATE: "中级", 
        models.DifficultyEnum.ADVANCED: "高级"
    }
    if hasattr(models, 'DifficultyLevelEnum'):
        difficulty_map.update({
            getattr(models.DifficultyLevelEnum, 'beginner', 'beginner'): "初级",
            getattr(models.DifficultyLevelEnum, 'intermediate', 'intermediate'): "中级",
            getattr(models.DifficultyLevelEnum, 'advanced', 'advanced'): "高级"
        })
    return difficulty_map.get(difficulty, "未知")

def _course_status_to_chinese(status) -> str:
    """课程状态转中文"""
    status_map = {
        models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED: "未发布",
        models.CourseInClassroomStatusTeacherEnum.LEARNING: "学习中",
        models.CourseInClassroomStatusTeacherEnum.MAKEUP: "补交中",
        models.CourseInClassroomStatusTeacherEnum.COMPLETED: "已完成"
    }
    return status_map.get(status, "未知")

def _calculate_remaining_time(deadline: Optional[datetime]) -> Optional[str]:
    """计算剩余时间"""
    if not deadline:
        return None
    
    now = datetime.now(timezone.utc)
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    
    remaining = deadline - now
    
    if remaining.total_seconds() <= 0:
        return "已截止"
    
    days = remaining.days
    hours = remaining.seconds // 3600
    
    if days > 0:
        return f"剩余{days}天"
    elif hours > 0:
        return f"剩余{hours}小时"
    else:
        return "即将截止"

def _get_course_student_stats(db: Session, classroom_course_id: int) -> dict:
    """获取课程的学生统计信息"""
    classroom_course = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.id == classroom_course_id
    ).first()
    if not classroom_course:
        return {"total": 0, "not_started": 0, "learning": 0, "completed": 0}

    total_students = db.query(models.ClassroomStudent).filter(
        models.ClassroomStudent.classroom_id == classroom_course.classroom_id
    ).count()

    is_practice = classroom_course.practice_id is not None
    if is_practice:
        stats = {"total": total_students, "not_started": 0, "learning": 0, "completed": 0}

        student_ids = [
            row[0] for row in db.query(models.ClassroomStudent.student_id).filter(
                models.ClassroomStudent.classroom_id == classroom_course.classroom_id
            ).all()
        ]
        if not student_ids:
            return stats

        total_tasks = db.query(func.count(models.Task.id)).filter(
            models.Task.practice_id == classroom_course.practice_id,
            models.Task.deleted_at.is_(None),
        ).scalar() or 0
        if total_tasks == 0:
            stats["not_started"] = total_students
            return stats

        progress_rows = db.query(models.StudentPracticeProgress).filter(
            models.StudentPracticeProgress.practice_id == classroom_course.practice_id,
            models.StudentPracticeProgress.student_id.in_(student_ids),
        ).all()
        progress_by_student = {row.student_id: row for row in progress_rows}

        missing_student_ids = [sid for sid in student_ids if sid not in progress_by_student]
        auto_pass_counts = {}
        if missing_student_ids:
            auto_rows = db.query(
                models.TaskEvaluationResult.user_id,
                func.count(func.distinct(models.TaskEvaluationResult.task_id)).label("passed_count"),
            ).join(
                models.Task,
                models.Task.id == models.TaskEvaluationResult.task_id,
            ).filter(
                models.TaskEvaluationResult.user_id.in_(missing_student_ids),
                models.Task.practice_id == classroom_course.practice_id,
                models.Task.deleted_at.is_(None),
                models.TaskEvaluationResult.status == "pass",
            ).group_by(
                models.TaskEvaluationResult.user_id
            ).all()
            auto_pass_counts = {row.user_id: row.passed_count for row in auto_rows}

        for student_id in student_ids:
            progress = progress_by_student.get(student_id)
            if progress:
                passed_count = progress.completed_task_count or 0
                is_completed = bool(progress.is_completed) or passed_count >= total_tasks
            else:
                passed_count = auto_pass_counts.get(student_id, 0)
                is_completed = passed_count >= total_tasks

            if is_completed:
                stats["completed"] += 1
            elif passed_count > 0:
                stats["learning"] += 1
            else:
                stats["not_started"] += 1
        return stats

    progress_rows = db.query(models.StudentCourseProgress).filter(
        models.StudentCourseProgress.classroom_course_id == classroom_course_id
    ).all()
    completed_statuses = {
        models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME,
        models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE,
    }
    learning_statuses = {
        models.CourseInClassroomStatusStudentEnum.LEARNING,
        models.CourseInClassroomStatusStudentEnum.PENDING_MAKEUP,
    }
    completed = sum(1 for row in progress_rows if row.student_status in completed_statuses)
    learning = sum(1 for row in progress_rows if row.student_status in learning_statuses)
    not_started = max(total_students - completed - learning, 0)
    return {
        "total": total_students,
        "not_started": not_started,
        "learning": learning,
        "completed": completed
    }

# 学生管理相关CRUD操作

def get_students_by_search(
    db: Session, 
    keyword: Optional[str] = None,
    department: Optional[str] = None,
    major: Optional[str] = None,
    grade: Optional[str] = None,
    organization_id: Optional[str] = None,
    exclude_classroom_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 20
):
    """搜索学生列表，支持组织筛选和排除已在指定课堂的学生"""
    # 首先连接用户表和用户档案表，只查询学生类型的用户
    query = db.query(models.User).join(
        models.UserProfile,
        models.User.id == models.UserProfile.user_id
    ).filter(
        models.UserProfile.user_type == models.UserTypeEnum.STUDENT
    )
    
    # 如果需要按组织筛选，连接组织表
    if department or major or grade or organization_id:
        query = query.join(
            models.Organization,
            models.UserProfile.organization_id == models.Organization.id
        )
        
        # 根据组织层级筛选
        if organization_id:
            # 如果直接指定了组织ID
            query = query.filter(models.Organization.id == organization_id)
        else:
            # 根据部门、专业、年级名称筛选
            if department:
                query = query.filter(models.Organization.name.ilike(f"%{department}%"))
            if major:
                query = query.filter(models.Organization.name.ilike(f"%{major}%"))
            if grade:
                query = query.filter(models.Organization.name.ilike(f"%{grade}%"))
    
    # 关键词搜索（姓名或用户名）
    if keyword:
        query = query.filter(
            or_(
                models.User.full_name.ilike(f"%{keyword}%"),
                models.User.username.ilike(f"%{keyword}%")
            )
        )
    
    # 排除已在指定课堂的学生
    if exclude_classroom_id:
        existing_student_ids = db.query(models.ClassroomStudent.student_id).filter(
            models.ClassroomStudent.classroom_id == exclude_classroom_id
        ).subquery()
        query = query.filter(~models.User.id.in_(existing_student_ids))
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    students = query.offset(skip).limit(limit).all()
    
    return students, total

def get_classroom_students(
    db: Session, 
    classroom_id: int, 
    keyword: Optional[str] = None,
    skip: int = 0, 
    limit: int = 20
):
    """获取课堂学生列表"""
    query = db.query(models.ClassroomStudent).filter(
        models.ClassroomStudent.classroom_id == classroom_id
    ).join(models.User, models.ClassroomStudent.student_id == models.User.id)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                models.User.full_name.ilike(f"%{keyword}%"),
                models.User.username.ilike(f"%{keyword}%")
            )
        )
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    classroom_students = query.offset(skip).limit(limit).all()
    
    return classroom_students, total

def add_students_to_classroom(db: Session, classroom_id: int, student_ids: List[int]):
    """批量添加学生到课堂"""
    # 检查课堂是否存在
    classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    if not classroom:
        raise ValueError("课堂不存在")
    
    # 检查学生是否存在
    existing_students = db.query(models.User).filter(models.User.id.in_(student_ids)).all()
    existing_student_ids = [s.id for s in existing_students]
    
    # 检查哪些学生已经在课堂中
    existing_classroom_students = db.query(models.ClassroomStudent).filter(
        models.ClassroomStudent.classroom_id == classroom_id,
        models.ClassroomStudent.student_id.in_(student_ids)
    ).all()
    existing_in_classroom_ids = [cs.student_id for cs in existing_classroom_students]
    
    # 过滤出需要添加的学生ID
    new_student_ids = [sid for sid in existing_student_ids if sid not in existing_in_classroom_ids]
    
    # 批量创建课堂学生关联记录
    new_classroom_students = []
    for student_id in new_student_ids:
        classroom_student = models.ClassroomStudent(
            classroom_id=classroom_id,
            student_id=student_id
        )
        new_classroom_students.append(classroom_student)
    
    if new_classroom_students:
        db.add_all(new_classroom_students)
        
        # 更新课堂学生数量
        classroom.student_count = db.query(models.ClassroomStudent).filter(
            models.ClassroomStudent.classroom_id == classroom_id
        ).count()
        
        db.commit()
    
    return {
        "added_count": len(new_student_ids),
        "already_exists_count": len(existing_in_classroom_ids),
        "not_found_count": len(student_ids) - len(existing_student_ids)
    }

def remove_students_from_classroom(db: Session, classroom_id: int, student_ids: List[int]):
    """批量从课堂移除学生"""
    # 检查课堂是否存在
    classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    if not classroom:
        raise ValueError("课堂不存在")
    
    # 删除课堂学生关联记录
    deleted_count = db.query(models.ClassroomStudent).filter(
        models.ClassroomStudent.classroom_id == classroom_id,
        models.ClassroomStudent.student_id.in_(student_ids)
    ).delete(synchronize_session=False)
    
    # 更新课堂学生数量
    classroom.student_count = db.query(models.ClassroomStudent).filter(
        models.ClassroomStudent.classroom_id == classroom_id
    ).count()
    
    db.commit()
    
    return {"removed_count": deleted_count}
def get_organization_tree(db: Session):
    """获取组织架构树（模拟数据，实际应该从组织架构表获取）"""
    # 这里返回模拟的组织架构数据
    # 实际项目中应该从专门的组织架构表中获取
    return [
        {
            "id": "dept_1",
            "name": "计算机学院",
            "type": "department",
            "parent_id": None,
            "student_count": 150,
            "children": [
                {
                    "id": "major_1_1",
                    "name": "计算机科学与技术",
                    "type": "major",
                    "parent_id": "dept_1",
                    "student_count": 80,
                    "children": [
                        {
                            "id": "grade_1_1_1",
                            "name": "2021级",
                            "type": "grade",
                            "parent_id": "major_1_1",
                            "student_count": 25,
                            "children": []
                        },
                        {
                            "id": "grade_1_1_2",
                            "name": "2022级",
                            "type": "grade",
                            "parent_id": "major_1_1",
                            "student_count": 30,
                            "children": []
                        },
                        {
                            "id": "grade_1_1_3",
                            "name": "2023级",
                            "type": "grade",
                            "parent_id": "major_1_1",
                            "student_count": 25,
                            "children": []
                        }
                    ]
                },
                {
                    "id": "major_1_2",
                    "name": "软件工程",
                    "type": "major",
                    "parent_id": "dept_1",
                    "student_count": 70,
                    "children": [
                        {
                            "id": "grade_1_2_1",
                            "name": "2021级",
                            "type": "grade",
                            "parent_id": "major_1_2",
                            "student_count": 20,
                            "children": []
                        },
                        {
                            "id": "grade_1_2_2",
                            "name": "2022级",
                            "type": "grade",
                            "parent_id": "major_1_2",
                            "student_count": 25,
                            "children": []
                        },
                        {
                            "id": "grade_1_2_3",
                            "name": "2023级",
                            "type": "grade",
                            "parent_id": "major_1_2",
                            "student_count": 25,
                            "children": []
                        }
                    ]
                }
            ]
        },
        {
            "id": "dept_2",
            "name": "信息工程学院",
            "type": "department",
            "parent_id": None,
            "student_count": 120,
            "children": [
                {
                    "id": "major_2_1",
                    "name": "电子信息工程",
                    "type": "major",
                    "parent_id": "dept_2",
                    "student_count": 60,
                    "children": [
                        {
                            "id": "grade_2_1_1",
                            "name": "2021级",
                            "type": "grade",
                            "parent_id": "major_2_1",
                            "student_count": 20,
                            "children": []
                        },
                        {
                            "id": "grade_2_1_2",
                            "name": "2022级",
                            "type": "grade",
                            "parent_id": "major_2_1",
                            "student_count": 20,
                            "children": []
                        },
                        {
                            "id": "grade_2_1_3",
                            "name": "2023级",
                            "type": "grade",
                            "parent_id": "major_2_1",
                            "student_count": 20,
                            "children": []
                        }
                    ]
                },
                {
                    "id": "major_2_2",
                    "name": "通信工程",
                    "type": "major",
                    "parent_id": "dept_2",
                    "student_count": 60,
                    "children": [
                        {
                            "id": "grade_2_2_1",
                            "name": "2021级",
                            "type": "grade",
                            "parent_id": "major_2_2",
                            "student_count": 20,
                            "children": []
                        },
                        {
                            "id": "grade_2_2_2",
                            "name": "2022级",
                            "type": "grade",
                            "parent_id": "major_2_2",
                            "student_count": 20,
                            "children": []
                        },
                        {
                            "id": "grade_2_2_3",
                            "name": "2023级",
                            "type": "grade",
                            "parent_id": "major_2_2",
                            "student_count": 20,
                            "children": []
                        }
                    ]
                }
            ]
        }
    ]

def check_classroom_teacher_permission(db: Session, classroom_id: int, teacher_id: int):
    """检查教师是否有课堂管理权限 (超级管理员拥有所有权限)"""
    # 检查是否为超级管理员
    user = db.query(models.User).filter(models.User.id == teacher_id).first()
    if user and getattr(user, 'is_superuser', False):
        return True
        
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == teacher_id
    ).first()
    return classroom is not None

# ==================== 课程添加和发布相关CRUD函数 ====================

def get_courses_for_selection(
    db: Session,
    classroom_id: int,
    course_type: Optional[str] = None,
    keyword: Optional[str] = None,
    direction: Optional[str] = None,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    teacher_id: Optional[int] = None
):
    """获取可选择的课程列表（用于添加到课堂）

    包含两个来源：
    1. courses表中的课程
    2. practices表中已发布的实践课程（PRIVATE需要creator_id匹配，PUBLIC直接可见）
    """
    results = []

    # ========== 1. 查询 courses 表 ==========
    # 如果不是只查实践课程，或者没有指定类型，则查询courses表
    if course_type != "practice":
        query = db.query(models.Course)

        # 课程类型筛选
        if course_type:
            if course_type == "training":
                query = query.filter(models.Course.course_type == models.CourseTypeEnum.TRAINING)
            elif course_type == "course_material":
                query = query.filter(models.Course.course_type == models.CourseTypeEnum.COURSE_MATERIAL)

        # 关键词搜索
        if keyword:
            query = query.filter(models.Course.title.ilike(f"%{keyword}%"))

        # 方向筛选
        if direction:
            query = query.filter(models.Course.direction.ilike(f"%{direction}%"))

        # 分类筛选
        if category:
            query = query.filter(models.Course.categories.any(category))

        # 难度筛选
        if difficulty:
            query = query.filter(models.Course.difficulty == difficulty)

        # 获取已添加到课堂的课程ID
        existing_course_ids = db.query(models.ClassroomCourse.course_id).filter(
            models.ClassroomCourse.classroom_id == classroom_id
        ).subquery()

        # 排除已添加的课程
        query = query.filter(~models.Course.id.in_(existing_course_ids))

        courses = query.all()
        results.extend(courses)

    # ========== 2. 查询 practices 表中的实践课程 ==========
    # 如果查询的是实践课程或者没有指定类型，则查询practices表
    if course_type is None or course_type == "practice":
        practice_query = db.query(models.Practice)

        # 只查询已发布的实践
        practice_query = practice_query.filter(
            models.Practice.publish_status == models.PracticePublishStatusEnum.PUBLISHED
        )

        # 可见性筛选：
        # - PRIVATE实践只对创建者可见
        # - PUBLIC实践对所有人可见
        if teacher_id:
            practice_query = practice_query.filter(
                or_(
                    models.Practice.visibility == models.PracticeVisibilityEnum.PUBLIC,
                    and_(
                        models.Practice.visibility == models.PracticeVisibilityEnum.PRIVATE,
                        models.Practice.creator_id == teacher_id
                    )
                )
            )
        else:
            # 没有teacher_id时只显示公开的
            practice_query = practice_query.filter(
                models.Practice.visibility == models.PracticeVisibilityEnum.PUBLIC
            )

        # 关键词搜索
        if keyword:
            practice_query = practice_query.filter(models.Practice.title.ilike(f"%{keyword}%"))

        # 方向筛选
        if direction:
            practice_query = practice_query.filter(models.Practice.direction.ilike(f"%{direction}%"))

        # 分类筛选
        if category:
            practice_query = practice_query.filter(models.Practice.category.ilike(f"%{category}%"))

        # 难度筛选
        if difficulty:
            practice_query = practice_query.filter(models.Practice.difficulty == difficulty)

        # 获取已添加到课堂的实践课程ID
        existing_practice_ids = db.query(models.ClassroomCourse.practice_id).filter(
            models.ClassroomCourse.classroom_id == classroom_id,
            models.ClassroomCourse.practice_id.isnot(None)
        ).subquery()

        # 排除已添加的实践课程
        practice_query = practice_query.filter(~models.Practice.id.in_(existing_practice_ids))

        practices = practice_query.all()

        # 将Practice转换为类似Course的结构以便统一处理
        for practice in practices:
            # 创建一个包装对象，添加course_type属性
            practice._course_type = "PRACTICE"  # 添加临时属性

        results.extend(practices)

    # 总数
    total = len(results)

    # 分页
    paginated_results = results[skip:skip + limit]

    return paginated_results, total

def add_courses_by_timetable(
    db: Session,
    classroom_id: int,
    source_course_id: int,
    teacher_id: int,
    selected_modules: Optional[List[str]] = None
):
    """按课表添加课程"""
    # 检查权限
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == teacher_id
    ).first()
    
    if not classroom:
        return None
    
    # 检查源课程是否存在
    source_course = db.query(models.Course).filter(
        models.Course.id == source_course_id
    ).first()
    
    if not source_course:
        return None
    
    # 更新课堂的源课程
    classroom.source_course_id = source_course_id
    
    # 获取源课程的章节信息
    chapters = db.query(models.Chapter).filter(
        models.Chapter.course_id == source_course_id
    ).order_by(models.Chapter.order_index).all()
    
    # 如果选择了特定模块，只添加这些模块
    if selected_modules:
        chapters = [chapter for chapter in chapters if chapter.title in selected_modules]
    
    # 获取下一个排序位置
    max_order = db.query(func.max(models.ClassroomCourse.order_in_classroom)).filter(
        models.ClassroomCourse.classroom_id == classroom_id
    ).scalar() or 0
    
    added_courses = []
    
    # 为每个章节创建课堂课程记录
    for i, chapter in enumerate(chapters):
        # 检查是否已经添加过这个课程
        existing = db.query(models.ClassroomCourse).filter(
            models.ClassroomCourse.classroom_id == classroom_id,
            models.ClassroomCourse.course_id == source_course_id,
            models.ClassroomCourse.classroom_chapter_title == chapter.title
        ).first()
        
        if existing:
            continue
        
        # 创建课堂课程记录
        classroom_course = models.ClassroomCourse(
            classroom_id=classroom_id,
            course_id=source_course_id,
            classroom_chapter_title=chapter.title,
            order_in_classroom=max_order + i + 1,
            teacher_publish_status=models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
        )
        
        db.add(classroom_course)
        added_courses.append(classroom_course)
    
    # 如果没有章节信息，直接添加整个课程
    if not chapters:
        existing = db.query(models.ClassroomCourse).filter(
            models.ClassroomCourse.classroom_id == classroom_id,
            models.ClassroomCourse.course_id == source_course_id
        ).first()
        
        if not existing:
            classroom_course = models.ClassroomCourse(
                classroom_id=classroom_id,
                course_id=source_course_id,
                classroom_chapter_title=source_course.title,
                order_in_classroom=max_order + 1,
                teacher_publish_status=models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
            )
            
            db.add(classroom_course)
            added_courses.append(classroom_course)
    
    db.commit()
    
    # 刷新所有添加的课程
    for course in added_courses:
        db.refresh(course)
    
    return {
        "added_courses": added_courses,
        "source_course": source_course,
        "selected_modules": selected_modules or [],
        "total_added": len(added_courses)
    }

def add_practice_courses_to_classroom(
    db: Session,
    classroom_id: int,
    practice_ids: List[int],
    teacher_id: int,
    chapter_id: Optional[int] = None
):
    """添加实践课程到课堂

    注意：practice_ids 是 practices 表的 ID，不是 courses 表的 ID
    """
    # 检查权限
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == teacher_id
    ).first()

    if not classroom:
        return None

    added_courses = []

    # 获取当前最大排序
    max_order = db.query(func.max(models.ClassroomCourse.order_in_classroom)).filter(
        models.ClassroomCourse.classroom_id == classroom_id
    ).scalar() or 0

    for i, practice_id in enumerate(practice_ids):
        # 检查实践课程是否存在
        practice = db.query(models.Practice).filter(
            models.Practice.id == practice_id
        ).first()

        if not practice:
            continue

        # 检查是否已经添加（通过 practice_id 检查）
        existing = db.query(models.ClassroomCourse).filter(
            models.ClassroomCourse.classroom_id == classroom_id,
            models.ClassroomCourse.practice_id == practice_id
        ).first()

        if existing:
            continue

        # 创建课堂课程记录（使用 practice_id 而不是 course_id）
        classroom_course = models.ClassroomCourse(
            classroom_id=classroom_id,
            course_id=None,  # 实践课程不关联 courses 表
            practice_id=practice_id,  # 关联 practices 表
            classroom_chapter_id=chapter_id,
            classroom_chapter_title=practice.title,
            order_in_classroom=max_order + i + 1,
            teacher_publish_status=models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
        )

        db.add(classroom_course)
        added_courses.append(classroom_course)

    db.commit()

    # 刷新所有添加的课程
    for course in added_courses:
        db.refresh(course)

    return added_courses

def add_training_courses_to_classroom(
    db: Session,
    classroom_id: int,
    course_ids: List[int],
    teacher_id: int,
    chapter_id: Optional[int] = None
):
    """添加实训课程到课堂"""
    # 检查权限
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == teacher_id
    ).first()
    
    if not classroom:
        return None
    
    added_courses = []
    
    # 获取当前最大排序
    max_order = db.query(func.max(models.ClassroomCourse.order_in_classroom)).filter(
        models.ClassroomCourse.classroom_id == classroom_id
    ).scalar() or 0
    
    for i, course_id in enumerate(course_ids):
        # 检查课程是否存在且为实训类型
        course = db.query(models.Course).filter(
            models.Course.id == course_id,
            models.Course.course_type == models.CourseTypeEnum.TRAINING
        ).first()
        
        if not course:
            continue
        
        # 检查是否已经添加
        existing = db.query(models.ClassroomCourse).filter(
            models.ClassroomCourse.classroom_id == classroom_id,
            models.ClassroomCourse.course_id == course_id
        ).first()
        
        if existing:
            continue
        
        # 创建课堂课程记录
        classroom_course = models.ClassroomCourse(
            classroom_id=classroom_id,
            course_id=course_id,
            classroom_chapter_id=chapter_id,
            classroom_chapter_title=course.title,
            order_in_classroom=max_order + i + 1,
            teacher_publish_status=models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
        )
        
        db.add(classroom_course)
        added_courses.append(classroom_course)
    
    db.commit()
    
    # 刷新所有添加的课程
    for course in added_courses:
        db.refresh(course)
    
    return added_courses

def publish_single_course(
    db: Session,
    classroom_id: int,
    course_id: int,
    teacher_id: int,
    settings: dict
):
    """发布单个课程"""
    # 检查权限
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == teacher_id
    ).first()
    
    if not classroom:
        return None
    
    # 验证截止时间不能超过课堂结束时间
    deadline_at = settings.get('deadline_at')
    if deadline_at and deadline_at.date() > classroom.end_date:
        raise ValueError("课程截止时间不能超过课堂结束时间")
    
    # 查找课堂课程
    classroom_course = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.course_id == course_id,
        models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).first()
    
    if not classroom_course:
        return None
    
    # 更新发布状态和设置
    current_time = datetime.now(timezone.utc)
    classroom_course.teacher_publish_status = models.CourseInClassroomStatusTeacherEnum.LEARNING
    classroom_course.published_at = current_time
    classroom_course.deadline_at = deadline_at
    classroom_course.is_mandatory = settings.get('is_mandatory', True)
    classroom_course.allow_late_submission = settings.get('allow_late_submission', True)
    classroom_course.late_submission_deduction_points = settings.get('late_submission_deduction_points', 0)
    classroom_course.total_score = settings.get('total_score', 100)
    classroom_course.publicize_grades = settings.get('publicize_grades', False)
    classroom_course.publicize_answers_after_completion = settings.get('publicize_answers_after_completion', False)
    
    # 计算补交截止时间（默认为截止时间后7天）
    if deadline_at:
        classroom_course.makeup_deadline_at = deadline_at + timedelta(days=7)
    
    db.commit()
    db.refresh(classroom_course)
    
    return classroom_course

def publish_batch_courses(
    db: Session,
    classroom_id: int,
    course_ids: List[int],
    teacher_id: int,
    settings: dict
):
    """批量发布课程"""
    # 检查权限
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == teacher_id
    ).first()
    
    if not classroom:
        return None
    
    # 验证截止时间
    deadline_at = settings.get('deadline_at')
    if deadline_at and deadline_at.date() > classroom.end_date:
        raise ValueError("课程截止时间不能超过课堂结束时间")
    
    # 批量更新
    current_time = datetime.now(timezone.utc)
    makeup_deadline = deadline_at + timedelta(days=7) if deadline_at else None
    
    updated_count = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.course_id.in_(course_ids),
        models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).update({
        models.ClassroomCourse.teacher_publish_status: models.CourseInClassroomStatusTeacherEnum.LEARNING,
        models.ClassroomCourse.published_at: current_time,
        models.ClassroomCourse.deadline_at: deadline_at,
        models.ClassroomCourse.makeup_deadline_at: makeup_deadline,
        models.ClassroomCourse.is_mandatory: settings.get('is_mandatory', True),
        models.ClassroomCourse.allow_late_submission: settings.get('allow_late_submission', True),
        models.ClassroomCourse.late_submission_deduction_points: settings.get('late_submission_deduction_points', 0),
        models.ClassroomCourse.total_score: settings.get('total_score', 100),
        models.ClassroomCourse.publicize_grades: settings.get('publicize_grades', False),
        models.ClassroomCourse.publicize_answers_after_completion: settings.get('publicize_answers_after_completion', False)
    }, synchronize_session=False)
    
    db.commit()
    
    return updated_count

def publish_all_courses(
    db: Session,
    classroom_id: int,
    teacher_id: int,
    settings: dict
):
    """发布课堂中所有未发布的课程"""
    # 检查权限
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == teacher_id
    ).first()
    
    if not classroom:
        return None
    
    # 验证截止时间
    deadline_at = settings.get('deadline_at')
    if deadline_at and deadline_at.date() > classroom.end_date:
        raise ValueError("课程截止时间不能超过课堂结束时间")
    
    # 获取所有未发布的课程
    unpublished_courses = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).all()
    
    if not unpublished_courses:
        return 0
    
    # 批量更新
    current_time = datetime.now(timezone.utc)
    makeup_deadline = deadline_at + timedelta(days=7) if deadline_at else None
    
    course_ids = [course.course_id for course in unpublished_courses]
    
    updated_count = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.course_id.in_(course_ids),
        models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).update({
        models.ClassroomCourse.teacher_publish_status: models.CourseInClassroomStatusTeacherEnum.LEARNING,
        models.ClassroomCourse.published_at: current_time,
        models.ClassroomCourse.deadline_at: deadline_at,
        models.ClassroomCourse.makeup_deadline_at: makeup_deadline,
        models.ClassroomCourse.is_mandatory: settings.get('is_mandatory', True),
        models.ClassroomCourse.allow_late_submission: settings.get('allow_late_submission', True),
        models.ClassroomCourse.late_submission_deduction_points: settings.get('late_submission_deduction_points', 0),
        models.ClassroomCourse.total_score: settings.get('total_score', 100),
        models.ClassroomCourse.publicize_grades: settings.get('publicize_grades', False),
        models.ClassroomCourse.publicize_answers_after_completion: settings.get('publicize_answers_after_completion', False)
    }, synchronize_session=False)
    
    db.commit()
    
    return updated_count

def publish_chapter_courses(
    db: Session,
    classroom_id: int,
    chapter_title: str,
    teacher_id: int,
    settings: dict
):
    """按章节发布课程（一键发布）"""
    # 检查权限
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == teacher_id
    ).first()
    
    if not classroom:
        return None
    
    # 验证截止时间
    deadline_at = settings.get('deadline_at')
    if deadline_at and deadline_at.date() > classroom.end_date:
        raise ValueError("课程截止时间不能超过课堂结束时间")
    
    # 获取指定章节下的所有未发布课程
    unpublished_courses = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.classroom_chapter_title == chapter_title,
        models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).all()
    
    if not unpublished_courses:
        return 0
    
    # 批量更新
    current_time = datetime.now(timezone.utc)
    makeup_deadline = deadline_at + timedelta(days=7) if deadline_at else None
    
    course_ids = [course.course_id for course in unpublished_courses]
    
    updated_count = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.classroom_chapter_title == chapter_title,
        models.ClassroomCourse.course_id.in_(course_ids),
        models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).update({
        models.ClassroomCourse.teacher_publish_status: models.CourseInClassroomStatusTeacherEnum.LEARNING,
        models.ClassroomCourse.published_at: current_time,
        models.ClassroomCourse.deadline_at: deadline_at,
        models.ClassroomCourse.makeup_deadline_at: makeup_deadline,
        models.ClassroomCourse.is_mandatory: settings.get('is_mandatory', True),
        models.ClassroomCourse.allow_late_submission: settings.get('allow_late_submission', True),
        models.ClassroomCourse.late_submission_deduction_points: settings.get('late_submission_deduction_points', 0),
        models.ClassroomCourse.total_score: settings.get('total_score', 100),
        models.ClassroomCourse.publicize_grades: settings.get('publicize_grades', False),
        models.ClassroomCourse.publicize_answers_after_completion: settings.get('publicize_answers_after_completion', False)
    }, synchronize_session=False)
    
    db.commit()
    
    return updated_count

def get_classroom_courses_with_stats(
    db: Session,
    classroom_id: int,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取带统计信息的课堂课程列表"""
    # 基础查询（同时加载 course 和 practice 关联）
    query = db.query(models.ClassroomCourse).options(
        joinedload(models.ClassroomCourse.course),
        joinedload(models.ClassroomCourse.practice),
        joinedload(models.ClassroomCourse.classroom_chapter)
    ).filter(models.ClassroomCourse.classroom_id == classroom_id)
    
    # 状态筛选
    if status and status != "all":
        if status == "unpublished":
            query = query.filter(models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED)
        elif status == "learning":
            query = query.filter(models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.LEARNING)
        elif status == "makeup":
            query = query.filter(models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.MAKEUP)
        elif status == "completed":
            query = query.filter(models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.COMPLETED)
    
    # 关键词搜索
    if keyword:
        query = query.join(models.Course).filter(
            models.Course.title.ilike(f"%{keyword}%")
        )
    
    # 总数
    total = query.count()

    # Z2.2 修: 加 ORDER BY 防止 PostgreSQL 物理顺序混乱.
    # 按 classroom 内的展示顺序 (order_in_classroom asc), 同顺序值或 NULL 时 fallback id asc.
    # 历史 bug: 大数据 105 12 行 frontend 显示倒序 (id desc, 关卡 12→1).
    query = query.order_by(
        models.ClassroomCourse.order_in_classroom.asc().nullslast(),
        models.ClassroomCourse.id.asc(),
    )

    # 分页
    classroom_courses = query.offset(skip).limit(limit).all()
    
    # 为每个课程添加统计信息
    result = []
    for classroom_course in classroom_courses:
        # 获取学生统计
        student_stats = _get_course_student_stats(db, classroom_course.id)
        
        # 状态中文显示
        status_cn_map = {
            models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED: "未发布",
            models.CourseInClassroomStatusTeacherEnum.LEARNING: "学习中",
            models.CourseInClassroomStatusTeacherEnum.MAKEUP: "补交中",
            models.CourseInClassroomStatusTeacherEnum.COMPLETED: "已完成"
        }
        
        # 计算剩余天数
        remaining_days = None
        is_overdue = False
        if classroom_course.deadline_at:
            deadline = classroom_course.deadline_at
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            remaining = deadline - datetime.now(timezone.utc)
            remaining_days = remaining.days
            is_overdue = remaining_days < 0
        
        # 将枚举状态转换为小写字符串（前端期望格式）
        status_value = classroom_course.teacher_publish_status.value.lower() if classroom_course.teacher_publish_status else "unpublished"
        
        # 从 __dict__ 中排除 SQLAlchemy 内部状态和关系对象
        # 排除的关系字段名列表
        excluded_relations = {'classroom', 'course', 'practice', 'classroom_chapter', 'student_progress', 'evaluations'}
        classroom_course_dict = {
            k: v for k, v in classroom_course.__dict__.items()
            if not k.startswith('_') and k not in excluded_relations
        }

        course_excluded = {'chapters', 'tasks', 'classroom_courses', 'evaluations'}
        course_dict = {
            k: v for k, v in classroom_course.course.__dict__.items()
            if not k.startswith('_') and k not in course_excluded
        } if classroom_course.course else None

        # 处理 practice 类型的课程（practice_id 有值但 course_id 为空）
        practice_excluded = {'stages', 'creator', 'classroom_courses'}
        practice_dict = {
            k: v for k, v in classroom_course.practice.__dict__.items()
            if not k.startswith('_') and k not in practice_excluded
        } if classroom_course.practice else None

        # 优先使用 name_override（课堂内的自定义名称）
        # 然后使用 course 或 practice 的原始名称
        if classroom_course.course:
            original_name = classroom_course.course.title
            course_cover = classroom_course.course.cover_url
            source_type = "course"
        elif classroom_course.practice:
            original_name = classroom_course.practice.title
            course_cover = classroom_course.practice.cover_url
            source_type = "practice"
        else:
            original_name = classroom_course.classroom_chapter_title
            course_cover = None
            source_type = "unknown"

        # 如果有自定义名称，优先使用
        course_name = classroom_course.name_override if classroom_course.name_override else original_name

        course_data = {
            **classroom_course_dict,
            "course": course_dict,
            "practice": practice_dict,
            "source_type": source_type,  # 标识来源类型
            "course_name": course_name,
            "course_cover": course_cover,
            "classroom_chapter_title": classroom_course.classroom_chapter.title if classroom_course.classroom_chapter else None,
            "student_count": student_stats["total"],
            "not_started_count": student_stats["not_started"],
            "learning_count": student_stats["learning"],
            "completed_count": student_stats["completed"],
            "studentCount": student_stats["total"],
            "notStartedCount": student_stats["not_started"],
            "learningCount": student_stats["learning"],
            "completedCount": student_stats["completed"],
            "status_cn": status_cn_map.get(classroom_course.teacher_publish_status, "未知"),
            "status": status_value,  # 添加小写格式的状态
            "remaining_days": remaining_days,
            "is_overdue": is_overdue
        }
        
        result.append(course_data)
    
    return result, total

def get_course_filter_tags_for_selection(db: Session, course_type: Optional[str] = None):
    """获取课程选择页面的筛选标签"""
    query = db.query(models.Course)
    
    # 根据课程类型筛选
    if course_type:
        if course_type == "practice":
            query = query.filter(models.Course.course_type == models.CourseTypeEnum.PRACTICE)
        elif course_type == "training":
            query = query.filter(models.Course.course_type == models.CourseTypeEnum.TRAINING)
        elif course_type == "course_material":
            query = query.filter(models.Course.course_type == models.CourseTypeEnum.COURSE_MATERIAL)
    
    courses = query.all()
    
    # 提取标签
    directions = set()
    categories = set()
    difficulties = set()
    
    for course in courses:
        if course.direction:
            directions.add(course.direction)
        if course.categories:
            for category in course.categories:
                categories.add(category)
        if course.difficulty:
            difficulties.add(course.difficulty.value)
    
    return {
        "directions": sorted(list(directions)),
        "categories": sorted(list(categories)),
        "difficulties": sorted(list(difficulties))
    }
def get_classroom_chapters(db: Session, classroom_id: int, teacher_id: int):
    """获取课堂中的章节列表"""
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return None

    # 从ClassroomChapter表获取章节列表
    chapters = db.query(models.ClassroomChapter).filter(
        models.ClassroomChapter.classroom_id == classroom_id
    ).order_by(models.ClassroomChapter.order_index).all()

    chapter_list = []
    for chapter in chapters:
        # 统计该章节下的课程数量
        course_count = db.query(func.count(models.ClassroomCourse.id)).filter(
            models.ClassroomCourse.classroom_id == classroom_id,
            models.ClassroomCourse.classroom_chapter_id == chapter.id
        ).scalar() or 0

        # 统计未发布的课程数量
        unpublished_count = db.query(func.count(models.ClassroomCourse.id)).filter(
            models.ClassroomCourse.classroom_id == classroom_id,
            models.ClassroomCourse.classroom_chapter_id == chapter.id,
            models.ClassroomCourse.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
        ).scalar() or 0

        chapter_list.append({
            "id": chapter.id,
            "title": chapter.title,
            "order_index": chapter.order_index,
            "course_count": course_count,
            "unpublished_count": unpublished_count,
            "can_publish": unpublished_count > 0
        })

    return chapter_list

# ==================== 课堂管理相关CRUD操作 ====================

def get_classroom_catalog(db: Session, classroom_id: int, teacher_id: int):
    """获取课堂目录结构（章节+课程）"""
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return None
    
    # 获取所有章节
    chapters = db.query(models.ClassroomChapter).filter(
        models.ClassroomChapter.classroom_id == classroom_id
    ).order_by(models.ClassroomChapter.order_index).all()
    
    # 获取所有课程
    courses = db.query(models.ClassroomCourse).options(
        joinedload(models.ClassroomCourse.course)
    ).filter(
        models.ClassroomCourse.classroom_id == classroom_id
    ).order_by(models.ClassroomCourse.order_in_classroom).all()
    
    # 构建目录结构
    catalog = []
    
    # 添加章节及其下的课程
    for chapter in chapters:
        chapter_node = {
            "id": chapter.id,
            "type": "chapter",
            "title": chapter.title,
            "order_index": chapter.order_index,
            "children": []
        }
        
        # 统计章节下的课程
        chapter_courses = [c for c in courses if c.classroom_chapter_id == chapter.id]
        chapter_node["course_count"] = len(chapter_courses)
        chapter_node["practice_count"] = len([c for c in chapter_courses if c.course.course_type == models.CourseTypeEnum.PRACTICE])
        chapter_node["training_count"] = len([c for c in chapter_courses if c.course.course_type == models.CourseTypeEnum.TRAINING])
        
        # 添加章节下的课程
        for course in chapter_courses:
            course_node = {
                "id": course.id,
                "type": "course",
                "title": course.course.title,
                "order_index": course.order_in_classroom,
                "course_type": course.course.course_type,
                "status": course.teacher_publish_status.value,
                "status_cn": get_course_status_cn(course.teacher_publish_status),
                "deadline_at": course.deadline_at,
                "is_mandatory": course.is_mandatory,
                "chapter_id": chapter.id
            }
            chapter_node["children"].append(course_node)
        
        catalog.append(chapter_node)
    
    # 添加未分章节的课程
    orphan_courses = [c for c in courses if c.classroom_chapter_id is None]
    for course in orphan_courses:
        course_node = {
            "id": course.id,
            "type": "course",
            "title": course.course.title,
            "order_index": course.order_in_classroom,
            "course_type": course.course.course_type,
            "status": course.teacher_publish_status.value,
            "status_cn": get_course_status_cn(course.teacher_publish_status),
            "deadline_at": course.deadline_at,
            "is_mandatory": course.is_mandatory,
            "chapter_id": None
        }
        catalog.append(course_node)
    
    return catalog

def get_course_status_cn(status):
    """获取课程状态中文名称"""
    status_map = {
        models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED: "未发布",
        models.CourseInClassroomStatusTeacherEnum.LEARNING: "学习中",
        models.CourseInClassroomStatusTeacherEnum.MAKEUP: "补交中",
        models.CourseInClassroomStatusTeacherEnum.COMPLETED: "已完成"
    }
    return status_map.get(status, "未知")

def create_classroom_chapter(db: Session, classroom_id: int, title: str, teacher_id: int):
    """创建课堂章节"""
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return None
    
    # 获取下一个排序位置
    max_order = db.query(func.max(models.ClassroomChapter.order_index)).filter(
        models.ClassroomChapter.classroom_id == classroom_id
    ).scalar() or 0
    
    # 创建章节
    chapter = models.ClassroomChapter(
        classroom_id=classroom_id,
        title=title,
        order_index=max_order + 1
    )
    
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    
    return chapter

def update_classroom_chapter(db: Session, chapter_id: int, title: str, teacher_id: int):
    """重命名课堂章节"""
    # 获取章节
    chapter = db.query(models.ClassroomChapter).filter(
        models.ClassroomChapter.id == chapter_id
    ).first()
    
    if not chapter:
        return None
    
    # 检查权限
    if not check_classroom_teacher_permission(db, chapter.classroom_id, teacher_id):
        return None
    
    # 更新标题
    chapter.title = title
    db.commit()
    db.refresh(chapter)
    
    return chapter

def delete_classroom_chapter(db: Session, chapter_id: int, teacher_id: int):
    """删除课堂章节（同时删除章节下的课程）"""
    # 获取章节
    chapter = db.query(models.ClassroomChapter).filter(
        models.ClassroomChapter.id == chapter_id
    ).first()
    
    if not chapter:
        return False
    
    # 检查权限
    if not check_classroom_teacher_permission(db, chapter.classroom_id, teacher_id):
        return False
    
    # 删除章节下的课程
    db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_chapter_id == chapter_id
    ).delete()
    
    # 删除章节
    db.delete(chapter)
    db.commit()
    
    return True

def update_course_order(db: Session, classroom_id: int, order_items: List, teacher_id: int):
    """更新课程和章节排序"""
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return False
    
    try:
        for item in order_items:
            # 如果item是Pydantic模型，转换为字典
            if hasattr(item, 'model_dump'):
                item_dict = item.model_dump()
            else:
                item_dict = item
                
            if item_dict["type"] == "chapter":
                # 更新章节排序
                db.query(models.ClassroomChapter).filter(
                    models.ClassroomChapter.id == item_dict["id"],
                    models.ClassroomChapter.classroom_id == classroom_id
                ).update({
                    "order_index": item_dict["order_index"]
                })
            elif item_dict["type"] == "course":
                # 更新课程排序和所属章节
                update_data = {
                    "order_in_classroom": item_dict["order_index"]
                }
                if "chapter_id" in item_dict:
                    update_data["classroom_chapter_id"] = item_dict["chapter_id"]
                
                db.query(models.ClassroomCourse).filter(
                    models.ClassroomCourse.id == item_dict["id"],
                    models.ClassroomCourse.classroom_id == classroom_id
                ).update(update_data)
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False

def rename_classroom_course(db: Session, classroom_course_id: int, new_title: str, teacher_id: int):
    """重命名课堂中的课程"""
    # 获取课程
    classroom_course = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.id == classroom_course_id
    ).first()
    
    if not classroom_course:
        return None
    
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_course.classroom_id, teacher_id):
        return None
    
    # 更新课程自定义名称（不影响原课程标题）
    classroom_course.name_override = new_title
    db.commit()
    db.refresh(classroom_course)
    
    return classroom_course

def update_course_settings(db: Session, classroom_course_id: int, settings: dict, teacher_id: int):
    """更新课程设置"""
    # 获取课程
    classroom_course = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.id == classroom_course_id
    ).first()
    
    if not classroom_course:
        return None
    
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_course.classroom_id, teacher_id):
        return None
    
    # 更新设置
    for key, value in settings.items():
        if hasattr(classroom_course, key):
            setattr(classroom_course, key, value)
    
    db.commit()
    db.refresh(classroom_course)
    
    return classroom_course

def delete_classroom_course(db: Session, classroom_course_id: int, teacher_id: int):
    """删除课堂中的课程"""
    # 获取课程
    classroom_course = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.id == classroom_course_id
    ).first()
    
    if not classroom_course:
        return False
    
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_course.classroom_id, teacher_id):
        return False
    
    # 只能删除未完成的课程
    if classroom_course.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.COMPLETED:
        return False
    
    # 删除课程
    db.delete(classroom_course)
    db.commit()
    
    return True

def get_classroom_management_data(db: Session, classroom_id: int, teacher_id: int):
    """获取课堂管理页面完整数据"""
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return None
    
    # 获取课堂基本信息
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id
    ).first()
    
    if not classroom:
        return None
    
    # 获取目录结构
    catalog = get_classroom_catalog(db, classroom_id, teacher_id)
    
    # 统计信息
    total_courses = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id
    ).count()
    
    practice_courses = db.query(models.ClassroomCourse).join(models.Course).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.Course.course_type == models.CourseTypeEnum.PRACTICE
    ).count()
    
    training_courses = db.query(models.ClassroomCourse).join(models.Course).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.Course.course_type == models.CourseTypeEnum.TRAINING
    ).count()
    
    published_courses = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.teacher_publish_status != models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).count()
    
    total_chapters = db.query(models.ClassroomChapter).filter(
        models.ClassroomChapter.classroom_id == classroom_id
    ).count()
    
    stats = {
        "total_chapters": total_chapters,
        "total_courses": total_courses,
        "practice_courses": practice_courses,
        "training_courses": training_courses,
        "published_courses": published_courses,
        "unpublished_courses": total_courses - published_courses
    }
    
    return {
        "classroom_info": {
            "id": classroom.id,
            "name": classroom.name,
            "status": classroom.status.value,
            "start_date": classroom.start_date,
            "end_date": classroom.end_date,
            "student_count": classroom.student_count
        },
        "catalog": catalog,
        "stats": stats
    }

# ==================== 成绩查看和作业点评相关CRUD操作 ====================

def get_course_grades(
    db: Session,
    classroom_id: int,
    classroom_course_id: int,
    teacher_id: int,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取课程成绩列表 (P1-W2-1 真修: 融合 task_evaluation_results)

    老逻辑只读 student_course_progress (SCP), 学生 fc 自动评测不写 SCP, 教师视角看不到.
    Phase C 改: PRACTICE 课程同时拉 task_evaluation_results (TER) latest per
    (user_id, task_id), 融合到 grade_data 的 completed_tasks / task_score /
    submission_time / assignment_status / current_score 字段中. 老字段不破坏 frontend
    course-grades.vue 字段映射.
    """
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return None, 0

    # 获取课程信息
    classroom_course = db.query(models.ClassroomCourse).options(
        joinedload(models.ClassroomCourse.course)
    ).filter(
        models.ClassroomCourse.id == classroom_course_id,
        models.ClassroomCourse.classroom_id == classroom_id
    ).first()

    if not classroom_course:
        return None, 0

    # 只能查看已发布课程的成绩
    if classroom_course.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED:
        return None, 0

    # 基础查询：获取所有学生的进度记录
    query = db.query(models.StudentCourseProgress).options(
        joinedload(models.StudentCourseProgress.student),
        joinedload(models.StudentCourseProgress.graded_by_teacher)
    ).filter(
        models.StudentCourseProgress.classroom_course_id == classroom_course_id
    )
    
    # 关键词搜索（学生姓名或学号）
    if keyword:
        query = query.join(models.User, models.StudentCourseProgress.student_id == models.User.id).filter(
            or_(
                models.User.full_name.ilike(f"%{keyword}%"),
                models.User.username.ilike(f"%{keyword}%")
            )
        )
    
    # 状态筛选
    if status:
        if classroom_course.course.course_type == models.CourseTypeEnum.PRACTICE:
            # 实践课程状态筛选
            if status == "not_started":
                query = query.filter(models.StudentCourseProgress.student_status == models.CourseInClassroomStatusStudentEnum.NOT_STARTED)
            elif status == "not_completed":
                query = query.filter(models.StudentCourseProgress.student_status == models.CourseInClassroomStatusStudentEnum.LEARNING)
            elif status == "completed_on_time":
                query = query.filter(models.StudentCourseProgress.student_status == models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME)
            elif status == "completed_late":
                query = query.filter(models.StudentCourseProgress.student_status == models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE)
        elif classroom_course.course.course_type == models.CourseTypeEnum.TRAINING:
            # 实训课程状态筛选
            if status == "not_started":
                query = query.filter(models.StudentCourseProgress.training_submission_status == models.SubmissionStatusEnum.NOT_STARTED)
            elif status == "not_submitted":
                query = query.filter(models.StudentCourseProgress.training_submission_status == models.SubmissionStatusEnum.IN_PROGRESS)
            elif status == "submitted":
                query = query.filter(models.StudentCourseProgress.training_submission_status == models.SubmissionStatusEnum.SUBMITTED)
            elif status == "late_submitted":
                query = query.filter(models.StudentCourseProgress.training_submission_status == models.SubmissionStatusEnum.LATE_SUBMISSION)
    
    # 获取总数 (注: total 含没 SCP 行学生时会在下方修正)
    total = query.count()

    # 分页查询
    progress_records = query.order_by(
        models.StudentCourseProgress.student_status,
        models.StudentCourseProgress.final_calculated_score.desc()
    ).offset(skip).limit(limit).all()

    # P1-W2-1 真修: PRACTICE 课程拉 TER + 该 classroom 全学生, 融合 auto 数据
    is_practice = classroom_course.course.course_type == models.CourseTypeEnum.PRACTICE
    ter_by_student: dict = {}            # {student_id: [TER rows]}
    practice_tasks: list = []
    practice_total_coin: int = 0
    classroom_student_ids: list = []     # 该 classroom 所有学生 id
    student_user_by_id: dict = {}         # {sid: User}
    if is_practice and classroom_course.practice_id:
        practice_tasks = db.query(models.Task.id, models.Task.coin).filter(
            models.Task.practice_id == classroom_course.practice_id,
            models.Task.deleted_at.is_(None),
        ).all()
        practice_total_coin = sum((t.coin or 0) for t in practice_tasks)
        task_ids = [t.id for t in practice_tasks]

        students_q = db.query(models.ClassroomStudent.student_id, models.User).join(
            models.User, models.User.id == models.ClassroomStudent.student_id
        ).filter(models.ClassroomStudent.classroom_id == classroom_id).all()
        for sid, user in students_q:
            classroom_student_ids.append(sid)
            student_user_by_id[sid] = user

        if classroom_student_ids and task_ids:
            ter_rows = db.query(models.TaskEvaluationResult).filter(
                models.TaskEvaluationResult.user_id.in_(classroom_student_ids),
                models.TaskEvaluationResult.task_id.in_(task_ids),
            ).distinct(
                models.TaskEvaluationResult.user_id,
                models.TaskEvaluationResult.task_id,
            ).order_by(
                models.TaskEvaluationResult.user_id,
                models.TaskEvaluationResult.task_id,
                models.TaskEvaluationResult.created_at.desc(),
            ).all()
            for ter in ter_rows:
                ter_by_student.setdefault(ter.user_id, []).append(ter)

    def _auto_metrics(sid):
        """汇总学生 sid 的 auto 评测指标."""
        ters = ter_by_student.get(sid, [])
        completed = sum(1 for t in ters if t.status == 'pass')
        score_sum = sum((t.score or 0) for t in ters if t.status == 'pass')
        score_pct = round(score_sum / practice_total_coin * 100, 1) if practice_total_coin else None
        last_at = max((t.created_at for t in ters), default=None)
        return completed, score_pct, last_at

    # 构建响应数据
    grade_list = []
    sids_in_scp = {p.student_id for p in progress_records}
    for progress in progress_records:
        student = progress.student
        
        # 根据课程类型构建不同的成绩信息
        if classroom_course.course.course_type == models.CourseTypeEnum.PRACTICE:
            # 实践课程成绩 (Phase C: 融合 SCP manual + TER auto)
            assignment_status, assignment_status_cn = _get_practice_status_display(progress.student_status)

            # 总关卡数 (来自 practice 关联的 tasks, 排除已删除)
            total_tasks_n = len(practice_tasks)

            # auto 数据补充 (SCP 没记完成数时用 auto)
            auto_completed, auto_score_pct, auto_last_at = _auto_metrics(student.id)
            completed_tasks_v = progress.completed_task_count if progress.completed_task_count else auto_completed
            submission_time_v = progress.last_submission_at or auto_last_at
            task_score_v = progress.overall_score if progress.overall_score is not None else auto_score_pct
            current_score_v = (
                progress.final_calculated_score if progress.final_calculated_score is not None
                else (auto_score_pct if auto_completed > 0 else None)
            )

            # 派生 status (优先 SCP graded, 其次 auto)
            if progress.graded_at:
                derived_status = "GRADED"
            elif total_tasks_n > 0 and auto_completed == total_tasks_n:
                derived_status = "AUTO_COMPLETED"
            elif auto_completed > 0:
                derived_status = "PARTIAL"
            else:
                derived_status = "NOT_STARTED"

            grade_data = {
                "id": progress.id,
                "classroom_course_id": classroom_course_id,
                "student_id": student.id,
                "student_name": student.full_name or student.username,
                "student_number": student.username,
                "avatar_url": None,
                "assignment_status": assignment_status,
                "assignment_status_cn": assignment_status_cn,
                "submission_time": submission_time_v,
                "total_duration": progress.total_time_spent_seconds,
                "completed_tasks": completed_tasks_v,
                "total_tasks": total_tasks_n,
                "task_score": task_score_v,
                "penalty_score": progress.teacher_penalties,
                "current_score": current_score_v,
                "grading_status": None,
                "teacher_feedback": progress.teacher_feedback,
                "is_excellent": progress.is_excellent_work,
                "graded_at": progress.graded_at,
                "graded_by_teacher_name": progress.graded_by_teacher.full_name if progress.graded_by_teacher else None,
                # 新增 auto 字段 (frontend 可选用)
                "auto_completed_tasks": auto_completed,
                "auto_score": auto_score_pct,
                "last_evaluation_at": auto_last_at,
                "derived_status": derived_status,
            }
        else:
            # 实训课程成绩
            assignment_status, assignment_status_cn = _get_training_status_display(progress.training_submission_status)
            grading_status = "已点评" if progress.graded_at else "未点评"
            
            grade_data = {
                "id": progress.id,
                "classroom_course_id": classroom_course_id,
                "student_id": student.id,
                "student_name": student.full_name or student.username,
                "student_number": student.username,
                "avatar_url": None,
                "assignment_status": assignment_status,
                "assignment_status_cn": assignment_status_cn,
                "submission_time": progress.last_submission_at,
                "total_duration": None,
                "completed_tasks": None,
                "total_tasks": None,
                "task_score": None,
                "penalty_score": progress.teacher_penalties,
                "current_score": progress.final_calculated_score,
                "grading_status": grading_status,
                "teacher_feedback": progress.teacher_feedback,
                "is_excellent": progress.is_excellent_work,
                "graded_at": progress.graded_at,
                "graded_by_teacher_name": progress.graded_by_teacher.full_name if progress.graded_by_teacher else None
            }
        
        grade_list.append(grade_data)

    # P1-W2-1 真修: PRACTICE 课程追加"无 SCP 行但有 auto 评测"的学生
    # 这些学生通关 fc 但教师从未补打分, SCP 表无行 → 老逻辑漏掉
    if is_practice and classroom_student_ids:
        total_tasks_n = len(practice_tasks)
        for sid in classroom_student_ids:
            if sid in sids_in_scp:
                continue
            user = student_user_by_id.get(sid)
            if not user:
                continue
            auto_completed, auto_score_pct, auto_last_at = _auto_metrics(sid)
            # 派生 status (无 SCP 即无 manual 评分)
            if total_tasks_n > 0 and auto_completed == total_tasks_n:
                derived_status = "AUTO_COMPLETED"
                assignment_status_v, assignment_status_cn_v = "completed_on_time", "按时通关"
            elif auto_completed > 0:
                derived_status = "PARTIAL"
                assignment_status_v, assignment_status_cn_v = "not_completed", "未通关"
            else:
                derived_status = "NOT_STARTED"
                assignment_status_v, assignment_status_cn_v = "not_started", "未开始"

            grade_list.append({
                "id": None,  # 没 SCP 行, frontend 区分
                "classroom_course_id": classroom_course_id,
                "student_id": sid,
                "student_name": user.full_name or user.username,
                "student_number": user.username,
                "avatar_url": None,
                "assignment_status": assignment_status_v,
                "assignment_status_cn": assignment_status_cn_v,
                "submission_time": auto_last_at,
                "total_duration": None,
                "completed_tasks": auto_completed,
                "total_tasks": total_tasks_n,
                "task_score": auto_score_pct,
                "penalty_score": 0,
                "current_score": auto_score_pct if auto_completed > 0 else None,
                "grading_status": None,
                "teacher_feedback": None,
                "is_excellent": False,
                "graded_at": None,
                "graded_by_teacher_name": None,
                "auto_completed_tasks": auto_completed,
                "auto_score": auto_score_pct,
                "last_evaluation_at": auto_last_at,
                "derived_status": derived_status,
            })

        # status filter 应用到融合后的全列表 (auto-only 学生也参与过滤)
        if status:
            def _match(g):
                if status == "not_started":
                    return g["assignment_status"] == "not_started"
                if status == "not_completed":
                    return g["assignment_status"] == "not_completed"
                if status == "completed_on_time":
                    return g["assignment_status"] == "completed_on_time"
                if status == "completed_late":
                    return g["assignment_status"] == "completed_late"
                return True
            grade_list = [g for g in grade_list if _match(g)]

        # total 修正为融合后行数 (auto-only 学生也算)
        total = len(grade_list)

    return grade_list, total

def _get_practice_status_display(student_status):
    """获取实践课程状态显示"""
    status_map = {
        models.CourseInClassroomStatusStudentEnum.NOT_STARTED: ("not_started", "未开始"),
        models.CourseInClassroomStatusStudentEnum.LEARNING: ("not_completed", "未通关"),
        models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME: ("completed_on_time", "按时通关"),
        models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE: ("completed_late", "补交通关"),
    }
    return status_map.get(student_status, ("unknown", "未知"))

def _get_training_status_display(submission_status):
    """获取实训课程状态显示"""
    status_map = {
        models.SubmissionStatusEnum.NOT_STARTED: ("not_started", "未开始"),
        models.SubmissionStatusEnum.IN_PROGRESS: ("not_submitted", "未提交"),
        models.SubmissionStatusEnum.SUBMITTED: ("submitted", "已提交"),
        models.SubmissionStatusEnum.LATE_SUBMISSION: ("late_submitted", "已补交"),
        models.SubmissionStatusEnum.GRADED: ("graded", "已评分"),
        models.SubmissionStatusEnum.PASSED: ("passed", "通过"),
        models.SubmissionStatusEnum.FAILED: ("failed", "失败"),
    }
    return status_map.get(submission_status, ("unknown", "未知"))

def get_course_grade_statistics(db: Session, classroom_course_id: int, teacher_id: int):
    """获取课程成绩统计信息"""
    # 获取课程信息
    classroom_course = db.query(models.ClassroomCourse).options(
        joinedload(models.ClassroomCourse.course),
        joinedload(models.ClassroomCourse.classroom)
    ).filter(
        models.ClassroomCourse.id == classroom_course_id
    ).first()
    
    if not classroom_course:
        return None
    
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_course.classroom_id, teacher_id):
        return None
    
    # 获取所有学生进度
    progress_records = db.query(models.StudentCourseProgress).filter(
        models.StudentCourseProgress.classroom_course_id == classroom_course_id
    ).all()
    
    total_students = len(progress_records)
    if total_students == 0:
        return {
            "course_info": {
                "id": classroom_course.course_id,
                "title": classroom_course.course.title,
                "course_type": classroom_course.course.course_type.value
            },
            "grade_distribution": {},
            "completion_rate": 0.0,
            "average_score": 0.0,
            "excellent_count": 0
        }
    
    # 统计成绩分布
    grade_ranges = {"0-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0}
    total_score = 0
    completed_count = 0
    excellent_count = 0
    
    for progress in progress_records:
        score = progress.final_calculated_score
        total_score += score
        
        if progress.is_excellent_work:
            excellent_count += 1
        
        # 判断是否完成
        if classroom_course.course.course_type == models.CourseTypeEnum.PRACTICE:
            if progress.student_status in [
                models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME,
                models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
            ]:
                completed_count += 1
        else:
            if progress.training_submission_status in [
                models.SubmissionStatusEnum.SUBMITTED,
                models.SubmissionStatusEnum.LATE_SUBMISSION
            ]:
                completed_count += 1
        
        # 成绩分布
        if score < 60:
            grade_ranges["0-59"] += 1
        elif score < 70:
            grade_ranges["60-69"] += 1
        elif score < 80:
            grade_ranges["70-79"] += 1
        elif score < 90:
            grade_ranges["80-89"] += 1
        else:
            grade_ranges["90-100"] += 1
    
    completion_rate = (completed_count / total_students) * 100
    average_score = total_score / total_students
    
    return {
        "course_info": {
            "id": classroom_course.course_id,
            "title": classroom_course.course.title,
            "course_type": classroom_course.course.course_type.value
        },
        "grade_distribution": grade_ranges,
        "completion_rate": round(completion_rate, 1),
        "average_score": round(average_score, 1),
        "excellent_count": excellent_count
    }

def update_student_penalty(
    db: Session,
    progress_id: int,
    teacher_id: int,
    penalty_score: int,
    reason: Optional[str] = None
):
    """更新学生奖惩扣分"""
    # 获取进度记录
    progress = db.query(models.StudentCourseProgress).options(
        joinedload(models.StudentCourseProgress.classroom_course)
    ).filter(
        models.StudentCourseProgress.id == progress_id
    ).first()
    
    if not progress:
        return None
    
    # 检查权限
    if not check_classroom_teacher_permission(db, progress.classroom_course.classroom_id, teacher_id):
        return None
    
    # 更新扣分
    progress.teacher_penalties = penalty_score
    progress.final_calculated_score = progress.overall_score - penalty_score
    
    # 记录操作日志（可以扩展日志表）
    # TODO: 添加操作日志记录
    
    db.commit()
    db.refresh(progress)
    
    return progress

def batch_update_student_penalty(
    db: Session,
    classroom_course_id: int,
    teacher_id: int,
    student_ids: List[int],
    penalty_score: int,
    reason: Optional[str] = None
):
    """批量更新学生奖惩扣分"""
    # 获取课程信息
    classroom_course = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.id == classroom_course_id
    ).first()
    
    if not classroom_course:
        return []
    
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_course.classroom_id, teacher_id):
        return []
    
    # 批量更新
    updated_records = []
    for student_id in student_ids:
        progress = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id == classroom_course_id,
            models.StudentCourseProgress.student_id == student_id
        ).first()
        
        if progress:
            progress.teacher_penalties = penalty_score
            progress.final_calculated_score = progress.overall_score - penalty_score
            updated_records.append(progress)
    
    db.commit()
    
    # 刷新所有记录
    for progress in updated_records:
        db.refresh(progress)
    
    return updated_records

def get_training_assignments(
    db: Session,
    classroom_course_id: int,
    teacher_id: int,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取实训作业列表"""
    # 获取课程信息
    classroom_course = db.query(models.ClassroomCourse).options(
        joinedload(models.ClassroomCourse.course),
        joinedload(models.ClassroomCourse.classroom)
    ).filter(
        models.ClassroomCourse.id == classroom_course_id
    ).first()
    
    if not classroom_course:
        return None, 0
    
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_course.classroom_id, teacher_id):
        return None, 0
    
    # 只能查看实训课程
    if classroom_course.course.course_type != models.CourseTypeEnum.TRAINING:
        return None, 0
    
    # 基础查询
    query = db.query(models.StudentCourseProgress).options(
        joinedload(models.StudentCourseProgress.student),
        joinedload(models.StudentCourseProgress.graded_by_teacher)
    ).filter(
        models.StudentCourseProgress.classroom_course_id == classroom_course_id
    )
    
    # 关键词搜索
    if keyword:
        query = query.join(models.User, models.StudentCourseProgress.student_id == models.User.id).filter(
            or_(
                models.User.full_name.ilike(f"%{keyword}%"),
                models.User.username.ilike(f"%{keyword}%")
            )
        )
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    progress_records = query.order_by(
        models.StudentCourseProgress.training_submission_status,
        models.StudentCourseProgress.last_submission_at.desc()
    ).offset(skip).limit(limit).all()
    
    # 构建响应数据
    assignment_list = []
    for progress in progress_records:
        student = progress.student
        
        # 解析作业文件
        design_files = []
        experiment_reports = []
        
        if progress.training_assignment_files:
            try:
                import json
                files_data = json.loads(progress.training_assignment_files)
                
                for file_info in files_data.get("design_files", []):
                    design_files.append({
                        "file_name": file_info.get("file_name", ""),
                        "file_url": file_info.get("file_url", ""),
                        "file_type": "design_file",
                        "file_size": file_info.get("file_size"),
                        "upload_time": file_info.get("upload_time")
                    })
                
                for file_info in files_data.get("experiment_reports", []):
                    experiment_reports.append({
                        "file_name": file_info.get("file_name", ""),
                        "file_url": file_info.get("file_url", ""),
                        "file_type": "experiment_report",
                        "file_size": file_info.get("file_size"),
                        "upload_time": file_info.get("upload_time")
                    })
            except:
                pass
        
        assignment_data = {
            "student_id": student.id,
            "student_name": student.full_name or student.username,
            "student_number": student.username,
            "avatar_url": None,
            "submission_status": progress.training_submission_status,
            "submission_time": progress.last_submission_at,
            "design_files": design_files,
            "experiment_reports": experiment_reports,
            "grading_status": models.GradingStatusEnum.GRADED if progress.graded_at else models.GradingStatusEnum.NOT_GRADED,
            "score": progress.final_calculated_score if progress.graded_at else None,
            "teacher_feedback": progress.teacher_feedback,
            "is_excellent": progress.is_excellent_work,
            "graded_at": progress.graded_at,
            "graded_by_teacher_name": progress.graded_by_teacher.full_name if progress.graded_by_teacher else None
        }
        
        assignment_list.append(assignment_data)
    
    return assignment_list, total

def grade_training_assignment(
    db: Session,
    classroom_course_id: int,
    student_id: int,
    teacher_id: int,
    score: int,
    feedback: Optional[str] = None,
    is_excellent: bool = False
):
    """实训作业点评"""
    # 获取学生进度记录
    progress = db.query(models.StudentCourseProgress).options(
        joinedload(models.StudentCourseProgress.classroom_course)
    ).filter(
        models.StudentCourseProgress.classroom_course_id == classroom_course_id,
        models.StudentCourseProgress.student_id == student_id
    ).first()
    
    if not progress:
        return None
    
    # 检查权限
    if not check_classroom_teacher_permission(db, progress.classroom_course.classroom_id, teacher_id):
        return None
    
    # 只能对已提交或已补交的作业进行点评
    if progress.training_submission_status not in [
        models.SubmissionStatusEnum.SUBMITTED,
        models.SubmissionStatusEnum.LATE_SUBMISSION
    ]:
        return None
    
    # 更新点评信息
    progress.overall_score = score
    progress.final_calculated_score = score - progress.teacher_penalties
    progress.teacher_feedback = feedback
    progress.is_excellent_work = is_excellent
    progress.graded_by_teacher_id = teacher_id
    progress.graded_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(progress)
    
    return progress

def set_excellent_work(
    db: Session,
    progress_id: int,
    teacher_id: int,
    is_excellent: bool = True
):
    """设置优秀作业"""
    # 获取进度记录
    progress = db.query(models.StudentCourseProgress).options(
        joinedload(models.StudentCourseProgress.classroom_course)
    ).filter(
        models.StudentCourseProgress.id == progress_id
    ).first()
    
    if not progress:
        return None
    
    # 检查权限
    if not check_classroom_teacher_permission(db, progress.classroom_course.classroom_id, teacher_id):
        return None
    
    # 只有已点评的作业才能设置为优秀作业
    if not progress.graded_at:
        return None
    
    progress.is_excellent_work = is_excellent
    db.commit()
    db.refresh(progress)
    
    return progress

def submit_training_assignment(
    db: Session,
    classroom_course_id: int,
    student_id: int,
    design_files: List[dict],
    experiment_reports: List[dict]
):
    """学生提交实训作业"""
    # 获取或创建学生进度记录
    progress = db.query(models.StudentCourseProgress).filter(
        models.StudentCourseProgress.classroom_course_id == classroom_course_id,
        models.StudentCourseProgress.student_id == student_id
    ).first()
    
    if not progress:
        # 创建新的进度记录
        progress = models.StudentCourseProgress(
            classroom_course_id=classroom_course_id,
            student_id=student_id,
            training_submission_status=models.SubmissionStatusEnum.NOT_STARTED
        )
        db.add(progress)
    
    # 获取课程信息以判断是否超期
    classroom_course = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.id == classroom_course_id
    ).first()
    
    current_time = datetime.now(timezone.utc)
    is_late = False
    
    if classroom_course and classroom_course.deadline_at:
        is_late = current_time > classroom_course.deadline_at
    
    # 构建文件数据
    import json
    files_data = {
        "design_files": design_files,
        "experiment_reports": experiment_reports
    }
    
    # 更新提交信息
    progress.training_assignment_files = json.dumps(files_data)
    progress.training_submission_status = models.SubmissionStatusEnum.LATE_SUBMISSION if is_late else models.SubmissionStatusEnum.SUBMITTED
    progress.student_status = (
        models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
        if is_late
        else models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME
    )
    progress.last_submission_at = current_time
    
    # 如果是首次访问，记录首次访问时间
    if not progress.first_access_at:
        progress.first_access_at = current_time
    
    db.commit()
    db.refresh(progress)
    
    return progress

# ==================== 考试阅卷相关CRUD函数 ====================

def get_exam_unmarked_students(db: Session, exam_id: int, teacher_id: int):
    """获取考试的待阅卷学生列表"""
    # 检查考试是否存在以及教师权限
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam:
        return None
    
    # 检查教师权限
    if not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None
    
    # 获取所有学生的答题记录
    attempts = db.query(models.StudentExamAttempt).filter(
        models.StudentExamAttempt.classroom_exam_id == exam_id,
        models.StudentExamAttempt.attempt_submission_time.isnot(None)  # 已提交
    ).join(
        models.User, models.StudentExamAttempt.student_id == models.User.id
    ).all()
    
    unmarked_students = []
    total_students = len(attempts)
    unmarked_count = 0
    
    for attempt in attempts:
        status = "graded" if attempt.is_graded else "submitted"
        if not attempt.is_graded:
            unmarked_count += 1
        
        student_item = {
            "attempt_id": attempt.id,
            "student_id": attempt.student_id,
            "student_name": attempt.student.full_name or attempt.student.username,
            "student_number": attempt.student.username,
            "submission_time": attempt.attempt_submission_time,
            "duration_seconds": attempt.actual_duration_seconds,
            "status": status
        }
        unmarked_students.append(student_item)
    
    return {
        "exam_id": exam_id,
        "exam_title": exam.title,
        "total_students": total_students,
        "unmarked_count": unmarked_count,
        "students": unmarked_students
    }

def get_student_exam_paper(db: Session, exam_id: int, student_id: int, teacher_id: int):
    """获取学生试卷详情（用于阅卷）"""
    # 检查考试是否存在以及教师权限
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam:
        return None
    
    # 检查教师权限
    if not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None
    
    # 获取学生答题记录
    attempt = db.query(models.StudentExamAttempt).filter(
        models.StudentExamAttempt.classroom_exam_id == exam_id,
        models.StudentExamAttempt.student_id == student_id
    ).first()
    
    if not attempt:
        return None
    
    # 获取学生信息
    student = db.query(models.User).filter(models.User.id == student_id).first()
    if not student:
        return None
    
    # 获取试卷题目
    paper_questions = db.query(models.TestPaperQuestion).filter(
        models.TestPaperQuestion.test_paper_id == exam.test_paper_id
    ).join(
        models.Question, models.TestPaperQuestion.question_id == models.Question.id
    ).order_by(models.TestPaperQuestion.order_in_paper).all()
    
    # 获取学生答案
    student_answers = db.query(models.StudentExamAnswer).filter(
        models.StudentExamAnswer.student_exam_attempt_id == attempt.id
    ).all()

    # 构建答案字典 (统一使用整数键，解决类型不匹配问题)
    answers_dict = {int(answer.question_id): answer for answer in student_answers}
    
    # 构建题目列表
    questions = []
    answers = []
    
    for pq in paper_questions:
        question = pq.question
        
        # 解析选项（如果是选择题）
        options = []
        if question.question_type in ["SINGLE_CHOICE", "MULTIPLE_CHOICE"]:
            try:
                import json
                options_data = json.loads(question.options or "[]")
                options = [{"key": opt.get("key", ""), "content": opt.get("content", "")} 
                          for opt in options_data]
            except:
                options = []
        
        question_data = {
            "id": question.id,
            "content": question.content,
            "question_type": question.question_type.value,
            "options": options,
            "score": pq.score_for_question,
            "order_in_paper": pq.order_in_paper,
            "section_title": pq.section_title
        }
        questions.append(question_data)
        
        # 学生答案 - 使用整数ID查找 (question.id可能是字符串)
        q_id = int(question.id) if isinstance(question.id, str) else question.id
        answer = answers_dict.get(q_id)
        answer_data = {
            "question_id": question.id,
            "answer_data": answer.answer_data if answer else None,
            "score_awarded": answer.score_awarded if answer else None,
            "is_correct": answer.is_correct if answer else None,
            "teacher_comments": answer.teacher_comments if answer else None
        }
        answers.append(answer_data)
    
    return {
        "exam_id": exam_id,
        "exam_title": exam.title,
        "student_id": student_id,
        "student_name": student.full_name or student.username,
        "student_number": student.username,
        "attempt_id": attempt.id,
        "exam_start_time": exam.exam_start_time,
        "exam_end_time": exam.exam_end_time,
        "duration_minutes": exam.duration_minutes,
        "attempt_start_time": attempt.attempt_start_time,
        "attempt_submission_time": attempt.attempt_submission_time,
        "actual_duration_seconds": attempt.actual_duration_seconds,
        "questions": questions,
        "answers": answers,
        "total_score_achieved": attempt.total_score_achieved,
        "is_graded": attempt.is_graded,
        "teacher_overall_comments": attempt.teacher_overall_comments
    }

def submit_exam_marks(db: Session, exam_id: int, student_id: int, teacher_id: int, marks_data: dict):
    """提交考试评分"""
    # 检查考试是否存在以及教师权限
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam:
        return None
    
    # 检查教师权限
    if not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None
    
    # 获取学生答题记录
    attempt = db.query(models.StudentExamAttempt).filter(
        models.StudentExamAttempt.classroom_exam_id == exam_id,
        models.StudentExamAttempt.student_id == student_id
    ).first()
    
    if not attempt:
        return None
    
    # 如果已经评分，不允许重复评分（除非是管理员）
    if attempt.is_graded:
        return {"error": "该试卷已经评分，不能重复评分"}
    
    # 获取试卷的所有主观题
    subjective_questions = db.query(models.TestPaperQuestion).filter(
        models.TestPaperQuestion.test_paper_id == exam.test_paper_id
    ).join(
        models.Question, models.TestPaperQuestion.question_id == models.Question.id
    ).filter(
        models.Question.question_type == "SHORT_ANSWER"
    ).all()
    
    # 验证是否所有主观题都已评分
    marks = marks_data.get("marks", [])
    marks_dict = {mark.get("question_id"): mark for mark in marks}
    
    missing_subjective_questions = []
    for pq in subjective_questions:
        question_id = pq.question_id
        if question_id not in marks_dict:
            missing_subjective_questions.append({
                "question_id": question_id,
                "question_content": pq.question.content[:50] + "..." if len(pq.question.content) > 50 else pq.question.content
            })
    
    if missing_subjective_questions:
        return {
            "error": "存在未评分的主观题，请完成所有主观题的评分后再提交",
            "missing_questions": missing_subjective_questions
        }
    
    try:
        total_score = 0
        
        # 更新每道题的评分
        for mark in marks:
            question_id = mark.get("question_id")
            score = mark.get("score", 0)
            comment = mark.get("comment", "")
            
            # 验证分数不能超过题目满分
            question_paper = db.query(models.TestPaperQuestion).filter(
                models.TestPaperQuestion.test_paper_id == exam.test_paper_id,
                models.TestPaperQuestion.question_id == question_id
            ).first()
            
            if question_paper and score > question_paper.score_for_question:
                return {
                    "error": f"题目 {question_id} 的评分 ({score}) 不能超过满分 ({question_paper.score_for_question})"
                }
            
            # 查找或创建答案记录
            answer = db.query(models.StudentExamAnswer).filter(
                models.StudentExamAnswer.student_exam_attempt_id == attempt.id,
                models.StudentExamAnswer.question_id == question_id
            ).first()
            
            if answer:
                answer.score_awarded = score
                answer.teacher_comments = comment
                # 对于主观题，根据得分判断是否正确
                if score > 0:
                    answer.is_correct = True
                else:
                    answer.is_correct = False
            else:
                # 创建新的答案记录
                answer = models.StudentExamAnswer(
                    student_exam_attempt_id=attempt.id,
                    question_id=question_id,
                    score_awarded=score,
                    teacher_comments=comment,
                    is_correct=score > 0
                )
                db.add(answer)
            
            total_score += score
        
        # 计算客观题得分（如果有的话）
        objective_answers = db.query(models.StudentExamAnswer).filter(
            models.StudentExamAnswer.student_exam_attempt_id == attempt.id
        ).join(
            models.Question, models.StudentExamAnswer.question_id == models.Question.id
        ).filter(
            models.Question.question_type.in_(["SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"])
        ).all()
        
        for obj_answer in objective_answers:
            if obj_answer.score_awarded is not None:
                total_score += obj_answer.score_awarded
        
        # 更新答题记录
        attempt.total_score_achieved = total_score
        attempt.is_graded = True
        attempt.teacher_overall_comments = marks_data.get("overall_comments", "")
        
        db.commit()
        
        return {
            "success": True,
            "total_score": total_score,
            "message": "评分提交成功",
            "graded_questions": len(marks),
            "subjective_questions_count": len(subjective_questions)
        }
        
    except Exception as e:
        db.rollback()
        return {"error": f"评分提交失败: {str(e)}"}

def get_exam_statistics(db: Session, exam_id: int, teacher_id: int):
    """获取考试统计信息"""
    # 检查考试是否存在以及教师权限
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam:
        return None
    
    # 检查教师权限
    if not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None
    
    # 获取所有答题记录
    attempts = db.query(models.StudentExamAttempt).filter(
        models.StudentExamAttempt.classroom_exam_id == exam_id
    ).all()
    
    total_students = len(attempts)
    submitted_count = len([a for a in attempts if a.attempt_submission_time])
    graded_count = len([a for a in attempts if a.is_graded])
    
    # 计算分数统计
    graded_attempts = [a for a in attempts if a.is_graded and a.total_score_achieved is not None]
    
    average_score = None
    highest_score = None
    lowest_score = None
    
    if graded_attempts:
        scores = [a.total_score_achieved for a in graded_attempts]
        average_score = sum(scores) / len(scores)
        highest_score = max(scores)
        lowest_score = min(scores)
    
    return {
        "exam_id": exam_id,
        "exam_title": exam.title,
        "total_students": total_students,
        "submitted_count": submitted_count,
        "graded_count": graded_count,
        "average_score": round(average_score, 1) if average_score else None,
        "highest_score": highest_score,
        "lowest_score": lowest_score
    }

def auto_grade_objective_questions(db: Session, exam_id: int):
    """自动评分客观题"""
    # 获取考试信息
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam:
        return False
    
    # 获取试卷的客观题
    objective_questions = db.query(models.TestPaperQuestion).filter(
        models.TestPaperQuestion.test_paper_id == exam.test_paper_id
    ).join(
        models.Question, models.TestPaperQuestion.question_id == models.Question.id
    ).filter(
        models.Question.question_type.in_(["SINGLE_CHOICE", "MULTIPLE_CHOICE"])
    ).all()
    
    # 获取所有学生答题记录
    attempts = db.query(models.StudentExamAttempt).filter(
        models.StudentExamAttempt.classroom_exam_id == exam_id,
        models.StudentExamAttempt.attempt_submission_time.isnot(None)
    ).all()
    
    try:
        import json
        
        for attempt in attempts:
            for pq in objective_questions:
                question = pq.question
                
                # 获取学生答案
                answer = db.query(models.StudentExamAnswer).filter(
                    models.StudentExamAnswer.student_exam_attempt_id == attempt.id,
                    models.StudentExamAnswer.question_id == question.id
                ).first()
                
                if not answer or not answer.answer_data:
                    continue
                
                # 解析正确答案和学生答案
                try:
                    correct_answers = json.loads(question.correct_answers or "[]")
                    student_answer = json.loads(answer.answer_data or "[]")
                    
                    # 判断答案是否正确（兼容枚举和字符串）
                    q_type = question.question_type.value if hasattr(question.question_type, 'value') else str(question.question_type)
                    is_correct = False
                    if q_type == "SINGLE_CHOICE":
                        is_correct = student_answer == correct_answers
                    elif q_type == "MULTIPLE_CHOICE":
                        # 多选题需要完全匹配
                        is_correct = set(str(a) for a in student_answer) == set(str(a) for a in correct_answers)
                    elif q_type == "TRUE_FALSE":
                        is_correct = student_answer == correct_answers

                    # 更新评分
                    answer.is_correct = is_correct
                    answer.score_awarded = pq.score_for_question if is_correct else 0

                except json.JSONDecodeError:
                    continue

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        return False

def get_courses_for_library(
    db: Session,
    course_type: Optional[str] = None,
    keyword: Optional[str] = None,
    direction: Optional[str] = None,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取课程库中的课程（用于课程选择，包括实践课程和实训课程）"""
    all_courses = []

    # 查询实践课程
    if course_type in [None, "practice"]:
        practice_query = db.query(models.Course).filter(
            models.Course.visibility.in_([
                models.CourseVisibilityEnum.PUBLIC_SELF,
                models.CourseVisibilityEnum.PUBLIC_PLATFORM
            ]),
            models.Course.course_type == models.CourseTypeEnum.PRACTICE
        )

        # 关键词搜索
        if keyword:
            practice_query = practice_query.filter(
                or_(
                    models.Course.title.ilike(f"%{keyword}%"),
                    models.Course.description.ilike(f"%{keyword}%")
                )
            )

        # 方向筛选
        if direction:
            practice_query = practice_query.filter(models.Course.direction.ilike(f"%{direction}%"))

        # 分类筛选
        if category:
            practice_query = practice_query.filter(models.Course.categories.contains(category))

        # 难度筛选
        if difficulty:
            if difficulty.upper() in ["BEGINNER", "INTERMEDIATE", "ADVANCED"]:
                practice_query = practice_query.filter(models.Course.difficulty == difficulty.upper())

        practice_courses = practice_query.order_by(models.Course.created_at.desc()).all()

        # 转换为统一的格式
        for course in practice_courses:
            all_courses.append({
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "course_type": "practice",
                "difficulty": course.difficulty,
                "direction": course.direction,
                "categories": course.categories,
                "visibility": course.visibility,
                "created_at": course.created_at,
                "practice_task_count": course.practice_task_count,
                "teaching_team_name": course.teaching_team_name
            })

    # 查询实训课程
    if course_type in [None, "training"]:
        training_query = db.query(models.Training).filter(
            models.Training.visibility == models.TrainingVisibilityEnum.PUBLIC
        )

        # 关键词搜索
        if keyword:
            training_query = training_query.filter(
                or_(
                    models.Training.title.ilike(f"%{keyword}%"),
                    models.Training.intro.ilike(f"%{keyword}%")
                )
            )

        # 行业筛选（对应方向）
        if direction:
            training_query = training_query.filter(models.Training.industry.ilike(f"%{direction}%"))

        # 难度筛选
        if difficulty:
            if difficulty.lower() in ["beginner", "intermediate", "advanced"]:
                training_query = training_query.filter(models.Training.difficulty == difficulty.lower())

        training_courses = training_query.order_by(models.Training.created_at.desc()).all()

        # 转换为统一的格式
        for training in training_courses:
            all_courses.append({
                "id": training.id,
                "title": training.title,
                "description": training.intro,
                "course_type": "training",
                "difficulty": training.difficulty,
                "direction": training.industry,
                "categories": None,  # Training没有categories字段
                "visibility": training.visibility,
                "created_at": training.created_at,
                "training_type": training.training_type,
                "course_hours": training.course_hours
            })

    # 按创建时间排序
    all_courses.sort(key=lambda x: x["created_at"], reverse=True)

    # 分页
    total = len(all_courses)
    paginated_courses = all_courses[skip:skip + limit]

    return paginated_courses, total
def get_course_filter_tags_for_selection(db: Session, course_type: Optional[str] = None):
    """获取课程选择页面的筛选标签"""
    # 基础查询
    query = db.query(models.Course).filter(
        models.Course.visibility.in_([
            models.CourseVisibilityEnum.PUBLIC_SELF,
            models.CourseVisibilityEnum.PUBLIC_PLATFORM
        ])
    )
    
    # 课程类型筛选
    if course_type:
        if course_type == "practice":
            query = query.filter(models.Course.course_type == models.CourseTypeEnum.PRACTICE)
        elif course_type == "training":
            query = query.filter(models.Course.course_type == models.CourseTypeEnum.TRAINING)
        elif course_type == "course_material":
            query = query.filter(models.Course.course_type == models.CourseTypeEnum.COURSE_MATERIAL)
    
    # 获取所有方向标签
    directions = db.query(models.Course.direction).filter(
        models.Course.direction.isnot(None),
        models.Course.direction != ""
    ).distinct().all()
    direction_list = [d[0] for d in directions if d[0]]
    
    # 获取所有分类标签
    categories_query = query.filter(models.Course.categories.isnot(None))
    all_categories = []
    for course in categories_query.all():
        if course.categories:
            all_categories.extend(course.categories)
    category_list = list(set(all_categories))
    
    # 获取所有难度级别
    difficulties = db.query(models.Course.difficulty).filter(
        models.Course.difficulty.isnot(None)
    ).distinct().all()
    difficulty_list = [d[0].value for d in difficulties if d[0]]
    
    return {
        "directions": sorted(direction_list),
        "categories": sorted(category_list),
        "difficulties": sorted(difficulty_list),
        "course_types": [
            {"value": "practice", "label": "实践课程"},
            {"value": "training", "label": "实训课程"},
            {"value": "course_material", "label": "课程教材"}
        ]
    }

# ==================== 教学资源管理相关CRUD操作 ====================

def get_classroom_resources(
    db: Session,
    classroom_id: int,
    resource_type: Optional[str] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取课堂教学资源列表"""
    query = db.query(models.ClassroomResource).filter(
        models.ClassroomResource.classroom_id == classroom_id,
        models.ClassroomResource.is_active == True
    )
    
    # 资源类型筛选
    if resource_type:
        query = query.filter(models.ClassroomResource.resource_type == resource_type)
    
    # 关键词搜索
    if keyword:
        query = query.filter(models.ClassroomResource.title.ilike(f"%{keyword}%"))
    
    # 排序
    query = query.order_by(models.ClassroomResource.created_at.desc())
    
    total = query.count()
    resources = query.offset(skip).limit(limit).all()
    
    return resources, total

def create_classroom_resource(
    db: Session,
    classroom_id: int,
    title: str,
    url: str,
    resource_type: str,
    teacher_id: int,
    file_size: Optional[int] = None
):
    """创建课堂教学资源"""
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return None
    
    # 创建资源
    resource = models.ClassroomResource(
        classroom_id=classroom_id,
        title=title,
        url=url,
        resource_type=resource_type,
        file_size=file_size,
        uploader_id=teacher_id
    )
    
    db.add(resource)
    db.commit()
    db.refresh(resource)
    
    return resource

def delete_classroom_resource(db: Session, classroom_id: int, resource_id: int, teacher_id: int):
    """删除课堂教学资源"""
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return False
    
    # 获取资源
    resource = db.query(models.ClassroomResource).filter(
        models.ClassroomResource.id == resource_id,
        models.ClassroomResource.classroom_id == classroom_id
    ).first()
    
    if not resource:
        return False
    
    # 软删除
    resource.is_active = False
    db.commit()
    
    return True

# ==================== 课堂云盘相关CRUD操作 ====================

def get_classroom_cloud_files(
    db: Session,
    classroom_id: int,
    folder_path: str = "",
    keyword: Optional[str] = None,
    file_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取课堂云盘文件列表"""
    query = db.query(models.ClassroomCloudFile).filter(
        models.ClassroomCloudFile.classroom_id == classroom_id,
        models.ClassroomCloudFile.folder_path == folder_path
    )
    
    # 文件类型筛选
    if file_type:
        query = query.filter(models.ClassroomCloudFile.file_type == file_type)
    
    # 关键词搜索
    if keyword:
        query = query.filter(models.ClassroomCloudFile.name.ilike(f"%{keyword}%"))
    
    # 排序
    query = query.order_by(models.ClassroomCloudFile.created_at.desc())
    
    total = query.count()
    files = query.offset(skip).limit(limit).all()
    
    return files, total

def upload_classroom_cloud_file(
    db: Session,
    classroom_id: int,
    file_name: str,
    file_type: str,
    file_size: int,
    folder_path: str,
    url: str,
    is_shared: bool,
    teacher_id: int
):
    """上传文件到课堂云盘"""
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return None
    
    # 创建文件记录
    cloud_file = models.ClassroomCloudFile(
        classroom_id=classroom_id,
        name=file_name,
        file_type=file_type,
        file_size=file_size,
        folder_path=folder_path,
        url=url,
        uploader_id=teacher_id,
        is_shared=is_shared
    )
    
    db.add(cloud_file)
    db.commit()
    db.refresh(cloud_file)
    
    return cloud_file

# ==================== 学情分析相关CRUD操作 ====================

def get_classroom_analytics_overview(db: Session, classroom_id: int):
    """获取学情分析总览"""
    # 获取课堂基本信息
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id
    ).first()
    
    if not classroom:
        return None
    
    # 学生总数
    total_students = classroom.student_count
    
    # 课程统计
    total_courses = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id
    ).count()
    
    # 必修课程数量
    mandatory_courses = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.is_mandatory == True
    ).count()
    
    # 拓展课程数量
    elective_courses = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.is_mandatory == False
    ).count()
    
    # 已发布课程数量
    published_courses = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.teacher_publish_status != models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).count()
    
    # 学生完成情况统计
    completed_students = db.query(models.StudentCourseProgress).filter(
        models.StudentCourseProgress.classroom_course_id.in_(
            db.query(models.ClassroomCourse.id).filter(
                models.ClassroomCourse.classroom_id == classroom_id
            )
        ),
        models.StudentCourseProgress.student_status.in_([
            models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME,
            models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
        ])
    ).distinct(models.StudentCourseProgress.student_id).count()
    
    # 平均成绩
    avg_score = db.query(func.avg(models.StudentCourseProgress.final_calculated_score)).filter(
        models.StudentCourseProgress.classroom_course_id.in_(
            db.query(models.ClassroomCourse.id).filter(
                models.ClassroomCourse.classroom_id == classroom_id,
                models.ClassroomCourse.is_mandatory == True
            )
        ),
        models.StudentCourseProgress.final_calculated_score > 0
    ).scalar() or 0
    
    return {
        "classroom_info": {
            "id": classroom.id,
            "name": classroom.name,
            "total_students": total_students,
            "start_date": classroom.start_date,
            "end_date": classroom.end_date
        },
        "course_stats": {
            "total_courses": total_courses,
            "mandatory_courses": mandatory_courses,
            "elective_courses": elective_courses,
            "published_courses": published_courses
        },
        "student_stats": {
            "total_students": total_students,
            "completed_students": completed_students,
            "completion_rate": round(completed_students / total_students * 100, 2) if total_students > 0 else 0,
            "average_score": round(avg_score, 2)
        }
    }

def get_mandatory_courses_analytics(db: Session, classroom_id: int):
    """获取必修课程统计"""
    # 获取必修课程列表及其完成情况
    mandatory_courses = db.query(models.ClassroomCourse).options(
        joinedload(models.ClassroomCourse.course)
    ).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.is_mandatory == True,
        models.ClassroomCourse.teacher_publish_status != models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).all()
    
    course_analytics = []
    for course in mandatory_courses:
        # 统计该课程的学生完成情况
        total_students = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id == course.id
        ).count()
        
        completed_students = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id == course.id,
            models.StudentCourseProgress.student_status.in_([
                models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME,
                models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
            ])
        ).count()
        
        avg_score = db.query(func.avg(models.StudentCourseProgress.final_calculated_score)).filter(
            models.StudentCourseProgress.classroom_course_id == course.id,
            models.StudentCourseProgress.final_calculated_score > 0
        ).scalar() or 0
        
        avg_time = db.query(func.avg(models.StudentCourseProgress.total_time_spent_seconds)).filter(
            models.StudentCourseProgress.classroom_course_id == course.id,
            models.StudentCourseProgress.total_time_spent_seconds > 0
        ).scalar() or 0
        
        course_analytics.append({
            "course_id": course.id,
            "course_title": course.classroom_chapter_title or course.course.title,
            "course_type": course.course.course_type.value,
            "deadline": course.deadline_at,
            "total_students": total_students,
            "completed_students": completed_students,
            "completion_rate": round(completed_students / total_students * 100, 2) if total_students > 0 else 0,
            "average_score": round(avg_score, 2),
            "average_time_hours": round(avg_time / 3600, 2) if avg_time > 0 else 0
        })
    
    return {
        "course_analytics": course_analytics,
        "summary": {
            "total_mandatory_courses": len(mandatory_courses),
            "overall_completion_rate": round(
                sum(c["completion_rate"] for c in course_analytics) / len(course_analytics), 2
            ) if course_analytics else 0,
            "overall_average_score": round(
                sum(c["average_score"] for c in course_analytics) / len(course_analytics), 2
            ) if course_analytics else 0
        }
    }

def get_elective_courses_analytics(db: Session, classroom_id: int):
    """获取拓展课程统计"""
    # 获取拓展课程列表及其完成情况
    elective_courses = db.query(models.ClassroomCourse).options(
        joinedload(models.ClassroomCourse.course)
    ).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.is_mandatory == False,
        models.ClassroomCourse.teacher_publish_status != models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).all()
    
    course_analytics = []
    for course in elective_courses:
        # 统计该课程的学生参与情况
        total_students = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id == course.id
        ).count()
        
        started_students = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id == course.id,
            models.StudentCourseProgress.student_status != models.CourseInClassroomStatusStudentEnum.NOT_STARTED
        ).count()
        
        completed_students = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id == course.id,
            models.StudentCourseProgress.student_status.in_([
                models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME,
                models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
            ])
        ).count()
        
        avg_score = db.query(func.avg(models.StudentCourseProgress.final_calculated_score)).filter(
            models.StudentCourseProgress.classroom_course_id == course.id,
            models.StudentCourseProgress.final_calculated_score > 0
        ).scalar() or 0
        
        course_analytics.append({
            "course_id": course.id,
            "course_title": course.classroom_chapter_title or course.course.title,
            "course_type": course.course.course_type.value,
            "total_students": total_students,
            "started_students": started_students,
            "completed_students": completed_students,
            "participation_rate": round(started_students / total_students * 100, 2) if total_students > 0 else 0,
            "completion_rate": round(completed_students / started_students * 100, 2) if started_students > 0 else 0,
            "average_score": round(avg_score, 2)
        })
    
    return {
        "course_analytics": course_analytics,
        "summary": {
            "total_elective_courses": len(elective_courses),
            "overall_participation_rate": round(
                sum(c["participation_rate"] for c in course_analytics) / len(course_analytics), 2
            ) if course_analytics else 0,
            "overall_completion_rate": round(
                sum(c["completion_rate"] for c in course_analytics) / len(course_analytics), 2
            ) if course_analytics else 0
        }
    }

# ==================== 课程考核相关CRUD函数 ====================

def get_test_papers_for_selection(
    db: Session,
    teacher_id: int,
    keyword: Optional[str] = None,
    difficulty: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取可选择的试卷列表"""
    # 基础查询 - 获取教师创建的或共享的试卷
    query = db.query(models.TestPaper).filter(
        or_(
            models.TestPaper.creator_id == teacher_id,
            models.TestPaper.is_shared == True
        ),
        models.TestPaper.deleted_at.is_(None)
    )
    
    # 关键词搜索
    if keyword:
        query = query.filter(models.TestPaper.title.ilike(f"%{keyword}%"))
    
    # 难度筛选
    if difficulty:
        query = query.filter(models.TestPaper.difficulty == difficulty)
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    test_papers = query.order_by(models.TestPaper.created_at.desc()).offset(skip).limit(limit).all()
    
    # 构建响应数据
    paper_list = []
    for paper in test_papers:
        # 统计题目数量
        question_count = db.query(models.TestPaperQuestion).filter(
            models.TestPaperQuestion.test_paper_id == paper.id
        ).count()
        
        paper_data = {
            "id": paper.id,
            "title": paper.title,
            "description": paper.description,
            "total_score": paper.total_score,
            "estimated_duration_minutes": paper.estimated_duration_minutes,
            "difficulty": paper.difficulty.value if paper.difficulty else None,
            "question_count": question_count,
            "is_selected": False
        }
        paper_list.append(paper_data)
    
    return paper_list, total

def create_classroom_exam(
    db: Session,
    classroom_id: int,
    teacher_id: int,
    title: str,
    test_paper_id: int
):
    """创建课堂考试"""
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return None
    
    # 检查试卷是否存在
    test_paper = db.query(models.TestPaper).filter(
        models.TestPaper.id == test_paper_id,
        models.TestPaper.deleted_at.is_(None)
    ).first()
    
    if not test_paper:
        return None
    
    # 检查试卷权限（教师创建的或共享的）
    if test_paper.creator_id != teacher_id and not test_paper.is_shared:
        return None
    
    try:
        # 创建考试
        exam = models.ClassroomExam(
            classroom_id=classroom_id,
            test_paper_id=test_paper_id,
            title=title,
            exam_start_time=datetime.now(timezone.utc),  # 临时时间，发布时会更新
            exam_end_time=datetime.now(timezone.utc) + timedelta(hours=2),  # 临时时间
            duration_minutes=test_paper.estimated_duration_minutes or 90,
            pass_mark=int(test_paper.total_score * 0.6),  # 默认60%及格
            shuffle_questions=False,
            shuffle_options=False,
            status=models.ExamStatusEnum.UNPUBLISHED,
            created_by_teacher_id=teacher_id
        )
        
        db.add(exam)
        db.commit()
        db.refresh(exam)
        
        return exam
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建考试失败: {str(e)}")
        return None

def get_classroom_exams(
    db: Session,
    classroom_id: int,
    teacher_id: int,
    skip: int = 0,
    limit: int = 20
):
    """获取课堂考试列表"""
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return None, 0
    
    # 查询考试列表
    query = db.query(models.ClassroomExam).options(
        joinedload(models.ClassroomExam.test_paper)
    ).filter(
        models.ClassroomExam.classroom_id == classroom_id
    )
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    exams = query.order_by(models.ClassroomExam.created_at.desc()).offset(skip).limit(limit).all()
    
    # 构建响应数据
    exam_list = []
    stats = {
        "total_exams": total,
        "unpublished_count": 0,
        "scheduled_count": 0,
        "ongoing_count": 0,
        "completed_count": 0
    }
    
    for exam in exams:
        # 获取学生统计
        total_students = db.query(models.ClassroomStudent).filter(
            models.ClassroomStudent.classroom_id == classroom_id
        ).count()
        
        submitted_count = db.query(models.StudentExamAttempt).filter(
            models.StudentExamAttempt.classroom_exam_id == exam.id,
            models.StudentExamAttempt.attempt_submission_time.isnot(None)
        ).count()
        
        graded_count = db.query(models.StudentExamAttempt).filter(
            models.StudentExamAttempt.classroom_exam_id == exam.id,
            models.StudentExamAttempt.is_graded == True
        ).count()
        
        # 状态中文映射
        status_cn_map = {
            "UNPUBLISHED": "未发布",
            "SCHEDULED": "未开始",
            "ONGOING": "进行中",
            "GRADING": "阅卷中",
            "COMPLETED": "已完成"
        }
        
        # 权限判断
        now = datetime.now(timezone.utc)
        # 确保考试开始时间有时区信息
        exam_start_time = exam.exam_start_time
        if exam_start_time and exam_start_time.tzinfo is None:
            exam_start_time = exam_start_time.replace(tzinfo=timezone.utc)
        
        can_edit = exam.status == models.ExamStatusEnum.UNPUBLISHED or (
            exam.status == models.ExamStatusEnum.SCHEDULED and exam_start_time > now
        )
        can_delete = exam.status == models.ExamStatusEnum.UNPUBLISHED
        can_publish = exam.status == models.ExamStatusEnum.UNPUBLISHED
        
        # 判断考试是否已发布（非未发布状态即为已发布）
        is_published = exam.status != models.ExamStatusEnum.UNPUBLISHED

        exam_data = {
            "id": exam.id,
            "classroom_id": exam.classroom_id,
            "test_paper_id": exam.test_paper_id,
            "title": exam.title,
            "status": exam.status.value,
            "status_cn": status_cn_map.get(exam.status.value, exam.status.value),
            "exam_start_time": exam.exam_start_time,
            "exam_end_time": exam.exam_end_time,
            "duration_minutes": exam.duration_minutes,
            "pass_mark": exam.pass_mark,
            "shuffle_questions": exam.shuffle_questions,
            "shuffle_options": exam.shuffle_options,
            "test_paper_title": exam.test_paper.title,
            "test_paper_total_score": exam.test_paper.total_score,
            "total_students": total_students,
            "submitted_count": submitted_count,
            "graded_count": graded_count,
            "is_published": is_published,
            "can_edit": can_edit,
            "can_delete": can_delete,
            "can_publish": can_publish,
            "created_by_teacher_id": exam.created_by_teacher_id,
            "created_at": exam.created_at
        }
        
        exam_list.append(exam_data)
        
        # 统计各状态数量
        if exam.status == models.ExamStatusEnum.UNPUBLISHED:
            stats["unpublished_count"] += 1
        elif exam.status == models.ExamStatusEnum.SCHEDULED:
            stats["scheduled_count"] += 1
        elif exam.status == models.ExamStatusEnum.ONGOING:
            stats["ongoing_count"] += 1
        elif exam.status in [models.ExamStatusEnum.GRADING, models.ExamStatusEnum.COMPLETED]:
            stats["completed_count"] += 1
    
    return exam_list, total, stats

def publish_classroom_exam(
    db: Session,
    exam_id: int,
    teacher_id: int,
    exam_start_time: datetime,
    exam_end_time: datetime,
    duration_minutes: int,
    pass_mark: int,
    shuffle_questions: bool = False,
    shuffle_options: bool = False
):
    """发布考试"""
    # 获取考试
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam:
        return None
    
    # 检查权限
    if not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None
    
    # 只能发布未发布状态的考试
    if exam.status != models.ExamStatusEnum.UNPUBLISHED:
        return {"error": "只能发布未发布状态的考试"}

    # 入参为 None 时，fallback 到 exam 已存储的值（允许无参发布）
    if exam_start_time is None:
        exam_start_time = exam.exam_start_time
    if exam_end_time is None:
        exam_end_time = exam.exam_end_time
    if duration_minutes is None:
        duration_minutes = exam.duration_minutes
    if pass_mark is None:
        pass_mark = exam.pass_mark

    if exam_start_time is None or exam_end_time is None or duration_minutes is None:
        return {"error": "考试开始时间、结束时间和时长不能为空"}

    # 验证时间
    if exam_end_time <= exam_start_time:
        return {"error": "考试结束时间必须晚于开始时间"}

    time_diff_minutes = (exam_end_time - exam_start_time).total_seconds() / 60
    if time_diff_minutes < duration_minutes:
        return {"error": "考试时间区间长度不得低于考试时长"}
    
    try:
        # 更新考试信息
        exam.exam_start_time = exam_start_time
        exam.exam_end_time = exam_end_time
        exam.duration_minutes = duration_minutes
        exam.pass_mark = pass_mark
        exam.shuffle_questions = shuffle_questions
        exam.shuffle_options = shuffle_options
        exam.status = models.ExamStatusEnum.SCHEDULED
        
        db.commit()
        db.refresh(exam)
        
        return exam
        
    except Exception as e:
        db.rollback()
        logger.error(f"发布考试失败: {str(e)}")
        return {"error": f"发布考试失败: {str(e)}"}

def update_classroom_exam(
    db: Session,
    exam_id: int,
    teacher_id: int,
    **update_data
):
    """更新考试信息"""
    # 获取考试
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam:
        return None
    
    # 检查权限
    if not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None
    
    # 检查是否可以编辑
    now = datetime.now(timezone.utc)
    # 确保考试开始时间有时区信息
    exam_start_time = exam.exam_start_time
    if exam_start_time and exam_start_time.tzinfo is None:
        exam_start_time = exam_start_time.replace(tzinfo=timezone.utc)
    
    can_edit = exam.status == models.ExamStatusEnum.UNPUBLISHED or (
        exam.status == models.ExamStatusEnum.SCHEDULED and exam_start_time > now
    )
    
    if not can_edit:
        return {"error": "考试已开始或已结束，无法编辑"}
    
    try:
        # 更新字段
        for field, value in update_data.items():
            if hasattr(exam, field) and value is not None:
                setattr(exam, field, value)
        
        # 如果更新了时间相关字段，需要验证
        if 'exam_start_time' in update_data or 'exam_end_time' in update_data or 'duration_minutes' in update_data:
            if exam.exam_end_time <= exam.exam_start_time:
                return {"error": "考试结束时间必须晚于开始时间"}
            
            time_diff_minutes = (exam.exam_end_time - exam.exam_start_time).total_seconds() / 60
            if time_diff_minutes < exam.duration_minutes:
                return {"error": "考试时间区间长度不得低于考试时长"}
        
        db.commit()
        db.refresh(exam)
        
        return exam
        
    except Exception as e:
        db.rollback()
        logger.error(f"更新考试失败: {str(e)}")
        return {"error": f"更新考试失败: {str(e)}"}

def rename_classroom_exam(
    db: Session,
    exam_id: int,
    teacher_id: int,
    new_title: str
):
    """重命名考试"""
    # 获取考试
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam:
        return None
    
    # 检查权限
    if not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None
    
    # 检查是否可以编辑
    now = datetime.now(timezone.utc)
    # 确保考试开始时间有时区信息
    exam_start_time = exam.exam_start_time
    if exam_start_time and exam_start_time.tzinfo is None:
        exam_start_time = exam_start_time.replace(tzinfo=timezone.utc)
    
    can_edit = exam.status == models.ExamStatusEnum.UNPUBLISHED or (
        exam.status == models.ExamStatusEnum.SCHEDULED and exam_start_time > now
    )
    
    if not can_edit:
        return {"error": "考试已开始或已结束，无法重命名"}
    
    try:
        exam.title = new_title
        db.commit()
        db.refresh(exam)
        
        return exam
        
    except Exception as e:
        db.rollback()
        logger.error(f"重命名考试失败: {str(e)}")
        return {"error": f"重命名考试失败: {str(e)}"}

def delete_classroom_exam(
    db: Session,
    exam_id: int,
    teacher_id: int
):
    """删除考试"""
    # 获取考试
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam:
        return None
    
    # 检查权限
    if not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None
    
    # 检查考试状态：只能删除未发布或未开始的已安排考试
    # 1. 未发布状态：可以直接删除
    # 2. 已安排状态：如果考试未开始（开始时间在当前时间之后），可以删除
    if exam.status == models.ExamStatusEnum.UNPUBLISHED:
        # 未发布，可以删除
        pass
    elif exam.status == models.ExamStatusEnum.SCHEDULED:
        # 已安排，检查是否已经开始
        if exam.exam_start_time and exam.exam_start_time <= datetime.now():
            return {"error": "考试已开始，无法删除"}
    else:
        # 进行中、阅卷中、已完成状态的考试不能删除
        return {"error": "该考试无法删除，只能删除未发布或未开始的考试"}
    
    try:
        # 删除相关的学生答题记录（如果有）
        db.query(models.StudentExamAnswer).filter(
            models.StudentExamAnswer.student_exam_attempt_id.in_(
                db.query(models.StudentExamAttempt.id).filter(
                    models.StudentExamAttempt.classroom_exam_id == exam_id
                )
            )
        ).delete(synchronize_session=False)
        
        db.query(models.StudentExamAttempt).filter(
            models.StudentExamAttempt.classroom_exam_id == exam_id
        ).delete(synchronize_session=False)
        
        # 删除考试
        db.delete(exam)
        db.commit()
        
        return {"success": True, "message": "考试删除成功"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"删除考试失败: {str(e)}")
        return {"error": f"删除考试失败: {str(e)}"}

def get_classroom_exam_detail(
    db: Session,
    exam_id: int,
    teacher_id: int
):
    """获取考试详情"""
    # 获取考试
    exam = db.query(models.ClassroomExam).options(
        joinedload(models.ClassroomExam.test_paper)
    ).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam:
        return None
    
    # 检查权限
    if not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None
    
    # 获取学生答题进度
    student_attempts = db.query(models.StudentExamAttempt).options(
        joinedload(models.StudentExamAttempt.student)
    ).filter(
        models.StudentExamAttempt.classroom_exam_id == exam_id
    ).all()
    
    # 构建学生进度列表
    student_progress = []
    for attempt in student_attempts:
        progress_item = {
            "student_id": attempt.student_id,
            "student_name": attempt.student.full_name or attempt.student.username,
            "student_number": attempt.student.username,
            "attempt_start_time": attempt.attempt_start_time,
            "attempt_submission_time": attempt.attempt_submission_time,
            "actual_duration_seconds": attempt.actual_duration_seconds,
            "total_score_achieved": attempt.total_score_achieved,
            "is_graded": attempt.is_graded,
            "status": "已提交" if attempt.attempt_submission_time else "未提交"
        }
        student_progress.append(progress_item)
    
    # 成绩统计
    submitted_attempts = [a for a in student_attempts if a.attempt_submission_time]
    graded_attempts = [a for a in student_attempts if a.is_graded and a.total_score_achieved is not None]
    
    score_statistics = None
    if graded_attempts:
        scores = [a.total_score_achieved for a in graded_attempts]
        score_statistics = {
            "average_score": sum(scores) / len(scores),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "pass_count": len([s for s in scores if s >= exam.pass_mark]),
            "pass_rate": len([s for s in scores if s >= exam.pass_mark]) / len(scores) * 100
        }
    
    # 状态中文映射
    status_cn_map = {
        "UNPUBLISHED": "未发布",
        "SCHEDULED": "未开始",
        "ONGOING": "进行中",
        "GRADING": "阅卷中",
        "COMPLETED": "已完成"
    }
    
    # 权限判断
    now = datetime.now(timezone.utc)
    can_edit = exam.status == models.ExamStatusEnum.UNPUBLISHED or (
        exam.status == models.ExamStatusEnum.SCHEDULED and exam.exam_start_time > now
    )
    can_delete = exam.status == models.ExamStatusEnum.UNPUBLISHED
    can_publish = exam.status == models.ExamStatusEnum.UNPUBLISHED
    
    exam_detail = {
        "id": exam.id,
        "classroom_id": exam.classroom_id,
        "test_paper_id": exam.test_paper_id,
        "title": exam.title,
        "status": exam.status.value,
        "status_cn": status_cn_map.get(exam.status.value, exam.status.value),
        "exam_start_time": exam.exam_start_time,
        "exam_end_time": exam.exam_end_time,
        "duration_minutes": exam.duration_minutes,
        "pass_mark": exam.pass_mark,
        "shuffle_questions": exam.shuffle_questions,
        "shuffle_options": exam.shuffle_options,
        "test_paper_title": exam.test_paper.title,
        "test_paper_total_score": exam.test_paper.total_score,
        "total_students": len(student_attempts),
        "submitted_count": len(submitted_attempts),
        "graded_count": len(graded_attempts),
        "can_edit": can_edit,
        "can_delete": can_delete,
        "can_publish": can_publish,
        "created_by_teacher_id": exam.created_by_teacher_id,
        "created_at": exam.created_at,
        "test_paper": {
            "id": exam.test_paper.id,
            "title": exam.test_paper.title,
            "description": exam.test_paper.description,
            "total_score": exam.test_paper.total_score,
            "estimated_duration_minutes": exam.test_paper.estimated_duration_minutes,
            "difficulty": exam.test_paper.difficulty.value if exam.test_paper.difficulty else None
        },
        "student_progress": student_progress,
        "score_statistics": score_statistics
    }
    
    return exam_detail

def get_next_unmarked_student(db: Session, exam_id: int, current_student_id: int, teacher_id: int):
    """获取下一份待阅卷试卷的学生信息（用于批量阅卷模式）"""
    # 检查考试是否存在以及教师权限
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam:
        return None
    
    # 检查教师权限
    if not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None
    
    # 获取下一个未阅卷的学生
    next_attempt = db.query(models.StudentExamAttempt).filter(
        models.StudentExamAttempt.classroom_exam_id == exam_id,
        models.StudentExamAttempt.attempt_submission_time.isnot(None),  # 已提交
        models.StudentExamAttempt.is_graded == False,  # 未阅卷
        models.StudentExamAttempt.student_id != current_student_id  # 不是当前学生
    ).join(
        models.User, models.StudentExamAttempt.student_id == models.User.id
    ).order_by(models.StudentExamAttempt.attempt_submission_time).first()
    
    if not next_attempt:
        return None
    
    return {
        "student_id": next_attempt.student_id,
        "student_name": next_attempt.student.full_name or next_attempt.student.username,
        "student_number": next_attempt.student.username,
        "attempt_id": next_attempt.id,
        "submission_time": next_attempt.attempt_submission_time
    }

def get_exam_grading_progress(db: Session, exam_id: int, teacher_id: int):
    """获取考试阅卷进度信息"""
    # 检查考试是否存在以及教师权限
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam:
        return None
    
    # 检查教师权限
    if not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None
    
    # 获取所有答题记录
    attempts = db.query(models.StudentExamAttempt).filter(
        models.StudentExamAttempt.classroom_exam_id == exam_id
    ).all()
    
    total_students = len(attempts)
    submitted_count = len([a for a in attempts if a.attempt_submission_time])
    graded_count = len([a for a in attempts if a.is_graded])
    ungraded_count = submitted_count - graded_count
    
    # 计算主观题和客观题的评分进度
    subjective_questions = db.query(models.TestPaperQuestion).filter(
        models.TestPaperQuestion.test_paper_id == exam.test_paper_id
    ).join(
        models.Question, models.TestPaperQuestion.question_id == models.Question.id
    ).filter(
        models.Question.question_type == "SHORT_ANSWER"
    ).count()
    
    objective_questions = db.query(models.TestPaperQuestion).filter(
        models.TestPaperQuestion.test_paper_id == exam.test_paper_id
    ).join(
        models.Question, models.TestPaperQuestion.question_id == models.Question.id
    ).filter(
        models.Question.question_type.in_(["SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"])
    ).count()
    
    return {
        "exam_id": exam_id,
        "exam_title": exam.title,
        "total_students": total_students,
        "submitted_count": submitted_count,
        "graded_count": graded_count,
        "ungraded_count": ungraded_count,
        "grading_progress_rate": round(graded_count / submitted_count * 100, 1) if submitted_count > 0 else 0,
        "subjective_questions_count": subjective_questions,
        "objective_questions_count": objective_questions,
        "total_questions": subjective_questions + objective_questions
    }

def batch_auto_grade_objective_questions(db: Session, exam_id: int):
    """批量自动评分所有客观题"""
    # 获取考试信息
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam:
        return {"success": False, "message": "考试不存在"}
    
    # 获取试卷的客观题
    objective_questions = db.query(models.TestPaperQuestion).filter(
        models.TestPaperQuestion.test_paper_id == exam.test_paper_id
    ).join(
        models.Question, models.TestPaperQuestion.question_id == models.Question.id
    ).filter(
        models.Question.question_type.in_(["SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"])
    ).all()
    
    # 获取所有学生答题记录
    attempts = db.query(models.StudentExamAttempt).filter(
        models.StudentExamAttempt.classroom_exam_id == exam_id,
        models.StudentExamAttempt.attempt_submission_time.isnot(None)
    ).all()
    
    try:
        import json
        graded_count = 0
        total_attempts = len(attempts)
        
        for attempt in attempts:
            attempt_graded = False
            for pq in objective_questions:
                question = pq.question
                
                # 获取学生答案
                answer = db.query(models.StudentExamAnswer).filter(
                    models.StudentExamAnswer.student_exam_attempt_id == attempt.id,
                    models.StudentExamAnswer.question_id == question.id
                ).first()
                
                if not answer or not answer.answer_data:
                    continue
                
                # 解析正确答案和学生答案
                try:
                    correct_answers = json.loads(question.correct_answers or "[]")
                    student_answer = json.loads(answer.answer_data or "[]")
                    
                    # 判断答案是否正确（兼容枚举和字符串）
                    q_type = question.question_type.value if hasattr(question.question_type, 'value') else str(question.question_type)
                    is_correct = False
                    if q_type == "SINGLE_CHOICE":
                        is_correct = student_answer == correct_answers
                    elif q_type == "MULTIPLE_CHOICE":
                        # 多选题需要完全匹配
                        is_correct = set(str(a) for a in student_answer) == set(str(a) for a in correct_answers)
                    elif q_type == "TRUE_FALSE":
                        # 判断题
                        is_correct = student_answer == correct_answers
                    
                    # 更新评分
                    answer.is_correct = is_correct
                    answer.score_awarded = pq.score_for_question if is_correct else 0
                    attempt_graded = True
                    
                except json.JSONDecodeError:
                    continue
            
            if attempt_graded:
                graded_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"成功为 {graded_count}/{total_attempts} 份试卷的客观题进行了自动评分",
            "graded_attempts": graded_count,
            "total_attempts": total_attempts,
            "objective_questions_count": len(objective_questions)
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"批量自动评分失败: {str(e)}"
        }

# ==================== 考试完成情况查看相关CRUD ====================

def get_exam_scores_with_students(
    db: Session, 
    exam_id: int, 
    teacher_id: int,
    sort_field: str = "score",
    sort_order: str = "desc",
    keyword: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取考试成绩统计（包含学生信息）"""
    # 检查考试权限
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam or not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None, 0, None
    
    # 获取课堂所有学生
    classroom_students = db.query(models.ClassroomStudent).filter(
        models.ClassroomStudent.classroom_id == exam.classroom_id
    ).all()
    
    # 获取学生答题记录
    attempts_query = db.query(models.StudentExamAttempt).filter(
        models.StudentExamAttempt.classroom_exam_id == exam_id
    )
    
    attempts = {attempt.student_id: attempt for attempt in attempts_query.all()}
    
    # 构建学生成绩列表
    student_scores = []
    for cs in classroom_students:
        student = db.query(models.User).filter(models.User.id == cs.student_id).first()
        if not student:
            continue
            
        attempt = attempts.get(cs.student_id)
        
        # 确定状态
        if not attempt or not attempt.attempt_submission_time:
            status = "not_submitted"
            status_cn = "未提交"
        elif attempt.is_graded:
            status = "graded"
            status_cn = "已评分"
        else:
            status = "submitted"
            status_cn = "已提交"
        
        # 应用状态筛选
        if status_filter and status != status_filter:
            continue
            
        # 应用关键词搜索
        if keyword:
            if (keyword.lower() not in (student.full_name or "").lower() and 
                keyword.lower() not in (student.username or "").lower()):
                continue
        
        student_score = {
            "student_id": student.id,
            "student_name": student.full_name or student.username,
            "student_number": student.username,  # 假设username是学号
            "grade": None,  # 需要从其他地方获取
            "major": None,  # 需要从其他地方获取
            "class_name": None,  # 需要从其他地方获取
            "score": attempt.total_score_achieved if attempt else None,
            "duration_seconds": attempt.actual_duration_seconds if attempt else None,
            "submission_time": attempt.attempt_submission_time if attempt else None,
            "status": status,
            "status_cn": status_cn
        }
        student_scores.append(student_score)
    
    # 排序
    reverse = sort_order == "desc"
    if sort_field == "score":
        student_scores.sort(key=lambda x: x["score"] or -1, reverse=reverse)
    elif sort_field == "duration":
        student_scores.sort(key=lambda x: x["duration_seconds"] or 0, reverse=reverse)
    elif sort_field == "submission_time":
        student_scores.sort(key=lambda x: x["submission_time"] or datetime.min.replace(tzinfo=timezone.utc), reverse=reverse)
    elif sort_field == "student_name":
        student_scores.sort(key=lambda x: x["student_name"], reverse=reverse)
    
    total = len(student_scores)
    
    # 分页
    paginated_scores = student_scores[skip:skip + limit]
    
    # 计算统计信息
    submitted_count = len([s for s in student_scores if s["status"] in ["submitted", "graded"]])
    graded_count = len([s for s in student_scores if s["status"] == "graded"])
    scores = [s["score"] for s in student_scores if s["score"] is not None]
    
    statistics = {
        "total_students": total,
        "submitted_count": submitted_count,
        "graded_count": graded_count,
        "average_score": round(sum(scores) / len(scores), 1) if scores else None,
        "highest_score": max(scores) if scores else None,
        "lowest_score": min(scores) if scores else None,
        "pass_rate": round(len([s for s in scores if s >= (exam.pass_mark or 60)]) / len(scores) * 100, 1) if scores else None
    }
    
    # 考试信息
    exam_info = {
        "exam_id": exam.id,
        "exam_title": exam.title,
        "exam_start_time": exam.exam_start_time,
        "exam_end_time": exam.exam_end_time,
        "duration_minutes": exam.duration_minutes,
        "pass_mark": exam.pass_mark,
        "total_score": exam.test_paper.total_score if exam.test_paper else 100,
        "status": exam.status.value,
        "status_cn": _exam_status_to_chinese(exam.status)
    }
    
    return paginated_scores, total, {"exam_info": exam_info, "statistics": statistics}

def get_exam_score_distribution(db: Session, exam_id: int, teacher_id: int):
    """获取考试成绩分布"""
    # 检查考试权限
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam or not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None
    
    # 获取已评分的成绩
    graded_attempts = db.query(models.StudentExamAttempt).filter(
        models.StudentExamAttempt.classroom_exam_id == exam_id,
        models.StudentExamAttempt.is_graded == True,
        models.StudentExamAttempt.total_score_achieved.isnot(None)
    ).all()
    
    scores = [attempt.total_score_achieved for attempt in graded_attempts]
    
    if not scores:
        return {
            "exam_info": _get_exam_info(exam),
            "distribution": [],
            "chart_data": {"bar_chart": [], "pie_chart": []},
            "current_ranges": _get_default_score_ranges(exam.test_paper.total_score if exam.test_paper else 100)
        }
    
    # 获取或创建分数段设置
    score_ranges = db.query(models.ExamScoreRange).filter(
        models.ExamScoreRange.classroom_exam_id == exam_id
    ).order_by(models.ExamScoreRange.order_index).all()
    
    if not score_ranges:
        # 使用默认分数段
        total_score = exam.test_paper.total_score if exam.test_paper else 100
        score_ranges = _create_default_score_ranges(db, exam_id, total_score)
    
    # 计算分布
    distribution = []
    for range_obj in score_ranges:
        count = len([s for s in scores if range_obj.min_score <= s <= range_obj.max_score])
        percentage = round(count / len(scores) * 100, 1) if scores else 0
        
        range_label = range_obj.label or f"{range_obj.min_score}-{range_obj.max_score}分"
        
        distribution.append({
            "range_label": range_label,
            "min_score": range_obj.min_score,
            "max_score": range_obj.max_score,
            "count": count,
            "percentage": percentage
        })
    
    # 生成图表数据
    chart_data = {
        "bar_chart": [
            {"name": item["range_label"], "value": item["count"]} 
            for item in distribution
        ],
        "pie_chart": [
            {"name": item["range_label"], "value": item["count"]} 
            for item in distribution if item["count"] > 0
        ]
    }
    
    current_ranges = [
        {"min_score": r.min_score, "max_score": r.max_score, "label": r.label}
        for r in score_ranges
    ]
    
    return {
        "exam_info": _get_exam_info(exam),
        "distribution": distribution,
        "chart_data": chart_data,
        "current_ranges": current_ranges
    }

def update_exam_score_ranges(db: Session, exam_id: int, teacher_id: int, ranges: List[dict], enable_custom_labels: bool = False):
    """更新考试分数段设置"""
    # 检查考试权限
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam or not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None
    
    try:
        # 验证分数段设置
        total_score = exam.test_paper.total_score if exam.test_paper else 100
        if not _validate_score_ranges(ranges, total_score):
            return {"error": "分数段设置不合法：必须覆盖0到满分且不能重叠"}
        
        # 删除现有分数段
        db.query(models.ExamScoreRange).filter(
            models.ExamScoreRange.classroom_exam_id == exam_id
        ).delete()
        
        # 创建新的分数段
        for i, range_data in enumerate(ranges):
            score_range = models.ExamScoreRange(
                classroom_exam_id=exam_id,
                min_score=range_data["min_score"],
                max_score=range_data["max_score"],
                label=range_data.get("label") if enable_custom_labels else None,
                order_index=i
            )
            db.add(score_range)
        
        db.commit()
        return {"success": True}
        
    except Exception as e:
        db.rollback()
        return {"error": f"更新分数段失败: {str(e)}"}

def get_exam_question_analysis(
    db: Session, 
    exam_id: int, 
    teacher_id: int,
    skip: int = 0,
    limit: int = 20
):
    """获取考试试题分析"""
    # 检查考试权限
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    if not exam or not check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
        return None, 0, None
    
    # 获取试卷题目
    paper_questions = db.query(models.TestPaperQuestion).filter(
        models.TestPaperQuestion.test_paper_id == exam.test_paper_id
    ).order_by(models.TestPaperQuestion.order_in_paper).all()
    
    total_questions = len(paper_questions)
    paginated_questions = paper_questions[skip:skip + limit]
    
    # 获取已提交的答题记录
    submitted_attempts = db.query(models.StudentExamAttempt).filter(
        models.StudentExamAttempt.classroom_exam_id == exam_id,
        models.StudentExamAttempt.attempt_submission_time.isnot(None)
    ).all()
    
    total_submissions = len(submitted_attempts)
    
    question_analyses = []
    total_correct_rate = 0
    
    for i, pq in enumerate(paginated_questions):
        question = pq.question
        
        # 获取该题的所有答案
        answers = db.query(models.StudentExamAnswer).filter(
            models.StudentExamAnswer.question_id == question.id,
            models.StudentExamAnswer.student_exam_attempt_id.in_([a.id for a in submitted_attempts])
        ).all()
        
        # 计算正确率和平均分
        correct_count = len([a for a in answers if a.is_correct])
        correct_rate = round(correct_count / total_submissions * 100, 1) if total_submissions > 0 else 0
        
        scored_answers = [a for a in answers if a.score_awarded is not None]
        average_score = round(sum(a.score_awarded for a in scored_answers) / len(scored_answers), 1) if scored_answers else 0
        
        # 选项统计（仅对选择题）
        option_statistics = []
        if question.question_type in ["SINGLE_CHOICE", "MULTIPLE_CHOICE"]:
            option_statistics = _calculate_option_statistics(question, answers, total_submissions)
        
        # 判断难度等级
        if correct_rate >= 80:
            difficulty_level = "easy"
        elif correct_rate >= 50:
            difficulty_level = "medium"
        else:
            difficulty_level = "hard"
        
        question_analysis = {
            "question_id": question.id,
            "question_number": skip + i + 1,
            "question_content": question.content[:100] + "..." if len(question.content) > 100 else question.content,
            "question_type": question.question_type.value,
            "question_type_cn": _question_type_to_chinese(question.question_type),
            "score": pq.score_for_question,
            "correct_rate": correct_rate,
            "average_score": average_score,
            "option_statistics": option_statistics,
            "difficulty_level": difficulty_level
        }
        question_analyses.append(question_analysis)
        total_correct_rate += correct_rate
    
    # 整体统计
    overall_statistics = {
        "total_questions": total_questions,
        "total_submissions": total_submissions,
        "average_correct_rate": round(total_correct_rate / len(paginated_questions), 1) if paginated_questions else 0,
        "easy_questions": len([q for q in question_analyses if q["difficulty_level"] == "easy"]),
        "medium_questions": len([q for q in question_analyses if q["difficulty_level"] == "medium"]),
        "hard_questions": len([q for q in question_analyses if q["difficulty_level"] == "hard"])
    }
    
    return question_analyses, total_questions, {
        "exam_info": _get_exam_info(exam),
        "overall_statistics": overall_statistics
    }

def export_exam_scores(
    db: Session,
    exam_id: int,
    teacher_id: int,
    sort_field: str = "score",
    sort_order: str = "desc",
    keyword: Optional[str] = None,
    status_filter: Optional[str] = None,
    export_format: str = "xlsx"
):
    """导出考试成绩"""
    # 获取所有成绩数据（不分页）
    scores, total, extra_data = get_exam_scores_with_students(
        db, exam_id, teacher_id, sort_field, sort_order, keyword, status_filter, 0, 10000
    )
    
    if scores is None:
        return None
    
    # 生成Excel或CSV文件
    import io
    import pandas as pd
    from datetime import datetime
    
    # 准备数据
    export_data = []
    for score in scores:
        export_data.append({
            "序号": len(export_data) + 1,
            "姓名": score["student_name"],
            "学号": score["student_number"],
            "年级": score["grade"] or "",
            "专业": score["major"] or "",
            "班级": score["class_name"] or "",
            "得分": score["score"] if score["score"] is not None else "",
            "用时(分钟)": round(score["duration_seconds"] / 60) if score["duration_seconds"] else "",
            "提交时间": score["submission_time"].strftime("%Y-%m-%d %H:%M:%S") if score["submission_time"] else "",
            "状态": score["status_cn"]
        })
    
    df = pd.DataFrame(export_data)
    
    # 生成文件
    output = io.BytesIO()
    exam_title = extra_data["exam_info"]["exam_title"]
    # 清理文件名中的特殊字符
    safe_exam_title = "".join(c for c in exam_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{safe_exam_title}_成绩统计_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if export_format == "xlsx":
        # 使用openpyxl引擎，支持中文
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='成绩统计', index=False)
        filename += ".xlsx"
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        # CSV使用UTF-8编码，添加BOM以便Excel正确识别
        csv_content = df.to_csv(index=False, encoding='utf-8-sig')
        output.write(csv_content.encode('utf-8-sig'))
        filename += ".csv"
        content_type = "text/csv; charset=utf-8"
    
    output.seek(0)
    return output, filename, content_type

# 辅助函数
def _get_exam_info(exam):
    """获取考试基本信息"""
    return {
        "exam_id": exam.id,
        "exam_title": exam.title,
        "exam_start_time": exam.exam_start_time,
        "exam_end_time": exam.exam_end_time,
        "duration_minutes": exam.duration_minutes,
        "pass_mark": exam.pass_mark,
        "total_score": exam.test_paper.total_score if exam.test_paper else 100,
        "status": exam.status.value,
        "status_cn": _exam_status_to_chinese(exam.status)
    }

def _exam_status_to_chinese(status):
    """考试状态转中文"""
    status_map = {
        "UNPUBLISHED": "未发布",
        "SCHEDULED": "已安排",
        "ONGOING": "进行中",
        "GRADING": "阅卷中",
        "COMPLETED": "已完成"
    }
    return status_map.get(status.value if hasattr(status, 'value') else status, "未知")

def _question_type_to_chinese(question_type):
    """题目类型转中文"""
    type_map = {
        "SINGLE_CHOICE": "单选题",
        "MULTIPLE_CHOICE": "多选题",
        "SHORT_ANSWER": "简答题"
    }
    return type_map.get(question_type.value if hasattr(question_type, 'value') else question_type, "未知")

def _get_default_score_ranges(total_score):
    """获取默认分数段"""
    return [
        {"min_score": int(total_score * 0.9), "max_score": total_score, "label": "优秀"},
        {"min_score": int(total_score * 0.8), "max_score": int(total_score * 0.9) - 1, "label": "良好"},
        {"min_score": int(total_score * 0.6), "max_score": int(total_score * 0.8) - 1, "label": "及格"},
        {"min_score": 0, "max_score": int(total_score * 0.6) - 1, "label": "不及格"}
    ]

def _create_default_score_ranges(db: Session, exam_id: int, total_score: int):
    """创建默认分数段"""
    default_ranges = _get_default_score_ranges(total_score)
    
    score_ranges = []
    for i, range_data in enumerate(default_ranges):
        score_range = models.ExamScoreRange(
            classroom_exam_id=exam_id,
            min_score=range_data["min_score"],
            max_score=range_data["max_score"],
            label=range_data["label"],
            order_index=i
        )
        db.add(score_range)
        score_ranges.append(score_range)
    
    db.commit()
    return score_ranges
def _validate_score_ranges(ranges, total_score):
    """验证分数段设置"""
    if len(ranges) < 2 or len(ranges) > 6:
        return False
    
    # 排序
    ranges.sort(key=lambda x: x["min_score"])
    
    # 检查是否覆盖0到满分
    if ranges[0]["min_score"] != 0 or ranges[-1]["max_score"] != total_score:
        return False
    
    # 检查是否连续且不重叠
    for i in range(len(ranges) - 1):
        if ranges[i]["max_score"] + 1 != ranges[i + 1]["min_score"]:
            return False
    
    return True

def _calculate_option_statistics(question, answers, total_submissions):
    """计算选项统计"""
    import json
    
    try:
        options = json.loads(question.options or "[]")
        correct_answers = json.loads(question.correct_answers or "[]")
    except json.JSONDecodeError:
        return []
    
    option_stats = {}
    
    # 初始化选项统计
    for option in options:
        option_key = option.get("key", "")
        option_stats[option_key] = {
            "option_key": option_key,
            "option_text": option.get("text", ""),
            "count": 0,
            "percentage": 0,
            "is_correct": option_key in correct_answers
        }
    
    # 统计学生选择
    for answer in answers:
        try:
            student_answer = json.loads(answer.answer_data or "[]")
            if isinstance(student_answer, list):
                for choice in student_answer:
                    if choice in option_stats:
                        option_stats[choice]["count"] += 1
            elif student_answer in option_stats:
                option_stats[student_answer]["count"] += 1
        except json.JSONDecodeError:
            continue
    
    # 计算百分比
    for option_key in option_stats:
        count = option_stats[option_key]["count"]
        option_stats[option_key]["percentage"] = round(count / total_submissions * 100, 1) if total_submissions > 0 else 0
    
    return list(option_stats.values())

# ==================== 学情分析相关CRUD操作 ====================

def _is_practice_classroom_course(classroom_course):
    """判断课堂课程是否为实践课程，兼容 course_id 为空、practice_id 直挂的真实数据形态。"""
    if not classroom_course or classroom_course.practice_id is None:
        return False
    course = classroom_course.course
    return course is None or course.course_type == models.CourseTypeEnum.PRACTICE


def _is_training_classroom_course(classroom_course):
    """判断课堂课程是否为实训项目。"""
    course = classroom_course.course if classroom_course else None
    return bool(course and course.course_type == models.CourseTypeEnum.TRAINING)


def _classroom_course_display_title(classroom_course):
    if classroom_course.classroom_chapter_title:
        return classroom_course.classroom_chapter_title
    if classroom_course.name_override:
        return classroom_course.name_override
    if classroom_course.practice:
        return classroom_course.practice.title
    if classroom_course.course:
        return classroom_course.course.title
    return f"课程 {classroom_course.id}"


def _get_practice_auto_metrics_by_student(db: Session, practice_id: int, student_ids: Optional[list] = None):
    """按学生汇总某个 practice 的 task_evaluation_results 最新评测结果。"""
    task_rows = db.query(models.Task.id, models.Task.coin).filter(
        models.Task.practice_id == practice_id,
        models.Task.deleted_at.is_(None),
    ).all()
    task_ids = [row.id for row in task_rows]
    total_coin = sum((row.coin or 0) for row in task_rows)

    metrics = {}
    if not task_ids:
        return {
            "total_tasks": 0,
            "total_coin": 0,
            "by_student": metrics,
        }

    query = db.query(models.TaskEvaluationResult).filter(
        models.TaskEvaluationResult.task_id.in_(task_ids)
    )
    if student_ids:
        query = query.filter(models.TaskEvaluationResult.user_id.in_(student_ids))

    rows = query.order_by(
        models.TaskEvaluationResult.user_id,
        models.TaskEvaluationResult.task_id,
        models.TaskEvaluationResult.created_at.desc(),
    ).all()

    latest_rows = []
    seen = set()
    for row in rows:
        key = (row.user_id, row.task_id)
        if key in seen:
            continue
        seen.add(key)
        latest_rows.append(row)

    for row in latest_rows:
        item = metrics.setdefault(row.user_id, {
            "completed": 0,
            "score_sum": 0,
            "last_at": None,
        })
        if row.status == "pass":
            item["completed"] += 1
            item["score_sum"] += row.score or 0
        if item["last_at"] is None or (row.created_at and row.created_at > item["last_at"]):
            item["last_at"] = row.created_at

    for item in metrics.values():
        item["score_pct"] = round(item["score_sum"] / total_coin * 100, 1) if total_coin else None

    return {
        "total_tasks": len(task_rows),
        "total_coin": total_coin,
        "by_student": metrics,
    }


def _build_learning_students_analytics(
    db: Session,
    classroom_id: int,
    is_mandatory: bool,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
):
    """构建必修/拓展学生学情统计，兼容 practice_id 直挂和 TER 自动评测。"""
    from sqlalchemy import or_

    query = db.query(models.User).join(
        models.ClassroomStudent, models.User.id == models.ClassroomStudent.student_id
    ).filter(
        models.ClassroomStudent.classroom_id == classroom_id
    )

    if keyword:
        query = query.filter(
            or_(
                models.User.full_name.ilike(f"%{keyword}%"),
                models.User.username.ilike(f"%{keyword}%")
            )
        )

    total = query.count()
    students = query.offset(skip).limit(limit).all()
    student_ids = [student.id for student in students]

    classroom_courses = db.query(models.ClassroomCourse).options(
        joinedload(models.ClassroomCourse.course),
        joinedload(models.ClassroomCourse.practice),
    ).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.is_mandatory == is_mandatory,
        models.ClassroomCourse.teacher_publish_status != models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED,
    ).all()
    classroom_course_ids = [cc.id for cc in classroom_courses]

    progress_rows = []
    if classroom_course_ids and student_ids:
        progress_rows = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id.in_(classroom_course_ids),
            models.StudentCourseProgress.student_id.in_(student_ids),
        ).all()
    progress_by_key = {
        (progress.classroom_course_id, progress.student_id): progress
        for progress in progress_rows
    }

    auto_metrics_by_course = {}
    for classroom_course in classroom_courses:
        if _is_practice_classroom_course(classroom_course):
            auto_metrics_by_course[classroom_course.id] = _get_practice_auto_metrics_by_student(
                db, classroom_course.practice_id, student_ids
            )

    student_records = []
    total_practice_score = 0
    total_training_score = 0
    total_course_score = 0
    total_study_hours = 0
    online_count = 0

    for student in students:
        is_online = (student.id % 3 == 0)
        if is_online:
            online_count += 1

        practice_completed = 0
        practice_scores = []
        training_completed = 0
        training_scores = []
        total_hours = 0

        for classroom_course in classroom_courses:
            progress = progress_by_key.get((classroom_course.id, student.id))
            if progress and progress.total_time_spent_seconds:
                total_hours += progress.total_time_spent_seconds / 3600

            if _is_practice_classroom_course(classroom_course):
                auto_metrics = auto_metrics_by_course.get(classroom_course.id, {})
                student_metric = (auto_metrics.get("by_student") or {}).get(student.id, {})
                auto_completed = student_metric.get("completed", 0)
                auto_score = student_metric.get("score_pct")

                if progress and progress.student_status in [
                    models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME,
                    models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
                ]:
                    practice_completed += progress.completed_task_count or auto_completed or 1
                elif auto_completed:
                    practice_completed += auto_completed

                if progress and progress.student_status not in [
                    models.CourseInClassroomStatusStudentEnum.NOT_YET_PUBLISHED,
                    models.CourseInClassroomStatusStudentEnum.NOT_STARTED
                ]:
                    practice_scores.append(progress.final_calculated_score or auto_score or 0)
                elif auto_score is not None:
                    practice_scores.append(auto_score)

            elif _is_training_classroom_course(classroom_course):
                if not progress:
                    continue
                if progress.student_status in [
                    models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME,
                    models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
                ]:
                    training_completed += 1
                if progress.student_status not in [
                    models.CourseInClassroomStatusStudentEnum.NOT_YET_PUBLISHED,
                    models.CourseInClassroomStatusStudentEnum.NOT_STARTED
                ]:
                    training_scores.append(progress.final_calculated_score or 0)

        practice_avg = sum(practice_scores) / len(practice_scores) if practice_scores else 0
        training_avg = sum(training_scores) / len(training_scores) if training_scores else 0
        course_avg = (
            (sum(practice_scores) + sum(training_scores)) / (len(practice_scores) + len(training_scores))
            if (practice_scores or training_scores) else 0
        )

        total_practice_score += practice_avg
        total_training_score += training_avg
        total_course_score += course_avg
        total_study_hours += total_hours

        student_records.append({
            "student_id": student.id,
            "student_name": student.full_name or "未知",
            "student_number": student.username,
            "online_status": "online" if is_online else "offline",
            "grade_class": None,
            "practice_completed": practice_completed,
            "practice_average_score": round(practice_avg, 1),
            "training_completed": training_completed,
            "training_average_score": round(training_avg, 1),
            "course_average_score": round(course_avg, 1),
            "total_study_hours": round(total_hours, 1)
        })

    student_count = len(students)
    summary = {
        "total_students": total,
        "online_students": online_count,
        "offline_students": student_count - online_count,
        "avg_practice_score": round(total_practice_score / student_count, 1) if student_count > 0 else 0,
        "avg_training_score": round(total_training_score / student_count, 1) if student_count > 0 else 0,
        "avg_overall_score": round(total_course_score / student_count, 1) if student_count > 0 else 0,
        "total_study_hours": round(total_study_hours, 1)
    }

    return {
        "list": student_records,
        "meta": {
            "total": total,
            "page": (skip // limit) + 1,
            "page_size": limit
        },
        "summary": summary
    }


def get_learning_overview(db: Session, classroom_id: int):
    """获取学情总览"""
    from sqlalchemy import func, case, distinct
    
    # 获取课堂基本信息
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id
    ).first()
    
    if not classroom:
        return None
    
    # 课堂基本信息
    classroom_info = {
        "id": classroom.id,
        "name": classroom.name,
        "start_date": classroom.start_date,
        "end_date": classroom.end_date
    }
    
    classroom_courses = db.query(models.ClassroomCourse).options(
        joinedload(models.ClassroomCourse.course),
        joinedload(models.ClassroomCourse.practice),
    ).filter(
        models.ClassroomCourse.classroom_id == classroom_id
    ).all()

    practice_courses = [
        classroom_course for classroom_course in classroom_courses
        if _is_practice_classroom_course(classroom_course)
    ]
    training_courses = [
        classroom_course for classroom_course in classroom_courses
        if _is_training_classroom_course(classroom_course)
    ]

    practice_total = len(practice_courses)
    practice_published = sum(
        1 for classroom_course in practice_courses
        if classroom_course.teacher_publish_status != models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    )
    training_total = len(training_courses)
    training_published = sum(
        1 for classroom_course in training_courses
        if classroom_course.teacher_publish_status != models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    )
    
    classroom_info.update({
        "practice_total": practice_total,
        "practice_published": practice_published,
        "training_total": training_total,
        "training_published": training_published,
        # Frontend compatibility: LearningOverviewTab currently reads these legacy keys.
        "practice_courses_total": practice_total,
        "practice_courses_published": practice_published,
        "training_courses_total": training_total,
        "training_courses_published": training_published
    })
    
    # 课程完成情况统计
    course_status_stats = db.query(
        models.ClassroomCourse.teacher_publish_status,
        func.count(models.ClassroomCourse.id).label('count')
    ).filter(
        models.ClassroomCourse.classroom_id == classroom_id
    ).group_by(models.ClassroomCourse.teacher_publish_status).all()
    
    course_completion_stats = {
        "completed": 0,
        "learning": 0,
        "makeup": 0,
        "unpublished": 0
    }
    
    for status, count in course_status_stats:
        if status == models.CourseInClassroomStatusTeacherEnum.COMPLETED:
            course_completion_stats["completed"] = count
        elif status == models.CourseInClassroomStatusTeacherEnum.LEARNING:
            course_completion_stats["learning"] = count
        elif status == models.CourseInClassroomStatusTeacherEnum.MAKEUP:
            course_completion_stats["makeup"] = count
        elif status == models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED:
            course_completion_stats["unpublished"] = count
    
    # 学生在线情况统计（模拟数据，实际应该根据最近心跳时间判断）
    total_students = classroom.student_count or 0
    # 这里简化处理，实际应该查询学生最近活动时间
    online_count = int(total_students * 0.3) if total_students else 0  # 假设30%在线
    offline_count = total_students - online_count
    
    student_online_stats = {
        "online_count": online_count,
        "offline_count": offline_count,
        "total_count": total_students
    }
    
    classroom_students = db.query(models.User).join(
        models.ClassroomStudent, models.User.id == models.ClassroomStudent.student_id
    ).filter(
        models.ClassroomStudent.classroom_id == classroom_id
    ).all()
    student_ids = [student.id for student in classroom_students]
    classroom_course_ids = [classroom_course.id for classroom_course in classroom_courses]

    progress_rows = []
    if classroom_course_ids and student_ids:
        progress_rows = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id.in_(classroom_course_ids),
            models.StudentCourseProgress.student_id.in_(student_ids),
        ).all()
    progress_by_key = {
        (progress.classroom_course_id, progress.student_id): progress
        for progress in progress_rows
    }

    auto_metrics_by_course = {
        classroom_course.id: _get_practice_auto_metrics_by_student(db, classroom_course.practice_id, student_ids)
        for classroom_course in practice_courses
    }

    student_average_scores = []
    for student in classroom_students:
        scores = []
        for classroom_course in classroom_courses:
            if classroom_course.is_mandatory is not True:
                continue
            progress = progress_by_key.get((classroom_course.id, student.id))
            if _is_practice_classroom_course(classroom_course):
                student_metric = (
                    auto_metrics_by_course.get(classroom_course.id, {}).get("by_student") or {}
                ).get(student.id, {})
                auto_score = student_metric.get("score_pct")
                if progress and progress.final_calculated_score and progress.final_calculated_score > 0:
                    scores.append(progress.final_calculated_score)
                elif auto_score is not None:
                    scores.append(auto_score)
            elif _is_training_classroom_course(classroom_course):
                if progress and progress.final_calculated_score and progress.final_calculated_score > 0:
                    scores.append(progress.final_calculated_score)

        if scores:
            student_average_scores.append({
                "student_id": student.id,
                "student_name": student.full_name or "未知",
                "average_score": round(sum(scores) / len(scores), 1)
            })
    
    # 平均成绩排名（前10名）
    top_students_ranking = sorted(student_average_scores, key=lambda x: x["average_score"], reverse=True)[:10]
    for i, student in enumerate(top_students_ranking):
        student["rank"] = i + 1
    
    # 学习时长统计（按学号升序）
    study_duration_data = db.query(
        models.User.id,
        models.User.username,
        models.User.full_name,
        func.sum(models.StudentCourseProgress.total_time_spent_seconds).label('total_seconds')
    ).join(
        models.StudentCourseProgress, models.User.id == models.StudentCourseProgress.student_id
    ).join(
        models.ClassroomCourse, models.StudentCourseProgress.classroom_course_id == models.ClassroomCourse.id
    ).filter(
        models.ClassroomCourse.classroom_id == classroom_id
    ).group_by(models.User.id, models.User.username, models.User.full_name).order_by(models.User.username).all()
    
    study_duration_stats = [
        {
            "student_number": username,
            "student_name": full_name or "未知",
            "total_hours": round(float(total_seconds or 0) / 3600, 1)
        }
        for _, username, full_name, total_seconds in study_duration_data
    ]
    
    # 课程平均成绩统计
    # 按章节统计
    chapter_scores = db.query(
        models.ClassroomChapter.title,
        func.avg(models.StudentCourseProgress.final_calculated_score).label('avg_score')
    ).join(
        models.ClassroomCourse, models.ClassroomChapter.id == models.ClassroomCourse.classroom_chapter_id
    ).join(
        models.StudentCourseProgress, models.ClassroomCourse.id == models.StudentCourseProgress.classroom_course_id
    ).filter(
        models.ClassroomChapter.classroom_id == classroom_id,
        models.StudentCourseProgress.final_calculated_score > 0
    ).group_by(models.ClassroomChapter.title).all()
    
    by_chapter = [
        {
            "chapter_name": title,
            "average_score": round(float(avg_score), 1)
        }
        for title, avg_score in chapter_scores
    ]
    
    # 按课程统计
    by_course = []
    for classroom_course in classroom_courses:
        scores = []
        if _is_practice_classroom_course(classroom_course):
            auto_metrics = auto_metrics_by_course.get(classroom_course.id)
            if auto_metrics is None:
                auto_metrics = _get_practice_auto_metrics_by_student(
                    db, classroom_course.practice_id, student_ids
                )
            for student_id, metric in (auto_metrics.get("by_student") or {}).items():
                score = metric.get("score_pct")
                if score is not None:
                    scores.append(score)

        course_progress_rows = [
            progress for progress in progress_rows
            if progress.classroom_course_id == classroom_course.id
            and progress.final_calculated_score
            and progress.final_calculated_score > 0
        ]
        for progress in course_progress_rows:
            scores.append(progress.final_calculated_score)

        if scores:
            by_course.append({
                "course_name": _classroom_course_display_title(classroom_course),
                "average_score": round(sum(scores) / len(scores), 1)
            })
    
    course_average_scores = {
        "by_chapter": by_chapter,
        "by_course": by_course
    }

    statistics = {
        "average_score": (
            round(
                sum(student["average_score"] for student in student_average_scores) / len(student_average_scores),
                1
            )
            if student_average_scores else 0
        ),
        "top_students": top_students_ranking,
        "study_time_stats": study_duration_stats,
        "course_avg_scores": by_course,
    }
    
    return {
        "classroom_info": classroom_info,
        "course_completion_stats": course_completion_stats,
        "course_completion": {
            "completed": course_completion_stats["completed"],
            "learning": course_completion_stats["learning"],
            "makeup": course_completion_stats["makeup"],
            "not_published": course_completion_stats["unpublished"],
        },
        "student_online_stats": student_online_stats,
        "online_status": {
            "online_count": student_online_stats["online_count"],
            "offline_count": student_online_stats["offline_count"],
        },
        "student_average_scores": student_average_scores,
        "top_students_ranking": top_students_ranking,
        "study_duration_stats": study_duration_stats,
        "course_average_scores": course_average_scores,
        "statistics": statistics,
    }

def get_required_courses_analytics(
    db: Session, 
    classroom_id: int, 
    keyword: Optional[str] = None,
    skip: int = 0, 
    limit: int = 20
):
    """获取必修课程统计"""
    return _build_learning_students_analytics(db, classroom_id, True, keyword, skip, limit)

def get_optional_courses_analytics(
    db: Session, 
    classroom_id: int, 
    keyword: Optional[str] = None,
    skip: int = 0, 
    limit: int = 20
):
    """获取拓展课程统计（与必修课程统计逻辑相同，但只统计拓展课程）"""
    return _build_learning_students_analytics(db, classroom_id, False, keyword, skip, limit)

def get_student_transcript(db: Session, classroom_id: int, student_id: int):
    """获取学生个人成绩单"""
    from sqlalchemy import func
    
    # 获取学生基本信息
    student = db.query(models.User).filter(models.User.id == student_id).first()
    if not student:
        return None
    
    # 检查学生是否在该课堂中
    classroom_student = db.query(models.ClassroomStudent).filter(
        models.ClassroomStudent.classroom_id == classroom_id,
        models.ClassroomStudent.student_id == student_id
    ).first()
    if not classroom_student:
        return None
    
    # 学生基本信息
    student_info = {
        "student_id": student.id,
        "student_name": student.full_name or "未知",
        "student_number": student.username,
        "grade": "",  # 暂时为空
        "major": "",  # 暂时为空
        "class_name": ""  # 暂时为空
    }
    
    # 获取学生的所有课程进度（必修课程）
    required_progress = db.query(models.StudentCourseProgress).join(
        models.ClassroomCourse, models.StudentCourseProgress.classroom_course_id == models.ClassroomCourse.id
    ).join(
        models.Course, models.ClassroomCourse.course_id == models.Course.id
    ).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.is_mandatory == True,
        models.StudentCourseProgress.student_id == student_id
    ).all()
    
    # 计算综合统计
    total_courses = len(required_progress)
    completed_courses = sum(1 for p in required_progress if p.student_status in [
        models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME,
        models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
    ])
    
    # 计算必修课程平均分
    valid_scores = [p.final_calculated_score for p in required_progress if p.final_calculated_score > 0]
    course_average_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
    
    # 计算总学习时长
    total_study_hours = sum(p.total_time_spent_seconds for p in required_progress) / 3600
    
    # 计算成绩排名（在课堂中的排名）
    all_students_avg = db.query(
        models.StudentCourseProgress.student_id,
        func.avg(models.StudentCourseProgress.final_calculated_score).label('avg_score')
    ).join(
        models.ClassroomCourse, models.StudentCourseProgress.classroom_course_id == models.ClassroomCourse.id
    ).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.is_mandatory == True,
        models.StudentCourseProgress.final_calculated_score > 0
    ).group_by(models.StudentCourseProgress.student_id).all()
    
    # 排序并找到当前学生的排名
    sorted_scores = sorted(all_students_avg, key=lambda x: x.avg_score, reverse=True)
    score_ranking = next((i + 1 for i, (sid, _) in enumerate(sorted_scores) if sid == student_id), 0)
    
    # 计算优秀作业数
    excellent_assignments = sum(1 for p in required_progress if p.is_excellent_work)
    
    # 综合统计
    overall_stats = {
        "course_average_score": round(course_average_score, 1),
        "score_ranking": score_ranking,
        "total_study_hours": round(total_study_hours, 1),
        "completed_courses": f"{completed_courses}/{total_courses}",
        "excellent_assignments": excellent_assignments
    }
    
    # 课程列表
    courses = []
    for progress in required_progress:
        course = progress.classroom_course.course
        
        course_data = {
            "course_id": course.id,
            "course_name": progress.classroom_course.classroom_chapter_title or course.title,
            "course_type": course.course_type.value,
            "study_hours": round(progress.total_time_spent_seconds / 3600, 1),
            "completion_time": progress.last_submission_at,
            "course_score": progress.final_calculated_score
        }
        
        if course.course_type == models.CourseTypeEnum.PRACTICE:
            # 实践课程：显示关卡完成进度
            course_data["level_progress"] = f"{progress.completed_task_count}/{course.practice_task_count}"
        elif course.course_type == models.CourseTypeEnum.TRAINING:
            # 实训课程：显示提交作业数量
            course_data["submission_count"] = 1 if progress.training_submission_status in [
                models.SubmissionStatusEnum.SUBMITTED,
                models.SubmissionStatusEnum.LATE_SUBMISSION
            ] else 0
        
        courses.append(course_data)
    
    return {
        "student_info": student_info,
        "overall_stats": overall_stats,
        "courses": courses
    }

def get_classroom_analytics_overview(db: Session, classroom_id: int):
    """获取学情分析总览"""
    # 获取课堂基本信息
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id
    ).first()
    
    if not classroom:
        return None
    
    # 学生总数
    total_students = classroom.student_count
    
    # 课程统计
    total_courses = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id
    ).count()
    
    # 必修课程数量
    mandatory_courses = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.is_mandatory == True
    ).count()
    
    # 拓展课程数量
    elective_courses = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.is_mandatory == False
    ).count()
    
    # 已发布课程数量
    published_courses = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.teacher_publish_status != models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
    ).count()
    
    # 学生完成情况统计
    completed_students = db.query(models.StudentCourseProgress).filter(
        models.StudentCourseProgress.classroom_course_id.in_(
            db.query(models.ClassroomCourse.id).filter(
                models.ClassroomCourse.classroom_id == classroom_id
            )
        ),
        models.StudentCourseProgress.student_status.in_([
            models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME,
            models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
        ])
    ).distinct(models.StudentCourseProgress.student_id).count()
    
    # 平均成绩
    avg_score = db.query(func.avg(models.StudentCourseProgress.final_calculated_score)).filter(
        models.StudentCourseProgress.classroom_course_id.in_(
            db.query(models.ClassroomCourse.id).filter(
                models.ClassroomCourse.classroom_id == classroom_id,
                models.ClassroomCourse.is_mandatory == True
            )
        ),
        models.StudentCourseProgress.final_calculated_score > 0
    ).scalar() or 0
    
    return {
        "classroom_info": {
            "id": classroom.id,
            "name": classroom.name,
            "total_students": total_students,
            "start_date": classroom.start_date,
            "end_date": classroom.end_date
        },
        "course_stats": {
            "total_courses": total_courses,
            "mandatory_courses": mandatory_courses,
            "elective_courses": elective_courses,
            "published_courses": published_courses
        },
        "student_stats": {
            "total_students": total_students,
            "completed_students": completed_students,
            "completion_rate": round(completed_students / total_students * 100, 2) if total_students > 0 else 0,
            "average_score": round(avg_score, 2)
        }
    }

# ==================== 教学资源模块相关CRUD操作 ====================

def get_classroom_resource_modules(
    db: Session,
    classroom_id: int,
    teacher_id: int
):
    """获取课堂教学资源模块列表"""
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return []
    
    modules = db.query(models.ResourceModule).filter(
        models.ResourceModule.classroom_id == classroom_id,
        models.ResourceModule.is_active == True
    ).order_by(models.ResourceModule.order_index.asc()).all()
    
    # 为每个模块添加文件数量统计
    for module in modules:
        file_count = db.query(models.ResourceFile).filter(
            models.ResourceFile.module_id == module.id,
            models.ResourceFile.is_active == True
        ).count()
        module.file_count = file_count
    
    return modules

def create_resource_module(
    db: Session,
    classroom_id: int,
    name: str,
    teacher_id: int,
    description: Optional[str] = None
):
    """创建教学资源模块"""
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return None
    
    # 获取下一个排序索引
    max_order = db.query(func.max(models.ResourceModule.order_index)).filter(
        models.ResourceModule.classroom_id == classroom_id,
        models.ResourceModule.is_active == True
    ).scalar() or 0
    
    # 创建模块
    module = models.ResourceModule(
        classroom_id=classroom_id,
        name=name,
        description=description,
        order_index=max_order + 1,
        created_by=teacher_id
    )
    
    db.add(module)
    db.commit()
    db.refresh(module)
    
    return module

def update_resource_module(
    db: Session,
    module_id: int,
    teacher_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    order_index: Optional[int] = None
):
    """更新教学资源模块"""
    # 获取模块
    module = db.query(models.ResourceModule).filter(
        models.ResourceModule.id == module_id,
        models.ResourceModule.is_active == True
    ).first()
    
    if not module:
        return None
    
    # 检查权限
    if not check_classroom_teacher_permission(db, module.classroom_id, teacher_id):
        return None
    
    # 更新字段
    if name is not None:
        module.name = name
    if description is not None:
        module.description = description
    if order_index is not None:
        module.order_index = order_index
    
    db.commit()
    db.refresh(module)
    
    return module
def delete_resource_module(
    db: Session,
    module_id: int,
    teacher_id: int
):
    """删除教学资源模块（软删除）"""
    # 获取模块
    module = db.query(models.ResourceModule).filter(
        models.ResourceModule.id == module_id,
        models.ResourceModule.is_active == True
    ).first()
    
    if not module:
        return False
    
    # 检查权限
    if not check_classroom_teacher_permission(db, module.classroom_id, teacher_id):
        return False
    
    # 软删除模块及其所有文件
    module.is_active = False
    
    # 同时软删除模块下的所有文件
    db.query(models.ResourceFile).filter(
        models.ResourceFile.module_id == module_id
    ).update({"is_active": False})
    
    db.commit()
    
    return True

def get_module_files(
    db: Session,
    module_id: int,
    teacher_id: int
):
    """获取模块内的文件列表"""
    # 获取模块
    module = db.query(models.ResourceModule).filter(
        models.ResourceModule.id == module_id,
        models.ResourceModule.is_active == True
    ).first()
    
    if not module:
        return []
    
    # 检查权限
    if not check_classroom_teacher_permission(db, module.classroom_id, teacher_id):
        return []
    
    files = db.query(models.ResourceFile).filter(
        models.ResourceFile.module_id == module_id,
        models.ResourceFile.is_active == True
    ).order_by(models.ResourceFile.created_at.desc()).all()
    
    return files

def upload_resource_file(
    db: Session,
    module_id: int,
    name: str,
    url: str,
    file_type: str,
    file_size: int,
    teacher_id: int,
    duration_seconds: Optional[int] = None
):
    """上传文件到教学资源模块"""
    # 获取模块
    module = db.query(models.ResourceModule).filter(
        models.ResourceModule.id == module_id,
        models.ResourceModule.is_active == True
    ).first()
    
    if not module:
        return None
    
    # 检查权限
    if not check_classroom_teacher_permission(db, module.classroom_id, teacher_id):
        return None
    
    # 验证文件类型
    allowed_types = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'mp4']
    if file_type.lower() not in allowed_types:
        return None
    
    # 创建文件记录
    resource_file = models.ResourceFile(
        module_id=module_id,
        name=name,
        url=url,
        file_type=file_type.lower(),
        file_size=file_size,
        duration_seconds=duration_seconds,
        uploader_id=teacher_id
    )
    
    db.add(resource_file)
    db.commit()
    db.refresh(resource_file)
    
    return resource_file

def delete_resource_file(
    db: Session,
    file_id: int,
    teacher_id: int
):
    """删除教学资源文件（软删除）"""
    # 获取文件
    resource_file = db.query(models.ResourceFile).filter(
        models.ResourceFile.id == file_id,
        models.ResourceFile.is_active == True
    ).first()
    
    if not resource_file:
        return False
    
    # 获取模块以检查权限
    module = db.query(models.ResourceModule).filter(
        models.ResourceModule.id == resource_file.module_id
    ).first()
    
    if not module or not check_classroom_teacher_permission(db, module.classroom_id, teacher_id):
        return False
    
    # 软删除文件
    resource_file.is_active = False
    db.commit()
    
    return True

def update_file_view_count(
    db: Session,
    file_id: int
):
    """更新文件查看次数"""
    resource_file = db.query(models.ResourceFile).filter(
        models.ResourceFile.id == file_id,
        models.ResourceFile.is_active == True
    ).first()
    
    if resource_file:
        resource_file.view_count += 1
        db.commit()
        return True
    
    return False

def record_student_learning(
    db: Session,
    student_id: int,
    resource_file_id: int,
    learning_duration_seconds: int,
    last_position: int = 0,
    is_completed: bool = False
):
    """记录学生学习时长"""
    # 查找现有记录
    learning_record = db.query(models.StudentResourceLearning).filter(
        models.StudentResourceLearning.student_id == student_id,
        models.StudentResourceLearning.resource_file_id == resource_file_id
    ).first()
    
    if learning_record:
        # 更新现有记录
        learning_record.learning_duration_seconds += learning_duration_seconds
        learning_record.last_position = last_position
        learning_record.is_completed = is_completed
        learning_record.last_access_at = func.now()
    else:
        # 创建新记录
        learning_record = models.StudentResourceLearning(
            student_id=student_id,
            resource_file_id=resource_file_id,
            learning_duration_seconds=learning_duration_seconds,
            last_position=last_position,
            is_completed=is_completed
        )
        db.add(learning_record)
    
    db.commit()
    db.refresh(learning_record)
    
    return learning_record

def get_student_learning_records(
    db: Session,
    student_id: int,
    classroom_id: int
):
    """获取学生在某个课堂的学习记录"""
    # 通过模块关联查询学习记录
    records = db.query(models.StudentResourceLearning).join(
        models.ResourceFile, models.StudentResourceLearning.resource_file_id == models.ResourceFile.id
    ).join(
        models.ResourceModule, models.ResourceFile.module_id == models.ResourceModule.id
    ).filter(
        models.StudentResourceLearning.student_id == student_id,
        models.ResourceModule.classroom_id == classroom_id,
        models.ResourceModule.is_active == True,
        models.ResourceFile.is_active == True
    ).all()
    
    return records

# ==================== 自定义实践相关CRUD操作 ====================

def get_practice_environments(db: Session):
    """获取可用的实践环境列表"""
    try:
        # 先尝试原生SQL查询
        result = db.execute(text("SELECT * FROM practice_environments"))
        rows = result.fetchall()

        # 如果找到记录，返回模拟对象
        if len(rows) > 0:
            environments = []
            from datetime import datetime
            for row in rows:
                env_dict = {
                    'id': row[0],
                    'name': row[1],
                    'environment_type': row[2],
                    'docker_image': row[11] if len(row) > 11 else 'jupyter/scipy-notebook:latest',
                    'description': row[3],
                    'config': row[4],
                    'status': row[5],
                    'max_sessions': row[6],
                    'session_timeout': row[7],
                    'default_storage': row[12] if len(row) > 12 else '1Gi',
                    'default_memory': row[13] if len(row) > 13 else '1Gi',
                    'default_cpu': row[14] if len(row) > 14 else '1',
                    'is_active': bool(row[10]) if len(row) > 10 else True,
                    'created_at': row[8] if row[8] else datetime.now(),
                    'updated_at': row[9] if row[9] else datetime.now()
                }
                environments.append(type('PracticeEnvironment', (), env_dict)())
            return environments

        # 如果原生SQL也没有找到，尝试ORM查询
        environments = db.query(models.PracticeEnvironment).all()
        return environments

    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

def get_direction_categories(db: Session):
    """获取方向分类选项"""
    # 从现有课程和实践中获取方向分类
    directions = db.query(models.Course.direction).distinct().all()
    categories = db.query(models.Course.categories).distinct().all()
    
    # 处理方向
    primary_categories = []
    for direction in directions:
        if direction[0] and direction[0] not in primary_categories:
            primary_categories.append(direction[0])
    
    # 处理分类（假设存储为JSON字符串）
    secondary_categories = {}
    for category in categories:
        if category[0]:
            try:
                import json
                cat_list = json.loads(category[0]) if isinstance(category[0], str) else category[0]
                if isinstance(cat_list, list):
                    for cat in cat_list:
                        # 这里简化处理，实际应该根据业务逻辑建立一级二级分类关系
                        if "大数据" not in secondary_categories:
                            secondary_categories["大数据"] = []
                        if cat not in secondary_categories["大数据"]:
                            secondary_categories["大数据"].append(cat)
            except:
                pass
    
    # 默认分类结构
    if not secondary_categories:
        secondary_categories = {
            "大数据": ["流式处理", "存储系统", "数据分析"],
            "人工智能": ["机器学习", "深度学习", "自然语言处理"],
            "云计算": ["容器技术", "微服务", "DevOps"],
            "区块链": ["智能合约", "DeFi", "NFT"],
            "编程语言": ["Python基础", "Java基础", "JavaScript"]
        }
        primary_categories = list(secondary_categories.keys())
    
    return {
        "primary_categories": primary_categories,
        "secondary_categories": secondary_categories
    }

def create_custom_practice(
    db: Session,
    practice_data: dict,
    creator_id: int
):
    """创建自定义实践"""
    # 验证环境是否存在
    environment = db.query(models.PracticeEnvironment).filter(
        models.PracticeEnvironment.id == practice_data["environment_id"]
    ).first()
    if not environment:
        raise ValueError("指定的实践环境不存在")

    # 创建实践记录
    practice = models.Practice(
        title=practice_data["title"],
        practice_type=practice_data["practice_type"],
        intro=practice_data["intro"],
        difficulty=practice_data["difficulty"],
        direction=practice_data.get("direction", "自定义实践"),  # 添加默认方向
        category=practice_data.get("category", "自定义"),  # 添加默认分类
        categories=json.dumps(practice_data.get("categories", [])),
        environment_id=practice_data["environment_id"],
        creator_id=creator_id,

        # 高级配置 - 修复NoneType错误
        storage_limit=practice_data.get("advanced_config", {}).get("storage_limit", "1Gi") if practice_data.get("advanced_config") else "1Gi",
        memory_limit=practice_data.get("advanced_config", {}).get("memory_limit", "1Gi") if practice_data.get("advanced_config") else "1Gi",
        cpu_limit=practice_data.get("advanced_config", {}).get("cpu_limit", "1") if practice_data.get("advanced_config") else "1",
        persistent_path=practice_data.get("advanced_config", {}).get("persistent_path") if practice_data.get("advanced_config") else None,
        
        # 默认配置
        enable_code_editor=True,
        enable_terminal=True,
        repo_visibility="visible",
        allow_skip_levels=True,
        is_published=False
    )
    
    db.add(practice)
    db.commit()
    db.refresh(practice)
    
    return practice

def update_custom_practice(
    db: Session,
    practice_id: int,
    practice_data: dict,
    creator_id: int
):
    """更新自定义实践"""
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return None
    
    # 更新字段
    if "title" in practice_data:
        practice.title = practice_data["title"]
    if "intro" in practice_data:
        practice.intro = practice_data["intro"]
    if "difficulty" in practice_data:
        practice.difficulty = practice_data["difficulty"]
    if "categories" in practice_data:
        practice.categories = json.dumps(practice_data["categories"])
    if "environment_id" in practice_data:
        practice.environment_id = practice_data["environment_id"]
    
    # 更新高级配置
    if "advanced_config" in practice_data:
        config = practice_data["advanced_config"]
        if "storage_limit" in config:
            practice.storage_limit = config["storage_limit"]
        if "memory_limit" in config:
            practice.memory_limit = config["memory_limit"]
        if "cpu_limit" in config:
            practice.cpu_limit = config["cpu_limit"]
        if "persistent_path" in config:
            practice.persistent_path = config["persistent_path"]
    
    db.commit()
    db.refresh(practice)
    
    return practice

def get_custom_practice_detail(db: Session, practice_id: int, creator_id: int):
    """获取自定义实践详情"""
    practice = db.query(models.Practice).options(
        joinedload(models.Practice.tasks),
        joinedload(models.Practice.code_repositories),
        joinedload(models.Practice.datasets),
        joinedload(models.Practice.creator)
    ).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    return practice

def get_practice_edit_page_data(db: Session, practice_id: int, creator_id: int):
    """获取实践任务编辑页面数据"""
    practice = get_custom_practice_detail(db, practice_id, creator_id)
    if not practice:
        return None
    
    # 构建四个页签的数据
    return {
        "task_tab": {
            "intro": practice.intro or "",
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "task_type": task.task_type.value,
                    "order_in_practice": task.order_in_practice,
                    "coin": task.coin,
                    "difficulty": task.difficulty
                }
                for task in sorted(practice.tasks, key=lambda x: x.order_in_practice)
            ]
        },
        "code_repo_tab": {
            "is_enabled": len(practice.code_repositories) > 0,
            "repository_url": practice.code_repositories[0].repository_url if practice.code_repositories else "",
            "branch_name": practice.code_repositories[0].branch_name if practice.code_repositories else "main"
        },
        "dataset_tab": {
            "datasets": [
                {
                    "id": dataset.id,
                    "name": dataset.name,
                    "file_type": dataset.file_type,
                    "file_size": dataset.file_size,
                    "description": dataset.description,
                    "access_url": dataset.access_url,
                    "created_at": dataset.created_at
                }
                for dataset in practice.datasets
            ]
        },
        "config_tab": {
            "enable_code_editor": practice.enable_code_editor,
            "enable_terminal": practice.enable_terminal,
            "repo_visibility": practice.repo_visibility,
            "allow_skip_levels": practice.allow_skip_levels
        }
    }

def create_practice_stage(
    db: Session,
    practice_id: int,
    stage_data: dict,
    creator_id: int
):
    """创建实践关卡"""
    # 验证实践所有权
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return None
    
    # 获取下一个排序号
    max_order = db.query(func.max(models.Task.order_in_practice)).filter(
        models.Task.practice_id == practice_id
    ).scalar() or 0
    
    # 创建任务
    task = models.Task(
        practice_id=practice_id,
        title=stage_data["title"],
        task_type=stage_data["task_type"],
        order_in_practice=max_order + 1,
        coin=stage_data.get("coin", 0),
        difficulty=stage_data.get("difficulty"),
        skills=json.dumps(stage_data.get("skills", [])),
        handbook_markdown=stage_data.get("handbook_markdown"),
        answer_content_markdown=stage_data.get("answer_content_markdown"),
        evaluation_script_path=stage_data.get("evaluation_script_path"),
        student_task_file_paths=json.dumps(stage_data.get("student_task_file_paths", [])),
        question_data=stage_data.get("question_data")
    )
    
    db.add(task)
    
    # 更新实践的任务数量和金币总数
    practice.task_count = practice.task_count + 1
    practice.coin = practice.coin + stage_data.get("coin", 0)
    
    db.commit()
    db.refresh(task)
    
    return task

def update_practice_code_repository(
    db: Session,
    practice_id: int,
    repo_data: dict,
    creator_id: int
):
    """更新实践代码仓库"""
    # 验证实践所有权
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return None
    
    # 查找或创建代码仓库记录
    repo = db.query(models.PracticeCodeRepository).filter(
        models.PracticeCodeRepository.practice_id == practice_id
    ).first()
    
    if repo:
        # 更新现有记录
        repo.repository_url = repo_data["repository_url"]
        repo.branch_name = repo_data.get("branch_name", "main")
        repo.is_enabled = repo_data.get("is_enabled", False)
    else:
        # 创建新记录
        repo = models.PracticeCodeRepository(
            practice_id=practice_id,
            repository_url=repo_data["repository_url"],
            branch_name=repo_data.get("branch_name", "main"),
            is_enabled=repo_data.get("is_enabled", False)
        )
        db.add(repo)
    
    db.commit()
    db.refresh(repo)
    
    return repo

def upload_practice_dataset(
    db: Session,
    practice_id: int,
    dataset_data: dict,
    creator_id: int
):
    """上传实践数据集"""
    # 验证实践所有权
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return None
    
    # 生成访问地址（用于代码中引用）
    access_url = f"/api/v1/practices/{practice_id}/datasets/{dataset_data['name']}"
    
    # 创建数据集记录
    dataset = models.PracticeDataset(
        practice_id=practice_id,
        name=dataset_data["name"],
        file_url=dataset_data["file_url"],
        file_type=dataset_data["file_type"],
        file_size=dataset_data["file_size"],
        description=dataset_data.get("description"),
        access_url=access_url,
        uploader_id=creator_id
    )
    
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    return dataset

def delete_practice_dataset(
    db: Session,
    practice_id: int,
    dataset_id: int,
    creator_id: int
):
    """删除实践数据集"""
    # 验证实践所有权
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return False
    
    # 删除数据集
    dataset = db.query(models.PracticeDataset).filter(
        models.PracticeDataset.id == dataset_id,
        models.PracticeDataset.practice_id == practice_id
    ).first()
    
    if dataset:
        db.delete(dataset)
        db.commit()
        return True
    
    return False

def update_practice_config(
    db: Session,
    practice_id: int,
    config_data: dict,
    creator_id: int
):
    """更新实践配置"""
    # 验证实践所有权
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return None
    
    # 更新配置
    if "enable_code_editor" in config_data:
        practice.enable_code_editor = config_data["enable_code_editor"]
    if "enable_terminal" in config_data:
        practice.enable_terminal = config_data["enable_terminal"]
    if "repo_visibility" in config_data:
        practice.repo_visibility = config_data["repo_visibility"]
    if "allow_skip_levels" in config_data:
        practice.allow_skip_levels = config_data["allow_skip_levels"]
    
    db.commit()
    db.refresh(practice)
    
    return practice

def update_standard_practice_config(
    db: Session,
    practice_id: int,
    config_data: dict,
    teacher_id: int
):
    """更新标准实践配置（支持教师权限检查）"""
    # 获取实践信息
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id
    ).first()
    
    if not practice:
        return None
    
    # 检查教师权限：
    # 1. 如果是自定义实践，检查创建者权限
    # 2. 如果是标准实践，检查是否有课堂使用权限（教师在课堂中使用了该实践）
    has_permission = False
    
    if practice.creator_id == teacher_id:
        # 创建者有权限
        has_permission = True
    else:
        # 检查是否在教师的课堂中使用了该实践
        classroom_practice = db.query(models.ClassroomPractice).join(
            models.Classroom
        ).filter(
            models.ClassroomPractice.practice_id == practice_id,
            models.Classroom.teacher_id == teacher_id
        ).first()
        
        if classroom_practice:
            has_permission = True
    
    if not has_permission:
        return None
    
    # 更新配置
    if "enable_code_editor" in config_data:
        practice.enable_code_editor = config_data["enable_code_editor"]
    if "enable_terminal" in config_data:
        practice.enable_terminal = config_data["enable_terminal"]
    if "repo_visibility" in config_data:
        practice.repo_visibility = config_data["repo_visibility"]
    if "allow_skip_levels" in config_data:
        practice.allow_skip_levels = config_data["allow_skip_levels"]
    
    # 更新时间戳
    practice.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(practice)
    
    return practice

def get_practice_config(
    db: Session,
    practice_id: int,
    teacher_id: int
):
    """获取实践配置（支持权限检查）"""
    # 获取实践信息
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id
    ).first()
    
    if not practice:
        return None
    
    # 检查教师权限
    has_permission = False
    
    if practice.creator_id == teacher_id:
        # 创建者有权限
        has_permission = True
    else:
        # 检查是否在教师的课堂中使用了该实践
        classroom_practice = db.query(models.ClassroomPractice).join(
            models.Classroom
        ).filter(
            models.ClassroomPractice.practice_id == practice_id,
            models.Classroom.teacher_id == teacher_id
        ).first()
        
        if classroom_practice:
            has_permission = True
    
    if not has_permission:
        return None
    
    return practice

def publish_custom_practice(
    db: Session,
    practice_id: int,
    creator_id: int,
    visibility: str = "private"
):
    """发布自定义实践"""
    from datetime import datetime, timezone
    
    # 验证实践所有权
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return None
    
    # 验证实践是否完整（至少有一个任务关卡）
    task_count = db.query(models.Task).filter(
        models.Task.practice_id == practice_id
    ).count()
    
    if task_count == 0:
        raise ValueError("实践至少需要包含一个任务关卡才能发布")
    
    # 检查当前状态是否允许发布
    if practice.publish_status == models.PracticePublishStatusEnum.PENDING_REVIEW:
        raise ValueError("实践正在审核中，无法重复提交")
    
    # 根据可见性设置发布状态
    visibility_lower = visibility.lower()
    if visibility_lower == "private":
        # 仅自己可见，直接发布
        practice.publish_status = models.PracticePublishStatusEnum.PUBLISHED
        practice.visibility = models.PracticeVisibilityEnum.PRIVATE
        practice.published_at = datetime.now(timezone.utc)
    elif visibility_lower == "public":
        # 公开发布，需要审核
        practice.publish_status = models.PracticePublishStatusEnum.PENDING_REVIEW
        practice.visibility = models.PracticeVisibilityEnum.PUBLIC
        practice.submitted_for_review_at = datetime.now(timezone.utc)
    else:
        raise ValueError("可见性参数必须是 private 或 public")
    
    # 保持向后兼容性
    practice.is_published = True
    
    db.commit()
    db.refresh(practice)
    
    return practice

def get_user_custom_practices(
    db: Session,
    creator_id: int,
    skip: int = 0,
    limit: int = 20
):
    """获取用户创建的自定义实践列表"""
    practices = db.query(models.Practice).filter(
        models.Practice.creator_id == creator_id
    ).offset(skip).limit(limit).all()
    
    total = db.query(models.Practice).filter(
        models.Practice.creator_id == creator_id
    ).count()
    
    return practices, total
# ==================== 课堂云盘增强功能 ====================

def batch_delete_cloud_files(
    db: Session,
    classroom_id: int,
    file_ids: List[int],
    teacher_id: int
):
    """批量删除云盘文件"""
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return False
    
    # 删除文件
    deleted_count = db.query(models.ClassroomCloudFile).filter(
        models.ClassroomCloudFile.classroom_id == classroom_id,
        models.ClassroomCloudFile.id.in_(file_ids)
    ).delete(synchronize_session=False)
    
    db.commit()
    
    return deleted_count

def get_cloud_file_preview_info(
    db: Session,
    classroom_id: int,
    file_id: int,
    teacher_id: int
):
    """获取云盘文件预览信息"""
    # 检查权限
    if not check_classroom_teacher_permission(db, classroom_id, teacher_id):
        return None
    
    file = db.query(models.ClassroomCloudFile).filter(
        models.ClassroomCloudFile.id == file_id,
        models.ClassroomCloudFile.classroom_id == classroom_id
    ).first()
    
    if not file:
        return None
    
    # 判断文件是否支持预览
    previewable_types = ["pdf", "jpg", "jpeg", "png", "gif", "txt", "md"]
    can_preview = file.file_type.lower() in previewable_types
    
    preview_message = None
    if not can_preview:
        preview_message = "当前文件不支持预览，请点击下载"
    
    return {
        "file_id": file.id,
        "file_name": file.name,
        "file_type": file.file_type,
        "preview_url": file.url if can_preview else None,
        "download_url": file.url,
        "can_preview": can_preview,
        "preview_message": preview_message
    }

def update_cloud_file_download_count(
    db: Session,
    file_id: int
):
    """更新云盘文件下载次数"""
    file = db.query(models.ClassroomCloudFile).filter(
        models.ClassroomCloudFile.id == file_id
    ).first()
    
    if file:
        file.download_count = file.download_count + 1
        db.commit()
        
    return file

# ==================== 代码仓库管理相关CRUD ====================

def init_practice_repository(
    db: Session,
    practice_id: int,
    creator_id: int
):
    """初始化实践代码仓库"""
    # 检查是否已存在代码仓库
    existing_repo = db.query(models.PracticeCodeRepository).filter(
        models.PracticeCodeRepository.practice_id == practice_id
    ).first()
    
    if existing_repo:
        return existing_repo
    
    # 创建新的代码仓库记录
    repo_url = f"git@internal:practice-{practice_id}.git"
    new_repo = models.PracticeCodeRepository(
        practice_id=practice_id,
        repository_url=repo_url,
        branch_name="main",
        is_enabled=True
    )
    
    db.add(new_repo)
    db.commit()
    db.refresh(new_repo)
    
    return new_repo


def get_practice_repository(
    db: Session,
    practice_id: int,
    creator_id: int
):
    """获取实践代码仓库信息"""
    # 检查权限
    practice = get_custom_practice_detail(db, practice_id, creator_id)
    if not practice:
        return None
    
    # 获取代码仓库
    repo = db.query(models.PracticeCodeRepository).filter(
        models.PracticeCodeRepository.practice_id == practice_id
    ).first()
    
    return repo


def get_repository_files(
    db: Session,
    practice_id: int,
    creator_id: int,
    path: str = ""
):
    """获取代码仓库文件列表"""
    repo = get_practice_repository(db, practice_id, creator_id)
    if not repo or not repo.is_enabled:
        return None
    
    # 模拟文件树结构（实际项目中应该调用Git API）
    # 这里返回一个示例文件结构
    base_files = [
        {
            "path": "README.md",
            "name": "README.md",
            "type": "file",
            "is_directory": False,
            "size": 1024,
            "last_modified": datetime.now(timezone.utc).isoformat()
        },
        {
            "path": "src",
            "name": "src",
            "type": "directory",
            "is_directory": True,
            "size": None,
            "last_modified": datetime.now(timezone.utc).isoformat()
        },
        {
            "path": "tests",
            "name": "tests",
            "type": "directory",
            "is_directory": True,
            "size": None,
            "last_modified": datetime.now(timezone.utc).isoformat()
        },
        {
            "path": "requirements.txt",
            "name": "requirements.txt",
            "type": "file",
            "is_directory": False,
            "size": 256,
            "last_modified": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # 如果指定了路径，返回该路径下的文件
    if path:
        # 模拟子目录文件
        if path == "src":
            return [
                {
                    "path": "src/main.py",
                    "name": "main.py",
                    "type": "file",
                    "is_directory": False,
                    "size": 512,
                    "last_modified": datetime.now(timezone.utc).isoformat()
                },
                {
                    "path": "src/utils.py",
                    "name": "utils.py",
                    "type": "file",
                    "is_directory": False,
                    "size": 256,
                    "last_modified": datetime.now(timezone.utc).isoformat()
                }
            ]
        elif path == "tests":
            return [
                {
                    "path": "tests/test_main.py",
                    "name": "test_main.py",
                    "type": "file",
                    "is_directory": False,
                    "size": 1024,
                    "last_modified": datetime.now(timezone.utc).isoformat()
                }
            ]
        else:
            return []
    
    return base_files


# 使用日志统计分析相关CRUD操作

def _get_time_range_filter(time_range: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    """获取时间范围过滤条件"""
    now = datetime.now(timezone.utc)
    
    if time_range == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end, "（今天）"
    elif time_range == "yesterday":
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end, f"（{yesterday.strftime('%Y.%m.%d')}）"
    elif time_range == "last_7_days":
        start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end, f"（{start.strftime('%Y.%m.%d')}~{end.strftime('%Y.%m.%d')}）"
    elif time_range == "last_30_days":
        start = (now - timedelta(days=29)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end, f"（{start.strftime('%Y.%m.%d')}~{end.strftime('%Y.%m.%d')}）"
    elif time_range == "custom" and start_date and end_date:
        return start_date, end_date, f"（{start_date.strftime('%Y.%m.%d')}~{end_date.strftime('%Y.%m.%d')}）"
    else:
        # 默认今天
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end, "（今天）"

def get_course_statistics(
    db: Session,
    time_range: str = "today",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取课程统计分析数据"""
    start_time, end_time, time_text = _get_time_range_filter(time_range, start_date, end_date)
    
    # 基础查询
    query = db.query(models.Course).filter(
        models.Course.course_type == models.CourseTypeEnum.COURSE_MATERIAL
    )
    
    # 关键词搜索
    if keyword:
        query = query.filter(models.Course.title.ilike(f"%{keyword}%"))
    
    # 获取课程列表
    courses = query.offset(skip).limit(limit).all()
    total_courses = query.count()
    
    # 统计概览数据
    total_count = db.query(models.Course).filter(
        models.Course.course_type == models.CourseTypeEnum.COURSE_MATERIAL
    ).count()
    
    # 内置课程数（假设来源为ADMIN的是内置课程）
    builtin_count = db.query(models.Course).filter(
        and_(
            models.Course.course_type == models.CourseTypeEnum.COURSE_MATERIAL,
            models.Course.visibility == models.CourseVisibilityEnum.PUBLIC_PLATFORM
        )
    ).count()
    
    # 教师公开课程数
    teacher_public_count = db.query(models.Course).filter(
        and_(
            models.Course.course_type == models.CourseTypeEnum.COURSE_MATERIAL,
            models.Course.visibility == models.CourseVisibilityEnum.PUBLIC_SELF
        )
    ).count()
    
    # 构建课程统计数据
    course_stats = []
    for course in courses:
        # 访问次数统计（模拟数据，实际需要日志表）
        access_count = 0
        access_users = 0
        classroom_creation_count = 0
        
        # 如果有日志表，使用真实数据
        try:
            access_count = db.query(models.CourseAccessLog).filter(
                and_(
                    models.CourseAccessLog.course_id == course.id,
                    models.CourseAccessLog.access_time >= start_time,
                    models.CourseAccessLog.access_time <= end_time
                )
            ).count()
            
            access_users = db.query(models.CourseAccessLog.user_id).filter(
                and_(
                    models.CourseAccessLog.course_id == course.id,
                    models.CourseAccessLog.access_time >= start_time,
                    models.CourseAccessLog.access_time <= end_time
                )
            ).distinct().count()
            
            classroom_creation_count = db.query(models.ClassroomCreationLog).filter(
                and_(
                    models.ClassroomCreationLog.course_id == course.id,
                    models.ClassroomCreationLog.created_time >= start_time,
                    models.ClassroomCreationLog.created_time <= end_time
                )
            ).count()
        except:
            # 如果表不存在，使用模拟数据
            access_count = course.id % 100  # 模拟访问次数
            access_users = course.id % 50   # 模拟访问人数
            classroom_creation_count = course.id % 10  # 模拟创建课堂次数
        
        # 人均访问次数
        avg_access = access_count / access_users if access_users > 0 else 0.0
        
        course_stats.append({
            "id": course.id,
            "title": course.title,
            "course_type": course.course_type,
            "course_type_cn": "课程教材",
            "access_count": access_count,
            "access_users": access_users,
            "avg_access_per_user": round(avg_access, 2),
            "classroom_creation_count": classroom_creation_count
        })
    
    return {
        "time_range_text": time_text,
        "total_courses": total_count,
        "builtin_courses": builtin_count,
        "teacher_public_courses": teacher_public_count,
        "courses": course_stats,
        "meta": {
            "total": total_courses,
            "page": (skip // limit) + 1,
            "page_size": limit
        }
    }

def get_practice_statistics(
    db: Session,
    time_range: str = "today",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_group: str = "teacher",
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取实践统计分析数据"""
    start_time, end_time, time_text = _get_time_range_filter(time_range, start_date, end_date)
    
    # 基础查询
    query = db.query(models.Practice)
    
    # 关键词搜索
    if keyword:
        query = query.filter(models.Practice.title.ilike(f"%{keyword}%"))
    
    # 获取实践列表
    practices = query.offset(skip).limit(limit).all()
    total_practices = query.count()
    
    # 构建实践统计数据
    practice_stats = []
    for practice in practices:
        # 模拟统计数据
        access_count = practice.id % 80
        access_users = practice.id % 40
        avg_access = access_count / access_users if access_users > 0 else 0.0
        
        # 教师端统计
        add_to_classroom_count = practice.id % 15 if user_group == "teacher" else 0
        
        # 学生端统计
        learning_count = practice.id % 60 if user_group == "student" else 0
        learning_duration = (practice.id % 3600) * 60 if user_group == "student" else 0  # 秒
        
        practice_stats.append({
            "id": practice.id,
            "title": practice.title,
            "access_count": access_count,
            "access_users": access_users,
            "avg_access_per_user": round(avg_access, 2),
            "teacher_add_to_classroom_count": add_to_classroom_count,
            "student_learning_count": learning_count,
            "student_learning_duration": learning_duration
        })
    
    return {
        "time_range_text": time_text,
        "user_group": user_group,
        "practices": practice_stats,
        "meta": {
            "total": total_practices,
            "page": (skip // limit) + 1,
            "page_size": limit
        }
    }

def get_training_statistics(
    db: Session,
    time_range: str = "today",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_group: str = "teacher",
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取实训统计分析数据"""
    start_time, end_time, time_text = _get_time_range_filter(time_range, start_date, end_date)
    
    # 基础查询
    query = db.query(models.Training)
    
    # 关键词搜索
    if keyword:
        query = query.filter(models.Training.title.ilike(f"%{keyword}%"))
    
    # 获取实训列表
    trainings = query.offset(skip).limit(limit).all()
    total_trainings = query.count()
    
    # 构建实训统计数据
    training_stats = []
    for training in trainings:
        # 模拟统计数据
        access_count = training.id % 70
        access_users = training.id % 35
        avg_access = access_count / access_users if access_users > 0 else 0.0
        
        # 教师端统计
        add_to_classroom_count = training.id % 12 if user_group == "teacher" else 0
        
        # 学生端统计
        learning_count = training.id % 50 if user_group == "student" else 0
        learning_duration = (training.id % 4800) * 60 if user_group == "student" else 0  # 秒
        
        training_stats.append({
            "id": training.id,
            "title": training.title,
            "access_count": access_count,
            "access_users": access_users,
            "avg_access_per_user": round(avg_access, 2),
            "teacher_add_to_classroom_count": add_to_classroom_count,
            "student_learning_count": learning_count,
            "student_learning_duration": learning_duration
        })
    
    return {
        "time_range_text": time_text,
        "user_group": user_group,
        "trainings": training_stats,
        "meta": {
            "total": total_trainings,
            "page": (skip // limit) + 1,
            "page_size": limit
        }
    }

def get_teacher_usage_statistics(
    db: Session,
    time_range: str = "today",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取教师使用统计数据"""
    start_time, end_time, time_text = _get_time_range_filter(time_range, start_date, end_date)
    
    # 基础查询 - 获取教师用户
    query = db.query(models.UserProfile).filter(
        models.UserProfile.user_type == models.UserTypeEnum.TEACHER
    )
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                models.UserProfile.real_name.ilike(f"%{keyword}%"),
                models.UserProfile.employee_id.ilike(f"%{keyword}%")
            )
        )
    
    # 获取教师列表
    teachers = query.offset(skip).limit(limit).all()
    total_teachers = query.count()
    
    # 构建教师统计数据
    teacher_stats = []
    for teacher in teachers:
        # 创建课堂数（状态量，当前时间节点的总数）
        classroom_count = db.query(models.Classroom).filter(
            models.Classroom.teacher_id == teacher.user_id
        ).count()
        
        # 创建实践数（当前时间节点的总数）
        practice_count = db.query(models.Practice).filter(
            models.Practice.creator_id == teacher.user_id
        ).count()
        
        # 个人发布实践数
        personal_practice_count = db.query(models.Practice).filter(
            and_(
                models.Practice.creator_id == teacher.user_id,
                models.Practice.visibility == models.PracticeVisibilityEnum.PRIVATE
            )
        ).count()
        
        # 公开发布实践数
        public_practice_count = db.query(models.Practice).filter(
            and_(
                models.Practice.creator_id == teacher.user_id,
                models.Practice.visibility == models.PracticeVisibilityEnum.PUBLIC
            )
        ).count()
        
        # 创建实训数
        training_count = db.query(models.Training).filter(
            models.Training.creator_id == teacher.user_id
        ).count()
        
        # 个人发布实训数
        personal_training_count = db.query(models.Training).filter(
            and_(
                models.Training.creator_id == teacher.user_id,
                models.Training.visibility == models.TrainingVisibilityEnum.PRIVATE
            )
        ).count()
        
        # 公开发布实训数
        public_training_count = db.query(models.Training).filter(
            and_(
                models.Training.creator_id == teacher.user_id,
                models.Training.visibility == models.TrainingVisibilityEnum.PUBLIC
            )
        ).count()
        
        teacher_stats.append({
            "id": teacher.id,
            "user_id": teacher.user_id,
            "real_name": teacher.real_name,
            "employee_id": teacher.employee_id,
            "organization_name": teacher.organization.name if teacher.organization else None,
            "classroom_count": classroom_count,
            "practice_count": practice_count,
            "personal_practice_count": personal_practice_count,
            "public_practice_count": public_practice_count,
            "training_count": training_count,
            "personal_training_count": personal_training_count,
            "public_training_count": public_training_count
        })
    
    return {
        "time_range_text": time_text,
        "teachers": teacher_stats,
        "meta": {
            "total": total_teachers,
            "page": (skip // limit) + 1,
            "page_size": limit
        }
    }

def get_student_usage_statistics(
    db: Session,
    time_range: str = "today",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取学生使用统计数据"""
    start_time, end_time, time_text = _get_time_range_filter(time_range, start_date, end_date)
    
    # 基础查询 - 获取学生用户
    query = db.query(models.UserProfile).filter(
        models.UserProfile.user_type == models.UserTypeEnum.STUDENT
    )
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                models.UserProfile.real_name.ilike(f"%{keyword}%"),
                models.UserProfile.employee_id.ilike(f"%{keyword}%")
            )
        )
    
    # 获取学生列表
    students = query.offset(skip).limit(limit).all()
    total_students = query.count()
    
    # 构建学生统计数据
    student_stats = []
    for student in students:
        # 模拟统计数据（实际应该从日志表查询）
        login_count = student.id % 30
        practice_start_count = student.id % 25
        practice_learning_duration = (student.id % 7200) * 60  # 秒
        resource_learning_duration = (student.id % 3600) * 60  # 秒
        training_start_count = student.id % 15
        training_learning_duration = (student.id % 5400) * 60  # 秒
        playground_project_count = student.id % 8
        
        student_stats.append({
            "id": student.id,
            "user_id": student.user_id,
            "real_name": student.real_name,
            "employee_id": student.employee_id,
            "organization_name": student.organization.name if student.organization else None,
            "login_count": login_count,
            "practice_start_count": practice_start_count,
            "practice_learning_duration": practice_learning_duration,
            "resource_learning_duration": resource_learning_duration,
            "training_start_count": training_start_count,
            "training_learning_duration": training_learning_duration,
            "playground_project_count": playground_project_count
        })
    
    return {
        "time_range_text": time_text,
        "students": student_stats,
        "meta": {
            "total": total_students,
            "page": (skip // limit) + 1,
            "page_size": limit
        }
    }

def get_course_detail_statistics(
    db: Session,
    course_id: int,
    time_range: str = "today",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_group: Optional[str] = None,
    name: Optional[str] = None,
    employee_id: Optional[str] = None,
    college: Optional[str] = None,
    major: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取课程详细统计数据（下钻页面）"""
    start_time, end_time, time_text = _get_time_range_filter(time_range, start_date, end_date)
    
    # 获取课程信息
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        return None
    
    # 基础查询 - 根据用户组筛选
    if user_group == "teacher":
        query = db.query(models.UserProfile).filter(
            models.UserProfile.user_type == models.UserTypeEnum.TEACHER
        )
    elif user_group == "student":
        query = db.query(models.UserProfile).filter(
            models.UserProfile.user_type == models.UserTypeEnum.STUDENT
        )
    else:
        query = db.query(models.UserProfile)
    
    # 筛选条件
    if name:
        query = query.filter(models.UserProfile.real_name.ilike(f"%{name}%"))
    if employee_id:
        query = query.filter(models.UserProfile.employee_id.ilike(f"%{employee_id}%"))
    if college:
        query = query.join(models.Organization).filter(
            models.Organization.name.ilike(f"%{college}%")
        )
    if major:
        query = query.join(models.Organization).filter(
            models.Organization.name.ilike(f"%{major}%")
        )
    
    # 获取用户列表
    users = query.offset(skip).limit(limit).all()
    total_users = query.count()
    
    # 构建用户统计数据
    user_stats = []
    for user in users:
        # 模拟统计数据
        access_count = user.id % 20
        learning_count = user.id % 15 if user.user_type == models.UserTypeEnum.STUDENT else 0
        learning_duration = (user.id % 3600) * 60 if user.user_type == models.UserTypeEnum.STUDENT else 0
        add_to_classroom_count = user.id % 8 if user.user_type == models.UserTypeEnum.TEACHER else 0
        
        user_stats.append({
            "user_id": user.user_id,
            "real_name": user.real_name,
            "employee_id": user.employee_id,
            "organization_name": user.organization.name if user.organization else None,
            "college": user.organization.name if user.organization and user.organization.org_type == models.OrganizationTypeEnum.COLLEGE else None,
            "major": user.organization.name if user.organization and user.organization.org_type == models.OrganizationTypeEnum.MAJOR else None,
            "access_count": access_count,
            "learning_count": learning_count,
            "learning_duration": learning_duration,
            "add_to_classroom_count": add_to_classroom_count
        })
    
    return {
        "course_id": course_id,
        "course_title": course.title,
        "time_range_text": time_text,
        "user_group": user_group,
        "users": user_stats,
        "meta": {
            "total": total_users,
            "page": (skip // limit) + 1,
            "page_size": limit
        }
    }

def export_statistics_data(
    db: Session,
    export_type: str,
    time_range: str = "today",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_group: Optional[str] = None,
    filters: Optional[dict] = None
):
    """导出统计数据"""
    import uuid
    
    # 生成导出文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{export_type}_statistics_{timestamp}.xlsx"
    
    # 模拟导出URL（实际应该生成真实的文件）
    export_url = f"/downloads/{filename}"
    
    # 根据导出类型获取数据
    if export_type == "course":
        data = get_course_statistics(db, time_range, start_date, end_date, 
                                   filters.get("keyword") if filters else None, 0, 1000)
        record_count = len(data["courses"])
    elif export_type == "practice":
        data = get_practice_statistics(db, time_range, start_date, end_date, 
                                     user_group or "teacher", 
                                     filters.get("keyword") if filters else None, 0, 1000)
        record_count = len(data["practices"])
    elif export_type == "training":
        data = get_training_statistics(db, time_range, start_date, end_date, 
                                     user_group or "teacher", 
                                     filters.get("keyword") if filters else None, 0, 1000)
        record_count = len(data["trainings"])
    elif export_type == "teacher":
        data = get_teacher_usage_statistics(db, time_range, start_date, end_date, 
                                          filters.get("keyword") if filters else None, 0, 1000)
        record_count = len(data["teachers"])
    elif export_type == "student":
        data = get_student_usage_statistics(db, time_range, start_date, end_date, 
                                          filters.get("keyword") if filters else None, 0, 1000)
        record_count = len(data["students"])
    else:
        record_count = 0
    
    return {
        "export_url": export_url,
        "filename": filename,
        "export_time": datetime.now(),
        "record_count": record_count
    }
# ==================== 环境会话管理 ====================

def get_user_active_environment(db: Session, user_id: int):
    """获取用户当前活跃的环境会话"""
    return db.query(models.EnvironmentSession).filter(
        and_(
            models.EnvironmentSession.user_id == user_id,
            models.EnvironmentSession.status == 'active'
        )
    ).options(
        joinedload(models.EnvironmentSession.practice)
    ).first()

def create_environment_session(db: Session, practice_id: int, user_id: int, environment_type: str):
    """创建新的环境会话"""
    # 先停止用户之前的所有活跃环境（如果系统不允许同时开启多个）。
    # 与 /environments/active 保持同一 SSOT: system_settings.concurrent_experiment_enabled。
    concurrent_setting = db.query(models.SystemSetting).filter(
        models.SystemSetting.key == 'concurrent_experiment_enabled'
    ).first()
    allow_multiple = (
        bool(concurrent_setting)
        and str(concurrent_setting.value).lower() == 'true'
    )

    if not allow_multiple:
        # 停止所有活跃环境
        db.query(models.EnvironmentSession).filter(
            and_(
                models.EnvironmentSession.user_id == user_id,
                models.EnvironmentSession.status == 'active'
            )
        ).update({"status": "stopped", "stopped_at": datetime.now(timezone.utc)})

    # 创建新的环境会话
    env_session = models.EnvironmentSession(
        practice_id=practice_id,
        user_id=user_id,
        environment_type=environment_type,
        status='active',
        created_at=datetime.now(timezone.utc)
    )

    db.add(env_session)
    db.commit()
    db.refresh(env_session)
    return env_session

def stop_environment_session(db: Session, environment_id: str, user_id: int):
    """停止指定的环境会话"""
    result = db.query(models.EnvironmentSession).filter(
        and_(
            models.EnvironmentSession.id == environment_id,
            models.EnvironmentSession.user_id == user_id,
            models.EnvironmentSession.status == 'active'
        )
    ).update({
        "status": "stopped",
        "stopped_at": datetime.now(timezone.utc)
    })

    db.commit()
    return result > 0


def get_course_grades_with_stats(
    db: Session,
    classroom_course_id: int,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取课程成绩列表 (Phase C-2 真融合 fc 自动评测 task_evaluation_results)

    返回 list of dicts (不再返 SQLAlchemy objects), 调用方 classrooms.py:1492
    PRACTICE 分支用 dict accessor 构建 frontend grade_data.

    PRACTICE 课程: 拉 ClassroomStudent 全列 + TER latest per (user_id, task_id),
    融合 SCP manual + auto 数据. 没 SCP 行的学生也包含 (auto-only).
    其他 (TRAINING / 没 practice_id) 走老逻辑只读 SCP, 字段名兼容.
    """
    # 取 classroom_course 看是否 PRACTICE + 找 practice_id + classroom_id
    classroom_course = db.query(models.ClassroomCourse).options(
        joinedload(models.ClassroomCourse.course)
    ).filter(models.ClassroomCourse.id == classroom_course_id).first()
    is_practice = (
        classroom_course
        and classroom_course.practice_id is not None
        and (
            classroom_course.course is None
            or classroom_course.course.course_type == models.CourseTypeEnum.PRACTICE
        )
    )
    practice_id = classroom_course.practice_id if classroom_course else None
    classroom_id_v = classroom_course.classroom_id if classroom_course else None

    # PRACTICE + 有 practice_id: 用融合逻辑
    if is_practice and practice_id and classroom_id_v:
        # 1) tasks (排除已删除)
        task_rows = db.query(models.Task.id, models.Task.coin).filter(
            models.Task.practice_id == practice_id,
            models.Task.deleted_at.is_(None),
        ).all()
        task_ids = [t.id for t in task_rows]
        total_coin = sum((t.coin or 0) for t in task_rows)
        total_tasks_n = len(task_rows)

        # 2) classroom 学生
        students_q = db.query(models.ClassroomStudent.student_id, models.User).join(
            models.User, models.User.id == models.ClassroomStudent.student_id
        ).filter(models.ClassroomStudent.classroom_id == classroom_id_v).all()
        student_user_by_id = {sid: user for sid, user in students_q}
        student_ids = list(student_user_by_id.keys())

        # 3) TER latest per (user_id, task_id)
        ter_by_student = {}
        if student_ids and task_ids:
            ter_rows = db.query(models.TaskEvaluationResult).filter(
                models.TaskEvaluationResult.user_id.in_(student_ids),
                models.TaskEvaluationResult.task_id.in_(task_ids),
            ).distinct(
                models.TaskEvaluationResult.user_id,
                models.TaskEvaluationResult.task_id,
            ).order_by(
                models.TaskEvaluationResult.user_id,
                models.TaskEvaluationResult.task_id,
                models.TaskEvaluationResult.created_at.desc(),
            ).all()
            for ter in ter_rows:
                ter_by_student.setdefault(ter.user_id, []).append(ter)

        # 4) SCP rows
        scps = db.query(models.StudentCourseProgress).options(
            joinedload(models.StudentCourseProgress.student),
            joinedload(models.StudentCourseProgress.graded_by_teacher),
        ).filter(models.StudentCourseProgress.classroom_course_id == classroom_course_id).all()
        scp_by_student = {s.student_id: s for s in scps}

        # 5) 聚合每学生为 dict
        def auto_metrics(sid):
            ters = ter_by_student.get(sid, [])
            completed = sum(1 for t in ters if t.status == 'pass')
            score_sum = sum((t.score or 0) for t in ters if t.status == 'pass')
            score_pct = round(score_sum / total_coin * 100, 1) if total_coin else None
            last_at = max((t.created_at for t in ters), default=None)
            return completed, score_pct, last_at

        def derive(sid, scp, auto_completed):
            if scp and scp.graded_at:
                return "GRADED"
            if total_tasks_n > 0 and auto_completed == total_tasks_n:
                return "AUTO_COMPLETED"
            if auto_completed > 0:
                return "PARTIAL"
            return "NOT_STARTED"

        rows = []
        for sid, user in student_user_by_id.items():
            scp = scp_by_student.get(sid)
            auto_completed, auto_score_pct, auto_last_at = auto_metrics(sid)
            derived_status = derive(sid, scp, auto_completed)

            # SCP 字段优先, auto 补缺
            completed_tasks_v = (scp.completed_task_count if scp and scp.completed_task_count else auto_completed)
            submission_at_v = (scp.last_submission_at if scp and scp.last_submission_at else auto_last_at)
            task_score_v = (scp.overall_score if scp and scp.overall_score is not None else auto_score_pct)
            current_score_v = (
                scp.final_calculated_score if scp and scp.final_calculated_score is not None
                else (auto_score_pct if auto_completed > 0 else None)
            )
            student_status_v = (scp.student_status.value if scp and scp.student_status else None)
            # 派生 student_status 给 frontend (无 SCP 时按 auto 给)
            if not student_status_v:
                if derived_status == "AUTO_COMPLETED":
                    student_status_v = "COMPLETED_ON_TIME"
                elif derived_status == "PARTIAL":
                    student_status_v = "LEARNING"
                else:
                    student_status_v = "NOT_STARTED"

            rows.append({
                "id": scp.id if scp else None,
                "student_id": sid,
                "student": user,           # 保留 SQLAlchemy User 给 classrooms.py 用
                "student_status_value": student_status_v,
                "training_submission_status_value": (
                    scp.training_submission_status.value if scp and scp.training_submission_status else None
                ),
                "completed_task_count": completed_tasks_v,
                "total_tasks": total_tasks_n,
                "overall_score": (scp.overall_score if scp else None),
                "task_score_v": task_score_v,
                "teacher_penalties": (scp.teacher_penalties or 0) if scp else 0,
                "final_calculated_score": (scp.final_calculated_score if scp else None),
                "current_score": current_score_v,
                "last_submission_at": submission_at_v,
                "total_time_spent_seconds": (scp.total_time_spent_seconds if scp else None),
                "graded_at": (scp.graded_at if scp else None),
                "teacher_feedback": (scp.teacher_feedback if scp else None),
                "is_excellent_work": (scp.is_excellent_work if scp else False),
                "auto_completed_tasks": auto_completed,
                "auto_score": auto_score_pct,
                "last_evaluation_at": auto_last_at,
                "derived_status": derived_status,
            })

        # 6) status filter
        # Codex 审计 P1 修: 兼容两套命名 ("completed/learning" 与
        # "completed_on_time/not_completed"). frontend UI 文档 + grades.py:31
        # endpoint description 用长形式 ("completed_on_time/completed_late/not_completed"),
        # crud.get_course_grades (Phase C) 接长形式. classrooms.py:1492 + 此函数
        # (Phase C-2) 老代码用短形式. 现在 _match 同时接受两套, 命中即过滤.
        if status and status != "all":
            def _match(r):
                ss = r["student_status_value"]
                if status in ("not_started",):
                    return ss == "NOT_STARTED"
                if status in ("learning", "not_completed"):
                    return ss == "LEARNING"
                if status in ("completed", "completed_on_time"):
                    return ss == "COMPLETED_ON_TIME"
                if status in ("late_completed", "completed_late"):
                    return ss == "COMPLETED_LATE"
                # training-only 状态对 PRACTICE 不适用, 不匹配
                return False
            rows = [r for r in rows if _match(r)]

        # 7) keyword (学生姓名/学号)
        if keyword:
            kw = keyword.lower()
            rows = [r for r in rows if (r["student"].full_name or "").lower().find(kw) >= 0
                    or (r["student"].username or "").lower().find(kw) >= 0]

        total = len(rows)
        rows = rows[skip:skip + limit]
        return rows, total

    # TRAINING / 无 practice 走老逻辑 (返 SQLAlchemy objects, 兼容 classrooms.py 老分支)
    query = db.query(models.StudentCourseProgress).options(
        joinedload(models.StudentCourseProgress.student)
    ).filter(models.StudentCourseProgress.classroom_course_id == classroom_course_id)

    # R1: 同 PRACTICE 分支兼容双命名 (frontend long form + 老 short form 都接受)
    if status and status != "all":
        if status == "not_started":
            query = query.filter(models.StudentCourseProgress.student_status == models.CourseInClassroomStatusStudentEnum.NOT_STARTED)
        elif status in ("learning", "not_completed"):
            query = query.filter(models.StudentCourseProgress.student_status == models.CourseInClassroomStatusStudentEnum.LEARNING)
        elif status in ("completed", "completed_on_time"):
            query = query.filter(models.StudentCourseProgress.student_status == models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME)
        elif status in ("late_completed", "completed_late"):
            query = query.filter(models.StudentCourseProgress.student_status == models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE)
        elif status == "submitted":
            query = query.filter(models.StudentCourseProgress.training_submission_status == models.SubmissionStatusEnum.SUBMITTED)
        elif status in ("late_submitted", "submitted_late"):
            query = query.filter(models.StudentCourseProgress.training_submission_status == models.SubmissionStatusEnum.LATE_SUBMISSION)

    if keyword:
        query = query.join(models.User).filter(
            models.User.full_name.ilike(f"%{keyword}%") |
            models.User.username.ilike(f"%{keyword}%")
        )

    total = query.count()
    grades = query.offset(skip).limit(limit).all()
    return grades, total
