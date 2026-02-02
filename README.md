# 🍹 Copo do Mundo - Sistema de Avaliação de Drinks

Sistema web para gerenciar competições de drinks, permitindo avaliação em tempo real, gestão de fotos e análise de resultados.

## ✨ Funcionalidades

### 👥 Área do Participante
- Avaliação de drinks por categoria (Caipirinha, Livre, Leite Condensado)
- Sistema de pontuação baseado em três critérios:
  - 🎨 Originalidade
  - 👀 Aparência
  - 😋 Sabor
- Acompanhamento em tempo real do progresso das votações
- Salvamento automático de rascunhos de votos

### 👨‍💼 Área do Administrador
- Gerenciamento de fotos dos drinks por participante e categoria
- Captura de fotos via câmera em tempo real ou upload
- Configuração do número de participantes
- Exportação dos dados em formato CSV
- Visualização dos resultados em tempo real

## 🚀 Como Começar

### Pré-requisitos
- Python 3.11 ou superior
- UV (gerenciador de pacotes Python moderno e rápido)

### Instalação Rápida

1. Instale o UV:
```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. Clone e configure o projeto:
```bash
git clone https://github.com/seu-usuario/copo-do-mundo.git
cd copo-do-mundo

# Crie e ative o ambiente virtual
uv venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Instale as dependências
uv pip install .
```

3. Execute a aplicação:
```bash
streamlit run src/main.py
```

4. Acesse no navegador:
- Abra http://localhost:8501

## 📁 Estrutura do Projeto

```
copo-do-mundo/     
├── pyproject.toml   # Dependências e configurações de lint/format
├── data/            # Dados e imagens
└── src
    ├── backend      # Lógica de negócio
    ├── frontend     # Interface do usuário
    ├── config.py    # Configurações de constantes
    └── main.py      # Ponto de entrada
```

## 🚀 Deploy

### Google Cloud Run

O projeto pode ser facilmente deployado no Google Cloud Run com suporte para armazenamento externo (BigQuery e Cloud Storage).

#### Deploy Automático via GitHub Actions

1. Configure os secrets no GitHub (Settings → Secrets):
   - `GCP_PROJECT_ID`: ID do projeto GCP
   - `GCP_SA_KEY`: Chave JSON da service account
   - `BIGQUERY_DATASET`: Nome do dataset (padrão: `copo_do_mundo`)
   - `BIGQUERY_TABLE`: Nome da tabela (padrão: `votes`)
   - `CLOUD_STORAGE_BUCKET`: Nome do bucket do Cloud Storage
   - `CLOUD_RUN_SERVICE_ACCOUNT`: Email da service account
   - `ADMIN_PASSWORD`: Senha do administrador

2. Faça push para a branch `main` ou `master` - o deploy será automático

#### Deploy Manual

1. Configure a infraestrutura GCP:
   ```bash
   export GCP_PROJECT_ID=seu-projeto-id
   ./infra/gcp-setup.sh
   ```

2. Migre dados existentes (opcional):
   ```bash
   python scripts/migrate_data.py
   ```

3. Deploy no Cloud Run:
   ```bash
   gcloud run deploy copo-do-mundo \
     --image gcr.io/SEU_PROJECT_ID/copo-do-mundo:latest \
     --platform managed \
     --region us-central1 \
     --set-env-vars "STORAGE_BACKEND=gcp,GCP_PROJECT_ID=SEU_PROJECT_ID,..."
   ```

Para mais detalhes, consulte a [documentação de deploy](docs/deployment.md) e [guia de migração](docs/migration.md).

## 📚 Documentação

- [Guia de Deploy](docs/deployment.md) - Como fazer deploy no Cloud Run
- [Guia de Migração](docs/migration.md) - Como migrar dados para GCP

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, consulte o [guia de desenvolvimento](docs/development.md).

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.
