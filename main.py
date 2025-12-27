"""
Aplicación principal de Streamlit - Dr. Valdés, ahora con chat unificado y adjuntos.
"""

import os
from datetime import datetime
from typing import List, Dict, Optional

import streamlit as st

from config import AVAILABLE_MODELS
from prompts import get_system_prompt
from openai_handler import (
    chat_with_valdez,
    generate_academic_work,
    build_context_block,
    generate_work_pipeline,
)
from file_processor import prepare_context_from_files
from validators import validate_section_word_counts
from section_limits import get_section_limits


# Configuración de la página
st.set_page_config(
    page_title="Dr. Valdés - Profesor de Psicología",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Estilos compactos y alto contraste
st.markdown(
    """
<style>
    .stApp { background-color: #0f0f0f; color: #f5f5f5; }
    .stChatMessage, .stChatMessage p, .stMarkdown { color: #f5f5f5 !important; }
    .bubble-user { background:#1f2a44; border-left:3px solid #4a9eff; padding:12px; border-radius:4px; margin-bottom:10px; color:#f5f5f5; }
    .bubble-assistant { background:#252525; border-left:3px solid #c41e3a; padding:12px; border-radius:4px; margin-bottom:10px; font-style: italic; color:#f5f5f5; }
    .attachment-pill { display:block; padding:8px 10px; margin:6px 0; background:#1f1f1f; border:1px solid #444; border-radius:10px; font-size:0.9em; color:#f5f5f5; }
    .small { font-size:0.85em; color:#cfcfcf; }
</style>
""",
    unsafe_allow_html=True,
)


# Estado de sesión
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("attachments", [])


# Verificar API key
if not os.getenv("OPENAI_API_KEY"):
    st.error("⚠️ ERROR: No se encontró OPENAI_API_KEY en las variables de entorno. Configura tu .env file")
    st.stop()


# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    temperature = st.slider(
        "Temperatura (sarcasmo/precisión):",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Más alto = más variabilidad y sarcasmo. Más bajo = más consistente.",
    )

    st.markdown("#### 🤖 Modelo GPT")
    model_choice = st.selectbox(
        "Seleccionar modelo",
        ["Automático (según contexto)", "gpt-4-turbo", "gpt-4.5", "gpt-4.5-turbo", "gpt-4o"],
        help="Automático: elige el mejor modelo según la tarea. gpt-4-turbo: análisis profundo. gpt-4.5: equilibrio calidad/velocidad. gpt-4.5-turbo: máxima velocidad. gpt-4o: visión avanzada.",
    )
    
    # Convertir selección a None si es automático
    force_model = None if model_choice == "Automático (según contexto)" else model_choice
    
    # Guardar en session state
    st.session_state.force_model = force_model
    st.caption(f"✓ Usando: {model_choice}")

    language_choice = st.selectbox(
        "Idioma de salida",
        ["Automático", "Català", "Castellano", "English"],
        help="Si eliges Automático, responde en el idioma del usuario.",
    )

    grade_choice = st.selectbox(
        "Nota/rigor objetivo",
        [
            "0-3 Suspenso grave",
            "4 Suspenso",
            "5 Aprobado",
            "6-7 Bien",
            "8-9 Notable",
            "10 Matrícula de Honor",
        ],
    )

    complexity_choice = st.select_slider(
        "Complejidad/estilo",
        options=["5/10 – Muy natural", "6/10 – Natural con rigor", "7/10 – Equilibrado", "8/10 – Académico formal", "9/10 – Muy técnico", "10/10 – Máxima complejidad"],
        value="7/10 – Equilibrado",
    )

    word_count_raw = st.text_input(
        "Longitud deseada para /generar (palabras, opcional)",
        placeholder="Ej: 2500",
        help="Sin límite interno; se usa el valor que indiques o el que escribas en tu mensaje.",
    )

    st.divider()
    st.markdown("### 🗂️ Adjuntos en contexto")
    uploaded_files = st.file_uploader(
        "Sube archivos (PDF, DOCX, TXT/MD, CSV/XLSX, JPG/PNG)",
        type=["pdf", "docx", "txt", "md", "csv", "xlsx", "xls", "jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
    )
    col_up1, col_up2 = st.columns(2)
    if col_up1.button("Añadir al contexto", use_container_width=True):
        if uploaded_files:
            with st.spinner("Procesando adjuntos..."):
                processed = prepare_context_from_files(uploaded_files)
                st.session_state.attachments.extend(processed)
                st.success(f"{len(processed)} adjunto(s) listos")
                st.rerun()
    if col_up2.button("Limpiar adjuntos", use_container_width=True):
        st.session_state.attachments = []
        st.rerun()

    if st.session_state.attachments:
        st.markdown(f"{len(st.session_state.attachments)} archivo(s):")
        for idx, att in enumerate(st.session_state.attachments, start=1):
            st.markdown(
                f"<span class='attachment-pill'>[{idx}] {att.get('name','archivo')} • {att.get('kind','?')}<br><span class='small'>{att.get('summary','(sin resumen)')[:200]}</span></span>",
                unsafe_allow_html=True,
            )
            if st.button("Quitar", key=f"rm_sidebar_{idx}", use_container_width=True):
                st.session_state.attachments.pop(idx - 1)
                st.rerun()

    st.divider()
    st.markdown("### 🧹 Limpiar conversación")
    if st.button("Reiniciar chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.attachments = []
        st.rerun()

    st.divider()
    st.markdown("### ℹ️ Comandos rápidos")
    st.markdown(
        """
        - `/nota ...` pide calificación 0-10.
        - `/generar ...` redacta un trabajo.
        - `/limpiar` reinicia chat y adjuntos.
        """
    )

    st.divider()
    st.markdown("### ℹ️ Acerca de")
    st.markdown(
        """
        **Dr. Valdés** es un sistema de apoyo académico diseñado para:
        - Análisis crítico de trabajos (APA 7, metodología)
        - Análisis estadístico riguroso
        - Generación de trabajos con tono exigente
        """
    )


# Header
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.markdown("### 🎓 Dr. Valdés - Catedrático de Psicología")
    st.markdown("*Universitat Oberta de Catalunya - Departamento de Psicología*")
with col2:
    st.markdown(f"📅 {datetime.now().strftime('%d/%m/%Y')}")

st.divider()


# Conversación
st.markdown("### 💬 Chat unificado")

for message in st.session_state.chat_history:
    with st.chat_message("user" if message["role"] == "user" else "assistant"):
        st.markdown(message["content"])


def handle_command(user_text: str, context_block: str, temperature: float, grade_choice: str, complexity_choice: str, language_choice: str, word_count: Optional[int], attachments: List[Dict]) -> str:
    """Gestiona comandos especiales como /nota o /generar."""
    lower = user_text.lower()

    if lower.startswith("/limpiar"):
        st.session_state.chat_history = []
        st.session_state.attachments = []
        st.rerun()

    if lower.startswith("/nota"):
        question = user_text[len("/nota"):].strip() or "Califica el trabajo adjunto con nota 0-10 y justifica APA/metodología/coherencia."
        system_prompt = get_system_prompt("analysis")
        control = f"Idioma: {language_choice}. Nota objetivo: {grade_choice}." if language_choice != "Automático" else f"Nota objetivo: {grade_choice}." 
        content = f"{context_block}\n\n{control}\n\nInstrucción: {question}"
        return chat_with_valdez(
            messages=[{"role": "user", "content": build_content_with_images(content, attachments)}],
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=1800,
            context="analysis",
            complexity=0.7,
            force_model=st.session_state.get("force_model"),
        )

    if lower.startswith("/generar"):
        rest = user_text[len("/generar"):].strip()
        topic = rest or "Trabajo académico solicitado"
        requirements = f"Usa los adjuntos como insumo. Detalles del usuario: {rest}\n\n{context_block}"
        complexity_score = int(complexity_choice.split("/")[0])
        lang = language_choice if language_choice != "Automático" else "auto"
        # Map grade_choice to bands
        band_map = {
            "0-3 Suspenso grave": "0-4",
            "4 Suspenso": "0-4",
            "5 Aprobado": "5-6",
            "6-7 Bien": "6-7",
            "8-9 Notable": "8-9",
            "10 Matrícula de Honor": "9-10",
        }
        grade_band = band_map.get(grade_choice, "7-8")
        lang_hint = None if language_choice == "Automático" else ("ca" if language_choice == "Català" else ("es" if language_choice == "Castellano" else "en"))

        work = generate_academic_work(
            topic=topic,
            requirements=requirements,
            grade_band=grade_band,
            language_hint=lang_hint,
            word_count=word_count,
            quality_level=complexity_score,
            temperature=temperature,
            complexity=complexity_score / 10.0,
            force_model=st.session_state.get("force_model"),
        )
        
        # Mostrar trabajo
        st.markdown("## 📄 Trabajo Generado")
        st.markdown(work)
        
        # Validar límites por sección (silenciosa, solo alertas si hay problemas)
        section_limits = get_section_limits("research_paper")
        section_validation = validate_section_word_counts(
            work,
            section_limits,
            language="es"
        )
        
        # Solo mostrar alerta si hay problemas
        if section_validation['non_compliant_sections'] > 0:
            st.divider()
            st.warning(
                f"⚠️ {section_validation['non_compliant_sections']} sección(es) fuera de límites:\n\n"
                + "\n".join([f"• {issue}" for issue in section_validation['issues'][:3]]),
                icon="⚠️"
            )
        else:
            st.divider()
            st.success(
                f"✓ Todas las secciones cumplen los límites de palabras",
                icon="✓"
            )
        
        return ""

    return ""


def parse_word_count(raw: str) -> Optional[int]:
    """Convierte un input libre en entero de palabras si aplica."""
    if not raw:
        return None
    cleaned = ''.join(ch for ch in raw if ch.isdigit())
    try:
        return int(cleaned) if cleaned else None
    except ValueError:
        return None


def build_content_with_images(text_block: str, attachments: List[Dict]) -> List[Dict]:
    """Prepara contenido multimodal para OpenAI (texto + imágenes base64)."""
    content: List[Dict] = [{"type": "text", "text": text_block}]
    for att in attachments:
        if att.get("kind") == "image" and att.get("base64"):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{att['base64']}"
                }
            })
    return content


if user_input := st.chat_input("Escribe o usa comandos /nota, /generar"):
    user_message = {"role": "user", "content": user_input}
    context_block = build_context_block(st.session_state.attachments)
    control_block = f"Idioma seleccionado: {language_choice}. Nota objetivo: {grade_choice}. Complejidad: {complexity_choice}."
    desired_words = parse_word_count(word_count_raw)

    # Ejecutar comandos primero
    response = handle_command(user_input, context_block, temperature, grade_choice, complexity_choice, language_choice, desired_words, st.session_state.attachments)

    if not response:  # Chat normal
        system_prompt = get_system_prompt("chat")
        user_content = build_content_with_images(
            f"{context_block}\n\n{control_block}\n\nMensaje del estudiante: {user_input}",
            st.session_state.attachments,
        )
        messages_for_api = st.session_state.chat_history + [
            {
                "role": "user",
                "content": user_content,
            }
        ]

        response = chat_with_valdez(
            messages=messages_for_api,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=2000,
            context="chat",
            complexity=0.5,
            force_model=st.session_state.get("force_model"),
        )

    st.session_state.chat_history.append(user_message)
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    st.rerun()


# Footer
st.divider()
st.markdown(
    """
---
**Dr. Valdés** - Sistema de Apoyo Académico | UOC Psicología  
*"La mediocridad académica no es disculpable"* - Dr. Valdés
"""
)
