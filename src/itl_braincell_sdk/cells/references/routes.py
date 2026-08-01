"""References routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.references.model import Reference
from itl_braincell_sdk.cells.references.schema import ReferenceCreate, ReferenceResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

router = APIRouter()


@router.post("", response_model=ReferenceResponse, status_code=status.HTTP_201_CREATED)
async def create_reference(ref: ReferenceCreate, db: Session = Depends(get_db)):
    db_ref = Reference(**schema_to_db_kwargs(ref))
    db.add(db_ref)
    db.commit()
    db.refresh(db_ref)
    return db_ref


@router.get("", response_model=list[ReferenceResponse])
async def list_references(
    category: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Reference)
    if category:
        query = query.filter(Reference.category == category)
    return query.order_by(Reference.created_at.desc()).limit(limit).all()


@router.get("/{ref_id}", response_model=ReferenceResponse)
async def get_reference(ref_id: UUID, db: Session = Depends(get_db)):
    ref = db.query(Reference).filter(Reference.id == ref_id).first()
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference not found")
    return ref


@router.put("/{ref_id}", response_model=ReferenceResponse)
async def update_reference(ref_id: UUID, ref_update: ReferenceCreate, db: Session = Depends(get_db)):
    ref = db.query(Reference).filter(Reference.id == ref_id).first()
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference not found")
    for key, value in ref_update.model_dump(exclude_unset=True).items():
        setattr(ref, key, value)
    db.commit()
    db.refresh(ref)
    return ref


@router.delete("/{ref_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reference(ref_id: UUID, db: Session = Depends(get_db)):
    ref = db.query(Reference).filter(Reference.id == ref_id).first()
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference not found")
    db.delete(ref)
    db.commit()
    return None
