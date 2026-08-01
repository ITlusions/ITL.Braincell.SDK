"""Kill chain routes — campaign-level attack lifecycle tracking."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.kill_chains.model import KillChain
from itl_braincell_sdk.cells.kill_chains.schema import KillChainCreate, KillChainPhaseUpdate, KillChainResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=KillChainResponse, status_code=status.HTTP_201_CREATED)
async def create_kill_chain(payload: KillChainCreate, db: Session = Depends(get_db)):
    row = KillChain(**schema_to_db_kwargs(payload))
    db.add(row)
    db.commit()
    db.refresh(row)
    try:
        weaviate = get_weaviate_service()
        weaviate.index_kill_chain(
            str(row.id),
            row.name,
            row.description,
            row.threat_actor_ref,
            row.objective,
        )
    except Exception:
        logger.warning("Weaviate indexing failed for kill chain %s — continuing", row.id)
    return row


@router.get("", response_model=list[KillChainResponse])
async def list_kill_chains(
    status_filter: str | None = None,
    framework: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(KillChain)
    if status_filter:
        q = q.filter(KillChain.status == status_filter)
    if framework:
        q = q.filter(KillChain.framework == framework)
    return q.order_by(KillChain.created_at.desc()).all()


@router.get("/{chain_id}", response_model=KillChainResponse)
async def get_kill_chain(chain_id: UUID, db: Session = Depends(get_db)):
    row = db.query(KillChain).filter(KillChain.id == chain_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kill chain not found")
    return row


@router.post("/{chain_id}/phases", response_model=KillChainResponse)
async def upsert_phase(
    chain_id: UUID,
    phase: KillChainPhaseUpdate,
    db: Session = Depends(get_db),
):
    """Add a new phase or update an existing phase (matched by `phase` name/ID)."""
    row = db.query(KillChain).filter(KillChain.id == chain_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kill chain not found")

    phases = list(row.phases or [])
    incoming = phase.model_dump(exclude_none=True)

    # Update existing phase if the phase name already exists
    for existing in phases:
        if existing.get("phase") == phase.phase:
            existing.update(incoming)
            break
    else:
        phases.append(incoming)

    phases.sort(key=lambda p: p.get("order", 999))
    row.phases = phases
    db.commit()
    db.refresh(row)
    return row


@router.put("/{chain_id}", response_model=KillChainResponse)
async def update_kill_chain(
    chain_id: UUID,
    payload: KillChainCreate,
    db: Session = Depends(get_db),
):
    row = db.query(KillChain).filter(KillChain.id == chain_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kill chain not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{chain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kill_chain(chain_id: UUID, db: Session = Depends(get_db)):
    row = db.query(KillChain).filter(KillChain.id == chain_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kill chain not found")
    db.delete(row)
    db.commit()
