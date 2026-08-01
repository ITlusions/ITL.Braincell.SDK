"""Decisions routes"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.decisions.model import DesignDecision
from itl_braincell_sdk.cells.decisions.schema import DecisionCreate, DecisionResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
async def create_decision(decision: DecisionCreate, db: Session = Depends(get_db)):
    db_decision = DesignDecision(**schema_to_db_kwargs(decision))
    db.add(db_decision)
    db.commit()
    db.refresh(db_decision)

    weaviate = get_weaviate_service()
    weaviate.index_decision(str(db_decision.id), db_decision.decision, db_decision.rationale)
    return db_decision


@router.get("", response_model=list[DecisionResponse])
async def get_decisions(status_filter: str = "active", db: Session = Depends(get_db)):
    return (
        db.query(DesignDecision)
        .filter(DesignDecision.status == status_filter)
        .order_by(DesignDecision.date_made.desc())
        .all()
    )


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(decision_id: UUID, db: Session = Depends(get_db)):
    decision = db.query(DesignDecision).filter(DesignDecision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")
    return decision


@router.put("/{decision_id}", response_model=DecisionResponse)
async def update_decision(
    decision_id: UUID, decision_update: DecisionCreate, db: Session = Depends(get_db)
):
    decision = db.query(DesignDecision).filter(DesignDecision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")

    for key, value in decision_update.model_dump(exclude_unset=True).items():
        setattr(decision, key, value)
    db.commit()
    db.refresh(decision)

    weaviate = get_weaviate_service()
    weaviate.index_decision(str(decision.id), decision.decision, decision.rationale)
    return decision


@router.delete("/{decision_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_decision(decision_id: UUID, db: Session = Depends(get_db)):
    decision = db.query(DesignDecision).filter(DesignDecision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")

    db.delete(decision)
    db.commit()

    weaviate = get_weaviate_service()
    weaviate.delete_decision(str(decision_id))
    return None
