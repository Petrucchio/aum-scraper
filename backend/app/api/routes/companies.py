from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.core.database import get_db
from app.models.company import Company
from app.models.aum_snapshot import AUMSnapshot
from app.schemas import Company as CompanySchema, AUMSnapshot as AUMSnapshotSchema
from app.services.csv_reader import CSVReader
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/companies",
    tags=["companies"]
)

@router.get("/", response_model=List[CompanySchema])
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Lista todas as empresas cadastradas"""
    result = await db.execute(
        select(Company)
        .offset(skip)
        .limit(limit)
        .order_by(Company.name)
    )
    
    companies = result.scalars().all()
    return companies

@router.get("/{company_id}", response_model=CompanySchema)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Obtém detalhes de uma empresa específica"""
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    return company

@router.get("/{company_id}/aum-history", response_model=List[AUMSnapshotSchema])
async def get_company_aum_history(
    company_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Obtém histórico de AUM de uma empresa"""
    # Verificar se empresa existe
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    # Buscar histórico de AUM
    result = await db.execute(
        select(AUMSnapshot)
        .where(AUMSnapshot.company_id == company_id)
        .order_by(AUMSnapshot.extracted_at.desc())
    )
    
    aum_snapshots = result.scalars().all()
    return aum_snapshots

@router.get("/{company_id}/latest-aum")
async def get_company_latest_aum(
    company_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Obtém o AUM mais recente de uma empresa"""
    # Verificar se empresa existe
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    # Buscar AUM mais recente
    result = await db.execute(
        select(AUMSnapshot)
        .where(AUMSnapshot.company_id == company_id)
        .order_by(AUMSnapshot.extracted_at.desc())
        .limit(1)
    )
    
    latest_aum = result.scalar_one_or_none()
    
    if not latest_aum:
        return {
            "company_id": company_id,
            "company_name": company.name,
            "aum_raw_text": "NAO_DISPONIVEL",
            "aum_normalized": None,
            "extracted_at": None,
            "message": "Nenhum AUM encontrado para esta empresa"
        }
    
    return {
        "company_id": company_id,
        "company_name": company.name,
        "aum_raw_text": latest_aum.aum_raw_text,
        "aum_normalized": latest_aum.aum_normalized,
        "confidence_score": latest_aum.confidence_score,
        "source_url": latest_aum.source_url,
        "extraction_method": latest_aum.extraction_method,
        "extracted_at": latest_aum.extracted_at
    }

@router.post("/load-from-csv")
async def load_companies_from_csv(
    db: AsyncSession = Depends(get_db)
):
    """Carrega empresas do arquivo CSV"""
    try:
        csv_reader = CSVReader()
        companies = await csv_reader.load_companies_to_db(db)
        
        return {
            "message": f"Empresas carregadas com sucesso",
            "total_companies": len(companies),
            "companies": [{"id": c.id, "name": c.name} for c in companies]
        }
        
    except Exception as e:
        logger.error(f"Erro ao carregar CSV: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar empresas do CSV: {str(e)}"
        )

@router.get("/stats/summary")
async def get_companies_summary(
    db: AsyncSession = Depends(get_db)
):
    """Retorna estatísticas resumidas das empresas"""
    
    # Total de empresas
    result = await db.execute(select(Company))
    total_companies = len(result.scalars().all())
    
    # Empresas com AUM
    result = await db.execute(
        select(AUMSnapshot)
        .where(AUMSnapshot.aum_normalized.isnot(None))
        .distinct(AUMSnapshot.company_id)
    )
    companies_with_aum = len(result.scalars().all())
    
    # AUM total
    result = await db.execute(
        select(AUMSnapshot.aum_normalized)
        .where(AUMSnapshot.aum_normalized.isnot(None))
    )
    aum_values = [float(value) for value in result.scalars().all() if value]
    
    total_aum = sum(aum_values) if aum_values else 0
    avg_aum = total_aum / len(aum_values) if aum_values else 0
    
    return {
        "total_companies": total_companies,
        "companies_with_aum": companies_with_aum,
        "success_rate": companies_with_aum / total_companies if total_companies > 0 else 0,
        "total_aum": total_aum,
        "average_aum": avg_aum,
        "max_aum": max(aum_values) if aum_values else 0,
        "min_aum": min(aum_values) if aum_values else 0
    }