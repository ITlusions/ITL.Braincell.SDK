"""Security incident routes"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.incidents.model import SecurityIncident
from itl_braincell_sdk.cells.incidents.schema import IncidentCreate, IncidentResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    db_incident = SecurityIncident(**schema_to_db_kwargs(incident))
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    weaviate = get_weaviate_service()
    weaviate.index_incident(
        str(db_incident.id), db_incident.title,
        db_incident.description, db_incident.severity
    )
    return db_incident


@router.get("", response_model=list[IncidentResponse])
async def get_incidents(status_filter: str = "open", db: Session = Depends(get_db)):
    return (
        db.query(SecurityIncident)
        .filter(SecurityIncident.status == status_filter)
        .order_by(SecurityIncident.detected_at.desc())
        .all()
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: UUID, db: Session = Depends(get_db)):
    incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.post("/{incident_id}/timeline", response_model=IncidentResponse)
async def add_timeline_event(
    incident_id: UUID,
    event: str,
    analyst: str | None = None,
    db: Session = Depends(get_db),
):
    incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, "analyst": analyst}
    current_timeline = list(incident.timeline or [])
    current_timeline.append(entry)
    incident.timeline = current_timeline
    db.commit()
    db.refresh(incident)
    return incident


@router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID, incident_update: IncidentCreate, db: Session = Depends(get_db)
):
    incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    for field, value in incident_update.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    db.commit()
    db.refresh(incident)
    return incident
