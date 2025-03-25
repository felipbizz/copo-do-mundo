# Guia de Desenvolvimento

## Configuração do Ambiente

### Requisitos
- Python 3.11+
- UV (gerenciador de pacotes)
- Git
- Editor de código (VS Code recomendado)

### Instalação
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

## Estrutura do Projeto

```
copo-do-mundo/
├── backend/           # Lógica de negócio
├── frontend/         # Interface do usuário
├── docs/            # Documentação
├── tests/           # Testes
├── main.py          # Ponto de entrada
└── pyproject.toml   # Configuração do projeto
```

## Convenções de Código

### Python
- Siga PEP 8
- Use docstrings em todas as funções
- Mantenha funções pequenas e focadas
- Use type hints

### Git
- Commits atômicos
- Mensagens descritivas
- Branches para features
- Pull requests para revisão

## Desenvolvimento

### Iniciando o Projeto
```bash
# Ative o ambiente virtual
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Execute o projeto
streamlit run main.py
```

### Fluxo de Trabalho
1. Crie uma branch para sua feature
2. Desenvolva e teste localmente
3. Faça commit das mudanças
4. Crie um pull request

### Testes
```bash
# Execute todos os testes
pytest

# Execute testes específicos
pytest tests/test_voting.py
```

## Componentes Principais

### VotingComponent
- Gerencia interface de votação
- Validação de entrada
- Processamento de votos

### DataManager
- Persistência de dados
- Cache
- Validação

### ImageManager
- Processamento de imagens
- Cache de imagens
- Otimização

## Boas Práticas

### Código
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple, Stupid)
- SOLID principles
- Clean Code

### Git
- Commits frequentes
- Branches descritivas
- Code review
- CI/CD

### Performance
- Cache quando possível
- Otimização de queries
- Lazy loading
- Compressão

## Debugging

### Logs
```python
import logging

logging.info("Mensagem informativa")
logging.error("Erro ocorreu", exc_info=True)
```

### Debugger
- Use breakpoints no VS Code
- Inspecione variáveis
- Step through code
- Watch expressions

## Deploy

### Preparação
- Atualize dependências
- Execute testes
- Verifique logs
- Backup de dados

### Processo
```bash
# Atualize o código
git pull

# Instale dependências
uv pip install .

# Execute testes
pytest

# Inicie o servidor
streamlit run main.py
```

## Manutenção

### Atualizações
- Atualize dependências
- Execute testes
- Verifique logs
- Backup de dados

### Monitoramento
- Logs de erro
- Métricas de performance
- Uso de recursos
- Tempo de resposta

## Contribuição

### Processo
1. Fork o repositório
2. Crie uma branch
3. Desenvolva e teste
4. Faça pull request

### Padrões
- Código limpo
- Testes incluídos
- Documentação atualizada
- Commits atômicos

## Recursos Adicionais

### Documentação
- [Streamlit Docs](https://docs.streamlit.io)
- [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/) 