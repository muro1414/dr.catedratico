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
        "use_case": "análisis complejo, precisión máxima",
        "cost": "medio",
        "speed": "rápido"
    },
    "gpt-4o": {
        "name": "GPT-4o (omni)",
        "use_case": "equilibrio calidad/velocidad, visión",
        "cost": "medio",
        "speed": "muy rápido"
    },
    "gpt-3.5-turbo": {
        "name": "GPT-3.5 Turbo",
        "use_case": "tareas simples, máxima velocidad",
        "cost": "bajo",
        "speed": "ultra rápido"
    }
}

DEFAULT_MODEL = "gpt-4o"  # Modelo por defecto

# Mapeo de contexto a modelo recomendado
MODEL_SELECTION_RULES = {
    "analysis": "gpt-4-turbo",      # Análisis de trabajos/PDFs: precisión
    "generation": "gpt-4o",         # Generación de contenido: equilibrio
    "vision": "gpt-4o",             # Análisis de imágenes
    "chat": "gpt-4o",               # Chat general: velocidad
    "simple": "gpt-3.5-turbo",      # Preguntas simples: máxima velocidad
}

# Configuración de Streamlit
STREAMLIT_CONFIG = {
    "theme.primaryColor": "#c41e3a",  # Rojo del Dr. Sanal
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

# Mensajes del Dr. Sanal (tono exigente pero respetuoso)
SANAL_QUIRKS = [
    "¿No te parece simplista?",
    "Esto necesita más rigor metodológico.",
    "Sin evidencia, esa afirmación no se sostiene.",
    "La coherencia entre hipótesis y análisis es obligatoria.",
    "Evita conclusiones bonitas sin datos.",
    "Justifica decisiones metodológicas explícitamente.",
]
