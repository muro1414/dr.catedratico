"""
Aplicación principal de Streamlit - Dr. Sanal, sistema académico sin límites artificiales.
"""

import os
from datetime import datetime
from typing import List, Dict, Optional

import streamlit as st

from prompts import get_system_prompt
from openai_handler import (
    chat_with_sanal,
    generate_academic_work_phased,
    build_context_block,
)
from file_processor import prepare_context_from_files


# Configuración de la página
st.set_page_config(
    page_title="Dr. Sanal - Profesor de Psicología",
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
    st.markdown("### ⚙️ Configuración simple")
    language_choice = st.selectbox(
        "Idioma de salida",
        ["Automático", "Català", "Castellano", "English"],
        help="Si eliges Automático, responde en el idioma del usuario.",
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
        **Dr. Sanal** es un sistema de apoyo académico diseñado para:
        - Análisis crítico de trabajos (APA 7, metodología)
        - Análisis estadístico riguroso
        - Generación de trabajos optimizados para máxima calidad
        - SIN límites artificiales de palabras ni notas objetivo
        """
    )


# Header
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.markdown("### 🎓 Dr. Sanal - Catedrático de Psicología")
    st.markdown("*Universitat Oberta de Catalunya - Departamento de Psicología*")
with col2:
    st.markdown(f"📅 {datetime.now().strftime('%d/%m/%Y')}")

st.divider()


# Conversación
st.markdown("### 💬 Chat unificado")

for message in st.session_state.chat_history:
    with st.chat_message("user" if message["role"] == "user" else "assistant"):
        st.markdown(message["content"])


def handle_command(user_text: str, context_block: str, language_choice: str, attachments: List[Dict]) -> str:
    """Gestiona comandos especiales como /nota o /generar."""
    lower = user_text.lower()

    if lower.startswith("/limpiar"):
        st.session_state.chat_history = []
        st.session_state.attachments = []
        st.rerun()

    if lower.startswith("/nota"):
        question = user_text[len("/nota"):].strip() or "Califica el trabajo adjunto con nota 0-10 REAL basada en criterios UOC y justifica APA/metodología/coherencia."
        system_prompt = get_system_prompt("analysis")
        control = f"Idioma: {language_choice}." if language_choice != "Automático" else ""
        content = f"{context_block}\n\n{control}\n\nInstrucción: {question}"
        # Guardar texto para contador de tokens
        st.session_state["last_prompt_text"] = f"SYSTEM:\n{get_system_prompt('analysis')}\n\nUSER:\n{content}"
        return chat_with_sanal(
            messages=[{"role": "user", "content": build_content_with_images(content, attachments)}],
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=3000,
            context="analysis",
            complexity=0.7,
            force_model=None,
        )

    if lower.startswith("/generar"):
        rest = user_text[len("/generar"):].strip()
        topic = rest or "Trabajo académico solicitado"
        requirements = f"Usa los adjuntos como insumo. Detalles del usuario: {rest}"
        lang_hint = None if language_choice == "Automático" else ("ca" if language_choice == "Català" else ("es" if language_choice == "Castellano" else "en"))

        work = generate_academic_work_phased(
            topic=topic,
            requirements=requirements,
            attachments=st.session_state.attachments,
            language_hint=lang_hint,
        )

        st.markdown("## 📄 Trabajo Generado")
        st.markdown(work)
        st.divider()
        st.success("✓ Trabajo generado con arquitectura por fases (estable)", icon="✓")
        return ""

    return ""


def looks_truncated(text: str) -> bool:
    """Heurística simple para detectar respuestas cortadas."""
    if not text or len(text) < 200:
        return False
    tail = text[-200:]
    # Incompleto si no termina con puntuación fuerte
    ends_ok = any(text.strip().endswith(p) for p in [".", "!", "?", ")", "]", "\""])
    has_heading = any(h in tail.lower() for h in ["referencias", "bibliografía", "discusión", "resultados"])
    mid_word_cut = tail.endswith(" ") and not ends_ok
    return (not ends_ok) or mid_word_cut or has_heading


def continue_generation(previous_text: str, language_hint: Optional[str], attachments: List[Dict]) -> str:
    """Solicita continuación del texto sin repetir contenido previo."""
    lang_line = f"Idioma: {language_hint}" if language_hint else "Idioma: automático"
    instruction = f"""
Continúa el trabajo EXACTAMENTE desde donde se quedó.
No repitas contenido previo. Mantén estructura académica.
Si estaba en medio de una sección, complétala y continúa.
{lang_line}
"""
    return chat_with_sanal(
        messages=[{"role": "user", "content": build_content_with_images(previous_text + "\n\n" + instruction, attachments)}],
        system_prompt=get_system_prompt("generation"),
        temperature=0.7,
        max_tokens=8000,
        context="generation",
        complexity=0.8,
        force_model=None,
    )


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
    control_block = f"Idioma seleccionado: {language_choice}."

    # Ejecutar comandos primero
    response = handle_command(user_input, context_block, language_choice, st.session_state.attachments)

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

        # Guardar prompt para contador
        st.session_state["last_prompt_text"] = f"SYSTEM:\n{get_system_prompt('chat')}\n\nUSER:\n{context_block}\n\n{control_block}\n\nMensaje: {user_input}"

        response = chat_with_sanal(
            messages=messages_for_api,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=3000,
            context="chat",
            complexity=0.5,
            force_model=None,
        )

    st.session_state.chat_history.append(user_message)
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    st.rerun()


# Footer
st.divider()
st.markdown(
    """
---
**Dr. Sanal** - Sistema de Apoyo Académico | UOC Psicología  
*"La excelencia académica no es negociable"* - Dr. Sanal
"""
)
