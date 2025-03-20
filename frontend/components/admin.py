import os
import streamlit as st
from PIL import Image
import time

from backend.image.image_manager import ImageManager
from backend.validation.validators import Validators
from config import CONFIG, UI_MESSAGES
from frontend.utils.ui_utils import UIUtils

class AdminComponent:
    def __init__(self):
        self.image_manager = ImageManager()
        self.validators = Validators()
        self.ui = UIUtils()

    def render(self):
        """Render the admin section"""
        st.sidebar.title("Área do Administrador")
        admin_password = st.sidebar.text_input("Senha do Administrador", type="password")

        if self.validators.validate_admin_password(admin_password):
            with st.sidebar:
                self.ui.show_success_message(UI_MESSAGES["ADMIN_WELCOME"])
                self._render_competition_settings()
                self._render_photo_management()
                self._render_data_export()
            st.session_state.is_admin = True
        elif admin_password:
            st.sidebar.error(UI_MESSAGES["ERROR_PASSWORD"])
            st.session_state.is_admin = False
        else:
            st.session_state.is_admin = False

    def _render_competition_settings(self):
        """Render competition settings section"""
        st.subheader("Configurações da Competição")
        new_num_drinks = st.number_input(
            "Número de Drinks", min_value=1, value=st.session_state.num_drinks
        )

        if new_num_drinks != st.session_state.num_drinks:
            with st.spinner("Atualizando configurações..."):
                st.session_state.num_drinks = new_num_drinks
                time.sleep(0.5)  # Add a small delay for better UX
                st.rerun()

    def _render_photo_management(self):
        """Render photo management section"""
        st.subheader("📸 Gerenciamento de Fotos")
        
        # Create columns for participant and category selection
        col1, col2 = self.ui.create_columns([1, 1])
        
        with col1:
            # Participant selection
            participant = st.selectbox(
                "Participante",
                options=list(range(1, st.session_state.num_participants + 1)),
                key="admin_participant_select"
            )
        
        with col2:
            # Category selection
            category = st.selectbox(
                "Categoria",
                options=st.session_state.categories,
                key="admin_category_select"
            )
        
        # Photo section in full width below
        st.markdown("---")
        
        # Current photo section
        st.markdown("### 📸 Foto Atual")
        image_path = os.path.join(CONFIG["IMAGES_DIR"], f"participant_{participant}_{category.lower()}.jpg")
        if os.path.exists(image_path):
            image = self.image_manager.load_and_resize_image(image_path, width=300)
            self.ui.display_image(image)
            
            # Add remove button
            if st.button("🗑️ Remover Foto", key=f"remove_{participant}_{category}"):
                with st.spinner("Removendo foto..."):
                    try:
                        os.remove(image_path)
                        self.ui.show_success_message("Foto removida com sucesso!")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        self.ui.show_error_message(f"Erro ao remover foto: {str(e)}")
        else:
            self.ui.show_info_message("Nenhuma foto disponível para este participante nesta categoria")
        
        # New photo section
        st.markdown("### 📤 Nova Foto")
        # Choose between upload and camera
        photo_method = st.radio(
            "Escolha o método de captura",
            ["Upload de Arquivo", "Câmera"],
            horizontal=True,
            key=f"photo_method_{participant}_{category}"
        )
        
        if photo_method == "Upload de Arquivo":
            # Photo upload section
            uploaded_file = st.file_uploader(
                "Selecione uma foto",
                type=CONFIG["ALLOWED_IMAGE_TYPES"],
                key=f"upload_{participant}_{category}"
            )
            
            if uploaded_file:
                # Show preview
                image = Image.open(uploaded_file)
                self.ui.display_image(image)
                
                # Add upload button
                if st.button("💾 Salvar Foto", key=f"save_upload_{participant}_{category}"):
                    with st.spinner("Processando foto..."):
                        try:
                            # Optimize and save image
                            optimized_image = self.image_manager.optimize_image(image)
                            optimized_image.save(
                                image_path,
                                quality=CONFIG["IMAGE_QUALITY"],
                                optimize=True
                            )
                            self.ui.show_success_message("Foto salva com sucesso!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            self.ui.show_error_message(f"Erro ao salvar foto: {str(e)}")
        
        else:
            # Camera section
            camera_image = st.camera_input(
                "Tire uma foto",
                key=f"camera_{participant}_{category}"
            )
            
            if camera_image:
                # Show preview
                self.ui.display_image(camera_image)
                
                # Add save button with unique key
                if st.button("💾 Salvar Foto da Câmera", key=f"save_camera_{participant}_{category}"):
                    with st.spinner("Processando foto..."):
                        try:
                            # Convert camera image to PIL Image if needed
                            if not isinstance(camera_image, Image.Image):
                                camera_image = Image.open(camera_image)
                            
                            # Optimize and save image
                            optimized_image = self.image_manager.optimize_image(camera_image)
                            optimized_image.save(
                                image_path,
                                quality=CONFIG["IMAGE_QUALITY"],
                                optimize=True
                            )
                            self.ui.show_success_message("Foto salva com sucesso!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            self.ui.show_error_message(f"Erro ao salvar foto: {str(e)}")

    def _render_data_export(self):
        """Render data export section"""
        st.subheader("Exportar Dados")
        if st.button("📥 Baixar Dados CSV"):
            with st.spinner("Preparando arquivo..."):
                try:
                    csv = st.session_state.data.to_csv(index=False)
                    st.download_button(
                        "📥 Clique para baixar",
                        csv,
                        "votos.csv",
                        "text/csv",
                        key="download-csv",
                    )
                except Exception as e:
                    self.ui.show_error_message(UI_MESSAGES["ERROR_EXPORT_DATA"].format(str(e))) 