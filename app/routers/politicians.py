from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.models.politician import Politician
from app.schemas.politician import PoliticianCreate, PoliticianOut, PoliticianUpdate
from app.dependencies import require_admin_user

router = APIRouter(prefix="/politicians", tags=["politicians"])

@router.post("/", response_model=PoliticianOut, status_code=status.HTTP_201_CREATED)
def create_politician(
    politician_data: PoliticianCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_user)
):
    # Admin-only endpoint
    politician = Politician(**politician_data.dict())
    db.add(politician)
    db.commit()
    db.refresh(politician)
    return politician

@router.get("/", response_model=list[PoliticianOut])
def list_politicians(db: Session = Depends(get_db)):
    # Public read, no auth required
    return db.query(Politician).all()

@router.get("/{politician_id}", response_model=PoliticianOut)
def get_politician(politician_id: UUID, db: Session = Depends(get_db)):
    # Public read, no auth required
    politician = db.query(Politician).filter(Politician.id == politician_id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
    return politician

@router.patch("/{politician_id}", response_model=PoliticianOut)
def update_politician(
    politician_id: UUID,
    politician_data: PoliticianUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_user)
):
    # Admin-only endpoint
    politician = db.query(Politician).filter(Politician.id == politician_id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")

    update_data = politician_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(politician, field, value)

    db.commit()
    db.refresh(politician)
    return politician

@router.delete("/{politician_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_politician(
    politician_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_user)
):
    # Admin-only endpoint
    politician = db.query(Politician).filter(Politician.id == politician_id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")

    db.delete(politician)
    db.commit()
    return None
