from backend.agents.llm_utils import call_llm
from backend.prompts.templates import CLASSIFICATION_PROMPT
from backend.schemas.models import EducationalMetadata


def classify_document(document_structure, user_context=None):
    ctx = user_context or {}
    text = document_structure.raw_text[:8000]

    prompt = CLASSIFICATION_PROMPT.format(document_text=text)

    if ctx.get("grade_level"):
        prompt += f"\n\nHINT: The teacher indicated this is for {ctx['grade_level']}."
    if ctx.get("subject_hint"):
        prompt += f"\nHINT: The teacher indicated the subject is {ctx['subject_hint']}."

    result = call_llm(prompt)

    if not result:
        return EducationalMetadata(
            subject=ctx.get("subject_hint", "General"),
            grade_level=ctx.get("grade_level", ""),
            topic=document_structure.filename,
            summary="Could not classify document"
        )

    grade = result.get("grade_level", "")
    if ctx.get("grade_level") and not grade:
        grade = ctx["grade_level"]

    subject = result.get("subject", "General")
    if ctx.get("subject_hint") and subject == "General":
        subject = ctx["subject_hint"]

    board = ctx.get("curriculum_alignment", "General")
    if board == "General" or not board:
        board = result.get("board_alignment", "General")

    lang = ctx.get("target_language", "English")
    if not lang or lang == "English":
        lang = result.get("language", "English")

    return EducationalMetadata(
        subject=subject,
        grade_level=grade,
        difficulty=result.get("difficulty", "Medium"),
        topic=result.get("topic", ""),
        chapter=result.get("chapter", ""),
        category=result.get("category", ""),
        language=lang,
        board_alignment=board,
        estimated_teaching_hours=result.get("estimated_teaching_hours", 2),
        summary=result.get("summary", "")
    )
