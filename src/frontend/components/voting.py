import os
import time

import pandas as pd
import seaborn as sns
import streamlit as st

from backend.data.data_manager import DataManager
from backend.data.vote_manager import VoteManager
from backend.image.image_manager import ImageManager
from backend.validation.validators import Validators
from config import CONFIG, UI_MESSAGES
from frontend.utils.anonymizer import Anonymizer
from frontend.utils.cache_manager import CacheManager
from frontend.utils.session_manager import SessionManager
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
        CacheManager.initialize_cache()
        Anonymizer.initialize_anonymization()
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
            current_name = SessionManager.get("juror_name", "")
            name = st.text_input(
                "Nome do Jurado", value=current_name, key="juror_name_input"
            ).strip()

            # Check if name has changed
            if name != current_name:
                SessionManager.set("juror_name", name)
                # Clear other related states when name changes
                SessionManager.reset_voting_state()
                st.rerun()

        return SessionManager.get("juror_name", "")

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

            # Get all available codes
            available_codes = self._get_available_codes()
            if not available_codes:
                st.warning("Nenhum drink disponível para votação.")
                return

            # Create a mapping of display names to codes
            code_options = {Anonymizer.get_drink_name(code): code for code in available_codes}

            # Let user select a drink by name
            selected_name = st.selectbox(
                "Nome do Drink",
                options=list(code_options.keys()),
                key="voting_drink_select",
                help="Selecione o drink que deseja avaliar",
            )

            if selected_name:
                selected_code = code_options[selected_name]
                self._render_voting_form(name, selected_code)

    def _get_available_codes(self) -> list:
        """Get list of available drink codes"""
        # Get all codes that have photos
        available_codes = []
        for code in Anonymizer.get_all_codes():
            participant, categoria = Anonymizer.get_participant_from_code(code)
            image_path = os.path.join(
                CONFIG["IMAGES_DIR"], f"participant_{participant}_{categoria.lower()}.jpg"
            )
            if os.path.exists(image_path):
                available_codes.append(code)
        return available_codes

    def _show_draft_votes(self, name: str):
        """Display saved draft votes."""
        draft_votes = SessionManager.get("draft_votes", [])
        if draft_votes:
            with st.expander("📝 Rascunhos Salvos"):
                for draft in draft_votes:
                    if draft["Nome"] == name:
                        self._render_draft_vote(draft)

    def _render_draft_vote(self, draft: dict):
        """Render a single draft vote with better visualization"""
        st.markdown("---")
        st.markdown(f"""
        ### 📝 Rascunho para Participante {draft["Participante"]}
        **Categoria:** {draft["Categoria"]}
        
        | Critério | Nota |
        |----------|------|
        | Originalidade | {draft["Originalidade"]}/10 |
        | Aparência | {draft["Aparencia"]}/10 |
        | Sabor | {draft["Sabor"]}/10 |
        
        *Salvo em: {draft["Data"].strftime("%d/%m/%Y %H:%M")}*
        """)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(
                "📥 Carregar Rascunho",
                key=f"load_draft_{draft['Participante']}_{draft['Categoria']}",
            ):
                SessionManager.set("selected_participant", draft["Participante"])
                SessionManager.set("selected_category", draft["Categoria"])
                st.rerun()
        with col2:
            if st.button(
                "🗑️ Excluir Rascunho",
                key=f"delete_draft_{draft['Participante']}_{draft['Categoria']}",
            ):
                draft_votes = SessionManager.get("draft_votes", [])
                draft_votes = [
                    d
                    for d in draft_votes
                    if not (
                        d["Participante"] == draft["Participante"]
                        and d["Categoria"] == draft["Categoria"]
                    )
                ]
                SessionManager.set("draft_votes", draft_votes)
                self.ui.show_success_message("Rascunho excluído com sucesso!")
                time.sleep(0.5)
                st.rerun()

    # Results Display Methods
    # ---------------------

    def _render_results_tab(self):
        """Manage results tab display and access control."""
        # Check if we have access to results (only via admin)
        if not SessionManager.get("results_access", False):
            self.ui.show_info_message(
                "🔒 Área restrita. Acesse como administrador para visualizar os resultados."
            )
            return

        # Show results if we have access
        self._render_results()

    def _render_results(self):
        """Render the results section"""
        try:
            # Get data from session state
            data = SessionManager.get("data")
            if data is None or data.empty:
                st.warning("Nenhum voto registrado ainda.")
                return

            # Create a copy of the data to avoid modifying the original
            data_copy = data.copy()

            # Ensure data types are correct
            data_copy["Participante"] = data_copy["Participante"].astype(str)
            data_copy["Categoria"] = data_copy["Categoria"].astype(str)
            data_copy["Originalidade"] = data_copy["Originalidade"].astype(float)
            data_copy["Aparencia"] = data_copy["Aparencia"].astype(float)
            data_copy["Sabor"] = data_copy["Sabor"].astype(float)

            # Calculate results using cache
            df_avg, winners = CacheManager.calculate_results(data_copy)

            # Display results
            st.subheader("Resultados por Categoria")

            # Create tabs for different views
            tab1, tab2 = st.tabs(["Resumo", "Detalhado"])

            with tab1:
                # Show overall winner first in a more prominent way
                if "Geral" in winners:
                    st.markdown("### 🏆 Vencedor Geral da Competição")
                    overall_winner = winners["Geral"]
                    participant_name = CacheManager.get_participant_name(
                        overall_winner["participant"], st.session_state.participant_names
                    )

                    # Get drink name from code
                    code = Anonymizer.get_or_create_code(overall_winner["participant"], "Geral")
                    drink_name = Anonymizer.get_drink_name(code)

                    # Create a more prominent display for the overall winner
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.markdown(f"### {participant_name}")
                        st.markdown(f"*{drink_name}*")
                        st.markdown(f"**{overall_winner['score']:.2f} pontos**")
                        st.markdown("</div>", unsafe_allow_html=True)

                    st.divider()

                # Then show category winners
                self._render_winners(winners)

            with tab2:
                self._render_detailed_results(df_avg)

        except Exception as e:
            st.error(f"Erro ao processar resultados: {str(e)}")
            st.exception(e)

    def _render_winners(self, winners):
        """Render winners section with caching"""
        st.subheader("🏆 Vencedores por Categoria")

        # Filter out the overall winner
        category_winners = {k: v for k, v in winners.items() if k != "Geral"}

        for cat, result in category_winners.items():
            participant_name = CacheManager.get_participant_name(
                result["participant"], st.session_state.participant_names
            )

            # Get drink name from code
            code = Anonymizer.get_or_create_code(result["participant"], cat)
            drink_name = Anonymizer.get_drink_name(code)

            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**{cat}**")
            with col2:
                st.markdown(f"**{participant_name}**")
                st.markdown(f"*{drink_name}*")
                st.markdown(f"*{result['score']:.2f} pontos*")
            st.divider()

    def _render_detailed_results(self, df_avg):
        """Render detailed results with caching"""
        with st.expander("Ver Resultados Detalhados", expanded=True):
            # Reset index for easier manipulation
            df_display = df_avg.reset_index()

            # Add participant names using cache
            df_display["Participante"] = df_display["Participante"].apply(
                lambda x: CacheManager.get_participant_name(x, st.session_state.participant_names)
            )

            # Set index back to multi-index
            df_display.set_index(["Participante", "Categoria"], inplace=True)

            # Sort by total score
            df_display.sort_values("Pontuação Total", ascending=False, inplace=True)

            # Style the DataFrame
            styled_df = df_display.style.background_gradient(
                subset=["Pontuação Total"], cmap="RdYlGn", vmin=0, vmax=30
            )

            st.dataframe(styled_df)

    # Vote Management Methods
    # ---------------------

    def _handle_vote_submission(
        self, name: str, code: str, originalidade: int, aparencia: int, sabor: int
    ):
        """Process vote submission."""
        if not self._validate_vote(name, code):
            return

        self._save_vote(name, code, originalidade, aparencia, sabor)

    def _validate_vote(self, name: str, code: str) -> bool:
        """Validate vote data."""
        if not code:
            self.ui.show_error_message("Código do drink inválido")
            return False
        return True

    def _save_vote(self, name: str, code: str, originalidade: int, aparencia: int, sabor: int):
        """Save the vote and handle success/failure."""
        participant, categoria = Anonymizer.get_participant_from_code(code)
        data = SessionManager.get("data")

        # Ensure data has the required columns
        if data.empty:
            data = pd.DataFrame(
                columns=[
                    "Nome",
                    "Participante",
                    "Categoria",
                    "Originalidade",
                    "Aparencia",
                    "Sabor",
                    "Data",
                ]
            )

        # Check for duplicate vote
        if self.vote_manager.check_duplicate_vote(data, name, categoria, str(participant)):
            self._handle_duplicate_vote(name, categoria, participant)
            return

        new_vote = self.vote_manager.create_vote(
            name, categoria, str(participant), originalidade, aparencia, sabor
        )
        SessionManager.set("data", pd.concat([data, new_vote], ignore_index=True))

        if self.data_manager.save_data(SessionManager.get("data")):
            self._handle_successful_vote(name)
        else:
            self.ui.show_error_message(UI_MESSAGES["ERROR_SAVE_VOTE"])

        CacheManager.invalidate_results_cache()

    def _handle_successful_vote(self, name: str):
        """Handle successful vote submission."""
        self.ui.show_success_message(UI_MESSAGES["SUCCESS_VOTE"].format(name))
        st.balloons()
        self._show_missing_votes(name)
        SessionManager.update_last_vote(name)

    def _show_missing_votes(self, name: str):
        """Show remaining votes for the user."""
        missing_votes = self.vote_manager.get_missing_votes(
            SessionManager.get("data"),
            name,
            SessionManager.get("categories"),
            SessionManager.get("num_participants"),
        )
        if missing_votes:
            self.ui.show_warning_message(
                "⚠️ Você ainda não votou nos seguintes participantes com foto disponível:"
            )
            for cat, part in missing_votes:
                st.write(f"- Categoria {cat}: Participante {part}")

    def _handle_duplicate_vote(self, name: str, categoria: str, participant: int):
        """Handle duplicate vote scenarios."""
        self.ui.show_warning_message(
            UI_MESSAGES["ERROR_DUPLICATE_VOTE"].format(participant, categoria)
        )

        # Store the duplicate vote info in session state
        SessionManager.set(
            "pending_duplicate_vote",
            {"name": name, "categoria": categoria, "participant": participant},
        )

        # Show options outside the form
        action = st.radio(
            "Escolha uma opção:",
            ["Manter meu voto anterior", "Remover meu voto anterior para votar novamente"],
            key=f"duplicate_action_{participant}_{categoria}",
        )

        if action == "Remover meu voto anterior para votar novamente":
            # Show confirmation button outside the form
            if st.button(
                "Confirmar remoção do voto", key=f"confirm_remove_{participant}_{categoria}"
            ):
                with st.spinner("Removendo voto anterior..."):
                    # Get current data
                    data = SessionManager.get("data")

                    # Remove duplicate vote
                    data = self.vote_manager.remove_duplicate_vote(
                        data, name, categoria, str(participant)
                    )

                    # Update session state with new data
                    SessionManager.set("data", data)

                    # Save to file
                    if self.data_manager.save_data(data):
                        # Clear cache to ensure fresh data
                        CacheManager.clear_cache()

                        # Reset voting state
                        SessionManager.reset_voting_state()

                        self.ui.show_success_message(UI_MESSAGES["VOTE_REMOVED"])
                        time.sleep(0.5)
                        st.rerun()
        else:
            self.ui.show_info_message(
                "Você pode continuar votando em outros participantes ou categorias."
            )
            st.stop()

    def _display_drink_image(self, code: str) -> None:
        """Display the drink image for the given code.

        Args:
            code (str): The drink code to display the image for.
        """
        participant, categoria = Anonymizer.get_participant_from_code(code)
        image_path = os.path.join(
            CONFIG["IMAGES_DIR"], f"participant_{participant}_{categoria.lower()}.jpg"
        )

        if os.path.exists(image_path):
            image = self.image_manager.load_and_resize_image(image_path, width=300)
            self.ui.display_image(image)
        else:
            self.ui.show_warning_message(UI_MESSAGES["NO_PHOTO_AVAILABLE"])

    def _render_voting_form(self, name: str, code: str):
        """Render the voting form for a selected drink."""
        participant, categoria = Anonymizer.get_participant_from_code(code)

        # Check for duplicate vote before showing the form
        if self.vote_manager.check_duplicate_vote(
            SessionManager.get("data", pd.DataFrame()), name, categoria, str(participant)
        ):
            self._handle_duplicate_vote(name, categoria, participant)
            return

        # Create the voting form
        with st.form(key=f"voting_form_{code}"):
            st.subheader(f"Votação para {Anonymizer.get_drink_name(code)}")

            # Display drink image
            self._display_drink_image(code)

            # Get scores
            col1, col2, col3 = st.columns(3)
            with col1:
                originalidade = st.slider(
                    "Originalidade", min_value=0, max_value=10, value=5, key=f"originalidade_{code}"
                )
            with col2:
                aparencia = st.slider(
                    "Aparência", min_value=0, max_value=10, value=5, key=f"aparencia_{code}"
                )
            with col3:
                sabor = st.slider("Sabor", min_value=0, max_value=10, value=5, key=f"sabor_{code}")

            # Show vote summary
            st.markdown("### Resumo do Voto")
            st.markdown(f"""
            - **Drink:** {Anonymizer.get_drink_name(code)}
            - **Originalidade:** {originalidade}/10
            - **Aparência:** {aparencia}/10
            - **Sabor:** {sabor}/10
            """)

            # Submit button
            submitted = st.form_submit_button("✅ Enviar Voto")

            if submitted:
                if originalidade == 0 and aparencia == 0 and sabor == 0:
                    st.error(
                        "❌ Não é possível enviar uma avaliação com todos os critérios zerados."
                    )
                else:
                    self._handle_vote_submission(name, code, originalidade, aparencia, sabor)

    def _render_statistics(self, data):
        """Render statistics section"""
        st.markdown("---")
        total_votes = self.data_manager.get_total_votes(data)
        st.markdown("### 📈 Estatísticas")
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
            display_df["Participante"] = display_df["Participante"].apply(
                lambda x: SessionManager.get("participant_names", {}).get(
                    int(x), f"Participante {x}"
                )
            )

            # Set the index back
            display_df = display_df.set_index(["Participante", "Categoria"])

            # Sort the index
            display_df = display_df.sort_index()

            # Style the DataFrame
            cm = sns.color_palette("blend:white,green", as_cmap=True)
            styled_df = display_df.style.background_gradient(cmap=cm, subset=["Pontuação Total"])
            st.dataframe(styled_df)
