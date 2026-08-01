"""Errors routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.errors.model import CellError
from itl_braincell_sdk.cells.errors.schema import ErrorCreate, ErrorResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

router = APIRouter()


@router.post("", response_model=ErrorResponse, status_code=status.HTTP_201_CREATED)
async def create_error(error: ErrorCreate, db: Session = Depends(get_db)):
    db_error = CellError(**schema_to_db_kwargs(error))
    db.add(db_error)
    db.commit()
    db.refresh(db_error)
    return db_error


@router.get("", response_model=list[ErrorResponse])
async def list_errors(
    status_filter: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(CellError)
    if status_filter:
        query = query.filter(CellError.status == status_filter)
    return query.order_by(CellError.created_at.desc()).limit(limit).all()


@router.get("/open", response_model=list[ErrorResponse])
async def list_open_errors(limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(CellError)
        .filter(CellError.status == "open")
        .order_by(CellError.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/{error_id}", response_model=ErrorResponse)
async def get_error(error_id: UUID, db: Session = Depends(get_db)):
    row = db.query(CellError).filter(CellError.id == error_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error not found")
    return row


@router.put("/{error_id}", response_model=ErrorResponse)
async def update_error(error_id: UUID, error_update: ErrorCreate, db: Session = Depends(get_db)):
    row = db.query(CellError).filter(CellError.id == error_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error not found")
    for key, value in error_update.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.post("/{error_id}/resolve", response_model=ErrorResponse)
async def resolve_error(error_id: UUID, resolution: str, db: Session = Depends(get_db)):
    """Mark an error as resolved and record how it was fixed."""
    row = db.query(CellError).filter(CellError.id == error_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error not found")
    row.status = "resolved"
    row.resolution = resolution
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{error_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_error(error_id: UUID, db: Session = Depends(get_db)):
    row = db.query(CellError).filter(CellError.id == error_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error not found")
    db.delete(row)
    db.commit()
    return None
