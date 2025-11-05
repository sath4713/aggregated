import streamlit as st
from datetime import datetime
import pytz

# --- ✂️ FAT CUT ---
# Removed 'auth' import
# Removed 'get_preferences' and 'login_user'
from api_client import get_news, get_all_leagues

st.set_page_config(page_title="Niche News", page_icon="📰")

# --- 1. ADD THE MAIN TITLE ---
st.title("📰 Niche Sports News")

# --- ✂️ FAT CUT ---
# Removed all auth.initialize_session() and token logic

# --- Custom CSS for News Cards (Unchanged) ---
st.markdown(
    """
<style>
    /* ... (Your news card CSS) ... */
    .news-card {
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        transition: box-shadow 0.3s ease-in-out;
    }
    .news-title a {
        font-size: 1.25em;
        font-weight: 600;
        text-decoration: none;
    }
    .news-title a:hover {
        text-decoration: underline;
    }
    .news-caption {
        font-size: 0.9em;
        margin-bottom: 8px;
    }
    .news-summary {
        font-family: 'Source Sans Pro', sans-serif;
        margin-bottom: 0;
    }
    [data-theme="light"] .news-card {
        border: 1px solid #e1e4e8;
        /* ... (rest of your CSS) ... */
    }
    [data-theme="dark"] .news-card {
        border: 1px solid #30363d;
        /* ... (rest of your CSS) ... */
    }
    [data-theme="dark"] .news-summary {
        color: #c9d1d9 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- ✂️ FAT CUT ---
# Removed the entire 'if token:' and 'else:' blocks.
# This page is now 100% public.

all_news_items = []

# 1. Get *all* available leagues from the public API
# This replaces the user-specific 'get_preferences()'
all_available_leagues = get_all_leagues()

if not all_available_leagues:
    st.info("No news feeds are currently configured by the API.")
else:
    # 2. Determine which unique feeds to fetch
    leagues_to_fetch_news_for = set()
    cycling_leagues = {"Cycling - World Tour", "Cycling - Pro Series"}

    user_follows_cycling = any(
        league in cycling_leagues for league in all_available_leagues
    )

    for league in all_available_leagues:
        if league in cycling_leagues:
            leagues_to_fetch_news_for.add("Cycling")
        else:
            leagues_to_fetch_news_for.add(league)

    league_options = sorted(list(leagues_to_fetch_news_for))
    selected_leagues = st.multiselect(
        "Filter news by league:", options=league_options, default=league_options
    )

    # 3. Fetch news for the *selected* set
    with st.spinner("Fetching latest news..."):
        for league_name in selected_leagues:
            # --- ✂️ FAT CUT ---
            # Removed 'token=token' from the function call
            news_items = get_news(league_name=league_name)
            if news_items:
                all_news_items.extend(news_items)

    if not all_news_items:
        st.info("No news articles found for your selected leagues.")
    else:
        # 4. Sort all items by published date (newest first)
        all_news_items.sort(
            key=lambda x: datetime.fromisoformat(
                x["published_date"].replace("Z", "+00:00")
            ),
            reverse=True,
        )

        # 5. Display news items
        st.divider()
        for item in all_news_items[:50]:
            try:
                pub_date_utc = datetime.fromisoformat(
                    item["published_date"].replace("Z", "+00:00")
                )
                pub_date_local = pub_date_utc.astimezone(
                    pytz.timezone(
                        "America/New_York"
                    )  # You'll need to add 'pytz' to your pip install
                )

                st.html(
                    f"""
                <div class="news-card">
                    <div class="news-title">
                        <a href="{item['url']}" target="_blank">{item['title']}</a>
                    </div>
                    <div class="news-caption">
                        {item['source']} &bull; {pub_date_local.strftime('%b %d, %Y, %-I:%M %p %Z')}
                    </div>
                    <p class="news-summary">{item.get('summary', 'No summary available.')}...</p>
                </div>
                """
                )
            except (ValueError, TypeError, KeyError):
                st.markdown(
                    f"**[{item.get('title', 'Untitled')}]({item.get('url', '#')})**"
                )
                st.caption(
                    f"Source: {item.get('source', 'Unknown')} | Published: {item.get('published_date', 'Unknown')}"
                )
                st.divider()
