"""Versions routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.versions.model import CellVersion
from itl_braincell_sdk.cells.versions.schema import VersionCreate, VersionResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

router = APIRouter()


@router.post("", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(version: VersionCreate, db: Session = Depends(get_db)):
    db_version = CellVersion(**schema_to_db_kwargs(version))
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version


@router.get("", response_model=list[VersionResponse])
async def list_versions(
    component: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(CellVersion)
    if component:
        query = query.filter(CellVersion.component == component)
    return query.order_by(CellVersion.created_at.desc()).limit(limit).all()


@router.get("/{version_id}", response_model=VersionResponse)
async def get_version(version_id: UUID, db: Session = Depends(get_db)):
    row = db.query(CellVersion).filter(CellVersion.id == version_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    return row


@router.put("/{version_id}", response_model=VersionResponse)
async def update_version(version_id: UUID, version_update: VersionCreate, db: Session = Depends(get_db)):
    row = db.query(CellVersion).filter(CellVersion.id == version_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    for key, value in version_update.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(version_id: UUID, db: Session = Depends(get_db)):
    row = db.query(CellVersion).filter(CellVersion.id == version_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    db.delete(row)
    db.commit()
    return None
