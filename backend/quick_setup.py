#!/usr/bin/env python3
"""
Script de setup rápido para o projeto AUM Scraper
Execute: python quick_setup.py
"""

import subprocess
import sys
import os
import time

def run_command(command, description, ignore_errors=False):
    """Executa um comando e mostra resultado"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - Sucesso")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()[:100]}...")
            return True
        else:
            if ignore_errors:
                print(f"⚠️  {description} - Aviso: {result.stderr.strip()[:100]}")
                return True
            else:
                print(f"❌ {description} - Erro: {result.stderr.strip()}")
                return False
                
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - Timeout (mais de 5 minutos)")
        return False
    except Exception as e:
        print(f"❌ {description} - Exceção: {str(e)}")
        return False

def check_requirements():
    """Verifica pré-requisitos"""
    print("🔍 Verificando pré-requisitos...")
    
    # Verificar Docker
    if not run_command("docker --version", "Verificar Docker"):
        print("❌ Docker não encontrado. Instale o Docker primeiro.")
        return False
    
    # Verificar Docker Compose
    if not run_command("docker-compose --version", "Verificar Docker Compose"):
        print("❌ Docker Compose não encontrado.")
        return False
    
    # Verificar arquivo CSV
    if not os.path.exists("companies.csv"):
        print("❌ Arquivo companies.csv não encontrado.")
        return False
    
    print("✅ Todos os pré-requisitos atendidos!\n")
    return True

def main():
    """Executa setup completo"""
    print("🚀 Setup Rápido - AUM Scraper Backend\n")
    
    # Verificar pré-requisitos
    if not check_requirements():
        return 1
    
    print("📋 Executando setup...")
    
    steps = [
        ("docker-compose down -v", "Limpando containers anteriores", True),
        ("docker system prune -f", "Limpando cache Docker", True),
        ("docker-compose build --no-cache", "Construindo imagens"),
        ("docker-compose up -d db rabbitmq", "Iniciando banco e RabbitMQ"),
    ]
    
    for command, description, *args in steps:
        ignore_errors = args[0] if args else False
        if not run_command(command, description, ignore_errors):
            print(f"\n❌ Falha em: {description}")
            return 1
        time.sleep(2)  # Aguardar entre comandos
    
    # Aguardar serviços ficarem prontos
    print("⏳ Aguardando serviços ficarem prontos...")
    time.sleep(15)
    
    # Iniciar backend
    if not run_command("docker-compose up -d backend", "Iniciando backend"):
        return 1
    
    # Aguardar backend ficar pronto
    print("⏳ Aguardando backend ficar pronto...")
    time.sleep(20)
    
    # Testar saúde
    if run_command("curl -f http://localhost:8000/health", "Testando health check", True):
        print("\n🎉 Setup concluído com sucesso!")
        print("\n📋 Próximos passos:")
        print("1. Acesse http://localhost:8000/docs para ver a API")
        print("2. Execute: curl -X POST http://localhost:8000/api/v1/companies/load-from-csv")
        print("3. Execute: curl -X POST http://localhost:8000/api/v1/scraping/pipeline/full")
        print("4. Monitore: docker-compose logs -f backend")
        return 0
    else:
        print("\n⚠️  Setup concluído, mas health check falhou.")
        print("Verifique os logs: docker-compose logs backend")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n🛑 Setup interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)