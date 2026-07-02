"""
成绩系统 CRUD 操作

包括：
- 教师评分
- 成绩查询
- 排名计算
- 学情分析
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models import StudentCourseProgress, TaskEvaluationResult, ClassroomCourse
from app.models.models import (
    CourseInClassroomStatusStudentEnum,
    SubmissionStatusEnum,
    Task,
    ClassroomStudent,
    User as ApiUser,
)


class GradingCRUD:
    """成绩系统数据操作"""
    
    @staticmethod
    def get_student_submissions(
        db: Session,
        classroom_course_id: int,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取待评分列表 (P1-W2-1 修: 融合 task_evaluation_results 自动评测 + student_course_progress 教师手动评分).

        Args:
            classroom_course_id: 课堂课程ID
            status: 状态过滤 (submitted/pending/graded/all)
            page: 页码
            page_size: 每页数量

        返回 1 行 = 1 学生 (按学生聚合, 不按提交). 没 SCP 行的学生也会包含 (auto 字段填充).
        """
        # 1) classroom_course → practice + classroom
        cc = db.query(ClassroomCourse).filter(ClassroomCourse.id == classroom_course_id).first()
        if not cc:
            return {"total": 0, "page": page, "page_size": page_size, "data": []}

        practice_id = cc.practice_id
        classroom_id = cc.classroom_id

        # 2) 该 practice 的 tasks (排除已删除)
        task_rows = []
        total_coin = 0
        if practice_id is not None:
            task_rows = db.query(Task.id, Task.coin).filter(
                Task.practice_id == practice_id,
                Task.deleted_at.is_(None),
            ).all()
            total_coin = sum((t.coin or 0) for t in task_rows)
        task_ids = [t.id for t in task_rows]
        total_tasks = len(task_rows)

        # 3) 该 classroom 学生
        students = db.query(
            ClassroomStudent.student_id,
            ApiUser.username,
            ApiUser.full_name,
        ).join(ApiUser, ApiUser.id == ClassroomStudent.student_id).filter(
            ClassroomStudent.classroom_id == classroom_id
        ).all()
        student_ids = [s.student_id for s in students]

        # 4) 每 student × 每 task 最新 TER (DISTINCT ON 走 PostgreSQL)
        latest_ter = []
        if student_ids and task_ids:
            latest_ter = db.query(TaskEvaluationResult).filter(
                TaskEvaluationResult.user_id.in_(student_ids),
                TaskEvaluationResult.task_id.in_(task_ids),
            ).distinct(
                TaskEvaluationResult.user_id, TaskEvaluationResult.task_id
            ).order_by(
                TaskEvaluationResult.user_id,
                TaskEvaluationResult.task_id,
                TaskEvaluationResult.created_at.desc(),
            ).all()

        # 5) SCP 行 (manual)
        scps = db.query(StudentCourseProgress).filter(
            StudentCourseProgress.classroom_course_id == classroom_course_id,
            StudentCourseProgress.student_id.in_(student_ids) if student_ids else True,
        ).all()
        scp_by_student = {s.student_id: s for s in scps}

        # 6) Python 聚合
        ter_by_student: Dict[int, list] = {}
        for t in latest_ter:
            ter_by_student.setdefault(t.user_id, []).append(t)

        data = []
        for s in students:
            sid = s.student_id
            ters = ter_by_student.get(sid, [])
            completed = sum(1 for t in ters if t.status == 'pass')
            auto_score_sum = sum((t.score or 0) for t in ters if t.status == 'pass')
            auto_score_pct = round(auto_score_sum / total_coin * 100, 1) if total_coin else None
            last_eval_at = max((t.created_at for t in ters), default=None)

            scp = scp_by_student.get(sid)
            manual_score = scp.overall_score if scp else None
            teacher_feedback = scp.teacher_feedback if scp else None
            final_score = scp.final_calculated_score if scp else (auto_score_pct if completed > 0 else None)

            # 派生状态
            if scp and scp.graded_at:
                derived_status = "GRADED"
            elif total_tasks > 0 and completed == total_tasks:
                derived_status = "AUTO_COMPLETED"
            elif completed > 0:
                derived_status = "PARTIAL"
            else:
                derived_status = "NOT_STARTED"

            data.append({
                # 新增 auto 字段
                "student_id": sid,
                "student_name": s.full_name or s.username,
                "auto_completed_tasks": completed,
                "total_tasks": total_tasks,
                "auto_score": auto_score_pct,
                "last_evaluation_at": last_eval_at.isoformat() if last_eval_at else None,
                "manual_score": manual_score,
                "final_score": final_score,
                "teacher_feedback": teacher_feedback,
                "graded_at": scp.graded_at.isoformat() if scp and scp.graded_at else None,
                "graded_by_teacher_id": scp.graded_by_teacher_id if scp else None,
                "is_excellent_work": scp.is_excellent_work if scp else False,
                "derived_status": derived_status,
                # 兼容老字段 (frontend 老逻辑)
                "id": scp.id if scp else None,
                "classroom_course_id": classroom_course_id,
                "student_status": (
                    scp.student_status.value if scp and scp.student_status else "AUTO_ONLY"
                ),
                "overall_score": manual_score,
                "teacher_penalties": (scp.teacher_penalties or 0) if scp else 0,
                "final_calculated_score": final_score,
            })

        # 7) status 过滤
        if status == 'graded':
            data = [d for d in data if d['graded_at']]
        elif status == 'pending':
            data = [d for d in data if d['derived_status'] in ('AUTO_COMPLETED', 'PARTIAL') and not d['graded_at']]
        elif status == 'submitted':
            data = [d for d in data if d['derived_status'] != 'NOT_STARTED']

        # 8) 分页
        total = len(data)
        start = (page - 1) * page_size
        data = data[start:start + page_size]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": data,
        }
    
    @staticmethod
    def submit_grade(
        db: Session,
        student_id: int,
        classroom_course_id: int,
        overall_score: float,
        teacher_penalties: float = 0,
        teacher_feedback: str = "",
        graded_by_teacher_id: int = None,
        is_excellent_work: bool = False
    ) -> Optional[StudentCourseProgress]:
        """
        提交成绩和反馈
        """
        from app.crud.audit_crud import AuditCRUD
        
        progress = db.query(StudentCourseProgress).filter(
            and_(
                StudentCourseProgress.student_id == student_id,
                StudentCourseProgress.classroom_course_id == classroom_course_id
            )
        ).first()
        
        # 记录旧值用于审计
        old_value = None
        if progress:
            old_value = {
                "overall_score": progress.overall_score,
                "teacher_penalties": progress.teacher_penalties,
                "teacher_feedback": progress.teacher_feedback,
                "is_excellent_work": progress.is_excellent_work
            }
        
        if not progress:
            # 创建新记录
            progress = StudentCourseProgress(
                student_id=student_id,
                classroom_course_id=classroom_course_id,
                overall_score=overall_score,
                teacher_penalties=teacher_penalties,
                teacher_feedback=teacher_feedback,
                graded_by_teacher_id=graded_by_teacher_id,
                is_excellent_work=is_excellent_work,
                graded_at=datetime.utcnow(),
                student_status=CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME,
                final_calculated_score=overall_score - teacher_penalties
            )
        else:
            # 更新现有记录
            progress.overall_score = overall_score
            progress.teacher_penalties = teacher_penalties
            progress.teacher_feedback = teacher_feedback
            progress.graded_by_teacher_id = graded_by_teacher_id
            progress.is_excellent_work = is_excellent_work
            progress.graded_at = datetime.utcnow()
            progress.student_status = CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME
            progress.final_calculated_score = overall_score - teacher_penalties
        
        db.add(progress)
        db.commit()
        db.refresh(progress)
        
        # 记录审计日志
        new_value = {
            "overall_score": progress.overall_score,
            "teacher_penalties": progress.teacher_penalties,
            "teacher_feedback": progress.teacher_feedback,
            "is_excellent_work": progress.is_excellent_work
        }
        
        AuditCRUD.log_grade_change(
            db,
            entity_type="student_course_progress",
            entity_id=progress.id,
            old_value=old_value,
            new_value=new_value,
            changed_by=graded_by_teacher_id or 0,
            action="grade_changed" if old_value else "grade_created"
        )
        
        return progress
    
    @staticmethod
    def get_student_grades(
        db: Session,
        student_id: int,
        classroom_id: int
    ) -> Dict[str, Any]:
        """
        获取学生成绩单
        """
        from app.models import Classroom, ClassroomCourse, Course
        
        # 获取课堂信息
        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom:
            return None
        
        # 获取所有课程及成绩
        courses_query = db.query(
            ClassroomCourse,
            StudentCourseProgress,
            Course
        ).outerjoin(
            StudentCourseProgress,
            and_(
                StudentCourseProgress.classroom_course_id == ClassroomCourse.id,
                StudentCourseProgress.student_id == student_id
            )
        ).join(
            Course,
            ClassroomCourse.course_id == Course.id
        ).filter(
            ClassroomCourse.classroom_id == classroom_id
        ).all()
        
        courses = []
        for cc, scp, course in courses_query:
            courses.append({
                "course_id": course.id,
                "course_name": course.title,
                "course_type": getattr(course, 'course_type', None),
                "overall_score": scp.overall_score if scp else None,
                "teacher_feedback": scp.teacher_feedback if scp else None,
                "graded_at": scp.graded_at.isoformat() if scp and scp.graded_at else None,
                "status": scp.student_status.value if scp and scp.student_status else "not_started",
                "is_required": getattr(cc, 'is_mandatory', True)
            })
        
        # 计算班级平均分
        class_average = db.query(
            func.avg(StudentCourseProgress.overall_score)
        ).join(
            ClassroomCourse,
            StudentCourseProgress.classroom_course_id == ClassroomCourse.id
        ).filter(
            and_(
                ClassroomCourse.classroom_id == classroom_id,
                ClassroomCourse.is_mandatory == True
            )
        ).scalar()

        # 计算学生排名：先获取该学生的平均分，再数比他高的人数
        student_avg = db.query(
            func.avg(StudentCourseProgress.overall_score)
        ).join(
            ClassroomCourse,
            StudentCourseProgress.classroom_course_id == ClassroomCourse.id
        ).filter(
            and_(
                ClassroomCourse.classroom_id == classroom_id,
                StudentCourseProgress.student_id == student_id
            )
        ).scalar()

        student_rank = 1
        if student_avg is not None:
            # 用子查询计算每个学生的平均分，再数比当前学生高的
            from sqlalchemy import literal
            better_count = db.query(
                func.count(func.distinct(StudentCourseProgress.student_id))
            ).join(
                ClassroomCourse,
                StudentCourseProgress.classroom_course_id == ClassroomCourse.id
            ).filter(
                and_(
                    ClassroomCourse.classroom_id == classroom_id,
                    StudentCourseProgress.overall_score > float(student_avg)
                )
            ).scalar() or 0
            student_rank = better_count + 1

        return {
            "classroom_name": classroom.name,
            "courses": courses,
            "class_average": float(class_average) if class_average else None,
            "student_rank": student_rank
        }
    
    @staticmethod
    def get_classroom_analytics(
        db: Session,
        classroom_id: int
    ) -> Dict[str, Any]:
        """
        获取班级学情总览
        """
        from app.models import ClassroomCourse, Course, Practice
        from sqlalchemy import case, literal_column, func

        # 获取所有课堂课程（同时支持 Course 和 Practice）
        classroom_courses = db.query(
            ClassroomCourse.id.label('cc_id'),
            ClassroomCourse.name_override,
            ClassroomCourse.course_id,
            ClassroomCourse.practice_id,
            Course.title.label('course_name'),
            Practice.title.label('practice_name')
        ).outerjoin(
            Course, ClassroomCourse.course_id == Course.id
        ).outerjoin(
            Practice, ClassroomCourse.practice_id == Practice.id
        ).filter(
            ClassroomCourse.classroom_id == classroom_id
        ).all()

        completion_by_course = []
        average_scores = []

        for cc in classroom_courses:
            # 优先使用自定义名称，其次是课程名或实践名
            course_name = cc.name_override or cc.course_name or cc.practice_name or '未命名课程'

            # 获取该课程的进度统计
            progress_stats = db.query(
                func.count(StudentCourseProgress.id).label('total_count'),
                func.count(StudentCourseProgress.graded_at).label('graded_count'),
                func.avg(StudentCourseProgress.overall_score).label('avg_score'),
                func.max(StudentCourseProgress.overall_score).label('max_score'),
                func.min(StudentCourseProgress.overall_score).label('min_score')
            ).filter(
                StudentCourseProgress.classroom_course_id == cc.cc_id
            ).first()

            total_count = progress_stats.total_count or 0
            graded_count = progress_stats.graded_count or 0

            completion_by_course.append({
                "course_name": course_name,
                "completed_count": graded_count,
                "total_count": total_count,
                "completion_rate": graded_count / total_count if total_count > 0 else 0
            })

            average_scores.append({
                "course_name": course_name,
                "average_score": float(progress_stats.avg_score) if progress_stats.avg_score else 0,
                "max_score": float(progress_stats.max_score) if progress_stats.max_score else 0,
                "min_score": float(progress_stats.min_score) if progress_stats.min_score else 0
            })

        # 获取优秀学生
        from app.models import User

        # 获取课堂课程ID列表
        cc_ids = [cc.cc_id for cc in classroom_courses]

        top_performers = db.query(
            User.id,
            User.username,
            func.avg(StudentCourseProgress.overall_score).label('avg_score')
        ).join(
            StudentCourseProgress, User.id == StudentCourseProgress.student_id
        ).filter(
            StudentCourseProgress.classroom_course_id.in_(cc_ids)
        ).group_by(User.id).order_by(
            desc('avg_score')
        ).limit(5).all()

        top_list = [
            {
                "rank": i + 1,
                "student_id": tp[0],
                "student_name": tp[1],
                "average_score": float(tp[2]) if tp[2] else 0
            }
            for i, tp in enumerate(top_performers)
        ]

        # 获取预警学生（成绩低于60）
        struggling = db.query(
            User.id,
            User.username,
            func.avg(StudentCourseProgress.overall_score).label('avg_score')
        ).join(
            StudentCourseProgress, User.id == StudentCourseProgress.student_id
        ).filter(
            and_(
                StudentCourseProgress.classroom_course_id.in_(cc_ids),
                StudentCourseProgress.overall_score < 60
            )
        ).group_by(User.id).all()

        struggling_list = [
            {
                "student_id": s[0],
                "student_name": s[1],
                "average_score": float(s[2]) if s[2] else 0
            }
            for s in struggling
        ]
        
        return {
            "completion_by_course": completion_by_course,
            "average_scores": average_scores,
            "top_performers": top_list,
            "struggling_students": struggling_list
        }
    
    @staticmethod
    def get_rankings(
        db: Session,
        classroom_id: int,
        course_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取班级排名
        
        Args:
            classroom_id: 课堂ID
            course_id: 可选的课程ID（不提供则为班级总排名）
        """
        from app.models import ClassroomCourse, User
        
        if course_id:
            # 获取特定课程的排名
            rankings = db.query(
                StudentCourseProgress.student_id,
                User.username,
                StudentCourseProgress.overall_score
            ).join(
                User, User.id == StudentCourseProgress.student_id
            ).filter(
                and_(
                    StudentCourseProgress.classroom_course_id == course_id,
                    StudentCourseProgress.overall_score.isnot(None)
                )
            ).order_by(
                desc(StudentCourseProgress.overall_score)
            ).all()
        else:
            # 获取班级总排名（所有课程平均分）
            rankings = db.query(
                StudentCourseProgress.student_id,
                User.username,
                func.avg(StudentCourseProgress.overall_score).label('avg_score')
            ).join(
                User, User.id == StudentCourseProgress.student_id
            ).join(
                ClassroomCourse,
                StudentCourseProgress.classroom_course_id == ClassroomCourse.id
            ).filter(
                ClassroomCourse.classroom_id == classroom_id
            ).group_by(
                StudentCourseProgress.student_id, User.username
            ).order_by(
                desc('avg_score')
            ).all()
        
        result = []
        for i, (student_id, username, score) in enumerate(rankings):
            result.append({
                "rank": i + 1,
                "student_id": student_id,
                "student_name": username,
                "score": float(score) if score else None
            })
        
        return result
    
    @staticmethod
    def get_course_stats(
        db: Session,
        classroom_id: int
    ) -> Dict[str, Any]:
        """
        获取课程统计（必修/拓展）
        """
        from app.models import ClassroomCourse, Course
        
        required = db.query(
            Course.title,
            func.count(StudentCourseProgress.id).label('total_count'),
            func.count(StudentCourseProgress.graded_at).label('graded_count'),
            func.avg(StudentCourseProgress.overall_score).label('avg_score')
        ).select_from(ClassroomCourse).join(
            Course, ClassroomCourse.course_id == Course.id
        ).outerjoin(
            StudentCourseProgress,
            StudentCourseProgress.classroom_course_id == ClassroomCourse.id
        ).filter(
            and_(
                ClassroomCourse.classroom_id == classroom_id,
                ClassroomCourse.is_mandatory == True
            )
        ).group_by(Course.id).all()

        optional = db.query(
            Course.title,
            func.count(StudentCourseProgress.id).label('total_count'),
            func.count(StudentCourseProgress.graded_at).label('graded_count'),
            func.avg(StudentCourseProgress.overall_score).label('avg_score')
        ).select_from(ClassroomCourse).join(
            Course, ClassroomCourse.course_id == Course.id
        ).outerjoin(
            StudentCourseProgress,
            StudentCourseProgress.classroom_course_id == ClassroomCourse.id
        ).filter(
            and_(
                ClassroomCourse.classroom_id == classroom_id,
                ClassroomCourse.is_mandatory == False
            )
        ).group_by(Course.id).all()
        
        def format_stats(stats_list):
            return [
                {
                    "course_name": stat[0],
                    "completion_rate": stat[3] / stat[2] if stat[2] > 0 else 0,
                    "average_score": float(stat[3]) if stat[3] else 0
                }
                for stat in stats_list
            ]
        
        return {
            "required_courses": format_stats(required),
            "optional_courses": format_stats(optional)
        }

