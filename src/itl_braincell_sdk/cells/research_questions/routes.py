"""Research Questions cell — FastAPI routes."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs
from itl_braincell_sdk.cells.research_questions.model import ResearchQuestion
from itl_braincell_sdk.cells.research_questions.schema import (
    ResearchQuestionCreate,
    ResearchQuestionUpdate,
    ResearchQuestionResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ResearchQuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(question: ResearchQuestionCreate, db: Session = Depends(get_db)):
    """Create a new research question."""
    db_q = ResearchQuestion(**schema_to_db_kwargs(question))
    db.add(db_q)
    db.commit()
    db.refresh(db_q)
    return db_q


@router.get("", response_model=list[ResearchQuestionResponse])
async def list_questions(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
):
    """List all research questions, optionally filtered by status."""
    q = db.query(ResearchQuestion).order_by(ResearchQuestion.created_at.desc())
    if status_filter:
        q = q.filter(ResearchQuestion.status == status_filter)
    return q.all()


@router.get("/{question_id}", response_model=ResearchQuestionResponse)
async def get_question(question_id: UUID, db: Session = Depends(get_db)):
    """Get a single research question by ID."""
    row = db.query(ResearchQuestion).filter(ResearchQuestion.id == question_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return row


@router.put("/{question_id}", response_model=ResearchQuestionResponse)
async def update_question(
    question_id: UUID,
    updates: ResearchQuestionUpdate,
    db: Session = Depends(get_db),
):
    """Update a research question — use to set status, answer, or priority."""
    row = db.query(ResearchQuestion).filter(ResearchQuestion.id == question_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: UUID, db: Session = Depends(get_db)):
    """Delete a research question."""
    row = db.query(ResearchQuestion).filter(ResearchQuestion.id == question_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    db.delete(row)
    db.commit()
