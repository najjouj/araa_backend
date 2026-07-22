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

    # Piston is a self-hostable sandboxed code execution engine
    # (https://github.com/engineer-man/piston). Point this at either your
    # own deployed instance or a compatible public instance during early
    # development. See DEPLOYMENT.md, Step 4.
    piston_url: str = "https://emkc.org/api/v2/piston"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()
