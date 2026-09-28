import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.crud.audit_logs import create_audit_log, list_audit_logs
from app.models.audit_log import AuditLog


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    AuditLog.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_audit_log_stores_the_action(db_session):
    entry = create_audit_log(
        db_session,
        admin_user_id=1,
        action="report_status_update",
        target_type="pollution_report",
        target_id=7,
        detail="unverified -> verified",
    )
    assert entry.id is not None
    assert entry.admin_user_id == 1
    assert entry.target_id == 7
    assert entry.detail == "unverified -> verified"


def test_list_audit_logs_returns_newest_first(db_session):
    create_audit_log(db_session, admin_user_id=1, action="a", target_type="x", target_id=1)
    create_audit_log(db_session, admin_user_id=1, action="b", target_type="x", target_id=2)

    entries = list_audit_logs(db_session)
    assert len(entries) == 2
    assert entries[0].action == "b"  # most recently created comes first


def test_list_audit_logs_respects_the_limit(db_session):
    for i in range(5):
        create_audit_log(db_session, admin_user_id=1, action="a", target_type="x", target_id=i)

    entries = list_audit_logs(db_session, limit=2)
    assert len(entries) == 2