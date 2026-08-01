from backend.agents.llm_utils import call_llm
from backend.prompts.templates import ASSESSMENT_GENERATION_PROMPT
from backend.schemas.models import (
    AssessmentPackage, MCQ, ShortAnswer, LongAnswer, NumericalProblem
)


def generate_assessments(metadata, knowledge):
    objectives_text = "\n".join(
        [f"- {obj.objective} (Bloom's: {obj.blooms_level})"
         for obj in knowledge.learning_objectives]
    )

    concepts_text = "\n".join(
        [f"- {con.name}: {con.definition}" for con in knowledge.concepts]
    )

    prompt = ASSESSMENT_GENERATION_PROMPT.format(
        subject=metadata.subject,
        grade_level=metadata.grade_level,
        topic=metadata.topic,
        difficulty=metadata.difficulty,
        learning_objectives=objectives_text,
        concepts=concepts_text
    )

    if metadata.language and metadata.language.lower() != "english":
        prompt += f"\n\nIMPORTANT: Generate all questions, options, explanations, and model answers in {metadata.language}."

    result = call_llm(prompt, max_tokens=8000)

    if not result:
        return AssessmentPackage()

    mcqs = []
    for m in result.get("mcqs", []):
        opts = m.get("options", [])
        if isinstance(opts, str):
            opts = [opts]
        elif not isinstance(opts, list):
            opts = []

        ww = m.get("why_wrong", [])
        if isinstance(ww, str):
            ww = [ww]
        elif not isinstance(ww, list):
            ww = []

        mcqs.append(MCQ(
            question=str(m.get("question", "")),
            options=[str(o) for o in opts],
            correct_answer=str(m.get("correct_answer", "")),
            explanation=str(m.get("explanation", "")),
            why_wrong=[str(w) for w in ww],
            difficulty=str(m.get("difficulty", "Medium")),
            blooms_level=str(m.get("blooms_level", "Remember")),
            source_citation=str(m.get("source_citation", ""))
        ))

    short_answers = []
    for sa in result.get("short_answers", []):
        short_answers.append(ShortAnswer(
            question=str(sa.get("question", "")),
            model_answer=str(sa.get("model_answer", "")),
            marks=int(sa.get("marks", 3)) if isinstance(sa.get("marks"), (int, float, str)) and str(sa.get("marks")).isdigit() else 3,
            marking_scheme=str(sa.get("marking_scheme", "")),
            blooms_level=str(sa.get("blooms_level", "Understand")),
            source_citation=str(sa.get("source_citation", ""))
        ))

    long_answers = []
    for la in result.get("long_answers", []):
        rubric_val = la.get("rubric", "")
        if isinstance(rubric_val, list):
            rubric_val = "\n".join(str(r) for r in rubric_val)
        else:
            rubric_val = str(rubric_val)

        long_answers.append(LongAnswer(
            question=str(la.get("question", "")),
            model_answer=str(la.get("model_answer", "")),
            marks=int(la.get("marks", 5)) if isinstance(la.get("marks"), (int, float, str)) and str(la.get("marks")).isdigit() else 5,
            rubric=rubric_val,
            blooms_level=str(la.get("blooms_level", "Analyze")),
            source_citation=str(la.get("source_citation", ""))
        ))

    numerical = []
    for np_item in result.get("numerical_problems", []):
        steps = np_item.get("solution_steps", [])
        if isinstance(steps, str):
            steps = [steps]
        elif not isinstance(steps, list):
            steps = []

        numerical.append(NumericalProblem(
            question=str(np_item.get("question", "")),
            solution_steps=[str(s) for s in steps],
            final_answer=str(np_item.get("final_answer", "")),
            marks=int(np_item.get("marks", 4)) if isinstance(np_item.get("marks"), (int, float, str)) and str(np_item.get("marks")).isdigit() else 4,
            blooms_level=str(np_item.get("blooms_level", "Apply")),
            source_citation=str(np_item.get("source_citation", ""))
        ))

    total_m = result.get("total_marks", 0)
    if not isinstance(total_m, int):
        try:
            total_m = int(total_m)
        except Exception:
            total_m = 0

    return AssessmentPackage(
        mcqs=mcqs,
        short_answers=short_answers,
        long_answers=long_answers,
        numerical_problems=numerical,
        total_marks=total_m
    )
