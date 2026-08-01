from backend.agents.llm_utils import call_llm
from backend.prompts.templates import KNOWLEDGE_EXTRACTION_PROMPT
from backend.schemas.models import (
    KnowledgeGraph, LearningObjective, Concept,
    Definition, Formula, Example, Misconception
)


def extract_knowledge(document_structure, metadata):
    text = document_structure.raw_text[:100000]

    prompt = KNOWLEDGE_EXTRACTION_PROMPT.format(
        subject=metadata.subject,
        grade_level=metadata.grade_level,
        topic=metadata.topic,
        document_text=text
    )

    if metadata.language and metadata.language.lower() != "english":
        prompt += f"\n\nIMPORTANT: Generate all JSON values, text descriptions, explanations, and definitions in {metadata.language}."

    result = call_llm(prompt, max_tokens=8000)

    if not result:
        return KnowledgeGraph()

    objectives = []
    for obj in result.get("learning_objectives", []):
        objectives.append(LearningObjective(
            objective=obj.get("objective", ""),
            blooms_level=obj.get("blooms_level", "Understand"),
            keywords=obj.get("keywords", []),
            source_citation=obj.get("source_citation", "")
        ))

    concepts = []
    for con in result.get("concepts", []):
        concepts.append(Concept(
            name=con.get("name", ""),
            definition=con.get("definition", ""),
            explanation=con.get("explanation", ""),
            related_concepts=con.get("related_concepts", []),
            source_citation=con.get("source_citation", "")
        ))

    definitions = []
    for d in result.get("definitions", []):
        definitions.append(Definition(
            term=d.get("term", ""),
            definition=d.get("definition", "")
        ))

    formulae = []
    for f in result.get("formulae", []):
        formulae.append(Formula(
            name=f.get("name", ""),
            formula=f.get("formula", ""),
            variables=f.get("variables", "")
        ))

    examples = []
    for e in result.get("examples", []):
        examples.append(Example(
            title=e.get("title", ""),
            description=e.get("description", "")
        ))

    misconceptions = []
    for m in result.get("common_misconceptions", []):
        misconceptions.append(Misconception(
            misconception=m.get("misconception", ""),
            correction=m.get("correction", "")
        ))

    return KnowledgeGraph(
        learning_objectives=objectives,
        prerequisites=result.get("prerequisites", []),
        concepts=concepts,
        definitions=definitions,
        formulae=formulae,
        keywords=result.get("keywords", []),
        examples=examples,
        applications=result.get("applications", []),
        common_misconceptions=misconceptions
    )
