# app/routers/global_return_address.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.models.global_return_address import GlobalReturnAddress
from app.schemas.global_return_address import GlobalReturnAddressCreate, GlobalReturnAddressOut, GlobalReturnAddressUpdate
from app.models.user import User
from app.dependencies import require_verified_user

router = APIRouter(prefix="/global-return-address", tags=["global_return_address"])

def is_admin(current_user: User) -> bool:
    return current_user.role == "administrator"

def get_global_return_address_or_404(db: Session) -> GlobalReturnAddress:
    addr = db.query(GlobalReturnAddress).first()
    if not addr:
        raise HTTPException(status_code=404, detail="No global return address set.")
    return addr

@router.get("/", response_model=GlobalReturnAddressOut)
def get_global_return_address(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    addr = db.query(GlobalReturnAddress).first()
    if not addr:
        raise HTTPException(status_code=404, detail="No global return address set.")
    return addr

@router.post("/", response_model=GlobalReturnAddressOut, status_code=status.HTTP_201_CREATED)
def create_global_return_address(
    data: GlobalReturnAddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")

    existing = db.query(GlobalReturnAddress).first()
    if existing:
        raise HTTPException(status_code=400, detail="Global return address already exists.")

    new_addr = GlobalReturnAddress(**data.dict())
    db.add(new_addr)
    db.commit()
    db.refresh(new_addr)
    return new_addr

@router.patch("/", response_model=GlobalReturnAddressOut)
def update_global_return_address(
    data: GlobalReturnAddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")

    addr = get_global_return_address_or_404(db)
    update_data = data.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(addr, field, value)

    db.commit()
    db.refresh(addr)
    return addr

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_global_return_address(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")

    addr = get_global_return_address_or_404(db)
    db.delete(addr)
    db.commit()
    return None
