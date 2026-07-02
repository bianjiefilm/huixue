"""
慧学 验收测试 - 共享 Fixtures
真实数据库（SQLite），禁止 mock，使用 FastAPI TestClient
"""
import os
import sys
import pytest
import tempfile

# 在导入 app 之前设置环境变量，确保使用可写的 SQLite
_db_path = os.path.join(tempfile.gettempdir(), "huixue_acceptance_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

# 确保 backend 目录在 sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.models import (
    User, Course, Practice, Task, Classroom, ClassroomStudent,
    ClassroomPractice, ClassroomExam, Question, StudentExamAttempt,
    ClassroomStatusEnum, ExamStatusEnum, PracticePublishStatusEnum,
    Training,
)

# ============================================================
# 数据库 Engine & Session（真实 SQLite）
# ============================================================
TEST_DB_URL = f"sqlite:///{_db_path}"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# 全局覆盖 DI
app.dependency_overrides[get_db] = override_get_db


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Session 级别：创建所有表并种入基础组织数据"""
    # Import all models to ensure they are registered
    from app.models import models as _  # noqa
    try:
        from app.models import organization as _o  # noqa
    except Exception:
        pass
    Base.metadata.create_all(bind=engine)

    # Seed minimal organization data needed for UserProfile FK constraints
    db = TestingSessionLocal()
    try:
        from app.models.organization import School
        school = db.query(School).first()
        if not school:
            school = School(id=1, name="测试学校", code="TEST001", is_active=True)
            db.add(school)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning: Could not seed school: {e}")
    finally:
        db.close()

    yield


@pytest.fixture(scope="session")
def client():
    """Session 级别的 TestClient"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def db_session():
    """Session 级别的 DB session（自动回滚脏事务）"""
    db = TestingSessionLocal()
    yield db
    try:
        db.rollback()
    except Exception:
        pass
    db.close()


@pytest.fixture(scope="session")
def seed_users(db_session):
    """创建测试用户（真实数据库记录）"""
    from app.core.security import get_password_hash

    users_data = [
        {"id": 1, "username": "admin", "email": "admin@test.com",
         "full_name": "管理员", "is_superuser": True, "is_active": True},
        {"id": 29, "username": "teacher1", "email": "teacher1@test.com",
         "full_name": "教师张三", "is_superuser": False, "is_active": True},
        {"id": 30, "username": "student1", "email": "student1@test.com",
         "full_name": "学生李四", "is_superuser": False, "is_active": True},
        {"id": 31, "username": "student2", "email": "student2@test.com",
         "full_name": "学生王五", "is_superuser": False, "is_active": True},
        {"id": 32, "username": "student3", "email": "student3@test.com",
         "full_name": "学生赵六", "is_superuser": False, "is_active": True},
        {"id": 99, "username": "disabled_user", "email": "disabled@test.com",
         "full_name": "停用用户", "is_superuser": False, "is_active": False},
    ]

    created = {}
    for u in users_data:
        existing = db_session.query(User).filter(User.id == u["id"]).first()
        if not existing:
            user = User(
                id=u["id"],
                username=u["username"],
                email=u["email"],
                full_name=u["full_name"],
                hashed_password=get_password_hash("test123"),
                is_superuser=u["is_superuser"],
                is_active=u["is_active"],
                total_coins=0,
            )
            db_session.add(user)
            created[u["username"]] = user
        else:
            created[u["username"]] = existing

    # Create UserProfile records if the table exists
    try:
        from app.models.models import UserProfile
        role_map = {
            "admin": "ADMIN", "teacher1": "TEACHER",
            "student1": "STUDENT", "student2": "STUDENT",
            "student3": "STUDENT", "disabled_user": "STUDENT",
        }
        for uname, role_val in role_map.items():
            user_obj = created.get(uname)
            if user_obj:
                existing_profile = db_session.query(UserProfile).filter(
                    UserProfile.user_id == user_obj.id
                ).first()
                if not existing_profile:
                    profile = UserProfile(
                        user_id=user_obj.id,
                        user_type=role_val,
                        school_id=1,
                        real_name=user_obj.full_name or uname,
                    )
                    db_session.add(profile)
    except Exception as e:
        print(f"Warning: Could not create UserProfile: {e}")

    db_session.commit()
    return created


@pytest.fixture(scope="session")
def admin_token(client, seed_users):
    """获取管理员 token（依赖 seed_users 确保用户已在DB中）"""
    resp = client.post("/api/login", json={
        "username": "admin", "password": "admin123"
    })
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("token", {}).get("access_token", "")
        return token
    return ""


@pytest.fixture(scope="session")
def teacher_token(client, seed_users):
    """获取教师 token"""
    resp = client.post("/api/login", json={
        "username": "teacher1", "password": "teacher123"
    })
    if resp.status_code == 200:
        data = resp.json()
        return data.get("token", {}).get("access_token", "")
    return ""


@pytest.fixture(scope="session")
def student_token(client, seed_users):
    """获取学生 token"""
    resp = client.post("/api/login", json={
        "username": "student1", "password": "student123"
    })
    if resp.status_code == 200:
        data = resp.json()
        return data.get("token", {}).get("access_token", "")
    return ""


def auth_header(token: str) -> dict:
    """Helper: 返回 Authorization header"""
    return {"Authorization": f"Bearer {token}"}
