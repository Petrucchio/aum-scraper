#!/usr/bin/env python3
"""
Script para criar a migração inicial do banco de dados
Execute este script para gerar a primeira migração do Alembic
"""

import subprocess
import sys
import os

def create_initial_migration():
    """Cria a migração inicial do banco de dados"""
    
    try:
        # Verificar se alembic está instalado
        subprocess.run(["alembic", "--version"], check=True, capture_output=True)
        print("✅ Alembic encontrado")
        
        # Criar migração inicial
        print("📝 Criando migração inicial...")
        result = subprocess.run([
            "alembic", "revision", "--autogenerate", 
            "-m", "Initial migration - create all tables"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migração inicial criada com sucesso!")
            print(f"Output: {result.stdout}")
        else:
            print(f"❌ Erro ao criar migração: {result.stderr}")
            return False
            
        # Aplicar migração
        print("🚀 Aplicando migração ao banco de dados...")
        result = subprocess.run([
            "alembic", "upgrade", "head"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migração aplicada com sucesso!")
            print(f"Output: {result.stdout}")
        else:
            print(f"❌ Erro ao aplicar migração: {result.stderr}")
            return False
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar comando: {e}")
        return False
    except FileNotFoundError:
        print("❌ Alembic não encontrado. Instale com: pip install alembic")
        return False

if __name__ == "__main__":
    print("🔧 Criando migração inicial do banco de dados...")
    print("📂 Certifique-se de estar na raiz do projeto (onde está o alembic.ini)")
    
    if not os.path.exists("alembic.ini"):
        print("❌ Arquivo alembic.ini não encontrado!")
        print("Execute este script na raiz do projeto onde está o alembic.ini")
        sys.exit(1)
    
    success = create_initial_migration()
    
    if success:
        print("\n🎉 Configuração do banco de dados concluída!")
        print("As seguintes tabelas foram criadas:")
        print("  - companies (empresas)")
        print("  - scrape_logs (logs de scraping)")
        print("  - aum_snapshots (snapshots de AUM)")
        print("  - usage (uso da API)")
    else:
        print("\n❌ Falha na configuração do banco de dados")
        sys.exit(1)