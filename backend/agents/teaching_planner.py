from backend.agents.llm_utils import call_llm
from backend.prompts.templates import TEACHING_PLANNER_PROMPT
from backend.schemas.models import TeachingPlan, PeriodPlan


def create_teaching_plan(metadata, knowledge, user_context=None):
    ctx = user_context or {}

    objectives_text = "\n".join(
        [f"- {obj.objective} (Bloom's: {obj.blooms_level})"
         for obj in knowledge.learning_objectives]
    )

    concepts_text = "\n".join(
        [f"- {con.name}: {con.definition}"
         for con in knowledge.concepts]
    )

    max_periods = ctx.get("max_periods", 0)
    try:
        max_periods = int(max_periods)
    except Exception:
        max_periods = 0

    teaching_style = str(ctx.get("teaching_style", "Balanced"))

    prompt = TEACHING_PLANNER_PROMPT.format(
        subject=metadata.subject,
        grade_level=metadata.grade_level,
        topic=metadata.topic,
        difficulty=metadata.difficulty,
        estimated_hours=metadata.estimated_teaching_hours,
        learning_objectives=objectives_text,
        concepts=concepts_text,
        teaching_style=teaching_style,
        max_periods_hint=f"The teacher has {max_periods} periods available." if max_periods > 0 else "Determine the optimal number of periods based on content complexity."
    )

    if metadata.language and metadata.language.lower() != "english":
        prompt += f"\n\nIMPORTANT: Generate the overall strategy, period titles, sequencing steps, and teaching methods in {metadata.language}."

    result = call_llm(prompt)

    if not result:
        return TeachingPlan(total_periods=1, periods=[
            PeriodPlan(period_number=1, title=metadata.topic, learning_objectives=[
                obj.objective for obj in knowledge.learning_objectives
            ])
        ])

    period_limit = max_periods if max_periods > 0 else 8
    periods = []
    for p in result.get("periods", [])[:period_limit]:
        periods.append(PeriodPlan(
            period_number=p.get("period_number", 0),
            title=p.get("title", ""),
            duration_minutes=p.get("duration_minutes", 40),
            learning_objectives=p.get("learning_objectives", []),
            topics_covered=p.get("topics_covered", []),
            sequence=p.get("sequence", []),
            teaching_methods=p.get("teaching_methods", [])
        ))

    return TeachingPlan(
        total_periods=len(periods),
        period_duration_minutes=result.get("period_duration_minutes", 40),
        overall_strategy=result.get("overall_strategy", ""),
        periods=periods
    )
