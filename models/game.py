from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Game(BaseModel):
    game_id: str
    league: str
    start_time: datetime
    start_time_local: Optional[str] = None  # Added for display
    status: str

    # We will treat this as the "Event Name" for niche sports
    home_team: str

    # This being Optional is the key
    away_team: Optional[str] = None

    logo_home: Optional[str] = None
    logo_away: Optional[str] = None
    score_home: Optional[str] = None
    score_away: Optional[str] = None
    venue: Optional[str] = None
    official_url: Optional[str] = None

    # --- ✂️ FAT CUT ---
    # We removed the 'class Config' block
    # It was only needed for SQLAlchemy (from_attributes = True)
    # Since we have no database, it's no longer needed.
