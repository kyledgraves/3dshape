from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.models import Part, Account
from backend.schemas import PartCreate, PartUpdate, PartResponse

router = APIRouter(prefix="/parts", tags=["parts"])


@router.post("", response_model=PartResponse, status_code=201)
def create_part(part: PartCreate, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == part.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    if part.supplied_id:
        existing = db.query(Part).filter(Part.account_id == part.account_id, Part.supplied_id == part.supplied_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Duplicate supplied_id")
    
    db_part = Part(
        account_id=part.account_id,
        supplied_id=part.supplied_id,
        name=part.name,
        description=part.description,
        category=part.category,
        part_metadata=part.metadata
    )
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    return db_part


@router.get("", response_model=List[PartResponse])
def list_parts(
    account_id: Optional[int] = Query(None, description="Filter by account_id"),
    search: Optional[str] = Query(None, description="Search query"),
    db: Session = Depends(get_db)
):
    query = db.query(Part)
    
    if account_id is not None:
        query = query.filter(Part.account_id == account_id)
        
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Part.name.ilike(search_term)) | 
            (Part.description.ilike(search_term)) |
            (Part.supplied_id.ilike(search_term))
        )
    
    return query.all()


@router.get("/{part_id}", response_model=PartResponse)
def get_part(part_id: int, db: Session = Depends(get_db)):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    return part


@router.patch("/{part_id}", response_model=PartResponse)
def update_part(part_id: int, part_update: PartUpdate, db: Session = Depends(get_db)):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    update_data = part_update.model_dump(exclude_unset=True)
    if 'metadata' in update_data:
        part.part_metadata = update_data.pop('metadata')
    for field, value in update_data.items():
        setattr(part, field, value)
    
    db.commit()
    db.refresh(part)
    return part


@router.delete("/{part_id}", status_code=204)
def delete_part(part_id: int, db: Session = Depends(get_db)):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    db.delete(part)
    db.commit()
    return None
