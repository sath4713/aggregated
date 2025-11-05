import streamlit as st
from datetime import datetime
import pytz

from api_client import get_news, get_all_leagues

# 1. Updated Browser Tab Title
st.set_page_config(page_title="The Aggregate - News", page_icon="📰")

# 2. Updated Page Title & Subheader
st.title("The Aggregate")
st.subheader("📰 News")

# --- Session Caching Logic (Part 1) ---
if st.button("Refresh News"):
    if "news_data" in st.session_state:
        del st.session_state["news_data"]
    if "news_leagues" in st.session_state:
        del st.session_state["news_leagues"]
    st.rerun()

# --- Custom CSS (Unchanged) ---
st.markdown(
    """
<style>
    /* ... (Your news card CSS) ... */
    .news-card {
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .news-title a {
        font-size: 1.25em;
        font-weight: 600;
        text-decoration: none;
    }
    .news-caption {
        font-size: 0.9em;
        margin-bottom: 8px;
    }
    /* ... (rest of your CSS) ... */
</style>
""",
    unsafe_allow_html=True,
)

# --- Session Caching Logic (Part 2) ---
# Only run this block if news is not already in the session
if "news_data" not in st.session_state:
    with st.spinner("Fetching latest news..."):
        all_news_items = []
        all_available_leagues = get_all_leagues()

        if not all_available_leagues:
            st.session_state["news_data"] = []
            st.session_state["news_leagues"] = []
        else:
            leagues_to_fetch_news_for = set()
            cycling_leagues = {"Cycling - World Tour", "Cycling - Pro Series"}

            for league in all_available_leagues:
                if league in cycling_leagues:
                    leagues_to_fetch_news_for.add("Cycling")
                else:
                    leagues_to_fetch_news_for.add(league)

            for league_name in leagues_to_fetch_news_for:
                news_items = get_news(league_name=league_name)
                if news_items:
                    all_news_items.extend(news_items)

            all_news_items.sort(
                key=lambda x: datetime.fromisoformat(
                    x["published_date"].replace("Z", "+00:00")
                ),
                reverse=True,
            )

            # Store results in the session
            st.session_state["news_data"] = all_news_items
            st.session_state["news_leagues"] = sorted(list(leagues_to_fetch_news_for))


# --- Read from the Session Cache (This is fast) ---
all_items_from_cache = st.session_state.get("news_data", [])
league_options = st.session_state.get("news_leagues", [])

if not all_items_from_cache:
    st.info("No news articles found.")
else:
    selected_leagues = st.multiselect(
        "Filter news by league:", options=league_options, default=league_options
    )

    final_filtered_items = []
    seen_urls = set()

    # Create a set of all the sources we want to show
    selected_sources = set(selected_leagues)

    # If "Cycling" is selected, make sure we also include
    # the specific league names, just in case.
    if "Cycling" in selected_sources:
        selected_sources.add("Cycling - World Tour")
        selected_sources.add("Cycling - Pro Series")

    for item in all_items_from_cache:
        if item["url"] in seen_urls:
            continue

        # This is the new, simple check.
        # If the item's source is in our set, add it.
        if item["source"] in selected_sources:
            final_filtered_items.append(item)
            seen_urls.add(item["url"])

    st.divider()

    if not final_filtered_items:
        st.info("No news articles found for your selected leagues.")

    for item in final_filtered_items[:50]:
        try:
            pub_date_utc = datetime.fromisoformat(
                item["published_date"].replace("Z", "+00:00")
            )
            pub_date_local = pub_date_utc.astimezone(pytz.timezone("America/New_York"))

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
