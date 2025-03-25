# Documentação da API

## Componentes do Sistema

### VotingComponent
Gerencia a interface e lógica de votação.

#### Métodos Principais
```python
def render(self) -> None:
    """Renderiza a interface de votação."""

def _render_voting_tab(self) -> None:
    """Renderiza a aba de votação."""

def _handle_vote_submission(self) -> None:
    """Processa o envio de um voto."""
```

### DataManager
Gerencia operações de dados e persistência.

#### Métodos Principais
```python
def save_vote(self, vote: Dict) -> bool:
    """Salva um voto no arquivo CSV."""

def load_votes(self) -> List[Dict]:
    """Carrega todos os votos do arquivo."""

def validate_vote(self, vote: Dict) -> bool:
    """Valida um voto antes de salvar."""
```

### VoteManager
Gerencia a lógica de votação.

#### Métodos Principais
```python
def create_vote(self, data: Dict) -> Dict:
    """Cria um novo voto."""

def check_duplicate(self, vote: Dict) -> bool:
    """Verifica se o voto é duplicado."""
```

### ImageManager
Gerencia processamento e exibição de imagens.

#### Métodos Principais
```python
def load_image(self, path: str) -> Image:
    """Carrega uma imagem do disco."""

def resize_image(self, image: Image, size: Tuple) -> Image:
    """Redimensiona uma imagem."""
```

## Utilitários

### UIUtils
Fornece utilitários para interface do usuário.

#### Métodos Principais
```python
def create_star_rating(self, key: str) -> None:
    """Cria um componente de avaliação por estrelas."""

def show_error(self, message: str) -> None:
    """Exibe uma mensagem de erro."""
```

### SessionManager
Gerencia o estado da sessão.

#### Métodos Principais
```python
def get_session(self, key: str) -> Any:
    """Obtém um valor da sessão."""

def set_session(self, key: str, value: Any) -> None:
    """Define um valor na sessão."""
```

### CacheManager
Gerencia cache de dados e resultados.

#### Métodos Principais
```python
def get_cached(self, key: str) -> Any:
    """Obtém um valor do cache."""

def set_cached(self, key: str, value: Any) -> None:
    """Define um valor no cache."""
```

### Anonymizer
Gerencia anonimização de dados.

#### Métodos Principais
```python
def generate_code(self) -> str:
    """Gera um código único."""

def anonymize_data(self, data: Dict) -> Dict:
    """Anonimiza dados sensíveis."""
```

## Configuração

### CONFIG
```python
CONFIG = {
    "IMAGES_DIR": "backend/image/images",
    "DATA_FILE": "backend/data/votes.csv",
    "VOTING_CRITERIA": {
        "Originalidade": "Criatividade da receita",
        "Aparência": "Apresentação visual",
        "Sabor": "Qualidade do gosto"
    }
}
```

### UI_MESSAGES
```python
UI_MESSAGES = {
    "WELCOME": "Bem-vindo ao Copo do Mundo!",
    "VOTE_SUCCESS": "Voto registrado com sucesso!",
    "VOTE_ERROR": "Erro ao registrar voto."
}
```

## Fluxos de Dados

### Votação
1. Usuário seleciona bebida
2. Avalia critérios
3. Sistema valida entrada
4. Voto é processado
5. Dados são salvos
6. Cache é atualizado

### Resultados
1. Dados são carregados
2. Resultados são calculados
3. Gráficos são gerados
4. Interface é atualizada

### Cache
1. Dados são solicitados
2. Cache é verificado
3. Dados são carregados
4. Cache é atualizado

## Tratamento de Erros

### Validação
- Verifica campos obrigatórios
- Valida tipos de dados
- Verifica regras de negócio

### Feedback
- Mensagens de erro claras
- Sugestões de correção
- Logs detalhados

### Recuperação
- Salvamento automático
- Recuperação de dados
- Estado consistente

## Segurança

### Anonimização
- Geração de códigos
- Mapeamento de dados
- Proteção de informações

### Validação
- Sanitização de entrada
- Verificação de integridade
- Proteção contra duplicidade

### Cache
- Limpeza periódica
- Invalidação seletiva
- Proteção de dados 