from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.company import Company
from app.schemas import CompanyCreate
import requests
import re
import logging
import io

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auto-setup",
    tags=["auto-setup"]
)

@router.post("/download-and-load-companies")
async def download_and_load_companies(
    limit: int = None,  # Limitar número de empresas (None = todas)
    db: AsyncSession = Depends(get_db)
):
    """
    ENDPOINT AUTOMÁTICO que:
    1. Baixa lista oficial do Google Sheets
    2. Processa para formato correto
    3. Carrega diretamente no banco
    4. Retorna empresas carregadas
    
    TOTALMENTE AUTOMATIZADO - sem arquivos intermediários!
    """
    
    try:
        # 1. BAIXAR lista oficial
        sheet_url = "https://docs.google.com/spreadsheets/d/1maRQQZIRymo_7EN3rJxR1jEYZ0nBsmK-vLuVBgAm594/export?format=csv"
        
        logger.info("📥 Baixando lista oficial do Google Sheets...")
        response = requests.get(sheet_url, timeout=30)
        response.raise_for_status()
        
        # 2. PROCESSAR CSV
        lines = response.text.strip().split('\n')
        logger.info(f"✅ Baixado: {len(lines)} linhas")
        
        # 3. EXTRAIR nomes das empresas
        company_names = []
        for line in lines[1:]:  # Pular header
            name = line.strip()
            if name and len(name) > 2:
                # Limpar numeração inicial
                clean_name = re.sub(r'^\d+\s*', '', name).strip()
                if clean_name and len(clean_name) > 2:
                    company_names.append(clean_name)
        
        # 4. LIMITAR se solicitado (para testes)
        if limit:
            company_names = company_names[:limit]
            logger.info(f"📊 Limitado a {limit} empresas para teste")
        
        logger.info(f"📊 Processando {len(company_names)} empresas...")
        
        # 5. CARREGAR diretamente no banco
        companies_created = []
        companies_existing = []
        
        for name in company_names:
            try:
                # Verificar se já existe
                from sqlalchemy import select
                result = await db.execute(
                    select(Company).where(Company.name == name)
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    companies_existing.append(existing)
                    continue
                
                # Gerar URLs
                site_url, linkedin_url, instagram_url, x_url = generate_company_urls(name)
                
                # Criar empresa
                company = Company(
                    name=name,
                    url_site=site_url,
                    url_linkedin=linkedin_url,
                    url_instagram=instagram_url,
                    url_x=x_url
                )
                
                db.add(company)
                companies_created.append(company)
                
            except Exception as e:
                logger.error(f"Erro ao processar {name}: {str(e)}")
                continue
        
        # 6. SALVAR no banco
        await db.commit()
        
        # 7. REFRESH objetos para ter IDs
        for company in companies_created:
            await db.refresh(company)
        
        total_companies = len(companies_created) + len(companies_existing)
        
        logger.info(f"🎉 Processamento completo: {len(companies_created)} criadas, {len(companies_existing)} já existiam")
        
        return {
            "message": "Lista oficial baixada e carregada automaticamente!",
            "source": "Google Sheets oficial do desafio",
            "total_processed": len(company_names),
            "companies_created": len(companies_created),
            "companies_existing": len(companies_existing),
            "total_companies": total_companies,
            "estimated_cost_usd": total_companies * 0.05,
            "companies_sample": [
                {"id": c.id, "name": c.name} 
                for c in (companies_created + companies_existing)[:10]
            ]
        }
        
    except Exception as e:
        logger.error(f"Erro no download automático: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no download automático: {str(e)}"
        )

def generate_company_urls(company_name: str):
    """Gera URLs automaticamente baseado no nome da empresa"""
    
    # Casos especiais conhecidos (URLs reais)
    special_cases = {
        'XP Investimentos': (
            'https://www.xpi.com.br',
            'https://www.linkedin.com/company/xp-investimentos',
            'https://www.instagram.com/xpinvestimentos',
            'https://x.com/xpinvestimentos'
        ),
        'BTG Pactual': (
            'https://www.btgpactual.com',
            'https://www.linkedin.com/company/btg-pactual',
            'https://www.instagram.com/btgpactual',
            'https://x.com/btgpactual'
        ),
        'Warren Investimentos': (
            'https://warren.com.br',
            'https://www.linkedin.com/company/warren-investimentos',
            'https://www.instagram.com/warreninvestimentos',
            'https://x.com/warren_inv'
        ),
        'Genial Investimentos': (
            'https://www.genialinvestimentos.com.br',
            'https://www.linkedin.com/company/genial-investimentos',
            'https://www.instagram.com/genialinvestimentos',
            ''
        ),
        'Itaú Asset Management': (
            'https://www.itauassetmanagement.com.br',
            'https://www.linkedin.com/company/itau-asset-management',
            'https://www.instagram.com/itauasset',
            ''
        ),
        'Hashdex': (
            'https://www.hashdex.com.br',
            'https://www.linkedin.com/company/hashdex',
            'https://www.instagram.com/hashdex',
            'https://x.com/hashdex'
        ),
        'Gávea Investimentos': (
            'https://www.gavea.com.br',
            'https://www.linkedin.com/company/gavea-investimentos',
            'https://www.instagram.com/gaveainvestimentos',
            ''
        )
    }
    
    if company_name in special_cases:
        return special_cases[company_name]
    
    # Gerar URLs automaticamente
    clean_name = company_name.lower()
    
    # Remover acentos
    replacements = {
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c'
    }
    
    for old, new in replacements.items():
        clean_name = clean_name.replace(old, new)
    
    # Remover caracteres especiais
    clean_name = re.sub(r'[^\w\s]', '', clean_name)
    
    # Remover palavras comuns
    words_to_remove = ['investimentos', 'capital', 'asset', 'management', 'gestao', 'recursos', 'ltda', 'sa', 'family', 'office']
    for word in words_to_remove:
        clean_name = clean_name.replace(word, '')
    
    # Limpar espaços e limitar
    clean_name = re.sub(r'\s+', '', clean_name.strip())
    
    if len(clean_name) > 15:
        clean_name = clean_name[:15]
    
    # Se ficou muito pequeno, usar original simplificado
    if len(clean_name) < 3:
        clean_name = re.sub(r'[^\w]', '', company_name.lower().replace(' ', ''))[:12]
    
    # Gerar URLs
    site_url = f"https://www.{clean_name}.com.br"
    linkedin_url = f"https://www.linkedin.com/company/{clean_name}"
    instagram_url = f"https://www.instagram.com/{clean_name}"
    x_url = ""  # Deixar vazio por padrão
    
    return site_url, linkedin_url, instagram_url, x_url

@router.post("/quick-demo-setup")
async def quick_demo_setup(db: AsyncSession = Depends(get_db)):
    """
    Setup RÁPIDO para demonstração com 20 empresas conhecidas
    URLs reais das maiores gestoras brasileiras
    """
    
    demo_companies = [
        {
            "name": "XP Investimentos",
            "url_site": "https://www.xpi.com.br",
            "url_linkedin": "https://www.linkedin.com/company/xp-investimentos",
            "url_instagram": "https://www.instagram.com/xpinvestimentos",
            "url_x": "https://x.com/xpinvestimentos"
        },
        {
            "name": "BTG Pactual",
            "url_site": "https://www.btgpactual.com",
            "url_linkedin": "https://www.linkedin.com/company/btg-pactual",
            "url_instagram": "https://www.instagram.com/btgpactual",
            "url_x": "https://x.com/btgpactual"
        },
        {
            "name": "Warren Investimentos",
            "url_site": "https://warren.com.br",
            "url_linkedin": "https://www.linkedin.com/company/warren-investimentos",
            "url_instagram": "https://www.instagram.com/warreninvestimentos",
            "url_x": "https://x.com/warren_inv"
        },
        {
            "name": "Genial Investimentos",
            "url_site": "https://www.genialinvestimentos.com.br",
            "url_linkedin": "https://www.linkedin.com/company/genial-investimentos",
            "url_instagram": "https://www.instagram.com/genialinvestimentos",
            "url_x": ""
        },
        {
            "name": "Itaú Asset Management",
            "url_site": "https://www.itauassetmanagement.com.br",
            "url_linkedin": "https://www.linkedin.com/company/itau-asset-management",
            "url_instagram": "https://www.instagram.com/itauasset",
            "url_x": ""
        },
        {
            "name": "Hashdex",
            "url_site": "https://www.hashdex.com.br",
            "url_linkedin": "https://www.linkedin.com/company/hashdex",
            "url_instagram": "https://www.instagram.com/hashdex",
            "url_x": "https://x.com/hashdex"
        },
        {
            "name": "Gávea Investimentos",
            "url_site": "https://www.gavea.com.br",
            "url_linkedin": "https://www.linkedin.com/company/gavea-investimentos",
            "url_instagram": "https://www.instagram.com/gaveainvestimentos",
            "url_x": ""
        },
        {
            "name": "Verde Asset Management",
            "url_site": "https://www.verde.com.br",
            "url_linkedin": "https://www.linkedin.com/company/verde-asset",
            "url_instagram": "https://www.instagram.com/verdeasset",
            "url_x": ""
        },
        {
            "name": "Absolute Investimentos",
            "url_site": "https://www.absoluteinvestimentos.com.br",
            "url_linkedin": "https://www.linkedin.com/company/absolute-investimentos",
            "url_instagram": "https://www.instagram.com/absoluteinvestimentos",
            "url_x": ""
        },
        {
            "name": "Kinea Investimentos",
            "url_site": "https://www.kinea.com.br",
            "url_linkedin": "https://www.linkedin.com/company/kinea-investimentos",
            "url_instagram": "https://www.instagram.com/kineainvestimentos",
            "url_x": ""
        }
    ]
    
    companies_created = []
    
    for company_data in demo_companies:
        try:
            # Verificar se já existe
            from sqlalchemy import select
            result = await db.execute(
                select(Company).where(Company.name == company_data["name"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                company = Company(**company_data)
                db.add(company)
                companies_created.append(company)
            
        except Exception as e:
            logger.error(f"Erro ao criar {company_data['name']}: {str(e)}")
    
    await db.commit()
    
    # Refresh para ter IDs
    for company in companies_created:
        await db.refresh(company)
    
    return {
        "message": "Demo setup concluído com sucesso!",
        "companies_created": len(companies_created),
        "total_companies": len(demo_companies),
        "estimated_cost_usd": len(demo_companies) * 0.05,
        "companies": [
            {"id": c.id, "name": c.name} 
            for c in companies_created
        ]
    }