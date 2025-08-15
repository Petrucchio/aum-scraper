import asyncio
import aiohttp
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.scrape_log import ScrapeLog
from app.models.company import Company
from app.services.news_scraper import NewsScaper  # Nova importação
from app.core.config import settings
import logging
import time

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.max_concurrent = settings.max_concurrent_requests
        self.request_delay = settings.request_delay
        self.timeout = 30
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.news_scraper = NewsScaper()  # Adicionar news scraper
    
    async def scrape_company_urls(
        self, 
        company: Company, 
        db: AsyncSession,
        use_playwright: bool = False,
        include_news: bool = True  # Novo parâmetro
    ) -> List[Dict]:
        """Scrapa todas as URLs de uma empresa + notícias"""
        results = []
        
        # URLs tradicionais da empresa
        urls_to_scrape = [
            ("site", company.url_site),
            ("linkedin", company.url_linkedin),
            ("instagram", company.url_instagram),
            ("x", company.url_x)
        ]
        
        # Filtrar URLs válidas
        valid_urls = [(content_type, url) for content_type, url in urls_to_scrape 
                     if url and url.strip() and url.startswith(('http://', 'https://'))]
        
        # Scraping das URLs da empresa
        for content_type, url in valid_urls:
            async with self.semaphore:
                try:
                    if use_playwright or content_type in ['instagram', 'x']:
                        content = await self._scrape_with_playwright(url)
                    else:
                        content = await self._scrape_with_requests(url)
                    
                    # Salvar log de sucesso
                    scrape_log = ScrapeLog(
                        company_id=company.id,
                        url=url,
                        status="success",
                        content_type=content_type,
                        scraped_content=content[:10000]  # Limitar tamanho
                    )
                    
                    db.add(scrape_log)
                    results.append({
                        "content_type": content_type,
                        "url": url,
                        "content": content,
                        "status": "success"
                    })
                    
                    logger.info(f"Scraping bem-sucedido: {url}")
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Erro ao fazer scraping de {url}: {error_msg}")
                    
                    # Salvar log de erro
                    scrape_log = ScrapeLog(
                        company_id=company.id,
                        url=url,
                        status="failed",
                        content_type=content_type,
                        error_message=error_msg
                    )
                    
                    db.add(scrape_log)
                    results.append({
                        "content_type": content_type,
                        "url": url,
                        "content": None,
                        "status": "failed",
                        "error": error_msg
                    })
                
                # Delay entre requests
                await asyncio.sleep(self.request_delay)
        
        # NOVO: Buscar notícias sobre a empresa
        if include_news:
            try:
                logger.info(f"Buscando notícias sobre {company.name}")
                news_results = await self.news_scraper.search_company_news(company.name)
                
                for news in news_results:
                    # Salvar log de notícia
                    scrape_log = ScrapeLog(
                        company_id=company.id,
                        url=news["url"],
                        status="success",
                        content_type="news",
                        scraped_content=news["content"][:10000]
                    )
                    
                    db.add(scrape_log)
                    results.append({
                        "content_type": "news",
                        "url": news["url"],
                        "content": news["content"],
                        "status": "success",
                        "source": news.get("site", "Notícias")
                    })
                
                logger.info(f"Encontradas {len(news_results)} notícias para {company.name}")
                
            except Exception as e:
                logger.error(f"Erro ao buscar notícias para {company.name}: {str(e)}")
        
        await db.commit()
        return results
    
    async def _scrape_with_requests(self, url: str) -> str:
        """Scraping com aiohttp para conteúdo estático"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    raise ValueError(f"Conteúdo não é HTML: {content_type}")
                
                html = await response.text()
                return self._clean_html(html)
    
    async def _scrape_with_playwright(self, url: str) -> str:
        """Scraping com Playwright para conteúdo dinâmico"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Configurações para evitar detecção
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            try:
                # Navegar para a página
                await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout * 1000)
                
                # Aguardar um pouco para conteúdo dinâmico carregar
                await page.wait_for_timeout(3000)
                
                # Obter conteúdo HTML
                html = await page.content()
                
                return self._clean_html(html)
                
            finally:
                await browser.close()
    
    def _clean_html(self, html: str) -> str:
        """Limpa HTML e extrai texto relevante"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remover elementos desnecessários
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Extrair texto
        text = soup.get_text(separator=' ', strip=True)
        
        # Limpeza básica
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_text = ' '.join(lines)
        
        return cleaned_text