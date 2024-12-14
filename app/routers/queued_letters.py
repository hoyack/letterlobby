# app/routers/queued_letters.py
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.core.database import get_db
from app.models.queued_letter import QueuedLetter
from app.schemas.queued_letter import QueuedLetterCreate, QueuedLetterUpdate, QueuedLetterOut
from app.services.mailing_service import format_letter_text
from app.services.printing_service import html_to_pdf, print_pdf
import json

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

@router.get("/{queued_letter_id}/pdf", response_class=Response)
def get_queued_letter_pdf(queued_letter_id: UUID, db: Session = Depends(get_db)):
    queued_letter = db.query(QueuedLetter).filter(QueuedLetter.id == queued_letter_id).first()
    if not queued_letter:
        raise HTTPException(status_code=404, detail="Queued letter not found")

    # Extract letter text as before
    try:
        letter_data = json.loads(queued_letter.final_letter_text)
        letter_text = letter_data.get("letter", "")
    except (json.JSONDecodeError, TypeError):
        letter_text = queued_letter.final_letter_text or ""

    user_letter_req = queued_letter.user_letter_request
    politician = user_letter_req.politician
    recipient_address = {
        "line1": politician.office_address_line1,
        "line2": politician.office_address_line2 or "",
        "city": politician.office_city,
        "state": politician.office_state,
        "zip": politician.office_zip
    }

    sender_name = "Your Organization"
    sender_address = {
        "line1": "500 Example St",
        "city": "YourCity",
        "state": "TX",
        "zip": "78702"
    }

    html = format_letter_text(letter_text, politician.name, recipient_address, sender_name, sender_address)
    pdf = html_to_pdf(html)
    return Response(content=pdf, media_type="application/pdf")

@router.post("/{queued_letter_id}/print")
def print_queued_letter(queued_letter_id: UUID, printer_name: str = Query(...), db: Session = Depends(get_db)):
    queued_letter = db.query(QueuedLetter).filter(QueuedLetter.id == queued_letter_id).first()
    if not queued_letter:
        raise HTTPException(status_code=404, detail="Queued letter not found")

    try:
        letter_data = json.loads(queued_letter.final_letter_text)
        letter_text = letter_data.get("letter", "")
    except (json.JSONDecodeError, TypeError):
        letter_text = queued_letter.final_letter_text or ""

    user_letter_req = queued_letter.user_letter_request
    politician = user_letter_req.politician
    recipient_address = {
        "line1": politician.office_address_line1,
        "line2": politician.office_address_line2 or "",
        "city": politician.office_city,
        "state": politician.office_state,
        "zip": politician.office_zip
    }

    sender_name = "Your Organization"
    sender_address = {
        "line1": "500 Example St",
        "city": "YourCity",
        "state": "TX",
        "zip": "78702"
    }

    html = format_letter_text(letter_text, politician.name, recipient_address, sender_name, sender_address)
    pdf = html_to_pdf(html)

    try:
        job_id = print_pdf(pdf, printer_name)
        return {"message": "Printing initiated", "job_id": job_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
