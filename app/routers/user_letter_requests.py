from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from uuid import UUID
import json
import requests

from app.core.database import get_db
from app.models.user_letter_request import UserLetterRequest, LetterStatus
from app.models.bill import Bill
from app.models.politician import Politician
from app.schemas.letter_request import UserLetterRequestCreate, UserLetterRequestOut, UserLetterRequestUpdate
from app.schemas.letter_draft_request import LetterDraftRequest
from app.services.letter_drafting import draft_letter
from app.services.payment_service import create_checkout_session
from app.models.mailing_transaction import MailingTransaction, MailingStatus
from app.services.mailing_service import format_letter_text, send_letter
from app.dependencies import require_verified_user
from app.models.user import User
from app.models.global_return_address import GlobalReturnAddress
from app.services.printing_service import html_to_pdf

router = APIRouter(prefix="/letter-requests", tags=["letter_requests"])

def is_admin(current_user: User) -> bool:
    return current_user.role == "administrator"

def get_letter_request_or_404(db: Session, letter_id: UUID, current_user: User) -> UserLetterRequest:
    letter_req = db.query(UserLetterRequest).filter(UserLetterRequest.id == letter_id).first()
    if not letter_req:
        raise HTTPException(status_code=404, detail="Letter request not found")

    # Check ownership unless admin
    if not is_admin(current_user) and letter_req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this letter request")

    return letter_req

@router.post("/", response_model=UserLetterRequestOut, status_code=status.HTTP_201_CREATED)
def create_letter_request(
    letter_data: UserLetterRequestCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_verified_user)
):
    # Validate that the Bill and Politician exist
    bill = db.query(Bill).filter(Bill.id == letter_data.bill_id).first()
    if not bill:
        raise HTTPException(status_code=400, detail="Invalid bill_id")
    
    politician = db.query(Politician).filter(Politician.id == letter_data.politician_id).first()
    if not politician:
        raise HTTPException(status_code=400, detail="Invalid politician_id")

    # Create the request in drafting status tied to current_user
    letter_req = UserLetterRequest(
        bill_id=letter_data.bill_id,
        politician_id=letter_data.politician_id,
        use_profile_return_address=letter_data.use_profile_return_address,
        user_id=current_user.id,
        status=LetterStatus.drafting
    )
    db.add(letter_req)
    db.commit()
    db.refresh(letter_req)
    return letter_req

@router.get("/", response_model=list[UserLetterRequestOut])
def list_letter_requests(db: Session = Depends(get_db), current_user: User = Depends(require_verified_user)):
    if is_admin(current_user):
        return db.query(UserLetterRequest).all()
    else:
        return db.query(UserLetterRequest).filter(UserLetterRequest.user_id == current_user.id).all()

@router.get("/{letter_id}", response_model=UserLetterRequestOut)
def get_letter_request(letter_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_verified_user)):
    letter_req = get_letter_request_or_404(db, letter_id, current_user)
    return letter_req

@router.patch("/{letter_id}", response_model=UserLetterRequestOut)
def update_letter_request(letter_id: UUID, updates: UserLetterRequestUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_verified_user)):
    letter_req = get_letter_request_or_404(db, letter_id, current_user)

    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(letter_req, field, value)

    db.commit()
    db.refresh(letter_req)
    return letter_req

@router.delete("/{letter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_letter_request(letter_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_verified_user)):
    letter_req = get_letter_request_or_404(db, letter_id, current_user)

    # Allow deletion only if not mailed yet
    if letter_req.status == LetterStatus.mailed:
        raise HTTPException(status_code=400, detail="Cannot delete a mailed letter request.")

    db.delete(letter_req)
    db.commit()
    return None

@router.post("/{letter_id}/draft", response_model=UserLetterRequestOut)
def generate_letter_draft(
    letter_id: UUID, 
    draft_data: LetterDraftRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_verified_user)
):
    letter_req = get_letter_request_or_404(db, letter_id, current_user)

    if not draft_data.personal_feedback:
        raise HTTPException(status_code=400, detail="personal_feedback is required to draft the letter.")

    # Use the personal_feedback as user_comments to draft the letter
    drafted_text = draft_letter(draft_data.personal_feedback)
    letter_req.final_letter_text = drafted_text
    letter_req.status = LetterStatus.finalized
    db.commit()
    db.refresh(letter_req)
    return letter_req

@router.post("/{letter_id}/pay")
def pay_for_letter(letter_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_verified_user)):
    letter_req = get_letter_request_or_404(db, letter_id, current_user)

    # Ensure letter is finalized before payment
    if letter_req.status != LetterStatus.finalized:
        raise HTTPException(status_code=400, detail="Letter must be finalized before paying.")

    amount = 500  # e.g. $5.00
    success_url = f"http://localhost:8000/payment-success?letter_id={letter_id}"
    cancel_url = f"http://localhost:8000/payment-cancel?letter_id={letter_id}"

    session = create_checkout_session(str(letter_id), amount, success_url, cancel_url)
    return {"checkout_url": session.url}

@router.post("/{letter_id}/mail")
def mail_letter(letter_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_verified_user)):
    letter_req = get_letter_request_or_404(db, letter_id, current_user)

    if letter_req.status != LetterStatus.paid:
        raise HTTPException(status_code=400, detail="Letter must be paid before mailing.")

    if not letter_req.final_letter_text:
        raise HTTPException(status_code=400, detail="No final letter text available.")

    global_addr = db.query(GlobalReturnAddress).first()
    if not global_addr:
        raise HTTPException(status_code=500, detail="No global return address set.")

    try:
        letter_data = json.loads(letter_req.final_letter_text)
        raw_letter_text = letter_data.get("letter")
        if not raw_letter_text:
            raise HTTPException(status_code=400, detail="No 'letter' field found in final_letter_text.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in final_letter_text.")

    politician = letter_req.politician
    recipient_address = {
        "line1": politician.office_address_line1,
        "line2": politician.office_address_line2 or "",
        "city": politician.office_city,
        "state": politician.office_state,
        "zip": politician.office_zip
    }

    sender_name = global_addr.organization_name
    sender_address = {
        "line1": global_addr.address_line1,
        "line2": global_addr.address_line2 or "",
        "city": global_addr.city,
        "state": global_addr.state,
        "zip": global_addr.zipcode
    }

    formatted_html = format_letter_text(
        raw_letter_text,
        recipient_name=politician.name,
        recipient_address=recipient_address,
        sender_name=sender_name,
        sender_address=sender_address
    )

    try:
        mail_response = send_letter(
            formatted_html=formatted_html,
            recipient_name=politician.name,
            recipient_address=recipient_address,
            sender_name=sender_name,
            sender_address=sender_address
        )
    except requests.HTTPError as e:
        mailing_tx = MailingTransaction(
            user_letter_request_id=letter_req.id,
            external_mail_service_id=None,
            status=MailingStatus.failed,
            error_message=str(e),
            mail_service_response=None
        )
        db.add(mailing_tx)
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to send letter")

    mailing_tx = MailingTransaction(
        user_letter_request_id=letter_req.id,
        external_mail_service_id=mail_response.get("id"),
        status=MailingStatus.sent,
        mail_service_response=mail_response
    )
    db.add(mailing_tx)
    letter_req.status = LetterStatus.mailed
    db.commit()
    db.refresh(letter_req)

    return {"message": "Letter mailed successfully", "mailing_transaction_id": str(mailing_tx.id), "mail_service_response": mail_response}

@router.get("/{letter_id}/pdf", response_class=Response)
def get_letter_pdf(letter_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_verified_user)):
    letter_req = get_letter_request_or_404(db, letter_id, current_user)

    if not letter_req.final_letter_text:
        raise HTTPException(status_code=400, detail="No final letter text available.")

    global_addr = db.query(GlobalReturnAddress).first()
    if not global_addr:
        raise HTTPException(status_code=500, detail="No global return address set.")

    try:
        letter_data = json.loads(letter_req.final_letter_text)
        raw_letter_text = letter_data.get("letter")
        if not raw_letter_text or not isinstance(raw_letter_text, str):
            raise HTTPException(status_code=400, detail="No 'letter' field found in final_letter_text.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in final_letter_text.")

    politician = letter_req.politician
    recipient_address = {
        "line1": politician.office_address_line1,
        "line2": politician.office_address_line2 or "",
        "city": politician.office_city,
        "state": politician.office_state,
        "zip": politician.office_zip
    }

    sender_name = global_addr.organization_name
    sender_address = {
        "line1": global_addr.address_line1,
        "line2": global_addr.address_line2 or "",
        "city": global_addr.city,
        "state": global_addr.state,
        "zip": global_addr.zipcode
    }

    formatted_html = format_letter_text(
        raw_letter_text,
        recipient_name=politician.name,
        recipient_address=recipient_address,
        sender_name=sender_name,
        sender_address=sender_address
    )

    pdf = html_to_pdf(formatted_html)
    return Response(content=pdf, media_type="application/pdf")
