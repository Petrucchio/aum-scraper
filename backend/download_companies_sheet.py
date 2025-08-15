#!/usr/bin/env python3
"""
Script para baixar a planilha do Google Sheets fornecida no case
Para executar DENTRO do container Docker:
docker-compose exec backend python download_companies_sheet.py

Ou usar curl diretamente (sem dependências):
curl "https://docs.google.com/spreadsheets/d/1maRQQZIRymo_7EN3rJxR1jEYZ0nBsmK-vLuVBgAm594/export?format=csv" -o companies.csv
"""

import sys
import subprocess

def download_with_curl():
    """Baixa usando curl (sem dependências Python)"""
    sheet_id = "1maRQQZIRymo_7EN3rJxR1jEYZ0nBsmK-vLuVBgAm594"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    print("📥 Baixando planilha com curl...")
    
    try:
        # Usar curl para baixar
        result = subprocess.run([
            "curl", 
            "-L",  # Seguir redirects
            "-o", "companies.csv",  # Output file
            csv_url
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Planilha baixada com sucesso usando curl!")
            
            # Verificar se o arquivo foi criado
            try:
                with open('companies.csv', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    print(f"📊 CSV contém {len(lines)} linhas")
                    if len(lines) > 0:
                        print(f"📋 Header: {lines[0].strip()}")
                    if len(lines) > 1:
                        print(f"📋 Primeira empresa: {lines[1].strip()}")
                return True
            except Exception as e:
                print(f"⚠️ Arquivo baixado mas erro ao ler: {e}")
                return True  # Arquivo existe, mesmo com erro de leitura
        else:
            print(f"❌ Erro no curl: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ Curl não encontrado no sistema")
        return False
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def download_with_python():
    """Baixa usando Python (dentro do container)"""
    try:
        import requests
        import pandas as pd
        import io
        
        sheet_id = "1maRQQZIRymo_7EN3rJxR1jEYZ0nBsmK-vLuVBgAm594"
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        
        print("📥 Baixando planilha com Python...")
        
        response = requests.get(csv_url, timeout=30)
        response.raise_for_status()
        
        # Processar CSV
        csv_data = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_data))
        
        print(f"✅ Planilha baixada: {len(df)} empresas encontradas")
        print(f"📋 Colunas: {list(df.columns)}")
        
        # Verificar e ajustar colunas
        expected_columns = ['name', 'url_site', 'url_linkedin', 'url_instagram', 'url_x']
        
        # Mapear colunas se necessário
        if not all(col in df.columns for col in expected_columns):
            print("🔄 Mapeando colunas...")
            
            column_mapping = {}
            for col in df.columns:
                col_lower = col.lower().strip()
                if any(word in col_lower for word in ['nome', 'name', 'empresa', 'company']):
                    column_mapping['name'] = col
                elif 'site' in col_lower:
                    column_mapping['url_site'] = col
                elif 'linkedin' in col_lower:
                    column_mapping['url_linkedin'] = col
                elif 'instagram' in col_lower:
                    column_mapping['url_instagram'] = col
                elif any(word in col_lower for word in ['twitter', 'x.com', 'x ']):
                    column_mapping['url_x'] = col
            
            print(f"🗺️ Mapeamento: {column_mapping}")
            df = df.rename(columns=column_mapping)
        
        # Garantir todas as colunas
        for col in expected_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Limpar e salvar
        df = df[expected_columns]
        df = df.fillna('')
        df = df.dropna(subset=['name'])
        
        df.to_csv('companies.csv', index=False, encoding='utf-8')
        
        print(f"🎉 CSV salvo com {len(df)} empresas!")
        print("\n📊 Primeiras empresas:")
        for i, row in df.head(3).iterrows():
            print(f"{i+1}. {row['name']}")
        
        return True
        
    except ImportError:
        print("❌ Dependências Python não disponíveis (requests/pandas)")
        return False
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def create_sample_csv():
    """Cria CSV de exemplo se download falhar"""
    sample_data = """name,url_site,url_linkedin,url_instagram,url_x
XP Investimentos,https://www.xpi.com.br,https://www.linkedin.com/company/xp-investimentos,https://www.instagram.com/xpinvestimentos,https://x.com/xpinvestimentos
BTG Pactual,https://www.btgpactual.com,https://www.linkedin.com/company/btg-pactual,https://www.instagram.com/btgpactual,https://x.com/btgpactual
Warren Investimentos,https://warren.com.br,https://www.linkedin.com/company/warren-investimentos,https://www.instagram.com/warreninvestimentos,https://x.com/warren_inv
Genial Investimentos,https://www.genialinvestimentos.com.br,https://www.linkedin.com/company/genial-investimentos,https://www.instagram.com/genialinvestimentos,
Itaú Asset Management,https://www.itauassetmanagement.com.br,https://www.linkedin.com/company/itau-asset-management,https://www.instagram.com/itauasset,"""
    
    with open('companies.csv', 'w', encoding='utf-8') as f:
        f.write(sample_data)
    
    print("✅ CSV de exemplo criado com 5 empresas")

def main():
    print("🔄 Tentando baixar planilha oficial do Google Sheets...")
    print("📋 URL: https://docs.google.com/spreadsheets/d/1maRQQZIRymo_7EN3rJxR1jEYZ0nBsmK-vLuVBgAm594/")
    
    # Tentar métodos em ordem de preferência
    success = False
    
    # 1. Tentar com Python (se estiver no container)
    if not success:
        success = download_with_python()
    
    # 2. Tentar com curl (se disponível)
    if not success:
        success = download_with_curl()
    
    # 3. Criar exemplo se tudo falhar
    if not success:
        print("\n🔄 Criando CSV de exemplo...")
        create_sample_csv()
    
    print("\n🚀 Próximos passos:")
    print("1. Verifique o arquivo companies.csv")
    print("2. Execute: docker-compose restart backend")
    print("3. Carregue: curl -X POST 'http://localhost:8000/api/v1/companies/load-from-csv'")
    print("4. Processe: curl -X POST 'http://localhost:8000/api/v1/scraping/pipeline/full'")
    
    # Instruções adicionais
    print("\n💡 Alternativas:")
    print("• Execute dentro do Docker: docker-compose exec backend python download_companies_sheet.py")
    print("• Use curl direto: curl 'https://docs.google.com/spreadsheets/d/1maRQQZIRymo_7EN3rJxR1jEYZ0nBsmK-vLuVBgAm594/export?format=csv' -o companies.csv")
    print("• Baixe manualmente do Google Sheets e salve como companies.csv")

if __name__ == "__main__":
    main()