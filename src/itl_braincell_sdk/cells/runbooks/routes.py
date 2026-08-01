"""Runbooks routes."""
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.runbooks.model import Runbook
from itl_braincell_sdk.cells.runbooks.schema import RunbookCreate, RunbookResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=RunbookResponse, status_code=status.HTTP_201_CREATED)
async def create_runbook(runbook: RunbookCreate, db: Session = Depends(get_db)):
    db_runbook = Runbook(**schema_to_db_kwargs(runbook))
    db.add(db_runbook)
    db.commit()
    db.refresh(db_runbook)
    return db_runbook


@router.get("", response_model=list[RunbookResponse])
async def list_runbooks(
    category: str | None = None,
    severity: str | None = None,
    service: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Runbook)
    if category:
        query = query.filter(Runbook.category == category)
    if severity:
        query = query.filter(Runbook.severity == severity)
    if service:
        query = query.filter(Runbook.services.contains([service]))
    return query.order_by(Runbook.created_at.desc()).all()


@router.get("/{runbook_id}", response_model=RunbookResponse)
async def get_runbook(runbook_id: UUID, db: Session = Depends(get_db)):
    runbook = db.query(Runbook).filter(Runbook.id == runbook_id).first()
    if not runbook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Runbook not found")
    return runbook


@router.post("/{runbook_id}/mark-used", response_model=RunbookResponse)
async def mark_runbook_used(runbook_id: UUID, db: Session = Depends(get_db)):
    """Record that this runbook was executed now."""
    runbook = db.query(Runbook).filter(Runbook.id == runbook_id).first()
    if not runbook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Runbook not found")
    runbook.last_used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(runbook)
    return runbook


@router.put("/{runbook_id}", response_model=RunbookResponse)
async def update_runbook(runbook_id: UUID, runbook_update: RunbookCreate, db: Session = Depends(get_db)):
    runbook = db.query(Runbook).filter(Runbook.id == runbook_id).first()
    if not runbook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Runbook not found")
    for key, value in runbook_update.model_dump(exclude_unset=True).items():
        setattr(runbook, key, value)
    db.commit()
    db.refresh(runbook)
    return runbook


@router.delete("/{runbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_runbook(runbook_id: UUID, db: Session = Depends(get_db)):
    runbook = db.query(Runbook).filter(Runbook.id == runbook_id).first()
    if not runbook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Runbook not found")
    db.delete(runbook)
    db.commit()
    return None
