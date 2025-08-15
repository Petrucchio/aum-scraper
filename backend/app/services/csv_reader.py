import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.company import Company
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class CSVReader:
    def __init__(self):
        self.csv_path = settings.csv_file_path
    
    async def read_csv(self) -> List[Dict[str, Any]]:
        """Lê o arquivo CSV e retorna lista de dicionários"""
        try:
            df = pd.read_csv(self.csv_path)
            
            # Limpeza dos dados
            df = df.fillna("")  # Substitui NaN por string vazia
            df.columns = df.columns.str.strip()  # Remove espaços dos headers
            
            # Validar se as colunas obrigatórias existem
            required_columns = ['name', 'url_site', 'url_linkedin', 'url_instagram', 'url_x']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Colunas obrigatórias faltando: {missing_columns}")
            
            companies_data = df.to_dict('records')
            logger.info(f"CSV lido com sucesso: {len(companies_data)} empresas encontradas")
            
            return companies_data
            
        except Exception as e:
            logger.error(f"Erro ao ler CSV: {str(e)}")
            raise
    
    async def load_companies_to_db(self, db: AsyncSession) -> List[Company]:
        """Carrega empresas do CSV para o banco de dados"""
        companies_data = await self.read_csv()
        companies = []
        
        for data in companies_data:
            # Verifica se a empresa já existe
            result = await db.execute(
                select(Company).where(Company.name == data['name'].strip())
            )
            existing_company = result.scalar_one_or_none()
            
            if not existing_company:
                company = Company(
                    name=data['name'].strip(),
                    url_site=data.get('url_site', '').strip() or None,
                    url_linkedin=data.get('url_linkedin', '').strip() or None,
                    url_instagram=data.get('url_instagram', '').strip() or None,
                    url_x=data.get('url_x', '').strip() or None
                )
                db.add(company)
                companies.append(company)
                logger.info(f"Empresa adicionada: {company.name}")
            else:
                companies.append(existing_company)
                logger.info(f"Empresa já existe: {existing_company.name}")
        
        await db.commit()
        logger.info(f"Total de empresas processadas: {len(companies)}")
        
        return companies