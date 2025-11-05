import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta

from models.news import NewsItem
from services.niche_service import fetch_niche_news
from core.config import RSS_FEEDS

router = APIRouter()
logger = logging.getLogger(__name__)

# --- 1. SET UP THE SERVER-SIDE CACHE ---
NEWS_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_DURATION = timedelta(minutes=30)  # Cache news for 30 minutes
ARTICLES_PER_SPORT = 10
# --- END CACHE SETUP ---


@router.get("/{league_name}", response_model=List[NewsItem])
def get_league_news(league_name: str):
    """
    Fetches news feed items for a *specific* league name.
    Uses a server-side cache.
    """

    if league_name not in RSS_FEEDS:
        raise HTTPException(
            status_code=404, detail=f"No RSS feed configured for league: {league_name}"
        )

    now = datetime.now()

    # 1. Check the cache
    if league_name in NEWS_CACHE:
        cached_data = NEWS_CACHE[league_name]
        cache_age = now - cached_data["timestamp"]

        if cache_age < CACHE_DURATION:
            logger.info(f"News cache HIT for {league_name}.")
            return cached_data["items"]

    # 2. CACHE MISS (or stale): Fetch new data
    logger.info(f"News cache MISS for {league_name}. Fetching new data...")

    # Fetch news from the service
    news_items = fetch_niche_news(league_name)

    # Sort by date
    news_items.sort(key=lambda x: x.published_date, reverse=True)

    # Apply the 10-article limit
    top_items = news_items[:ARTICLES_PER_SPORT]

    # 3. Update the cache with the *limited* list
    NEWS_CACHE[league_name] = {"timestamp": now, "items": top_items}

    return top_items
