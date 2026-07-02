from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, timezone

from app.models import models
from app.schemas import schemas


def get_excellent_works_navigation_tree(db: Session, user_id: int, user_role: str = "student"):
    """获取优秀作业导航树"""
    from app.core.cache import get_cache

    # 生成缓存键
    cache_key = f"excellent_works:nav_tree:{user_id}:{user_role}"

    # 尝试从缓存获取
    cache = get_cache()
    cached_result = cache.get_excellent_work_stats(cache_key)
    if cached_result:
        return cached_result
    # 根据用户角色确定可访问的课堂
    if user_role == "teacher":
        # 教师可以看到自己教授的课堂
        classrooms = db.query(models.Classroom).filter(
            models.Classroom.teacher_id == user_id,
            models.Classroom.deleted_at.is_(None)
        ).all()
    elif user_role == "admin":
        # 管理员可以看到所有课堂（有优秀作业的）
        # 首先找到有优秀作业的classroom_practice和classroom_training
        excellent_practice_classrooms = db.query(models.ClassroomPractice.classroom_id).select_from(
            models.ClassroomPractice
        ).join(
            models.StudentCourseProgress,
            models.StudentCourseProgress.classroom_course_id == models.ClassroomPractice.id
        ).filter(models.StudentCourseProgress.is_excellent_work == True).distinct().subquery()

        excellent_training_classrooms = db.query(models.ClassroomTraining.classroom_id).select_from(
            models.ClassroomTraining
        ).join(
            models.StudentCourseProgress,
            models.StudentCourseProgress.classroom_course_id == models.ClassroomTraining.id
        ).filter(models.StudentCourseProgress.is_excellent_work == True).distinct().subquery()

        practice_classrooms = db.query(excellent_practice_classrooms.c.classroom_id)
        training_classrooms = db.query(excellent_training_classrooms.c.classroom_id)

        all_classroom_ids = practice_classrooms.union(training_classrooms).subquery()

        classrooms = db.query(models.Classroom).filter(
            models.Classroom.id.in_(all_classroom_ids),
            models.Classroom.deleted_at.is_(None)
        ).all()
    else:
        # 学生可以看到自己参与的课堂
        classroom_students = db.query(models.ClassroomStudent).filter(
            models.ClassroomStudent.student_id == user_id
        ).all()
        classroom_ids = [cs.classroom_id for cs in classroom_students]
        classrooms = db.query(models.Classroom).filter(
            models.Classroom.id.in_(classroom_ids),
            models.Classroom.deleted_at.is_(None)
        ).all() if classroom_ids else []
    
    tree = []
    for classroom in classrooms:
        # 获取课堂下的practices和trainings及其优秀作业数量
        classroom_practices = db.query(models.ClassroomPractice).options(
            joinedload(models.ClassroomPractice.practice)
        ).filter(
            models.ClassroomPractice.classroom_id == classroom.id
        ).all()

        classroom_trainings = db.query(models.ClassroomTraining).options(
            joinedload(models.ClassroomTraining.training)
        ).filter(
            models.ClassroomTraining.classroom_id == classroom.id
        ).all()

        total_course_count = len(classroom_practices) + len(classroom_trainings)

        classroom_node = {
            "id": classroom.id,
            "name": f"{classroom.name}-{classroom.semester or ''}",
            "type": "classroom",
            "course_count": total_course_count,
            "semester": classroom.semester,
            "children": []
        }

        # 处理practices
        for cp in classroom_practices:
            # 统计该practice的优秀作业数量
            excellent_count = db.query(models.StudentCourseProgress).filter(
                models.StudentCourseProgress.classroom_course_id == cp.id,
                models.StudentCourseProgress.is_excellent_work == True,
                models.StudentCourseProgress.graded_at.isnot(None)
            ).count()

            if excellent_count > 0:  # 只显示有优秀作业的课程
                course_node = {
                    "id": cp.id,
                    "name": cp.practice.title,
                    "type": "course",
                    "excellent_count": excellent_count,
                    "course_type": "PRACTICE",
                    "children": []
                }
                classroom_node["children"].append(course_node)

        # 处理trainings
        for ct in classroom_trainings:
            # 统计该training的优秀作业数量
            excellent_count = db.query(models.StudentCourseProgress).filter(
                models.StudentCourseProgress.classroom_course_id == ct.id,
                models.StudentCourseProgress.is_excellent_work == True,
                models.StudentCourseProgress.graded_at.isnot(None)
            ).count()

            if excellent_count > 0:  # 只显示有优秀作业的课程
                course_node = {
                    "id": ct.id,
                    "name": ct.training.title,
                    "type": "course",
                    "excellent_count": excellent_count,
                    "course_type": "TRAINING",
                    "children": []
                }
                classroom_node["children"].append(course_node)

        if classroom_node["children"]:  # 只显示有优秀作业的课堂
            tree.append(classroom_node)

    # 缓存导航树结果 (10分钟缓存，因为导航树变化不频繁)
    cache.set_excellent_work_stats(cache_key, tree, ttl=600)

    return tree


def get_excellent_works_list(
    db: Session,
    user_id: int,
    user_role: str = "student",
    classroom_id: Optional[int] = None,
    course_id: Optional[int] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取优秀作业列表"""
    from app.core.cache import get_cache

    # 生成缓存键
    cache_key = f"excellent_works:list:{user_id}:{user_role}:{classroom_id or 'all'}:{course_id or 'all'}:{keyword or 'none'}:{skip}:{limit}"

    # 尝试从缓存获取
    cache = get_cache()
    cached_result = cache.get_excellent_work_stats(cache_key)
    if cached_result:
        return cached_result

    # 基础查询 - 处理practices和trainings的关联
    query = db.query(models.StudentCourseProgress).options(
        joinedload(models.StudentCourseProgress.student),
        joinedload(models.StudentCourseProgress.graded_by_teacher)
    ).filter(
        models.StudentCourseProgress.is_excellent_work == True,
        models.StudentCourseProgress.graded_at.isnot(None)
    )

    # 权限过滤和关联处理
    if user_role == "student":
        # 学生只能看到自己参与的课堂的优秀作业
        classroom_students = db.query(models.ClassroomStudent).filter(
            models.ClassroomStudent.student_id == user_id
        ).all()
        classroom_ids = [cs.classroom_id for cs in classroom_students]
        if classroom_ids:
            # 同时检查practices和trainings的关联
            practice_query = db.query(models.StudentCourseProgress.id).select_from(
                models.StudentCourseProgress
            ).join(
                models.ClassroomPractice,
                models.StudentCourseProgress.classroom_course_id == models.ClassroomPractice.id
            ).filter(models.ClassroomPractice.classroom_id.in_(classroom_ids))

            training_query = db.query(models.StudentCourseProgress.id).select_from(
                models.StudentCourseProgress
            ).join(
                models.ClassroomTraining,
                models.StudentCourseProgress.classroom_course_id == models.ClassroomTraining.id
            ).filter(models.ClassroomTraining.classroom_id.in_(classroom_ids))

            query = query.filter(
                models.StudentCourseProgress.id.in_(practice_query.union(training_query))
            )
        else:
            return {"list": [], "total": 0}
    elif user_role == "teacher":
        # 教师只能看到自己教授的课堂的优秀作业
        practice_query = db.query(models.StudentCourseProgress.id).select_from(
            models.StudentCourseProgress
        ).join(
            models.ClassroomPractice,
            models.StudentCourseProgress.classroom_course_id == models.ClassroomPractice.id
        ).join(models.Classroom, models.Classroom.id == models.ClassroomPractice.classroom_id).filter(models.Classroom.teacher_id == user_id)

        training_query = db.query(models.StudentCourseProgress.id).select_from(
            models.StudentCourseProgress
        ).join(
            models.ClassroomTraining,
            models.StudentCourseProgress.classroom_course_id == models.ClassroomTraining.id
        ).join(models.Classroom, models.Classroom.id == models.ClassroomTraining.classroom_id).filter(models.Classroom.teacher_id == user_id)

        query = query.filter(
            models.StudentCourseProgress.id.in_(practice_query.union(training_query))
        )
    # 管理员可以看到所有优秀作业，无需额外过滤

    # 课堂筛选
    if classroom_id:
        practice_query = db.query(models.StudentCourseProgress.id).select_from(
            models.StudentCourseProgress
        ).join(
            models.ClassroomPractice,
            models.StudentCourseProgress.classroom_course_id == models.ClassroomPractice.id
        ).filter(models.ClassroomPractice.classroom_id == classroom_id)

        training_query = db.query(models.StudentCourseProgress.id).select_from(
            models.StudentCourseProgress
        ).join(
            models.ClassroomTraining,
            models.StudentCourseProgress.classroom_course_id == models.ClassroomTraining.id
        ).filter(models.ClassroomTraining.classroom_id == classroom_id)

        query = query.filter(
            models.StudentCourseProgress.id.in_(practice_query.union(training_query))
        )

    # 课程筛选（这里course_id实际上是classroom_practice_id或classroom_training_id）
    if course_id:
        query = query.filter(models.StudentCourseProgress.classroom_course_id == course_id)

    # 关键词搜索（搜索课程标题）
    if keyword:
        # 通过关联查询找到匹配的课程标题
        practice_query = db.query(models.StudentCourseProgress.id).select_from(
            models.StudentCourseProgress
        ).join(
            models.ClassroomPractice,
            models.StudentCourseProgress.classroom_course_id == models.ClassroomPractice.id
        ).join(models.Practice, models.Practice.id == models.ClassroomPractice.practice_id).filter(models.Practice.title.ilike(f"%{keyword}%"))

        training_query = db.query(models.StudentCourseProgress.id).select_from(
            models.StudentCourseProgress
        ).join(
            models.ClassroomTraining,
            models.StudentCourseProgress.classroom_course_id == models.ClassroomTraining.id
        ).join(models.Training, models.Training.id == models.ClassroomTraining.training_id).filter(models.Training.title.ilike(f"%{keyword}%"))

        query = query.filter(
            models.StudentCourseProgress.id.in_(practice_query.union(training_query))
        )
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    excellent_works = query.order_by(
        models.StudentCourseProgress.graded_at.desc()
    ).offset(skip).limit(limit).all()
    
    # 构建响应数据
    excellent_list = []
    for progress in excellent_works:
        # 统计阅读量
        view_count = db.query(models.ExcellentWorkView).filter(
            models.ExcellentWorkView.student_progress_id == progress.id
        ).count()
        
        # 统计点赞数
        like_count = db.query(models.ExcellentWorkLike).filter(
            models.ExcellentWorkLike.student_progress_id == progress.id
        ).count()
        
        # 检查当前用户是否已点赞
        is_liked = db.query(models.ExcellentWorkLike).filter(
            models.ExcellentWorkLike.student_progress_id == progress.id,
            models.ExcellentWorkLike.user_id == user_id
        ).first() is not None
        
        # 检查当前用户是否已收藏
        is_favorited = db.query(models.ExcellentWorkFavorite).filter(
            models.ExcellentWorkFavorite.student_progress_id == progress.id,
            models.ExcellentWorkFavorite.user_id == user_id
        ).first() is not None
        
        # 获取课程信息
        course_info = None
        classroom_info = None

        # 尝试从ClassroomPractice获取信息
        classroom_practice = db.query(models.ClassroomPractice).filter(
            models.ClassroomPractice.id == progress.classroom_course_id
        ).first()

        if classroom_practice:
            practice = db.query(models.Practice).filter(
                models.Practice.id == classroom_practice.practice_id
            ).first()
            classroom = db.query(models.Classroom).filter(
                models.Classroom.id == classroom_practice.classroom_id
            ).first()

            if practice and classroom:
                course_info = {
                    "id": classroom_practice.id,
                    "course_id": practice.id,
                    "course_name": practice.title,
                    "course_type": "PRACTICE"
                }
                classroom_info = {
                    "id": classroom.id,
                    "name": classroom.name
                }
        else:
            # 尝试从ClassroomTraining获取信息
            classroom_training = db.query(models.ClassroomTraining).filter(
                models.ClassroomTraining.id == progress.classroom_course_id
            ).first()

            if classroom_training:
                training = db.query(models.Training).filter(
                    models.Training.id == classroom_training.training_id
                ).first()
                classroom = db.query(models.Classroom).filter(
                    models.Classroom.id == classroom_training.classroom_id
                ).first()

                if training and classroom:
                    course_info = {
                        "id": classroom_training.id,
                        "course_id": training.id,
                        "course_name": training.title,
                        "course_type": "TRAINING"
                    }
                    classroom_info = {
                        "id": classroom.id,
                        "name": classroom.name
                    }

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
            "view_count": view_count,
            "like_count": like_count,
            "is_liked": is_liked,
            "is_favorited": is_favorited,
            "course_info": course_info,
            "classroom_info": classroom_info
        }
        
        excellent_list.append(excellent_work)

    result = {
        "list": excellent_list,
        "total": total
    }

    # 缓存结果 (只缓存前几页的热门查询)
    if skip == 0 and limit <= 50 and not keyword:  # 只缓存首页和无搜索的查询
        cache.set_excellent_work_stats(cache_key, result, ttl=300)  # 5分钟缓存

    return result


def get_excellent_work_detail(db: Session, work_id: int, user_id: int, user_role: str = "student"):
    """获取优秀作业详情"""
    # 获取优秀作业
    progress = db.query(models.StudentCourseProgress).options(
        joinedload(models.StudentCourseProgress.student),
        joinedload(models.StudentCourseProgress.graded_by_teacher),
        joinedload(models.StudentCourseProgress.classroom_course),
        joinedload(models.StudentCourseProgress.classroom_course, models.ClassroomCourse.course),
        joinedload(models.StudentCourseProgress.classroom_course, models.ClassroomCourse.classroom)
    ).filter(
        models.StudentCourseProgress.id == work_id,
        models.StudentCourseProgress.is_excellent_work == True,
        models.StudentCourseProgress.graded_at.isnot(None)
    ).first()
    
    if not progress:
        return None
    
    # 权限检查
    if user_role == "student":
        # 检查学生是否在此课堂中
        student_in_classroom = db.query(models.ClassroomStudent).filter(
            models.ClassroomStudent.classroom_id == progress.classroom_course.classroom_id,
            models.ClassroomStudent.student_id == user_id
        ).first()
        if not student_in_classroom:
            return None
    elif user_role == "teacher":
        # 检查教师是否是此课堂的教师
        if progress.classroom_course.classroom.teacher_id != user_id:
            return None
    
    # 记录浏览
    record_excellent_work_view(db, work_id, user_id)
    
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
    
    # 统计信息
    view_count = db.query(models.ExcellentWorkView).filter(
        models.ExcellentWorkView.student_progress_id == work_id
    ).count()
    
    like_count = db.query(models.ExcellentWorkLike).filter(
        models.ExcellentWorkLike.student_progress_id == work_id
    ).count()
    
    is_liked = db.query(models.ExcellentWorkLike).filter(
        models.ExcellentWorkLike.student_progress_id == work_id,
        models.ExcellentWorkLike.user_id == user_id
    ).first() is not None
    
    is_favorited = db.query(models.ExcellentWorkFavorite).filter(
        models.ExcellentWorkFavorite.student_progress_id == work_id,
        models.ExcellentWorkFavorite.user_id == user_id
    ).first() is not None
    
    return {
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
        "course_name": progress.classroom_course.course.title,
        "course_type": progress.classroom_course.course.course_type.value,
        "classroom_name": progress.classroom_course.classroom.name,
        "view_count": view_count,
        "like_count": like_count,
        "is_liked": is_liked,
        "is_favorited": is_favorited
    }


def record_excellent_work_view(db: Session, work_id: int, user_id: Optional[int] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
    """记录优秀作业浏览"""
    # 创建浏览记录
    view_record = models.ExcellentWorkView(
        student_progress_id=work_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(view_record)
    db.commit()
    return view_record


def toggle_excellent_work_like(db: Session, work_id: int, user_id: int, action: str):
    """切换优秀作业点赞状态"""
    from app.core.cache import get_cache

    # 检查作业是否存在
    progress = db.query(models.StudentCourseProgress).filter(
        models.StudentCourseProgress.id == work_id,
        models.StudentCourseProgress.is_excellent_work == True
    ).first()

    if not progress:
        return None

    # 使用数据库行级锁确保原子性操作
    db.execute("SELECT 1 FROM student_course_progress WHERE id = :work_id FOR UPDATE",
               {"work_id": work_id})

    # 检查现有点赞记录
    existing_like = db.query(models.ExcellentWorkLike).filter(
        models.ExcellentWorkLike.student_progress_id == work_id,
        models.ExcellentWorkLike.user_id == user_id
    ).first()

    if action == "like":
        if not existing_like:
            # 添加点赞
            like_record = models.ExcellentWorkLike(
                student_progress_id=work_id,
                user_id=user_id
            )
            db.add(like_record)
            is_active = True
        else:
            is_active = True
    elif action == "unlike":
        if existing_like:
            # 取消点赞
            db.delete(existing_like)
            is_active = False
        else:
            is_active = False
    else:
        return None

    # 提交事务
    db.commit()

    # 获取当前点赞数
    current_count = db.query(models.ExcellentWorkLike).filter(
        models.ExcellentWorkLike.student_progress_id == work_id
    ).count()

    # 使相关缓存失效
    cache = get_cache()
    # 清除优秀作业列表缓存
    cache.invalidate_excellent_work_stats(work_id)
    # 清除用户相关缓存
    cache.invalidate_user_practices(user_id)

    return {
        "success": True,
        "action": action,
        "current_count": current_count,
        "is_active": is_active
    }


def toggle_excellent_work_favorite(db: Session, work_id: int, user_id: int, action: str):
    """切换优秀作业收藏状态"""
    from app.core.cache import get_cache

    # 检查作业是否存在
    progress = db.query(models.StudentCourseProgress).filter(
        models.StudentCourseProgress.id == work_id,
        models.StudentCourseProgress.is_excellent_work == True
    ).first()

    if not progress:
        return None

    # 使用数据库行级锁确保原子性操作
    db.execute("SELECT 1 FROM student_course_progress WHERE id = :work_id FOR UPDATE",
               {"work_id": work_id})

    # 检查现有收藏记录
    existing_favorite = db.query(models.ExcellentWorkFavorite).filter(
        models.ExcellentWorkFavorite.student_progress_id == work_id,
        models.ExcellentWorkFavorite.user_id == user_id
    ).first()

    if action == "favorite":
        if not existing_favorite:
            # 添加收藏
            favorite_record = models.ExcellentWorkFavorite(
                student_progress_id=work_id,
                user_id=user_id
            )
            db.add(favorite_record)
            is_active = True
        else:
            is_active = True
    elif action == "unfavorite":
        if existing_favorite:
            # 取消收藏
            db.delete(existing_favorite)
            is_active = False
        else:
            is_active = False
    else:
        return None

    # 提交事务
    db.commit()

    # 获取当前收藏数
    current_count = db.query(models.ExcellentWorkFavorite).filter(
        models.ExcellentWorkFavorite.student_progress_id == work_id
    ).count()

    # 使相关缓存失效
    cache = get_cache()
    # 清除优秀作业列表缓存
    cache.invalidate_excellent_work_stats(work_id)
    # 清除用户相关缓存
    cache.invalidate_user_practices(user_id)

    return {
        "success": True,
        "action": action,
        "current_count": current_count,
        "is_active": is_active
    }


def get_my_favorite_works(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20
):
    """获取我收藏的优秀作业列表"""
    # 查询收藏记录
    favorites = db.query(models.ExcellentWorkFavorite).options(
        joinedload(models.ExcellentWorkFavorite.student_progress),
        joinedload(models.ExcellentWorkFavorite.student_progress, models.StudentCourseProgress.student),
        joinedload(models.ExcellentWorkFavorite.student_progress, models.StudentCourseProgress.graded_by_teacher),
        joinedload(models.ExcellentWorkFavorite.student_progress, models.StudentCourseProgress.classroom_course),
        joinedload(models.ExcellentWorkFavorite.student_progress, models.StudentCourseProgress.classroom_course, models.ClassroomCourse.course),
        joinedload(models.ExcellentWorkFavorite.student_progress, models.StudentCourseProgress.classroom_course, models.ClassroomCourse.classroom)
    ).filter(
        models.ExcellentWorkFavorite.user_id == user_id
    ).order_by(
        models.ExcellentWorkFavorite.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    # 获取总数
    total = db.query(models.ExcellentWorkFavorite).filter(
        models.ExcellentWorkFavorite.user_id == user_id
    ).count()
    
    # 构建响应数据
    favorite_list = []
    for favorite in favorites:
        progress = favorite.student_progress
        
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
        
        # 统计信息
        view_count = db.query(models.ExcellentWorkView).filter(
            models.ExcellentWorkView.student_progress_id == progress.id
        ).count()
        
        like_count = db.query(models.ExcellentWorkLike).filter(
            models.ExcellentWorkLike.student_progress_id == progress.id
        ).count()
        
        is_liked = db.query(models.ExcellentWorkLike).filter(
            models.ExcellentWorkLike.student_progress_id == progress.id,
            models.ExcellentWorkLike.user_id == user_id
        ).first() is not None
        
        favorite_work = {
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
            "course_name": progress.classroom_course.course.title,
            "course_type": progress.classroom_course.course.course_type.value,
            "classroom_name": progress.classroom_course.classroom.name,
            "view_count": view_count,
            "like_count": like_count,
            "is_liked": is_liked,
            "is_favorited": True  # 在收藏列表中，肯定是已收藏的
        }
        
        favorite_list.append(favorite_work)
    
    return {
        "list": favorite_list,
        "total": total
    }


def get_excellent_work_statistics(db: Session, user_id: int, user_role: str = "student"):
    """获取优秀作业统计信息"""
    # 根据用户角色确定可访问的优秀作业
    if user_role == "teacher":
        # 教师可以看到自己教授的课堂的优秀作业
        excellent_works = db.query(models.StudentCourseProgress).join(
            models.ClassroomCourse
        ).join(models.Classroom).filter(
            models.StudentCourseProgress.is_excellent_work == True,
            models.StudentCourseProgress.graded_at.isnot(None),
            models.Classroom.teacher_id == user_id
        ).all()
    else:
        # 学生可以看到自己参与的课堂的优秀作业
        classroom_students = db.query(models.ClassroomStudent).filter(
            models.ClassroomStudent.student_id == user_id
        ).all()
        classroom_ids = [cs.classroom_id for cs in classroom_students]
        
        if classroom_ids:
            excellent_works = db.query(models.StudentCourseProgress).join(
                models.ClassroomCourse
            ).filter(
                models.StudentCourseProgress.is_excellent_work == True,
                models.StudentCourseProgress.graded_at.isnot(None),
                models.ClassroomCourse.classroom_id.in_(classroom_ids)
            ).all()
        else:
            excellent_works = []
    
    work_ids = [work.id for work in excellent_works]
    
    # 统计总阅读量
    total_views = db.query(models.ExcellentWorkView).filter(
        models.ExcellentWorkView.student_progress_id.in_(work_ids)
    ).count() if work_ids else 0
    
    # 统计总点赞数
    total_likes = db.query(models.ExcellentWorkLike).filter(
        models.ExcellentWorkLike.student_progress_id.in_(work_ids)
    ).count() if work_ids else 0
    
    # 统计总收藏数
    total_favorites = db.query(models.ExcellentWorkFavorite).filter(
        models.ExcellentWorkFavorite.student_progress_id.in_(work_ids)
    ).count() if work_ids else 0
    
    # 统计我的收藏数
    my_favorites_count = db.query(models.ExcellentWorkFavorite).filter(
        models.ExcellentWorkFavorite.user_id == user_id
    ).count()
    
    return {
        "total_works": len(excellent_works),
        "total_views": total_views,
        "total_likes": total_likes,
        "total_favorites": total_favorites,
        "my_favorites_count": my_favorites_count
    } 