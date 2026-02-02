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
    "QUOTA_PROTECTION_ENABLED": os.getenv("QUOTA_PROTECTION_ENABLED", "true").lower()
    == "true",
}

# GCP Free Tier Quota Limits
# These can be overridden via environment variables
QUOTA_LIMITS = {
    "bigquery": {
        "storage_gb": float(os.getenv("BIGQUERY_STORAGE_LIMIT_GB", "10")),
        "queries_tb": float(os.getenv("BIGQUERY_QUERIES_LIMIT_TB", "1")),
        "streaming_gb": float(os.getenv("BIGQUERY_STREAMING_LIMIT_GB", "10")),
        # Estimated average row size in bytes (for vote records)
        "avg_row_size_bytes": 200,
    },
    "cloud_storage": {
        "storage_gb": float(os.getenv("CLOUD_STORAGE_STORAGE_LIMIT_GB", "5")),
        "egress_gb": float(os.getenv("CLOUD_STORAGE_EGRESS_LIMIT_GB", "5")),
        "class_a_ops": int(os.getenv("CLOUD_STORAGE_CLASS_A_LIMIT", "5000")),
        "class_b_ops": int(os.getenv("CLOUD_STORAGE_CLASS_B_LIMIT", "50000")),
    },
}

# Quota Protection Thresholds (as percentages)
QUOTA_THRESHOLDS = {
    "warning": float(os.getenv("QUOTA_WARNING_THRESHOLD", "70")),  # 70%
    "critical": float(os.getenv("QUOTA_CRITICAL_THRESHOLD", "90")),  # 90%
    "emergency": float(os.getenv("QUOTA_EMERGENCY_THRESHOLD", "95")),  # 95%
}

# Rate Limiting Configuration
RATE_LIMITS = {
    "bigquery": {
        "query": {"max_ops": int(os.getenv("BQ_QUERY_RATE_LIMIT", "100")), "window": 60},
        "insert": {"max_ops": int(os.getenv("BQ_INSERT_RATE_LIMIT", "1000")), "window": 60},
        "load": {"max_ops": int(os.getenv("BQ_LOAD_RATE_LIMIT", "10")), "window": 60},
    },
    "cloud_storage": {
        "upload": {"max_ops": int(os.getenv("GCS_UPLOAD_RATE_LIMIT", "100")), "window": 60},
        "download": {"max_ops": int(os.getenv("GCS_DOWNLOAD_RATE_LIMIT", "200")), "window": 60},
        "delete": {"max_ops": int(os.getenv("GCS_DELETE_RATE_LIMIT", "50")), "window": 60},
    },
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
    "ERROR_PHOTO": "Erro ao processar foto: {}",
    "VOTE_REMOVED": "Voto anterior removido. Agora você pode votar novamente.",
}

# Para votar:
#     1. Digite seu nome
#     2. Selecione o número do participante
#     3. Selecione a categoria
#     4. Avalie o drink nos critérios abaixo
#     5. Envie seu voto
