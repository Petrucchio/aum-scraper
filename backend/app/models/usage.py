from sqlalchemy import Column, Integer, DateTime, Float, String, Text
from sqlalchemy.sql import func
from app.core.database import Base

class Usage(Base):
    __tablename__ = "usage"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    model_used = Column(String, default="gpt-4o")
    request_type = Column(String)  # aum_extraction, content_analysis
    created_at = Column(DateTime(timezone=True), server_default=func.now())