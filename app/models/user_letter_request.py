# app/models/user_letter_request.py

import uuid
from sqlalchemy import Column, ForeignKey, String, Text, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.core.database import Base

class LetterStatus(PyEnum):
    drafting = "drafting"
    finalized = "finalized"
    paid = "paid"
    mailed = "mailed"

class UserLetterRequest(Base):
    __tablename__ = "user_letter_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("bills.id"), nullable=False)
    politician_id = Column(UUID(as_uuid=True), ForeignKey("politicians.id"), nullable=False)

    user_provided_name = Column(String, nullable=True)
    user_provided_address_line1 = Column(String, nullable=True)
    user_provided_address_line2 = Column(String, nullable=True)
    user_provided_city = Column(String, nullable=True)
    user_provided_state = Column(String, nullable=True)
    user_provided_zip = Column(String, nullable=True)

    user_comments = Column(Text, nullable=True)
    final_letter_text = Column(Text, nullable=True)
    status = Column(Enum(LetterStatus), default=LetterStatus.drafting)

    stripe_charge_id = Column(String, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="letter_requests")
    bill = relationship("Bill", backref="letter_requests")
    politician = relationship("Politician", backref="letter_requests")