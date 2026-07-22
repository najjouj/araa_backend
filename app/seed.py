"""
Run once after the database is up to populate the `lists-intro` demo lesson
that the Phase 5 frontend already renders, so submitting code actually
produces real pass/fail results end to end.

    python -m app.seed
"""

from app.database import SessionLocal, Base, engine
from app.models import Lesson, Exercise, ExerciseTestCase

Base.metadata.create_all(bind=engine)
db = SessionLocal()

existing = db.query(Lesson).filter(Lesson.slug == "lists-intro").first()
if existing:
    print("lists-intro already seeded, skipping.")
else:
    lesson = Lesson(slug="lists-intro", order_index=4)
    exercise = Exercise(
        lesson=lesson,
        xp_reward=10,
        starter_code='groceries = ["bread"]\n# write your code below\n\nprint(len(groceries))',
    )
    test_case = ExerciseTestCase(
        exercise=exercise,
        input_payload="",
        expected_output="4",  # bread + 3 appended items
        is_hidden=False,
    )
    db.add_all([lesson, exercise, test_case])
    db.commit()
    print("Seeded lists-intro lesson.")

db.close()
