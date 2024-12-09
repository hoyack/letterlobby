from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
import json, requests

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

router = APIRouter(prefix="/letter-requests", tags=["letter_requests"])

@router.post("/", response_model=UserLetterRequestOut, status_code=status.HTTP_201_CREATED)
def create_letter_request(letter_data: UserLetterRequestCreate, db: Session = Depends(get_db)):
    # Validate that the Bill and Politician exist
    bill = db.query(Bill).filter(Bill.id == letter_data.bill_id).first()
    if not bill:
        raise HTTPException(status_code=400, detail="Invalid bill_id")
    
    politician = db.query(Politician).filter(Politician.id == letter_data.politician_id).first()
    if not politician:
        raise HTTPException(status_code=400, detail="Invalid politician_id")

    # Create the request in drafting status
    letter_req = UserLetterRequest(
        **letter_data.dict(),
        status=LetterStatus.drafting
    )
    db.add(letter_req)
    db.commit()
    db.refresh(letter_req)
    return letter_req

@router.get("/", response_model=list[UserLetterRequestOut])
def list_letter_requests(db: Session = Depends(get_db)):
    return db.query(UserLetterRequest).all()

@router.get("/{letter_id}", response_model=UserLetterRequestOut)
def get_letter_request(letter_id: UUID, db: Session = Depends(get_db)):
    letter_req = db.query(UserLetterRequest).filter(UserLetterRequest.id == letter_id).first()
    if not letter_req:
        raise HTTPException(status_code=404, detail="Letter request not found")
    return letter_req

@router.patch("/{letter_id}", response_model=UserLetterRequestOut)
def update_letter_request(letter_id: UUID, updates: UserLetterRequestUpdate, db: Session = Depends(get_db)):
    letter_req = db.query(UserLetterRequest).filter(UserLetterRequest.id == letter_id).first()
    if not letter_req:
        raise HTTPException(status_code=404, detail="Letter request not found")

    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(letter_req, field, value)

    db.commit()
    db.refresh(letter_req)
    return letter_req

@router.post("/{letter_id}/draft", response_model=UserLetterRequestOut)
def generate_letter_draft(letter_id: UUID, draft_data: LetterDraftRequest, db: Session = Depends(get_db)):
    """
    This endpoint accepts a JSON payload like:
    {
        "bill_name": "string",
        "lawmaker_name": "string",
        "stance": "support" or "oppose",
        "support_level": integer 1-10,
        "personal_feedback": "optional string"
    }
    Generates a drafted letter using LLM.
    """
    letter_req = db.query(UserLetterRequest).filter(UserLetterRequest.id == letter_id).first()
    if not letter_req:
        raise HTTPException(status_code=404, detail="Letter request not found")

    if not letter_req.user_comments:
        raise HTTPException(status_code=400, detail="No user_comments provided for drafting.")

    prompt = f"""
    Write a respectful and clear letter to {draft_data.lawmaker_name} regarding the bill "{draft_data.bill_name}".
    The writer's stance towards this bill is: {draft_data.stance}. 
    On a scale from 1 to 10, their support level is: {draft_data.support_level}.

    Background comments from the requester:
    {letter_req.user_comments}
    """

    if draft_data.personal_feedback:
        prompt += f"\nAdditional personal feedback from the requester:\n{draft_data.personal_feedback}\n"

    prompt += """
    The letter should be concise, persuasive, and well-structured. Sign off at the end.
    Please respond with a JSON object containing a field "letter" that holds the final letter text.
    """

    drafted_text = draft_letter(prompt)
    letter_req.final_letter_text = drafted_text
    letter_req.status = LetterStatus.finalized
    db.commit()
    db.refresh(letter_req)
    return letter_req

@router.post("/{letter_id}/pay")
def pay_for_letter(letter_id: UUID, db: Session = Depends(get_db)):
    letter_req = db.query(UserLetterRequest).filter(UserLetterRequest.id == letter_id).first()
    if not letter_req:
        raise HTTPException(status_code=404, detail="Letter request not found")

    # Ensure letter is finalized before payment
    if letter_req.status != LetterStatus.finalized:
        raise HTTPException(status_code=400, detail="Letter must be finalized before paying.")

    amount = 500  # e.g. $5.00
    success_url = f"http://localhost:8000/payment-success?letter_id={letter_id}"
    cancel_url = f"http://localhost:8000/payment-cancel?letter_id={letter_id}"

    session = create_checkout_session(str(letter_id), amount, success_url, cancel_url)
    return {"checkout_url": session.url}

@router.post("/{letter_id}/mail")
def mail_letter(letter_id: UUID, db: Session = Depends(get_db)):
    letter_req = db.query(UserLetterRequest).filter(UserLetterRequest.id == letter_id).first()
    if not letter_req:
        raise HTTPException(status_code=404, detail="Letter request not found")

    if letter_req.status != LetterStatus.paid:
        raise HTTPException(status_code=400, detail="Letter must be paid before mailing.")

    if not letter_req.final_letter_text:
        raise HTTPException(status_code=400, detail="No final letter text available.")

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

    # Format the letter into HTML before sending
    formatted_html = format_letter_text(
        raw_letter_text,
        recipient_name=politician.name,
        recipient_address=recipient_address,
        sender_name="Your Organization",
        sender_address={"line1": "500 Example St", "city": "YourCity", "state": "TX", "zip": "78702"}
    )

    try:
        mail_response = send_letter(
            formatted_html=formatted_html,
            recipient_name=politician.name,
            recipient_address=recipient_address
        )
    except requests.HTTPError as e:
        mailing_tx = MailingTransaction(
            user_letter_request_id=letter_req.id,
            external_mail_service_id=None,
            status=MailingStatus.failed,
            error_message=str(e)
        )
        db.add(mailing_tx)
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to send letter")

    mailing_tx = MailingTransaction(
        user_letter_request_id=letter_req.id,
        external_mail_service_id=mail_response.get("id"),
        status=MailingStatus.sent
    )
    db.add(mailing_tx)
    letter_req.status = LetterStatus.mailed
    db.commit()
    db.refresh(letter_req)

    return {"message": "Letter mailed successfully", "mailing_transaction_id": str(mailing_tx.id), "mail_service_response": mail_response}
