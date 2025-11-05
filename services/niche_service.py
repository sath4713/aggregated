from datetime import datetime
import logging
import feedparser
from typing import List
import pytz
import requests
from bs4 import BeautifulSoup
import re

# Pydantic models for data validation
from models.game import Game as PydanticGame
from models.news import NewsItem

# Config for RSS feeds
from core.config import RSS_FEEDS

# --- Cycling Scraper (Unchanged) ---
def _scrape_cycling_schedule(year: int) -> List[PydanticGame]:
    logging.info(
        f"SCRAPER: Fetching cycling schedule from ProCyclingStats for {year}..."
    )
    scraped_games = []
    URL = f"https://www.procyclingstats.com/races.php?year={year}&circuit=1,2&race_type=1&_im_show_all=1"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(URL, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")
        table = soup.find("table", class_="basic")
        if not table:
            logging.error("SCRAPER ERROR: Could not find cycling schedule table.")
            return []

        for row in table.find_all("tr")[1:]:
            columns = row.find_all("td")
            if len(columns) < 4:
                continue
            try:
                link_tag = columns[2].find("a")
                if not link_tag or "race/" not in link_tag.get("href", ""):
                    continue
                race_name = link_tag.text.strip()
                race_link = "https://www.procyclingstats.com/" + link_tag["href"]
                date_str = columns[0].text.strip()
                category = columns[3].text.strip()
                start_day_str, end_day_str, month_str = "", "", ""
                if "-" in date_str:
                    parts = date_str.split("-")
                    start_day_str = parts[0].split(".")[0].strip()
                    end_day_str = parts[1].split(".")[0].strip()
                    month_str = parts[0].split(".")[1].strip()
                else:
                    parts = date_str.split(".")
                    start_day_str = parts[0].strip()
                    month_str = parts[1].strip()
                    end_day_str = start_day_str

                start_day = int(start_day_str)
                end_day = int(end_day_str)
                month = int(month_str)
                stage_number = 1

                for day in range(start_day, end_day + 1):
                    try:
                        start_time_obj = datetime(year, month, day, hour=8)
                        utc_start_time = pytz.utc.localize(start_time_obj)
                    except ValueError:
                        logging.warning(f"SCRAPER: Invalid date: {year}-{month}-{day}")
                        continue

                    event_name = race_name
                    if start_day != end_day:
                        event_name = f"{race_name} - Stage {stage_number}"

                    game_id = f"PCS_{year}_{race_name.replace(' ', '_')}_{day}"

                    scraped_games.append(
                        PydanticGame(
                            game_id=game_id,
                            league="Cycling - World Tour",
                            home_team=event_name,
                            away_team=None,
                            start_time=utc_start_time,
                            status="Scheduled",
                            venue=f"UCI {category}",
                            official_url=race_link,
                        )
                    )
                    stage_number += 1
            except (ValueError, IndexError, AttributeError, TypeError) as e:
                logging.warning(f"SCRAPER: Could not parse cycling row: {e}")
                continue
    except requests.RequestException as e:
        logging.critical(f"SCRAPER: Could not fetch ProCyclingStats page: {e}")
        return []

    logging.info(f"SCRAPER: Found {len(scraped_games)} cycling stages for {year}.")
    return scraped_games


# --- Track Scraper (Unchanged) ---
def _scrape_wikipedia_for_year(year: int) -> List[PydanticGame]:
    logging.info(
        f"SCRAPER: Fetching Diamond League schedule from Wikipedia for {year}..."
    )
    scraped_games = []
    URL = f"https://en.wikipedia.org/wiki/{year}_Diamond_League"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(URL, headers=headers, timeout=15)
        if response.status_code == 404:
            logging.warning(f"SCRAPER: No Wikipedia page found for {year}.")
            return []
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")
        schedule_table = None
        all_tables = soup.find_all("table", class_="wikitable")
        for table in all_tables:
            headers = [th.text.strip() for th in table.find_all("th")]
            if "Date" in headers and "Meet" in headers and "Stadium" in headers:
                schedule_table = table
                break
        if not schedule_table:
            logging.error(f"SCRAPER ERROR: Could not find schedule table for {year}.")
            return []

        for row in schedule_table.find("tbody").find_all("tr"):
            columns = row.find_all("td")
            if len(columns) < 4:
                continue
            try:
                date_str = columns[1].text.strip()
                start_time_obj = None
                possible_formats = ["%d %B %Y", "%d %b %Y"]
                date_str_cleaned = date_str.split("–")[0].strip()

                for fmt in possible_formats:
                    try:
                        start_time_obj = datetime.strptime(
                            f"{date_str_cleaned} {year}", fmt
                        ).replace(hour=12)
                        break
                    except ValueError:
                        continue
                if not start_time_obj:
                    match_day_month = re.search(
                        r"(\d+)\s*([A-Za-z]+)", date_str_cleaned
                    )
                    if match_day_month:
                        day, month_name = match_day_month.groups()
                        try:
                            month_num = datetime.strptime(month_name, "%B").month
                            start_time_obj = datetime(
                                year, month_num, int(day), hour=12
                            )
                        except ValueError:
                            try:
                                month_num = datetime.strptime(month_name, "%b").month
                                start_time_obj = datetime(
                                    year, month_num, int(day), hour=12
                                )
                            except ValueError:
                                logging.warning(f"Could not parse date: {date_str}.")
                                continue
                    else:
                        logging.warning(f"Could not parse date: {date_str}.")
                        continue

                utc_start_time = pytz.utc.localize(start_time_obj)
                meet_link_tag = columns[2].find("a")
                meet_name = (
                    meet_link_tag.text.strip()
                    if meet_link_tag
                    else columns[2].text.strip()
                )
                meet_url = (
                    ("https://en.wikipedia.org" + meet_link_tag["href"])
                    if meet_link_tag and meet_link_tag.get("href")
                    else None
                )
                stadium = columns[3].text.strip()
                city_country = columns[4].text.strip()

                scraped_games.append(
                    PydanticGame(
                        game_id=f"DL_WIKI_{year}_{meet_name.replace(' ', '_')}",
                        league="Track & Field - Diamond League",
                        home_team=meet_name,
                        away_team=None,
                        start_time=utc_start_time,
                        status="Scheduled",
                        venue=f"{stadium}, {city_country}",
                        official_url=meet_url,
                    )
                )
            except (ValueError, IndexError, AttributeError, TypeError) as e:
                logging.warning(f"SCRAPER: Could not parse track row: {e}.")
                continue
    except requests.RequestException as e:
        logging.critical(f"SCRAPER: Could not fetch Wikipedia page for {year}: {e}")
        return []
    logging.info(f"SCRAPER: Found {len(scraped_games)} track events for {year}.")
    return scraped_games


# --- Climbing Scraper (Unchanged) ---
def _scrape_climbing_wikipedia(year: int) -> List[PydanticGame]:
    logging.info(
        f"SCRAPER: Fetching IFSC Climbing schedule from Wikipedia for {year}..."
    )
    scraped_games = []
    URL = f"https://en.wikipedia.org/wiki/{year}_IFSC_Climbing_World_Cup"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(URL, headers=headers, timeout=15)
        if response.status_code == 404:
            logging.warning(
                f"SCRAPER: No Wikipedia page found for {year} IFSC World Cup."
            )
            return []
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")

        overview_header = soup.find(id="Overview")
        if not overview_header:
            overview_header = soup.find("span", class_="mw-headline", string="Overview")
        if not overview_header:
            logging.error(
                f"SCRAPER ERROR: Could not find 'Overview' section for {year}."
            )
            return []
        schedule_table = overview_header.find_next("table", class_="wikitable")
        if not schedule_table:
            logging.error(
                f"SCRAPER ERROR: Could not find wikitable after 'Overview' for {year}."
            )
            return []

        headers = [
            th.get_text(strip=True).lower() for th in schedule_table.find_all("th")
        ]
        date_loc_col, disc_col_start = -1, -1
        try:
            if "location" in headers:
                date_loc_col = headers.index("location")
            elif len(headers) > 1:
                date_loc_col = 1
            else:
                raise ValueError("Not enough headers")
            for i, h in enumerate(headers):
                if h in ["boulder", "lead", "speed"]:
                    disc_col_start = i
                    break
            if disc_col_start == -1:
                raise ValueError("Could not find discipline columns")
        except ValueError as e:
            logging.error(f"SCRAPER ERROR: Could not find columns for {year}: {e}")
            return []

        current_month = datetime.now().month

        for row in schedule_table.find("tbody").find_all("tr"):
            columns = row.find_all(["td", "th"])
            if len(columns) <= max(date_loc_col, disc_col_start):
                continue
            if columns[0].name == "th" and columns[date_loc_col].name == "th":
                continue
            if columns[date_loc_col].name != "td":
                continue

            try:
                date_loc_cell = columns[date_loc_col]
                date_str, city, country, disciplines_str = (
                    "",
                    "Unknown City",
                    "Unknown Country",
                    "B, L, S",
                )
                location_tag = date_loc_cell.find("a")
                city = location_tag.get_text(strip=True) if location_tag else city
                country_text = ""
                node = location_tag.next_sibling if location_tag else None
                while node:
                    if isinstance(node, str) and node.strip():
                        country_text = node.strip().split("[")[0].strip()
                        break
                    node = node.next_sibling
                country = country_text if country_text else country
                br_tag = date_loc_cell.find("br")
                node = br_tag.next_sibling if br_tag else None
                while node:
                    if isinstance(node, str) and node.strip():
                        date_str = node.strip()
                        break
                    node = node.next_sibling
                if not date_str:
                    date_str_search = (
                        date_loc_cell.get_text(strip=True, separator=" ")
                        .split(city)[-1]
                        .strip()
                    )
                    date_pattern_match = re.search(
                        r"(\d{1,2}(?:[–-])?\d{1,2}\s+[A-Za-z]+)", date_str_search
                    )
                    if date_pattern_match:
                        date_str = date_pattern_match.group(1)
                    else:
                        continue

                disciplines = []
                for i in range(disc_col_start, len(columns)):
                    cell_text = columns[i].get_text(strip=True)
                    if cell_text and cell_text not in ["–", "TBA"]:
                        disciplines.append(headers[i].capitalize())
                if disciplines:
                    disciplines_str = ", ".join(disciplines)

                event_name = f"IFSC World Cup {city}"
                full_location = f"{city}, {country}".replace(
                    ", Unknown Country", ""
                ).strip()
                date_match = re.search(
                    r"(\d{1,2})(?:[–-])?(\d{1,2})?\s+([A-Za-z]+)", date_str
                )
                if not date_match:
                    continue
                start_day = int(date_match.group(1))
                month_name = date_match.group(3)

                try:
                    month_num = datetime.strptime(month_name, "%B").month
                except ValueError:
                    try:
                        month_num = datetime.strptime(month_name, "%b").month
                    except ValueError:
                        continue

                event_year = year
                if (
                    year == datetime.now().year and month_num < current_month - 6
                ):
                    event_year = year + 1

                start_time_obj = datetime(
                    event_year, month_num, start_day, hour=9
                )
                utc_start_time = pytz.utc.localize(start_time_obj)

                game_id = f"IFSC_WIKI_{event_year}_{month_num}_{start_day}_{city.replace(' ', '_')}"
                venue_details = f"{full_location} ({disciplines_str})"

                scraped_games.append(
                    PydanticGame(
                        game_id=game_id,
                        league="World Cup Rock Climbing",
                        home_team=event_name,
                        away_team=None,
                        start_time=utc_start_time,
                        status="Scheduled",
                        venue=venue_details,
                        official_url=URL,
                    )
                )
            except Exception as e:
                logging.error(f"SCRAPER: Unhandled error parsing climbing row: {e}.")
                continue
    except requests.RequestException as e:
        logging.critical(f"SCRAPERS: Could not fetch Wikipedia page for {year}: {e}")
        return []

    logging.info(f"SCRAPER: Found {len(scraped_games)} climbing events for {year}.")
    return scraped_games


# --- ✂️ F1 API FUNCTION REMOVED ---
# --- ✂️ _get_f1_schedule FUNCTION REMOVED ---


# --- Helper Functions (Public) ---

def _filter_upcoming(games: List[PydanticGame]) -> List[PydanticGame]:
    """Helper to filter a list of games for only upcoming events."""
    now = datetime.now(pytz.utc)
    return [g for g in games if g.start_time >= now]


def _scrape_diamond_league_from_wikipedia() -> List[PydanticGame]:
    now = datetime.now(pytz.utc)
    current_year = now.year
    games_current_year = _scrape_wikipedia_for_year(current_year)
    upcoming_games = _filter_upcoming(games_current_year)

    if not upcoming_games:
        logging.info(f"Track season {current_year} over. Checking {current_year + 1}.")
        games_next_year = _scrape_wikipedia_for_year(current_year + 1)
        return _filter_upcoming(games_next_year)
    return upcoming_games


def _get_cycling_schedule() -> List[PydanticGame]:
    now = datetime.now(pytz.utc)
    current_year = now.year
    games_current_year = _scrape_cycling_schedule(current_year)
    upcoming_games = _filter_upcoming(games_current_year)

    if not upcoming_games:
        logging.info(
            f"Cycling season {current_year} over. Checking {current_year + 1}."
        )
        games_next_year = _scrape_cycling_schedule(current_year + 1)
        return _filter_upcoming(games_next_year)
    return upcoming_games


def _get_climbing_schedule() -> List[PydanticGame]:
    now = datetime.now(pytz.utc)
    current_year = now.year
    games_current_year = _scrape_climbing_wikipedia(current_year)
    upcoming_games = _filter_upcoming(games_current_year)

    if not upcoming_games:
        # --- THIS IS THE FIX ---
        # The following lines are now correctly indented
        logging.info(
            f"Climbing season {current_year} over. Checking {current_year + 1}."
        )
        games_next_year = _scrape_climbing_wikipedia(current_year + 1)
        return _filter_upcoming(games_next_year)
        # --- END FIX ---

    return upcoming_games


# --- News Fetch Function (Unchanged) ---
def fetch_niche_news(league_name: str) -> List[NewsItem]:
    rss_url_list = RSS_FEEDS.get(league_name)
    if not rss_url_list:
        logging.warning(f"No RSS feed URL(s) found for {league_name}.")
        return []
    if isinstance(rss_url_list, str):
        rss_url_list = [rss_url_list]

    all_items = []
    SOURCE_NAME = league_name
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."

    for RSS_URL in rss_url_list:
        try:
            feed = feedparser.parse(RSS_URL, agent=user_agent)
            if not feed.entries:
                if feed.bozo:
                    logging.warning(
                        f"RSS feed for {league_name} ({RSS_URL}) is malformed."
                    )
                else:
                    logging.warning(f"RSS feed for {league_name} ({RSS_URL}) is empty.")
                continue
        except Exception as e:
            logging.error(f"RSS feed fetch failed for {league_name} ({RSS_URL}): {e}")
            continue

        for entry in feed.entries:
            try:
                pub_parsed = entry.get("published_parsed")
                pub_time = (
                    datetime(*(pub_parsed[:6]))
                    if pub_parsed
                    else datetime.now()
                )
                if pub_time.tzinfo is None:
                    utc_pub_time = pytz.utc.localize(pub_time)
                else:
                    utc_pub_time = pub_time.astimezone(pytz.utc)

                all_items.append(
                    NewsItem(
                        title=entry.get("title", "Untitled"),
                        summary=re.sub(
                            "<[^<]+?>",
                            "",
                            entry.get("summary", "No summary available."),
                        )[:250],
                        url=entry.link,
                        source=SOURCE_NAME,
                        published_date=utc_pub_time,
                    )
                )
            except Exception as e:
                logging.warning(f"Could not parse RSS entry: {e}")
                continue

    logging.info(f"Found {len(all_items)} news items for {league_name}.")
    return all_items
