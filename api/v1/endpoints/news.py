import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta

from models.news import NewsItem
from services.niche_service import fetch_niche_news
from core.config import RSS_FEEDS

router = APIRouter()
logger = logging.getLogger(__name__)

# --- CACHE SETUP (Unchanged) ---
NEWS_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_DURATION = timedelta(minutes=30)
ARTICLES_PER_SPORT = 10

# --- THIS IS THE NEW, SMARTER LOGIC ---
CYCLING_LEAGUE_NAMES = {"Cycling - World Tour", "Cycling - Pro Series"}
# --- END NEW LOGIC ---


@router.get("/{league_name}", response_model=List[NewsItem])
def get_league_news(league_name: str):
    """
    Fetches news feed items for a *specific* league name.
    Uses a server-side cache.
    """

    # --- THIS IS THE NEW, SMARTER LOGIC ---
    # If the request is for a specific cycling league,
    # map it to our general "Cycling" RSS feed.
    if league_name in CYCLING_LEAGUE_NAMES:
        feed_key = "Cycling"
    else:
        feed_key = league_name
    # --- END NEW LOGIC ---

    # Now, we check for the 'feed_key' in our config
    if feed_key not in RSS_FEEDS:
        raise HTTPException(
            status_code=404, detail=f"No RSS feed configured for: {league_name}"
        )

    now = datetime.now()

    # 1. Check the cache (using the feed_key)
    if feed_key in NEWS_CACHE:
        cached_data = NEWS_CACHE[feed_key]
        cache_age = now - cached_data["timestamp"]

        if cache_age < CACHE_DURATION:
            logger.info(f"News cache HIT for {feed_key}.")
            return cached_data["items"]

    # 2. CACHE MISS (or stale): Fetch new data
    logger.info(f"News cache MISS for {feed_key}. Fetching new data...")

    # Fetch news from the service (using the feed_key)
    news_items = fetch_niche_news(feed_key)

    # Sort by date
    news_items.sort(key=lambda x: x.published_date, reverse=True)

    # Apply the 10-article limit
    top_items = news_items[:ARTICLES_PER_SPORT]

    # 3. Update the cache with the *limited* list
    NEWS_CACHE[feed_key] = {"timestamp": now, "items": top_items}

    return top_items
