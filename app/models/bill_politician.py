# app/models/bill_politician.py

import uuid
from sqlalchemy import Column, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class BillPolitician(Base):
    __tablename__ = "bill_politicians"

    bill_id = Column(UUID(as_uuid=True), ForeignKey("bills.id", ondelete="CASCADE"), primary_key=True)
    politician_id = Column(UUID(as_uuid=True), ForeignKey("politicians.id", ondelete="CASCADE"), primary_key=True)
    does_support = Column(Boolean, nullable=True)

    bill = relationship("Bill", back_populates="bill_politicians_assocs")
    politician = relationship("Politician", back_populates="bill_politicians_assocs")
