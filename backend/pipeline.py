# This file orchestrates the 10-stage AI processing pipeline asynchronously with progress updates.

import asyncio
import os
import time
import structlog
from datetime import datetime
from backend.agents.document_parser import parse_document
from backend.agents.classifier import classify_document
from backend.agents.knowledge_extractor import extract_knowledge
from backend.agents.teaching_planner import create_teaching_plan
from backend.agents.content_generator import generate_all_period_contents_async
from backend.agents.activity_generator import generate_activities
from backend.agents.assessment_generator import generate_assessments
from backend.agents.gap_analyzer import analyze_learning_gaps
from backend.agents.validator import validate_tkp
from backend.agents.publisher import publish_tkp

logger = structlog.get_logger()

job_store = {}

STAGE_DELAY = 0.5


# This class tracks job state, progress percentage, stage timers, and event queues for pipeline runs.
class PipelineJob:
    # This constructor initializes job attributes and sets up an async queue for live streaming.
    def __init__(self, job_id, file_path, user_context=None):
        self.job_id = job_id
        self.file_path = file_path
        self.user_context = user_context or {}
        self.status = "pending"
        self.progress = 0
        self.current_stage = ""
        self.message = ""
        self.result = None
        self.output_path = None
        self.error = None
        self.queue = asyncio.Queue()
        self.start_time = None
        self.end_time = None
        self.stage_times = {}


# This function pushes progress updates and status messages into the job async queue.
async def send_progress(job, stage, progress, message):
    job.current_stage = stage
    job.progress = progress
    job.message = message
    await job.queue.put({
        "stage": stage,
        "progress": progress,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })
    logger.info("pipeline_progress", stage=stage, progress=progress, message=message)


# Main async function that executes all 10 pipeline stages, parallelizing agents where possible.
async def run_pipeline(job):
    job.status = "running"
    job.start_time = time.time()
    ctx = job.user_context

    try:
        await send_progress(job, "document-intelligence", 5, "Parsing document...")
        stage_start = time.time()
        document = await asyncio.to_thread(parse_document, job.file_path)
        job.stage_times["document-intelligence"] = time.time() - stage_start
        await send_progress(job, "document-intelligence", 10,
                          f"Parsed {document.word_count} words, {len(document.sections)} sections")

        await asyncio.sleep(STAGE_DELAY)

        await send_progress(job, "classification", 15, "Classifying educational content...")
        stage_start = time.time()
        metadata = await asyncio.to_thread(classify_document, document, ctx)
        job.stage_times["classification"] = time.time() - stage_start
        await send_progress(job, "classification", 20,
                          f"Classified as {metadata.subject} - {metadata.topic} ({metadata.difficulty})")

        await asyncio.sleep(STAGE_DELAY)

        await send_progress(job, "knowledge-extraction", 25, "Extracting knowledge structures...")
        stage_start = time.time()
        knowledge = await asyncio.to_thread(extract_knowledge, document, metadata)
        job.stage_times["knowledge-extraction"] = time.time() - stage_start
        await send_progress(job, "knowledge-extraction", 35,
                          f"Extracted {len(knowledge.learning_objectives)} objectives, {len(knowledge.concepts)} concepts")

        await asyncio.sleep(STAGE_DELAY)

        await send_progress(job, "teaching-planning", 40, "Creating teaching plan...")
        stage_start = time.time()
        teaching_plan = await asyncio.to_thread(create_teaching_plan, metadata, knowledge, ctx)
        job.stage_times["teaching-planning"] = time.time() - stage_start
        await send_progress(job, "teaching-planning", 45,
                          f"Planned {teaching_plan.total_periods} periods of {teaching_plan.period_duration_minutes} min each")

        await asyncio.sleep(STAGE_DELAY)

        await send_progress(job, "content-generation", 50, "Generating classroom content for all periods (in parallel)...")
        stage_start = time.time()
        period_contents = await generate_all_period_contents_async(
            teaching_plan, metadata, knowledge, ctx
        )
        job.stage_times["content-generation"] = time.time() - stage_start
        await send_progress(job, "content-generation", 65,
                          f"Generated content for {len(period_contents)} periods")

        await asyncio.sleep(STAGE_DELAY)

        await send_progress(job, "parallel-generation", 70, "Generating activities, assessments, and gap analysis concurrently...")
        stage_start = time.time()
        
        activities_task = asyncio.to_thread(generate_activities, metadata, knowledge, teaching_plan)
        assessments_task = asyncio.to_thread(generate_assessments, metadata, knowledge)
        gaps_task = asyncio.to_thread(analyze_learning_gaps, metadata, knowledge)
        
        activities, assessments, learning_gaps = await asyncio.gather(
            activities_task, assessments_task, gaps_task
        )
        
        job.stage_times["parallel-generation"] = time.time() - stage_start
        total_q = (len(assessments.mcqs) + len(assessments.short_answers) +
                   len(assessments.long_answers) + len(assessments.numerical_problems))
                   
        await send_progress(job, "parallel-generation", 85,
                          f"Generated {len(activities)} activities, {total_q} assessment items, and {len(learning_gaps)} learning gaps.")

        await asyncio.sleep(STAGE_DELAY)

        await send_progress(job, "validation", 90, "Running validation checks...")
        stage_start = time.time()
        validation_report = await asyncio.to_thread(
            validate_tkp, document, metadata, knowledge, teaching_plan,
            period_contents, activities, assessments, learning_gaps
        )
        job.stage_times["validation"] = time.time() - stage_start
        await send_progress(job, "validation", 95,
                          f"Validation: {validation_report.passed_checks}/{validation_report.total_checks} checks passed")

        await send_progress(job, "publishing", 97, "Packaging Teacher Knowledge Package...")
        stage_start = time.time()
        tkp, output_path = await asyncio.to_thread(
            publish_tkp, document, metadata, knowledge, teaching_plan,
            period_contents, activities, assessments, learning_gaps, validation_report
        )
        job.stage_times["publishing"] = time.time() - stage_start

        job.result = tkp
        job.output_path = output_path
        job.status = "completed"
        job.end_time = time.time()
        total_time = job.end_time - job.start_time

        await send_progress(job, "completed", 100,
                          f"Done! Generated in {total_time:.1f}s. Output: {output_path}")

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.end_time = time.time()
        logger.error("pipeline_failed", error=str(e))
        await send_progress(job, "error", job.progress, f"Pipeline failed: {str(e)}")

    finally:
        if os.path.exists(job.file_path):
            try:
                os.remove(job.file_path)
            except Exception as e:
                logger.error("cleanup_failed", error=str(e))
        
        if len(job_store) > 100:
            old_jobs = sorted(job_store.values(), key=lambda j: j.start_time or 0)
            for j in old_jobs[:50]:
                if j.output_path and os.path.exists(j.output_path):
                    try:
                        os.remove(j.output_path)
                    except Exception as e:
                        logger.error("output_cleanup_failed", error=str(e))
                job_store.pop(j.job_id, None)

        await job.queue.put(None)
