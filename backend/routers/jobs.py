from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid
import time

from backend.database import get_db
from backend.models import File
from backend.schemas import ConversionJobCreate, ConversionJobResponse

router = APIRouter(tags=["Jobs"])

# A simple dictionary to store fake jobs
JOBS_STORE = {}

def process_conversion_job(job_id: str, file_id: int):
    # sleep 1 second
    time.sleep(1)
    
    # Create a new session for the background task
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        db_file = db.execute(select(File).where(File.id == file_id)).scalar_one_or_none()
        if db_file:
            db_file.status = "completed"
            db.commit()
        JOBS_STORE[job_id] = "completed"
    finally:
        db.close()

@router.post("/convert", response_model=ConversionJobResponse)
def create_conversion_job(
    job_req: ConversionJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        file_id_int = int(job_req.file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file_id")
        
    db_file = db.execute(select(File).where(File.id == file_id_int)).scalar_one_or_none()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
        
    job_id = f"job-{uuid.uuid4()}"
    JOBS_STORE[job_id] = "processing"
    
    db_file.status = "processing"
    db.commit()
    
    background_tasks.add_task(process_conversion_job, job_id, file_id_int)
    
    return {"job_id": job_id, "status": "processing"}

@router.get("/jobs/{job_id}", response_model=ConversionJobResponse)
def get_job_status(job_id: str):
    if job_id not in JOBS_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "status": JOBS_STORE[job_id]}
