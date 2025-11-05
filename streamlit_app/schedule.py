import streamlit as st
from datetime import datetime, timedelta

# --- ✂️ FAT CUT ---
# Removed 'auth' import
# Removed 'get_preferences'
# We now get the *public* schedule and *all* leagues
from api_client import get_schedule, get_all_leagues

# Set page config as the first Streamlit command
st.set_page_config(page_title="The Aggregate", page_icon="", layout="wide")
# --- ✂️ FAT CUT ---
# Removed all auth.initialize_session() and token logic

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

# --- ✂️ FAT CUT ---
# Removed the entire 'if token:' and 'else:' wrapper.
# This page is now 100% public.

st.title("The Aggregate")
st.subheader("Schedule")

# --- 1. Fetch Public Data (No Token) ---
schedule_data = get_schedule()
all_league_names = get_all_leagues()
# --- END ---

# --- 2. Setup Sidebar Filter ---
if all_league_names:
    filter_options = ["All Sports"] + all_league_names
else:
    filter_options = ["All Sports"]  # Fallback if API fails

with st.sidebar:
    st.header("Filter Options")
    selected_league = st.selectbox("Filter by league:", options=filter_options)
# --- END ---


# --- 3. Date Picker Controls (Unchanged) ---
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
# --- END ---


# --- 4. Main Schedule Display Logic ---
if schedule_data:
    # --- Filtering Logic (Unchanged) ---
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
        local_time = utc_time.astimezone()  # Uses local timezone of the server/browser
        if local_time.date() == current_date:
            final_schedule.append(game)

    st.header(
        f"Schedule for {selected_league} - {current_date.strftime('%a, %b %d, %Y')}"
    )

    if not final_schedule:
        st.info(f"No upcoming games found for '{selected_league}' on this date.")

    # --- Status Definitions (Unchanged) ---
    LIVE_STATES = {"STATUS_IN_PROGRESS", "STATUS_HALFTIME"}
    FINAL_STATES = {"STATUS_FINAL", "STATUS_FULL_TIME"}

    for game in final_schedule:
        with st.container(border=True):
            # --- This logic is now the key! ---
            # It correctly handles niche sports by checking if away_team is missing
            is_team_sport = game.get("away_team") and game.get("away_team") != "TBD"
            game_status = game.get("status", "STATUS_SCHEDULED")

            if is_team_sport:
                # --- This block is for future use (if you add a team sport) ---
                col1, col2, col3, col4 = st.columns([2, 1, 2, 3])
                with col1:
                    if game.get("logo_away"):
                        st.image(game["logo_away"], width=70)
                    st.markdown(
                        f"<div class='team-name'>{game['away_team']}</div>",
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.markdown("vs")
                with col3:
                    if game.get("logo_home"):
                        st.image(game["logo_home"], width=70)
                    st.markdown(
                        f"<div class='team-name'>{game['home_team']}</div>",
                        unsafe_allow_html=True,
                    )
                with col4:
                    if game_status in LIVE_STATES:
                        # ... (rest of your live/final logic) ...
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

            else:
                # --- THIS BLOCK IS FOR NICHE SPORTS (Cycling, Track, etc.) ---
                col1, col2 = st.columns([4, 3])
                with col1:
                    # We use 'home_team' as the main event name
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
                        st.write(game.get("status_detail_short", ""))
                    elif game_status in FINAL_STATES:
                        st.markdown(
                            '<div class="status-final">Final</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.write("**Time (Local)**")
                        st.write(game["start_time_local"])
                # --- END OF NICHE SPORT LOGIC ---

            with st.expander("More Info"):
                st.write(f"**Status:** {game['status']}")
                st.write(f"**Venue:** {game.get('venue', 'N/A')}")
                st.write(f"**League:** {game.get('league', 'N/A')}")
                if game.get("official_url"):
                    st.markdown(f"[View on source]({game['official_url']})")

else:
    # --- ✂️ FAT CUT ---
    # Simplified the error logic
    if schedule_data is None:
        # This means the API client returned None (e.g., connection error)
        st.error(
            "Failed to fetch schedule: The backend API may be offline or starting up."
        )
    else:
        # This means the API returned an empty list []
        st.info("No upcoming games found in any of the configured leagues.")
