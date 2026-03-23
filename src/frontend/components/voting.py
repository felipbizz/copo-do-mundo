import logging
import time

import pandas as pd
import seaborn as sns
import streamlit as st

from backend.data.data_manager import DataManager
from backend.data.vote_manager import VoteManager
from backend.image.image_manager import ImageManager
from backend.validation.validators import Validators
from config import UI_MESSAGES
from frontend.utils.anonymizer import Anonymizer
from frontend.utils.cache_manager import CacheManager
from frontend.utils.session_manager import SessionManager
from frontend.utils.ui_utils import UIUtils

logger = logging.getLogger(__name__)


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
            
            # Show progress indicator
            self._show_voting_progress(name)
            
            # Show voted drinks
            self._show_voted_drinks(name)
            
            self._show_draft_votes(name)

            # Get available codes (filtered to exclude already-voted drinks)
            available_codes = self._get_available_codes(name)
            if not available_codes:
                st.info("✅ Você já votou em todos os drinks disponíveis!")
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

    def _get_available_codes(self, name: str) -> list:
        """Get list of available drink codes that the juror hasn't voted on yet.
        
        Args:
            name (str): Name of the juror to filter drinks for.
            
        Returns:
            List[str]: List of drink codes available for voting.
        """
        # Get all codes from anonymizer
        all_codes = Anonymizer.get_all_codes()
        if not all_codes:
            return []
        
        # Get voting data
        data = SessionManager.get("data", pd.DataFrame())
        
        # Filter to only show drinks not yet voted on by this juror
        available_codes = self.vote_manager.get_available_drinks_for_juror(
            data, name, all_codes
        )
        
        return available_codes

    def _show_voting_progress(self, name: str):
        """Show progress indicator for voting completion."""
        data = SessionManager.get("data", pd.DataFrame())
        all_codes = Anonymizer.get_all_codes()
        
        if not all_codes:
            return
        
        total_drinks = len(all_codes)
        
        if data.empty or "Nome" not in data.columns:
            voted_count = 0
        else:
            juror_votes = data[data["Nome"] == name]
            # Count unique participant-category combinations
            voted_count = 0 if juror_votes.empty else len(juror_votes[["Categoria", "Participante"]].drop_duplicates())
        
        # Show progress bar
        progress = voted_count / total_drinks if total_drinks > 0 else 0
        st.progress(progress, text=f"Progresso: {voted_count} de {total_drinks} drinks votados")
        
    def _show_voted_drinks(self, name: str):
        """Display drinks the user has already voted on."""
        data = SessionManager.get("data", pd.DataFrame())
        
        if data.empty or "Nome" not in data.columns:
            return
        
        voted_drinks = self.vote_manager.get_voted_drinks_for_juror(data, name)
        
        if not voted_drinks:
            return
        
        with st.expander("✅ Drinks Já Votados", expanded=False):
            st.markdown("Você já votou nos seguintes drinks:")
            
            # Group by category for better organization
            drinks_by_category = {}
            for categoria, participant, _ in voted_drinks:
                if categoria not in drinks_by_category:
                    drinks_by_category[categoria] = []
                drinks_by_category[categoria].append(participant)
            
            for categoria in sorted(drinks_by_category.keys()):
                st.markdown(f"**{categoria}:**")
                for participant in sorted(drinks_by_category[categoria], key=lambda x: int(x) if x.isdigit() else 0):
                    # Get the code for this participant-category combination
                    try:
                        participant_int = int(participant) if participant.isdigit() else None
                        if participant_int is not None:
                            code = Anonymizer.get_code_from_participant(participant_int, categoria)
                            if code:
                                drink_name = Anonymizer.get_drink_name(code)
                                st.markdown(f"  ✓ {drink_name} (Participante {participant})")
                            else:
                                st.markdown(f"  ✓ Participante {participant}")
                        else:
                            st.markdown(f"  ✓ Participante {participant}")
                    except (ValueError, TypeError):
                        st.markdown(f"  ✓ Participante {participant}")
                st.markdown("")  # Add spacing between categories

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
        """Validate vote data with comprehensive checks.
        
        Args:
            name (str): Name of the juror.
            code (str): Drink code to validate.
            
        Returns:
            bool: True if vote is valid, False otherwise.
        """
        # Check if code is provided
        if not code or not code.strip():
            self.ui.show_error_message("❌ Erro: Código do drink não fornecido.")
            return False
        
        # Check if code exists in anonymizer
        participant_info = Anonymizer.get_participant_from_code(code)
        if participant_info is None:
            self.ui.show_error_message(
                f"❌ Erro: Código do drink '{code}' não encontrado no sistema. "
                "O drink pode ter sido removido ou o código está inválido."
            )
            return False
        
        participant, categoria = participant_info
        
        # Check if name is provided
        if not name or not name.strip():
            self.ui.show_error_message("❌ Erro: Nome do jurado não fornecido.")
            return False
        
        # Final duplicate check (defense in depth)
        data = SessionManager.get("data", pd.DataFrame())
        if not data.empty and self.vote_manager.check_duplicate_vote(
            data, name, categoria, str(participant)
        ):
            drink_name = Anonymizer.get_drink_name(code)
            self.ui.show_error_message(
                f"❌ Erro: Você já votou neste drink: **{drink_name}** "
                f"(Categoria: {categoria}, Participante: {participant}). "
                "Não é possível votar duas vezes no mesmo drink."
            )
            return False
        
        return True

    def _save_vote(self, name: str, code: str, originalidade: int, aparencia: int, sabor: int):
        """Save the vote and handle success/failure.

        Uses efficient append operations instead of full dataset save.
        """
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

        # Use append_vote for efficient single vote insertion
        try:
            if self.vote_manager.append_vote(
                name=name,
                categoria=categoria,
                participant=str(participant),
                originalidade=originalidade,
                aparencia=aparencia,
                sabor=sabor,
            ):
                # Update session state with new vote
                new_vote = self.vote_manager.create_vote(
                    name, categoria, str(participant), originalidade, aparencia, sabor
                )
                SessionManager.set("data", pd.concat([data, new_vote], ignore_index=True))

                self._handle_successful_vote(name)
                CacheManager.invalidate_results_cache()
            else:
                self.ui.show_error_message(UI_MESSAGES["ERROR_SAVE_VOTE"])
        except Exception as e:
            logger.error(f"Error saving vote: {str(e)}")
            self.ui.show_error_message(f"Erro ao salvar voto: {str(e)}")

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

    def _display_drink_image(self, code: str):
        """Display the drink image for the given code.

        Args:
            code (str): The drink code to display the image for.
        """
        participant, categoria = Anonymizer.get_participant_from_code(code)
        # Use relative path for storage abstraction
        image_path = f"participant_{participant}_{categoria.lower()}.jpg"

        if self.image_manager.image_exists(image_path):
            image = self.image_manager.load_and_resize_image(image_path, width=300)
            self.ui.display_image(image)
        else:
            st.info("Imagem ainda não disponível para este drink. Será que ele já ta pronto?")

    def _render_voting_form(self, name: str, code: str):
        """Render the voting form for a selected drink."""
        # Validate code exists
        participant_info = Anonymizer.get_participant_from_code(code)
        if participant_info is None:
            self.ui.show_error_message(
                f"❌ Erro: Código do drink '{code}' não encontrado. "
                "Por favor, selecione um drink válido da lista."
            )
            return
        
        participant, categoria = participant_info

        # Proactive duplicate check before showing the form
        data = SessionManager.get("data", pd.DataFrame())
        if not data.empty and self.vote_manager.check_duplicate_vote(
            data, name, categoria, str(participant)
        ):
            drink_name = Anonymizer.get_drink_name(code)
            self.ui.show_warning_message(
                f"⚠️ Você já votou neste drink: **{drink_name}** "
                f"(Categoria: {categoria}, Participante: {participant})"
            )
            st.info(
                "💡 Dica: Este drink não deveria aparecer na lista de drinks disponíveis. "
                "Se você precisa alterar seu voto, entre em contato com o administrador."
            )
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
            # st.markdown("### Resumo do Voto")
            # st.markdown(f"""
            # - **Drink:** {Anonymizer.get_drink_name(code)}
            # - **Originalidade:** {originalidade}/10
            # - **Aparência:** {aparencia}/10
            # - **Sabor:** {sabor}/10
            # """)

            # Submit button
            submitted = st.form_submit_button("✅ Enviar Voto")

            if submitted:
                if originalidade == 0 and aparencia == 0 and sabor == 0:
                    st.error(
                        "❌ Não é possível enviar uma avaliação com todos os critérios zerados."
                    )
                else:
                    self._handle_vote_submission(name, code, originalidade, aparencia, sabor)

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
