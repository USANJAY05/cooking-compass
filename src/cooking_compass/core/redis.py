import os

import certifi
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL is not configured")

redis_kwargs = {
    "encoding": "utf-8",
    "decode_responses": True,
}

if REDIS_URL.startswith("rediss://"):
    redis_kwargs["ssl_ca_certs"] = certifi.where()

redis_client = redis.from_url(
    REDIS_URL,
    **redis_kwargs,
)


def get_redis():
    return redis_client