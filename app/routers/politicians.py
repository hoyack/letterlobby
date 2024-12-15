# app/routers/politicians.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.core.database import get_db
from app.models.politician import Politician
from app.models.bill_politician import BillPolitician
from app.models.bill import Bill
from app.schemas.politician import PoliticianCreate, PoliticianUpdate, PoliticianOut, PoliticianBillAssociationOut
from app.dependencies import get_current_user, require_verified_user
from app.models.user import User

router = APIRouter(prefix="/politicians", tags=["politicians"])

def require_admin_user(current_user: User = Depends(require_verified_user)) -> User:
    if current_user.role != "administrator":
        raise HTTPException(status_code=403, detail="Admin privilege required")
    return current_user

def set_politician_bills(db: Session, politician: Politician, bills_data: List[PoliticianBillAssociationOut]):
    # Clear existing associations
    db.query(BillPolitician).filter(BillPolitician.politician_id == politician.id).delete()
    db.commit()

    if bills_data:
        bill_ids = [b.bill_id for b in bills_data]
        bills = db.query(Bill).filter(Bill.id.in_(bill_ids)).all()
        if len(bills) != len(bill_ids):
            raise HTTPException(status_code=400, detail="One or more bill_ids are invalid")

        for b_data in bills_data:
            assoc = BillPolitician(
                bill_id=b_data.bill_id,
                politician_id=politician.id,
                does_support=b_data.does_support
            )
            db.add(assoc)
        db.commit()

def politician_to_out(db: Session, politician: Politician) -> PoliticianOut:
    assocs = db.query(BillPolitician).filter(BillPolitician.politician_id == politician.id).all()
    bills_out = [{"bill_id": a.bill_id, "does_support": a.does_support} for a in assocs]

    return PoliticianOut(
        name=politician.name,
        title=politician.title,
        office_address_line1=politician.office_address_line1,
        office_address_line2=politician.office_address_line2,
        office_city=politician.office_city,
        office_state=politician.office_state,
        office_zip=politician.office_zip,
        legislative_body=politician.legislative_body,
        email=politician.email,
        id=politician.id,
        created_at=politician.created_at,
        updated_at=politician.updated_at,
        bills=bills_out
    )

@router.post("/", response_model=PoliticianOut, status_code=status.HTTP_201_CREATED)
def create_politician(
    data: PoliticianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    politician = Politician(
        name=data.name,
        title=data.title,
        office_address_line1=data.office_address_line1,
        office_address_line2=data.office_address_line2,
        office_city=data.office_city,
        office_state=data.office_state,
        office_zip=data.office_zip,
        legislative_body=data.legislative_body,
        email=data.email
    )
    db.add(politician)
    db.commit()
    db.refresh(politician)

    if data.bills:
        set_politician_bills(db, politician, data.bills)
        db.refresh(politician)

    return politician_to_out(db, politician)

@router.get("/", response_model=List[PoliticianOut])
def list_politicians(db: Session = Depends(get_db)):
    politicians = db.query(Politician).all()
    return [politician_to_out(db, p) for p in politicians]

@router.get("/{politician_id}", response_model=PoliticianOut)
def get_politician(politician_id: UUID, db: Session = Depends(get_db)):
    politician = db.query(Politician).filter(Politician.id == politician_id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
    return politician_to_out(db, politician)

@router.patch("/{politician_id}", response_model=PoliticianOut)
def update_politician(
    politician_id: UUID,
    updates: PoliticianUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    politician = db.query(Politician).filter(Politician.id == politician_id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")

    if updates.name is not None:
        politician.name = updates.name
    if updates.title is not None:
        politician.title = updates.title
    if updates.office_address_line1 is not None:
        politician.office_address_line1 = updates.office_address_line1
    if updates.office_address_line2 is not None:
        politician.office_address_line2 = updates.office_address_line2
    if updates.office_city is not None:
        politician.office_city = updates.office_city
    if updates.office_state is not None:
        politician.office_state = updates.office_state
    if updates.office_zip is not None:
        politician.office_zip = updates.office_zip
    if updates.legislative_body is not None:
        politician.legislative_body = updates.legislative_body
    if updates.email is not None:
        politician.email = updates.email

    db.commit()
    db.refresh(politician)

    if updates.bills is not None:
        set_politician_bills(db, politician, updates.bills)
        db.refresh(politician)

    return politician_to_out(db, politician)

@router.delete("/{politician_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_politician(
    politician_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    politician = db.query(Politician).filter(Politician.id == politician_id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")

    db.delete(politician)
    db.commit()
    return None
