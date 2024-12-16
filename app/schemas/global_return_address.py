# app/schemas/global_return_address.py
from pydantic import BaseModel
from typing import Optional

class GlobalReturnAddressBase(BaseModel):
    organization_name: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    zipcode: str

class GlobalReturnAddressCreate(GlobalReturnAddressBase):
    pass

class GlobalReturnAddressUpdate(BaseModel):
    organization_name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None

class GlobalReturnAddressOut(GlobalReturnAddressBase):
    class Config:
        from_attributes = True
