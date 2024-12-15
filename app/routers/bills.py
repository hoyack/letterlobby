from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.models.bill import Bill
from app.schemas.bill import BillCreate, BillOut, BillUpdate
from app.dependencies import require_admin_user

router = APIRouter(prefix="/bills", tags=["bills"])

@router.post("/", response_model=BillOut, status_code=status.HTTP_201_CREATED)
def create_bill(
    bill_data: BillCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_user)
):
    # Admin-only endpoint
    bill = Bill(**bill_data.dict())
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill

@router.get("/", response_model=list[BillOut])
def list_bills(db: Session = Depends(get_db)):
    # Public read, no auth required
    bills = db.query(Bill).all()
    return bills

@router.get("/{bill_id}", response_model=BillOut)
def get_bill(bill_id: UUID, db: Session = Depends(get_db)):
    # Public read, no auth required
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill

@router.patch("/{bill_id}", response_model=BillOut)
def update_bill(
    bill_id: UUID,
    bill_data: BillUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_user)
):
    # Admin-only endpoint
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    update_data = bill_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bill, field, value)

    db.commit()
    db.refresh(bill)
    return bill

@router.delete("/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bill(
    bill_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_user)
):
    # Admin-only endpoint
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    db.delete(bill)
    db.commit()
    return None
