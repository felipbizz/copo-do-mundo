import pandas as pd
import streamlit as st

# Streamlit app
st.title("Votação COPO DO MUNDO")
st.image("image-copo-do-mundo.jpeg")

# Inicializa a lista para armazenar as votos
if "votes_list" not in st.session_state:
    st.session_state.votes_list = []

col1, col2, col3 = st.columns(3)

with col1:
    # Collect user name
    name = st.text_input("Insira o seu nome:")
    originalidade = st.number_input("Vote para originalidade :", 0, 10, 0, key="originalidade")

with col2:
    categoria = st.selectbox("Qual a categoria?", ("Caipirinha", "Livre", "Leite Condensado"))
    aparencia = st.number_input("Vote para aparência :", 0, 10, 0, key="aparencia")

with col3:
    drink = st.selectbox("Qual o Drink?", ("1", "2", "3", "4"))
    sabor = st.number_input("Vote para sabor :", 0, 10, 0, key="sabor")

# "Send Results" button
if st.button("Enviar minhas notas"):
    votacao = {
        "Nome": name,
        "Categoria": categoria,
        "Drink": drink,
        "Originalidade": originalidade,
        "Aparencia": aparencia,
        "Sabor": sabor,
    }
    st.session_state.votes_list.append(votacao)
    st.write(f"{name}'s votes foi submetido.")

if st.session_state.votes_list != []:
    df = pd.json_normalize(st.session_state.votes_list)
    df = df.explode(list(df.columns))
    # df.Score = df.Score.astype(int)
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
        scores = (
            df.drop(columns=["Nome"]).groupby(["Categoria", "Drink"])["Score"].sum().reset_index()
        )

        # Display scores for each drink in each category
        for category, category_df in scores.groupby("Category"):
            st.subheader(f"Notas para {category}:")
            for _index, row in category_df.iterrows():
                st.write(f"{row['Drink']}: {row['Score']}")

            # Find the winner for each category
            winner = category_df.loc[category_df.groupby("Category")["Score"].idxmax()][
                "Drink"
            ].values
            st.subheader(
                f"""A maior nota de {category}: 
                {winner} com pontuação total de 
                {category_df.loc[category_df.groupby("Category")["Score"].idxmax()]["Score"].values}"""
            )

    else:
        st.error("Senha incorreta. Tente novamente")
