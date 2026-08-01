"""Architecture notes routes"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.architecture_notes.model import ArchitectureNote
from itl_braincell_sdk.cells.architecture_notes.schema import ArchitectureNoteCreate, ArchitectureNoteResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ArchitectureNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_architecture_note(note: ArchitectureNoteCreate, db: Session = Depends(get_db)):
    db_note = ArchitectureNote(**schema_to_db_kwargs(note))
    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    weaviate = get_weaviate_service()
    success = weaviate.index_architecture_note(
        str(db_note.id), db_note.component, db_note.description, db_note.type, db_note.tags
    )
    if not success:
        logger.warning("Failed to sync architecture note %s to Weaviate", db_note.id)

    return db_note


@router.get("", response_model=list[ArchitectureNoteResponse])
async def get_architecture_notes(component: str = None, db: Session = Depends(get_db)):
    query = db.query(ArchitectureNote)
    if component:
        query = query.filter(ArchitectureNote.component.contains(component))
    return query.order_by(ArchitectureNote.updated_at.desc()).all()


@router.put("/{note_id}", response_model=ArchitectureNoteResponse)
async def update_architecture_note(
    note_id: UUID, note_update: ArchitectureNoteCreate, db: Session = Depends(get_db)
):
    note = db.query(ArchitectureNote).filter(ArchitectureNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Architecture note not found")

    for key, value in note_update.model_dump(exclude_unset=True).items():
        setattr(note, key, value)
    db.commit()
    db.refresh(note)

    weaviate = get_weaviate_service()
    weaviate.update_architecture_note(
        str(note.id), component=note.component, description=note.description, note_type=note.type
    )
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_architecture_note(note_id: UUID, db: Session = Depends(get_db)):
    note = db.query(ArchitectureNote).filter(ArchitectureNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Architecture note not found")

    db.delete(note)
    db.commit()

    weaviate = get_weaviate_service()
    weaviate.delete_architecture_note(str(note_id))
    return None
