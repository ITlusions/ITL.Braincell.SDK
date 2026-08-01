"""Snippets routes"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.snippets.model import CodeSnippet
from itl_braincell_sdk.cells.snippets.schema import CodeSnippetCreate, CodeSnippetResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=CodeSnippetResponse, status_code=status.HTTP_201_CREATED)
async def create_code_snippet(snippet: CodeSnippetCreate, db: Session = Depends(get_db)):
    db_snippet = CodeSnippet(**schema_to_db_kwargs(snippet))
    db.add(db_snippet)
    db.commit()
    db.refresh(db_snippet)

    weaviate = get_weaviate_service()
    success = weaviate.index_code_snippet(
        str(db_snippet.id), db_snippet.title, db_snippet.code_content, db_snippet.language
    )
    if not success:
        logger.warning("Failed to sync code snippet %s to Weaviate", db_snippet.id)

    return db_snippet


@router.get("", response_model=list[CodeSnippetResponse])
async def get_code_snippets(language: str = None, db: Session = Depends(get_db)):
    query = db.query(CodeSnippet)
    if language:
        query = query.filter(CodeSnippet.language == language)
    return query.order_by(CodeSnippet.created_at.desc()).all()


@router.put("/{snippet_id}", response_model=CodeSnippetResponse)
async def update_code_snippet(
    snippet_id: UUID, snippet_update: CodeSnippetCreate, db: Session = Depends(get_db)
):
    snippet = db.query(CodeSnippet).filter(CodeSnippet.id == snippet_id).first()
    if not snippet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Code snippet not found")

    for key, value in snippet_update.model_dump(exclude_unset=True).items():
        setattr(snippet, key, value)
    db.commit()
    db.refresh(snippet)

    weaviate = get_weaviate_service()
    weaviate.index_code_snippet(str(snippet.id), snippet.title, snippet.code_content, snippet.language)
    return snippet


@router.delete("/{snippet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_code_snippet(snippet_id: UUID, db: Session = Depends(get_db)):
    snippet = db.query(CodeSnippet).filter(CodeSnippet.id == snippet_id).first()
    if not snippet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Code snippet not found")

    db.delete(snippet)
    db.commit()

    weaviate = get_weaviate_service()
    weaviate.delete_code_snippet(str(snippet_id))
    return None
