import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from cooking_compass.core.db import Base, engine
from cooking_compass import models
from cooking_compass.routes.router import router
from fastapi.middleware.cors import CORSMiddleware

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
    swagger_ui_init_oauth={
        "clientId": "your-culinary-app-client-id",
        "usePkceWithAuthorizationCodeGrant": True,
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend's actual domain in production (e.g., ["https://your-frontend.vercel.app"])
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods including OPTIONS for preflight
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def home():
    return {
        "message": f"Welcome to {os.getenv('APP_NAME', 'Cooking Compass')}"
    }