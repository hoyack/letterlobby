# app/models/mailing_transaction.py

import uuid
from sqlalchemy import Column, ForeignKey, String, DateTime, Enum, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum as PyEnum
from app.core.database import Base

class MailingStatus(PyEnum):
    pending = "pending"
    sent = "sent"
    failed = "failed"

class MailingTransaction(Base):
    __tablename__ = "mailing_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_letter_request_id = Column(UUID(as_uuid=True), ForeignKey("user_letter_requests.id"), nullable=False)

    external_mail_service_id = Column(String, nullable=True)
    status = Column(Enum(MailingStatus), default=MailingStatus.pending)
    error_message = Column(String, nullable=True)
    mail_service_response = Column(JSON, nullable=True)  # Added JSON column

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
