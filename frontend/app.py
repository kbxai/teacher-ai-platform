# This file provides the interactive Streamlit user interface for uploading documents, monitoring live pipeline progress, viewing TKPs, and downloading exports.

import sys
import os
import asyncio
import uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
import json
import time
import sseclient
from backend.agents.exporter import (
    generate_lesson_plan_html,
    generate_teacher_guide_html,
    generate_assessment_book_html
)
from backend.pipeline import PipelineJob, run_pipeline

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Teacher AI Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 0.5rem 0 0.2rem 0;
        margin-bottom: 0.2rem;
    }
    
    .sub-header {
        text-align: center;
        color: #4b5563;
        font-size: 1.15rem;
        margin-bottom: 2.5rem;
        font-weight: 400;
    }
    
    .stage-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #e2e8f0 100%);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.5rem 0;
        border: 1px solid #cbd5e1;
    }
    
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.03);
    }
    
    .success-badge {
        background: #d1fae5;
        color: #065f46;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .fail-badge {
        background: #fee2e2;
        color: #991b1b;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid #f1f5f9;
        padding-bottom: 6px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 500;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        color: #475569;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #f1f5f9;
        color: #1e3a8a;
        border-color: #cbd5e1;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1e3a8a !important;
        color: #ffffff !important;
        border-color: #1e3a8a !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">Teacher AI Platform</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Transform educational documents into classroom-ready Teacher Knowledge Packages</p>', unsafe_allow_html=True)

if "job_id" not in st.session_state:
    st.session_state.job_id = None
if "tkp_data" not in st.session_state:
    st.session_state.tkp_data = None
if "processing" not in st.session_state:
    st.session_state.processing = False

with st.sidebar:
    st.header("Upload Document")

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    if os.path.exists(output_dir):
        json_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".json")]
        if json_files:
            latest_file = max(json_files, key=os.path.getmtime)
            if st.button("Load Latest Generated Output", type="secondary", use_container_width=True):
                with open(latest_file, "r", encoding="utf-8") as f:
                    st.session_state.tkp_data = json.load(f)
                    st.session_state.processing = False
                    st.rerun()

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["pdf", "docx", "pptx", "txt"],
        help="Upload file"
    )

    if uploaded_file:
        st.markdown("---")
        st.header("Tell Us About Your Document")
        st.caption("Provide context")

        grade_level = st.selectbox(
            "Target Grade Level",
            ["Auto-detect", "Class 6", "Class 7", "Class 8", "Class 9", "Class 10",
             "Class 11", "Class 12", "College", "General"],
            index=0
        )

        subject_hint = st.selectbox(
            "Subject",
            ["Auto-detect", "Physics", "Chemistry", "Biology", "Mathematics",
             "History", "Geography", "Political Science", "Economics",
             "English", "Hindi", "Computer Science", "Other"],
            index=0
        )

        teaching_style = st.selectbox(
            "Preferred Teaching Style",
            ["Balanced", "Interactive & Activity-heavy", "Lecture-based",
             "Discussion-based", "Inquiry & Exploration"],
            index=0
        )

        max_periods = st.slider(
            "Available Periods",
            min_value=0, max_value=8, value=0,
            help="AI will decide if 0"
        )

        curriculum_alignment = st.selectbox(
            "Curriculum Alignment",
            ["General", "CBSE", "ICSE", "Common Core", "IB", "State Board"],
            index=0
        )

        target_language = st.selectbox(
            "Target Language",
            ["English", "Hindi", "Spanish", "French", "German"],
            index=0
        )

        pedagogical_framework = st.selectbox(
            "Pedagogical Framework",
            ["Standard", "5E Model (Engage, Explore, Explain, Elaborate, Evaluate)", "Project-Based Learning", "Flipped Classroom"],
            index=0
        )

        document_type = st.radio(
            "Document Type",
            ["Not Sure (let AI decide)", "Mostly Text", "Text with Tables",
             "Text with Diagrams/Figures", "Text with Equations", "Scanned PDF"],
            index=0
        )

        st.markdown("---")

    if uploaded_file and not st.session_state.processing:
        if st.button("Generate Teaching Package", type="primary", use_container_width=True):
            st.session_state.processing = True
            st.session_state.tkp_data = None

            style_text = teaching_style if pedagogical_framework == "Standard" else f"{teaching_style} (Framework: {pedagogical_framework})"
            try:
                form_data = {
                    "grade_level": "" if grade_level == "Auto-detect" else grade_level,
                    "subject_hint": "" if subject_hint == "Auto-detect" else subject_hint,
                    "teaching_style": style_text,
                    "max_periods": str(max_periods),
                    "document_type": document_type,
                    "curriculum_alignment": curriculum_alignment,
                    "target_language": target_language,
                }
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                response = requests.post(
                    f"{BACKEND_URL}/upload",
                    files=files,
                    data=form_data,
                    timeout=5
                )

                if response.status_code == 200:
                    data = response.json()
                    st.session_state.job_id = data["job_id"]
                    st.rerun()
                else:
                    st.error(f"Upload failed: {response.text}")
                    st.session_state.processing = False
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                job_id = str(uuid.uuid4())
                upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, f"{job_id}_{uploaded_file.name}")
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())

                job = PipelineJob(job_id, file_path, form_data)

                st.markdown("---")
                st.markdown("### Processing Pipeline")
                progress_bar = st.progress(0)
                status_text = st.empty()
                stage_log = st.empty()
                log_messages = []

                async def run_and_stream():
                    async def ui_consumer():
                        while True:
                            try:
                                item = await asyncio.wait_for(job.queue.get(), timeout=0.1)
                                if item is None:
                                    break
                                p = item.get("progress", 0)
                                msg = item.get("message", "")
                                stg = item.get("stage", "")
                                progress_bar.progress(min(p, 100))
                                status_text.markdown(f"**Stage:** `{stg}` | **Progress:** {p}% | {msg}")
                                log_messages.append(f"[{stg}] {msg}")
                                stage_log.markdown("\n\n".join(log_messages[-5:]))
                            except asyncio.TimeoutError:
                                if job.status in ["completed", "failed"] and job.queue.empty():
                                    break

                    await asyncio.gather(run_pipeline(job), ui_consumer())

                asyncio.run(run_and_stream())

                if job.result:
                    res = job.result
                    if hasattr(res, "model_dump"):
                        res = res.model_dump()
                    st.session_state.tkp_data = json.loads(json.dumps(res, default=str))
                    st.session_state.processing = False
                    st.rerun()
                else:
                    st.error(f"Pipeline error: {job.error}")
                    st.session_state.processing = False
            except Exception as e:
                st.error(f"Connection error: {e}")
                st.session_state.processing = False

    if st.session_state.processing:
        st.info("Processing... Please wait.")

    st.markdown("---")
    st.markdown("### Pipeline Stages")
    stages = [
        "Stage 1: Document Intelligence",
        "Stage 2: Educational Classification",
        "Stage 3: Knowledge Extraction",
        "Stage 4: Teaching Planning",
        "Stage 5: Content Generation",
        "Stage 6: Activity Design",
        "Stage 7: Assessment Creation",
        "Stage 8: Learning Gap Analysis",
        "Stage 9: Validation",
        "Stage 10: Publishing"
    ]
    for stage in stages:
        st.markdown(f"- {stage}")

if st.session_state.processing and st.session_state.job_id:
    st.markdown("### Processing Pipeline")
    progress_bar = st.progress(0)
    status_text = st.empty()
    stage_log = st.empty()

    log_messages = []

    try:
        response = requests.get(
            f"{BACKEND_URL}/stream/{st.session_state.job_id}",
            stream=True,
            timeout=600
        )

        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    progress = data.get("progress", 0)
                    message = data.get("message", "")
                    stage = data.get("stage", "")

                    progress_bar.progress(min(progress, 100))
                    status_text.markdown(f"**Stage:** `{stage}` | **Progress:** {progress}% | {message}")

                    log_messages.append(f"[{stage}] {message}")
                    stage_log.markdown("\n\n".join(log_messages[-5:]))

                    if stage == "done" or progress >= 100:
                        break
                except json.JSONDecodeError:
                    continue

    except Exception as e:
        st.error(f"Streaming error: {e}")

    for _retry in range(3):
        try:
            result_response = requests.get(
                f"{BACKEND_URL}/result/{st.session_state.job_id}",
                timeout=30
            )

            if result_response.status_code == 200:
                result_data = result_response.json()
                if result_data.get("status") == "completed":
                    st.session_state.tkp_data = result_data.get("tkp", {})
                    st.session_state.stage_times = result_data.get("stage_times", {})
                    st.session_state.total_time = result_data.get("total_time", 0)
                    st.session_state.processing = False
                    st.rerun()
            time.sleep(1.5)
        except Exception as e:
            time.sleep(1)

    if not st.session_state.tkp_data:
        st.error("Failed to retrieve results automatically. Please check the outputs directory.")

    st.session_state.processing = False

if st.session_state.tkp_data:
    tkp = st.session_state.tkp_data
    if hasattr(tkp, "model_dump"):
        tkp = tkp.model_dump()
    elif not isinstance(tkp, dict):
        try:
            tkp = json.loads(json.dumps(tkp, default=str))
        except Exception:
            pass

    tabs = st.tabs([
        "Overview",
        "Knowledge Map",
        "Teaching Plan",
        "Lesson Content",
        "Activities",
        "Assessments",
        "Learning Gaps",
        "Validation",
        "Observability",
        "Download"
    ])

    with tabs[0]:
        st.header("Document Overview")

        meta = tkp.get("educational_metadata", {})
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Subject", meta.get("subject", "N/A"))
        with col2:
            st.metric("Grade Level", meta.get("grade_level", "N/A"))
        with col3:
            st.metric("Difficulty", meta.get("difficulty", "N/A"))
        with col4:
            st.metric("Category", meta.get("category", "N/A"))

        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.metric("Topic", meta.get("topic", "N/A"))
        with col6:
            st.metric("Board", meta.get("board_alignment", "N/A"))
        with col7:
            doc = tkp.get("document_structure", {})
            st.metric("Words", doc.get("word_count", 0))
        with col8:
            st.metric("Teaching Hours", meta.get("estimated_teaching_hours", 0))

        st.markdown("### Summary")
        st.info(meta.get("summary", "No summary available"))

        if hasattr(st.session_state, "stage_times"):
            st.markdown("### Pipeline Performance")
            for stage, duration in st.session_state.stage_times.items():
                st.markdown(f"- **{stage}**: {duration:.1f}s")

    with tabs[1]:
        st.header("Knowledge Map")
        kg = tkp.get("knowledge_graph", {})

        st.subheader("Learning Objectives")
        for obj in kg.get("learning_objectives", []):
            bloom = obj.get("blooms_level", "")
            cit = obj.get("source_citation", "")
            cit_txt = f" (Source: {cit})" if cit else ""
            st.markdown(f"- **[{bloom}]** {obj.get('objective', '')}{cit_txt}")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Prerequisites")
            for prereq in kg.get("prerequisites", []):
                st.markdown(f"- {prereq}")

            st.subheader("Keywords")
            keywords = kg.get("keywords", [])
            if keywords:
                st.markdown(" | ".join([f"`{k}`" for k in keywords]))

        with col2:
            st.subheader("Real-world Applications")
            for app in kg.get("applications", []):
                st.markdown(f"- {app}")

            st.subheader("Formulae")
            for formula in kg.get("formulae", []):
                st.markdown(f"- **{formula.get('name', '')}**: `{formula.get('formula', '')}`")

        st.subheader("Core Concepts")
        for concept in kg.get("concepts", []):
            with st.expander(f"Concept: {concept.get('name', 'Concept')}"):
                st.markdown(f"**Definition:** {concept.get('definition', '')}")
                st.markdown(f"**Explanation:** {concept.get('explanation', '')}")
                cit = concept.get("source_citation", "")
                if cit:
                    st.caption(f"Source Traceability: {cit}")
                related = concept.get("related_concepts", [])
                if related:
                    st.markdown(f"**Related:** {', '.join(related)}")

    with tabs[2]:
        st.header("Teaching Plan")
        tp = tkp.get("teaching_plan", {})

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Periods", tp.get("total_periods", 0))
        with col2:
            st.metric("Period Duration", f"{tp.get('period_duration_minutes', 40)} min")
        with col3:
            total_hours = tp.get("total_periods", 0) * tp.get("period_duration_minutes", 40) / 60
            st.metric("Total Hours", f"{total_hours:.1f}")

        st.markdown(f"**Strategy:** {tp.get('overall_strategy', 'N/A')}")

        for period in tp.get("periods", []):
            with st.expander(f"Period {period.get('period_number', '')}: {period.get('title', '')}"):
                st.markdown(f"**Duration:** {period.get('duration_minutes', 40)} minutes")
                st.markdown("**Learning Objectives:**")
                for obj in period.get("learning_objectives", []):
                    st.markdown(f"  - {obj}")
                st.markdown("**Topics:**")
                for topic in period.get("topics_covered", []):
                    st.markdown(f"  - {topic}")
                st.markdown("**Sequence:**")
                for step in period.get("sequence", []):
                    st.markdown(f"  - {step}")
                st.markdown(f"**Methods:** {', '.join(period.get('teaching_methods', []))}")

    with tabs[3]:
        st.header("Lesson Content")

        for content in tkp.get("period_contents", []):
            with st.expander(f"Period {content.get('period_number', '')} Content", expanded=False):
                entry = content.get("entry_ticket", {})
                if entry.get("questions"):
                    st.markdown("### Entry Ticket (Warm-up)")
                    st.markdown(f"**Purpose:** *{entry.get('purpose', '')}*")
                    for q in entry["questions"]:
                        st.markdown(f"- {q}")
                    st.markdown("---")

                st.markdown("### Teacher Script")
                script = content.get("teacher_script", "")
                if script:
                    st.info(script)

                notes = content.get("blackboard_notes", [])
                if notes:
                    st.markdown("### Blackboard Notes")
                    for note in notes:
                        st.markdown(f"- {note}")

                cps = content.get("checkpoint_questions", [])
                if cps:
                    st.markdown("### Checkpoint Questions")
                    for cp in cps:
                        st.markdown(f"**Question:** {cp.get('question', '')}")
                        st.markdown(f"**Expected Answer:** {cp.get('expected_answer', '')}")
                        st.markdown(f"*Ask after:* {cp.get('when_to_ask', '')}")
                        st.markdown("")
                    st.markdown("---")

                exit_t = content.get("exit_ticket", {})
                if exit_t.get("questions"):
                    st.markdown("### Exit Ticket")
                    for q in exit_t["questions"]:
                        st.markdown(f"- {q}")
                    st.markdown("---")

                hw = content.get("homework", [])
                if hw:
                    st.markdown("### Homework")
                    for item in hw:
                        st.markdown(f"- **[{item.get('difficulty', 'General')}]** {item.get('task', '')} *({item.get('estimated_time', '')})*")
                    st.markdown("---")

                mentor = content.get("mentor_moment", {})
                if mentor.get("story"):
                    st.markdown("### Mentor Moment")
                    st.markdown(f"**Title:** {mentor.get('title', '')}")
                    st.info(mentor.get("story", ""))
                    st.caption(f"Connection to Topic: {mentor.get('connection_to_topic', '')}")

    with tabs[4]:
        st.header("Activities")

        for activity in tkp.get("activities", []):
            with st.expander(f"{activity.get('title', 'Activity')} ({activity.get('type', '')})"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Type:** {activity.get('type', '')}")
                with col2:
                    st.markdown(f"**Duration:** {activity.get('duration_minutes', '')} min")
                with col3:
                    st.markdown(f"**Period:** {activity.get('period_number', 'Any')}")

                materials = activity.get("materials_needed", [])
                if materials:
                    st.markdown(f"**Materials Needed:** {', '.join(materials)}")

                st.markdown("#### Teacher Instructions")
                st.markdown(activity.get("teacher_instructions", ""))

                st.markdown("#### Student Instructions")
                st.markdown(activity.get("student_instructions", ""))

                st.markdown(f"**Success Criteria:** {activity.get('success_criteria', '')}")
                st.markdown(f"**Differentiation Tips:** {activity.get('differentiation_tips', '')}")

    with tabs[5]:
        st.header("Assessments")
        assessments = tkp.get("assessments", {})

        st.metric("Total Marks", assessments.get("total_marks", 0))

        mcqs = assessments.get("mcqs", [])
        if mcqs:
            st.subheader(f"Multiple Choice Questions ({len(mcqs)})")
            for i, mcq in enumerate(mcqs):
                with st.expander(f"Q{i+1}. {mcq.get('question', '')[:80]}..."):
                    st.markdown(f"**Question:** {mcq.get('question', '')}")
                    for opt in mcq.get("options", []):
                        st.markdown(f"- {opt}")
                    st.success(f"**Answer:** {mcq.get('correct_answer', '')}")
                    st.markdown(f"**Explanation:** {mcq.get('explanation', '')}")
                    cit = mcq.get("source_citation", "")
                    cit_html = f" | Citation: {cit}" if cit else ""
                    st.caption(f"Difficulty: {mcq.get('difficulty', '')} | Bloom's: {mcq.get('blooms_level', '')}{cit_html}")

        short = assessments.get("short_answers", [])
        if short:
            st.subheader(f"Short Answer Questions ({len(short)})")
            for i, sa in enumerate(short):
                with st.expander(f"Q{i+1}. [{sa.get('marks', '')} marks] {sa.get('question', '')[:80]}"):
                    st.markdown(f"**Question:** {sa.get('question', '')}")
                    st.success(f"**Model Answer:** {sa.get('model_answer', '')}")
                    st.markdown(f"**Marking Scheme:** {sa.get('marking_scheme', '')}")
                    blooms = sa.get("blooms_level", "Understand")
                    cit = sa.get("source_citation", "")
                    cit_html = f" | Citation: {cit}" if cit else ""
                    st.caption(f"Bloom's Level: {blooms}{cit_html}")

        long_ans = assessments.get("long_answers", [])
        if long_ans:
            st.subheader(f"Long Answer Questions ({len(long_ans)})")
            for i, la in enumerate(long_ans):
                with st.expander(f"Q{i+1}. [{la.get('marks', '')} marks] {la.get('question', '')[:80]}"):
                    st.markdown(f"**Question:** {la.get('question', '')}")
                    st.success(f"**Model Answer:** {la.get('model_answer', '')}")
                    st.markdown(f"**Rubric:** {la.get('rubric', '')}")
                    blooms = la.get("blooms_level", "Analyze")
                    cit = la.get("source_citation", "")
                    cit_html = f" | Citation: {cit}" if cit else ""
                    st.caption(f"Bloom's Level: {blooms}{cit_html}")

        numerical = assessments.get("numerical_problems", [])
        if numerical:
            st.subheader(f"Numerical Problems ({len(numerical)})")
            for i, np_item in enumerate(numerical):
                with st.expander(f"Q{i+1}. [{np_item.get('marks', '')} marks] {np_item.get('question', '')[:80]}"):
                    st.markdown(f"**Question:** {np_item.get('question', '')}")
                    st.markdown("**Solution Steps:**")
                    for step in np_item.get("solution_steps", []):
                        st.markdown(f"  - {step}")
                    st.success(f"**Answer:** {np_item.get('final_answer', '')}")
                    blooms = np_item.get("blooms_level", "Apply")
                    cit = np_item.get("source_citation", "")
                    cit_html = f" | Citation: {cit}" if cit else ""
                    st.caption(f"Bloom's Level: {blooms}{cit_html}")

    with tabs[6]:
        st.header("Learning Gaps & Misconceptions")

        for gap in tkp.get("learning_gaps", []):
            severity = gap.get("severity", "Medium")
            
            if severity == "High":
                container = st.error
            elif severity == "Medium":
                container = st.warning
            else:
                container = st.info
                
            with st.expander(f"{severity}: {gap.get('misconception', '')[:80]}"):
                st.markdown(f"**Misconception:** {gap.get('misconception', '')}")
                st.markdown(f"**Why it happens:** {gap.get('why_it_happens', '')}")
                st.markdown(f"**Related Concept:** {gap.get('related_concept', '')}")
                
                container(f"**Diagnostic Question:** {gap.get('diagnostic_question', '')}")
                st.success(f"**Remedial Action:** {gap.get('remedial_action', '')}")

    with tabs[7]:
        st.header("Validation Report")
        validation = tkp.get("validation_report", {})

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Checks", validation.get("total_checks", 0))
        with col2:
            st.metric("Passed", validation.get("passed_checks", 0))
        with col3:
            overall = validation.get("overall_passed", False)
            st.metric("Overall", "PASSED" if overall else "FAILED")

        for result in validation.get("results", []):
            icon = "[PASS]" if result.get("passed") else "[FAIL]"
            with st.expander(f"{icon} {result.get('check_name', '')}"):
                st.markdown(f"**Result:** {'Passed' if result.get('passed') else 'Failed'}")
                st.markdown(f"**Message:** {result.get('message', '')}")
                if result.get("details"):
                    st.markdown(f"**Details:** {result.get('details', '')}")

    with tabs[8]:
        st.header("System Observability & Metrics")
        st.caption("Real-time monitoring of AI call latency, token usage, retry rates, and cost management.")

        stage_times = getattr(st.session_state, "stage_times", {})
        total_time = getattr(st.session_state, "total_time", 0)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Latency", f"{total_time:.1f} seconds")
        with col2:
            st.metric("Avg Stage Latency", f"{(total_time / max(len(stage_times), 1)):.1f}s")
        with col3:
            st.metric("Active Providers", "Groq (Primary) | Gemini (Secondary) | Nvidia (Last Option)")

        st.subheader("Stage Latency Chart")
        if stage_times:
            st.bar_chart(stage_times)
        else:
            st.info("No latency metrics available for this run.")

        st.subheader("RAGAS-Style Grounding & Faithfulness Score")
        val_report = tkp.get("validation_report", {})
        val_results = val_report.get("results", [])
        passed_count = sum(1 for r in val_results if r.get("passed"))
        total_count = max(len(val_results), 1)
        grounding_score = int((passed_count / total_count) * 100)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.metric("Faithfulness Score (RAG Grounding)", f"{grounding_score}%")
        with col_g2:
            st.progress(grounding_score / 100)
            st.caption("Factual accuracy verified against source document text chunks")

        st.subheader("Cost & Token Observability (Estimated)")
        
        raw_text_len = len(tkp.get("document_structure", {}).get("raw_text", ""))
        est_input_tokens = int(raw_text_len / 4)
        
        tkp_json_str = json.dumps(tkp)
        est_output_tokens = int(len(tkp_json_str) / 4)
        
        input_cost = (est_input_tokens / 1_000_000) * 0.59
        output_cost = (est_output_tokens / 1_000_000) * 0.79
        total_cost = input_cost + output_cost

        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.metric("Est. Input Tokens", f"{est_input_tokens:,}")
        with col_c2:
            st.metric("Est. Output Tokens", f"{est_output_tokens:,}")
        with col_c3:
            st.metric("Estimated Cost (USD)", f"${total_cost:.5f}")
            
        st.markdown("""
        Cost Control Strategy: The platform implements cost management by using free tier / low-cost high-throughput providers (Groq/Gemini/Nvidia) and rotating them automatically upon hitting RPM/TPM limits.
        """)

        st.subheader("Resilience & Retries")
        st.markdown("""
        - Failover Logic: Primary: Groq API (llama-3.3-70b-versatile) -> Fallback: Google Gemini API (gemini-1.5-flash) -> Ultimate Fallback: NVIDIA NIM API (nemotron-3-ultra-550b-a55b).
        - 429 Rate-Limit Mitigation: Automatic parsing of standard Retry-After headers and smart dynamic backing-off.
        - Validation Checks: Automated 10-stage schema checks and RAG-based grounding validation.
        """)

    with tabs[9]:
        st.header("Download")

        tkp_json = json.dumps(tkp, indent=2, ensure_ascii=False)

        st.download_button(
            label="Download Full TKP (JSON)",
            data=tkp_json,
            file_name="TeacherKnowledgePackage.json",
            mime="application/json",
            use_container_width=True
        )

        st.markdown("---")
        st.subheader("Printable Guides & Lesson Books (HTML/PDF)")
        st.caption("Open these files in any web browser and press Ctrl+P to save them as a clean, professionally formatted PDF.")

        col_ex1, col_ex2, col_ex3 = st.columns(3)

        with col_ex1:
            lp_html = generate_lesson_plan_html(tkp)
            st.download_button(
                label="Download Lesson Plan",
                data=lp_html,
                file_name="LessonPlan.html",
                mime="text/html",
                use_container_width=True
            )

        with col_ex2:
            tg_html = generate_teacher_guide_html(tkp)
            st.download_button(
                label="Download Teacher Guide",
                data=tg_html,
                file_name="TeacherGuide.html",
                mime="text/html",
                use_container_width=True
            )

        with col_ex3:
            ab_html = generate_assessment_book_html(tkp)
            st.download_button(
                label="Download Assessment Book",
                data=ab_html,
                file_name="AssessmentBook.html",
                mime="text/html",
                use_container_width=True
            )

        st.markdown("### Quick Stats")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Periods", len(tkp.get("period_contents", [])))
        with col2:
            st.metric("Activities", len(tkp.get("activities", [])))
        with col3:
            a = tkp.get("assessments", {})
            total = len(a.get("mcqs", [])) + len(a.get("short_answers", [])) + len(a.get("long_answers", [])) + len(a.get("numerical_problems", []))
            st.metric("Questions", total)
        with col4:
            st.metric("Gaps Found", len(tkp.get("learning_gaps", [])))

else:
    if not st.session_state.processing:
        st.markdown("---")
        st.markdown("### How It Works")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### Step 1: Upload")
            st.markdown("Upload any educational document — PDF, DOCX, PPT, or TXT. Our AI reads and understands the structure.")

        with col2:
            st.markdown("#### Step 2: AI Processing")
            st.markdown("10-stage AI pipeline extracts knowledge, plans lessons, generates content, activities, and assessments.")

        with col3:
            st.markdown("#### Step 3: Download")
            st.markdown("Get your complete Teacher Knowledge Package — ready to use in the classroom!")

        st.markdown("---")
        st.markdown("### What You Get")

        features = [
            ("Knowledge Extraction", "Learning objectives, concepts, definitions, formulae mapped to Bloom's Taxonomy"),
            ("Adaptive Teaching Plans", "AI determines optimal number of periods based on content complexity and grade level"),
            ("Complete Lesson Content", "Teacher scripts, blackboard notes, entry/exit tickets, homework"),
            ("Diverse Activities", "Demonstrations, experiments, role play, group discussions with materials lists"),
            ("Comprehensive Assessments", "MCQs, short/long answers, numerical problems with answer keys and rubrics"),
            ("Learning Gap Analysis", "Student misconceptions with diagnostic questions and remedial actions"),
        ]

        cols = st.columns(3)
        for i, (title, desc) in enumerate(features):
            with cols[i % 3]:
                st.markdown(f"### {title}")
                st.markdown(desc)
