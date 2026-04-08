from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os
import shutil
import traceback
import logging

from core.db import get_db
from models.database import FileRecord
from core.redis_client import task_queue
from rq.job import Job
from core.redis_client import redis_conn
from services.upload_service import merge_roadmap_chunks, process_upload_task, process_supplementary_upload_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/spaces", tags=["Files"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/{space_id}/upload")
def upload_file(space_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        file_path = os.path.join(UPLOAD_DIR, f"{space_id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        ftype = "pdf" if file.filename.lower().endswith(".pdf") else "ppt"
        
        record = FileRecord(
            space_id=space_id,
            filename=file.filename,
            filepath=file_path,
            file_type=ftype,
            processed=False
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        job = task_queue.enqueue(process_upload_task, space_id, record.id, file_path, ftype)

        return {"message": "OK", "job_id": job.id, "file_record_id": record.id}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/status/{job_id}")
def get_task_status(job_id: str):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        if job.is_finished:
            return {"status": "completed", "result": job.result}
        elif job.is_failed:
            return {"status": "failed", "error": str(job.exc_info)}
        else:
            job.refresh()
            msg = job.meta.get("progress_message", "processing...")
            return {"status": "processing", "message": msg}
    except Exception as e:
        return {"status": "not_found", "detail": str(e)}

@router.post("/{space_id}/upload_supplementary")
def upload_supplementary_file(space_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        file_path = os.path.join(UPLOAD_DIR, f"{space_id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        fname_lower = file.filename.lower()
        if fname_lower.endswith(".pdf"):
            ftype = "pdf"
        elif fname_lower.endswith(".ppt") or fname_lower.endswith(".pptx"):
            ftype = "ppt"
        elif fname_lower.endswith(".jpg") or fname_lower.endswith(".jpeg") or fname_lower.endswith(".png") or fname_lower.endswith(".webp"):
            ftype = "jpg"
        else:
            ftype = "txt"
            
        record = FileRecord(
            space_id=space_id,
            filename=file.filename,
            filepath=file_path,
            file_type=ftype,
            processed=False
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        job = task_queue.enqueue(process_supplementary_upload_task, space_id, record.id, file_path, ftype)

        return {"message": "OK", "job_id": job.id, "file_record_id": record.id}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))