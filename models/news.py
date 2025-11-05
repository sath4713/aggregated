from pydantic import BaseModel
from typing import Optional
import datetime


class NewsItem(BaseModel):
    title: str
    summary: Optional[str] = None
    url: str
    source: str
    published_date: datetime.datetime
