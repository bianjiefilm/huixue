"""
优秀作业AI推荐服务
基于用户行为分析，为学生推荐相关优秀作业
"""

import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from collections import defaultdict
import math

from app.models import models
from app.utils.dashboard_helpers import (
    recommendation_score as _recommendation_score,
    work_similarity_score as _work_similarity_score,
)

logger = logging.getLogger(__name__)


class ExcellentWorkRecommender:
    """优秀作业推荐器"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_behavior_profile(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户的行为画像
        分析用户喜欢的作业类型、课程偏好等
        """
        # 获取用户喜欢的作业
        liked_works = self.db.query(models.ExcellentWorkLike).filter(
            models.ExcellentWorkLike.user_id == user_id
        ).all()

        # 获取用户收藏的作业
        favorited_works = self.db.query(models.ExcellentWorkFavorite).filter(
            models.ExcellentWorkFavorite.user_id == user_id
        ).all()

        # 获取用户浏览记录
        viewed_works = self.db.query(models.ExcellentWorkView).filter(
            models.ExcellentWorkView.user_id == user_id
        ).all()

        # 统计课程偏好
        course_preferences = defaultdict(int)
        work_ids = set()

        for like in liked_works:
            work_ids.add(like.student_progress_id)
        for favorite in favorited_works:
            work_ids.add(favorite.student_progress_id)
        for view in viewed_works:
            work_ids.add(view.student_progress_id)

        # 获取作业详情和课程信息
        for work_id in work_ids:
            progress = self.db.query(models.StudentCourseProgress).filter(
                models.StudentCourseProgress.id == work_id,
                models.StudentCourseProgress.is_excellent_work == True
            ).first()

            if progress and progress.classroom_course:
                course_preferences[progress.classroom_course.course_id] += 1

        return {
            "liked_count": len(liked_works),
            "favorited_count": len(favorited_works),
            "viewed_count": len(viewed_works),
            "course_preferences": dict(course_preferences),
            "total_interactions": len(liked_works) + len(favorited_works) + len(viewed_works)
        }

    def get_recommendations_for_user(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        为用户推荐优秀作业

        Args:
            user_id: 用户ID
            limit: 推荐数量

        Returns:
            推荐的优秀作业列表，按推荐分数排序
        """
        try:
            # 获取用户行为画像
            user_profile = self.get_user_behavior_profile(user_id)

            if user_profile["total_interactions"] == 0:
                # 新用户：推荐最热门的作业
                return self.get_popular_works(limit)

            # 获取用户已交互过的作业ID
            interacted_work_ids = set()
            liked_works = self.db.query(models.ExcellentWorkLike).filter(
                models.ExcellentWorkLike.user_id == user_id
            ).all()
            favorited_works = self.db.query(models.ExcellentWorkFavorite).filter(
                models.ExcellentWorkFavorite.user_id == user_id
            ).all()

            for work in liked_works + favorited_works:
                interacted_work_ids.add(work.student_progress_id)

            # 获取用户已浏览的作业ID
            viewed_works = self.db.query(models.ExcellentWorkView).filter(
                models.ExcellentWorkView.user_id == user_id
            ).all()
            for view in viewed_works:
                interacted_work_ids.add(view.student_progress_id)

            # 获取所有优秀作业（排除已交互的）
            all_works = self.db.query(models.StudentCourseProgress).join(
                models.User, models.StudentCourseProgress.student_id == models.User.id
            ).filter(
                models.StudentCourseProgress.is_excellent_work == True,
                ~models.StudentCourseProgress.id.in_(interacted_work_ids)  # 排除已交互的
            ).all()

            # 计算推荐分数
            recommendations = []
            for work in all_works:
                # 获取作业统计信息
                view_count = self.db.query(models.ExcellentWorkView).filter(
                    models.ExcellentWorkView.student_progress_id == work.id
                ).count()

                like_count = self.db.query(models.ExcellentWorkLike).filter(
                    models.ExcellentWorkLike.student_progress_id == work.id
                ).count()

                work_data = {
                    "id": work.id,
                    "course_id": work.classroom_course.course_id if work.classroom_course else None,
                    "difficulty": work.difficulty,
                    "view_count": view_count,
                    "like_count": like_count,
                    "overall_score": work.overall_score
                }

                # 计算与用户偏好的相似度
                course_pref = user_profile["course_preferences"].get(work_data["course_id"], 0)
                score = _recommendation_score(
                    course_pref_count=course_pref,
                    liked_count=user_profile["liked_count"],
                    overall_score=work.overall_score,
                    view_count=view_count,
                    like_count=like_count,
                )

                if score > 0:
                    recommendations.append({
                        "work": work,
                        "score": score,
                        "stats": work_data
                    })

            # 按分数排序并返回前N个
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return recommendations[:limit]

        except Exception as e:
            logger.error(f"获取用户推荐失败: {e}")
            # 出错时返回热门推荐
            return self.get_popular_works(limit)

    def get_popular_works(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最热门的优秀作业 (用于新用户或出错时的兜底)
        """
        try:
            # 获取所有优秀作业
            all_works = self.db.query(models.StudentCourseProgress).filter(
                models.StudentCourseProgress.is_excellent_work == True
            ).all()

            # 为每个作业计算统计信息并排序
            works_with_stats = []
            for work in all_works:
                view_count = self.db.query(models.ExcellentWorkView).filter(
                    models.ExcellentWorkView.student_progress_id == work.id
                ).count()

                like_count = self.db.query(models.ExcellentWorkLike).filter(
                    models.ExcellentWorkLike.student_progress_id == work.id
                ).count()

                total_score = view_count + like_count
                works_with_stats.append((work, view_count, like_count, total_score))

            # 按总分排序
            works_with_stats.sort(key=lambda x: x[3], reverse=True)

            # 返回前N个
            result = []
            for work, view_count, like_count, total_score in works_with_stats[:limit]:
                result.append({
                    "work": work,
                    "score": total_score / 10.0,  # 标准化分数
                    "stats": {
                        "view_count": view_count,
                        "like_count": like_count
                    }
                })
            return result

        except Exception as e:
            logger.error(f"获取热门作业失败: {e}")
            return []

    def get_similar_works(self, work_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取与指定作业相似的其他作业
        用于"相关推荐"功能
        """
        try:
            # 获取基准作业信息
            base_work = self.db.query(models.StudentCourseProgress).filter(
                models.StudentCourseProgress.id == work_id,
                models.StudentCourseProgress.is_excellent_work == True
            ).first()

            if not base_work:
                return []

            # 获取基准作业统计
            base_view_count = self.db.query(models.ExcellentWorkView).filter(
                models.ExcellentWorkView.student_progress_id == work_id
            ).count()

            base_like_count = self.db.query(models.ExcellentWorkLike).filter(
                models.ExcellentWorkLike.student_progress_id == work_id
            ).count()

            base_work_data = {
                "course_id": base_work.classroom_course.course_id if base_work.classroom_course else None,
                "difficulty": base_work.difficulty,
                "view_count": base_view_count,
                "like_count": base_like_count
            }

            # 获取其他作业并计算相似度
            similar_works = []
            other_works = self.db.query(models.StudentCourseProgress).filter(
                models.StudentCourseProgress.is_excellent_work == True,
                models.StudentCourseProgress.id != work_id
            ).all()

            for work in other_works:
                view_count = self.db.query(models.ExcellentWorkView).filter(
                    models.ExcellentWorkView.student_progress_id == work.id
                ).count()

                like_count = self.db.query(models.ExcellentWorkLike).filter(
                    models.ExcellentWorkLike.student_progress_id == work.id
                ).count()

                work_data = {
                    "course_id": work.classroom_course.course_id if work.classroom_course else None,
                    "difficulty": work.difficulty,
                    "view_count": view_count,
                    "like_count": like_count
                }

                # 计算相似度
                heat_diff = abs((view_count + like_count) - (base_view_count + base_like_count))
                similarity_score = _work_similarity_score(
                    same_course=work_data.get("course_id") == base_work_data.get("course_id"),
                    same_difficulty=work_data.get("difficulty") == base_work_data.get("difficulty"),
                    heat_diff=heat_diff,
                )

                if similarity_score > 0.3:  # 相似度阈值
                    similar_works.append({
                        "work": work,
                        "similarity_score": similarity_score,
                        "stats": work_data
                    })

            # 按相似度排序
            similar_works.sort(key=lambda x: x["similarity_score"], reverse=True)
            return similar_works[:limit]

        except Exception as e:
            logger.error(f"获取相似作业失败: {e}")
            return []