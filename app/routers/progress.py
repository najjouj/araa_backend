from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Submission, User
from app.auth import get_current_user

router = APIRouter(prefix="/api/progress", tags=["progress"])


class ProgressResponse(BaseModel):
    exercises_attempted: int
    exercises_passed: int
    # XP ledger (Phase 2 schema §3.6) isn't built yet — this is a stand-in
    # computed straight from passed submissions so the dashboard has a real
    # (if simplified) number rather than a hardcoded placeholder.
    xp_estimate: int


@router.get("/me", response_model=ProgressResponse)
def my_progress(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    attempted = db.query(func.count(Submission.id)).filter(Submission.user_id == user.id).scalar() or 0
    passed = (
        db.query(func.count(Submission.id))
        .filter(Submission.user_id == user.id, Submission.passed.is_(True))
        .scalar()
        or 0
    )
    return ProgressResponse(
        exercises_attempted=attempted,
        exercises_passed=passed,
        xp_estimate=passed * 10,  # flat 10 XP/exercise until the real xp_ledger exists
    )
