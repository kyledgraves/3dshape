from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import get_db
from backend.models import PartRevision
from backend.schemas import PartRevisionCreate, PartRevisionResponse, PartRevisionUpdate

router = APIRouter(prefix="/part-revisions", tags=["Part Revisions"])

@router.post("", response_model=PartRevisionResponse)
def create_part_revision(revision: PartRevisionCreate, db: Session = Depends(get_db)):
    db_revision = PartRevision(
        part_id=revision.part_id,
        revision_number=revision.revision_number,
        supplied_id=revision.supplied_id,
        status=revision.status,
        part_metadata=revision.metadata
    )
    db.add(db_revision)
    db.commit()
    db.refresh(db_revision)
    return db_revision

@router.get("", response_model=List[PartRevisionResponse])
def get_part_revisions(part_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = select(PartRevision)
    if part_id is not None:
        query = query.where(PartRevision.part_id == part_id)
    result = db.execute(query).scalars().all()
    return result

@router.get("/{revision_id}", response_model=PartRevisionResponse)
def get_part_revision(revision_id: int, db: Session = Depends(get_db)):
    db_revision = db.execute(select(PartRevision).where(PartRevision.id == revision_id)).scalar_one_or_none()
    if db_revision is None:
        raise HTTPException(status_code=404, detail="Part revision not found")
    return db_revision

@router.patch("/{revision_id}", response_model=PartRevisionResponse)
def update_part_revision(revision_id: int, revision: PartRevisionUpdate, db: Session = Depends(get_db)):
    db_revision = db.execute(select(PartRevision).where(PartRevision.id == revision_id)).scalar_one_or_none()
    if db_revision is None:
        raise HTTPException(status_code=404, detail="Part revision not found")
    
    update_data = revision.model_dump(exclude_unset=True)
    if 'metadata' in update_data:
        update_data['part_metadata'] = update_data.pop('metadata')
        
    for key, value in update_data.items():
        setattr(db_revision, key, value)
        
    db.commit()
    db.refresh(db_revision)
    return db_revision

@router.delete("/{revision_id}")
def delete_part_revision(revision_id: int, db: Session = Depends(get_db)):
    db_revision = db.execute(select(PartRevision).where(PartRevision.id == revision_id)).scalar_one_or_none()
    if db_revision is None:
        raise HTTPException(status_code=404, detail="Part revision not found")
    
    db.delete(db_revision)
    db.commit()
    return {"message": "Part revision deleted successfully"}
