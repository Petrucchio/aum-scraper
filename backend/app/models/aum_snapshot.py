from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class AUMSnapshot(Base):
    __tablename__ = "aum_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    aum_raw_text = Column(String)  # Ex: "R$ 2,3 bi"
    aum_normalized = Column(Float)  # Ex: 2.3e9
    source_url = Column(String)
    source_content = Column(Text)
    extraction_method = Column(String)  # gpt4o, regex
    confidence_score = Column(Float, default=0.0)
    extracted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    company = relationship("Company", back_populates="aum_snapshots")