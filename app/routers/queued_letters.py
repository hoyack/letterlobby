from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.core.database import get_db
from app.models.queued_letter import QueuedLetter, QueuedLetterStatus
from app.schemas.queued_letter import QueuedLetterCreate, QueuedLetterUpdate, QueuedLetterOut

router = APIRouter(prefix="/queued-letters", tags=["queued_letters"])

@router.post("/", response_model=QueuedLetterOut, status_code=status.HTTP_201_CREATED)
def create_queued_letter(payload: QueuedLetterCreate, db: Session = Depends(get_db)):
    # Ensure the user_letter_request exists and is valid if needed
    # For now, we assume it exists. You could add validation if required.

    queued_letter = QueuedLetter(**payload.dict())
    db.add(queued_letter)
    db.commit()
    db.refresh(queued_letter)
    return queued_letter

@router.get("/", response_model=List[QueuedLetterOut])
def list_queued_letters(db: Session = Depends(get_db)):
    return db.query(QueuedLetter).all()

@router.get("/{queued_letter_id}", response_model=QueuedLetterOut)
def get_queued_letter(queued_letter_id: UUID, db: Session = Depends(get_db)):
    queued_letter = db.query(QueuedLetter).filter(QueuedLetter.id == queued_letter_id).first()
    if not queued_letter:
        raise HTTPException(status_code=404, detail="Queued letter not found")
    return queued_letter

@router.patch("/{queued_letter_id}", response_model=QueuedLetterOut)
def update_queued_letter(queued_letter_id: UUID, updates: QueuedLetterUpdate, db: Session = Depends(get_db)):
    queued_letter = db.query(QueuedLetter).filter(QueuedLetter.id == queued_letter_id).first()
    if not queued_letter:
        raise HTTPException(status_code=404, detail="Queued letter not found")

    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(queued_letter, field, value)

    db.commit()
    db.refresh(queued_letter)
    return queued_letter

@router.delete("/{queued_letter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_queued_letter(queued_letter_id: UUID, db: Session = Depends(get_db)):
    queued_letter = db.query(QueuedLetter).filter(QueuedLetter.id == queued_letter_id).first()
    if not queued_letter:
        raise HTTPException(status_code=404, detail="Queued letter not found")

    db.delete(queued_letter)
    db.commit()
    return None

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_queue(db: Session = Depends(get_db)):
    # Delete all queued letters
    db.query(QueuedLetter).delete()
    db.commit()
    return None
