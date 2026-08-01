"""Files discussed routes"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.files_discussed.model import FileDiscussed
from itl_braincell_sdk.cells.files_discussed.schema import FileDiscussedCreate, FileDiscussedResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=FileDiscussedResponse, status_code=status.HTTP_201_CREATED)
async def create_file_discussed(file: FileDiscussedCreate, db: Session = Depends(get_db)):
    db_file = db.query(FileDiscussed).filter(FileDiscussed.file_path == file.file_path).first()
    if db_file:
        db_file.discussion_count += 1
        db.commit()
        db.refresh(db_file)
        return db_file

    db_file = FileDiscussed(**schema_to_db_kwargs(file))
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    weaviate = get_weaviate_service()
    success = weaviate.index_file_discussed(
        str(db_file.id), db_file.file_path, db_file.description, db_file.language, db_file.purpose
    )
    if not success:
        logger.warning("Failed to sync file %s to Weaviate", db_file.id)

    return db_file


@router.get("", response_model=list[FileDiscussedResponse])
async def get_discussed_files(language: str = None, db: Session = Depends(get_db)):
    query = db.query(FileDiscussed)
    if language:
        query = query.filter(FileDiscussed.language == language)
    return query.order_by(FileDiscussed.discussion_count.desc()).all()


@router.put("/{file_id}", response_model=FileDiscussedResponse)
async def update_file_discussed(
    file_id: UUID, file_update: FileDiscussedCreate, db: Session = Depends(get_db)
):
    file = db.query(FileDiscussed).filter(FileDiscussed.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    for key, value in file_update.model_dump(exclude_unset=True).items():
        setattr(file, key, value)
    db.commit()
    db.refresh(file)

    weaviate = get_weaviate_service()
    weaviate.update_file_discussed(str(file.id), description=file.description, purpose=file.purpose)
    return file


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_discussed(file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(FileDiscussed).filter(FileDiscussed.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    db.delete(file)
    db.commit()

    weaviate = get_weaviate_service()
    weaviate.delete_file_discussed(str(file_id))
    return None
