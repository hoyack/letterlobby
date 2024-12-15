# app/routers/bills.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.core.database import get_db
from app.models.bill import Bill
from app.models.bill_politician import BillPolitician
from app.models.politician import Politician
from app.schemas.bill import BillCreate, BillOut, BillUpdate, BillPoliticianAssociationOut
from app.dependencies import get_current_user, require_verified_user
from app.models.user import User

router = APIRouter(prefix="/bills", tags=["bills"])

def require_admin_user(current_user: User = Depends(require_verified_user)) -> User:
    if current_user.role != "administrator":
        raise HTTPException(status_code=403, detail="Admin privilege required")
    return current_user

def set_bill_politicians(db: Session, bill: Bill, assoc_data: List[BillPoliticianAssociationOut]):
    # Clear existing associations
    db.query(BillPolitician).filter(BillPolitician.bill_id == bill.id).delete()
    db.commit()

    if assoc_data:
        bill_ids = [bill.id]  # just one bill here
        politician_ids = [a.politician_id for a in assoc_data]
        politicians = db.query(Politician).filter(Politician.id.in_(politician_ids)).all()
        if len(politicians) != len(politician_ids):
            raise HTTPException(status_code=400, detail="One or more politician_ids are invalid")

        for pdata in assoc_data:
            assoc = BillPolitician(
                bill_id=bill.id,
                politician_id=pdata.politician_id,
                does_support=pdata.does_support
            )
            db.add(assoc)
        db.commit()

def bill_to_out(db: Session, bill: Bill) -> BillOut:
    assocs = db.query(BillPolitician).filter(BillPolitician.bill_id == bill.id).all()
    politician_out = [{"politician_id": a.politician_id, "does_support": a.does_support} for a in assocs]

    return BillOut(
        title=bill.title,
        description=bill.description,
        bill_number=bill.bill_number,
        legislative_body=bill.legislative_body,
        status=bill.status,
        id=bill.id,
        created_at=bill.created_at,
        updated_at=bill.updated_at,
        politicians=politician_out
    )

@router.post("/", response_model=BillOut, status_code=status.HTTP_201_CREATED)
def create_bill(
    bill_data: BillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    bill = Bill(
        title=bill_data.title,
        description=bill_data.description,
        bill_number=bill_data.bill_number,
        legislative_body=bill_data.legislative_body,
        status=bill_data.status
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)

    if bill_data.politicians:
        set_bill_politicians(db, bill, bill_data.politicians)
        db.refresh(bill)

    return bill_to_out(db, bill)

@router.get("/", response_model=List[BillOut])
def list_bills(db: Session = Depends(get_db)):
    bills = db.query(Bill).all()
    return [bill_to_out(db, b) for b in bills]

@router.get("/{bill_id}", response_model=BillOut)
def get_bill(bill_id: UUID, db: Session = Depends(get_db)):
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill_to_out(db, bill)

@router.patch("/{bill_id}", response_model=BillOut)
def update_bill(
    bill_id: UUID,
    updates: BillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    if updates.title is not None:
        bill.title = updates.title
    if updates.description is not None:
        bill.description = updates.description
    if updates.bill_number is not None:
        bill.bill_number = updates.bill_number
    if updates.legislative_body is not None:
        bill.legislative_body = updates.legislative_body
    if updates.status is not None:
        bill.status = updates.status

    db.commit()
    db.refresh(bill)

    if updates.politicians is not None:
        set_bill_politicians(db, bill, updates.politicians)
        db.refresh(bill)

    return bill_to_out(db, bill)

@router.delete("/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bill(
    bill_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    db.delete(bill)
    db.commit()
    return None
