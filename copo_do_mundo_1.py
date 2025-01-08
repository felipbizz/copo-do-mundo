import streamlit as st
import pandas as pd

# Streamlit app
st.title("Votação COPO DO MUNDO")
st.image('image-copo-do-mundo.jpeg')

# Collect user name
name = st.text_input("Insira o seu nome:")

# Inicializa a lista para armazenar as votos
if 'votes_list' not in st.session_state:
    st.session_state.votes_list = []

col1, col2, col3 = st.columns(3)

with col1:
    Caipirinha_1 = st.number_input(f"Vote para Caipirinha_1 :",  0,  10,  0, key='Caipirinha_1')
    Caipirinha_2 = st.number_input(f"Vote para Caipirinha_2 :",  0,  10,  0, key='Caipirinha_2')
    Caipirinha_3 = st.number_input(f"Vote para Caipirinha_3 :",  0,  10,  0, key='Caipirinha_3')
    Caipirinha_4 = st.number_input(f"Vote para Caipirinha_4 :",  0,  10,  0, key='Caipirinha_4')

with col2:
    Livre_1 = st.number_input(f"Vote para Livre_1 :",  0,  10,  0, key='Livre_1')
    Livre_2 = st.number_input(f"Vote para Livre_2 :",  0,  10,  0, key='Livre_2')
    Livre_3 = st.number_input(f"Vote para Livre_3 :",  0,  10,  0, key='Livre_3')
    Livre_4 = st.number_input(f"Vote para Livre_4 :",  0,  10,  0, key='Livre_4')

with col3:
    LeiteCond_1 = st.number_input(f"Vote para LeiteCond_1 :",  0,  10,  0, key='LeiteCond_1')
    LeiteCond_2 = st.number_input(f"Vote para LeiteCond_2 :",  0,  10,  0, key='LeiteCond_2')
    LeiteCond_3 = st.number_input(f"Vote para LeiteCond_3 :",  0,  10,  0, key='LeiteCond_3')
    LeiteCond_4 = st.number_input(f"Vote para LeiteCond_4 :",  0,  10,  0, key='LeiteCond_4')

# "Send Results" button
if st.button("Enviar minhas notas"):
    votacao = {
        'Nome': [name,name, name, name,name,name, name, name,name,name, name, name],
        'Category': ['Caipirinha','Caipirinha', 'Caipirinha', 'Caipirinha',
                      'Livre',  'Livre', 'Livre', 'Livre', 
                      'LeiteCond', 'LeiteCond', 'LeiteCond', 'LeiteCond'],
        'Drink': ['Caipirinha_1', 'Caipirinha_2', 'Caipirinha_3', 'Caipirinha_4',
                'Livre_1', 'Livre_2', 'Livre_3','Livre_4',
                'LeiteCond_1', 'LeiteCond_2', 'LeiteCond_3', 'LeiteCond_4'],
        'Score': [f'{Caipirinha_1}', f'{Caipirinha_2}', f'{Caipirinha_3}', f'{Caipirinha_4}',
                 f'{Livre_1}', f'{Livre_2}', f'{Livre_3}', f'{Livre_4}',
                f'{LeiteCond_1}', f'{LeiteCond_2}', f'{LeiteCond_3}', f'{LeiteCond_4}']
            }
    st.session_state.votes_list.append(votacao)
    st.write(f"{name}'s votes foi submetido.")

if st.session_state.votes_list != []:

    df = pd.json_normalize(st.session_state.votes_list)
    df = df.explode(list(df.columns))
    df.Score = df.Score.astype(int)
    st.dataframe(df)

# Collect password
password_input = st.text_input("Insira a senha para exibir o resultado:", type="password")

# Display results button
if st.button("Exibir resultado"):
    if password_input == "senha":
        # Display the results as before
        st.header("Resultados")
        
        df = pd.json_normalize(st.session_state.votes_list)
        df = df.explode(list(df.columns))
        df.Score = df.Score.astype(int)
        # Calculate scores for each drink in each category
        scores = df.groupby(['Category', 'Drink'])['Score'].sum().reset_index()

        # Display scores for each drink in each category
        for category, category_df in scores.groupby('Category'):
            st.subheader(f"Notas para {category}:")
            for index, row in category_df.iterrows():
                st.write(f"{row['Drink']}: {row['Score']}")

            # Find the winner for each category
            winner = category_df.loc[category_df.groupby('Category')['Score'].idxmax()]['Drink'].values
            st.subheader(f"A maior nota de {category}: {winner} com pontuação total de {category_df.loc[category_df.groupby('Category')['Score'].idxmax()]['Score'].values}")

    else:
        st.error("Senha incorreta. Tente novamente")