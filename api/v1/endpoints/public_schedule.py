import logging
from typing import List, Dict, Any
from fastapi import APIRouter
from datetime import datetime, timedelta

from models.game import Game as PydanticGame

# Import the scraping functions
from services.niche_service import (
    _get_cycling_schedule,
    _scrape_diamond_league_from_wikipedia,
    _get_climbing_schedule,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# --- CACHE SETUP (Unchanged) ---
SCHEDULE_CACHE: Dict[str, Any] = {}
CACHE_DURATION = timedelta(hours=4)
# --- END CACHE SETUP ---


def _fetch_and_cache_schedule() -> List[PydanticGame]:
    """
    This is the "slow" function that runs on a cache miss.
    It now runs each scraper independently so one failure
    doesn't break the whole schedule.
    """
    logger.info("--- CACHE MISS ---")
    logger.info("Running all niche scrapers to build new cache...")

    now = datetime.now()
    all_upcoming_games = []

    # --- THIS IS THE SMARTER LOGIC ---

    # 1. Try to get Cycling
    try:
        scraped_games_cycling = _get_cycling_schedule()
        if scraped_games_cycling:
            all_upcoming_games.extend(scraped_games_cycling)
            logger.info(
                f"Successfully scraped {len(scraped_games_cycling)} cycling events."
            )
    except Exception as e:
        logger.error(f"SCRAPER FAILED: Cycling scraper failed. Error: {e}")

    # 2. Try to get Track & Field
    try:
        scraped_games_athletics = _scrape_diamond_league_from_wikipedia()
        if scraped_games_athletics:
            all_upcoming_games.extend(scraped_games_athletics)
            logger.info(
                f"Successfully scraped {len(scraped_games_athletics)} track events."
            )
    except Exception as e:
        logger.error(f"SCRAPER FAILED: Track scraper failed. Error: {e}")

    # 3. Try to get Climbing
    try:
        scraped_games_climbing = _get_climbing_schedule()
        if scraped_games_climbing:
            all_upcoming_games.extend(scraped_games_climbing)
            logger.info(
                f"Successfully scraped {len(scraped_games_climbing)} climbing events."
            )
    except Exception as e:
        logger.error(f"SCRAPER FAILED: Climbing scraper failed. Error: {e}")

    # --- END SMARTER LOGIC ---

    # Sort the final list (of successfully scraped events)
    all_upcoming_games.sort(key=lambda x: x.start_time)

    logger.info(f"Scrape complete. Found {len(all_upcoming_games)} total games.")

    # Update the cache
    SCHEDULE_CACHE["timestamp"] = now
    SCHEDULE_CACHE["items"] = all_upcoming_games

    return all_upcoming_games


@router.get("/", response_model=List[PydanticGame])
def get_public_schedule():
    """
    Returns a list of all upcoming niche sport events.
    Uses a 4-hour in-memory cache to avoid slow scrapes.
    """
    now = datetime.now()

    # 1. Check the cache (Unchanged)
    if "timestamp" in SCHEDULE_CACHE:
        cache_age = now - SCHEDULE_CACHE["timestamp"]

        if cache_age < CACHE_DURATION:
            logger.info("Schedule cache HIT. Returning cached data.")
            return SCHEDULE_CACHE["items"]

    # 2. Cache MISS (or stale): Fetch new data (Unchanged)
    return _fetch_and_cache_schedule()
