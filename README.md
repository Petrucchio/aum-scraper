# AUM Scraper Backend

Sistema backend para coleta automatizada de Patrimônio Sob Gestão (AUM) de empresas do mercado financeiro através de scraping web e extração via GPT-4o.

## 🚀 Funcionalidades

- **Scraping Web Inteligente**: Coleta dados de sites, LinkedIn, Instagram e Twitter/X
- **Extração via IA**: Usa GPT-4o para extrair informações de AUM do conteúdo coletado
- **Controle de Budget**: Monitora e limita gastos da API OpenAI
- **Processamento em Lote**: Processa múltiplas empresas de forma eficiente
- **Exportação Excel**: Gera relatórios completos em formato Excel
- **API REST Completa**: Endpoints documentados com Swagger/OpenAPI
- **Histórico e Logs**: Mantém registro completo de todas as operações

## 🛠️ Tecnologias

- **Python 3.11**
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy 2** + **Alembic** - ORM e migrações de banco
- **PostgreSQL** - Banco de dados principal
- **Playwright** - Scraping de conteúdo dinâmico
- **OpenAI GPT-4o** - Extração inteligente de dados
- **Docker** + **Docker Compose** - Containerização
- **Pytest** - Testes automatizados

## 📋 Pré-requisitos

- Docker e Docker Compose
- Arquivo `companies.csv` com as empresas (ver formato abaixo)
- Chave API OpenAI (já configurada no projeto)

## 🔧 Instalação e Execução

### 1. Clone o repositório
```bash
git clone https://github.com/Petrucchio/aum-scraper.git
cd aum-scraper-backend
```

### 2. Prepare o arquivo CSV
Crie um arquivo `companies.csv` na raiz do projeto com o formato:
```csv
name,url_site,url_linkedin,url_instagram,url_x
Empresa A,https://empresaa.com.br,https://linkedin.com/company/empresaa,https://instagram.com/empresaa,https://x.com/empresaa
Empresa B,https://empresab.com.br,https://linkedin.com/company/empresab,,
```

### 3. Execute com Docker Compose
```bash
# Construir e iniciar todos os serviços
docker-compose up --build

# Ou executar em background
docker-compose up -d --build
```

### 4. Acesse a aplicação
- **API Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **PostgreSQL**: localhost:5432
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## 📚 Uso da API

### Endpoints Principais

#### 1. Carregar Empresas do CSV
```bash
POST /api/v1/companies/load-from-csv
```

#### 2. Executar Pipeline Completo
```bash
POST /api/v1/scraping/pipeline/full
```

#### 3. Scraping de Empresa Específica
```bash
POST /api/v1/scraping/company/{company_id}
```

#### 4. Exportar Resultados para Excel
```bash
GET /api/v1/scraping/export/excel
```

#### 5. Monitorar Uso de Budget
```bash
GET /api/v1/usage/today
GET /api/v1/usage/budget/status
```

### Exemplo de Uso Completo

1. **Carregar empresas do CSV**:
```bash
curl -X POST "http://localhost:8000/api/v1/companies/load-from-csv"
```

2. **Executar pipeline completo**:
```bash
curl -X POST "http://localhost:8000/api/v1/scraping/pipeline/full"
```

3. **Verificar resultados**:
```bash
curl "http://localhost:8000/api/v1/companies/stats/summary"
```

4. **Baixar relatório Excel**:
```bash
curl -o resultados.xlsx "http://localhost:8000/api/v1/scraping/export/excel"
```

## 🗃️ Estrutura do Banco de Dados

### Tabelas Principais

- **companies**: Dados das empresas (nome, URLs)
- **scrape_logs**: Logs de scraping (sucesso/falha, conteúdo)
- **aum_snapshots**: Snapshots de AUM extraídos
- **usage**: Registro de uso da API OpenAI

## 💰 Controle de Budget

O sistema monitora automaticamente os gastos da API OpenAI:

- **Budget Diário**: $50 USD (configurável)
- **Alerta**: 80% do budget utilizado
- **Bloqueio**: Impede execução quando budget esgotado
- **Estimativa**: Calcula custos antes da execução

## 🧪 Testes

Execute os testes automatizados:

```bash
# Dentro do container
docker-compose exec backend pytest tests/ -v --cov=app --cov-report=html

# Ou localmente (após instalar dependências)
pytest tests/ -v --cov=app --cov-report=html
```

## 📊 Monitoramento

### Métricas Disponíveis

- Uso diário de tokens e custos
- Taxa de sucesso do scraping
- Histórico de AUM por empresa
- Performance por fonte de dados

### Logs

Os logs são armazenados em `/app/logs` dentro do container e podem ser acessados via:

```bash
docker-compose logs backend
```

## 🔒 Segurança e Limites

- **Rate Limiting**: Máximo 3 requests simultâneas
- **Delay entre Requests**: 1 segundo entre cada scraping
- **Timeout**: 30 segundos por request
- **Validação**: Todos os inputs são validados com Pydantic

## 🐛 Troubleshooting

### Problemas Comuns

1. **Erro de conexão com PostgreSQL**:
   - Verifique se o container do banco está rodando
   - Aguarde o healthcheck passar

2. **Budget esgotado**:
   - Monitore via `/api/v1/usage/today`
   - Ajuste o budget em `app/core/config.py`

3. **Scraping bloqueado**:
   - Use `use_playwright=true` para sites dinâmicos
   - Verifique logs em `/api/v1/scraping/status`

4. **Arquivo CSV não encontrado**:
   - Verifique se está na raiz do projeto
   - Confirme o formato das colunas

## 📈 Melhorias Futuras

- [ ] Integração com APIs de notícias
- [ ] Scheduler para execução automática
- [ ] Dashboard web para visualização
- [ ] Cache Redis para otimização
- [ ] Alertas por email/Slack
- [ ] API rate limiting mais sofisticado

## 📝 Licença

Este projeto foi desenvolvido como case técnico e está disponível para uso conforme especificado.

## 🤝 Suporte

Para dúvidas ou problemas:
1. Verifique os logs: `docker-compose logs backend`
2. Consulte a documentação da API: http://localhost:8000/docs
3. Execute os testes para validar o ambiente
