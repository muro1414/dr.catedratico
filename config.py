"""
Configuración de la aplicación
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Modelos disponibles
AVAILABLE_MODELS = {
    "gpt-4-turbo": {
        "name": "GPT-4 Turbo",
        "use_case": "análisis complejo, visión",
        "cost": "bajo",
        "speed": "rápido"
    },
    "gpt-4.5": {
        "name": "GPT-4.5",
        "use_case": "equilibrio calidad/velocidad",
        "cost": "medio",
        "speed": "muy rápido"
    },
    "gpt-4.5-turbo": {
        "name": "GPT-4.5 Turbo",
        "use_case": "máxima velocidad, tareas simples",
        "cost": "bajo",
        "speed": "ultra rápido"
    },
    "gpt-4o": {
        "name": "GPT-4o (omni)",
        "use_case": "visión avanzada, multimodal",
        "cost": "medio",
        "speed": "rápido"
    }
}

DEFAULT_MODEL = "gpt-4.5"  # Modelo por defecto

# Mapeo de contexto a modelo recomendado
MODEL_SELECTION_RULES = {
    "analysis": "gpt-4-turbo",      # Análisis de trabajos/PDFs: precisión
    "generation": "gpt-4.5",        # Generación de contenido: equilibrio
    "vision": "gpt-4o",             # Análisis de imágenes
    "chat": "gpt-4.5",              # Chat general: velocidad
    "simple": "gpt-4.5-turbo",      # Preguntas simples: máxima velocidad
}

# Configuración de Streamlit
STREAMLIT_CONFIG = {
    "theme.primaryColor": "#c41e3a",  # Rojo del Dr. Valdés
    "theme.backgroundColor": "#1e1e1e",  # Oscuro
    "theme.secondaryBackgroundColor": "#2d2d2d",
    "theme.textColor": "#e0e0e0",
}

# Límites de tokens
MAX_TOKENS_CHAT = 2000
MAX_TOKENS_ANALYSIS = 2500
MAX_TOKENS_GENERATION = 4000

# Temperatura por defecto
DEFAULT_TEMPERATURE = 0.7

# Mensajes del Dr. Valdés
VALDEZ_QUIRKS = [
    "en parbulos enseñan a limpiarse el culo con tus trabajos"
    "a e i o u borriquito como tu"
    "sabes leer entre líneas?",
    "¿No te parece un poco simplista eso?",
    "¿De verdad crees eso?",
    "¿En serio?",
    "Interesante... pero insuficiente.",
    "Vuelve a pensarlo.",
    "Eso que dices carece de rigor.",
    "Necesitas más evidencia.",
]
