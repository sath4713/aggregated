import pytz
from typing import Dict, List

# --- Global Timezone Configuration ---
TARGET_TIMEZONE = pytz.timezone("America/New_York")

# --- Niche League Master List ---
LEAGUE_ID_MAP: Dict[str, Dict[str, str]] = {
    "Cycling - World Tour": {"source": "niche_scrape", "id": "pcs_world"},
    "Cycling - Pro Series": {"source": "niche_scrape", "id": "pcs_pro"},
    "Track & Field - Diamond League": {
        "source": "niche_scrape",
        "id": "dl_wiki",
    },
    "World Cup Rock Climbing": {"source": "niche_scrape", "id": "ifsc_wiki"},
}

# --- Niche RSS Feed Master List ---
# --- Niche RSS Feed Master List ---
RSS_FEEDS: Dict[str, List[str]] = {
    "Cycling": [
        "http://feeds2.feedburner.com/cyclingnews/news"  # <-- THIS IS THE NEW, RELIABLE FEED
    ],
    "Track & Field - Diamond League": ["https://www.letsrun.com/feed/"],
    "World Cup Rock Climbing": ["https://www.climbing.com/feed/"],
}
