from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://scraper:scraperpw@db:5432/scraperdb"
    
    # OpenAI
    openai_api_key: str = "chave-open-ai-aqui"
    openai_model: str = "gpt-4o"
    max_tokens_per_request: int = 1500
    
    # Budget
    daily_budget_usd: float = 50.0
    budget_alert_threshold: float = 0.8  # 80%
    
    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    
    # Scraping
    max_concurrent_requests: int = 3
    request_delay: float = 1.0
    
    # Paths
    csv_file_path: str = "companies.csv"
    
    class Config:
        env_file = ".env"

settings = Settings()