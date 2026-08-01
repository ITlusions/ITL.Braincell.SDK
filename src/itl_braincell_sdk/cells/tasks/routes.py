"""Tasks routes."""
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.tasks.model import Task
from itl_braincell_sdk.cells.tasks.schema import TaskCreate, TaskResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(**schema_to_db_kwargs(task))
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    status_filter: str | None = None,
    priority: str | None = None,
    project: str | None = None,
    assignee: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Task)
    if status_filter:
        query = query.filter(Task.status == status_filter)
    if priority:
        query = query.filter(Task.priority == priority)
    if project:
        query = query.filter(Task.project == project)
    if assignee:
        query = query.filter(Task.assignee == assignee)
    return query.order_by(Task.created_at.desc()).all()


@router.get("/open", response_model=list[TaskResponse])
async def get_open_tasks(project: str | None = None, db: Session = Depends(get_db)):
    """Return all tasks that are open or in_progress, optionally filtered by project."""
    query = db.query(Task).filter(Task.status.in_(["open", "in_progress", "blocked"]))
    if project:
        query = query.filter(Task.project == project)
    return query.order_by(Task.priority.desc(), Task.created_at.asc()).all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: UUID, task_update: TaskCreate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    for key, value in task_update.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    if task_update.status == "done" and not task.completed_at:
        task.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.delete(task)
    db.commit()
    return None
