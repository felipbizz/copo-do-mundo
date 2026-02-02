import os
import time

import streamlit as st
from PIL import Image

from backend.data.vote_manager import VoteManager
from backend.image.image_manager import ImageManager
from backend.validation.validators import Validators
from config import CONFIG, UI_MESSAGES
from frontend.utils.anonymizer import Anonymizer
from frontend.utils.cache_manager import CacheManager
from frontend.utils.session_manager import SessionManager
from frontend.utils.ui_utils import UIUtils


class AdminComponent:
    def __init__(self):
        CacheManager.initialize_cache()
        Anonymizer.initialize_anonymization()
        self.image_manager = ImageManager()
        self.validators = Validators()
        self.vote_manager = VoteManager()
        self.ui = UIUtils()

    def render(self):
        """Render the admin section"""
        # Render admin login in sidebar
        self._render_admin_login()

        # If admin is authenticated, render admin content
        if SessionManager.get("is_admin", False):
            st.title("Área Administrativa! 👨‍💼")

            # Configuration expander at the beginning
            self._render_configuracoes_gerais()

            # Codes and drink names
            self._render_codes_and_drink_names()

            # Photo management
            self._render_photo_management()

            # Results access
            self._render_results_access()

            # Data management
            self._render_data_management()

    def _render_admin_login(self):
        """Render admin login section in sidebar."""
        st.sidebar.title("Área do Administrador")
        admin_password = st.sidebar.text_input(
            "Senha do Administrador", type="password", key="admin_password_input"
        )

        if self.validators.validate_admin_password(admin_password):
            st.sidebar.success(UI_MESSAGES["ADMIN_WELCOME"])
            SessionManager.set("is_admin", True)
        elif admin_password:
            st.sidebar.error(UI_MESSAGES["ERROR_PASSWORD"])
            SessionManager.reset_access_state()
        else:
            SessionManager.reset_access_state()

    def _render_configuracoes_gerais(self):
        with st.expander("⚙️ Configurações Gerais", expanded=True):
            # Definindo número de participantes
            self._define_num_participantes()
            # Category management
            self._define_categorias()

    def _define_num_participantes(self):
        new_num_participants = st.number_input(
            "Número de Participantes",
            min_value=1,
            value=SessionManager.get("num_participants"),
            key="admin_num_participants",
        )

        if new_num_participants != SessionManager.get("num_participants"):
            with st.spinner("Atualizando configurações..."):
                SessionManager.set("num_participants", new_num_participants)
                time.sleep(0.5)
                st.rerun()

    def _define_categorias(self):
        st.markdown("---")
        st.subheader("🏷️ Gerenciamento de Categorias")

        # Get current categories
        current_categories = SessionManager.get("categories", CONFIG["CATEGORIES"])

        # Display current categories
        st.write("**Categorias Atuais:**")
        for i, category in enumerate(current_categories):
            col1, col2 = st.columns([4, 1])
            with col1:
                new_category = st.text_input(
                    f"Categoria {i + 1}", value=category, key=f"category_{i}"
                )
            with col2:
                if st.button("Remover", key=f"remove_{i}"):
                    with st.spinner("Atualizando categorias..."):
                        current_categories.pop(i)
                        SessionManager.set("categories", current_categories)
                        st.rerun()

            # Update category if changed
            if new_category != category:
                with st.spinner("Atualizando categorias..."):
                    current_categories[i] = new_category
                    SessionManager.set("categories", current_categories)
                    st.rerun()

        # Add new category
        if st.button("Adicionar Nova Categoria"):
            with st.spinner("Atualizando categorias..."):
                current_categories.append("Nova Categoria")
                SessionManager.set("categories", current_categories)
                st.rerun()

    def _render_data_export(self):
        """Render data export section"""
        st.subheader("📥 Exportar Dados")
        if st.button("Baixar Dados CSV"):
            with st.spinner("Preparando arquivo..."):
                try:
                    csv = SessionManager.get("data").to_csv(index=False)
                    st.download_button(
                        "📥 Clique para baixar",
                        csv,
                        "votos.csv",
                        "text/csv",
                        key="download-csv",
                    )
                except Exception as e:
                    self.ui.show_error_message(UI_MESSAGES["ERROR_EXPORT_DATA"].format(str(e)))

    def _render_clear_votes(self):
        """Render clear votes section"""
        st.subheader("🗑️ Limpar Votos")
        if st.button("Limpar Todos os Votos", key="clear_votes"):
            with st.spinner("Limpando votos..."):
                try:
                    # Clear votes using VoteManager
                    empty_df = self.vote_manager.clear_votes()

                    # Update session state
                    SessionManager.set("data", empty_df)

                    # Invalidate cache
                    CacheManager.invalidate_results_cache()

                    st.success("Votos limpos com sucesso!")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao limpar votos: {str(e)}")

    def _render_codes_and_drink_names(self):
        # Show current drink codes and names
        with st.expander("🔑 Códigos e Nomes dos Drinks"):
            st.markdown("### Drinks Cadastrados")
            codes = Anonymizer.get_all_codes()
            if codes:
                for code, (participant, categoria) in codes.items():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
                    with col1:
                        st.markdown(f"**Código:** {code}")
                    with col2:
                        st.markdown(f"**Participante:** {participant}")
                    with col3:
                        st.markdown(f"**Categoria:** {categoria}")
                    with col4:
                        # Add custom name input
                        current_name = Anonymizer.get_drink_name(code)
                        new_name = st.text_input(
                            "Nome do Drink",
                            value=current_name,
                            key=f"drink_name_{code}",
                            help="Digite um nome personalizado para o drink",
                        )
                        if new_name != current_name:
                            Anonymizer.set_drink_name(code, new_name)
                            st.success("Nome atualizado!")
            else:
                st.info("Nenhum drink cadastrado ainda.")

            if st.button("🔄 Regenerar Códigos"):
                Anonymizer.clear_anonymization()
                # Generate new codes for all participants
                for participant in range(1, SessionManager.get("num_participants") + 1):
                    for categoria in SessionManager.get("categories"):
                        Anonymizer.get_or_create_code(participant, categoria)
                st.success("Códigos regenerados com sucesso!")
                st.rerun()

    def _render_photo_management(self):
        """Render photo management section"""
        with st.expander("📸 Gerenciamento de Fotos"):
            # Photo upload section
            st.markdown("### Upload de Fotos")

            # Create columns for participant and category selection
            col1, col2 = self.ui.create_columns([1, 1])

            with col1:
                # Participant selection
                participant = st.selectbox(
                    "Participante",
                    options=list(range(1, SessionManager.get("num_participants") + 1)),
                    key="admin_participant_select",
                )

            with col2:
                # Category selection
                category = st.selectbox(
                    "Categoria",
                    options=SessionManager.get("categories"),
                    key="admin_category_select",
                )

            # Photo section in full width below
            st.markdown("---")

            # Current photo section
            st.markdown("### 📸 Foto Atual")
            # Use relative path for storage abstraction
            image_path = f"participant_{participant}_{category.lower()}.jpg"
            if self.image_manager.image_exists(image_path):
                image = self.image_manager.load_and_resize_image(image_path, width=300)
                self.ui.display_image(image)

                # Add remove button
                if st.button("🗑️ Remover Foto", key=f"remove_{participant}_{category}"):
                    with st.spinner("Removendo foto..."):
                        try:
                            if self.image_manager.delete_image(image_path):
                                self.ui.show_success_message("Foto removida com sucesso!")
                                time.sleep(0.5)
                                CacheManager.invalidate_results_cache()
                                st.rerun()
                            else:
                                self.ui.show_error_message("Erro ao remover foto")
                        except Exception as e:
                            self.ui.show_error_message(f"Erro ao remover foto: {str(e)}")
            else:
                self.ui.show_info_message(
                    "Nenhuma foto disponível para este participante nesta categoria"
                )

            # New photo section
            st.markdown("### 📤 Nova Foto")
            # Choose between upload and camera
            photo_method = st.radio(
                "Escolha o método de captura",
                ["Upload de Arquivo", "Câmera"],
                horizontal=True,
                key=f"photo_method_{participant}_{category}",
            )

            if photo_method == "Upload de Arquivo":
                # Photo upload section
                uploaded_file = st.file_uploader(
                    "Selecione uma foto",
                    type=CONFIG["ALLOWED_IMAGE_TYPES"],
                    key=f"upload_{participant}_{category}",
                )

                if uploaded_file:
                    # Show preview
                    image = Image.open(uploaded_file)
                    self.ui.display_image(image)

                    # Add upload button
                    if st.button("💾 Salvar Foto", key=f"save_upload_{participant}_{category}"):
                        with st.spinner("Processando foto..."):
                            try:
                                # Use ImageManager to save (handles optimization and storage)
                                image_path = f"participant_{participant}_{category.lower()}.jpg"
                                if self.image_manager.save_image(image, image_path):
                                    self.ui.show_success_message("Foto salva com sucesso!")
                                    time.sleep(0.5)
                                    CacheManager.invalidate_results_cache()
                                    st.rerun()
                                else:
                                    self.ui.show_error_message("Erro ao salvar foto")
                            except Exception as e:
                                self.ui.show_error_message(f"Erro ao salvar foto: {str(e)}")

            else:
                # Camera section
                camera_image = st.camera_input(
                    "Tire uma foto", key=f"camera_{participant}_{category}"
                )

                if camera_image:
                    # Show preview
                    self.ui.display_image(camera_image)

                    # Add save button with unique key
                    if st.button(
                        "💾 Salvar Foto da Câmera", key=f"save_camera_{participant}_{category}"
                    ):
                        with st.spinner("Processando foto..."):
                            try:
                                # Convert camera image to PIL Image if needed
                                if not isinstance(camera_image, Image.Image):
                                    camera_image = Image.open(camera_image)

                                # Use ImageManager to save (handles optimization and storage)
                                image_path = f"participant_{participant}_{category.lower()}.jpg"
                                if self.image_manager.save_image(camera_image, image_path):
                                    self.ui.show_success_message("Foto salva com sucesso!")
                                    time.sleep(0.5)
                                    CacheManager.invalidate_results_cache()
                                    st.rerun()
                                else:
                                    self.ui.show_error_message("Erro ao salvar foto")
                            except Exception as e:
                                self.ui.show_error_message(f"Erro ao salvar foto: {str(e)}")

    def _render_results_access(self):
        """Render results access control with cache invalidation"""
        with st.expander("🔒 Controle de Acesso aos Resultados"):
            # Get current state
            results_access = SessionManager.get("results_access", False)

            # Show current status
            status = "🔓 Liberado" if results_access else "🔒 Bloqueado"
            st.markdown(f"**Status atual:** {status}")

            # Only show toggle button if user is admin
            if SessionManager.get("is_admin", False) and st.button(
                "🔓 Liberar Resultados" if not results_access else "🔒 Bloquear Resultados",
                key="toggle_results",
            ):
                SessionManager.set("results_access", not results_access)
                CacheManager.invalidate_results_cache()
                st.rerun()

    def _render_data_management(self):
        """Render data management section"""
        with st.expander("💾 Gerenciamento de Dados", expanded=False):
            # Clear votes and export data side by side
            col1, col2 = st.columns(2)

            with col1:
                self._render_clear_votes()

            with col2:
                self._render_data_export()
