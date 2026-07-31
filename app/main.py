from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import exercises, auth, classes, progress

app = FastAPI(title="PyLearn API")

# CORS_ORIGINS is a comma-separated env var so the deployed Vercel URL can
# be added without a code change — see DEPLOYMENT.md, Step 5.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(exercises.router)
app.include_router(auth.router)
app.include_router(classes.router)
app.include_router(progress.router)


@app.on_event("startup")
def on_startup():
    # For an MVP this creates tables directly; swap for Alembic migrations
    # (already in requirements.txt) once the schema starts changing after
    # launch, so upgrades don't require a destructive rebuild.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    # Railway/Render both use this to know the service is up.
    return {"status": "ok"}
