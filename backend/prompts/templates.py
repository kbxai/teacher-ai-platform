CLASSIFICATION_PROMPT = """You are an expert educational content analyst. Analyze the following document text and classify it.

DOCUMENT TEXT:
{document_text}

Return a JSON object with these fields:
{{
    "subject": "the academic subject (e.g., Physics, History, Mathematics, Biology)",
    "grade_level": "target grade level (e.g., Class 6, Class 9, Class 11, College)",
    "difficulty": "Easy, Medium, or Hard",
    "topic": "specific topic name",
    "chapter": "chapter name if identifiable, else same as topic",
    "category": "STEM, Humanities, Social Science, Language, Arts, or Commerce",
    "language": "language of the document",
    "board_alignment": "CBSE, ICSE, Common Core, IB, or General",
    "estimated_teaching_hours": estimated number of hours to teach this content (a number),
    "summary": "a 2-3 sentence summary of what this document covers"
}}

Return ONLY the JSON object, no extra text."""


KNOWLEDGE_EXTRACTION_PROMPT = """You are an expert curriculum designer. Extract structured educational knowledge from this document.

SUBJECT: {subject}
GRADE: {grade_level}
TOPIC: {topic}

DOCUMENT TEXT:
{document_text}

Return a JSON object with:
{{
    "learning_objectives": [
        {{
            "objective": "what the student should be able to do after learning",
            "blooms_level": "Remember, Understand, Apply, Analyze, Evaluate, or Create",
            "keywords": ["key action verbs"],
            "source_citation": "specific section header, page number, or text snippet from the document where this objective is grounded"
        }}
    ],
    "prerequisites": ["list of things students should already know"],
    "concepts": [
        {{
            "name": "concept name",
            "definition": "clear definition",
            "explanation": "detailed explanation in simple language",
            "related_concepts": ["related topic names"],
            "source_citation": "specific section header, page number, or text snippet from the document where this concept is grounded"
        }}
    ],
    "definitions": [
        {{"term": "word", "definition": "meaning"}}
    ],
    "formulae": [
        {{"name": "formula name", "formula": "the formula", "variables": "what each variable means"}}
    ],
    "keywords": ["important terms from the document"],
    "examples": [
        {{"title": "example title", "description": "the example explained"}}
    ],
    "applications": ["real-world applications of these concepts"],
    "common_misconceptions": [
        {{"misconception": "what students wrongly believe", "correction": "the correct understanding"}}
    ]
}}

IMPORTANT: Only extract knowledge that is explicitly present in the document. Do NOT add facts or concepts not found in the source text.
Extract at least 5 learning objectives, 5 concepts, and 3 examples. Be thorough.
Return ONLY the JSON object."""


TEACHING_PLANNER_PROMPT = """Act as a Master Educator and Curriculum Architect with 20 years of experience in differentiated instruction, Bloom's Taxonomy, and inquiry-based learning. Your task is to create a detailed, highly effective multi-period teaching plan.

SUBJECT: {subject}
GRADE: {grade_level}
TOPIC: {topic}
DIFFICULTY: {difficulty}
ESTIMATED HOURS: {estimated_hours}
TEACHING STYLE PREFERENCE: {teaching_style}
PERIOD CONSTRAINT: {max_periods_hint}

LEARNING OBJECTIVES:
{learning_objectives}

CONCEPTS TO COVER:
{concepts}

INSTRUCTIONS:
- Determine the optimal number of periods based on content volume, conceptual complexity, learning objectives, and grade level.
- Each period can be 30 to 50 minutes long.
- Use a Bloom's Taxonomy progression: The sequence MUST move from lower-order thinking (Remember/Understand) in early periods to higher-order thinking (Evaluate/Create) in later periods.
- Consider the teaching style preference when designing the plan. If a 5E Model is requested, strictly align the sequence to Engage, Explore, Explain, Elaborate, Evaluate.

Return a JSON object:
{{
    "total_periods": number of periods determined,
    "period_duration_minutes": average duration per period,
    "pedagogical_rationale": "Chain-of-thought: Before listing the periods, explain your logical reasoning for sequencing the concepts this way based on cognitive load and the chosen teaching style.",
    "overall_strategy": "brief description of the teaching approach",
    "periods": [
        {{
            "period_number": 1,
            "title": "descriptive title for this period",
            "duration_minutes": duration based on content needs,
            "learning_objectives": ["objectives covered in this period"],
            "topics_covered": ["concepts/topics taught"],
            "sequence": ["step 1: ...", "step 2: ...", "step 3: ..."],
            "teaching_methods": ["lecture", "discussion", "activity", etc.]
        }}
    ]
}}

Make sure every learning objective is covered across the periods.
Return ONLY the JSON object."""


CONTENT_GENERATION_PROMPT = """Act as a Master Teacher creating detailed, highly engaging classroom content for Period {period_number}.

SUBJECT: {subject} | GRADE: {grade_level} | TOPIC: {topic}
TEACHING STYLE: {teaching_style}

PERIOD PLAN:
Title: {period_title}
Objectives: {period_objectives}
Topics: {period_topics}
Sequence: {period_sequence}

FULL KNOWLEDGE CONTEXT (from source document):
{knowledge_context}

IMPORTANT GROUNDING RULE: All factual content, definitions, formulae, and examples MUST come from the source document above. You may add teaching strategies, analogies, and classroom activities, but do NOT introduce new subject matter facts not present in the source.

Generate complete teaching content for this period. Return a JSON object:
{{
    "period_number": {period_number},
    "entry_ticket": {{
        "questions": ["2-3 highly engaging warm-up questions that spark curiosity"],
        "purpose": "why these questions effectively hook the students"
    }},
    "teacher_script": "A detailed script of what the teacher should say. FORMAT REQUIREMENT: Format like a screenplay. Use [Brackets] for stage directions and pacing (e.g., [Wait 5 seconds], [Write 'X' on board]). Use **bold text** for key terms. Include specific 'Turn and Talk' prompts to keep students engaged. At least 300 words.",
    "blackboard_notes": ["key point 1 to write on board", "key point 2", "key point 3", "..."],
    "classroom_activities": ["activity 1 description", "activity 2 description"],
    "checkpoint_questions": [
        {{
            "question": "a specific question to check understanding mid-lesson",
            "expected_answer": "what students should answer",
            "when_to_ask": "exact moment in the script to ask this"
        }}
    ],
    "exit_ticket": {{
        "questions": ["2-3 questions to definitively assess if objectives were met"],
        "success_criteria": "what a correct, passing response looks like"
    }},
    "homework": [
        {{
            "task": "homework assignment description",
            "difficulty": "Easy, Medium, or Hard",
            "estimated_time": "15 minutes"
        }}
    ],
    "mentor_moment": {{
        "title": "an inspiring title",
        "story": "A motivational anecdote or story related to this topic. Ensure the figures you choose reflect diverse backgrounds (gender, ethnicity, culture) to promote inclusive education. Make it highly engaging.",
        "connection_to_topic": "how this story practically connects to what they learned today"
    }}
}}

Make the content engaging, pedagogically sound, and age-appropriate for {grade_level}.
Return ONLY the JSON object."""


ACTIVITY_GENERATION_PROMPT = """Act as an Expert Interactive Learning Designer specializing in Universal Design for Learning (UDL). Create diverse, highly engaging classroom activities.

SUBJECT: {subject} | GRADE: {grade_level} | TOPIC: {topic}

CONCEPTS:
{concepts}

TEACHING PLAN SUMMARY:
{teaching_plan_summary}

Design 5-8 varied activities. Include at least 3 different types from: Demonstration, Role Play, Experiment, Group Discussion, Think-Pair-Share, Debate, Case Study, Problem Solving, Jigsaw, Gallery Walk, Simulation.

Return a JSON object:
{{
    "activities": [
        {{
            "type": "activity type",
            "title": "catchy activity title",
            "duration_minutes": 15,
            "materials_needed": ["list of materials"],
            "teacher_instructions": "step-by-step instructions for the teacher",
            "student_instructions": "clear instructions for students",
            "success_criteria": "how to know the activity worked",
            "scaffold": "Specific differentiation strategy to simplify this activity for struggling learners (e.g., providing a graphic organizer, sentence starters).",
            "extension": "Specific differentiation strategy to increase the rigor for advanced learners.",
            "period_number": which period this fits best in
        }}
    ]
}}

Return ONLY the JSON object."""


ASSESSMENT_GENERATION_PROMPT = """Act as an Expert Assessment Designer who specializes in psychometrics and educational testing. Create a rigorous, comprehensive assessment package.

SUBJECT: {subject} | GRADE: {grade_level} | TOPIC: {topic} | DIFFICULTY: {difficulty}

LEARNING OBJECTIVES:
{learning_objectives}

CONCEPTS:
{concepts}

IMPORTANT: All assessment questions must be answerable using ONLY the concepts and information from the source document. Do not test knowledge beyond the scope of the provided content.

Create assessments covering ALL learning objectives. Return a JSON object:
{{
    "mcqs": [
        {{
            "question": "question text",
            "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
            "correct_answer": "A",
            "explanation": "why the correct answer is right",
            "why_wrong": ["why option B is wrong", "why C is wrong", "why D is wrong"],
            "difficulty": "Easy/Medium/Hard",
            "blooms_level": "Remember/Understand/Apply/Analyze",
            "source_citation": "specific section header, page number, or text snippet from the document where this question's fact is verified"
        }}
    ],
    "short_answers": [
        {{
            "question": "question requiring 2-3 sentence answer",
            "model_answer": "the ideal answer",
            "marks": 3,
            "marking_scheme": "1 mark for X, 1 mark for Y, 1 mark for Z",
            "blooms_level": "Remember/Understand/Apply/Analyze/Evaluate",
            "source_citation": "specific section header, page number, or text snippet from the document where this question's fact is verified"
        }}
    ],
    "long_answers": [
        {{
            "question": "question requiring detailed answer",
            "model_answer": "comprehensive model answer",
            "marks": 5,
            "rubric": "detailed rubric for grading",
            "blooms_level": "Remember/Understand/Apply/Analyze/Evaluate",
            "source_citation": "specific section header, page number, or text snippet from the document where this question's fact is verified"
        }}
    ],
    "numerical_problems": [
        {{
            "question": "problem statement with numbers",
            "solution_steps": ["step 1: ...", "step 2: ...", "step 3: ..."],
            "final_answer": "the answer with units",
            "marks": 4,
            "blooms_level": "Remember/Understand/Apply/Analyze/Evaluate",
            "source_citation": "specific section header, page number, or text snippet from the document where this question's fact is verified"
        }}
    ],
    "total_marks": sum of all marks
}}

Generate at least: 10 MCQs (mix of difficulties), 4 short answers, 2 long answers, and 3 numerical problems (if STEM subject, else skip numerical).
Return ONLY the JSON object."""


GAP_ANALYSIS_PROMPT = """Act as an Expert Educational Psychologist specializing in cognitive friction and conceptual scaffolding. Analyze potential student learning gaps.

SUBJECT: {subject} | GRADE: {grade_level} | TOPIC: {topic}

CONCEPTS:
{concepts}

COMMON MISCONCEPTIONS FROM DOCUMENT:
{misconceptions}

Identify 5-8 learning gaps students commonly have with this topic. Return a JSON object:
{{
    "learning_gaps": [
        {{
            "misconception": "what students commonly get wrong",
            "why_it_happens": "psychological or conceptual reason for this gap",
            "cognitive_friction": "the specific point in the learning process where their understanding breaks down",
            "diagnostic_question": "a question that reveals if a student has this misconception",
            "socratic_question": "a probing question you can ask the student to help them self-correct without just giving them the answer",
            "severity": "Low, Medium, High",
            "remedial_action": "actionable step for the teacher to correct it",
            "related_concept": "which concept this relates to"
        }}
    ]
}}

Return ONLY the JSON object."""
