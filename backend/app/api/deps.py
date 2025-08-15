"""
Dependências comuns para as rotas da API
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.budget_controller import BudgetController
import logging

logger = logging.getLogger(__name__)

async def get_budget_controller() -> BudgetController:
    """Dependency para obter uma instância do BudgetController"""
    return BudgetController()

async def check_budget_dependency(
    db: AsyncSession = Depends(get_db),
    budget_controller: BudgetController = Depends(get_budget_controller)
) -> BudgetController:
    """
    Dependency que verifica se ainda há budget disponível
    Usado em endpoints que consomem API OpenAI
    """
    usage_summary = await budget_controller.get_usage_summary(db)
    
    if usage_summary["budget_used_percentage"] >= 100:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Budget diário esgotado. Usado: ${usage_summary['total_cost_usd']:.2f} de ${usage_summary['daily_budget_usd']:.2f}"
        )
    
    if usage_summary["budget_used_percentage"] >= 90:
        logger.warning(
            f"Budget quase esgotado: {usage_summary['budget_used_percentage']:.1f}%"
        )
    
    return budget_controller

async def validate_company_exists(
    company_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Dependency para validar se uma empresa existe"""
    from app.models.company import Company
    from sqlalchemy import select
    
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empresa com ID {company_id} não encontrada"
        )
    
    return company