from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.budget_controller import BudgetController
from app.schemas import UsageSummary
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/usage",
    tags=["usage"]
)

@router.get("/today", response_model=UsageSummary)
async def get_today_usage(
    db: AsyncSession = Depends(get_db)
):
    """Retorna o resumo de uso de hoje"""
    
    budget_controller = BudgetController()
    summary = await budget_controller.get_usage_summary(db)
    
    return UsageSummary(
        total_requests=summary["total_requests"],
        total_tokens=summary["total_tokens"],
        total_cost_usd=summary["total_cost_usd"],
        budget_used_percentage=summary["budget_used_percentage"],
        remaining_budget_usd=summary["remaining_budget_usd"]
    )

@router.get("/budget/status")
async def get_budget_status(
    db: AsyncSession = Depends(get_db)
):
    """Retorna status detalhado do budget"""
    
    budget_controller = BudgetController()
    summary = await budget_controller.get_usage_summary(db)
    
    return {
        "daily_budget_usd": summary["daily_budget_usd"],
        "used_today_usd": summary["total_cost_usd"],
        "remaining_usd": summary["remaining_budget_usd"],
        "usage_percentage": summary["budget_used_percentage"],
        "alert_threshold_reached": summary["alert_threshold_reached"],
        "can_continue": summary["budget_used_percentage"] < 100,
        "requests_today": summary["total_requests"],
        "tokens_today": summary["total_tokens"]
    }

@router.get("/history")
async def get_usage_history(
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """Retorna histórico de uso dos últimos N dias"""
    
    from app.models.usage import Usage
    from sqlalchemy import select, func
    from datetime import datetime, timedelta
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    result = await db.execute(
        select(
            func.date(Usage.created_at).label('date'),
            func.count(Usage.id).label('requests'),
            func.sum(Usage.total_tokens).label('tokens'),
            func.sum(Usage.cost_usd).label('cost')
        )
        .where(
            func.date(Usage.created_at) >= start_date,
            func.date(Usage.created_at) <= end_date
        )
        .group_by(func.date(Usage.created_at))
        .order_by(func.date(Usage.created_at))
    )
    
    history = []
    for row in result:
        history.append({
            "date": row.date.strftime('%Y-%m-%d'),
            "requests": row.requests,
            "tokens": int(row.tokens or 0),
            "cost_usd": float(row.cost or 0)
        })
    
    return {
        "period_days": days,
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
        "daily_usage": history,
        "total_requests": sum(day["requests"] for day in history),
        "total_tokens": sum(day["tokens"] for day in history),
        "total_cost_usd": sum(day["cost_usd"] for day in history)
    }

@router.get("/by-company")
async def get_usage_by_company(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Retorna uso por empresa"""
    
    from app.models.usage import Usage
    from app.models.company import Company
    from sqlalchemy import select, func
    
    result = await db.execute(
        select(
            Company.name,
            Company.id,
            func.count(Usage.id).label('requests'),
            func.sum(Usage.total_tokens).label('tokens'),
            func.sum(Usage.cost_usd).label('cost')
        )
        .join(Company, Usage.company_id == Company.id)
        .group_by(Company.id, Company.name)
        .order_by(func.sum(Usage.cost_usd).desc())
        .limit(limit)
    )
    
    company_usage = []
    for row in result:
        company_usage.append({
            "company_id": row.id,
            "company_name": row.name,
            "requests": row.requests,
            "tokens": int(row.tokens or 0),
            "cost_usd": float(row.cost or 0)
        })
    
    return {
        "companies": company_usage,
        "total_companies": len(company_usage)
    }

@router.post("/reset-daily")
async def reset_daily_usage(
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para resetar uso diário (apenas para desenvolvimento/testes)
    Em produção, isso seria feito automaticamente via cron job
    """
    
    from app.models.usage import Usage
    from sqlalchemy import delete
    from datetime import datetime
    
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Deletar registros de uso de hoje (apenas para testes)
    await db.execute(
        delete(Usage).where(
            Usage.created_at >= today,
            Usage.created_at < tomorrow
        )
    )
    
    await db.commit()
    
    return {
        "message": "Uso diário resetado com sucesso",
        "date": today.strftime('%Y-%m-%d')
    }

@router.get("/cost-estimation")
async def estimate_costs(
    companies_count: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Estima custos para processar N empresas"""
    
    budget_controller = BudgetController()
    
    # Estimativa baseada em tokens médios por empresa
    estimated_tokens_per_company = 1000  # Estimativa conservadora
    total_estimated_tokens = companies_count * estimated_tokens_per_company
    
    estimated_cost = budget_controller.estimate_task_cost(total_estimated_tokens)
    
    # Verificar budget atual
    summary = await budget_controller.get_usage_summary(db)
    can_afford = estimated_cost <= summary["remaining_budget_usd"]
    
    return {
        "companies_count": companies_count,
        "estimated_tokens": total_estimated_tokens,
        "estimated_cost_usd": estimated_cost,
        "current_budget_used": summary["total_cost_usd"],
        "remaining_budget": summary["remaining_budget_usd"],
        "can_afford": can_afford,
        "budget_after_processing": summary["remaining_budget_usd"] - estimated_cost
    }