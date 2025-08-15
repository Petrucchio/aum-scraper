import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def convert_aum_to_float(aum_text: str) -> Optional[float]:
    """
    Converte texto de AUM para número float padronizado
    Ex: "R$ 2,3 bi" -> 2.3e9
    """
    if not aum_text or aum_text.upper() == "NAO_DISPONIVEL":
        return None
    
    try:
        # Normalizar o texto
        text = aum_text.lower().strip()
        
        # Extrair número
        number_match = re.search(r'(\d+[,.]\d+|\d+)', text)
        if not number_match:
            return None
        
        number_str = number_match.group(1).replace(',', '.')
        base_value = float(number_str)
        
        # Identificar unidade
        multiplier = 1
        
        if any(unit in text for unit in ['bilhão', 'bilhões', 'bi', 'billion']):
            multiplier = 1e9
        elif any(unit in text for unit in ['milhão', 'milhões', 'mi', 'million']):
            multiplier = 1e6
        elif any(unit in text for unit in ['mil', 'thousand', 'k']):
            multiplier = 1e3
        elif any(unit in text for unit in ['trilhão', 'trilhões', 'tri', 'trillion']):
            multiplier = 1e12
        
        result = base_value * multiplier
        logger.info(f"Convertido '{aum_text}' para {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao converter '{aum_text}': {str(e)}")
        return None

def format_currency(value: float, currency: str = "BRL") -> str:
    """Formatar valor monetário para exibição"""
    if value is None:
        return "N/A"
    
    try:
        if currency == "BRL":
            symbol = "R$ "
        else:
            symbol = "US$ "
        
        if value >= 1e9:
            return f"{symbol}{value/1e9:.2f} bi"
        elif value >= 1e6:
            return f"{symbol}{value/1e6:.2f} mi"
        elif value >= 1e3:
            return f"{symbol}{value/1e3:.2f} mil"
        else:
            return f"{symbol}{value:.2f}"
            
    except Exception:
        return str(value)

def normalize_currency_text(text: str) -> str:
    """Normaliza texto de moeda para processamento consistente"""
    if not text:
        return text
    
    # Substituições comuns
    replacements = {
        'bilhões': 'bi',
        'bilhão': 'bi',
        'milhões': 'mi',
        'milhão': 'mi',
        'reais': '',
        'dólares': 'USD',
        'dólar': 'USD'
    }
    
    normalized = text.lower()
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    return normalized.strip()

def validate_aum_value(value: float) -> bool:
    """Valida se um valor de AUM é razoável"""
    if value is None:
        return False
    
    # Valores muito baixos ou muito altos são suspeitos
    min_value = 1e6  # 1 milhão
    max_value = 1e15  # 1 quatrilhão
    
    return min_value <= value <= max_value