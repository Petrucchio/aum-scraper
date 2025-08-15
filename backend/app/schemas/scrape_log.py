from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ScrapeLogBase(BaseModel):
    company_id: int
    url: str
    status: str
    content_type: Optional[str] = None
    scraped_content: Optional[str] = None
    error_message: Optional[str] = None

class ScrapeLogCreate(ScrapeLogBase):
    pass

class ScrapeLog(ScrapeLogBase):
    id: int
    scraped_at: datetime
    
    class Config:
        from_attributes = True