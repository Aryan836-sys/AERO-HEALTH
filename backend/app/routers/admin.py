"""Day 9 (extended): admin-only moderation, stats, and the audit trail
those actions write to. Every route here is gated by require_role("admin")
-- there is currently no way to become an admin except the bootstrap
script (see scripts/promote_admin.py), by design: promotion should never
be reachable over the API itself.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.crud.audit_logs import create_audit_log, list_audit_logs
from app.crud.pollution_reports import list_reports, update_report_status
from app.database import get_db
from app.models import Location, PollutionReport, User, UserAlert
from app.schemas.admin import AdminStatsOut, AuditLogOut, ReportStatusUpdate
from app.schemas.report import ReportOut

router = APIRouter(prefix="/admin", tags=["admin"])

_require_admin = require_role("admin")


@router.get("/reports", response_model=list[ReportOut])
def read_moderation_queue(
    verification_status: str | None = "unverified",
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Defaults to just the unverified ones -- the actual moderation
    queue -- but pass verification_status=None to see every report
    regardless of status, e.g. to review past decisions."""
    return list_reports(db, verification_status=verification_status)


@router.patch("/reports/{report_id}", response_model=ReportOut)
def moderate_report(
    report_id: int,
    payload: ReportStatusUpdate,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    report = update_report_status(db, report_id, payload.verification_status)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    create_audit_log(
        db,
        admin_user_id=admin.id,
        action="report_status_update",
        target_type="pollution_report",
        target_id=report_id,
        detail=f"-> {payload.verification_status}",
    )
    return report


@router.get("/stats", response_model=AdminStatsOut)
def read_admin_stats(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    reports_by_status = {
        s: db.query(PollutionReport).filter(PollutionReport.verification_status == s).count()
        for s in ("unverified", "verified", "rejected", "flagged")
    }
    return AdminStatsOut(
        total_users=db.query(User).count(),
        total_locations=db.query(Location).count(),
        total_reports=db.query(PollutionReport).count(),
        reports_by_status=reports_by_status,
        active_alerts=db.query(UserAlert).filter(UserAlert.active.is_(True)).count(),
    )


@router.get("/audit-log", response_model=list[AuditLogOut])
def read_audit_log(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    return list_audit_logs(db)