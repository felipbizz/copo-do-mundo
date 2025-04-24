import os

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

credentials_dict = {
    "type": os.getenv("GOOGLE_SHEETS_TYPE"),
    "project_id": os.getenv("GOOGLE_SHEETS_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_SHEETS_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_SHEETS_PRIVATE_KEY").replace(
        "\\n", "\n"
    ),  # Replace escaped newlines
    "client_email": os.getenv("GOOGLE_SHEETS_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_SHEETS_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_SHEETS_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_SHEETS_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_SHEETS_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("GOOGLE_SHEETS_CLIENT_X509_CERT_URL"),
}

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

creds = Credentials.from_service_account_info(credentials_dict, scopes=SCOPE)
gc = gspread.authorize(creds)

spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
sh = gc.open_by_key(spreadsheet_id)

worksheet = sh.sheet1
data = worksheet.get_all_values()

sh.worksheet(
    os.getenv("GOOGLE_SHEETS_ABA_CODIGOS")
)  # nessa aba serão salvos os códigos e nomes dos drinks

voto = ["name", "categoria", "drink", "originalidade", "aparencia", "sabor"]

sh.worksheet(os.getenv("GOOGLE_SHEETS_ABA_VOTOS")).append_row(
    voto
)  ## dessa forma serão inseridos os votos

## Exemplo salvando fotos no drive

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

service = build("drive", "v3", credentials=creds)

file_path = "/home/felip/projetos/copo-do-mundo/modern_data_stack.png"

media = MediaFileUpload(file_path, mimetype="image/*")

file_name = "foto_teste"
parent_folder_id = "folder_id"

file_metadata = {"name": file_name}
if parent_folder_id:
    file_metadata["parents"] = [parent_folder_id]

file = (
    service.files()
    .create(media_body=media, body=file_metadata, fields="id, name, webViewLink")
    .execute()
)

print(
    f"Arquivo '{file.get('name')}' (ID: {file.get('id')}) enviado com sucesso. Link: {file.get('webViewLink')}"
)
