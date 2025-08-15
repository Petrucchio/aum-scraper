from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.models.usage import Usage
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class BudgetController:
    def __init__(self):
        self.daily_budget = settings.daily_budget_usd
        self.alert_threshold = settings.budget_alert_threshold
    
    async def get_today_usage(self, db: AsyncSession) -> float:
        """Retorna o gasto total do dia em USD"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        result = await db.execute(
            select(func.sum(Usage.cost_usd)).where(
                Usage.created_at >= today,
                Usage.created_at < tomorrow
            )
        )
        
        total_cost = result.scalar() or 0.0
        return float(total_cost)
    
    async def get_usage_summary(self, db: AsyncSession) -> dict:
        """Retorna resumo do uso diário"""
        today_cost = await self.get_today_usage(db)
        
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        # Total de requests hoje
        result = await db.execute(
            select(func.count(Usage.id)).where(
                Usage.created_at >= today,
                Usage.created_at < tomorrow
            )
        )
        total_requests = result.scalar() or 0
        
        # Total de tokens hoje
        result = await db.execute(
            select(func.sum(Usage.total_tokens)).where(
                Usage.created_at >= today,
                Usage.created_at < tomorrow
            )
        )
        total_tokens = result.scalar() or 0
        
        budget_used_pct = (today_cost / self.daily_budget) * 100
        remaining_budget = max(0, self.daily_budget - today_cost)
        
        return {
            "total_requests": total_requests,
            "total_tokens": int(total_tokens),
            "total_cost_usd": today_cost,
            "budget_used_percentage": budget_used_pct,
            "remaining_budget_usd": remaining_budget,
            "daily_budget_usd": self.daily_budget,
            "alert_threshold_reached": budget_used_pct >= (self.alert_threshold * 100)
        }
    
    async def check_budget_and_run(self, task_cost: float, db: AsyncSession) -> bool:
        """
        Verifica se há budget suficiente para executar uma tarefa
        Retorna True se pode executar, False caso contrário
        """
        today_usage = await self.get_today_usage(db)
        projected_usage = today_usage + task_cost
        
        if projected_usage > self.daily_budget:
            logger.warning(
                f"Budget excedido! Uso atual: ${today_usage:.4f}, "
                f"Custo da tarefa: ${task_cost:.4f}, "
                f"Budget diário: ${self.daily_budget}"
            )
            return False
        
        # Alerta se estiver próximo do limite
        usage_percentage = projected_usage / self.daily_budget
        if usage_percentage >= self.alert_threshold:
            logger.warning(
                f"Alerta de budget! Uso projetado: {usage_percentage*100:.1f}% "
                f"do budget diário (${projected_usage:.4f}/${self.daily_budget})"
            )
        
        return True
    
    async def record_usage(
        self, 
        db: AsyncSession,
        company_id: int = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        model: str = "gpt-4o",
        request_type: str = "aum_extraction"
    ):
        """Registra uso da API OpenAI"""
        total_tokens = prompt_tokens + completion_tokens
        
        # Cálculo de custo (preços aproximados para GPT-4o)
        prompt_cost = prompt_tokens * 0.00003  # $0.03 per 1K tokens
        completion_cost = completion_tokens * 0.00006  # $0.06 per 1K tokens
        total_cost = prompt_cost + completion_cost
        
        usage = Usage(
            company_id=company_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=total_cost,
            model_used=model,
            request_type=request_type
        )
        
        db.add(usage)
        await db.commit()
        
        logger.info(
            f"Uso registrado: {total_tokens} tokens, "
            f"${total_cost:.4f} para empresa {company_id}"
        )
        
        return usage
    
    def estimate_task_cost(self, estimated_tokens: int, model: str = "gpt-4o") -> float:
        """Estima o custo de uma tarefa baseado no número de tokens"""
        if model == "gpt-4o":
            # Assumindo distribuição 60/40 entre prompt e completion
            prompt_tokens = int(estimated_tokens * 0.6)
            completion_tokens = int(estimated_tokens * 0.4)
            
            prompt_cost = prompt_tokens * 0.00003
            completion_cost = completion_tokens * 0.00006
            
            return prompt_cost + completion_cost
        
        # Fallback para outros modelos
        return estimated_tokens * 0.00004