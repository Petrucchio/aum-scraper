#!/usr/bin/env python3
"""
Script para testar todas as importações antes de executar o Docker
Execute: python test_imports.py
"""

import sys
import traceback

def test_import(module_name, description):
    """Testa uma importação específica"""
    try:
        __import__(module_name)
        print(f"✅ {description}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {description}: {e}")
        return False

def main():
    """Testa todas as importações críticas"""
    print("🔍 Testando importações do projeto AUM Scraper...\n")
    
    # Dependências externas
    tests = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pydantic", "Pydantic"),
        ("requests", "Requests"),
        ("aiohttp", "AioHTTP"),
        ("beautifulsoup4", "BeautifulSoup4"),
        ("openai", "OpenAI"),
        ("pandas", "Pandas"),
        ("openpyxl", "OpenPyXL"),
        ("pytest", "Pytest"),
        ("tiktoken", "TikToken"),
    ]
    
    print("📦 Testando dependências externas:")
    external_ok = 0
    for module, desc in tests:
        if test_import(module, desc):
            external_ok += 1
    
    print(f"\n📊 Dependências externas: {external_ok}/{len(tests)} OK\n")
    
    # Módulos internos
    print("🏠 Testando módulos internos:")
    internal_tests = [
        ("app.core.config", "Configurações"),
        ("app.core.database", "Banco de dados"),
        ("app.models", "Modelos"),
        ("app.schemas", "Schemas"),
        ("app.services", "Serviços"),
        ("app.utils", "Utilitários"),
        ("app.api.routes.companies", "Rotas Companies"),
        ("app.api.routes.scraping", "Rotas Scraping"),
        ("app.api.routes.usage", "Rotas Usage"),
    ]
    
    internal_ok = 0
    for module, desc in internal_tests:
        if test_import(module, desc):
            internal_ok += 1
    
    print(f"\n📊 Módulos internos: {internal_ok}/{len(internal_tests)} OK\n")
    
    # Teste final: importar main app
    print("🚀 Testando aplicação principal:")
    try:
        from app.main import app
        print("✅ Aplicação FastAPI carregada com sucesso!")
        main_ok = True
    except Exception as e:
        print(f"❌ Erro ao carregar aplicação: {e}")
        traceback.print_exc()
        main_ok = False
    
    # Resumo
    total_tests = len(tests) + len(internal_tests) + 1
    total_ok = external_ok + internal_ok + (1 if main_ok else 0)
    
    print(f"\n{'='*50}")
    print(f"📈 RESUMO: {total_ok}/{total_tests} testes passaram")
    
    if total_ok == total_tests:
        print("🎉 Todos os testes passaram! Projeto pronto para execução.")
        return 0
    else:
        print("❌ Alguns testes falharam. Verifique as dependências.")
        return 1

if __name__ == "__main__":
    sys.exit(main())