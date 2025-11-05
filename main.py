import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# --- THIS IS THE MODERN (V2) SYNTAX ---
# It is 100% compatible with the 'fastapi-cache2' library
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from api.v1.api import api_router
from core.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")

    yield


app = FastAPI(title="Niche-Lite Sports API", lifespan=lifespan)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Niche-Lite Sports API! Go to /docs for API details."
    }


app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
