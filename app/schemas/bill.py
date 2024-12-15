# app/schemas/bill.py

from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class BillPoliticianAssociationOut(BaseModel):
    politician_id: UUID
    does_support: Optional[bool]

class BillBase(BaseModel):
    title: str
    description: Optional[str] = None
    bill_number: str
    legislative_body: str
    status: Optional[str] = None

class BillCreate(BillBase):
    # On creation, allow specifying politicians and does_support
    politicians: Optional[List[BillPoliticianAssociationOut]] = []

class BillUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    bill_number: Optional[str] = None
    legislative_body: Optional[str] = None
    status: Optional[str] = None
    politicians: Optional[List[BillPoliticianAssociationOut]] = None

class BillOut(BillBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    politicians: List[BillPoliticianAssociationOut]

    class Config:
        from_attributes = True
