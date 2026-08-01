"""IOC routes"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.iocs.model import IOC
from itl_braincell_sdk.cells.iocs.schema import IOCCreate, IOCResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=IOCResponse, status_code=status.HTTP_201_CREATED)
async def create_ioc(ioc: IOCCreate, db: Session = Depends(get_db)):
    # Deduplicate by type + value
    existing = db.query(IOC).filter(IOC.type == ioc.type, IOC.value == ioc.value).first()
    if existing:
        for field, value in ioc.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    db_ioc = IOC(**schema_to_db_kwargs(ioc))
    db.add(db_ioc)
    db.commit()
    db.refresh(db_ioc)
    weaviate = get_weaviate_service()
    weaviate.index_ioc(str(db_ioc.id), db_ioc.type, db_ioc.value, db_ioc.context)
    return db_ioc


@router.get("", response_model=list[IOCResponse])
async def get_iocs(
    ioc_type: str | None = None,
    status_filter: str = "active",
    db: Session = Depends(get_db),
):
    query = db.query(IOC).filter(IOC.status == status_filter)
    if ioc_type:
        query = query.filter(IOC.type == ioc_type)
    return query.order_by(IOC.last_seen.desc()).all()


@router.get("/lookup/{value}", response_model=list[IOCResponse])
async def lookup_ioc(value: str, db: Session = Depends(get_db)):
    """Exact-match lookup by IOC value."""
    return db.query(IOC).filter(IOC.value == value).all()


@router.get("/{ioc_id}", response_model=IOCResponse)
async def get_ioc(ioc_id: UUID, db: Session = Depends(get_db)):
    ioc = db.query(IOC).filter(IOC.id == ioc_id).first()
    if not ioc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IOC not found")
    return ioc


@router.put("/{ioc_id}", response_model=IOCResponse)
async def update_ioc(ioc_id: UUID, ioc_update: IOCCreate, db: Session = Depends(get_db)):
    ioc = db.query(IOC).filter(IOC.id == ioc_id).first()
    if not ioc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IOC not found")
    for field, value in ioc_update.model_dump(exclude_unset=True).items():
        setattr(ioc, field, value)
    db.commit()
    db.refresh(ioc)
    return ioc
