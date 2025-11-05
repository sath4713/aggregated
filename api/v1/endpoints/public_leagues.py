from typing import List
from fastapi import APIRouter
from core.config import LEAGUE_ID_MAP

router = APIRouter()


@router.get("/", response_model=List[str])
def get_available_leagues():
    """
    Returns a list of all available niche league names.
    (This is read from the config file).
    """
    # LEAGUE_ID_MAP should *only* contain your niche sports
    return sorted(list(LEAGUE_ID_MAP.keys()))
