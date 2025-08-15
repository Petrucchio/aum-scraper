from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class UsageBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    company_id: Optional[int] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    model_used: str = "gpt-4o"
    request_type: Optional[str] = None

class UsageCreate(UsageBase):
    pass

class Usage(UsageBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UsageSummary(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    budget_used_percentage: float
    remaining_budget_usd: float

class ScrapeResponse(BaseModel):
    message: str
    company_id: int
    status: str
    aum_found: Optional[str] = None