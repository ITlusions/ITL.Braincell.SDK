"""Dependencies routes."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.dependencies.model import Dependency
from itl_braincell_sdk.cells.dependencies.schema import DependencyCreate, DependencyResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=DependencyResponse, status_code=status.HTTP_201_CREATED)
async def create_dependency(dep: DependencyCreate, db: Session = Depends(get_db)):
    db_dep = Dependency(**schema_to_db_kwargs(dep))
    db.add(db_dep)
    db.commit()
    db.refresh(db_dep)
    return db_dep


@router.get("", response_model=list[DependencyResponse])
async def list_dependencies(
    ecosystem: str | None = None,
    status_filter: str | None = None,
    project: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Dependency)
    if ecosystem:
        query = query.filter(Dependency.ecosystem == ecosystem)
    if status_filter:
        query = query.filter(Dependency.status == status_filter)
    if project:
        query = query.filter(Dependency.project == project)
    return query.order_by(Dependency.name, Dependency.version.desc()).all()


@router.get("/vulnerable", response_model=list[DependencyResponse])
async def get_vulnerable_dependencies(project: str | None = None, db: Session = Depends(get_db)):
    """Return all dependencies with status 'vulnerable'."""
    query = db.query(Dependency).filter(Dependency.status == "vulnerable")
    if project:
        query = query.filter(Dependency.project == project)
    return query.order_by(Dependency.name).all()


@router.get("/by_cve/{cve_id}", response_model=list[DependencyResponse])
async def get_by_cve(cve_id: str, db: Session = Depends(get_db)):
    """Return all dependencies linked to a specific CVE."""
    return (
        db.query(Dependency)
        .filter(Dependency.cve_refs.contains([cve_id]))
        .all()
    )


@router.get("/{dep_id}", response_model=DependencyResponse)
async def get_dependency(dep_id: UUID, db: Session = Depends(get_db)):
    dep = db.query(Dependency).filter(Dependency.id == dep_id).first()
    if not dep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dependency not found")
    return dep


@router.put("/{dep_id}", response_model=DependencyResponse)
async def update_dependency(dep_id: UUID, dep_update: DependencyCreate, db: Session = Depends(get_db)):
    dep = db.query(Dependency).filter(Dependency.id == dep_id).first()
    if not dep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dependency not found")
    for key, value in dep_update.model_dump(exclude_unset=True).items():
        setattr(dep, key, value)
    db.commit()
    db.refresh(dep)
    return dep


@router.delete("/{dep_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dependency(dep_id: UUID, db: Session = Depends(get_db)):
    dep = db.query(Dependency).filter(Dependency.id == dep_id).first()
    if not dep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dependency not found")
    db.delete(dep)
    db.commit()
    return None
