# app/models/user.py

import uuid
from sqlalchemy import Column, Date, LargeBinary, String, DateTime, Boolean, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    token_version = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Default role is 'user'. Possible values now are 'user' or 'administrator'.
    role = Column(String, nullable=False, server_default='user')
    profile_complete = Column(Boolean, nullable=False, server_default='false')
    
    # Profile fields
    first_name = Column(String)
    last_name = Column(String)
    address_line1 = Column(String)
    address_line2 = Column(String)
    city = Column(String)
    state = Column(String)
    zipcode = Column(String)
    
    profile_photo = Column(LargeBinary)      # Store binary for the image after resizing
    thumbnail_photo = Column(LargeBinary)    # binary for thumbnail image
    personal_description = Column(String)
    political_party = Column(String)
    date_of_birth = Column(Date)
    gender = Column(String)
    race = Column(String)

    # Additional fields suggested
    home_phone = Column(String)
    cell_phone = Column(String)
    occupation = Column(String)
    employer = Column(String)
    website_url = Column(String)
    social_media_handles = Column(JSON)   # e.g. {"twitter": "@handle", "linkedin": "url"}
    preferred_contact_method = Column(String)  # e.g. "email", "cell", etc.
    interests = Column(JSON)  # e.g. ["reading","hiking","coding"]
    preferred_language = Column(String)   # e.g. "en", "es"
