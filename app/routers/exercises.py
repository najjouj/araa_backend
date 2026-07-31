from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lesson, Exercise, Submission
from app.services.sandbox import run_python, check_output, SandboxError
from app.auth import get_optional_user
from app.models import User

router = APIRouter(prefix="/api/exercises", tags=["exercises"])


class SubmitRequest(BaseModel):
    code: str


class SubmitResponse(BaseModel):
    passing: int
    total: int
    stderr: str | None = None


@router.post("/{lesson_slug}/submit", response_model=SubmitResponse)
async def submit_exercise(
    lesson_slug: str,
    body: SubmitRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """
    Matches the route the frontend's CodeExercisePane already calls
    (POST /api/exercises/{lessonId}/submit) from Phase 5. Runs the
    student's code against every test case for the lesson's coding
    exercise via the sandbox service, then records the submission.
    """
    lesson = db.query(Lesson).filter(Lesson.slug == lesson_slug).first()
    if not lesson or not lesson.exercises:
        raise HTTPException(status_code=404, detail="No exercise found for this lesson")

    exercise = lesson.exercises[0]
    test_cases = exercise.test_cases

    if not test_cases:
        raise HTTPException(status_code=422, detail="Exercise has no test cases configured")

    passing = 0
    last_stderr = None

    for case in test_cases:
        try:
            result = await run_python(body.code, stdin=case.input_payload or "")
        except SandboxError as exc:
            raise HTTPException(status_code=502, detail=f"Sandbox unavailable: {exc}")

        last_stderr = result["stderr"] or last_stderr
        if check_output(result["stdout"], case.expected_output):
            passing += 1

    submission = Submission(
        user_id=current_user.id if current_user else None,
        exercise_id=exercise.id,
        code_text=body.code,
        passed=passing == len(test_cases),
        tests_passing=passing,
        tests_total=len(test_cases),
    )
    db.add(submission)
    db.commit()

    return SubmitResponse(passing=passing, total=len(test_cases), stderr=last_stderr)
