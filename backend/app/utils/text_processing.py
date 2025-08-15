import re
from typing import List, Tuple
from bs4 import BeautifulSoup
import tiktoken

def extract_relevant_chunks(html: str, max_tokens: int = 1200) -> List[str]:
    """
    Extrai apenas os parágrafos relevantes que podem conter informações de AUM
    """
    # Parse HTML
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove scripts e styles
    for script in soup(["script", "style", "nav", "header", "footer"]):
        script.decompose()
    
    # Pega todo o texto
    text = soup.get_text()
    
    # Keywords para identificar conteúdo relevante
    aum_keywords = [
        'aum', 'assets under management', 'patrimônio sob gestão', 
        'patrimônio', 'gestão', 'bilhões', 'milhões', 'bi', 'mi',
        'r$', 'reais', 'usd', 'dólares', 'fundos', 'carteira'
    ]
    
    # Regex para valores monetários
    money_pattern = r'[R$US$]?\s*\d+[,.]\d+\s*[bmk]?[iI]?[lhões]*'
    
    # Dividir em parágrafos
    paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 20]
    
    relevant_chunks = []
    
    for paragraph in paragraphs:
        paragraph_lower = paragraph.lower()
        
        # Verificar se contém keywords ou padrões monetários
        has_keywords = any(keyword in paragraph_lower for keyword in aum_keywords)
        has_money_pattern = re.search(money_pattern, paragraph)
        
        if has_keywords or has_money_pattern:
            relevant_chunks.append(paragraph)
    
    # Se não encontrou nada relevante, pega os primeiros parágrafos
    if not relevant_chunks:
        relevant_chunks = paragraphs[:5]  # Primeiros 5 parágrafos
    
    # Limitar por tokens
    encoding = tiktoken.get_encoding("cl100k_base")
    final_chunks = []
    total_tokens = 0
    
    for chunk in relevant_chunks:
        chunk_tokens = len(encoding.encode(chunk))
        if total_tokens + chunk_tokens <= max_tokens:
            final_chunks.append(chunk)
            total_tokens += chunk_tokens
        else:
            # Adicionar parcialmente se couber
            remaining_tokens = max_tokens - total_tokens
            if remaining_tokens > 50:  # Mínimo útil
                truncated = encoding.decode(encoding.encode(chunk)[:remaining_tokens])
                final_chunks.append(truncated + "...")
            break
    
    return final_chunks

def clean_text(text: str) -> str:
    """Limpa e normaliza texto"""
    if not text:
        return ""
    
    # Remove caracteres especiais em excesso
    text = re.sub(r'\s+', ' ', text)  # Múltiplos espaços
    text = re.sub(r'[\r\n]+', '\n', text)  # Múltiplas quebras de linha
    
    return text.strip()

def extract_money_values(text: str) -> List[str]:
    """Extrai valores monetários do texto"""
    patterns = [
        r'[R$]\s*\d+[,.]?\d*\s*[bmk]?[iI]?[lhões]*',
        r'US?\$\s*\d+[,.]?\d*\s*[bmk]?[iI]?[lhões]*',
        r'\d+[,.]?\d*\s*[bmk]?[iI]?[lhões]*\s*de\s*reais',
        r'\d+[,.]?\d*\s*[bmk]?[iI]?[lhões]*\s*em\s*ativos'
    ]
    
    values = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        values.extend(matches)
    
    return values

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Conta tokens usando tiktoken"""
    try:
        if model.startswith("gpt-4"):
            encoding = tiktoken.get_encoding("cl100k_base")
        else:
            encoding = tiktoken.get_encoding("p50k_base")
        
        return len(encoding.encode(text))
    except Exception:
        # Fallback: estimativa aproximada
        return len(text.split()) * 1.3