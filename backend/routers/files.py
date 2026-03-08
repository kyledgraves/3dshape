from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, File as FastAPIFile
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import get_db
from backend.models import File, PartRevision
from backend.schemas import FileResponse

router = APIRouter(prefix="/files", tags=["Files"])

@router.post("", response_model=FileResponse)
def upload_file(
    part_revision_id: str = Form(...),
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db)
):
    try:
        part_rev_id = int(part_revision_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid part_revision_id")

    # verify revision exists
    db_revision = db.execute(select(PartRevision).where(PartRevision.id == part_rev_id)).scalar_one_or_none()
    if not db_revision:
        raise HTTPException(status_code=404, detail="Part revision not found")

    file_bytes = file.file.read()
    file_size = len(file_bytes)
    
    db_file = File(
        part_revision_id=part_rev_id,
        original_filename=file.filename,
        file_data=file_bytes,
        file_size=file_size,
        status="uploaded"
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return db_file

@router.get("/{file_id}", response_model=FileResponse)
def get_file_record(file_id: int, db: Session = Depends(get_db)):
    db_file = db.execute(select(File).where(File.id == file_id)).scalar_one_or_none()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return db_file

@router.get("/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db)):
    db_file = db.execute(select(File).where(File.id == file_id)).scalar_one_or_none()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    if db_file.file_data is None:
        raise HTTPException(status_code=404, detail="File data not found")
        
    return Response(
        content=db_file.file_data, 
        headers={
            "Content-Disposition": f'attachment; filename="{db_file.original_filename}"'
        }
    )
