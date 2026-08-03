# This file defines all the Pydantic data schemas used to validate inputs and outputs across the AI pipeline.

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class Section(BaseModel):
    heading: str = ""
    content: str = ""
    level: int = 0
    page_number: int = 0


class TableData(BaseModel):
    title: str = ""
    headers: list[str] = []
    rows: list[list[str]] = []


class DocumentStructure(BaseModel):
    filename: str = ""
    file_type: str = ""
    total_pages: int = 0
    word_count: int = 0
    detected_language: str = "English"
    raw_text: str = ""
    sections: list[Section] = []
    tables: list[TableData] = []
    equations: list[str] = []
    figures: list[str] = []
    metadata: dict = {}


class EducationalMetadata(BaseModel):
    subject: str = ""
    grade_level: str = ""
    difficulty: str = ""
    topic: str = ""
    chapter: str = ""
    category: str = ""
    language: str = "English"
    board_alignment: str = ""
    estimated_teaching_hours: float = 0
    summary: str = ""


class LearningObjective(BaseModel):
    objective: str = ""
    blooms_level: str = ""
    keywords: list[str] = []
    source_citation: str = ""


class Concept(BaseModel):
    name: str = ""
    definition: str = ""
    explanation: str = ""
    related_concepts: list[str] = []
    source_citation: str = ""


class Definition(BaseModel):
    term: str = ""
    definition: str = ""

class Formula(BaseModel):
    name: str = ""
    formula: str = ""
    variables: str = ""

class Example(BaseModel):
    title: str = ""
    description: str = ""

class Misconception(BaseModel):
    misconception: str = ""
    correction: str = ""

class KnowledgeGraph(BaseModel):
    learning_objectives: list[LearningObjective] = []
    prerequisites: list[str] = []
    concepts: list[Concept] = []
    definitions: list[Definition] = []
    formulae: list[Formula] = []
    keywords: list[str] = []
    examples: list[Example] = []
    applications: list[str] = []
    common_misconceptions: list[Misconception] = []


class PeriodPlan(BaseModel):
    period_number: int = 0
    title: str = ""
    duration_minutes: int = 40
    learning_objectives: list[str] = []
    topics_covered: list[str] = []
    sequence: list[str] = []
    teaching_methods: list[str] = []


class TeachingPlan(BaseModel):
    total_periods: int = 0
    period_duration_minutes: int = 40
    overall_strategy: str = ""
    pedagogical_rationale: str = ""
    periods: list[PeriodPlan] = []


class EntryTicket(BaseModel):
    questions: list[str] = []
    purpose: str = ""


class CheckpointQuestion(BaseModel):
    question: str = ""
    expected_answer: str = ""
    when_to_ask: str = ""


class ExitTicket(BaseModel):
    questions: list[str] = []
    success_criteria: str = ""


class HomeworkItem(BaseModel):
    task: str = ""
    difficulty: str = ""
    estimated_time: str = ""


class MentorMoment(BaseModel):
    title: str = ""
    story: str = ""
    connection_to_topic: str = ""


class PeriodContent(BaseModel):
    period_number: int = 0
    entry_ticket: EntryTicket = EntryTicket()
    teacher_script: str = ""
    blackboard_notes: list[str] = []
    classroom_activities: list[str] = []
    checkpoint_questions: list[CheckpointQuestion] = []
    exit_ticket: ExitTicket = ExitTicket()
    homework: list[HomeworkItem] = []
    mentor_moment: MentorMoment = MentorMoment()


class Activity(BaseModel):
    type: str = ""
    title: str = ""
    duration_minutes: int = 0
    materials_needed: list[str] = []
    teacher_instructions: str = ""
    student_instructions: str = ""
    success_criteria: str = ""
    scaffold: str = ""
    extension: str = ""
    period_number: int = 0


class MCQ(BaseModel):
    question: str = ""
    options: list[str] = []
    correct_answer: str = ""
    explanation: str = ""
    why_wrong: list[str] = []
    difficulty: str = ""
    blooms_level: str = ""
    source_citation: str = ""


class ShortAnswer(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    question: str = ""
    model_answer: str = ""
    marks: int = 0
    marking_scheme: str = ""
    blooms_level: str = ""
    source_citation: str = ""


class LongAnswer(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    question: str = ""
    model_answer: str = ""
    marks: int = 0
    rubric: str = ""
    blooms_level: str = ""
    source_citation: str = ""


class NumericalProblem(BaseModel):
    question: str = ""
    solution_steps: list[str] = []
    final_answer: str = ""
    marks: int = 0
    blooms_level: str = ""
    source_citation: str = ""


class AssessmentPackage(BaseModel):
    mcqs: list[MCQ] = []
    short_answers: list[ShortAnswer] = []
    long_answers: list[LongAnswer] = []
    numerical_problems: list[NumericalProblem] = []
    total_marks: int = 0


class LearningGap(BaseModel):
    misconception: str = ""
    why_it_happens: str = ""
    cognitive_friction: str = ""
    diagnostic_question: str = ""
    socratic_question: str = ""
    severity: str = ""
    remedial_action: str = ""
    related_concept: str = ""


class ValidationResult(BaseModel):
    check_name: str = ""
    passed: bool = False
    message: str = ""
    details: str = ""


class ValidationReport(BaseModel):
    overall_passed: bool = False
    total_checks: int = 0
    passed_checks: int = 0
    results: list[ValidationResult] = []
    timestamp: str = ""


class TeacherKnowledgePackage(BaseModel):
    version: str = "1.0"
    generated_at: str = ""
    source_document: str = ""
    document_structure: DocumentStructure = DocumentStructure()
    educational_metadata: EducationalMetadata = EducationalMetadata()
    knowledge_graph: KnowledgeGraph = KnowledgeGraph()
    teaching_plan: TeachingPlan = TeachingPlan()
    period_contents: list[PeriodContent] = []
    activities: list[Activity] = []
    assessments: AssessmentPackage = AssessmentPackage()
    learning_gaps: list[LearningGap] = []
    validation_report: ValidationReport = ValidationReport()
    pipeline_metadata: dict = {}
