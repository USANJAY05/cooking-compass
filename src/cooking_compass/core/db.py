

from cooking_compass.models.base import Base




import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Do not load a second .env file if Uvicorn is already
# providing the environment with --env-file.
load_dotenv()


# =========================================================
# Environment
# =========================================================

APP_ENV = os.getenv("APP_ENV", "development").lower()


# =========================================================
# Database URL
# =========================================================

DB_URL = os.getenv("DB_URL")

if not DB_URL:
    raise RuntimeError("DB_URL is not set")


# =========================================================
# SSL Configuration
# =========================================================

connect_args = {}

if APP_ENV == "production":
    CA_CERT = os.getenv("MYSQL_CA_CERT")

    if not CA_CERT:
        raise RuntimeError(
            "MYSQL_CA_CERT is required when APP_ENV=production"
        )

    CA_CERT_PATH = Path(CA_CERT).expanduser().resolve()

    if not CA_CERT_PATH.exists():
        raise RuntimeError(
            f"MySQL CA certificate not found: {CA_CERT_PATH}"
        )

    if not CA_CERT_PATH.is_file():
        raise RuntimeError(
            f"MySQL CA certificate path is not a file: {CA_CERT_PATH}"
        )

    connect_args["ssl"] = {
        "ca": str(CA_CERT_PATH),
    }


# =========================================================
# SQLAlchemy Async Engine
# =========================================================

engine = create_async_engine(
    DB_URL,
    echo=True,
    connect_args=connect_args,
)


# =========================================================
# Async Session
# =========================================================

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# =========================================================
# FastAPI Database Dependency
# =========================================================

async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()