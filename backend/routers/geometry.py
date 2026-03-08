from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.models import Geometry, PartRevision
from backend.schemas import GeometryCreate, GeometryResponse

router = APIRouter(tags=["Geometry"])

@router.post("/geometry", response_model=GeometryResponse, status_code=201)
def create_geometry(geometry: GeometryCreate, db: Session = Depends(get_db)):
    db_part_rev = db.query(PartRevision).filter(PartRevision.id == geometry.part_revision_id).first()
    if not db_part_rev:
        raise HTTPException(status_code=404, detail="Part revision not found")
        
    db_geometry = Geometry(
        part_revision_id=geometry.part_revision_id,
        format=geometry.format,
        version=geometry.version,
        vertex_count=geometry.vertex_count,
        face_count=geometry.face_count,
        bounding_box=geometry.bounding_box,
        data=geometry.data
    )
    db.add(db_geometry)
    db.commit()
    db.refresh(db_geometry)
    return db_geometry

@router.get("/geometry/{id}", response_model=GeometryResponse)
def get_geometry(id: int, db: Session = Depends(get_db)):
    db_geometry = db.query(Geometry).filter(Geometry.id == id).first()
    if not db_geometry:
        raise HTTPException(status_code=404, detail="Geometry not found")
    return db_geometry

@router.get("/geometry/{id}/data")
def get_geometry_data(id: int, db: Session = Depends(get_db)):
    db_geometry = db.query(Geometry).filter(Geometry.id == id).first()
    if not db_geometry:
        raise HTTPException(status_code=404, detail="Geometry not found")
    if db_geometry.data is None:
        raise HTTPException(status_code=404, detail="Geometry data not found")
    
    return db_geometry.data
