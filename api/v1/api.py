from fastapi import APIRouter

# We will create these endpoints next
from api.v1.endpoints import public_schedule, public_leagues, news

api_router = APIRouter()

# These are the only endpoints in the entire app
api_router.include_router(public_schedule.router, prefix="/schedule", tags=["schedule"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(public_leagues.router, prefix="/leagues", tags=["leagues"])
