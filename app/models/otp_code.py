import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class OTPCode(Base):
    __tablename__ = "otp_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    code = Column(String, nullable=False)
    purpose = Column(String, nullable=False)  # e.g. "verify_email", "reset_password"
    expires_at = Column(DateTime(timezone=True), server_default=func.now())
