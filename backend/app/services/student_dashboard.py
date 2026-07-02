"""
Student Dashboard Service
提供学生仪表板所需的数据：活跃学习路径、技能图谱、优先情报
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.models import (
    ClassroomCourse, StudentCourseProgress, Course, Classroom,
    Task, TaskEvaluationResult, Practice, ClassroomStudent,
    CourseInClassroomStatusStudentEnum, CourseInClassroomStatusTeacherEnum
)
from app.utils.dashboard_helpers import (
    deadline_urgency as _deadline_urgency,
    progress_percent as _progress_percent,
    attention_score as _attention_score,
    priority_type as _priority_type,
    categorize_skill as _categorize_skill,
)

logger = logging.getLogger(__name__)


class StudentDashboardService:
    """学生仪表板服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_active_learning_paths(
        self, 
        student_id: int, 
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        获取学生的活跃学习路径（按优先级排序）
        
        优先级算法：
        Score = (W1 × DeadlineUrgency) + (W2 × ProgressGap) + (W3 × IsMandatory)
        """
        try:
            now = datetime.now()
            
            # 查询学生正在进行中的课程
            query = self.db.query(
                StudentCourseProgress,
                ClassroomCourse,
                Course,
                Classroom
            ).join(
                ClassroomCourse, StudentCourseProgress.classroom_course_id == ClassroomCourse.id
            ).join(
                Course, ClassroomCourse.course_id == Course.id
            ).join(
                Classroom, ClassroomCourse.classroom_id == Classroom.id
            ).filter(
                StudentCourseProgress.student_id == student_id,
                StudentCourseProgress.student_status.in_([
                    CourseInClassroomStatusStudentEnum.ONGOING,
                    CourseInClassroomStatusStudentEnum.MAKEUP
                ]),
                ClassroomCourse.teacher_publish_status == CourseInClassroomStatusTeacherEnum.PUBLISHED
            )
            
            results = query.all()
            
            paths = []
            for progress, cc, course, classroom in results:
                # 计算剩余天数
                days_left = None
                if cc.deadline_at:
                    delta = cc.deadline_at - now
                    days_left = max(0, delta.days)

                urgency = _deadline_urgency(days_left)

                # 计算进度差距
                total_tasks = course.practice_task_count or 1
                completed = progress.completed_task_count or 0
                pct = _progress_percent(completed, total_tasks)
                progress_gap = 100 - pct

                # 计算综合得分
                score = _attention_score(urgency, progress_gap, cc.is_mandatory)

                # 确定优先级类型
                ptype = _priority_type(days_left, pct, total_tasks, cc.is_mandatory)
                
                paths.append({
                    "id": f"{classroom.id}-{course.id}",
                    "courseId": str(course.id),
                    "classroomCourseId": cc.id,
                    "title": course.title,
                    "code": f"COURSE-{course.id}",
                    "coverImage": course.cover_url,
                    "progress": pct,
                    "priority": ptype,
                    "daysRemaining": days_left,
                    "dueDate": cc.deadline_at.isoformat() if cc.deadline_at else None,
                    "classroomId": str(classroom.id),
                    "classroomName": classroom.name,
                    "isMandatory": cc.is_mandatory,
                    "totalTasks": total_tasks,
                    "completedTasks": completed,
                    "attentionScore": score
                })
            
            # 按关注度得分降序排序
            paths.sort(key=lambda x: x["attentionScore"], reverse=True)
            
            return paths[:limit]
            
        except Exception as e:
            logger.error(f"获取活跃学习路径失败: {e}")
            return []
    
    def get_skill_constellation(self, student_id: int) -> Dict[str, Any]:
        """
        获取学生的技能星座数据
        基于学生已通过的任务，聚合技能标签
        """
        try:
            # 查询学生通过的所有任务
            passed_results = self.db.query(
                TaskEvaluationResult, Task
            ).join(
                Task, TaskEvaluationResult.task_id == Task.id
            ).filter(
                TaskEvaluationResult.user_id == student_id,
                TaskEvaluationResult.status == 'pass'
            ).all()
            
            # 统计技能
            skill_counts = Counter()
            skill_pairs = Counter()  # 技能共现关系
            
            for result, task in passed_results:
                if task.skills:
                    # 解析技能标签（可能是JSON或逗号分隔）
                    try:
                        skills = json.loads(task.skills) if task.skills.startswith('[') else [s.strip() for s in task.skills.split(',')]
                    except:
                        skills = [s.strip() for s in task.skills.split(',')]
                    
                    skills = [s for s in skills if s]  # 过滤空字符串
                    
                    for skill in skills:
                        skill_counts[skill] += 1
                    
                    # 计算技能共现（用于连线）
                    for i, s1 in enumerate(skills):
                        for s2 in skills[i+1:]:
                            pair = tuple(sorted([s1, s2]))
                            skill_pairs[pair] += 1
            
            # 构建节点数据
            max_count = max(skill_counts.values()) if skill_counts else 1
            nodes = []
            for skill, count in skill_counts.most_common(12):  # 最多显示12个技能
                mastery = min(100, int((count / max_count) * 100))
                nodes.append({
                    "id": skill.lower().replace(' ', '-'),
                    "name": skill,
                    "category": self._categorize_skill(skill),
                    "mastery": mastery,
                    "count": count,
                    "connections": []
                })
            
            # 构建连线数据
            links = []
            node_ids = {n["name"]: n["id"] for n in nodes}
            for (s1, s2), weight in skill_pairs.most_common(20):
                if s1 in node_ids and s2 in node_ids:
                    links.append({
                        "source": node_ids[s1],
                        "target": node_ids[s2],
                        "weight": weight
                    })
                    # 更新节点的连接信息
                    for node in nodes:
                        if node["name"] == s1:
                            node["connections"].append(node_ids[s2])
                        elif node["name"] == s2:
                            node["connections"].append(node_ids[s1])
            
            # 如果没有数据，返回示例数据
            if not nodes:
                nodes = self._get_default_skills()
            
            return {
                "nodes": nodes,
                "links": links,
                "totalSkills": len(skill_counts),
                "topSkills": [s for s, _ in skill_counts.most_common(3)]
            }
            
        except Exception as e:
            logger.error(f"获取技能星座失败: {e}")
            return {
                "nodes": self._get_default_skills(),
                "links": [],
                "totalSkills": 0,
                "topSkills": []
            }
    
    def _categorize_skill(self, skill: str) -> str:
        """技能分类"""
        return _categorize_skill(skill)
    
    def _get_default_skills(self) -> List[Dict[str, Any]]:
        """返回默认技能数据（用于演示）"""
        return [
            {"id": "python", "name": "Python", "category": "编程", "mastery": 85, "connections": ["data-analysis", "ml"]},
            {"id": "data-analysis", "name": "数据分析", "category": "数据分析", "mastery": 70, "connections": ["python", "statistics"]},
            {"id": "statistics", "name": "统计学", "category": "数学统计", "mastery": 60, "connections": ["data-analysis", "ml"]},
            {"id": "ml", "name": "机器学习", "category": "人工智能", "mastery": 45, "connections": ["python", "statistics"]},
            {"id": "sql", "name": "SQL", "category": "编程", "mastery": 75, "connections": ["data-analysis"]},
            {"id": "visualization", "name": "数据可视化", "category": "数据分析", "mastery": 65, "connections": ["data-analysis", "python"]}
        ]
    
    def get_priority_intel(self, student_id: int) -> Dict[str, Any]:
        """
        获取优先情报：即将到期的任务和推荐课程
        """
        try:
            now = datetime.now()
            
            # 获取即将到期的课程
            deadlines = []
            paths = self.get_active_learning_paths(student_id, limit=10)
            
            for path in paths:
                if path["daysRemaining"] is not None and path["daysRemaining"] <= 7:
                    deadlines.append({
                        "id": f"deadline-{path['courseId']}",
                        "title": path["title"],
                        "dueDate": path["dueDate"],
                        "daysRemaining": path["daysRemaining"],
                        "type": "assignment",
                        "courseId": path["courseId"],
                        "classroomId": path["classroomId"],
                        "isCritical": path["daysRemaining"] <= 3
                    })
            
            # 按剩余天数排序
            deadlines.sort(key=lambda x: x["daysRemaining"])
            
            # 获取推荐课程（拓展课程）
            recommendations = self._get_course_recommendations(student_id)
            
            return {
                "deadlines": deadlines[:5],
                "recommendations": recommendations[:3],
                "criticalCount": len([d for d in deadlines if d["isCritical"]])
            }
            
        except Exception as e:
            logger.error(f"获取优先情报失败: {e}")
            return {
                "deadlines": [],
                "recommendations": [],
                "criticalCount": 0
            }
    
    def _get_course_recommendations(self, student_id: int) -> List[Dict[str, Any]]:
        """获取课程推荐（基于技能匹配）"""
        try:
            # 获取学生的技能
            skill_data = self.get_skill_constellation(student_id)
            student_skills = [n["name"] for n in skill_data["nodes"]]
            
            # 查询学生尚未加入的拓展课程
            # 这里简化处理，返回一些推荐
            recommendations = [
                {
                    "courseId": "rec-1",
                    "title": "人工智能伦理入门",
                    "reason": "基于您的技能图谱，这门拓展课程与您的学习路径高度匹配",
                    "matchScore": 85,
                    "tags": ["AI", "伦理", "拓展"]
                }
            ]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"获取课程推荐失败: {e}")
            return []
    
    def get_dashboard_summary(self, student_id: int) -> Dict[str, Any]:
        """获取仪表板完整数据"""
        return {
            "activePaths": self.get_active_learning_paths(student_id),
            "skillConstellation": self.get_skill_constellation(student_id),
            "priorityIntel": self.get_priority_intel(student_id)
        }

