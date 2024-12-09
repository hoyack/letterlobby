# app/schemas/politician.py

from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class PoliticianBase(BaseModel):
    name: str
    title: str
    office_address_line1: str
    office_address_line2: Optional[str] = None
    office_city: str
    office_state: str
    office_zip: str
    legislative_body: str

class PoliticianCreate(PoliticianBase):
    pass

class PoliticianUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    office_address_line1: Optional[str] = None
    office_address_line2: Optional[str] = None
    office_city: Optional[str] = None
    office_state: Optional[str] = None
    office_zip: Optional[str] = None
    legislative_body: Optional[str] = None

class PoliticianOut(PoliticianBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
