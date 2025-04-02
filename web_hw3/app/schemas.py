from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class LinkCreate(BaseModel):
    original_url: str
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkResponse(LinkCreate):
    short_code : str
    created_at : datetime
    is_active: bool