import os
from datetime import timedelta

CONFIG = {
    "DATA_FILE": "data/votes.csv",
    "IMAGES_DIR": "data/images",
    "DEFAULT_NUM_DRINKS": 4,
    "DEFAULT_CATEGORIES": ["Caipirinha", "Livre", "Leite Condensado"],
    "IMAGE_MAX_SIZE": (800, 800),
    "ADMIN_PASSWORD": "admin2024",
    "RESULTS_PASSWORD": "copo2024",
    "IMAGE_QUALITY": 85,
    "ALLOWED_IMAGE_TYPES": ["png", "jpg", "jpeg"],
    "RATE_LIMIT": 5,  # seconds between votes
    "CACHE_TTL": 300,  # 5 minutes
    "IMAGE_CACHE_TTL": 600,  # 10 minutes
    "NUM_PARTICIPANTS": 4,  # Number of participants
    "CATEGORIES": ["Caipirinha", "Livre", "Leite Condensado"],  # Competition categories
    "PARTICIPANT_NAMES": {
        1: "Participante 1",
        2: "Participante 2",
        3: "Participante 3",
        4: "Participante 4"
    },
    "VOTING_CRITERIA": {
        "Originalidade": "Avalie a criatividade e inovação do drink",
        "Aparencia": "Avalie a apresentação visual do drink",
        "Sabor": "Avalie o sabor e equilíbrio do drink"
    },
}

# Column names for consistency
COLUMNS = [
    "Timestamp",
    "Nome",
    "Categoria",
    "Drink",
    "Originalidade",
    "Aparencia",
    "Sabor",
]

# UI Constants
UI_MESSAGES = {
    "ERROR_NOME_REQUIRED": "⚠️ Por favor, insira seu nome antes de começar a votação",
    "ERROR_DUPLICATE_VOTE": "Você já votou para o Drink #{} na categoria {}!",
    "SUCCESS_VOTE": "✅ Voto registrado com sucesso!",
    "ERROR_PASSWORD": "Senha incorreta. Tente novamente.",
    "ERROR_ADMIN_PASSWORD": "Senha de administrador incorreta. Tente novamente.",
    "ERROR_RESULTS_PASSWORD": "❌ Senha incorreta!",
    "INFO_NO_DATA": "📊 Nenhum voto registrado ainda.",
    "SUCCESS_PHOTO": "Foto salva com sucesso!",
    "ERROR_PHOTO": "Erro ao salvar imagem: {}",
    "WELCOME_MESSAGE": "🍹 Bem-vindo ao Copo do Mundo!",
    "ADMIN_WELCOME": "Área Administrativa! 👨‍💼",
    "VOTING_INSTRUCTIONS": """
    Para votar:
    1. Digite seu nome
    2. Selecione o número do participante
    3. Selecione a categoria
    4. Avalie o drink nos critérios abaixo
    5. Envie seu voto
    """,
    "RESULTS_LOCKED": "🔒 Os resultados estão bloqueados. Digite a senha para visualizar.",
    "ERROR_RATE_LIMIT": "⏳ Aguarde alguns segundos entre os votos",
    "ERROR_SAVE_VOTE": "❌ Erro ao salvar o voto. Tente novamente.",
    "ERROR_LOAD_DATA": "Erro ao carregar dados: {}",
    "ERROR_LOAD_IMAGE": "Erro ao carregar imagem: {}",
    "ERROR_OPTIMIZE_IMAGE": "Erro ao otimizar imagem: {}",
    "ERROR_EXPORT_DATA": "Erro ao exportar dados: {}",
}
