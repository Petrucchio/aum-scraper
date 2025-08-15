from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models.company import Company
from app.services.scraper import WebScraper
from app.services.ai_extractor import AIExtractor
from app.services.excel_exporter import ExcelExporter
from app.services.csv_reader import CSVReader
from app.schemas import ScrapeResponse
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/scraping",
    tags=["scraping"]
)

@router.post("/company/{company_id}", response_model=ScrapeResponse)
async def scrape_company(
    company_id: int,
    use_playwright: bool = False,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """Executa scraping manual para uma empresa específica"""
    
    # Verificar se a empresa existe
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    try:
        # Executar scraping
        scraper = WebScraper()
        scraped_data = await scraper.scrape_company_urls(company, db, use_playwright)
        
        # Executar extração de AUM
        ai_extractor = AIExtractor()
        aum_snapshot = await ai_extractor.extract_aum_from_content(company, scraped_data, db)
        
        return ScrapeResponse(
            message="Scraping executado com sucesso",
            company_id=company_id,
            status="success",
            aum_found=aum_snapshot.aum_raw_text if aum_snapshot else "NAO_DISPONIVEL"
        )
        
    except Exception as e:
        logger.error(f"Erro no scraping da empresa {company_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro durante o scraping: {str(e)}"
        )

@router.post("/all-companies")
async def scrape_all_companies(
    use_playwright: bool = False,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """Executa scraping para todas as empresas"""
    
    # Buscar todas as empresas
    result = await db.execute(select(Company))
    companies = result.scalars().all()
    
    if not companies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma empresa encontrada. Execute /companies/load-from-csv primeiro."
        )
    
    try:
        # Executar em background se solicitado
        if background_tasks:
            background_tasks.add_task(
                _process_all_companies, 
                companies, 
                use_playwright, 
                db
            )
            
            return {
                "message": f"Scraping iniciado em background para {len(companies)} empresas",
                "total_companies": len(companies),
                "status": "processing"
            }
        else:
            # Executar sincronamente (para demonstração)
            results = await _process_all_companies(companies, use_playwright, db)
            
            successful = len([r for r in results if r.get("status") == "success"])
            
            return {
                "message": "Scraping concluído para todas as empresas",
                "total_companies": len(companies),
                "successful": successful,
                "failed": len(companies) - successful,
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Erro no scraping de todas as empresas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro durante o scraping: {str(e)}"
        )

@router.post("/pipeline/full")
async def run_full_pipeline(
    use_playwright: bool = False,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """Executa pipeline completo: carrega CSV + scraping + extração AUM"""
    
    try:
        # 1. Carregar empresas do CSV
        csv_reader = CSVReader()
        companies = await csv_reader.load_companies_to_db(db)
        
        logger.info(f"Carregadas {len(companies)} empresas do CSV")
        
        # 2. Executar scraping e extração
        if background_tasks:
            background_tasks.add_task(
                _process_all_companies,
                companies,
                use_playwright,
                db
            )
            
            return {
                "message": "Pipeline completo iniciado em background",
                "companies_loaded": len(companies),
                "status": "processing"
            }
        else:
            results = await _process_all_companies(companies, use_playwright, db)
            successful = len([r for r in results if r.get("status") == "success"])
            
            return {
                "message": "Pipeline completo executado com sucesso",
                "companies_loaded": len(companies),
                "companies_processed": len(results),
                "successful_extractions": successful,
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Erro no pipeline completo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no pipeline: {str(e)}"
        )

@router.get("/export/excel")
async def export_results_to_excel(
    db: AsyncSession = Depends(get_db)
):
    """Exporta resultados para Excel"""
    
    try:
        exporter = ExcelExporter()
        excel_data = await exporter.export_results(db)
        
        filename = exporter.get_filename()
        
        return Response(
            content=excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Erro ao exportar Excel: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na exportação: {str(e)}"
        )

@router.get("/status")
async def get_scraping_status(
    db: AsyncSession = Depends(get_db)
):
    """Retorna status atual do scraping"""
    
    from app.models.scrape_log import ScrapeLog
    from app.models.usage import Usage
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Logs de hoje
    result = await db.execute(
        select(
            ScrapeLog.status,
            func.count(ScrapeLog.id).label('count')
        )
        .where(
            ScrapeLog.scraped_at >= today,
            ScrapeLog.scraped_at < tomorrow
        )
        .group_by(ScrapeLog.status)
    )
    
    scraping_stats = {row.status: row.count for row in result}
    
    # Uso de API hoje
    result = await db.execute(
        select(
            func.count(Usage.id).label('requests'),
            func.sum(Usage.total_tokens).label('tokens'),
            func.sum(Usage.cost_usd).label('cost')
        )
        .where(
            Usage.created_at >= today,
            Usage.created_at < tomorrow
        )
    )
    
    usage_stats = result.first()
    
    return {
        "scraping_today": {
            "successful": scraping_stats.get("success", 0),
            "failed": scraping_stats.get("failed", 0),
            "blocked": scraping_stats.get("blocked", 0)
        },
        "api_usage_today": {
            "requests": usage_stats.requests or 0,
            "tokens": int(usage_stats.tokens or 0),
            "cost_usd": float(usage_stats.cost or 0)
        },
        "timestamp": datetime.now().isoformat()
    }

async def _process_all_companies(
    companies: List[Company],
    use_playwright: bool,
    db: AsyncSession
) -> List[dict]:
    """Função auxiliar para processar todas as empresas"""
    
    scraper = WebScraper()
    ai_extractor = AIExtractor()
    
    results = []
    
    for i, company in enumerate(companies):
        logger.info(f"Processando empresa {i+1}/{len(companies)}: {company.name}")
        
        try:
            # Scraping
            scraped_data = await scraper.scrape_company_urls(company, db, use_playwright)
            
            # Extração AUM
            aum_snapshot = await ai_extractor.extract_aum_from_content(company, scraped_data, db)
            
            results.append({
                "company_id": company.id,
                "company_name": company.name,
                "status": "success",
                "aum_found": aum_snapshot.aum_raw_text if aum_snapshot else "NAO_DISPONIVEL"
            })
            
        except Exception as e:
            logger.error(f"Erro processando {company.name}: {str(e)}")
            results.append({
                "company_id": company.id,
                "company_name": company.name,
                "status": "failed",
                "error": str(e)
            })
        
        # Pequeno delay entre empresas
        await asyncio.sleep(1)
    
    return results