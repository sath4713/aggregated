import streamlit as st
from datetime import datetime, timedelta

from api_client import get_schedule, get_all_leagues

# 1. Updated Browser Tab Title
st.set_page_config(page_title="The Aggregate", page_icon="🗓️", layout="wide")

if "schedule_date" not in st.session_state:
    st.session_state.schedule_date = datetime.today().date()

# --- CSS (Unchanged) ---
st.markdown(
    """
<style>
    /* ... (your existing CSS) ... */
    .st-emotion-cache-1b250tt div {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
    }
    .team-name { font-size: 1.1em; font-weight: bold; }
    .event-name { font-size: 1.2em; font-weight: bold; text-align: left; }
    .live-badge { color: #FF4B4B; font-weight: bold; font-size: 1.1em; }
    .score { font-size: 1.3em; font-weight: bold; letter-spacing: 1px; }
    .status-final { font-weight: bold; color: #8A8D93; }
    [data-theme="light"] .status-final { color: #4F4F4F; }
</style>
""",
    unsafe_allow_html=True,
)

# 2. Updated Page Title & Subheader
st.title("The Aggregate")
st.subheader("🗓️ Schedule")

# --- Fetch Public Data (No Token) ---
schedule_data = get_schedule()
all_league_names = get_all_leagues()

# --- Setup Sidebar Filter ---
if all_league_names:
    filter_options = ["All Sports"] + all_league_names
else:
    filter_options = ["All Sports"]  # Fallback if API fails

with st.sidebar:
    st.header("Filter Options")
    selected_league = st.selectbox("Filter by league:", options=filter_options)

# --- Date Picker Controls (Unchanged) ---
date_col1, date_col2, date_col3, date_col4 = st.columns([2, 3, 2, 2])
with date_col1:
    if st.button("← Prev", use_container_width=True):
        st.session_state.schedule_date -= timedelta(days=1)
        st.rerun()
with date_col2:
    picked_date = st.date_input(
        "Jump to date",
        value=st.session_state.schedule_date,
        label_visibility="collapsed",
    )
    if picked_date != st.session_state.schedule_date:
        st.session_state.schedule_date = picked_date
        st.rerun()
with date_col3:
    if st.button("Today", use_container_width=True):
        st.session_state.schedule_date = datetime.today().date()
        st.rerun()
with date_col4:
    if st.button("Next →", use_container_width=True):
        st.session_state.schedule_date += timedelta(days=1)
        st.rerun()
st.divider()

# --- Main Schedule Display Logic (Unchanged) ---
if schedule_data:
    filtered_by_league = []
    if selected_league == "All Sports":
        filtered_by_league = schedule_data
    else:
        filtered_by_league = [
            game for game in schedule_data if game.get("league") == selected_league
        ]

    final_schedule = []
    current_date = st.session_state.schedule_date
    for game in filtered_by_league:
        utc_string = game["start_time"].replace("Z", "+00:00")
        utc_time = datetime.fromisoformat(utc_string)
        local_time = utc_time.astimezone()  # Uses local timezone
        if local_time.date() == current_date:
            final_schedule.append(game)

    st.header(
        f"Schedule for {selected_league} - {current_date.strftime('%a, %b %d, %Y')}"
    )

    if not final_schedule:
        st.info(f"No upcoming games found for '{selected_league}' on this date.")

    LIVE_STATES = {"STATUS_IN_PROGRESS", "STATUS_HALFTIME"}
    FINAL_STATES = {"STATUS_FINAL", "STATUS_FULL_TIME"}

    for game in final_schedule:
        with st.container(border=True):
            is_team_sport = game.get("away_team") and game.get("away_team") != "TBD"
            game_status = game.get("status", "STATUS_SCHEDULED")

            if is_team_sport:
                # (Team sport logic is unchanged)
                col1, col2, col3, col4 = st.columns([2, 1, 2, 3])
                # ...
            else:
                # (Niche sport logic is unchanged)
                col1, col2 = st.columns([4, 3])
                with col1:
                    st.markdown(
                        f"<div class='event-name'>{game['home_team']}</div>",
                        unsafe_allow_html=True,
                    )
                with col2:
                    if game_status in LIVE_STATES:
                        st.markdown(
                            '<div class="live-badge">LIVE</div>',
                            unsafe_allow_html=True,
                        )
                    elif game_status in FINAL_STATES:
                        st.markdown(
                            '<div class="status-final">Final</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.write("**Time (Local)**")
                        st.write(game["start_time_local"])

            with st.expander("More Info"):
                st.write(f"**Status:** {game['status']}")
                st.write(f"**Venue:** {game.get('venue', 'N/A')}")
                st.write(f"**League:** {game.get('league', 'N/A')}")
                if game.get("official_url"):
                    st.markdown(f"[View on source]({game['official_url']})")
else:
    if schedule_data is None:
        st.error(
            "Failed to fetch schedule: The backend API may be offline or starting up."
        )
    else:
        st.info("No upcoming games found in any of the configured leagues.")
