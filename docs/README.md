# Documentação do Projeto Copo do Mundo

## Visão Geral
O Copo do Mundo é uma aplicação web para gerenciamento de competições de drinks. O sistema permite que jurados avaliem drinks em diferentes categorias, fornecendo uma interface intuitiva para votação e visualização de resultados.

## Documentação

### Para Usuários
- [Manual do Usuário](user_manual.md) - Guia completo de uso do sistema
- [Configuração e Instalação](setup.md) - Como configurar e instalar o sistema

### Para Desenvolvedores
- [Arquitetura do Sistema](architecture.md) - Visão técnica da arquitetura
- [Guia de Desenvolvimento](development.md) - Como desenvolver e contribuir
- [API e Componentes](api.md) - Documentação técnica dos componentes

## Tecnologias Utilizadas
- Python 3.11+
- Streamlit (interface web)
- Pandas (manipulação de dados)
- Seaborn (visualização)
- PIL (processamento de imagens)

## Requisitos do Sistema
- Python 3.11 ou superior
- Sistema operacional: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- Navegador web moderno (Chrome recomendado)
- 4GB RAM mínimo
- 1GB espaço em disco

## Estrutura do Projeto
```
copo-do-mundo/
├── backend/
│   ├── data/         # Gerenciamento de dados e votos
│   ├── image/        # Processamento de imagens
│   └── validation/   # Validações e regras de negócio
├── frontend/
│   ├── components/   # Componentes da interface
│   └── utils/        # Utilitários da interface
├── docs/            # Documentação do projeto
└── config.py        # Configurações do sistema
```

## Componentes Principais

### Backend
- **DataManager**: Gerencia operações de dados e persistência
- **VoteManager**: Controla a lógica de votação e validação de votos
- **ImageManager**: Processa e gerencia imagens dos drinks
- **Validators**: Implementa regras de validação

### Frontend
- **VotingComponent**: Componente principal de votação
- **UIUtils**: Utilitários para interface do usuário
- **SessionManager**: Gerenciamento de sessão
- **CacheManager**: Cache de resultados e dados
- **Anonymizer**: Sistema de anonimização de participantes

## Funcionalidades Principais
1. Sistema de votação com critérios múltiplos
2. Visualização de resultados em tempo real
3. Gerenciamento de rascunhos de votos
4. Sistema de anonimização de participantes
5. Cache de resultados para melhor performance
6. Validação de votos duplicados
7. Interface responsiva e intuitiva

## Contribuição
Para contribuir com o projeto, consulte o [Guia de Desenvolvimento](development.md) e siga as diretrizes de contribuição. 