# This file defines the FastAPI REST server endpoints for uploading documents, streaming SSE progress, and getting results.

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import uuid
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from backend.config import UPLOAD_DIR, OUTPUT_DIR
from backend.pipeline import PipelineJob, run_pipeline, job_store

app = FastAPI(
    title="Teacher AI Platform",
    description="AI-powered system that converts educational documents into Teacher Knowledge Packages",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API endpoint to check if backend server is healthy and running.
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


# API endpoint to handle document upload and start background pipeline execution.
@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    grade_level: Optional[str] = Form(None),
    subject_hint: Optional[str] = Form(None),
    teaching_style: Optional[str] = Form(None),
    max_periods: Optional[int] = Form(None),
    document_type: Optional[str] = Form(None),
    curriculum_alignment: Optional[str] = Form(None),
    target_language: Optional[str] = Form(None),
):
    allowed_extensions = [".pdf", ".docx", ".pptx", ".ppt", ".txt"]
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    job_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{job_id}{file_ext}")

    with open(file_path, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

    user_context = {
        "grade_level": grade_level or "",
        "subject_hint": subject_hint or "",
        "teaching_style": teaching_style or "Balanced",
        "max_periods": max_periods or 0,
        "document_type": document_type or "Not Sure",
        "curriculum_alignment": curriculum_alignment or "General",
        "target_language": target_language or "English",
    }

    job = PipelineJob(job_id=job_id, file_path=file_path, user_context=user_context)
    job_store[job_id] = job

    asyncio.create_task(run_pipeline(job))

    return {"job_id": job_id, "filename": file.filename, "status": "started", "user_context": user_context}


# SSE endpoint to stream real-time pipeline execution progress to frontend clients.
@app.get("/stream/{job_id}")
async def stream_progress(job_id: str):
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_store[job_id]

    async def event_generator():
        while True:
            try:
                data = await asyncio.wait_for(job.queue.get(), timeout=600)
                if data is None:
                    yield f"data: {json.dumps({'stage': 'done', 'progress': 100, 'message': 'Pipeline complete'})}\n\n"
                    break
                yield f"data: {json.dumps(data)}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'stage': 'timeout', 'progress': 0, 'message': 'Pipeline timed out'})}\n\n"
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# API endpoint to retrieve completed TKP result data and stage timing stats.
@app.get("/result/{job_id}")
async def get_result(job_id: str):
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_store[job_id]

    if job.status == "running":
        return JSONResponse(
            content={
                "status": "running",
                "progress": job.progress,
                "current_stage": job.current_stage,
                "message": job.message
            },
            status_code=202
        )

    if job.status == "failed":
        raise HTTPException(status_code=500, detail=job.error)

    if job.result:
        return {
            "status": "completed",
            "output_path": job.output_path,
            "tkp": job.result.model_dump(),
            "stage_times": job.stage_times,
            "total_time": (job.end_time - job.start_time) if job.end_time else 0
        }

    return {"status": job.status}


# API endpoint to list all currently tracked pipeline jobs and their statuses.
@app.get("/jobs")
async def list_jobs():
    jobs = []
    for job_id, job in job_store.items():
        jobs.append({
            "job_id": job_id,
            "status": job.status,
            "progress": job.progress,
            "current_stage": job.current_stage
        })
    return {"jobs": jobs}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
