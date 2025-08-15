import pytest
from app.utils.unit_converter import (
    convert_aum_to_float,
    format_currency,
    validate_aum_value,
    normalize_currency_text
)

class TestUnitConverter:
    """Testes para conversão de unidades monetárias"""
    
    def test_convert_aum_basic_billions(self):
        """Teste conversão básica de bilhões"""
        assert convert_aum_to_float("R$ 2,3 bi") == 2.3e9
        assert convert_aum_to_float("2.5 bilhões") == 2.5e9
        assert convert_aum_to_float("US$ 1,8 billion") == 1.8e9
    
    def test_convert_aum_basic_millions(self):
        """Teste conversão básica de milhões"""
        assert convert_aum_to_float("R$ 500 mi") == 500e6
        assert convert_aum_to_float("750,5 milhões") == 750.5e6
        assert convert_aum_to_float("US$ 100 million") == 100e6
    
    def test_convert_aum_thousands(self):
        """Teste conversão de milhares"""
        assert convert_aum_to_float("R$ 500 mil") == 500e3
        assert convert_aum_to_float("1.200 thousand") == 1200e3
    
    def test_convert_aum_invalid_cases(self):
        """Teste casos inválidos"""
        assert convert_aum_to_float("NAO_DISPONIVEL") is None
        assert convert_aum_to_float("") is None
        assert convert_aum_to_float(None) is None
        assert convert_aum_to_float("texto sem números") is None
    
    def test_format_currency_billions(self):
        """Teste formatação de bilhões"""
        assert format_currency(2.3e9) == "R$ 2.30 bi"
        assert format_currency(1.5e9, "USD") == "US$ 1.50 bi"
    
    def test_format_currency_millions(self):
        """Teste formatação de milhões"""
        assert format_currency(500e6) == "R$ 500.00 mi"
        assert format_currency(750.5e6) == "R$ 750.50 mi"
    
    def test_validate_aum_value(self):
        """Teste validação de valores razoáveis"""
        assert validate_aum_value(1e9) == True  # 1 bilhão - ok
        assert validate_aum_value(500e6) == True  # 500 milhões - ok
        assert validate_aum_value(100) == False  # Muito baixo
        assert validate_aum_value(1e20) == False  # Muito alto
        assert validate_aum_value(None) == False  # None
    
    def test_normalize_currency_text(self):
        """Teste normalização de texto"""
        assert "bi" in normalize_currency_text("bilhões de reais")
        assert "mi" in normalize_currency_text("milhões de dólares")
        assert "USD" in normalize_currency_text("dólares americanos")