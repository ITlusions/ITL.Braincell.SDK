"""Conversations routes"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.conversations.model import Conversation
from itl_braincell_sdk.cells.conversations.schema import ConversationCreate, ConversationResponse, ConversationUpdate
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conv: ConversationCreate,
    db: Session = Depends(get_db),
):
    db_conv = Conversation(**schema_to_db_kwargs(conv))
    db.add(db_conv)
    db.commit()
    db.refresh(db_conv)

    weaviate = get_weaviate_service()
    success = weaviate.index_conversation(
        str(db_conv.id), db_conv.topic, db_conv.summary, str(db_conv.session_id)
    )
    if not success:
        logger.warning("Failed to sync conversation %s to Weaviate", db_conv.id)

    return db_conv


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: UUID, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    conv_update: ConversationUpdate,
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    for key, value in conv_update.model_dump(exclude_unset=True).items():
        setattr(conv, key, value)
    db.commit()
    db.refresh(conv)

    weaviate = get_weaviate_service()
    weaviate.update_conversation(str(conv.id), topic=conv.topic, summary=conv.summary)
    return conv


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: UUID, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    db.delete(conv)
    db.commit()

    weaviate = get_weaviate_service()
    weaviate.delete_conversation(str(conversation_id))
    return None
