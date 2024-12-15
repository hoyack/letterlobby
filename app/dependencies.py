from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from app.core.database import get_db
from app.models.user import User
from app.services.jwt_service import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        token_version = payload.get("token_version", 0)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Invalid user")

        if user.token_version != token_version:
            raise HTTPException(status_code=401, detail="Token revoked")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user

def require_verified_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return current_user

def require_admin_user(current_user: User = Depends(require_verified_user)) -> User:
    if current_user.role != "administrator":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user
