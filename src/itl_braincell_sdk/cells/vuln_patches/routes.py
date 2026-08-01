"""VulnPatch routes — CRUD for known-vulnerable / patched code pairs."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.vuln_patches.model import VulnPatch
from itl_braincell_sdk.cells.vuln_patches.schema import VulnPatchCreate, VulnPatchResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=VulnPatchResponse, status_code=status.HTTP_201_CREATED)
async def create_vuln_patch(entry: VulnPatchCreate, db: Session = Depends(get_db)):
    db_entry = VulnPatch(**schema_to_db_kwargs(entry))
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    try:
        get_weaviate_service().index_vuln_patch(
            str(db_entry.id),
            title=db_entry.title,
            description=db_entry.description or "",
            vulnerable_code=db_entry.vulnerable_code,
            patched_code=db_entry.patched_code,
            patch_explanation=db_entry.patch_explanation or "",
        )
    except Exception:
        logger.warning("Failed to index vuln_patch %s in Weaviate", db_entry.id)
    return db_entry


@router.get("", response_model=list[VulnPatchResponse])
async def list_vuln_patches(
    severity: str | None = None,
    language: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(VulnPatch)
    if severity:
        q = q.filter(VulnPatch.severity == severity)
    if language:
        q = q.filter(VulnPatch.language == language)
    if category:
        q = q.filter(VulnPatch.category == category)
    return q.order_by(VulnPatch.created_at.desc()).all()


@router.get("/by_cve/{cve_id}", response_model=list[VulnPatchResponse])
async def get_by_cve(cve_id: str, db: Session = Depends(get_db)):
    """Find all vuln/patch pairs that reference a specific CVE."""
    from sqlalchemy import cast
    from sqlalchemy.dialects.postgresql import JSONB
    results = (
        db.query(VulnPatch)
        .filter(cast(VulnPatch.cve_refs, JSONB).contains([cve_id]))
        .all()
    )
    return results


@router.get("/{entry_id}", response_model=VulnPatchResponse)
async def get_vuln_patch(entry_id: UUID, db: Session = Depends(get_db)):
    entry = db.query(VulnPatch).filter(VulnPatch.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VulnPatch not found")
    return entry


@router.put("/{entry_id}", response_model=VulnPatchResponse)
async def update_vuln_patch(
    entry_id: UUID, update: VulnPatchCreate, db: Session = Depends(get_db)
):
    entry = db.query(VulnPatch).filter(VulnPatch.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VulnPatch not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    try:
        get_weaviate_service().index_vuln_patch(
            str(entry.id),
            title=entry.title,
            description=entry.description or "",
            vulnerable_code=entry.vulnerable_code,
            patched_code=entry.patched_code,
            patch_explanation=entry.patch_explanation or "",
        )
    except Exception:
        pass
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vuln_patch(entry_id: UUID, db: Session = Depends(get_db)):
    entry = db.query(VulnPatch).filter(VulnPatch.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VulnPatch not found")
    db.delete(entry)
    db.commit()
