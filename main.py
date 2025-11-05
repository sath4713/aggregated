import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

# We will create this file next
from api.v1.api import api_router
from core.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup:
    setup_logging()

    # Initialize the in-memory cache
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")

    yield  # The application runs

    # Code to run on shutdown (if any):
    pass


# Create the FastAPI app
app = FastAPI(title="Niche-Lite Sports API", lifespan=lifespan)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Niche-Lite Sports API! Go to /docs for API details."
    }


# Include only the public-facing routers
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    # Use 8001 to avoid conflicts with your other project
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
