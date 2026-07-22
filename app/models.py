import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class Locale(str, enum.Enum):
    en = "en"
    ar = "ar"


class User(Base):
    """Matches Phase 2 schema §3.1 (identity_roles), trimmed to launch-critical fields."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.student)
    preferred_locale = Column(Enum(Locale), nullable=False, default=Locale.en)
    display_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Lesson(Base):
    """Matches Phase 2 schema §3.2 (curriculum structure), language-agnostic."""

    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    slug = Column(String, unique=True, nullable=False, index=True)
    order_index = Column(Integer, nullable=False, default=0)

    exercises = relationship("Exercise", back_populates="lesson")


class Exercise(Base):
    """Matches Phase 2 schema §3.4. Prompt/localization lives in a separate
    translations table in the full schema — omitted here for the MVP slice,
    added back in when the admin/content pipeline is built."""

    __tablename__ = "exercises"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    lesson_id = Column(UUID(as_uuid=False), ForeignKey("lessons.id"), nullable=True)
    xp_reward = Column(Integer, nullable=False, default=10)
    starter_code = Column(Text, nullable=False, default="")

    lesson = relationship("Lesson", back_populates="exercises")
    test_cases = relationship("ExerciseTestCase", back_populates="exercise")


class ExerciseTestCase(Base):
    """Matches Phase 2 schema §3.4 (exercise_test_cases) — language-neutral,
    shared across locales."""

    __tablename__ = "exercise_test_cases"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    exercise_id = Column(UUID(as_uuid=False), ForeignKey("exercises.id"), nullable=False)
    input_payload = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=False)
    is_hidden = Column(Boolean, default=False)

    exercise = relationship("Exercise", back_populates="test_cases")


class Submission(Base):
    """Matches Phase 2 schema §3.4 (submissions)."""

    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    exercise_id = Column(UUID(as_uuid=False), ForeignKey("exercises.id"), nullable=False)
    code_text = Column(Text, nullable=False)
    passed = Column(Boolean, nullable=False, default=False)
    tests_passing = Column(Integer, nullable=False, default=0)
    tests_total = Column(Integer, nullable=False, default=0)
    submitted_at = Column(DateTime, default=datetime.utcnow)
