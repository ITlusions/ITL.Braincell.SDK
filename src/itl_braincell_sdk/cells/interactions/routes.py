"""Interactions routes"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.interactions.model import Interaction
from itl_braincell_sdk.cells.interactions.schema import InteractionCreate, InteractionResponse, InteractionUpdate
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
async def create_interaction(
    interaction: InteractionCreate,
    db: Session = Depends(get_db),
):
    db_interaction = Interaction(**schema_to_db_kwargs(interaction))
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)

    weaviate = get_weaviate_service()
    success = weaviate.index_interaction(
        str(db_interaction.id),
        db_interaction.content,
        db_interaction.role,
        db_interaction.message_type,
        str(db_interaction.conversation_id),
        str(db_interaction.session_id),
    )
    if not success:
        logger.warning("Failed to sync interaction %s to Weaviate", db_interaction.id)

    return db_interaction


@router.get("/{interaction_id}", response_model=InteractionResponse)
async def get_interaction(interaction_id: UUID, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")
    return interaction


@router.get("/conversations/{conversation_id}", response_model=list[InteractionResponse])
async def get_conversation_interactions(conversation_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(Interaction)
        .filter(Interaction.conversation_id == conversation_id)
        .order_by(Interaction.timestamp.asc())
        .all()
    )


@router.put("/{interaction_id}", response_model=InteractionResponse)
async def update_interaction(
    interaction_id: UUID,
    interaction_update: InteractionUpdate,
    db: Session = Depends(get_db),
):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")

    for key, value in interaction_update.model_dump(exclude_unset=True).items():
        setattr(interaction, key, value)
    db.commit()
    db.refresh(interaction)

    weaviate = get_weaviate_service()
    weaviate.update_interaction(
        str(interaction.id),
        content=interaction.content,
        role=interaction.role,
        message_type=interaction.message_type,
    )
    return interaction


@router.delete("/{interaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interaction(interaction_id: UUID, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")

    db.delete(interaction)
    db.commit()

    weaviate = get_weaviate_service()
    weaviate.delete_interaction(str(interaction_id))
    return None
