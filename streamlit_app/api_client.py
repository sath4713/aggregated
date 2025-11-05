import requests
import streamlit as st
import logging

# --- THIS IS THE CHANGE ---
# Get the API URL from Streamlit's secrets
# Fallback to port 8001 (the new API) for local development
API_URL = st.secrets.get("API_URL", "http://127.0.0.1:8001/api/v1")
# --- END CHANGE ---

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --- ✂️ FAT CUT ---
# All authentication, user, and preference functions have been deleted:
# - _handle_401_error
# - login_user
# - get_preferences
# - add_preference
# - remove_preference
# - register_user
# - get_user_details
# --- END CUT ---


@st.cache_data(ttl=900)  # Cache for 15 minutes
def get_schedule():
    """Fetches the public schedule from the API."""
    # --- ✂️ FAT CUT ---
    # Removed token, headers, and 401 handling
    # Changed endpoint from /schedule/me to /schedule

    schedule_url = f"{API_URL}/schedule"
    logger.info("API Client: Fetching public schedule...")
    try:
        # No 'headers' argument needed
        response = requests.get(schedule_url, timeout=30)

        if response.status_code == 200:
            logger.info("API Client: Schedule fetched successfully.")
            return response.json()
        else:
            logger.error(
                f"API Client: Failed to fetch schedule. Status: {response.status_code}, Response: {response.text[:200]}"
            )
            st.error(f"Failed to fetch schedule: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        logger.error("API Client: Request timed out fetching schedule.")
        st.error("Request timed out fetching schedule.")
        return None
    except requests.exceptions.ConnectionError:
        logger.critical(
            f"API Client: Connection error fetching schedule. API_URL: {API_URL}"
        )
        st.error(f"Connection Error: Could not connect to the API at {API_URL}.")
        return None


def get_news(league_name: str):
    """Fetches the news feed for a specific league from the API."""
    # --- ✂️ FAT CUT ---
    # Removed token, headers, and 401 handling

    news_url = f"{API_URL}/news/{league_name}"
    logger.info(f"API Client: Fetching news for {league_name}...")
    try:
        # No 'headers' argument needed
        response = requests.get(news_url, timeout=30)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            logger.warning(f"API Client: No news feed found for {league_name} (404).")
            return []
        else:
            logger.error(
                f"API Client: Failed to fetch news for {league_name}. Status: {response.status_code}, Response: {response.text[:200]}"
            )
            st.error(
                f"Failed to fetch news feed for {league_name}. Status: {response.status_code}"
            )
            return None

    except requests.exceptions.Timeout:
        logger.error(f"API Client: Request timed out fetching news for {league_name}.")
        st.error(f"Request timed out fetching news for {league_name}.")
        return None
    except requests.exceptions.ConnectionError:
        logger.critical(
            f"API Client: Connection error fetching news for {league_name}. API_URL: {API_URL}"
        )
        st.error(f"Connection Error: Could not connect to the API at {API_URL}.")
        return None


@st.cache_data(ttl=3600)  # Cache the list for 1 hour
def get_all_leagues():
    """Fetches the complete list of available leagues from the API."""
    # --- THIS FUNCTION WAS ALREADY PERFECT (NO FAT) ---

    leagues_url = f"{API_URL}/leagues/"
    logger.info("API Client: Fetching all leagues (cached)...")
    try:
        response = requests.get(leagues_url, timeout=30)
        if response.status_code == 200:
            logger.info("API Client: All leagues fetched successfully.")
            return response.json()
        else:
            logger.error(
                f"API Client: Failed to fetch all leagues. Status: {response.status_code}"
            )
            st.error(f"Failed to fetch league list. Status: {response.status_code}")
            return []
    except requests.exceptions.Timeout:
        logger.error("API Client: Request timed out fetching all leagues.")
        st.error("Request timed out fetching all leagues.")
        return []
    except requests.exceptions.ConnectionError:
        logger.critical(
            f"API Client: Connection error fetching all leagues. API_URL: {API_URL}"
        )
        st.error(f"Connection Error: Could not connect to the API at {API_URL}.")
        return []
