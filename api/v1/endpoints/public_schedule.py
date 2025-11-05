import logging
from typing import List, Dict, Any
from fastapi import APIRouter
from datetime import datetime, timedelta

# Import our Pydantic model
from models.game import Game as PydanticGame

# Import the scraping functions (NO MORE F1)
from services.niche_service import (
    _get_cycling_schedule,
    _scrape_diamond_league_from_wikipedia,
    _get_climbing_schedule,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# --- 1. SET UP THE SERVER-SIDE CACHE ---
SCHEDULE_CACHE: Dict[str, Any] = {}
CACHE_DURATION = timedelta(hours=4)  # Cache for 4 hours
# --- END CACHE SETUP ---


def _fetch_and_cache_schedule() -> List[PydanticGame]:
    """
    This is the "slow" function that runs on a cache miss.
    It runs all scrapers, combines the data, and updates the cache.
    """
    logger.info("--- CACHE MISS ---")
    logger.info("Running all niche scrapers to build new cache...")

    now = datetime.now()
    all_upcoming_games = []

    try:
        # Run all the scrapers from niche_service.py
        scraped_games_athletics = _scrape_diamond_league_from_wikipedia()
        scraped_games_cycling = _get_cycling_schedule()
        scraped_games_climbing = _get_climbing_schedule()

        # Combine all the lists
        if scraped_games_athletics:
            all_upcoming_games.extend(scraped_games_athletics)
        if scraped_games_cycling:
            all_upcoming_games.extend(scraped_games_cycling)
        if scraped_games_climbing:
            all_upcoming_games.extend(scraped_games_climbing)

        # Sort the final list by start time
        all_upcoming_games.sort(key=lambda x: x.start_time)

        logger.info(f"Scrape complete. Found {len(all_upcoming_games)} total games.")

        # Update the cache
        SCHEDULE_CACHE["timestamp"] = now
        SCHEDULE_CACHE["items"] = all_upcoming_games

        return all_upcoming_games

    except Exception as e:
        logger.critical(f"CRITICAL: Failed to run scrapers. Error: {e}")
        return []


@router.get("/", response_model=List[PydanticGame])
def get_public_schedule():
    """
    Returns a list of all upcoming niche sport events.
    Uses a 4-hour in-memory cache to avoid slow scrapes.
    """
    now = datetime.now()

    # 1. Check the cache
    if "timestamp" in SCHEDULE_CACHE:
        cache_age = now - SCHEDULE_CACHE["timestamp"]

        if cache_age < CACHE_DURATION:
            # Cache HIT: Return the fast, cached data
            logger.info("Schedule cache HIT. Returning cached data.")
            return SCHEDULE_CACHE["items"]

    # 2. Cache MISS (or stale): Fetch new data
    return _fetch_and_cache_schedule()
