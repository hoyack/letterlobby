# app/models/politician.py

import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class Politician(Base):
    __tablename__ = "politicians"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    office_address_line1 = Column(String, nullable=False)
    office_address_line2 = Column(String, nullable=True)
    office_city = Column(String, nullable=False)
    office_state = Column(String, nullable=False)
    office_zip = Column(String, nullable=False)
    legislative_body = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
