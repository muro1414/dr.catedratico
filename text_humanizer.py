"""
Humanización LIGERA de texto generado por IA.
Sin introducir errores artificiales que rompan la coherencia académica.
La humanización debe lograrse POR PROMPT, no estropeando el texto después.
"""

import re
import random


def sanitize_meta_discourse(text: str) -> str:
    """
    Elimina frases de meta-discurso y encabezados redundantes del texto generado.
    
    Args:
        text: Texto generado por el modelo
        
    Returns:
        Texto limpio sin meta-discurso
    """
    # Patrones de frases de asistente a eliminar (al inicio)
    meta_patterns_start = [
        r"^(aquí tens|aquí tienes|per generar|para generar|vaig a crear|voy a crear).*?[\n:]",
        r"^(here is|here's).*?[\n:]",
        r"^(espero que|espero que t'ajudi|espero que te ayude).*?[\n]",
    ]
    
    # Patrones de cierre a eliminar (al final)
    meta_patterns_end = [
        r"(si necessites|si necesitas|si requieres|estaré disponible|estic disponible).*$",
    ]
    
    # Encabezados redundantes
    redundant_headers = [
        r"^Nom i cognoms:.*?\n",
        r"^Nombre y apellidos:.*?\n",
        r"^Assignatura:.*?\n",
        r"^Asignatura:.*?\n",
    ]
    
    cleaned = text.strip()
    
    # Eliminar patrones de inicio
    for pattern in meta_patterns_start:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    # Eliminar patrones de cierre
    for pattern in meta_patterns_end:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    # Eliminar encabezados redundantes (solo las primeras 5 líneas)
    lines = cleaned.split("\n")
    if len(lines) > 5:
        first_lines = "\n".join(lines[:5])
        rest_lines = "\n".join(lines[5:])
        for pattern in redundant_headers:
            first_lines = re.sub(pattern, "", first_lines, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = first_lines + "\n" + rest_lines
    
    return cleaned.strip()


def humanize_text_light(text: str) -> str:
    """
    Humanización LIGERA sin estropear coherencia académica.
    Solo elimina patrones obvios de IA y asegura formato correcto.
    
    Args:
        text: Texto a humanizar
    
    Returns:
        Texto con humanización ligera
    """
    # Eliminar puntos suspensivos innecesarios
    text = re.sub(r'(\w)\s*\.\.\.\s*(\w)', r'\1 \2', text)
    
    # Eliminar múltiples asteriscos de énfasis
    text = re.sub(r'\*{2,}(.+?)\*{2,}', r'\1', text)
    
    # Asegurar espaciado correcto
    text = re.sub(r' +', ' ', text)  # Espacios múltiples -> uno
    text = re.sub(r'\n{3,}', '\n\n', text)  # Múltiples saltos -> dos
    
    # Asegurar puntuación correcta
    text = re.sub(r' +([.,;:])', r'\1', text)  # Espacio antes de puntuación
    
    # Comillas correctas
    text = re.sub(r'"([^"]*)"', r'"\1"', text)
    
    return text.strip()


def ensure_proper_formatting(text: str) -> str:
    """
    Asegura formato APA 7 correcto sin símbolos de IA.
    Alias de humanize_text_light para compatibilidad.
    """
    return humanize_text_light(text)


# Funciones legacy mantenidas por compatibilidad pero sin efecto
def humanize_text(text: str, quality_level: int = 7, target_words: int = None) -> str:
    """Función legacy. Ahora solo aplica humanización ligera."""
    return humanize_text_light(text)


def adjust_sections_to_word_counts(text: str, section_limits: dict, language: str = "es") -> str:
    """Función legacy. Ya NO ajusta límites de palabras. Retorna el texto sin cambios."""
    return text
