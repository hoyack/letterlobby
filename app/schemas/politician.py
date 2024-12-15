# app/schemas/politician.py

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class PoliticianBillAssociationOut(BaseModel):
    bill_id: UUID
    does_support: Optional[bool]

class PoliticianBase(BaseModel):
    name: str
    title: str
    office_address_line1: str
    office_address_line2: Optional[str] = None
    office_city: str
    office_state: str
    office_zip: str
    legislative_body: str
    email: Optional[EmailStr] = None

class PoliticianCreate(PoliticianBase):
    # On create, allow specifying associated bills with does_support
    bills: Optional[List[PoliticianBillAssociationOut]] = []

class PoliticianUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    office_address_line1: Optional[str] = None
    office_address_line2: Optional[str] = None
    office_city: Optional[str] = None
    office_state: Optional[str] = None
    office_zip: Optional[str] = None
    legislative_body: Optional[str] = None
    email: Optional[EmailStr] = None
    bills: Optional[List[PoliticianBillAssociationOut]] = None

class PoliticianOut(PoliticianBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    bills: List[PoliticianBillAssociationOut]

    class Config:
        from_attributes = True
