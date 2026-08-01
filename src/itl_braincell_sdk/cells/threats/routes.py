"""Threat actor routes"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.threats.model import ThreatActor
from itl_braincell_sdk.cells.threats.schema import ThreatActorCreate, ThreatActorResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ThreatActorResponse, status_code=status.HTTP_201_CREATED)
async def create_threat_actor(actor: ThreatActorCreate, db: Session = Depends(get_db)):
    db_actor = ThreatActor(**schema_to_db_kwargs(actor))
    db.add(db_actor)
    db.commit()
    db.refresh(db_actor)
    weaviate = get_weaviate_service()
    weaviate.index_threat_actor(
        str(db_actor.id), db_actor.name,
        db_actor.classification, db_actor.motivation, db_actor.ttps or []
    )
    return db_actor


@router.get("", response_model=list[ThreatActorResponse])
async def get_threat_actors(status_filter: str = "active", db: Session = Depends(get_db)):
    return (
        db.query(ThreatActor)
        .filter(ThreatActor.status == status_filter)
        .order_by(ThreatActor.last_seen.desc())
        .all()
    )


@router.get("/{actor_id}", response_model=ThreatActorResponse)
async def get_threat_actor(actor_id: UUID, db: Session = Depends(get_db)):
    actor = db.query(ThreatActor).filter(ThreatActor.id == actor_id).first()
    if not actor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threat actor not found")
    return actor


@router.put("/{actor_id}", response_model=ThreatActorResponse)
async def update_threat_actor(
    actor_id: UUID, actor_update: ThreatActorCreate, db: Session = Depends(get_db)
):
    actor = db.query(ThreatActor).filter(ThreatActor.id == actor_id).first()
    if not actor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threat actor not found")
    for field, value in actor_update.model_dump(exclude_unset=True).items():
        setattr(actor, field, value)
    db.commit()
    db.refresh(actor)
    return actor


@router.delete("/{actor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_threat_actor(actor_id: UUID, db: Session = Depends(get_db)):
    actor = db.query(ThreatActor).filter(ThreatActor.id == actor_id).first()
    if not actor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threat actor not found")
    db.delete(actor)
    db.commit()
