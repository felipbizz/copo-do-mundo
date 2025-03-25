# Guia de Configuração e Instalação

## Requisitos do Sistema

### Hardware
- Processador: 1.6 GHz ou superior
- Memória RAM: 4 GB mínimo
- Espaço em disco: 1 GB livre
- Resolução de tela: 1366x768 ou superior

### Software
- Sistema Operacional:
  - Windows 10/11
  - macOS 10.15 ou superior
  - Linux (Ubuntu 20.04 ou superior)
- Python 3.11 ou superior
- UV (gerenciador de pacotes Python)

## Instalação

### 1. Instale o Python e UV

#### Windows
```bash
# Instale o Python 3.11
# Baixe do site oficial: https://www.python.org/downloads/

# Instale o UV
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### macOS
```bash
# Instale o Homebrew (se não tiver)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instale o Python e UV
brew install python
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Linux (Ubuntu)
```bash
# Atualize o sistema
sudo apt update
sudo apt upgrade

# Instale o Python e UV
sudo apt install python3.11 python3.11-venv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Configure o Projeto

```bash
# Clone o repositório
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

### 3. Execute o Projeto

```bash
# Inicie o servidor
streamlit run main.py

# Acesse no navegador
# Abra http://localhost:8501
```

## Solução de Problemas

### Problemas Comuns

#### Erro de Dependências
```bash
# Atualize o UV
uv self upgrade

# Reinstale as dependências
uv pip install .
```

#### Erro de Ambiente Virtual
```bash
# Remova o ambiente virtual
rm -rf .venv

# Recrie o ambiente
uv venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Reinstale as dependências
uv pip install .
```

#### Erro de Porta
```bash
# Verifique processos usando a porta
lsof -i :8501

# Mate o processo se necessário
kill -9 <PID>
```

### Logs
```bash
# Verifique os logs
tail -f logs/app.log
```

## Manutenção

### Atualizações
```bash
# Atualize o código
git pull

# Atualize as dependências
uv pip install --upgrade .
```

### Backup
```bash
# Backup dos dados
cp data/votes.csv data/votes.csv.bak
``` 