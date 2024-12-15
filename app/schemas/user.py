# app/schemas/user.py

from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List, Dict

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ChangeEmailRequest(BaseModel):
    new_email: EmailStr
    password: str

class ChangeEmailVerifyRequest(BaseModel):
    new_email: EmailStr
    code: str

class UserProfile(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None

    profile_photo: Optional[str] = None
    thumbnail_photo: Optional[str] = None
    personal_description: Optional[str] = None
    political_party: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    race: Optional[str] = None

    home_phone: Optional[str] = None
    cell_phone: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    website_url: Optional[str] = None
    social_media_handles: Optional[Dict[str, str]] = None
    preferred_contact_method: Optional[str] = None
    interests: Optional[List[str]] = None
    preferred_language: Optional[str] = None

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None

    profile_photo: Optional[str] = None
    thumbnail_photo: Optional[str] = None
    personal_description: Optional[str] = None
    political_party: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    race: Optional[str] = None

    home_phone: Optional[str] = None
    cell_phone: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    website_url: Optional[str] = None
    social_media_handles: Optional[Dict[str, str]] = None
    preferred_contact_method: Optional[str] = None
    interests: Optional[List[str]] = None
    preferred_language: Optional[str] = None

class UserOut(UserBase):
    id: UUID
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    role: str
    profile_complete: bool

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None

    profile_photo: Optional[str] = None
    thumbnail_photo: Optional[str] = None
    personal_description: Optional[str] = None
    political_party: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    race: Optional[str] = None

    home_phone: Optional[str] = None
    cell_phone: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    website_url: Optional[str] = None
    social_media_handles: Optional[Dict[str, str]] = None
    preferred_contact_method: Optional[str] = None
    interests: Optional[List[str]] = None
    preferred_language: Optional[str] = None

    class Config:
        from_attributes = True
