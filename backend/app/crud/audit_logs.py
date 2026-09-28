from sqlalchemy.orm import Session

from app.models import AuditLog


def create_audit_log(
    db: Session,
    admin_user_id: int,
    action: str,
    target_type: str,
    target_id: int,
    detail: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        admin_user_id=admin_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_audit_logs(db: Session, limit: int = 100) -> list[AuditLog]:
    """Newest first. Orders by id as a tiebreaker after created_at --
    two entries created within the same timestamp tick (SQLite's
    CURRENT_TIMESTAMP only has 1-second resolution; even Postgres could
    tie under fast concurrent actions) would otherwise sort
    unpredictably rather than in the order they actually happened."""
    return (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(limit)
        .all()
    )