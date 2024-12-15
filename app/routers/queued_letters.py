from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
import json

from app.core.database import get_db
from app.models.queued_letter import QueuedLetter
from app.models.user_letter_request import UserLetterRequest
from app.models.user import User
from app.schemas.queued_letter import QueuedLetterCreate, QueuedLetterUpdate, QueuedLetterOut
from app.services.mailing_service import format_letter_text
from app.services.printing_service import html_to_pdf, print_pdf
from app.dependencies import require_verified_user

router = APIRouter(prefix="/queued-letters", tags=["queued_letters"])

def is_admin(current_user: User) -> bool:
    return current_user.role == "administrator"

def get_queued_letter_or_404(db: Session, queued_letter_id: UUID, current_user: User) -> QueuedLetter:
    queued_letter = db.query(QueuedLetter).filter(QueuedLetter.id == queued_letter_id).first()
    if not queued_letter:
        raise HTTPException(status_code=404, detail="Queued letter not found")

    user_letter_req = queued_letter.user_letter_request
    if not user_letter_req:
        # Data inconsistency if this happens
        raise HTTPException(status_code=500, detail="Queued letter missing associated user_letter_request")

    if not is_admin(current_user) and user_letter_req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this queued letter")

    return queued_letter

@router.post("/", response_model=QueuedLetterOut, status_code=status.HTTP_201_CREATED)
def create_queued_letter(
    payload: QueuedLetterCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_verified_user)
):
    # Validate that the user_letter_request exists and belongs to current_user (or current_user is admin)
    user_letter_req = db.query(UserLetterRequest).filter(UserLetterRequest.id == payload.user_letter_request_id).first()
    if not user_letter_req:
        raise HTTPException(status_code=400, detail="Invalid user_letter_request_id")

    if not is_admin(current_user) and user_letter_req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    queued_letter = QueuedLetter(**payload.dict())
    db.add(queued_letter)
    db.commit()
    db.refresh(queued_letter)
    return queued_letter

@router.get("/", response_model=List[QueuedLetterOut])
def list_queued_letters(
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_verified_user)
):
    if is_admin(current_user):
        return db.query(QueuedLetter).all()
    else:
        # Filter by user's own queued letters via a join
        return (db.query(QueuedLetter)
                  .join(UserLetterRequest, QueuedLetter.user_letter_request_id == UserLetterRequest.id)
                  .filter(UserLetterRequest.user_id == current_user.id)
                  .all())

@router.get("/{queued_letter_id}", response_model=QueuedLetterOut)
def get_queued_letter(
    queued_letter_id: UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    queued_letter = get_queued_letter_or_404(db, queued_letter_id, current_user)
    return queued_letter

@router.patch("/{queued_letter_id}", response_model=QueuedLetterOut)
def update_queued_letter(
    queued_letter_id: UUID,
    updates: QueuedLetterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    queued_letter = get_queued_letter_or_404(db, queued_letter_id, current_user)

    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(queued_letter, field, value)

    db.commit()
    db.refresh(queued_letter)
    return queued_letter

@router.delete("/{queued_letter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_queued_letter(
    queued_letter_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    queued_letter = get_queued_letter_or_404(db, queued_letter_id, current_user)
    db.delete(queued_letter)
    db.commit()
    return None

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_queue(
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_verified_user)
):
    if is_admin(current_user):
        # Admin clears entire queue
        db.query(QueuedLetter).delete(synchronize_session=False)
        db.commit()
        return None
    else:
        # Normal user: delete only user's own queued letters via subquery
        subq = db.query(UserLetterRequest.id).filter(UserLetterRequest.user_id == current_user.id).subquery()
        db.query(QueuedLetter).filter(QueuedLetter.user_letter_request_id.in_(subq)).delete(synchronize_session=False)
        db.commit()
        return None

@router.get("/{queued_letter_id}/pdf", response_class=Response)
def get_queued_letter_pdf(
    queued_letter_id: UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    queued_letter = get_queued_letter_or_404(db, queued_letter_id, current_user)

    # Extract letter text
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
def print_queued_letter(
    queued_letter_id: UUID, 
    printer_name: str = Query(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    queued_letter = get_queued_letter_or_404(db, queued_letter_id, current_user)

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
