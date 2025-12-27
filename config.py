"""
Configuración de la aplicación
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Modelos
DEFAULT_MODEL = "gpt-4o"

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
