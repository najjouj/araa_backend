from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    All config comes from environment variables so the same image runs
    unchanged locally (via docker-compose) and on Railway/Render, per the
    twelve-factor pattern the deployment guide assumes.
    """

    # Railway/Render inject DATABASE_URL automatically when you attach a
    # Postgres plugin — this default is for local docker-compose only.
    database_url: str = "postgresql://pylearn:pylearn@db:5432/pylearn"

    # Comma-separated list of allowed frontend origins, e.g.
    # "https://pylearn.vercel.app,http://localhost:3000"
    cors_origins: str = "http://localhost:3000"

    # NOTE: Piston (self-hosted or public) is no longer used for code
    # execution — see app/services/sandbox.py, which now runs student code
    # as a resource-limited local subprocess instead. This variable is kept
    # only so an old PISTON_URL env var doesn't break startup; it's unused.
    piston_url: str = ""

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()
