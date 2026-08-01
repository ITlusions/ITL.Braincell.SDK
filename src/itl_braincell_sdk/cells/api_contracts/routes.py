"""Api contracts routes."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.api_contracts.model import ApiContract
from itl_braincell_sdk.cells.api_contracts.schema import ApiContractCreate, ApiContractResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ApiContractResponse, status_code=status.HTTP_201_CREATED)
async def create_api_contract(contract: ApiContractCreate, db: Session = Depends(get_db)):
    db_contract = ApiContract(**schema_to_db_kwargs(contract))
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return db_contract


@router.get("", response_model=list[ApiContractResponse])
async def list_api_contracts(
    service_name: str | None = None,
    status_filter: str | None = None,
    spec_format: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ApiContract)
    if service_name:
        query = query.filter(ApiContract.service_name == service_name)
    if status_filter:
        query = query.filter(ApiContract.status == status_filter)
    if spec_format:
        query = query.filter(ApiContract.spec_format == spec_format)
    return query.order_by(ApiContract.created_at.desc()).all()


@router.get("/service/{service_name}", response_model=list[ApiContractResponse])
async def get_by_service(service_name: str, db: Session = Depends(get_db)):
    """Return all versions for a given service, newest first."""
    return (
        db.query(ApiContract)
        .filter(ApiContract.service_name == service_name)
        .order_by(ApiContract.version.desc())
        .all()
    )


@router.get("/{contract_id}", response_model=ApiContractResponse)
async def get_api_contract(contract_id: UUID, db: Session = Depends(get_db)):
    contract = db.query(ApiContract).filter(ApiContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API contract not found")
    return contract


@router.put("/{contract_id}", response_model=ApiContractResponse)
async def update_api_contract(
    contract_id: UUID, contract_update: ApiContractCreate, db: Session = Depends(get_db)
):
    contract = db.query(ApiContract).filter(ApiContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API contract not found")
    for key, value in contract_update.model_dump(exclude_unset=True).items():
        setattr(contract, key, value)
    db.commit()
    db.refresh(contract)
    return contract


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_contract(contract_id: UUID, db: Session = Depends(get_db)):
    contract = db.query(ApiContract).filter(ApiContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API contract not found")
    db.delete(contract)
    db.commit()
    return None
