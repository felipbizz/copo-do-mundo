import os
import streamlit as st
import pandas as pd
import seaborn as sns
from PIL import Image
import time

from backend.data.data_manager import DataManager
from backend.data.vote_manager import VoteManager
from backend.image.image_manager import ImageManager
from backend.validation.validators import Validators
from config import CONFIG, UI_MESSAGES
from frontend.utils.ui_utils import UIUtils

class VotingComponent:
    def __init__(self):
        self.data_manager = DataManager()
        self.vote_manager = VoteManager()
        self.image_manager = ImageManager()
        self.validators = Validators()
        self.ui = UIUtils()

    def render(self):
        """Render the voting section"""
        st.title(UI_MESSAGES["WELCOME_MESSAGE"])
        st.write(UI_MESSAGES["VOTING_INSTRUCTIONS"])

        # Initialize juror name in session state if not exists
        if "juror_name" not in st.session_state:
            st.session_state.juror_name = ""

        # Juror name input with container for better responsiveness
        name_container = st.container()
        with name_container:
            st.subheader("Identificação do Jurado")
            name = st.text_input(
                "Nome do Jurado", 
                value=st.session_state.juror_name, 
                key="juror_name_input"
            )
            st.session_state.juror_name = name

        if not name.strip():
            self.ui.show_warning_message("⚠️ Por favor, insira seu nome antes de começar a votação")
            return

        # Create tabs with container for better responsiveness
        tabs_container = st.container()
        with tabs_container:
            aba_votacao, aba_resultados = self.ui.create_tabs(["Votação", "Resultados"])

        # Results tab content
        with aba_resultados:
            self._render_results_tab()

        # Voting tab content
        with aba_votacao:
            self._render_voting_tab(name)

    def _render_results_tab(self):
        """Render the results tab"""
        if st.session_state.get("is_admin", False):
            st.session_state.results_access = True
            self._render_results()
        else:
            if not st.session_state.results_access:
                self.ui.show_info_message(UI_MESSAGES["RESULTS_LOCKED"])
                results_container = st.container()
                with results_container:
                    results_password = st.text_input(
                        "Senha dos Resultados", 
                        type="password", 
                        key="results_password_input"
                    )

                    if results_password:
                        if self.validators.validate_results_password(results_password):
                            with st.spinner("Verificando senha..."):
                                time.sleep(0.5)  # Add a small delay for better UX
                                st.session_state.results_access = True
                                self._render_results()
                        else:
                            self.ui.show_error_message(UI_MESSAGES["ERROR_RESULTS_PASSWORD"])
                            st.session_state.results_access = False
            else:
                # Add a button to clear results access
                if st.button("🔒 Fechar Resultados"):
                    st.session_state.results_access = False
                    st.rerun()
                self._render_results()

    def _render_voting_tab(self, name: str):
        """Render the voting tab"""
        # Create columns for selection and form
        col1, col2 = self.ui.create_columns([2, 1])

        with col1:
            # Drink selection with container for better responsiveness
            drink_container = st.container()
            with drink_container:
                st.subheader("Selecione o Drink")
                
                # Show draft votes if any
                if "draft_votes" in st.session_state and st.session_state.draft_votes:
                    with st.expander("📝 Rascunhos Salvos"):
                        for draft in st.session_state.draft_votes:
                            if draft["Nome"] == name:
                                st.markdown(f"""
                                **Participante: {draft['Participante']}**
                                **Categoria: {draft['Categoria']}**
                                - Originalidade: {draft['Originalidade']}/10
                                - Aparência: {draft['Aparencia']}/10
                                - Sabor: {draft['Sabor']}/10
                                """)
                                if st.button("Carregar Rascunho", key=f"load_draft_{draft['Participante']}_{draft['Categoria']}"):
                                    st.session_state.selected_participant = draft["Participante"]
                                    st.session_state.selected_category = draft["Categoria"]
                                    st.rerun()

                # Get valid participant range
                participants = list(range(1, st.session_state.num_participants + 1))
                
                # Validate and adjust selected participant
                selected_participant = st.session_state.get("selected_participant", 1)
                if selected_participant not in participants:
                    selected_participant = 1
                    st.session_state.selected_participant = selected_participant
                
                # Calculate valid index (0-based)
                participant_index = selected_participant - 1
                
                participant = st.selectbox(
                    "Participante",
                    options=participants,
                    key="voting_participant_select",
                    index=participant_index
                )

                # Validate and adjust selected category
                selected_category = st.session_state.get("selected_category", st.session_state.categories[0])
                if selected_category not in st.session_state.categories:
                    selected_category = st.session_state.categories[0]
                    st.session_state.selected_category = selected_category
                
                # Category selection
                categoria = st.selectbox(
                    "Categoria", 
                    options=st.session_state.categories,
                    key="voting_category_select",
                    index=st.session_state.categories.index(selected_category)
                )

                # Check for duplicate vote
                if self.vote_manager.check_duplicate_vote(
                    st.session_state.data, name, categoria, str(participant)
                ):
                    self._handle_duplicate_vote(name, categoria, participant)
                    return

                # Voting form
                self._render_voting_form(name, categoria, participant)

    def _render_voting_form(self, name: str, categoria: str, participant: int):
        """Render the voting form"""
        with st.form("voting_form", clear_on_submit=False):
            st.subheader(f"Participante {participant} - {categoria}")
            
            # Show drink photo with container for better responsiveness
            photo_container = st.container()
            with photo_container:
                image_path = os.path.join(CONFIG["IMAGES_DIR"], f"participant_{participant}_{categoria.lower()}.jpg")
                if os.path.exists(image_path):
                    image = self.image_manager.load_and_resize_image(image_path, width=300)
                    self.ui.display_image(image)
                else:
                    self.ui.show_info_message("Foto não disponível para este participante nesta categoria")

            # Voting criteria with container for better responsiveness
            criteria_container = st.container()
            with criteria_container:
                st.subheader("Avaliação")
                for criterion, description in CONFIG["VOTING_CRITERIA"].items():
                    st.write(f"**{criterion}**: {description}")
                    value = st.slider(criterion, 0, 10, 5)
                    if criterion == "Originalidade":
                        originalidade = value
                    elif criterion == "Aparencia":
                        aparencia = value
                    else:
                        sabor = value

            # Show vote summary
            st.markdown("### 📝 Resumo do Voto")
            st.markdown(f"""
            - **Participante:** {participant}
            - **Categoria:** {categoria}
            - **Originalidade:** {originalidade}/10
            - **Aparência:** {aparencia}/10
            - **Sabor:** {sabor}/10
            """)

            # Add keyboard shortcuts info
            with st.expander("⌨️ Atalhos de Teclado"):
                st.markdown("""
                - **Tab:** Navegar entre os campos
                - **Enter:** Enviar voto
                - **Esc:** Cancelar voto
                """)

            # Add voting progress
            total_votes = len(st.session_state.categories) * st.session_state.num_participants
            current_votes = len(st.session_state.data[st.session_state.data['Nome'] == name])
            progress = min(current_votes / total_votes, 1.0)
            st.progress(progress)
            st.markdown(f"**Progresso:** {current_votes}/{total_votes} votos ({progress*100:.1f}%)")

            # Form buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                submitted = st.form_submit_button("✅ Enviar Voto")
            with col2:
                if st.form_submit_button("💾 Salvar Rascunho"):
                    self._save_draft(name, categoria, participant, originalidade, aparencia, sabor)
            with col3:
                if st.form_submit_button("❌ Cancelar"):
                    st.rerun()

            if submitted:
                # Show confirmation dialog
                if st.session_state.get("confirm_vote", False):
                    self._handle_vote_submission(name, categoria, participant, originalidade, aparencia, sabor)
                else:
                    st.session_state.confirm_vote = True
                    st.warning("Tem certeza que deseja enviar este voto? Clique em 'Enviar Voto' novamente para confirmar.")

    def _save_draft(self, name: str, categoria: str, participant: int, originalidade: int, aparencia: int, sabor: int):
        """Save vote as draft"""
        draft = {
            "Nome": name,
            "Participante": participant,
            "Categoria": categoria,
            "Originalidade": originalidade,
            "Aparencia": aparencia,
            "Sabor": sabor,
            "Data": pd.Timestamp.now()
        }
        
        if "draft_votes" not in st.session_state:
            st.session_state.draft_votes = []
        
        # Remove any existing draft for this participant and category
        st.session_state.draft_votes = [
            d for d in st.session_state.draft_votes 
            if not (d["Participante"] == participant and d["Categoria"] == categoria)
        ]
        
        st.session_state.draft_votes.append(draft)
        self.ui.show_success_message("Voto salvo como rascunho!")
        time.sleep(0.5)
        st.rerun()

    def _handle_vote_submission(
        self, name: str, categoria: str, participant: int, originalidade: int, aparencia: int, sabor: int
    ):
        """Handle vote submission"""
        with st.spinner("Processando voto..."):
            # Validate input
            is_valid, error_message = self.validators.validate_vote_data(
                name, categoria, str(participant), st.session_state.num_participants
            )
            if not is_valid:
                self.ui.show_error_message(error_message)
                return

            # Check rate limit
            is_allowed, error_message = self.validators.check_rate_limit(
                st.session_state.last_votes, name
            )
            if not is_allowed:
                self.ui.show_error_message(error_message)
                return

            # Create and save vote
            new_vote = self.vote_manager.create_vote(
                name, categoria, str(participant), originalidade, aparencia, sabor
            )
            st.session_state.data = pd.concat([st.session_state.data, new_vote], ignore_index=True)

            if self.data_manager.save_data(st.session_state.data):
                self.ui.show_success_message(UI_MESSAGES["SUCCESS_VOTE"].format(name))
                st.balloons()

                # Check for missing votes
                missing_votes = self.vote_manager.get_missing_votes(
                    st.session_state.data,
                    name,
                    st.session_state.categories,
                    st.session_state.num_participants,
                )
                if missing_votes:
                    self.ui.show_warning_message("⚠️ Você ainda não votou nos seguintes participantes com foto disponível:")
                    for cat, part in missing_votes:
                        st.write(f"- Categoria {cat}: Participante {part}")
            else:
                self.ui.show_error_message(UI_MESSAGES["ERROR_SAVE_VOTE"])

    def _handle_duplicate_vote(self, name: str, categoria: str, participant: int):
        """Handle duplicate vote"""
        self.ui.show_warning_message(
            f"""Você já votou para o Participante {participant} na categoria {categoria}. 
            O que você deseja fazer?"""
        )
        
        action = st.radio(
            "Escolha uma opção:",
            ["Manter meu voto anterior", "Remover meu voto anterior para votar novamente"],
            key=f"duplicate_action_{participant}_{categoria}",
        )
        
        if action == "Remover meu voto anterior para votar novamente":
            if st.button("Confirmar remoção do voto", key=f"confirm_remove_{participant}_{categoria}"):
                with st.spinner("Removendo voto anterior..."):
                    st.session_state.data = self.vote_manager.remove_duplicate_vote(
                        st.session_state.data, name, categoria, str(participant)
                    )
                    if self.data_manager.save_data(st.session_state.data):
                        self.ui.show_success_message("Voto anterior removido. Agora você pode votar novamente.")
                        time.sleep(0.5)  # Add a small delay for better UX
                        st.rerun()
        else:
            self.ui.show_info_message("Você pode continuar votando em outros participantes ou categorias.")
            st.stop()

    def _render_results(self):
        """Render results section"""
        if not st.session_state.data.empty:
            st.title("📊 Resultados da Competição")

            try:
                with st.spinner("Calculando resultados..."):
                    # Create a copy of the data to avoid SettingWithCopyWarning
                    data_copy = st.session_state.data.copy()
                    
                    # Ensure data types are correct
                    data_copy['Drink'] = data_copy['Drink'].astype(int)
                    data_copy['Originalidade'] = data_copy['Originalidade'].astype(float)
                    data_copy['Aparencia'] = data_copy['Aparencia'].astype(float)
                    data_copy['Sabor'] = data_copy['Sabor'].astype(float)
                    
                    # Calculate results
                    df_avg, winners = self.data_manager.calculate_results(data_copy)
                    
                    if df_avg is not None and not df_avg.empty:
                        self._render_winners(df_avg, winners)
                        self._render_statistics(data_copy)
                        self._render_detailed_results(df_avg)
                    else:
                        self.ui.show_error_message("Erro ao calcular os resultados. Verifique se há dados válidos.")
            except Exception as e:
                self.ui.show_error_message(f"Erro ao processar resultados: {str(e)}")
                st.write("Stack trace:", e.__traceback__)
        else:
            self.ui.show_info_message(UI_MESSAGES["INFO_NO_DATA"])

    def _render_winners(self, df_avg, winners):
        """Render winners section"""
        st.subheader("🏆 Vencedores por Categoria")
        cols = self.ui.create_columns(len(winners))
        
        for idx, (cat, result) in enumerate(winners.items()):
            with cols[idx]:
                st.markdown(f"### {cat}")
                # Get participant name from the mapping
                participant_name = st.session_state.participant_names.get(
                    result["participant"], 
                    f"Participante {result['participant']}"
                )
                st.markdown(f"**{participant_name}**")
                st.markdown(f"**Pontuação: {result['score']:.2f}**")
                st.markdown("---")
                st.markdown(f"**Detalhes:**")
                st.markdown(f"- Originalidade: {df_avg.loc[(result['participant'], cat), 'Originalidade']:.2f}")
                st.markdown(f"- Aparência: {df_avg.loc[(result['participant'], cat), 'Aparencia']:.2f}")
                st.markdown(f"- Sabor: {df_avg.loc[(result['participant'], cat), 'Sabor']:.2f}")

    def _render_statistics(self, data):
        """Render statistics section"""
        st.markdown("---")
        total_votes = self.data_manager.get_total_votes(data)
        st.markdown(f"### 📈 Estatísticas")
        st.markdown(f"**Total de votos:** {total_votes}")

    def _render_detailed_results(self, df_avg):
        """Render detailed results section"""
        with self.ui.create_expander("Ver todos os resultados detalhados"):
            st.subheader("Resultados Detalhados")
            
            # Create a copy of the DataFrame for display
            display_df = df_avg.copy()
            
            # Add participant names
            display_df.index = pd.MultiIndex.from_tuples(
                [(st.session_state.participant_names.get(p, f"Participante {p}"), c) 
                 for p, c in display_df.index],
                names=["Participante", "Categoria"]
            )
            
            # Style the DataFrame
            cm = sns.color_palette("blend:white,green", as_cmap=True)
            st.dataframe(display_df.style.background_gradient(cmap=cm)) 