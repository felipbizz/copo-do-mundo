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
    """
    Component responsible for managing the voting interface and results display.
    
    This component handles:
    - Voting form display and submission
    - Results visualization
    - Draft vote management
    - Duplicate vote handling
    """
    
    def __init__(self):
        """Initialize component dependencies."""
        self.data_manager = DataManager()
        self.vote_manager = VoteManager()
        self.image_manager = ImageManager()
        self.validators = Validators()
        self.ui = UIUtils()

    # Main Rendering Methods
    # --------------------

    def render(self):
        """Main entry point for rendering the voting section."""
        self._setup_page()
        name = self._get_juror_name()
        
        if not name.strip():
            self.ui.show_warning_message(UI_MESSAGES["ERROR_NOME_REQUIRED"])
            return

        # Create tabs
        tab_votacao, tab_resultados = st.tabs(["Votação", "Resultados"])

        # Render voting tab
        with tab_votacao:
            self._render_voting_tab(name)

        # Render results tab
        with tab_resultados:
            self._render_results_tab()

    def _setup_page(self):
        """Setup initial page elements."""
        st.title(UI_MESSAGES["WELCOME_MESSAGE"])
        st.write(UI_MESSAGES["VOTING_INSTRUCTIONS"])

    def _get_juror_name(self) -> str:
        """Get and manage juror name input."""
        name_container = st.container()
        with name_container:
            st.subheader("Identificação do Jurado")
            name = st.text_input(
                "Nome do Jurado", 
                value=st.session_state.get("juror_name", ""),
                key="juror_name_input"
            ).strip()
            
            if name:  # Only update session state if we have a valid name
                st.session_state.juror_name = name
            
        return st.session_state.get("juror_name", "")

    # Voting Interface Methods
    # ----------------------

    def _render_voting_tab(self, name: str):
        """Render the main voting interface."""
        col1, col2 = self.ui.create_columns([2, 1])

        with col1:
            self._render_drink_selection(name)

    def _render_drink_selection(self, name: str):
        """Handle drink selection and form display."""
        with st.container():
            st.subheader("Selecione o Drink")
            self._show_draft_votes(name)
            
            participant = self._get_participant_selection()
            categoria = self._get_category_selection()

            if self.vote_manager.check_duplicate_vote(
                st.session_state.data, name, categoria, str(participant)
            ):
                self._handle_duplicate_vote(name, categoria, participant)
                return

            self._render_voting_form(name, categoria, participant)

    def _get_participant_selection(self) -> int:
        """Handle participant selection logic."""
        participants = list(range(1, st.session_state.num_participants + 1))
        selected_participant = st.session_state.get("selected_participant", 1)
        
        if selected_participant not in participants:
            selected_participant = 1
            st.session_state.selected_participant = selected_participant
        
        participant_index = selected_participant - 1
        
        return st.selectbox(
            "Participante",
            options=participants,
            key="voting_participant_select",
            index=participant_index
        )

    def _get_category_selection(self) -> str:
        """Handle category selection logic."""
        selected_category = st.session_state.get("selected_category", st.session_state.categories[0])
        if selected_category not in st.session_state.categories:
            selected_category = st.session_state.categories[0]
            st.session_state.selected_category = selected_category
        
        return st.selectbox(
            "Categoria", 
            options=st.session_state.categories,
            key="voting_category_select",
            index=st.session_state.categories.index(selected_category)
        )

    def _show_draft_votes(self, name: str):
        """Display saved draft votes."""
        if "draft_votes" in st.session_state and st.session_state.draft_votes:
            with st.expander("📝 Rascunhos Salvos"):
                for draft in st.session_state.draft_votes:
                    if draft["Nome"] == name:
                        self._render_draft_vote(draft)

    def _render_draft_vote(self, draft: dict):
        """Render a single draft vote."""
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

    # Results Display Methods
    # ---------------------

    def _render_results_tab(self):
        """Manage results tab display and access control."""
        # Check if we have access to results (only via admin)
        if not st.session_state.get("results_access", False):
            self.ui.show_info_message("🔒 Área restrita. Acesse como administrador para visualizar os resultados.")
            return

        # Show results if we have access
        self._render_results()

    def _render_results(self):
        """Display competition results."""
        if st.session_state.data.empty:
            self.ui.show_info_message(UI_MESSAGES["INFO_NO_DATA"])
            return

        st.title("📊 Resultados da Competição")
        try:
            df_avg, winners = self._calculate_results()
            if not df_avg.empty:
                self._render_winners(df_avg, winners)
                self._render_statistics(st.session_state.data)
                self._render_detailed_results(df_avg)
            else:
                self.ui.show_error_message("Erro ao calcular os resultados. Verifique se há dados válidos.")
        except Exception as e:
            self._handle_results_error(e)

    def _calculate_results(self) -> tuple[pd.DataFrame, dict]:
        """Calculate competition results."""
        with st.spinner("Calculando resultados..."):
            data_copy = st.session_state.data.copy()
            data_copy = self._prepare_data_types(data_copy)
            
            df_avg = self._calculate_averages(data_copy)
            winners = self._determine_winners(df_avg)
            
            return df_avg, winners

    def _prepare_data_types(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare data types for calculation."""
        data['Participante'] = data['Participante'].astype(str)
        data['Originalidade'] = data['Originalidade'].astype(float)
        data['Aparencia'] = data['Aparencia'].astype(float)
        data['Sabor'] = data['Sabor'].astype(float)
        return data

    def _calculate_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate average scores."""
        df_avg = data.groupby(['Categoria', 'Participante']).agg({
            'Originalidade': 'mean',
            'Aparencia': 'mean',
            'Sabor': 'mean'
        }).round(2)
        
        df_avg['Pontuação Total'] = df_avg[['Originalidade', 'Aparencia', 'Sabor']].sum(axis=1)
        return df_avg

    def _determine_winners(self, df_avg: pd.DataFrame) -> dict:
        """Determine winners for each category."""
        winners = {}
        for cat in df_avg.index.get_level_values('Categoria').unique():
            cat_scores = df_avg.loc[cat]
            winner_idx = cat_scores['Pontuação Total'].idxmax()
            winners[cat] = {
                'participant': winner_idx,
                'score': cat_scores.loc[winner_idx, 'Pontuação Total']
            }
        return winners

    def _handle_results_error(self, error: Exception):
        """Handle and display results calculation errors."""
        self.ui.show_error_message(f"Erro ao processar resultados: {str(error)}")
        st.write("Stack trace:", error.__traceback__)

    # Vote Management Methods
    # ---------------------

    def _handle_vote_submission(
        self, name: str, categoria: str, participant: int, 
        originalidade: int, aparencia: int, sabor: int
    ):
        """Process vote submission."""
        with st.spinner("Processando voto..."):
            if not self._validate_vote(name, categoria, participant):
                return

            if not self._check_rate_limit(name):
                return

            self._save_vote(name, categoria, participant, originalidade, aparencia, sabor)

    def _validate_vote(self, name: str, categoria: str, participant: int) -> bool:
        """Validate vote data."""
        is_valid, error_message = self.validators.validate_vote_data(
            name, categoria, str(participant), st.session_state.num_participants
        )
        if not is_valid:
            self.ui.show_error_message(error_message)
            return False
        return True

    def _check_rate_limit(self, name: str) -> bool:
        """Check voting rate limit."""
        is_allowed, error_message = self.validators.check_rate_limit(
            st.session_state.last_votes, name
        )
        if not is_allowed:
            self.ui.show_error_message(error_message)
            return False
        return True

    def _save_vote(
        self, name: str, categoria: str, participant: int, 
        originalidade: int, aparencia: int, sabor: int
    ):
        """Save the vote and handle success/failure."""
        new_vote = self.vote_manager.create_vote(
            name, categoria, str(participant), originalidade, aparencia, sabor
        )
        st.session_state.data = pd.concat([st.session_state.data, new_vote], ignore_index=True)

        if self.data_manager.save_data(st.session_state.data):
            self._handle_successful_vote(name)
        else:
            self.ui.show_error_message(UI_MESSAGES["ERROR_SAVE_VOTE"])

    def _handle_successful_vote(self, name: str):
        """Handle successful vote submission."""
        self.ui.show_success_message(UI_MESSAGES["SUCCESS_VOTE"].format(name))
        st.balloons()
        self._show_missing_votes(name)

    def _show_missing_votes(self, name: str):
        """Show remaining votes for the user."""
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

    def _handle_duplicate_vote(self, name: str, categoria: str, participant: int):
        """Handle duplicate vote scenarios."""
        self.ui.show_warning_message(
            UI_MESSAGES["ERROR_DUPLICATE_VOTE"].format(participant, categoria)
        )
        
        action = self._get_duplicate_vote_action(participant, categoria)
        
        if action == "Remover meu voto anterior para votar novamente":
            self._handle_vote_removal(name, categoria, participant)
        else:
            self.ui.show_info_message("Você pode continuar votando em outros participantes ou categorias.")
            st.stop()

    def _get_duplicate_vote_action(self, participant: int, categoria: str) -> str:
        """Get user action for duplicate vote."""
        return st.radio(
            "Escolha uma opção:",
            ["Manter meu voto anterior", "Remover meu voto anterior para votar novamente"],
            key=f"duplicate_action_{participant}_{categoria}",
        )

    def _handle_vote_removal(self, name: str, categoria: str, participant: int):
        """Handle vote removal process."""
        if st.button("Confirmar remoção do voto", key=f"confirm_remove_{participant}_{categoria}"):
            with st.spinner("Removendo voto anterior..."):
                st.session_state.data = self.vote_manager.remove_duplicate_vote(
                    st.session_state.data, name, categoria, str(participant)
                )
                if self.data_manager.save_data(st.session_state.data):
                    self.ui.show_success_message(UI_MESSAGES["VOTE_REMOVED"])
                    time.sleep(0.5)
                    st.rerun()

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
                    self.ui.show_info_message(UI_MESSAGES["NO_PHOTO_AVAILABLE"])

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
            st.markdown(f"### {UI_MESSAGES['VOTE_SUMMARY']}")
            st.markdown(f"""
            - **Participante:** {participant}
            - **Categoria:** {categoria}
            - **Originalidade:** {originalidade}/10
            - **Aparência:** {aparencia}/10
            - **Sabor:** {sabor}/10
            """)

            # Add keyboard shortcuts info
            with st.expander("⌨️ Atalhos de Teclado"):
                st.markdown(UI_MESSAGES["KEYBOARD_SHORTCUTS"])

            # Add voting progress
            total_votes = len(st.session_state.categories) * st.session_state.num_participants
            current_votes = len(st.session_state.data[st.session_state.data['Nome'] == name])
            progress = min(current_votes / total_votes, 1.0)
            st.progress(progress)
            st.markdown(UI_MESSAGES["VOTING_PROGRESS"].format(current_votes, total_votes, progress*100))

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
        self.ui.show_success_message(UI_MESSAGES["DRAFT_SAVED"])
        time.sleep(0.5)
        st.rerun()

    def _render_winners(self, df_avg, winners):
        """Render winners section"""
        st.subheader("🏆 Vencedores por Categoria")
        cols = self.ui.create_columns(len(winners))
        
        for idx, (cat, result) in enumerate(winners.items()):
            with cols[idx]:
                st.markdown(f"### {cat}")
                participant = result["participant"]
                
                # Get participant name from the mapping
                participant_name = st.session_state.participant_names.get(
                    int(participant), 
                    f"Participante {participant}"
                )
                st.markdown(f"**{participant_name}**")
                st.markdown(f"**Pontuação: {result['score']:.2f}**")
                st.markdown("---")
                st.markdown(f"**Detalhes:**")
                
                # Get scores for this participant and category
                scores = df_avg.loc[(cat, participant)]
                st.markdown(f"- Originalidade: {scores['Originalidade']:.2f}")
                st.markdown(f"- Aparência: {scores['Aparencia']:.2f}")
                st.markdown(f"- Sabor: {scores['Sabor']:.2f}")

    def _render_statistics(self, data):
        """Render statistics section"""
        st.markdown("---")
        total_votes = self.data_manager.get_total_votes(data)
        st.markdown(f"### 📈 Estatísticas")
        st.markdown(f"**Total de votos:** {total_votes}")

    def _render_detailed_results(self, df_avg):
        """Render detailed results section"""
        with st.expander("Ver todos os resultados detalhados"):
            st.subheader("Resultados Detalhados")
            
            # Create a copy of the DataFrame for display
            display_df = df_avg.copy()
            
            # Reset index to make it easier to work with
            display_df = display_df.reset_index()
            
            # Add participant names
            display_df['Participante'] = display_df['Participante'].apply(
                lambda x: st.session_state.participant_names.get(int(x), f"Participante {x}")
            )
            
            # Set the index back
            display_df = display_df.set_index(['Participante', 'Categoria'])
            
            # Sort the index
            display_df = display_df.sort_index()
            
            # Style the DataFrame
            cm = sns.color_palette("blend:white,green", as_cmap=True)
            styled_df = display_df.style.background_gradient(cmap=cm, subset=['Pontuação Total'])
            st.dataframe(styled_df) 