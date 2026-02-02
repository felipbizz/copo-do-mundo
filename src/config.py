import os

CONFIG = {
    "DATA_FILE": "data/votes.csv",
    "IMAGES_DIR": "data/images",
    "NUM_PARTICIPANTS": 4,  # Number of participants
    "CATEGORIES": ["Shot Perfeito", "Morango Blu", "Livre"],  # Competition categories
    "PARTICIPANT_NAMES": {
        1: "Participante 1",
        2: "Participante 2",
        3: "Participante 3",
        4: "Participante 4",
    },
    "IMAGE_MAX_SIZE": (800, 800),
    "ADMIN_PASSWORD": os.getenv("ADMIN_PASSWORD", "admin2024"),
    "IMAGE_QUALITY": 85,
    "ALLOWED_IMAGE_TYPES": ["png", "jpg", "jpeg"],
    # Storage backend configuration
    "STORAGE_BACKEND": os.getenv("STORAGE_BACKEND", "local"),  # "local" or "gcp"
    # GCP configuration
    "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID"),
    "BIGQUERY_DATASET": os.getenv("BIGQUERY_DATASET", "copo_do_mundo"),
    "BIGQUERY_TABLE": os.getenv("BIGQUERY_TABLE", "votes"),
    "CLOUD_STORAGE_BUCKET": os.getenv("CLOUD_STORAGE_BUCKET"),
}

# Column names for consistency
COLUMNS = [
    "Timestamp",
    "Nome",
    "Categoria",
    "Participante",
    "Originalidade",
    "Aparencia",
    "Sabor",
]

# UI Constants
UI_MESSAGES = {
    "ERROR_NOME_REQUIRED": "⚠️ Por favor, insira seu nome antes de começar a votação",
    "ERROR_DUPLICATE_VOTE": "Você já votou para o Participante #{} na categoria {}!",
    "SUCCESS_VOTE": "✅ Voto registrado com sucesso!",
    "ERROR_PASSWORD": "Senha incorreta. Tente novamente.",
    "WELCOME_MESSAGE": "🍹 Bem-vindo ao Copo do Mundo!",
    "ADMIN_WELCOME": "Área Administrativa! 👨‍💼",
    "VOTING_INSTRUCTIONS": """

    """,
    "ERROR_SAVE_VOTE": "❌ Erro ao salvar o voto. Tente novamente.",
    "ERROR_LOAD_IMAGE": "Erro ao carregar imagem: {}",
    "ERROR_OPTIMIZE_IMAGE": "Erro ao otimizar imagem: {}",
    "ERROR_EXPORT_DATA": "Erro ao exportar dados: {}",
    "VOTE_REMOVED": "Voto anterior removido. Agora você pode votar novamente.",
}

# Para votar:
#     1. Digite seu nome
#     2. Selecione o número do participante
#     3. Selecione a categoria
#     4. Avalie o drink nos critérios abaixo
#     5. Envie seu voto
