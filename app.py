import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from cooking_compass.core.db import Base, engine
from cooking_compass.models import recipe, users

load_dotenv(".env.dev")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Registered tables:", Base.metadata.tables.keys())

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables created successfully.")

    yield

    await engine.dispose()


app = FastAPI(
    title="Cooking Compass",
    lifespan=lifespan,
)


@app.get("/")
async def home():
    return f"Welcome to {os.getenv('APP_NAME', 'Cooking Compass')}"