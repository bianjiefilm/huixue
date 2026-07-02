"""
test_grade_authorization.py — 成绩与作业授权测试
验证 Fail-Soft 模式、越权查看成绩、已评分作业重复提交
Targets: GAP-B1, GAP-B5
"""
import pytest


class TestGradeAccessControl:
    """成绩访问控制"""

    def test_student_outside_classroom_gets_explicit_error(
        self, client, student2_headers, sample_classroom
    ):
        """
        未加入课堂的学生查询成绩应返回明确错误，而非空数组。
        已知问题 (GAP-B1): Fail-Soft 模式返回 {"code":"0000","data":[]}
        """
        # student2 没有加入 sample_classroom
        resp = client.get(
            f"/api/v1/classrooms/{sample_classroom.id}/grades",
            headers=student2_headers,
        )
        if resp.status_code == 200:
            data = resp.json()
            # 如果返回 200 但 data 为空，说明是 Fail-Soft 模式 → 这是 bug
            if isinstance(data.get("data"), list) and len(data["data"]) == 0:
                pytest.fail(
                    f"GAP-B1 confirmed: endpoint returned empty success instead of 403. "
                    f"Response: {data}"
                )
            # 如果 data 有内容且属于其他学生 → 更严重的越权
            if data.get("data"):
                pytest.fail(
                    f"CRITICAL: student outside classroom can see grade data! "
                    f"Response: {data}"
                )
        else:
            # 返回 403/401 是正确行为
            assert resp.status_code in (403, 401, 404), \
                f"Unexpected status {resp.status_code}"

    def test_student_cannot_see_other_student_grades(
        self, client, student2_headers, sample_classroom, student_user
    ):
        """学生不能查看其他学生的成绩单"""
        resp = client.get(
            f"/api/v1/classrooms/{sample_classroom.id}/report-cards/{student_user.id}",
            headers=student2_headers,
        )
        assert resp.status_code in (403, 401, 404), \
            f"Expected 403/401 but got {resp.status_code}: student should not see other's grades"


class TestHomeworkSubmissionLock:
    """作业提交锁定测试"""

    def test_student_cannot_resubmit_graded_homework(
        self, client, student_headers, db_session, sample_classroom, sample_practice
    ):
        """
        教师评分后学生不可再提交更新作业 (GAP-B5)
        先模拟已评分状态，再尝试提交
        """
        from app.models.models import (
            ClassroomCourse, StudentCourseProgress,
            CourseInClassroomStatusTeacherEnum, SubmissionStatusEnum,
        )

        # 创建课堂课程关联
        cc = ClassroomCourse(
            id=600,
            classroom_id=sample_classroom.id,
            practice_id=sample_practice.id,
            teacher_publish_status=CourseInClassroomStatusTeacherEnum.LEARNING,
        )
        db_session.add(cc)
        db_session.flush()

        # 创建已评分的学生进度
        progress = StudentCourseProgress(
            id=700,
            classroom_course_id=600,
            student_id=30,  # student_user
            training_submission_status=SubmissionStatusEnum.GRADED,
            overall_score=85,
        )
        db_session.add(progress)
        db_session.commit()

        # 尝试重新提交 — 应该被拒绝
        resp = client.post(
            f"/api/v1/trainings/{sample_practice.id}/submit-homework",
            json={"content": "尝试重新提交"},
            headers=student_headers,
        )
        # 如果已评分，不应允许再次提交
        if resp.status_code == 200:
            pytest.fail(
                "GAP-B5 confirmed: student can resubmit homework after teacher grading"
            )


class TestGradeScoreBounds:
    """成绩分数边界测试"""

    def test_grade_score_exceeds_total(
        self, client, teacher_headers, sample_classroom, student_user
    ):
        """打分超过总分应被拒绝"""
        resp = client.put(
            f"/api/v1/classrooms/{sample_classroom.id}/courses/600/grades/{student_user.id}",
            json={"score": 999},
            headers=teacher_headers,
        )
        # 分数不应超过 total_score
        assert resp.status_code in (400, 422, 404), \
            f"Expected validation error but got {resp.status_code}: score > total should be rejected"

    def test_negative_grade_rejected(
        self, client, teacher_headers, sample_classroom, student_user
    ):
        """负数成绩应被拒绝"""
        resp = client.put(
            f"/api/v1/classrooms/{sample_classroom.id}/courses/600/grades/{student_user.id}",
            json={"score": -1},
            headers=teacher_headers,
        )
        assert resp.status_code in (400, 422, 404), \
            f"Expected validation error but got {resp.status_code}: negative score should be rejected"
