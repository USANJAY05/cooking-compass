import os

from dotenv import load_dotenv

load_dotenv()


# S3-compatible object storage (Backblaze B2 / AWS S3)
STORAGE_REGION = os.getenv("STORAGE_REGION")
STORAGE_ENDPOINT = os.getenv("STORAGE_ENDPOINT")
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET")
STORAGE_ACCESS_KEY_ID = os.getenv("STORAGE_ACCESS_KEY_ID")
STORAGE_SECRET_ACCESS_KEY = os.getenv("STORAGE_SECRET_ACCESS_KEY")
