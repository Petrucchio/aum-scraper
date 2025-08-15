from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AUMSnapshotBase(BaseModel):
    company_id: int
    aum_raw_text: Optional[str] = None
    aum_normalized: Optional[float] = None
    source_url: Optional[str] = None
    source_content: Optional[str] = None
    extraction_method: Optional[str] = None
    confidence_score: Optional[float] = 0.0

class AUMSnapshotCreate(AUMSnapshotBase):
    pass

class AUMSnapshot(AUMSnapshotBase):
    id: int
    extracted_at: datetime
    
    class Config:
        from_attributes = True