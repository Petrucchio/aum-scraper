import openai
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.aum_snapshot import AUMSnapshot
from app.models.company import Company
from app.services.budget_controller import BudgetController
from app.utils.text_processing import extract_relevant_chunks, count_tokens
from app.utils.unit_converter import convert_aum_to_float, validate_aum_value
from app.core.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)

class AIExtractor:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens_per_request = settings.max_tokens_per_request
        self.budget_controller = BudgetController()
    
    async def extract_aum_from_content(
        self, 
        company: Company, 
        scraped_data: List[Dict], 
        db: AsyncSession
    ) -> Optional[AUMSnapshot]:
        """Extrai AUM usando GPT-4o a partir dos dados coletados"""
        
        # Combinar todo o conteúdo relevante
        all_content = []
        sources = []
        
        for data in scraped_data:
            if data["status"] == "success" and data["content"]:
                # Extrair chunks relevantes
                chunks = extract_relevant_chunks(data["content"], max_tokens=400)
                if chunks:
                    all_content.extend(chunks)
                    sources.append(f"{data['content_type']}: {data['url']}")
        
        if not all_content:
            logger.warning(f"Nenhum conteúdo relevante encontrado para {company.name}")
            return await self._create_empty_snapshot(company, db)
        
        # Preparar prompt
        content_text = "\n\n".join(all_content)
        prompt = self._create_extraction_prompt(company.name, content_text)
        
        # Verificar limite de tokens
        prompt_tokens = count_tokens(prompt, self.model)
        if prompt_tokens > self.max_tokens_per_request - 200:  # Reservar espaço para resposta
            # Truncar conteúdo
            content_text = content_text[:int(len(content_text) * 0.7)]
            prompt = self._create_extraction_prompt(company.name, content_text)
            prompt_tokens = count_tokens(prompt, self.model)
        
        # Verificar budget
        estimated_cost = self.budget_controller.estimate_task_cost(
            prompt_tokens + 200  # Estimativa da resposta
        )
        
        if not await self.budget_controller.check_budget_and_run(estimated_cost, db):
            logger.error(f"Budget insuficiente para processar {company.name}")
            return await self._create_empty_snapshot(company, db, error="Budget insuficiente")
        
        try:
            # Fazer chamada para OpenAI
            response = await self._call_openai(prompt)
            
            # Registrar uso
            await self.budget_controller.record_usage(
                db=db,
                company_id=company.id,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                model=self.model,
                request_type="aum_extraction"
            )
            
            # Processar resposta
            aum_text = response.choices[0].message.content.strip()
            
            return await self._create_aum_snapshot(
                company=company,
                aum_text=aum_text,
                sources=sources,
                content_text=content_text,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Erro na extração de AUM para {company.name}: {str(e)}")
            return await self._create_empty_snapshot(company, db, error=str(e))
    
    def _create_extraction_prompt(self, company_name: str, content: str) -> str:
        """Cria prompt otimizado para extração de AUM"""
        return f"""Você é um especialista em análise de informações financeiras. Sua tarefa é encontrar o Patrimônio Sob Gestão (AUM) da empresa {company_name}.

INSTRUÇÕES:
1. Analise o conteúdo abaixo procurando por informações sobre AUM, Assets Under Management, ou Patrimônio Sob Gestão
2. Procure por valores em reais (R$), dólares (US$), bilhões (bi), milhões (mi)
3. Se encontrar o valor, responda APENAS com o número e unidade (ex: "R$ 2,3 bi", "US$ 500 mi")
4. Se NÃO encontrar informações sobre AUM, responda exatamente: "NAO_DISPONIVEL"
5. NÃO adicione explicações, contexto ou outras informações

CONTEÚDO PARA ANÁLISE:
{content}

RESPOSTA (apenas o valor do AUM ou NAO_DISPONIVEL):"""
    
    async def _call_openai(self, prompt: str):
        """Faz chamada para a API OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=100,  # Resposta curta
                temperature=0,  # Determinística
                timeout=30
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Erro na chamada OpenAI: {str(e)}")
            raise
    
    async def _create_aum_snapshot(
        self, 
        company: Company, 
        aum_text: str, 
        sources: List[str],
        content_text: str,
        db: AsyncSession
    ) -> AUMSnapshot:
        """Cria snapshot do AUM extraído"""
        
        # Converter para float
        aum_normalized = convert_aum_to_float(aum_text)
        
        # Calcular score de confiança básico
        confidence_score = 0.0
        if aum_text != "NAO_DISPONIVEL":
            confidence_score = 0.8  # Alta confiança se GPT encontrou valor
            if aum_normalized and validate_aum_value(aum_normalized):
                confidence_score = 0.9  # Ainda maior se valor é razoável
        
        snapshot = AUMSnapshot(
            company_id=company.id,
            aum_raw_text=aum_text,
            aum_normalized=aum_normalized,
            source_url="; ".join(sources[:3]),  # Primeiras 3 fontes
            source_content=content_text[:5000],  # Limitar tamanho
            extraction_method="gpt4o",
            confidence_score=confidence_score
        )
        
        db.add(snapshot)
        await db.commit()
        
        logger.info(f"AUM extraído para {company.name}: {aum_text}")
        return snapshot
    
    async def _create_empty_snapshot(
        self, 
        company: Company, 
        db: AsyncSession, 
        error: str = None
    ) -> AUMSnapshot:
        """Cria snapshot vazio quando não há dados"""
        
        snapshot = AUMSnapshot(
            company_id=company.id,
            aum_raw_text="NAO_DISPONIVEL",
            aum_normalized=None,
            source_url=None,
            source_content=error or "Nenhum conteúdo relevante encontrado",
            extraction_method="gpt4o",
            confidence_score=0.0
        )
        
        db.add(snapshot)
        await db.commit()
        
        return snapshot
    
    async def batch_extract_aum(
        self, 
        companies_data: List[Dict], 
        db: AsyncSession
    ) -> List[AUMSnapshot]:
        """Processa múltiplas empresas em lote"""
        
        results = []
        
        for i, company_data in enumerate(companies_data):
            company = company_data["company"]
            scraped_data = company_data["scraped_data"]
            
            logger.info(f"Processando AUM {i+1}/{len(companies_data)}: {company.name}")
            
            # Verificar budget antes de cada empresa
            usage_summary = await self.budget_controller.get_usage_summary(db)
            if usage_summary["budget_used_percentage"] >= 95:
                logger.error("Budget quase esgotado, parando processamento")
                break
            
            try:
                snapshot = await self.extract_aum_from_content(company, scraped_data, db)
                results.append(snapshot)
                
            except Exception as e:
                logger.error(f"Erro ao processar {company.name}: {str(e)}")
                empty_snapshot = await self._create_empty_snapshot(
                    company, db, error=str(e)
                )
                results.append(empty_snapshot)
        
        return results