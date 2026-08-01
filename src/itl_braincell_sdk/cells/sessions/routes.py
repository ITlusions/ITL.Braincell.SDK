"""Sessions routes"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.sessions.model import MemorySession
from itl_braincell_sdk.cells.sessions.schema import MemorySessionCreate, MemorySessionResponse, MemorySessionUpdate
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=MemorySessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(session: MemorySessionCreate, db: Session = Depends(get_db)):
    db_session = MemorySession(**schema_to_db_kwargs(session))
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    weaviate = get_weaviate_service()
    success = weaviate.index_memory_session(
        str(db_session.id), db_session.session_name, db_session.summary, db_session.status
    )
    if not success:
        logger.warning("Failed to sync memory session %s to Weaviate", db_session.id)

    return db_session


@router.get("/{session_id}", response_model=MemorySessionResponse)
async def get_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(MemorySession).filter(MemorySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.put("/{session_id}", response_model=MemorySessionResponse)
async def update_session(
    session_id: UUID, session_update: MemorySessionUpdate, db: Session = Depends(get_db)
):
    session = db.query(MemorySession).filter(MemorySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    for key, value in session_update.model_dump(exclude_unset=True).items():
        setattr(session, key, value)
    db.commit()
    db.refresh(session)

    weaviate = get_weaviate_service()
    weaviate.update_memory_session(
        str(session.id),
        session_name=session.session_name,
        summary=session.summary,
        status=session.status,
    )
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(MemorySession).filter(MemorySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    db.delete(session)
    db.commit()

    weaviate = get_weaviate_service()
    weaviate.delete_memory_session(str(session_id))
    return None
