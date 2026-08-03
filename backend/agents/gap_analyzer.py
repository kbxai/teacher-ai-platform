# This file analyzes student misconceptions and generates diagnostic questions and remedial actions.

from backend.agents.llm_utils import call_llm
from backend.prompts.templates import GAP_ANALYSIS_PROMPT
from backend.schemas.models import LearningGap


# This function prompts LLM to analyze cognitive friction and return a list of LearningGap models.
def analyze_learning_gaps(metadata, knowledge):
    concepts_text = "\n".join(
        [f"- {con.name}: {con.explanation}" for con in knowledge.concepts]
    )

    misconceptions_text = "\n".join(
        [f"- {m.misconception}: {m.correction}"
         for m in knowledge.common_misconceptions]
    )

    prompt = GAP_ANALYSIS_PROMPT.format(
        subject=metadata.subject,
        grade_level=metadata.grade_level,
        topic=metadata.topic,
        concepts=concepts_text,
        misconceptions=misconceptions_text if misconceptions_text else "None found in document"
    )

    if metadata.language and metadata.language.lower() != "english":
        prompt += f"\n\nIMPORTANT: Generate all misconceptions, diagnostic questions, explanations, and remedial actions in {metadata.language}."

    result = call_llm(prompt)

    if not result:
        return []

    gaps = []
    for gap in result.get("learning_gaps", []):
        gaps.append(LearningGap(
            misconception=str(gap.get("misconception", "")),
            why_it_happens=str(gap.get("why_it_happens", "")),
            cognitive_friction=str(gap.get("cognitive_friction", "")),
            diagnostic_question=str(gap.get("diagnostic_question", "")),
            socratic_question=str(gap.get("socratic_question", "")),
            severity=str(gap.get("severity", "Medium")),
            remedial_action=str(gap.get("remedial_action", "")),
            related_concept=str(gap.get("related_concept", ""))
        ))

    return gaps
