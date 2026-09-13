from sqlalchemy.orm import Session

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
    query = db.query(PollutionReport)
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
