# app/services/otp_service.py

import uuid
import random
import string
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.otp_code import OTPCode
from app.models.user import User
from app.core.config import settings
import requests

def generate_otp_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

def create_otp_code(db: Session, user_id: uuid.UUID, purpose: str, expires_in_minutes=30):
    code = generate_otp_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
    otp = OTPCode(user_id=user_id, code=code, purpose=purpose, expires_at=expires_at)
    db.add(otp)
    db.commit()
    db.refresh(otp)
    return code

def verify_otp_code(db: Session, identifier: str, code: str, purpose: str, user_id: uuid.UUID = None):
    """
    identifier: For 'verify_email' or 'reset_password', this is the user's email.
                For 'change_email', this is the new_email, but we won't use it to find the user.
    user_id: For 'change_email' scenario, the user's ID.
    """
    if purpose == "change_email":
        if not user_id:
            return False
        # For change_email, find OTP by user_id, code, and purpose directly
        otp = db.query(OTPCode).filter(
            OTPCode.user_id == user_id,
            OTPCode.code == code,
            OTPCode.purpose == purpose
        ).first()
        if not otp or otp.expires_at < datetime.now(timezone.utc):
            return False
        db.delete(otp)
        db.commit()
        user = db.query(User).filter(User.id == user_id).first()
        return user
    else:
        # Old behavior: find user by email
        user = db.query(User).filter(User.email == identifier).first()
        if not user:
            return False
        otp = db.query(OTPCode).filter(
            OTPCode.user_id == user.id,
            OTPCode.code == code,
            OTPCode.purpose == purpose
        ).first()
        if not otp or otp.expires_at < datetime.now(timezone.utc):
            return False
        db.delete(otp)
        db.commit()
        return user

def send_email(to: str, subject: str, body: str):
    url = f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages"
    auth = ("api", settings.MAILGUN_API_KEY)
    data = {
        "from": "letterlobby@serviceorchard.com",
        "to": [to],
        "subject": subject,
        "text": body
    }
    response = requests.post(url, auth=auth, data=data)

    if response.status_code != 200:
        print("Failed to send email:", response.text)
    else:
        print(f"Email sent to {to}: {subject}")
