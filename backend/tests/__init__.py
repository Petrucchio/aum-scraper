# Tests package for AUM Scraper
"""
Pacote de testes para o AUM Scraper.

Estrutura:
- test_api/: Testes das rotas da API
- test_services/: Testes dos serviços de negócio  
- test_utils/: Testes das funções utilitárias
- conftest.py: Fixtures compartilhadas
"""

import pytest
import asyncio

# Configurar asyncio para testes
pytest_plugins = ['pytest_asyncio']