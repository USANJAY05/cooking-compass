import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from cooking_compass.models.base import Base


load_dotenv(".env")

DB_URL = os.getenv("DB_URL")

if not DB_URL:
    raise RuntimeError("DB_URL is not set")


engine = create_async_engine(
    DB_URL,
    echo=True,
)


SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)