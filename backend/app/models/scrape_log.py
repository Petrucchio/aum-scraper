from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class ScrapeLog(Base):
    __tablename__ = "scrape_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    url = Column(String, nullable=False)
    status = Column(String, nullable=False)  # success, failed, blocked
    content_type = Column(String)  # site, linkedin, instagram, x, news
    scraped_content = Column(Text)
    error_message = Column(Text)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    
    company = relationship("Company", back_populates="scrape_logs")