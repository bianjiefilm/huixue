"""
测试配置和fixtures
Phase 2: 多角色安全网测试基础设施

策略: 使用 session-scoped 引擎 + 每测试函数嵌套事务 (savepoint)
"""

import os
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# ---------- Bootstrap ----------
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_pytest_only_12345")

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models.models import (
    User, UserProfile, School, Classroom, ClassroomStudent, ClassroomStatusEnum,
    Practice, Task, TaskTypeEnum, DifficultyLevelEnum,
    ClassroomCourse, ClassroomExam, TestPaper, Question, TestPaperQuestion,
    CourseInClassroomStatusTeacherEnum, ExamStatusEnum, QuestionTypeEnum,
    DifficultyEnum, StudentCourseProgress, SubmissionStatusEnum,
    PracticePublishStatusEnum, PracticeVisibilityEnum, UserTypeEnum,
    UserStatusEnum,
)
from app.main import app


# ==================== Database Engine (session scope) ====================

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

@event.listens_for(_test_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.close()

# 创建所有表（一次）
Base.metadata.create_all(bind=_test_engine)

_TestSessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


# ==================== Core Fixtures ====================

@pytest.fixture(autouse=True)
def _clean_tables():
    """每个测试后清空所有表数据，保持隔离"""
    yield
    # 清理 — 删除所有行但保留表结构
    session = _TestSessionFactory()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    finally:
        session.close()


@pytest.fixture
def db_session():
    """每个测试函数独立会话"""
    session = _TestSessionFactory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient，覆盖 get_db 依赖"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    from app.core import database as core_db_module
    original_get_db = core_db_module.get_db
    core_db_module.get_db = override_get_db

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()
    core_db_module.get_db = original_get_db


# ==================== Seed Fixtures ====================

@pytest.fixture
def test_school(db_session):
    school = School(id=1, name="测试大学")
    db_session.add(school)
    db_session.commit()
    db_session.refresh(school)
    return school


@pytest.fixture
def admin_user(db_session, test_school):
    user = User(
        id=1, username="admin", email="admin@test.com",
        full_name="管理员", hashed_password="not_real_hash",
        is_active=True, is_superuser=True, total_coins=0,
    )
    db_session.add(user)
    db_session.flush()
    profile = UserProfile(
        user_id=1, school_id=test_school.id,
        user_type=UserTypeEnum.ADMIN, real_name="管理员",
        status=UserStatusEnum.ACTIVE,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def teacher_user(db_session, test_school):
    user = User(
        id=29, username="teacher1", email="teacher1@test.com",
        full_name="教师", hashed_password="not_real_hash",
        is_active=True, is_superuser=False, total_coins=0,
    )
    db_session.add(user)
    db_session.flush()
    profile = UserProfile(
        user_id=29, school_id=test_school.id,
        user_type=UserTypeEnum.TEACHER, real_name="教师",
        status=UserStatusEnum.ACTIVE,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def student_user(db_session, test_school):
    user = User(
        id=30, username="student1", email="student1@test.com",
        full_name="学生1", hashed_password="not_real_hash",
        is_active=True, is_superuser=False, total_coins=0,
    )
    db_session.add(user)
    db_session.flush()
    profile = UserProfile(
        user_id=30, school_id=test_school.id,
        user_type=UserTypeEnum.STUDENT, real_name="学生1",
        status=UserStatusEnum.ACTIVE,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def student_user_2(db_session, test_school):
    user = User(
        id=31, username="student2", email="student2@test.com",
        full_name="学生2", hashed_password="not_real_hash",
        is_active=True, is_superuser=False, total_coins=0,
    )
    db_session.add(user)
    db_session.flush()
    profile = UserProfile(
        user_id=31, school_id=test_school.id,
        user_type=UserTypeEnum.STUDENT, real_name="学生2",
        status=UserStatusEnum.ACTIVE,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    return user


# ==================== Token / Header Fixtures ====================

def _make_token(user_id: int, username: str, role: str) -> str:
    return create_access_token(
        data={"sub": username, "user_id": user_id, "role": role},
        expires_delta=timedelta(hours=8),
    )

def _make_expired_token(user_id: int, username: str, role: str) -> str:
    return create_access_token(
        data={"sub": username, "user_id": user_id, "role": role},
        expires_delta=timedelta(seconds=-1),
    )

@pytest.fixture
def admin_token(admin_user):
    return _make_token(admin_user.id, admin_user.username, "admin")

@pytest.fixture
def teacher_token(teacher_user):
    return _make_token(teacher_user.id, teacher_user.username, "teacher")

@pytest.fixture
def student_token(student_user):
    return _make_token(student_user.id, student_user.username, "student")

@pytest.fixture
def student2_token(student_user_2):
    return _make_token(student_user_2.id, student_user_2.username, "student")

@pytest.fixture
def expired_token(teacher_user):
    return _make_expired_token(teacher_user.id, teacher_user.username, "teacher")

@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def teacher_headers(teacher_token):
    return {"Authorization": f"Bearer {teacher_token}"}

@pytest.fixture
def student_headers(student_token):
    return {"Authorization": f"Bearer {student_token}"}

@pytest.fixture
def student2_headers(student2_token):
    return {"Authorization": f"Bearer {student2_token}"}

@pytest.fixture
def expired_headers(expired_token):
    return {"Authorization": f"Bearer {expired_token}"}

@pytest.fixture
def no_auth_headers():
    return {}


# ==================== Domain Seed Fixtures ====================

@pytest.fixture
def sample_classroom(db_session, teacher_user, student_user):
    classroom = Classroom(
        id=100, name="测试课堂-数据分析基础",
        description="Phase 2 测试用课堂",
        teacher_id=teacher_user.id,
        start_date=datetime(2026, 3, 1),
        end_date=datetime(2026, 7, 1),
        status=ClassroomStatusEnum.ONGOING, student_count=1,
    )
    db_session.add(classroom)
    db_session.flush()
    cs = ClassroomStudent(classroom_id=100, student_id=student_user.id)
    db_session.add(cs)
    db_session.commit()
    db_session.refresh(classroom)
    return classroom


@pytest.fixture
def ended_classroom(db_session, teacher_user):
    classroom = Classroom(
        id=101, name="历史课堂-已结束",
        teacher_id=teacher_user.id,
        start_date=datetime(2025, 3, 1),
        end_date=datetime(2025, 7, 1),
        status=ClassroomStatusEnum.ENDED,
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)
    return classroom


@pytest.fixture
def sample_practice(db_session, teacher_user):
    practice = Practice(
        id=200, title="Python 数据清洗入门",
        description="测试实践课程",
        direction="数据科学", category="数据清洗",
        difficulty=DifficultyLevelEnum.beginner,
        task_count=2, creator_id=teacher_user.id,
        publish_status=PracticePublishStatusEnum.PUBLISHED,
        visibility=PracticeVisibilityEnum.PRIVATE,
    )
    db_session.add(practice)
    db_session.flush()
    task1 = Task(
        id=300, practice_id=200, title="关卡1: 读取CSV",
        task_type=TaskTypeEnum.CODE, order_in_practice=0, coin=10,
    )
    task2 = Task(
        id=301, practice_id=200, title="关卡2: 清洗缺失值",
        task_type=TaskTypeEnum.CODE, order_in_practice=1, coin=20,
    )
    db_session.add_all([task1, task2])
    db_session.commit()
    db_session.refresh(practice)
    return practice


@pytest.fixture
def sample_exam(db_session, teacher_user, sample_classroom):
    paper = TestPaper(
        id=400, title="期中测试", creator_id=teacher_user.id,
        total_score=100, difficulty=DifficultyEnum.INTERMEDIATE,
    )
    db_session.add(paper)
    db_session.flush()
    q1 = Question(
        id="q_001",
        content="Python 中 list 和 tuple 的区别是什么？",
        question_type=QuestionTypeEnum.SINGLE_CHOICE,
        options='["可变 vs 不可变", "有序 vs 无序", "没有区别", "以上都不对"]',
        correct_answers='["A"]',
        difficulty=DifficultyEnum.BEGINNER, creator_id=teacher_user.id,
    )
    db_session.add(q1)
    db_session.flush()
    tpq = TestPaperQuestion(
        test_paper_id=400, question_id="q_001",
        score_for_question=10, order_in_paper=0,
    )
    db_session.add(tpq)
    db_session.flush()
    exam = ClassroomExam(
        id=500, classroom_id=sample_classroom.id, test_paper_id=400,
        title="期中测试",
        exam_start_time=datetime(2026, 4, 15, 9, 0),
        exam_end_time=datetime(2026, 4, 15, 11, 0),
        duration_minutes=90, pass_mark=60,
        status=ExamStatusEnum.UNPUBLISHED,
        created_by_teacher_id=teacher_user.id,
    )
    db_session.add(exam)
    db_session.commit()
    db_session.refresh(exam)
    return exam
