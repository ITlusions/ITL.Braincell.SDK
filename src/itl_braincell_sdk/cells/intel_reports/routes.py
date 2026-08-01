"""Intel report routes"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.intel_reports.model import IntelReport
from itl_braincell_sdk.cells.intel_reports.schema import IntelReportCreate, IntelReportResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=IntelReportResponse, status_code=status.HTTP_201_CREATED)
async def create_intel_report(report: IntelReportCreate, db: Session = Depends(get_db)):
    db_report = IntelReport(**schema_to_db_kwargs(report))
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    weaviate = get_weaviate_service()
    weaviate.index_intel_report(
        str(db_report.id), db_report.title,
        db_report.summary, db_report.content
    )
    return db_report


@router.get("", response_model=list[IntelReportResponse])
async def get_intel_reports(
    classification: str | None = None,
    tlp: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(IntelReport)
    if classification:
        query = query.filter(IntelReport.classification_level == classification)
    if tlp:
        query = query.filter(IntelReport.tlp_level == tlp)
    return query.order_by(IntelReport.report_date.desc()).all()


@router.get("/{report_id}", response_model=IntelReportResponse)
async def get_intel_report(report_id: UUID, db: Session = Depends(get_db)):
    report = db.query(IntelReport).filter(IntelReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intel report not found")
    return report


@router.put("/{report_id}", response_model=IntelReportResponse)
async def update_intel_report(
    report_id: UUID, report_update: IntelReportCreate, db: Session = Depends(get_db)
):
    report = db.query(IntelReport).filter(IntelReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intel report not found")
    for field, value in report_update.model_dump(exclude_unset=True).items():
        setattr(report, field, value)
    db.commit()
    db.refresh(report)
    return report
