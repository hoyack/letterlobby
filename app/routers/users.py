from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile, File
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Dict, Any, Union
import base64
from io import BytesIO
from PIL import Image

from app.core.database import get_db
from app.schemas.user import (
    ChangeEmailRequest, ChangeEmailVerifyRequest, UserCreate, UserOut, UserLogin, Token, VerifyEmailRequest,
    PasswordResetRequest, PasswordResetConfirm, UserProfile, UserProfileUpdate
)
from app.models.user import User
from app.services.security import hash_password, verify_password
from app.services.jwt_service import create_access_token
from app.dependencies import require_verified_user
from app.services.otp_service import create_otp_code, verify_otp_code, send_email
from app.core.config import settings

router = APIRouter(prefix="/users", tags=["users"])

def user_to_userout(user: User) -> UserOut:
    # Convert binary images to base64 if present
    user_dict = {
        "email": user.email,
        "id": user.id,
        "is_verified": user.is_verified,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "role": user.role,
        "profile_complete": user.profile_complete,

        "first_name": user.first_name,
        "last_name": user.last_name,
        "address_line1": user.address_line1,
        "address_line2": user.address_line2,
        "city": user.city,
        "state": user.state,
        "zipcode": user.zipcode,

        "personal_description": user.personal_description,
        "political_party": user.political_party,
        "date_of_birth": user.date_of_birth,
        "gender": user.gender,
        "race": user.race,
        "home_phone": user.home_phone,
        "cell_phone": user.cell_phone,
        "occupation": user.occupation,
        "employer": user.employer,
        "website_url": user.website_url,
        "social_media_handles": user.social_media_handles,
        "preferred_contact_method": user.preferred_contact_method,
        "interests": user.interests,
        "preferred_language": user.preferred_language
    }

    if user.profile_photo is not None:
        user_dict["profile_photo"] = base64.b64encode(user.profile_photo).decode('utf-8')
    else:
        user_dict["profile_photo"] = None

    if user.thumbnail_photo is not None:
        user_dict["thumbnail_photo"] = base64.b64encode(user.thumbnail_photo).decode('utf-8')
    else:
        user_dict["thumbnail_photo"] = None

    return UserOut(**user_dict)

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        is_verified=False,
        is_active=True,
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    code = create_otp_code(db, user.id, "verify_email", 30)
    send_email(user.email, "Verify your account", f"Your OTP code is: {code}")

    return user_to_userout(user)

@router.post("/verify-email")
def verify_email(data: VerifyEmailRequest, db: Session = Depends(get_db)):
    user = verify_otp_code(db, data.email, data.code, "verify_email")
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return {"message": "Email verified"}

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "token_version": user.token_version},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(current_user: User = Depends(require_verified_user), db: Session = Depends(get_db)):
    current_user.token_version += 1
    db.commit()
    db.refresh(current_user)
    return {"message": "Logged out"}

@router.post("/request-password-reset")
def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user with that email")
    code = create_otp_code(db, user.id, "reset_password", 30)
    send_email(user.email, "Reset your password", f"Your reset code is: {code}")
    return {"message": "Check your email for a reset code"}

@router.post("/reset-password")
def reset_password(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    user = verify_otp_code(db, data.email, data.code, "reset_password")
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    db.refresh(user)
    return {"message": "Password updated"}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(require_verified_user)):
    return user_to_userout(current_user)

@router.post("/me/query")
def query_me(fields: Dict[str, Any] = Body(...), current_user: User = Depends(require_verified_user)):
    if "fields" not in fields or not isinstance(fields["fields"], list):
        raise HTTPException(status_code=400, detail="Invalid request format")

    userout = user_to_userout(current_user)
    requested_fields = fields["fields"]
    response = {}
    userout_dict = userout.dict()
    for field in requested_fields:
        if field in userout_dict:
            response[field] = userout_dict[field]

    return response

@router.post("/me/profile", response_model=UserOut)
def create_or_replace_profile(profile_data: UserProfile, db: Session = Depends(get_db), current_user: User = Depends(require_verified_user)):
    update_user_profile_fields(profile_data, current_user)
    current_user.profile_complete = True
    db.commit()
    db.refresh(current_user)
    return user_to_userout(current_user)

@router.patch("/me/profile", response_model=UserOut)
def update_profile(profile_data: UserProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_verified_user)):
    update_user_profile_fields(profile_data, current_user)
    db.commit()
    db.refresh(current_user)
    return user_to_userout(current_user)

@router.delete("/me/profile", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(db: Session = Depends(get_db), current_user: User = Depends(require_verified_user)):
    reset_user_profile_fields(current_user)
    current_user.profile_complete = False
    db.commit()
    return None

@router.post("/me/profile/photo", response_model=UserOut)
def upload_profile_photo(
    profile_photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    if profile_photo.content_type not in ["image/png", "image/jpeg", "image/gif"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Accepted: PNG, JPG, GIF.")

    file_bytes = profile_photo.file.read()
    try:
        img = Image.open(BytesIO(file_bytes))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not identify image file.")

    img_400 = img.copy().resize((400, 400))
    output_400 = BytesIO()
    img_400.save(output_400, format="PNG")

    img_40 = img.copy().resize((40,40))
    output_40 = BytesIO()
    img_40.save(output_40, format="PNG")

    current_user.profile_photo = output_400.getvalue()
    current_user.thumbnail_photo = output_40.getvalue()
    db.commit()
    db.refresh(current_user)

    return user_to_userout(current_user)

def update_user_profile_fields(profile_data: Union[UserProfile, UserProfileUpdate], user: User):
    data = profile_data.dict(exclude_unset=True)
    if "profile_photo" in data:
        data.pop("profile_photo")
    if "thumbnail_photo" in data:
        data.pop("thumbnail_photo")

    for field, value in data.items():
        setattr(user, field, value)

def reset_user_profile_fields(user: User):
    profile_fields = [
        "first_name","last_name","address_line1","address_line2","city","state","zipcode",
        "profile_photo","thumbnail_photo","personal_description","political_party",
        "date_of_birth","gender","race","home_phone","cell_phone","occupation","employer",
        "website_url","social_media_handles","preferred_contact_method","interests","preferred_language"
    ]
    for field in profile_fields:
        setattr(user, field, None)

@router.post("/me/change-email")
def request_email_change(
    data: ChangeEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    if not verify_password(data.password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    existing = db.query(User).filter(User.email == data.new_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use")

    code = create_otp_code(db, current_user.id, "change_email", 30)
    send_email(data.new_email, "Verify your new email", f"Your OTP code: {code}")
    return {"message": "Check your new email for a verification code."}

@router.post("/me/change-email/verify")
def verify_email_change(
    data: ChangeEmailVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    user = verify_otp_code(db, data.new_email, data.code, "change_email", user_id=current_user.id)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    current_user.email = data.new_email
    current_user.token_version += 1
    db.commit()
    db.refresh(current_user)

    return {"message": "Email changed successfully."}
