"""VulnReport routes — CRUD and status workflow for bug bounty / responsible disclosure dossiers."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.vuln_reports.model import VulnReport
from itl_braincell_sdk.cells.vuln_reports.schema import VulnReportCreate, VulnReportResponse, VulnReportStatusUpdate
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _index_in_weaviate(report: VulnReport) -> None:
    """Non-fatal Weaviate indexing call."""
    try:
        get_weaviate_service().index_vuln_report(
            embedding_id=str(report.id),
            title=report.title,
            summary=report.summary or "",
            vendor=report.vendor or "",
            product=report.product or "",
            cve_candidate=report.cve_candidate or "",
            owasp_category=report.owasp_category or "",
            status=report.status,
            severity=report.severity,
        )
    except Exception:
        logger.warning("Failed to index vuln_report %s in Weaviate", report.id)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("", response_model=VulnReportResponse, status_code=status.HTTP_201_CREATED)
async def create_vuln_report(entry: VulnReportCreate, db: Session = Depends(get_db)):
    """Create a new vulnerability report / bug bounty dossier."""
    db_entry = VulnReport(**schema_to_db_kwargs(entry))
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    _index_in_weaviate(db_entry)
    return db_entry


@router.get("", response_model=list[VulnReportResponse])
async def list_vuln_reports(
    status_filter: str | None = None,
    severity: str | None = None,
    vendor: str | None = None,
    bounty_program: str | None = None,
    db: Session = Depends(get_db),
):
    """List vulnerability reports, optionally filtered by status, severity, vendor, or bounty program."""
    q = db.query(VulnReport)
    if status_filter:
        q = q.filter(VulnReport.status == status_filter)
    if severity:
        q = q.filter(VulnReport.severity == severity)
    if vendor:
        q = q.filter(VulnReport.vendor.ilike(f"%{vendor}%"))
    if bounty_program:
        q = q.filter(VulnReport.bounty_program.ilike(f"%{bounty_program}%"))
    return q.order_by(VulnReport.created_at.desc()).all()


@router.get("/{report_id}", response_model=VulnReportResponse)
async def get_vuln_report(report_id: UUID, db: Session = Depends(get_db)):
    """Retrieve a single vulnerability report by ID."""
    report = db.query(VulnReport).filter(VulnReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VulnReport not found")
    return report


@router.patch("/{report_id}/status", response_model=VulnReportResponse)
async def update_status(
    report_id: UUID,
    update: VulnReportStatusUpdate,
    db: Session = Depends(get_db),
):
    """Advance the status of a vulnerability report (draft → submitted → triaged → accepted → paid).

    Also accepts: rejected / duplicate / disclosed.
    When status is 'accepted' or 'paid' and tlp_level is not provided, tlp_level is relaxed to AMBER.
    """
    report = db.query(VulnReport).filter(VulnReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VulnReport not found")

    report.status = update.status
    if update.submission_id:
        report.submission_id = update.submission_id
    if update.payout_amount is not None:
        report.payout_amount = update.payout_amount
    if update.payout_currency:
        report.payout_currency = update.payout_currency
    if update.tlp_level:
        report.tlp_level = update.tlp_level
    elif update.status in ("accepted", "paid", "disclosed") and report.tlp_level == "RED":
        report.tlp_level = "AMBER"

    db.commit()
    db.refresh(report)
    _index_in_weaviate(report)
    return report


@router.put("/{report_id}", response_model=VulnReportResponse)
async def update_vuln_report(
    report_id: UUID, update: VulnReportCreate, db: Session = Depends(get_db)
):
    """Full update of a vulnerability report."""
    report = db.query(VulnReport).filter(VulnReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VulnReport not found")
    for field, value in update.model_dump().items():
        setattr(report, field, value)
    db.commit()
    db.refresh(report)
    _index_in_weaviate(report)
    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vuln_report(report_id: UUID, db: Session = Depends(get_db)):
    """Permanently delete a vulnerability report."""
    report = db.query(VulnReport).filter(VulnReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VulnReport not found")
    db.delete(report)
    db.commit()
