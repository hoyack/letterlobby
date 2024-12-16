# app/main.py

from fastapi import FastAPI
from app.core.database import Base, engine
from app.models.user import User
from app.models.bill import Bill
from app.models.politician import Politician
from app.models.user_letter_request import UserLetterRequest
from app.models.mailing_transaction import MailingTransaction
from app.models.queued_letter import QueuedLetter  # new model import
from app.routers import bills, global_return_address, politicians, user_letter_requests, webhooks, queued_letters
from uuid import UUID
from app.models.user import User
from app.models.otp_code import OTPCode
from app.routers import users
from app.models.global_return_address import GlobalReturnAddress


# Import the bills router
from app.routers import bills, politicians, user_letter_requests, webhooks

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LetterLobby")

# Include the bills router
app.include_router(bills.router)
app.include_router(politicians.router)
app.include_router(user_letter_requests.router)
app.include_router(webhooks.router)
app.include_router(queued_letters.router)
app.include_router(users.router)
app.include_router(global_return_address.router)


@app.get("/")
def read_root():
    return {"message": "Hello from LetterLobby!"}

from uuid import UUID

@app.get("/payment-success")
def payment_success(letter_id: UUID):
    return {"message": f"Payment succeeded for letter_id: {letter_id}"}

@app.get("/payment-cancel")
def payment_cancel(letter_id: UUID):
    return {"message": f"Payment was canceled for letter_id: {letter_id}"}
