from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import companies, scraping, usage, auto_setup
from app.core.database import engine, Base
# Importar modelos para criação das tabelas
from app.models import Company, ScrapeLog, AUMSnapshot, Usage
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="AUM Scraper API",
    description="API para coleta e extração de Patrimônio Sob Gestão (AUM) de empresas do mercado financeiro",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origins específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(companies.router, prefix="/api/v1")
app.include_router(scraping.router, prefix="/api/v1")
app.include_router(usage.router, prefix="/api/v1")
app.include_router(auto_setup.router, prefix="/api/v1")  # NOVO!

@app.on_event("startup")
async def startup():
    """Executado na inicialização da aplicação"""
    logger.info("Iniciando aplicação AUM Scraper")
    
    # Criar tabelas no banco de dados
    try:
        async with engine.begin() as conn:
            # Em produção, usar Alembic para migrações
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Tabelas do banco de dados criadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown():
    """Executado no shutdown da aplicação"""
    logger.info("Encerrando aplicação AUM Scraper")
    await engine.dispose()

@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "AUM Scraper API está funcionando!",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "quick_start": {
            "1_demo_setup": "POST /api/v1/auto-setup/quick-demo-setup",
            "2_full_setup": "POST /api/v1/auto-setup/download-and-load-companies",
            "3_run_pipeline": "POST /api/v1/scraping/pipeline/full",
            "4_check_results": "GET /api/v1/companies/stats/summary"
        },
        "endpoints": {
            "companies": "/api/v1/companies",
            "scraping": "/api/v1/scraping", 
            "usage": "/api/v1/usage",
            "auto_setup": "/api/v1/auto-setup"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "aum-scraper",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ).basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="AUM Scraper API",
    description="API para coleta e extração de Patrimônio Sob Gestão (AUM) de empresas do mercado financeiro",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origins específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(companies.router, prefix="/api/v1")
app.include_router(scraping.router, prefix="/api/v1")
app.include_router(usage.router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    """Executado na inicialização da aplicação"""
    logger.info("Iniciando aplicação AUM Scraper")
    
    # Criar tabelas no banco de dados
    try:
        async with engine.begin() as conn:
            # Em produção, usar Alembic para migrações
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Tabelas do banco de dados criadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown():
    """Executado no shutdown da aplicação"""
    logger.info("Encerrando aplicação AUM Scraper")
    await engine.dispose()

@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "AUM Scraper API está funcionando!",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "companies": "/api/v1/companies",
            "scraping": "/api/v1/scraping", 
            "usage": "/api/v1/usage"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "aum-scraper",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )