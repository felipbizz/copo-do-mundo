import base64
import json
import logging
import os
from datetime import datetime

import gspread
import pandas as pd
import seaborn as sns
import streamlit as st
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("copo_do_mundo.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

load_dotenv()

# Configurações constantes
SHEET_URL = os.getenv("GOOGLE_SHEET_URL")

cm = sns.color_palette("blend:white,green", as_cmap=True)


@st.cache_resource
def get_credentials():
    """Carrega e retorna as credenciais do Google Sheets."""
    SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    try:
        base64_creds = os.getenv("GOOGLE_SERVICE_ACCOUNT_CREDENTIALS")
        if base64_creds:
            credentials_json = base64.b64decode(base64_creds).decode("utf-8")
            credentials = Credentials.from_service_account_info(
                json.loads(credentials_json), scopes=SCOPES
            )
            return credentials
    except Exception as e:
        logger.error(f"Erro ao carregar credenciais do ambiente: {e}")

    raise Exception("Não foi possível carregar nenhuma credencial")


@st.cache_resource
def get_sheet():
    """Retorna a planilha do Google Sheets."""
    creds = get_credentials()
    client = gspread.authorize(creds)
    return client.open_by_url(SHEET_URL)


def get_results():
    """Retorna os resultados processados do Google Sheets."""
    try:
        sheet = get_sheet()
        df = pd.DataFrame(sheet.worksheet("copo_do_mundo").get_all_records())
        #df_sum = df.drop(columns=["Nome"]).groupby(["Categoria", "Drink"]).sum().reset_index()
        return df
    except Exception as e:
        logger.error(f"Erro ao obter resultados: {e}")
        raise


if __name__ == "__main__":
    # Configuração inicial
    st.set_page_config(
        page_title="Copo do Mundo",
        page_icon="🍹",
    )

    # Criar abas
    tab1, tab2 = st.tabs(["Votar", "Resultados"])

    with tab1:
        st.title("VI Copo do Mundo🍹")
        st.image("./copo_do_mundo.png", width=300)

        # Interface do usuário
        name = st.text_input("Digite o seu nome:", help="Nome de quem está votando")
        categoria = st.selectbox("Categoria:", ["Shot Perfeito", "Morango Blue", "Livre"])
        drink = st.selectbox("Qual o Drink?", ("1", "2", "3", "4", "5"))

        col1, col2, col3 = st.columns(3)
        with col1:
            originalidade = st.slider("Originalidade:", 0, 10, 5)
        with col2:
            aparencia = st.slider("Aparência:", 0, 10, 5)
        with col3:
            sabor = st.slider("Sabor:", 0, 10, 5)

        if st.button("Enviar minhas notas"):
            try:
                # Verifica se todos os campos obrigatórios foram preenchidos
                if not all([name, categoria, drink]):
                    raise ValueError("Por favor, preencha todos os campos obrigatórios")

                voto = [
                    name,
                    categoria,
                    drink,
                    originalidade,
                    aparencia,
                    sabor,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ]

                # Tenta registrar o voto com retry
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        sheet = get_sheet()
                        worksheet = sheet.worksheet("copo_do_mundo")
                        worksheet.append_row(voto)
                        st.success(
                            f"Voto de {name} no drink {drink} {categoria} cadastrado corretamente!"
                        )
                        logger.info(f"Voto registrado: {voto}")
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:  # Última tentativa
                            logger.error(f"Erro ao processar voto após {max_retries} tentativas: {e}")
                            st.error("Erro ao processar voto. Por favor, tente novamente.")
                        else:
                            logger.warning(f"Tentativa {attempt + 1} falhou. Tentando novamente...")
                            continue

            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                logger.error(f"Erro ao processar voto: {e}")
                st.error("Erro ao processar voto. Por favor, tente novamente.")

    with tab2:
        st.title("VI Copo do Mundo - Resultados 🍹")
        #st.image("./copo_do_mundo.png", width=300)

        # Coleta de senha
        password_input = st.text_input("Insira a senha para exibir o resultado:", type="password")

        # Botão para exibir resultados
        if st.button("Exibir resultado"):
            if password_input == "senha_admin":
                st.header("Resultados")
                try:
                    df = get_results()
                    
                    # Calcular os vencedores por categoria
                    winners = {}
                    for categoria in df['Categoria'].unique():
                        categoria_df = df[df['Categoria'] == categoria]
                        # Calcular a soma total de cada drink
                        categoria_df['Total'] = categoria_df[['Originalidade', 'Aparencia', 'Sabor']].sum(axis=1)
                        # Encontrar o drink com a maior pontuação total
                        winner_drink = categoria_df.loc[categoria_df['Total'].idxmax()]['Drink']
                        winners[categoria] = winner_drink
                    
                    # Mostrar os vencedores
                    st.subheader("🏆 Vencedores por Categoria")
                    for categoria, drink in winners.items():
                        st.write(f"- {categoria}: Drink {str(drink)}")
                    
                    # Calcular e mostrar tabela completa com somas
                    st.subheader("Total de Resultados")
                    # Primeiro agrupa e soma as colunas individuais
                    df_sum = df.groupby(['Categoria', 'Drink']).agg({
                        'Originalidade': 'sum',
                        'Aparencia': 'sum',
                        'Sabor': 'sum'
                    }).reset_index()
                    
                    # Calcula o total para cada linha
                    df_sum['Total'] = df_sum[['Originalidade', 'Aparencia', 'Sabor']].sum(axis=1)
                    
                    # Ordenar por categoria e total decrescente
                    df_sum = df_sum.sort_values(['Categoria', 'Total'], ascending=[True, False])
                    
                    # Estilizar a tabela
                    styled_df = df_sum.style.background_gradient(cmap=cm, axis=None)
                    st.dataframe(styled_df)
                except Exception as e:
                    logger.error(f"Erro ao carregar resultados: {e}")
                    st.error("Erro ao carregar resultados. Por favor, tente novamente.")
            else:
                st.error("Senha incorreta. Tente novamente")
