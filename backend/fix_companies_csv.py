#!/usr/bin/env python3
"""
Script corrigido para baixar e processar a lista COMPLETA de empresas
Execute: python fix_companies_csv_final.py
"""

import re

def download_and_process_full_list():
    """Baixa lista completa e processa para formato correto"""
    
    try:
        import requests
        import pandas as pd
        import io
        
        # URL da planilha oficial
        sheet_url = "https://docs.google.com/spreadsheets/d/1maRQQZIRymo_7EN3rJxR1jEYZ0nBsmK-vLuVBgAm594/export?format=csv"
        
        print("📥 Baixando lista COMPLETA do Google Sheets...")
        
        # Baixar CSV
        response = requests.get(sheet_url, timeout=30)
        response.raise_for_status()
        
        # Ler com pandas
        df = pd.read_csv(io.StringIO(response.text))
        
        print(f"✅ Baixado: {len(df)} linhas")
        print(f"📋 Colunas: {list(df.columns)}")
        
        # Pegar lista de nomes da primeira coluna
        company_names = df.iloc[:, 0].dropna().astype(str).tolist()
        
        print(f"📊 Processando {len(company_names)} empresas...")
        
        # Processar cada empresa
        companies = []
        for name in company_names:
            clean_name = clean_company_name(name)
            if clean_name and len(clean_name) > 2:
                site_url, linkedin_url, instagram_url, x_url = generate_urls(clean_name)
                
                companies.append({
                    'name': clean_name,
                    'url_site': site_url,
                    'url_linkedin': linkedin_url,
                    'url_instagram': instagram_url,
                    'url_x': x_url
                })
        
        # Salvar CSV
        df_output = pd.DataFrame(companies)
        df_output.to_csv('/app/companies.csv', index=False, encoding='utf-8')
        
        print(f"🎉 CSV criado com {len(companies)} empresas!")
        print(f"💰 Custo estimado: ${len(companies) * 0.05:.2f} USD")
        
        # Mostrar primeiras empresas
        print("\n📋 Primeiras 5 empresas:")
        for i, company in enumerate(companies[:5]):
            print(f"{i+1}. {company['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def clean_company_name(name):
    """Limpa nome da empresa"""
    if not name:
        return None
    
    # Converter para string
    name = str(name).strip()
    
    # Remover numeração inicial
    name = re.sub(r'^\d+\s*', '', name)
    
    # Remover caracteres especiais no início/fim
    name = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', name)
    
    # Se muito pequeno ou só números, ignorar
    if len(name) < 3 or name.isdigit():
        return None
    
    return name.strip()

def generate_urls(company_name):
    """Gera URLs baseadas no nome da empresa"""
    
    # Casos especiais conhecidos
    special_cases = {
        'XP Investimentos': ('https://www.xpi.com.br', 'https://www.linkedin.com/company/xp-investimentos', 'https://www.instagram.com/xpinvestimentos', 'https://x.com/xpinvestimentos'),
        'BTG Pactual': ('https://www.btgpactual.com', 'https://www.linkedin.com/company/btg-pactual', 'https://www.instagram.com/btgpactual', 'https://x.com/btgpactual'),
        'Warren Investimentos': ('https://warren.com.br', 'https://www.linkedin.com/company/warren-investimentos', 'https://www.instagram.com/warreninvestimentos', 'https://x.com/warren_inv'),
        'Genial Investimentos': ('https://www.genialinvestimentos.com.br', 'https://www.linkedin.com/company/genial-investimentos', 'https://www.instagram.com/genialinvestimentos', ''),
    }
    
    if company_name in special_cases:
        return special_cases[company_name]
    
    # Gerar URLs genéricas
    clean_name = company_name.lower()
    
    # Remover acentos
    clean_name = clean_name.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ç', 'c')
    
    # Remover caracteres especiais
    clean_name = re.sub(r'[^\w\s]', '', clean_name)
    
    # Remover palavras comuns
    words_to_remove = ['investimentos', 'capital', 'asset', 'management', 'gestao', 'recursos', 'ltda', 'sa']
    for word in words_to_remove:
        clean_name = clean_name.replace(word, '')
    
    # Limpar espaços e limitar tamanho
    clean_name = re.sub(r'\s+', '', clean_name.strip())
    
    if len(clean_name) > 15:
        clean_name = clean_name[:15]
    
    # Se muito pequeno, usar versão simplificada
    if len(clean_name) < 3:
        clean_name = re.sub(r'[^\w]', '', company_name.lower())[:10]
    
    # Gerar URLs
    site_url = f"https://www.{clean_name}.com.br"
    linkedin_url = f"https://www.linkedin.com/company/{clean_name}"
    instagram_url = f"https://www.instagram.com/{clean_name}"
    x_url = ""  # Deixar vazio por padrão
    
    return site_url, linkedin_url, instagram_url, x_url

def create_sample_csv():
    """Cria CSV de exemplo se falhar"""
    sample_data = """name,url_site,url_linkedin,url_instagram,url_x
XP Investimentos,https://www.xpi.com.br,https://www.linkedin.com/company/xp-investimentos,https://www.instagram.com/xpinvestimentos,https://x.com/xpinvestimentos
BTG Pactual,https://www.btgpactual.com,https://www.linkedin.com/company/btg-pactual,https://www.instagram.com/btgpactual,https://x.com/btgpactual
Warren Investimentos,https://warren.com.br,https://www.linkedin.com/company/warren-investimentos,https://www.instagram.com/warreninvestimentos,https://x.com/warren_inv
Genial Investimentos,https://www.genialinvestimentos.com.br,https://www.linkedin.com/company/genial-investimentos,https://www.instagram.com/genialinvestimentos,
Time Invest,https://www.timeinvest.com.br,https://www.linkedin.com/company/time-invest,https://www.instagram.com/timeinvest,
1A Investimentos,https://www.1ainvestimentos.com.br,https://www.linkedin.com/company/1a-investimentos,https://www.instagram.com/1ainvestimentos,
Absolute Investimentos,https://www.absoluteinvestimentos.com.br,https://www.linkedin.com/company/absolute-investimentos,https://www.instagram.com/absoluteinvestimentos,
A7 Capital,https://www.a7capital.com.br,https://www.linkedin.com/company/a7-capital,https://www.instagram.com/a7capital,
Gávea Investimentos,https://www.gavea.com.br,https://www.linkedin.com/company/gavea-investimentos,https://www.instagram.com/gaveainvestimentos,
Verde Asset Management,https://www.verde.com.br,https://www.linkedin.com/company/verde-asset,https://www.instagram.com/verdeasset,"""
    
    try:
        with open('/app/companies.csv', 'w', encoding='utf-8') as f:
            f.write(sample_data)
        print("✅ CSV de exemplo criado com 10 empresas")
    except Exception as e:
        print(f"❌ Erro ao criar arquivo: {e}")

def main():
    print("🔧 Processador de Lista Completa de Empresas")
    print("=" * 50)
    
    # Tentar baixar lista completa
    success = download_and_process_full_list()
    
    if not success:
        print("\n🔄 Criando CSV de exemplo...")
        create_sample_csv()
    
    print("\n🚀 Próximos passos:")
    print("1. Reinicie: docker-compose restart backend")
    print("2. Carregue: POST /api/v1/companies/load-from-csv")
    print("3. Execute: POST /api/v1/scraping/pipeline/full")

if __name__ == "__main__":
    main()