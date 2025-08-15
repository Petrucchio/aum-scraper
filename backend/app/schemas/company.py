from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class CompanyBase(BaseModel):
    name: str
    url_site: Optional[str] = None
    url_linkedin: Optional[str] = None
    url_instagram: Optional[str] = None
    url_x: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    url_site: Optional[str] = None
    url_linkedin: Optional[str] = None
    url_instagram: Optional[str] = None
    url_x: Optional[str] = None

class Company(CompanyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True