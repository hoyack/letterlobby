from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.core.database import get_db
from app.schemas.user import (UserCreate, UserOut, UserLogin, Token, VerifyEmailRequest, PasswordResetRequest, PasswordResetConfirm)
from app.models.user import User
from app.services.security import hash_password, verify_password
from app.services.jwt_service import create_access_token
from app.dependencies import get_current_user, require_verified_user
from app.services.otp_service import create_otp_code, verify_otp_code, send_email
from app.core.config import settings

router = APIRouter(prefix="/users", tags=["users"])

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
        role="user"  # By default, new users have role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    code = create_otp_code(db, user.id, "verify_email", 30)
    send_email(user.email, "Verify your account", f"Your OTP code is: {code}")

    return user

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
    return current_user
