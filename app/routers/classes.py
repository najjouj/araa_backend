import secrets
import string

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Class, ClassEnrollment, User, UserRole, Submission
from app.auth import get_current_user, require_role

router = APIRouter(prefix="/api/classes", tags=["classes"])


def generate_join_code(length: int = 6) -> str:
    # Uppercase letters + digits, no ambiguous characters (0/O, 1/I) since
    # students type this in by hand.
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class CreateClassRequest(BaseModel):
    name: str


class ClassResponse(BaseModel):
    id: str
    name: str
    join_code: str
    student_count: int

    class Config:
        from_attributes = True


class JoinClassRequest(BaseModel):
    join_code: str


class RosterEntry(BaseModel):
    student_id: str
    display_name: str
    email: str
    exercises_attempted: int
    exercises_passed: int


@router.post("", response_model=ClassResponse)
def create_class(
    body: CreateClassRequest,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
):
    new_class = Class(teacher_id=teacher.id, name=body.name, join_code=generate_join_code())
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    return ClassResponse(
        id=new_class.id, name=new_class.name, join_code=new_class.join_code, student_count=0
    )


@router.get("", response_model=list[ClassResponse])
def list_my_classes(
    db: Session = Depends(get_db),
    teacher: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
):
    classes = db.query(Class).filter(Class.teacher_id == teacher.id).all()
    return [
        ClassResponse(
            id=c.id, name=c.name, join_code=c.join_code, student_count=len(c.enrollments)
        )
        for c in classes
    ]


@router.post("/join")
def join_class(
    body: JoinClassRequest,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_user),
):
    target_class = db.query(Class).filter(Class.join_code == body.join_code.upper()).first()
    if not target_class:
        raise HTTPException(status_code=404, detail="No class found with that join code")

    already_enrolled = (
        db.query(ClassEnrollment)
        .filter(
            ClassEnrollment.class_id == target_class.id,
            ClassEnrollment.student_id == student.id,
        )
        .first()
    )
    if already_enrolled:
        raise HTTPException(status_code=409, detail="Already enrolled in this class")

    db.add(ClassEnrollment(class_id=target_class.id, student_id=student.id))
    db.commit()
    return {"joined": target_class.name}


@router.get("/{class_id}/roster", response_model=list[RosterEntry])
def get_roster(
    class_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
):
    target_class = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher.id).first()
    if not target_class:
        raise HTTPException(status_code=404, detail="Class not found")

    roster = []
    for enrollment in target_class.enrollments:
        student = enrollment.student
        # Minimal per-student stats for the teacher analytics view — a fuller
        # analytics pass (per-lesson breakdown, time-on-task, etc.) is a
        # later iteration on top of this same query shape.
        attempted = (
            db.query(func.count(Submission.id)).filter(Submission.user_id == student.id).scalar()
        )
        passed = (
            db.query(func.count(Submission.id))
            .filter(Submission.user_id == student.id, Submission.passed.is_(True))
            .scalar()
        )
        roster.append(
            RosterEntry(
                student_id=student.id,
                display_name=student.display_name,
                email=student.email,
                exercises_attempted=attempted or 0,
                exercises_passed=passed or 0,
            )
        )
    return roster
