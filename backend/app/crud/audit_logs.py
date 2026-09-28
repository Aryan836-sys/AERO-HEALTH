from sqlalchemy.orm import Session

from app.models import AuditLog


def record_action(
    db: Session,
    actor_id: int,
    action: str,
    target_type: str,
    target_id: int,
    detail: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_actions(db: Session, limit: int = 100) -> list[AuditLog]:
    return db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
