# This file generates classroom activities, experiments, and exercises mapped to the teaching plan.

from backend.agents.llm_utils import call_llm
from backend.prompts.templates import ACTIVITY_GENERATION_PROMPT
from backend.schemas.models import Activity


# This function prompts LLM to generate a list of interactive classroom activities.
def generate_activities(metadata, knowledge, teaching_plan):
    concepts_text = "\n".join(
        [f"- {con.name}: {con.definition}" for con in knowledge.concepts]
    )

    plan_summary = "\n".join(
        [f"Period {p.period_number}: {p.title} - Topics: {', '.join(p.topics_covered)}"
         for p in teaching_plan.periods]
    )

    prompt = ACTIVITY_GENERATION_PROMPT.format(
        subject=metadata.subject,
        grade_level=metadata.grade_level,
        topic=metadata.topic,
        concepts=concepts_text,
        teaching_plan_summary=plan_summary
    )

    if metadata.language and metadata.language.lower() != "english":
        prompt += f"\n\nIMPORTANT: Generate the activity title, teacher instructions, student instructions, and success criteria in {metadata.language}."

    result = call_llm(prompt)

    if not result:
        return []

    activities = []
    for act in result.get("activities", []):
        activities.append(Activity(
            type=act.get("type", ""),
            title=act.get("title", ""),
            duration_minutes=act.get("duration_minutes", 15),
            materials_needed=act.get("materials_needed", []),
            teacher_instructions=act.get("teacher_instructions", ""),
            student_instructions=act.get("student_instructions", ""),
            success_criteria=act.get("success_criteria", ""),
            scaffold=act.get("scaffold", ""),
            extension=act.get("extension", ""),
            period_number=act.get("period_number", 0)
        ))

    return activities
