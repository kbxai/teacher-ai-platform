# This file performs automated validation, quality checks, and source grounding audits on the generated TKP package.

from backend.schemas.models import ValidationResult, ValidationReport
from datetime import datetime


# This function runs all 10 automated quality checks and returns a comprehensive ValidationReport.
def validate_tkp(document, metadata, knowledge, teaching_plan,
                 period_contents, activities, assessments, learning_gaps):
    results = []

    results.append(check_schema_completeness(metadata, knowledge, teaching_plan))
    results.append(check_objectives_coverage(knowledge, teaching_plan))
    results.append(check_content_coverage(teaching_plan, period_contents))
    results.append(check_assessment_coverage(knowledge, assessments))
    results.append(check_activity_diversity(activities))
    results.append(check_gap_analysis(learning_gaps))
    results.append(check_concept_grounding(document, knowledge))
    results.append(check_content_grounding(document, period_contents))
    results.append(check_period_consistency(teaching_plan, period_contents))
    results.append(check_assessment_grounding(document, assessments))

    passed_count = sum(1 for r in results if r.passed)

    return ValidationReport(
        overall_passed=passed_count >= len(results) * 0.7,
        total_checks=len(results),
        passed_checks=passed_count,
        results=results,
        timestamp=datetime.now().isoformat()
    )


# This check verifies that all required metadata, objectives, concepts, and plan periods exist.
def check_schema_completeness(metadata, knowledge, teaching_plan):
    issues = []
    if not metadata.subject:
        issues.append("Missing subject")
    if not metadata.topic:
        issues.append("Missing topic")
    if not knowledge.learning_objectives:
        issues.append("No learning objectives")
    if not knowledge.concepts:
        issues.append("No concepts extracted")
    if not teaching_plan.periods:
        issues.append("No periods in teaching plan")

    return ValidationResult(
        check_name="Schema Completeness",
        passed=len(issues) == 0,
        message="All required fields present" if not issues else f"Missing: {', '.join(issues)}",
        details=str(issues)
    )


# This check verifies that all learning objectives are assigned across teaching plan periods.
def check_objectives_coverage(knowledge, teaching_plan):
    all_objectives = [obj.objective.lower() for obj in knowledge.learning_objectives]
    covered_objectives = []

    for period in teaching_plan.periods:
        for obj in period.learning_objectives:
            covered_objectives.append(obj.lower())

    uncovered = []
    for obj in all_objectives:
        found = False
        for covered in covered_objectives:
            if obj[:30] in covered or covered[:30] in obj:
                found = True
                break
        if not found:
            uncovered.append(obj[:50])

    return ValidationResult(
        check_name="Learning Objectives Coverage",
        passed=len(uncovered) <= 1,
        message=f"{len(all_objectives) - len(uncovered)}/{len(all_objectives)} objectives covered in teaching plan",
        details=f"Uncovered: {uncovered}" if uncovered else "All covered"
    )


# This check verifies that content is generated for all planned periods.
def check_content_coverage(teaching_plan, period_contents):
    plan_periods = len(teaching_plan.periods)
    content_periods = len(period_contents)

    return ValidationResult(
        check_name="Content Coverage",
        passed=content_periods >= plan_periods,
        message=f"Content generated for {content_periods}/{plan_periods} periods",
        details=""
    )


# This check verifies that a minimum number of assessment questions have been generated.
def check_assessment_coverage(knowledge, assessments):
    total_questions = (
        len(assessments.mcqs) +
        len(assessments.short_answers) +
        len(assessments.long_answers) +
        len(assessments.numerical_problems)
    )

    return ValidationResult(
        check_name="Assessment Coverage",
        passed=total_questions >= 10,
        message=f"{total_questions} assessment items generated",
        details=f"MCQs: {len(assessments.mcqs)}, Short: {len(assessments.short_answers)}, Long: {len(assessments.long_answers)}, Numerical: {len(assessments.numerical_problems)}"
    )


# This check verifies that classroom activities cover at least 3 distinct activity types.
def check_activity_diversity(activities):
    if not activities:
        return ValidationResult(
            check_name="Activity Diversity",
            passed=False,
            message="No activities generated",
            details=""
        )

    types = set(a.type for a in activities)

    return ValidationResult(
        check_name="Activity Diversity",
        passed=len(types) >= 3,
        message=f"{len(activities)} activities with {len(types)} different types",
        details=f"Types: {', '.join(types)}"
    )


# This check verifies that student learning gaps and misconceptions are identified.
def check_gap_analysis(learning_gaps):
    return ValidationResult(
        check_name="Learning Gap Analysis",
        passed=len(learning_gaps) >= 3,
        message=f"{len(learning_gaps)} learning gaps identified",
        details=""
    )


# This check performs fuzzy substring matching to verify concepts exist in the source document.
def check_concept_grounding(document, knowledge):
    doc_text = document.raw_text.lower()
    grounded = 0
    total = len(knowledge.concepts)
    ungrounded = []

    for concept in knowledge.concepts:
        name_words = concept.name.lower().split()
        found = False
        for word in name_words:
            if len(word) > 3 and word in doc_text:
                found = True
                break
        if found:
            grounded += 1
        else:
            ungrounded.append(concept.name)

    ratio = grounded / total if total > 0 else 0

    return ValidationResult(
        check_name="Concept Source Grounding",
        passed=ratio >= 0.7,
        message=f"{grounded}/{total} concepts grounded in source document ({ratio*100:.0f}%)",
        details=f"Ungrounded: {ungrounded[:5]}" if ungrounded else "All concepts found in source"
    )


# This check verifies that generated teacher scripts reference words from the source document.
def check_content_grounding(document, period_contents):
    doc_text = document.raw_text.lower()
    doc_words = set(doc_text.split())

    total_scripts = 0
    grounded_scripts = 0

    for content in period_contents:
        if not content.teacher_script:
            continue
        total_scripts += 1
        script_words = content.teacher_script.lower().split()
        key_words = [w for w in script_words if len(w) > 5]

        if not key_words:
            continue

        overlap = sum(1 for w in key_words if w in doc_words)
        ratio = overlap / len(key_words)
        if ratio >= 0.15:
            grounded_scripts += 1

    if total_scripts == 0:
        return ValidationResult(
            check_name="Content Source Grounding",
            passed=False,
            message="No teacher scripts to validate",
            details=""
        )

    ratio = grounded_scripts / total_scripts

    return ValidationResult(
        check_name="Content Source Grounding",
        passed=ratio >= 0.7,
        message=f"{grounded_scripts}/{total_scripts} teacher scripts are grounded in source ({ratio*100:.0f}%)",
        details="Validates that generated teaching content references concepts from the original document"
    )


# This check verifies that assessment questions test knowledge present in the source document.
def check_assessment_grounding(document, assessments):
    doc_text = document.raw_text.lower()
    total = 0
    grounded = 0

    all_questions = []
    for mcq in assessments.mcqs:
        all_questions.append(mcq.question)
    for sa in assessments.short_answers:
        all_questions.append(sa.question)
    for la in assessments.long_answers:
        all_questions.append(la.question)

    for q in all_questions:
        total += 1
        q_words = [w for w in q.lower().split() if len(w) > 4]
        if not q_words:
            continue
        overlap = sum(1 for w in q_words if w in doc_text)
        if overlap >= 2:
            grounded += 1

    ratio = grounded / total if total > 0 else 0

    return ValidationResult(
        check_name="Assessment Source Grounding",
        passed=ratio >= 0.6,
        message=f"{grounded}/{total} assessment questions reference source content ({ratio*100:.0f}%)",
        details="Validates that assessment questions test knowledge from the original document, not hallucinated content"
    )


# This check verifies that each period has complete scripts, entry tickets, and exit tickets.
def check_period_consistency(teaching_plan, period_contents):
    issues = []

    for content in period_contents:
        if not content.teacher_script or len(content.teacher_script) < 50:
            issues.append(f"Period {content.period_number}: Teacher script too short")
        if not content.entry_ticket.questions:
            issues.append(f"Period {content.period_number}: Missing entry ticket")
        if not content.exit_ticket.questions:
            issues.append(f"Period {content.period_number}: Missing exit ticket")

    return ValidationResult(
        check_name="Period Content Consistency",
        passed=len(issues) == 0,
        message="All periods have complete content" if not issues else f"{len(issues)} issues found",
        details=str(issues) if issues else ""
    )
