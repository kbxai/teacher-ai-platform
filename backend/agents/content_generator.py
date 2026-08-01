import asyncio
import time
from backend.agents.llm_utils import call_llm
from backend.prompts.templates import CONTENT_GENERATION_PROMPT
from backend.schemas.models import (
    PeriodContent, EntryTicket, CheckpointQuestion,
    ExitTicket, HomeworkItem, MentorMoment
)


def generate_period_content(period_plan, metadata, knowledge, user_context=None):
    ctx = user_context or {}
    knowledge_context = ""
    for con in knowledge.concepts:
        knowledge_context += f"- {con.name}: {con.explanation}\n"
    for defn in knowledge.definitions:
        knowledge_context += f"- {defn.term}: {defn.definition}\n"

    prompt = CONTENT_GENERATION_PROMPT.format(
        period_number=period_plan.period_number,
        subject=metadata.subject,
        grade_level=metadata.grade_level,
        topic=metadata.topic,
        period_title=period_plan.title,
        period_objectives=", ".join(period_plan.learning_objectives),
        period_topics=", ".join(period_plan.topics_covered),
        period_sequence=", ".join(period_plan.sequence),
        knowledge_context=knowledge_context[:3000],
        teaching_style=ctx.get("teaching_style", "Balanced")
    )

    if metadata.language and metadata.language.lower() != "english":
        prompt += f"\n\nIMPORTANT: Generate the entry/exit tickets, teacher script, blackboard notes, activities, checkpoint questions, homework, and mentor stories in {metadata.language}."

    result = call_llm(prompt, max_tokens=8000)

    if not result:
        return PeriodContent(period_number=period_plan.period_number)

    entry = result.get("entry_ticket", {})
    exit_t = result.get("exit_ticket", {})
    mentor = result.get("mentor_moment", {})

    checkpoints = []
    for cp in result.get("checkpoint_questions", []):
        checkpoints.append(CheckpointQuestion(
            question=cp.get("question", ""),
            expected_answer=cp.get("expected_answer", ""),
            when_to_ask=cp.get("when_to_ask", "")
        ))

    homework = []
    for hw in result.get("homework", []):
        homework.append(HomeworkItem(
            task=hw.get("task", ""),
            difficulty=hw.get("difficulty", "Medium"),
            estimated_time=hw.get("estimated_time", "15 minutes")
        ))

    t_script = result.get("teacher_script", "")
    if isinstance(t_script, list):
        t_script = "\n\n".join(str(s) for s in t_script)
    else:
        t_script = str(t_script)

    b_notes = result.get("blackboard_notes", [])
    if isinstance(b_notes, str):
        b_notes = [b_notes]
    elif not isinstance(b_notes, list):
        b_notes = []

    c_activities = result.get("classroom_activities", [])
    if isinstance(c_activities, str):
        c_activities = [c_activities]
    elif not isinstance(c_activities, list):
        c_activities = []

    return PeriodContent(
        period_number=period_plan.period_number,
        entry_ticket=EntryTicket(
            questions=entry.get("questions", []),
            purpose=entry.get("purpose", "")
        ),
        teacher_script=t_script,
        blackboard_notes=b_notes,
        classroom_activities=c_activities,
        checkpoint_questions=checkpoints,
        exit_ticket=ExitTicket(
            questions=exit_t.get("questions", []),
            success_criteria=exit_t.get("success_criteria", "")
        ),
        homework=homework,
        mentor_moment=MentorMoment(
            title=mentor.get("title", ""),
            story=mentor.get("story", ""),
            connection_to_topic=mentor.get("connection_to_topic", "")
        )
    )


async def generate_period_content_async(period_plan, metadata, knowledge, user_context=None):
    return await asyncio.to_thread(generate_period_content, period_plan, metadata, knowledge, user_context)


async def generate_all_period_contents_async(teaching_plan, metadata, knowledge, user_context=None):
    sem = asyncio.Semaphore(2)

    async def run_with_sem(period):
        async with sem:
            res = await generate_period_content_async(period, metadata, knowledge, user_context)
            await asyncio.sleep(2.0)
            return res

    tasks = [run_with_sem(p) for p in teaching_plan.periods]
    return await asyncio.gather(*tasks)
