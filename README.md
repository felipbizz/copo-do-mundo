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
streamlit run main.py
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

O projeto pode ser facilmente deployado no Google Cloud Run. Para mais detalhes, consulte a [documentação de deploy](docs/deploy.md).

```bash
# Deploy no Google Cloud Run
gcloud builds submit --config deploy/gcp/cloudbuild.yaml
```

## 📚 Documentação

Para mais detalhes, consulte a [documentação completa](docs/README.md).

## Tutorial deploy:

Suba a sua imagem docker no dockerhub com os comandos abaixo:

Faz login na sua conta:
`docker login`

Define a tag da imagem:
`docker tag copo-do-mundo seu_user/copo-do-mundo:latest`

Sobe a imagem pro repositório:
`docker push seu_user/copo-do-mundo:latest`

No google cloud shell, rode o comando: 

`gcloud run deploy copo-do-mundo --image docker.io/seu_user/copo-do-mundo:latest --port 8501`

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, consulte o [guia de desenvolvimento](docs/development.md).

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.
