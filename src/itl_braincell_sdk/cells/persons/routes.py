"""Persons routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.persons.model import Person
from itl_braincell_sdk.cells.persons.schema import PersonCreate, PersonResponse
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.core.schemas import schema_to_db_kwargs

router = APIRouter()


@router.post("", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(person: PersonCreate, db: Session = Depends(get_db)):
    db_person = Person(**schema_to_db_kwargs(person))
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person


@router.get("", response_model=list[PersonResponse])
async def list_persons(
    team: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Person)
    if team:
        query = query.filter(Person.team == team)
    return query.order_by(Person.name).limit(limit).all()


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(person_id: UUID, db: Session = Depends(get_db)):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return person


@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(person_id: UUID, person_update: PersonCreate, db: Session = Depends(get_db)):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    for key, value in person_update.model_dump(exclude_unset=True).items():
        setattr(person, key, value)
    db.commit()
    db.refresh(person)
    return person


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(person_id: UUID, db: Session = Depends(get_db)):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    db.delete(person)
    db.commit()
    return None
