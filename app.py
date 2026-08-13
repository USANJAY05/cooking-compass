from fastapi import FastAPI
from dotenv import load_dotenv
import os

from cooking_compass.routes.router import router

load_dotenv()

app = FastAPI()
app.include_router(router)


@app.get("/")
def home():
    return f"Welcome to {os.getenv('APP_NAME')}"