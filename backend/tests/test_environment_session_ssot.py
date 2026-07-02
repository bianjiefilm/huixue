from app.crud.crud import create_environment_session
from app.models.models import EnvironmentSession, Practice, SystemSetting
from app.models.models import DifficultyLevelEnum, PracticePublishStatusEnum, PracticeVisibilityEnum


def _add_practice(db_session, practice_id: int, title: str):
    practice = Practice(
        id=practice_id,
        title=title,
        direction="数据测试",
        category="资源控制",
        difficulty=DifficultyLevelEnum.beginner,
        publish_status=PracticePublishStatusEnum.PUBLISHED,
        visibility=PracticeVisibilityEnum.PUBLIC,
    )
    db_session.add(practice)
    db_session.commit()
    return practice


def _set_concurrent_enabled(db_session, enabled: bool):
    db_session.add(SystemSetting(
        key="concurrent_experiment_enabled",
        value="true" if enabled else "false",
        value_type="bool",
        category="experiment",
    ))
    db_session.commit()


def test_create_environment_session_stops_existing_when_db_setting_false(db_session, student_user):
    _set_concurrent_enabled(db_session, False)
    _add_practice(db_session, 990011, "LAB-RESOURCE-TEST-A")
    _add_practice(db_session, 990012, "LAB-RESOURCE-TEST-B")

    first = create_environment_session(db_session, 990011, student_user.id, "shell")
    second = create_environment_session(db_session, 990012, student_user.id, "desktop")

    db_session.refresh(first)
    db_session.refresh(second)

    assert first.status == "stopped"
    assert second.status == "active"


def test_create_environment_session_keeps_existing_when_db_setting_true(db_session, student_user):
    _set_concurrent_enabled(db_session, True)
    _add_practice(db_session, 990011, "LAB-RESOURCE-TEST-A")
    _add_practice(db_session, 990012, "LAB-RESOURCE-TEST-B")

    create_environment_session(db_session, 990011, student_user.id, "shell")
    create_environment_session(db_session, 990012, student_user.id, "desktop")

    active_count = db_session.query(EnvironmentSession).filter(
        EnvironmentSession.user_id == student_user.id,
        EnvironmentSession.status == "active",
    ).count()

    assert active_count == 2
