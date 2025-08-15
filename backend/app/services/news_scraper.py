import aiohttp
import asyncio
from typing import List, Dict
from urllib.parse import quote
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class NewsScaper:
    def __init__(self):
        self.timeout = 30
        
    async def search_company_news(self, company_name: str) -> List[Dict]:
        """Busca notícias sobre a empresa com foco em AUM"""
        
        # Termos de busca específicos para AUM
        search_terms = [
            f'"{company_name}" patrimônio sob gestão',
            f'"{company_name}" AUM bilhões',
            f'"{company_name}" assets under management',
            f'"{company_name}" recursos sob gestão'
        ]
        
        results = []
        
        for term in search_terms:
            try:
                # Buscar em sites de notícias financeiras
                news_results = await self._search_financial_news(term)
                results.extend(news_results)
                
                # Delay entre buscas
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Erro ao buscar notícias para '{term}': {str(e)}")
                continue
        
        return results[:10]  # Limitar a 10 resultados mais relevantes
    
    async def _search_financial_news(self, search_term: str) -> List[Dict]:
        """Busca em sites de notícias financeiras"""
        
        # Sites de notícias financeiras brasileiras
        news_sites = [
            f"https://www.valor.com.br/busca?q={quote(search_term)}",
            f"https://www.infomoney.com.br/busca/?q={quote(search_term)}",
            f"https://www.moneytimes.com.br/busca/?s={quote(search_term)}",
        ]
        
        results = []
        
        for site_url in news_sites:
            try:
                content = await self._fetch_search_results(site_url)
                if content:
                    # Extrair links de notícias dos resultados
                    news_links = self._extract_news_links(content, site_url)
                    
                    # Buscar conteúdo das notícias
                    for link in news_links[:3]:  # Máximo 3 por site
                        news_content = await self._fetch_news_content(link)
                        if news_content:
                            results.append({
                                "url": link,
                                "content": news_content,
                                "source": "news",
                                "site": self._get_site_name(site_url)
                            })
                
            except Exception as e:
                logger.error(f"Erro ao buscar em {site_url}: {str(e)}")
                continue
        
        return results
    
    async def _fetch_search_results(self, url: str) -> str:
        """Faz fetch dos resultados de busca"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Status {response.status} para {url}")
                    return None
    
    def _extract_news_links(self, html: str, base_url: str) -> List[str]:
        """Extrai links de notícias dos resultados de busca"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # Seletores específicos por site
        if "valor.com.br" in base_url:
            # Seletores para Valor Econômico
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/noticia/' in href or '/empresas/' in href:
                    if href.startswith('/'):
                        href = 'https://www.valor.com.br' + href
                    links.append(href)
        
        elif "infomoney.com.br" in base_url:
            # Seletores para InfoMoney
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/mercados/' in href or '/negocios/' in href:
                    if href.startswith('/'):
                        href = 'https://www.infomoney.com.br' + href
                    links.append(href)
        
        elif "moneytimes.com.br" in base_url:
            # Seletores para MoneyTimes
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/mercados/' in href or '/investimentos/' in href:
                    if href.startswith('/'):
                        href = 'https://www.moneytimes.com.br' + href
                    links.append(href)
        
        # Remover duplicatas e limitar
        return list(set(links))[:5]
    
    async def _fetch_news_content(self, url: str) -> str:
        """Busca o conteúdo completo de uma notícia"""
        try:
            content = await self._fetch_search_results(url)
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remover elementos desnecessários
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    element.decompose()
                
                # Extrair texto principal
                article_text = soup.get_text(separator=' ', strip=True)
                
                # Limitar tamanho
                if len(article_text) > 5000:
                    article_text = article_text[:5000] + "..."
                
                return article_text
                
        except Exception as e:
            logger.error(f"Erro ao buscar conteúdo de {url}: {str(e)}")
            return None
    
    def _get_site_name(self, url: str) -> str:
        """Extrai nome do site da URL"""
        if "valor.com.br" in url:
            return "Valor Econômico"
        elif "infomoney.com.br" in url:
            return "InfoMoney"
        elif "moneytimes.com.br" in url:
            return "MoneyTimes"
        else:
            return "Notícias"