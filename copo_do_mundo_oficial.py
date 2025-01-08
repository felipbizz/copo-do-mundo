import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import seaborn as sns
import gspread
from oauth2client.service_account import ServiceAccountCredentials
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

json_file = 'copo-do-mundo-your_json.json'
sheel_url = 'https://docs.google.com/spreadsheets/d/your_spreadsheet'

creds = ServiceAccountCredentials.from_json_keyfile_name(json_file, scope)
client = gspread.authorize(creds)

sheet = client.open_by_url(sheel_url)

cm = sns.color_palette("blend:white,green", as_cmap=True)

st.title("Votação COPO DO MUNDO")
st.image('image-copo-do-mundo.jpeg')

col1, col2, col3 = st.columns(3)

with col1:
    name = st.text_input("Insira o seu nome:")
    originalidade = st.number_input(f"Vote para originalidade :",  0,  10,  0, key='originalidade')

with col2:
    categoria = st.selectbox('Qual a categoria?', 
                            ('Caipirinha', 'Livre', 'Leite Condensado'))
    aparencia = st.number_input(f"Vote para aparência :",  0,  10,  0, key='aparencia')

with col3:
    drink = st.selectbox('Qual o Drink?',
                        ('1', '2', '3', '4'))
    sabor = st.number_input(f"Vote para sabor :",  0,  10,  0, key='sabor')

if st.button("Enviar minhas notas"):
    
    voto = [name, categoria,drink, originalidade, aparencia, sabor]
    sheet.worksheet('copo_do_mundo').append_row(voto)
    st.success(f"Voto de {name} cadastrado corretamente!")
    
# Collect password
password_input = st.text_input("Insira a senha para exibir o resultado:", type="password")

# Display results button
if st.button("Exibir resultado"):
    if password_input == "senha":
        # Display the results as before
        st.header("Resultados")
        
        df = pd.DataFrame(sheet.worksheet('copo_do_mundo').get_all_records())
        # Calculate scores for each drink in each category
        df_sum = df.drop(columns=['Nome']).groupby(['Categoria', 'Drink']).sum().reset_index()

        df_sum = df_sum.style.background_gradient(cmap = cm,axis=None)
        st.dataframe(df_sum)

    else:
        st.error("Senha incorreta. Tente novamente")