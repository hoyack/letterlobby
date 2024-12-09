from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import stripe
from app.core.config import settings
from app.core.database import get_db
from app.models.user_letter_request import UserLetterRequest, LetterStatus
from uuid import UUID
from datetime import datetime

router = APIRouter()

@router.post("/stripe-webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET  # Make sure this is in your .env and config

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig, secret=endpoint_secret
        )
    except ValueError:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        letter_request_id = session["metadata"].get("letter_request_id")
        if letter_request_id:
            letter_req = db.query(UserLetterRequest).filter(UserLetterRequest.id == UUID(letter_request_id)).first()
            if letter_req:
                letter_req.status = LetterStatus.paid
                letter_req.paid_at = datetime.utcnow()
                db.commit()

    return {"status": "success"}
