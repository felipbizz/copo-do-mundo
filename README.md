# 🍹 Copo do Mundo - Sistema de Avaliação de Drinks

Um sistema web interativo para gerenciar competições de drinks, permitindo avaliação em tempo real, gestão de fotos e análise de resultados.

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
- Captura de fotos via:
  - 📸 Câmera em tempo real
  - 📤 Upload de arquivo
- Configuração do número de participantes
- Exportação dos dados em formato CSV
- Visualização dos resultados em tempo real

### 📊 Sistema de Resultados
- Cálculo automático de médias por categoria
- Ranking de participantes
- Visualização detalhada das pontuações
- Proteção por senha para acesso aos resultados

## 🚀 Como Começar

### Pré-requisitos
- Python 3.11 ou superior
- UV (gerenciador de pacotes Python moderno e rápido)

### Instalação

1. Instale o UV:
```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/copo-do-mundo.git
cd copo-do-mundo
```

3. Crie e ative um ambiente virtual com UV:
```bash
uv venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

4. Instale as dependências com UV:
```bash
uv pip install .
```

5. Execute a aplicação:
```bash
streamlit run main.py
```

## 🛠️ Configuração

### Dependências do Projeto
O arquivo `pyproject.toml` gerencia todas as dependências e configurações do projeto:

```toml
[project]
name = "copo-do-mundo"
version = "1.0.0"
dependencies = [
    "streamlit",
    "pandas",
    "pillow",
    "seaborn"
]

[project.optional-dependencies]
dev = [
    "ruff"
]
```

### Configurações da Aplicação
O arquivo `config.py` permite personalizar diversos aspectos da aplicação:

- Senhas de acesso
- Número de participantes
- Categorias de drinks
- Configurações de imagem
- Mensagens do sistema

## 📁 Estrutura do Projeto

```
copo-do-mundo/
├── backend/
│   ├── data/           # Gerenciamento de dados
│   ├── image/          # Processamento de imagens
│   └── validation/     # Validadores
├── frontend/
│   ├── components/     # Componentes da UI
│   └── utils/         # Utilitários da interface
├── data/
│   ├── images/        # Armazenamento de fotos
│   └── votes.csv      # Dados das votações
├── config.py          # Configurações
├── main.py           # Ponto de entrada
├── pyproject.toml    # Configuração do projeto e dependências
└── README.md         # Documentação
```

## 🔒 Segurança

- Proteção por senha para área administrativa
- Validação de dados em tempo real
- Proteção contra votos duplicados
- Sistema de rate limiting

## 📱 Responsividade

A interface foi desenvolvida para funcionar em diversos dispositivos:
- 💻 Desktop
- 📱 Tablets
- 📱 Smartphones

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, sinta-se à vontade para:
- Reportar bugs
- Sugerir novas funcionalidades
- Enviar pull requests

### Desenvolvimento Local

1. Instale as dependências de desenvolvimento:
```bash
uv pip install ".[dev]"
```

2. Configure seu ambiente:
- Use `ruff` para formatação de código e linting

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.
