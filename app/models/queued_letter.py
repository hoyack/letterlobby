# app/models/queued_letter.py

import uuid
from sqlalchemy import Column, ForeignKey, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.core.database import Base

class QueuedLetterStatus(PyEnum):
    queued = "queued"
    processed = "processed"  # optional future states if needed

class QueuedLetter(Base):
    __tablename__ = "queued_letters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_letter_request_id = Column(UUID(as_uuid=True), ForeignKey("user_letter_requests.id"), nullable=False)
    status = Column(Enum(QueuedLetterStatus), default=QueuedLetterStatus.queued)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_letter_request = relationship("UserLetterRequest", backref="queued_letters")
