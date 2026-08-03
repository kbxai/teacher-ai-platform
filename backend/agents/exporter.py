# This file renders TKP JSON data into print-optimized HTML documents for lesson plans, teacher guides, and assessment books.

COMMON_CSS = """
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    body {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        line-height: 1.6;
        color: #1e293b;
        max-width: 900px;
        margin: 0 auto;
        padding: 40px 20px;
        background-color: #fafafa;
    }
    h1, h2, h3, h4 {
        color: #0f172a;
        font-weight: 700;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
    }
    h1 {
        font-size: 2.5rem;
        border-bottom: 3px solid #3b82f6;
        padding-bottom: 12px;
        margin-top: 0;
    }
    h2 {
        font-size: 1.75rem;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 8px;
        color: #1e3a8a;
    }
    h3 {
        font-size: 1.35rem;
        color: #2563eb;
    }
    p, li {
        font-size: 1.05rem;
        color: #334155;
    }
    ul, ol {
        padding-left: 24px;
        margin-bottom: 1.25rem;
    }
    li {
        margin-bottom: 0.5rem;
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        background: #eff6ff;
        color: #2563eb;
        border-radius: 6px;
        font-size: 0.85em;
        font-weight: 600;
        border: 1px solid #bfdbfe;
    }
    .meta-box {
        background: #ffffff;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 30px;
        border: 1px solid #e2e8f0;
        border-left: 6px solid #2563eb;
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .meta-item {
        flex: 1 1 200px;
        font-size: 1rem;
    }
    .period-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        page-break-inside: avoid;
    }
    .script-box {
        background: #fffbeb;
        border-left: 6px solid #d97706;
        padding: 18px;
        margin: 20px 0;
        border-radius: 0 8px 8px 0;
        font-style: italic;
        white-space: pre-line;
        color: #78350f;
        box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.02);
    }
    .notes-box {
        background: #f8fafc;
        border-left: 6px solid #475569;
        padding: 18px;
        border-radius: 0 8px 8px 0;
        margin: 20px 0;
        color: #334155;
    }
    .concept-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px -1px rgba(0,0,0,0.03);
        page-break-inside: avoid;
    }
    .activity-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 6px solid #16a34a;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        color: #14532d;
        page-break-inside: avoid;
    }
    .activity-card h4 {
        color: #166534;
        margin-top: 0;
    }
    .activity-card p {
        color: #14532d;
    }
    .gap-card {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-left: 6px solid #dc2626;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        color: #7f1d1d;
        page-break-inside: avoid;
    }
    .gap-card h4 {
        color: #991b1b;
        margin-top: 0;
    }
    .gap-card p {
        color: #7f1d1d;
    }
    .question-item {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 2px 4px -1px rgba(0,0,0,0.03);
        page-break-inside: avoid;
    }
    .options-list {
        list-style-type: none;
        padding-left: 0;
        margin: 15px 0;
    }
    .options-list li {
        padding: 8px 12px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        margin-bottom: 8px;
        font-size: 0.95rem;
    }
    .key-section {
        background: #ffffff;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        border-top: 6px solid #0f172a;
        margin-top: 40px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        page-break-before: always;
    }
    .citation {
        font-size: 0.85em;
        color: #64748b;
        font-weight: 500;
    }
    code {
        background: #f1f5f9;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: Consolas, Monaco, "Andale Mono", monospace;
        font-size: 0.9em;
        color: #0f172a;
    }
    @media print {
        body {
            max-width: 100%;
            padding: 0;
            background-color: #ffffff;
        }
        .period-box, .concept-card, .activity-card, .gap-card, .question-item, .key-section {
            border: 1px solid #cbd5e1 !important;
            box-shadow: none !important;
        }
    }
"""


# This function builds an HTML document for the multi-period lesson plan.
def generate_lesson_plan_html(tkp):
    meta = tkp.get("educational_metadata", {})
    tp = tkp.get("teaching_plan", {})
    period_contents = tkp.get("period_contents", [])

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Lesson Plan - {meta.get('topic', 'Topic')}</title>
<style>
{COMMON_CSS}
</style>
</head>
<body>
    <h1>Lesson Plan: {meta.get('topic', 'Topic')}</h1>
    <div class="meta-box">
        <div class="meta-item"><strong>Subject:</strong> {meta.get('subject', 'N/A')}</div>
        <div class="meta-item"><strong>Grade:</strong> {meta.get('grade_level', 'N/A')}</div>
        <div class="meta-item"><strong>Difficulty:</strong> {meta.get('difficulty', 'N/A')}</div>
        <div class="meta-item"><strong>Board:</strong> {meta.get('board_alignment', 'General')}</div>
        <div class="meta-item"><strong>Estimated Hours:</strong> {meta.get('estimated_teaching_hours', 2)} hours</div>
        <div class="meta-item"><strong>Total Periods:</strong> {tp.get('total_periods', 0)} ({tp.get('period_duration_minutes', 40)} mins each)</div>
    </div>

    <h2>Overall Strategy</h2>
    <p>{tp.get('overall_strategy', 'N/A')}</p>

    <h2>Period Breakdown</h2>
"""

    period_content_map = {str(c.get('period_number', '0')): c for c in period_contents}

    for period in tp.get("periods", []):
        num = str(period.get("period_number", 1))
        p_content = period_content_map.get(num, {})

        html += f"""
    <div class="period-box">
        <h3>Period {num}: {period.get('title', '')}</h3>
        <p><strong>Duration:</strong> {period.get('duration_minutes', 40)} minutes</p>
        
        <p><strong>Learning Objectives:</strong></p>
        <ul>
"""
        for obj in period.get("learning_objectives", []):
            html += f"            <li>{obj}</li>\n"
        html += f"""        </ul>

        <p><strong>Topics Covered:</strong> {', '.join(period.get('topics_covered', []))}</p>
        <p><strong>Teaching Methods:</strong> {', '.join(period.get('teaching_methods', []))}</p>

        <p><strong>Sequence:</strong></p>
        <ol>
"""
        for seq in period.get("sequence", []):
            html += f"            <li>{seq}</li>\n"
        html += """        </ol>
"""

        entry = p_content.get("entry_ticket", {})
        if entry and entry.get("questions"):
            html += f"""
        <h4>Entry Ticket</h4>
        <p><em>Purpose: {entry.get('purpose', '')}</em></p>
        <ul>
"""
            for q in entry.get("questions", []):
                html += f"            <li>{q}</li>\n"
            html += "        </ul>\n"

        script = p_content.get("teacher_script", "")
        if script:
            html += f"""
        <h4>Teacher Script</h4>
        <div class="script-box">{script}</div>
"""

        notes = p_content.get("blackboard_notes", [])
        if notes:
            html += f"""
        <h4>Blackboard Notes</h4>
        <div class="notes-box">
            <ul>
"""
            for note in notes:
                html += f"                <li>{note}</li>\n"
            html += """            </ul>
        </div>
"""

        cps = p_content.get("checkpoint_questions", [])
        if cps:
            html += f"""
        <h4>Checkpoint Questions</h4>
        <ul>
"""
            for cp in cps:
                html += f"            <li><strong>Q:</strong> {cp.get('question', '')}<br><strong>A:</strong> {cp.get('expected_answer', '')} (Ask after: {cp.get('when_to_ask', '')})</li>\n"
            html += "        </ul>\n"

        exit_t = p_content.get("exit_ticket", {})
        if exit_t and exit_t.get("questions"):
            html += f"""
        <h4>Exit Ticket</h4>
        <ul>
"""
            for q in exit_t.get("questions", []):
                html += f"            <li>{q}</li>\n"
            html += "        </ul>\n"

        hw = p_content.get("homework", [])
        if hw:
            html += f"""
        <h4>Homework</h4>
        <ul>
"""
            for h in hw:
                html += f"            <li>[{h.get('difficulty', '')}] {h.get('task', '')} ({h.get('estimated_time', '')})</li>\n"
            html += "        </ul>\n"

        mentor = p_content.get("mentor_moment", {})
        if mentor and mentor.get("story"):
            html += f"""
        <h4>Mentor Moment: {mentor.get('title', '')}</h4>
        <p>{mentor.get('story', '')}</p>
        <p><em>Connection to Topic: {mentor.get('connection_to_topic', '')}</em></p>
"""

        html += "    </div>\n"

    html += """
</body>
</html>
"""
    return html


# This function builds an HTML document for the teacher guide including activities and misconceptions.
def generate_teacher_guide_html(tkp):
    meta = tkp.get("educational_metadata", {})
    kg = tkp.get("knowledge_graph", {})
    activities = tkp.get("activities", [])
    gaps = tkp.get("learning_gaps", [])

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Teacher Guide - {meta.get('topic', 'Topic')}</title>
<style>
{COMMON_CSS}
    .section {{ margin-bottom: 30px; }}
</style>
</head>
<body>
    <h1>Teacher Guide: {meta.get('topic', 'Topic')}</h1>
    <p><strong>Subject:</strong> {meta.get('subject', 'N/A')} | <strong>Grade:</strong> {meta.get('grade_level', 'N/A')}</p>

    <div class="section">
        <h2>1. Knowledge Mapping</h2>
        <h3>Prerequisites</h3>
        <ul>
"""
    for p in kg.get("prerequisites", []):
        html += f"            <li>{p}</li>\n"
    html += """        </ul>

        <h3>Core Concepts</h3>
"""
    for concept in kg.get("concepts", []):
        cit = concept.get("source_citation", "")
        cit_html = f"<br><small><strong>Source Citation:</strong> {cit}</small>" if cit else ""
        html += f"""
        <div class="concept-card">
            <h4>{concept.get('name', '')}</h4>
            <p><strong>Definition:</strong> {concept.get('definition', '')}</p>
            <p><strong>Explanation:</strong> {concept.get('explanation', '')}{cit_html}</p>
        </div>
"""

    formulae = kg.get("formulae", [])
    if formulae:
        html += """
        <h3>Key Formulae</h3>
        <ul>
"""
        for f in formulae:
            html += f"            <li><strong>{f.get('name', '')}</strong>: <code>{f.get('formula', '')}</code> (Variables: {f.get('variables', '')})</li>\n"
        html += "        </ul>\n"

    apps = kg.get("applications", [])
    if apps:
        html += """
        <h3>Real-world Applications</h3>
        <ul>
"""
        for app in apps:
            html += f"            <li>{app}</li>\n"
        html += "        </ul>\n"

    html += """
    </div>

    <div class="section">
        <h2>2. Classroom Activities</h2>
"""
    for act in activities:
        html += f"""
        <div class="activity-card">
            <h4>{act.get('title', '')}</h4>
            <p><strong>Type:</strong> {act.get('type', '')} | <strong>Duration:</strong> {act.get('duration_minutes', 15)} mins | <strong>Period:</strong> {act.get('period_number', 'Any')}</p>
            <p><strong>Materials Needed:</strong> {', '.join(act.get('materials_needed', []))}</p>
            <p><strong>Teacher Instructions:</strong> {act.get('teacher_instructions', '')}</p>
            <p><strong>Student Instructions:</strong> {act.get('student_instructions', '')}</p>
            <p><strong>Success Criteria:</strong> {act.get('success_criteria', '')}</p>
            <p><strong>Scaffold (Support):</strong> {act.get('scaffold', '')}</p>
            <p><strong>Extension (Challenge):</strong> {act.get('extension', '')}</p>
        </div>
"""

    html += """
    </div>

    <div class="section">
        <h2>3. Misconceptions & Learning Gap Diagnostics</h2>
"""
    for gap in gaps:
        html += f"""
        <div class="gap-card">
            <h4>{gap.get('misconception', '')}</h4>
            <p><strong>Severity:</strong> {gap.get('severity', 'Medium')} | <strong>Related Concept:</strong> {gap.get('related_concept', '')}</p>
            <p><strong>Why it happens:</strong> {gap.get('why_it_happens', '')}</p>
            <p><strong>Cognitive Friction:</strong> {gap.get('cognitive_friction', '')}</p>
            <p><strong>Diagnostic Question:</strong> <em>{gap.get('diagnostic_question', '')}</em></p>
            <p><strong>Socratic Question:</strong> <em>{gap.get('socratic_question', '')}</em></p>
            <p><strong>Remedial Action:</strong> {gap.get('remedial_action', '')}</p>
        </div>
"""

    html += """
    </div>
</body>
</html>
"""
    return html


# This function builds an HTML document for the assessment book containing questions, rubrics, and solutions.
def generate_assessment_book_html(tkp):
    meta = tkp.get("educational_metadata", {})
    assessments = tkp.get("assessments", {})

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Assessment Book - {meta.get('topic', 'Topic')}</title>
<style>
{COMMON_CSS}
</style>
</head>
<body>
    <h1>Assessment: {meta.get('topic', 'Topic')}</h1>
    <p><strong>Subject:</strong> {meta.get('subject', 'N/A')} | <strong>Grade:</strong> {meta.get('grade_level', 'N/A')} | <strong>Total Marks:</strong> {assessments.get('total_marks', 0)}</p>

"""

    mcqs = assessments.get("mcqs", [])
    if mcqs:
        html += "    <h2>Section A: Multiple Choice Questions</h2>\n"
        for i, q in enumerate(mcqs):
            html += f"""
    <div class="question-item">
        <p><strong>Q{i+1}.</strong> {q.get('question', '')}</p>
        <ul class="options-list">
"""
            for opt in q.get("options", []):
                html += f"            <li>{opt}</li>\n"
            html += f"""        </ul>
        <div class="explanation">
            <strong>Explanation:</strong> {q.get('explanation', '')}<br>
            <strong>Why others are wrong:</strong> {', '.join(q.get('why_wrong', []))}
        </div>
    </div>
"""

    short = assessments.get("short_answers", [])
    if short:
        html += "    <h2>Section B: Short Answer Questions</h2>\n"
        for i, q in enumerate(short):
            html += f"""
    <div class="question-item">
        <p><strong>Q{i+1}.</strong> {q.get('question', '')} ({q.get('marks', 3)} Marks)</p>
    </div>
"""

    long_ans = assessments.get("long_answers", [])
    if long_ans:
        html += "    <h2>Section C: Long Answer Questions</h2>\n"
        for i, q in enumerate(long_ans):
            html += f"""
    <div class="question-item">
        <p><strong>Q{i+1}.</strong> {q.get('question', '')} ({q.get('marks', 5)} Marks)</p>
    </div>
"""

    numerical = assessments.get("numerical_problems", [])
    if numerical:
        html += "    <h2>Section D: Numerical Problems</h2>\n"
        for i, q in enumerate(numerical):
            html += f"""
    <div class="question-item">
        <p><strong>Q{i+1}.</strong> {q.get('question', '')} ({q.get('marks', 4)} Marks)</p>
    </div>
"""

    html += """
    <div class="key-section">
        <h2>Answer Key & Grading Rubrics</h2>
"""

    if mcqs:
        html += "        <h3>Section A Answers</h3>\n        <ol>\n"
        for q in mcqs:
            cit = q.get('source_citation', '')
            cit_txt = f" <span class='citation'>(Citation: {cit})</span>" if cit else ""
            html += f"            <li>Correct Answer: <strong>{q.get('correct_answer', '')}</strong>. {q.get('explanation', '')}{cit_txt}</li>\n"
        html += "        </ol>\n"

    if short:
        html += "        <h3>Section B Answers & Marking Scheme</h3>\n"
        for i, q in enumerate(short):
            cit = q.get('source_citation', '')
            cit_txt = f" <span class='citation'>(Citation: {cit})</span>" if cit else ""
            html += f"""
        <p><strong>Q{i+1} Model Answer:</strong> {q.get('model_answer', '')}{cit_txt}</p>
        <p><strong>Marking Scheme:</strong> {q.get('marking_scheme', '')}</p>
"""

    if long_ans:
        html += "        <h3>Section C Answers & Rubrics</h3>\n"
        for i, q in enumerate(long_ans):
            cit = q.get('source_citation', '')
            cit_txt = f" <span class='citation'>(Citation: {cit})</span>" if cit else ""
            html += f"""
        <p><strong>Q{i+1} Model Answer:</strong> {q.get('model_answer', '')}{cit_txt}</p>
        <p><strong>Rubric:</strong> {q.get('rubric', '')}</p>
"""

    if numerical:
        html += "        <h3>Section D Answers & Solutions</h3>\n"
        for i, q in enumerate(numerical):
            cit = q.get('source_citation', '')
            cit_txt = f" <span class='citation'>(Citation: {cit})</span>" if cit else ""
            steps = "".join([f"<li>{s}</li>" for s in q.get('solution_steps', [])])
            html += f"""
        <p><strong>Q{i+1} Solution Steps:</strong></p>
        <ol>{steps}</ol>
        <p><strong>Final Answer:</strong> {q.get('final_answer', '')}{cit_txt}</p>
"""

    html += """
    </div>
</body>
</html>
"""
    return html
