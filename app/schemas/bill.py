# app/schemas/bill.py

from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class BillBase(BaseModel):
    title: str
    description: Optional[str] = None
    bill_number: str
    legislative_body: str
    status: Optional[str] = None

class BillCreate(BillBase):
    pass  # same fields as BillBase for creation

class BillUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    bill_number: Optional[str] = None
    legislative_body: Optional[str] = None
    status: Optional[str] = None

class BillOut(BillBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
