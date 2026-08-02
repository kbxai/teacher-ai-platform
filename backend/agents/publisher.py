import json
import os
from datetime import datetime
from backend.schemas.models import TeacherKnowledgePackage
from backend.config import OUTPUT_DIR


def publish_tkp(document, metadata, knowledge, teaching_plan,
                period_contents, activities, assessments, learning_gaps,
                validation_report):

    tkp = TeacherKnowledgePackage(
        version="1.0",
        generated_at=datetime.now().isoformat(),
        source_document=document.filename,
        document_structure=document,
        educational_metadata=metadata,
        knowledge_graph=knowledge,
        teaching_plan=teaching_plan,
        period_contents=period_contents,
        activities=activities,
        assessments=assessments,
        learning_gaps=learning_gaps,
        validation_report=validation_report,
        pipeline_metadata={
            "model": "Multi-Provider Hybrid Architecture (Groq / Gemini / Nvidia)",
            "pipeline_version": "1.0",
            "total_periods": teaching_plan.total_periods,
            "total_activities": len(activities),
            "total_assessments": (
                len(assessments.mcqs) + len(assessments.short_answers) +
                len(assessments.long_answers) + len(assessments.numerical_problems)
            ),
            "total_learning_gaps": len(learning_gaps),
            "validation_passed": validation_report.overall_passed
        }
    )

    safe_name = document.filename.replace(" ", "_").replace(".", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"TKP_{safe_name}_{timestamp}.json"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tkp.model_dump(), f, indent=2, ensure_ascii=False)

    return tkp, output_path
