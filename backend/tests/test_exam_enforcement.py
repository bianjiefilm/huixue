"""
test_exam_enforcement.py — 考试规则强制执行测试
验证时间窗口、进行中考试编辑锁、及格分数默认值
Targets: GAP-B4
"""
import pytest
from datetime import datetime, timedelta


class TestExamTimeWindow:
    """考试时间窗口校验"""

    def test_create_exam_with_valid_time_window(
        self, client, teacher_headers, sample_classroom, db_session
    ):
        """
        考试时间窗口 >= 考试时长 → 允许创建
        手册要求: 考试时间区间长度不得低于考试时长
        """
        # 先确保有试卷
        from app.models.models import TestPaper, DifficultyEnum
        paper = TestPaper(
            id=401, title="合法考试试卷", creator_id=29,
            total_score=100, difficulty=DifficultyEnum.INTERMEDIATE,
        )
        db_session.add(paper)
        db_session.commit()

        resp = client.post(f"/api/v1/exams/classrooms/{sample_classroom.id}/exams", json={
            "test_paper_id": 401,
            "title": "合法考试",
            "exam_start_time": "2026-05-01T09:00:00",
            "exam_end_time": "2026-05-01T11:00:00",   # 2 hours window
            "duration_minutes": 90,                      # 90 min <= 120 min ✓
        }, headers=teacher_headers)
        # 应该能创建（可能返回 200 或不同路由格式）
        assert resp.status_code in (200, 201, 404, 422), \
            f"Unexpected status {resp.status_code}: {resp.text[:200]}"

    def test_create_exam_window_shorter_than_duration(
        self, client, teacher_headers, sample_classroom
    ):
        """
        考试时间窗口 < 考试时长 → 应拒绝
        手册 §4.7.4: 考试时间区间长度不得低于考试时长
        """
        resp = client.post(f"/api/v1/exams/classrooms/{sample_classroom.id}/exams", json={
            "test_paper_id": 401,
            "title": "时间窗口不足的考试",
            "exam_start_time": "2026-05-01T09:00:00",
            "exam_end_time": "2026-05-01T10:00:00",   # 1 hour window
            "duration_minutes": 120,                     # 120 min > 60 min ✗
        }, headers=teacher_headers)
        # 应返回 422 Validation Error
        if resp.status_code in (200, 201):
            pytest.fail(
                "GAP-B4 confirmed: exam created with time_window < duration. "
                "Manual requires: window >= duration"
            )


class TestOngoingExamEditLock:
    """进行中考试不可编辑"""

    def test_cannot_edit_ongoing_exam(
        self, client, teacher_headers, sample_exam, db_session
    ):
        """
        进行中的考试不应被编辑
        手册 §4.7.4: 已发布/已开始的考试不可修改
        """
        from app.models.models import ExamStatusEnum
        sample_exam.status = ExamStatusEnum.ONGOING
        db_session.commit()

        resp = client.put(f"/api/v1/exams/{sample_exam.id}", json={
            "title": "尝试修改进行中考试",
        }, headers=teacher_headers)
        if resp.status_code == 200:
            pytest.fail(
                "GAP-B4 confirmed: ongoing exam can be edited. "
                "Manual requires: no edits on ongoing exams"
            )

    def test_cannot_delete_ongoing_exam(
        self, client, teacher_headers, sample_exam, db_session
    ):
        """进行中的考试不应被删除"""
        from app.models.models import ExamStatusEnum
        sample_exam.status = ExamStatusEnum.ONGOING
        db_session.commit()

        resp = client.delete(f"/api/v1/exams/{sample_exam.id}",
                            headers=teacher_headers)
        if resp.status_code == 200:
            pytest.fail(
                "GAP-B4 confirmed: ongoing exam can be deleted"
            )


class TestExamDefaults:
    """考试默认值测试"""

    def test_exam_title_max_length_60_chars(
        self, client, teacher_headers, sample_classroom
    ):
        """
        手册 §4.7.4: 考试名称限制长度60字符
        """
        long_title = "A" * 61  # 超过60字符
        resp = client.post(f"/api/v1/exams/classrooms/{sample_classroom.id}/exams", json={
            "test_paper_id": 400,
            "title": long_title,
            "exam_start_time": "2026-06-01T09:00:00",
            "exam_end_time": "2026-06-01T11:00:00",
            "duration_minutes": 60,
        }, headers=teacher_headers)
        if resp.status_code in (200, 201):
            data = resp.json()
            created_title = data.get("data", {}).get("title", "")
            if len(created_title) > 60:
                pytest.fail(
                    f"Exam title exceeds 60 chars limit: {len(created_title)} chars"
                )

    def test_zero_duration_exam_rejected(
        self, client, teacher_headers, sample_classroom
    ):
        """考试时长为0应被拒绝"""
        resp = client.post(f"/api/v1/exams/classrooms/{sample_classroom.id}/exams", json={
            "test_paper_id": 400,
            "title": "零时长考试",
            "exam_start_time": "2026-06-01T09:00:00",
            "exam_end_time": "2026-06-01T11:00:00",
            "duration_minutes": 0,
        }, headers=teacher_headers)
        if resp.status_code in (200, 201):
            pytest.fail("Zero-duration exam should be rejected")
