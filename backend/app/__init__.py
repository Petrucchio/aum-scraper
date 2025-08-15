# AUM Scraper Application
"""
Sistema backend para coleta automatizada de Patrimônio Sob Gestão (AUM)
de empresas do mercado financeiro através de scraping web e extração via IA.

Módulos principais:
- api: Rotas da API REST com FastAPI
- core: Configurações e banco de dados  
- models: Modelos SQLAlchemy (ORM)
- schemas: Schemas Pydantic para validação
- services: Lógica de negócio (scraping, IA, etc.)
- utils: Funções utilitárias auxiliares
"""

__version__ = "1.0.0"
__author__ = "AUM Scraper Team"
__description__ = "Sistema backend para coleta automatizada de Patrimônio Sob Gestão (AUM)"

# Versões de dependências importantes
__fastapi_version__ = "0.104.1"
__sqlalchemy_version__ = "2.0.23"
__pydantic_version__ = "2.5.0"

# Configurações da aplicação
APP_NAME = "AUM Scraper Backend"
API_VERSION = "v1"