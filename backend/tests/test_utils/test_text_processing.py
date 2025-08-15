import pytest
from app.utils.text_processing import (
    extract_relevant_chunks,
    clean_text,
    extract_money_values,
    count_tokens
)

class TestTextProcessing:
    """Testes para processamento de texto"""
    
    def test_extract_relevant_chunks_with_aum_keywords(self):
        """Teste extração de chunks relevantes com keywords de AUM"""
        html = """
        <html>
            <body>
                <p>Esta empresa tem um patrimônio sob gestão de R$ 2,5 bilhões.</p>
                <p>Oferecemos serviços de consultoria financeira.</p>
                <p>Nosso AUM cresceu 20% no último ano.</p>
            </body>
        </html>
        """
        
        chunks = extract_relevant_chunks(html)
        assert len(chunks) >= 2
        assert any("patrimônio sob gestão" in chunk.lower() for chunk in chunks)
        assert any("aum" in chunk.lower() for chunk in chunks)
    
    def test_extract_relevant_chunks_with_money_patterns(self):
        """Teste extração com padrões monetários"""
        html = """
        <html>
            <body>
                <p>A empresa gerencia R$ 1,2 bi em ativos.</p>
                <p>Informações sobre nossa equipe.</p>
                <p>Contato: email@empresa.com</p>
            </body>
        </html>
        """
        
        chunks = extract_relevant_chunks(html)
        assert len(chunks) >= 1
        assert any("R$ 1,2 bi" in chunk for chunk in chunks)
    
    def test_extract_relevant_chunks_no_relevant_content(self):
        """Teste quando não há conteúdo relevante"""
        html = """
        <html>
            <body>
                <p>Sobre nossa empresa</p>
                <p>História da companhia</p>
                <p>Entre em contato</p>
            </body>
        </html>
        """
        
        chunks = extract_relevant_chunks(html)
        # Deve retornar os primeiros parágrafos como fallback
        assert len(chunks) > 0
    
    def test_clean_text(self):
        """Teste limpeza de texto"""
        dirty_text = "  Texto    com   espaços\n\n\nexcessivos\r\n  "
        clean = clean_text(dirty_text)
        
        assert clean == "Texto com espaços\nexcessivos"
        assert clean_text("") == ""
        assert clean_text(None) == ""
    
    def test_extract_money_values(self):
        """Teste extração de valores monetários"""
        text = "A empresa tem R$ 2,5 bi e US$ 500 mi em ativos."
        values = extract_money_values(text)
        
        assert len(values) >= 2
        assert any("R$ 2,5 bi" in str(values))
        assert any("US$ 500 mi" in str(values))
    
    def test_count_tokens_estimation(self):
        """Teste contagem estimada de tokens"""
        text = "Esta é uma frase de teste para contagem de tokens."
        token_count = count_tokens(text)
        
        # Deve retornar um número razoável (entre 8-15 tokens para esta frase)
        assert 5 <= token_count <= 20
        assert isinstance(token_count, (int, float))
    
    def test_extract_relevant_chunks_token_limit(self):
        """Teste limite de tokens nos chunks"""
        # HTML com muito conteúdo
        long_html = "<html><body>"
        for i in range(100):
            long_html += f"<p>Parágrafo {i} com patrimônio sob gestão de R$ {i} milhões.</p>"
        long_html += "</body></html>"
        
        chunks = extract_relevant_chunks(long_html, max_tokens=500)
        
        # Verificar que total de tokens não excede o limite
        total_text = " ".join(chunks)
        total_tokens = count_tokens(total_text)
        assert total_tokens <= 600  # Margem de erro para estimativa