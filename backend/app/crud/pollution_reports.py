from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models import PollutionReport


def create_report(
    db: Session,
    location_id: int,
    category: str,
    user_id: int | None = None,
    description: str | None = None,
    image_url: str | None = None,
    severity: str | None = None,
) -> PollutionReport:
    """user_id is optional -- anonymous reports are allowed. Always starts
    'unverified' (the model's default); moderation flips it via
    update_report_status."""
    report = PollutionReport(
        user_id=user_id,
        location_id=location_id,
        category=category,
        description=description,
        image_url=image_url,
        severity=severity,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def list_reports(
    db: Session, verification_status: str | None = None
) -> list[PollutionReport]:
    """All reports, optionally filtered by status -- e.g. the admin
    moderation queue calls this with 'unverified'."""
    query = db.query(PollutionReport).options(joinedload(PollutionReport.location))
    if verification_status is not None:
        query = query.filter(PollutionReport.verification_status == verification_status)
    return query.order_by(PollutionReport.created_at.desc()).all()


def update_report_status(
    db: Session, report_id: int, verification_status: str
) -> PollutionReport | None:
    report = db.get(PollutionReport, report_id)
    if report is not None:
        report.verification_status = verification_status
        db.commit()
        db.refresh(report)
    return report


def get_report(db: Session, report_id: int) -> PollutionReport | None:
    return db.get(PollutionReport, report_id)


def list_public_reports(
    db: Session,
    statuses: tuple[str, ...] = ("unverified", "verified"),
    location_ids: list[int] | None = None,
    limit: int = 50,
) -> list[PollutionReport]:
    """Recent reports safe to show publicly (rejected/flagged are hidden),
    newest first, optionally limited to a set of locations."""
    query = (
        db.query(PollutionReport)
        .options(joinedload(PollutionReport.location))
        .filter(PollutionReport.verification_status.in_(statuses))
    )
    if location_ids is not None:
        query = query.filter(PollutionReport.location_id.in_(location_ids))
    return query.order_by(PollutionReport.created_at.desc()).limit(limit).all()


def count_reports_by_category(db: Session) -> dict[str, int]:
    rows = (
        db.query(PollutionReport.category, func.count(PollutionReport.id))
        .group_by(PollutionReport.category)
        .all()
    )
    return {category: count for category, count in rows}


def count_reports(db: Session, verification_status: str | None = None) -> int:
    query = db.query(func.count(PollutionReport.id))
    if verification_status is not None:
        query = query.filter(PollutionReport.verification_status == verification_status)
    return query.scalar()


def list_image_urls_for_user(db: Session, user_id: int) -> list[str]:
    rows = (
        db.query(PollutionReport.image_url)
        .filter(PollutionReport.user_id == user_id, PollutionReport.image_url.isnot(None))
        .all()
    )
    return [url for (url,) in rows]
