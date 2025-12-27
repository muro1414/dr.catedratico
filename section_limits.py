"""
Especificaciones de límites de palabras por sección de trabajos académicos
"""

from typing import Dict, Optional

# Estructuras de límites para diferentes tipos de trabajos
SECTION_LIMITS = {
    "research_paper": {
        "título": {"min": 5, "max": 15},
        "resumen": {"min": 100, "max": 250},
        "introducción": {"min": 300, "max": 600},
        "método": {"min": 400, "max": 800},
        "resultados": {"min": 400, "max": 800},
        "discusión": {"min": 300, "max": 600},
        "referencias": {"min": 50, "max": 500},
    },
    "essay": {
        "título": {"min": 5, "max": 15},
        "introducción": {"min": 150, "max": 300},
        "desarrollo": {"min": 800, "max": 1500},
        "conclusión": {"min": 150, "max": 300},
        "referencias": {"min": 30, "max": 200},
    },
    "case_study": {
        "título": {"min": 5, "max": 15},
        "introducción": {"min": 200, "max": 400},
        "contexto": {"min": 300, "max": 500},
        "análisis": {"min": 500, "max": 1000},
        "recomendaciones": {"min": 200, "max": 400},
        "referencias": {"min": 50, "max": 300},
    },
    "proposal": {
        "título": {"min": 5, "max": 15},
        "justificación": {"min": 300, "max": 600},
        "objetivos": {"min": 150, "max": 300},
        "metodología": {"min": 400, "max": 800},
        "recursos": {"min": 150, "max": 300},
        "presupuesto": {"min": 100, "max": 300},
        "referencias": {"min": 50, "max": 200},
    },
}

# Estructura por defecto (research paper)
DEFAULT_LIMITS = SECTION_LIMITS["research_paper"]


def get_section_limits(work_type: str = "research_paper") -> Dict[str, Dict[str, int]]:
    """
    Obtiene los límites de palabras para un tipo de trabajo.
    
    Args:
        work_type: Tipo de trabajo ('research_paper', 'essay', 'case_study', 'proposal')
    
    Returns:
        Dict con límites por sección
    """
    return SECTION_LIMITS.get(work_type, DEFAULT_LIMITS)


def calculate_total_target_words(section_limits: Dict) -> int:
    """
    Calcula el total de palabras esperado basado en límites de secciones.
    
    Args:
        section_limits: Dict con límites por sección
    
    Returns:
        Número estimado de palabras totales (suma de máximos)
    """
    return sum(limits.get("max", 0) for limits in section_limits.values())


def get_section_instructions(section_limits: Dict) -> str:
    """
    Genera instrucciones claras sobre límites de palabras para el prompt.
    
    Args:
        section_limits: Dict con límites por sección
    
    Returns:
        String con instrucciones formateadas
    """
    lines = ["LÍMITES ESTRICTOS DE PALABRAS POR SECCIÓN:"]
    lines.append("")
    
    for section, limits in section_limits.items():
        min_words = limits.get("min", 50)
        max_words = limits.get("max", 500)
        avg = (min_words + max_words) // 2
        
        section_name = section.replace("_", " ").title()
        lines.append(f"• {section_name}: {min_words}-{max_words} palabras (objetivo: ~{avg})")
    
    lines.append("")
    lines.append("IMPORTANTE: Mantén EXACTAMENTE estos límites. Cuenta las palabras de cada sección.")
    
    return "\n".join(lines)


def create_section_aware_prompt(
    base_prompt: str,
    section_limits: Dict,
    user_requirements: str = ""
) -> str:
    """
    Crea un prompt que instruya al modelo sobre límites por sección.
    
    Args:
        base_prompt: Prompt base
        section_limits: Límites por sección
        user_requirements: Requisitos adicionales del usuario
    
    Returns:
        Prompt mejorado con instrucciones de secciones
    """
    
    instructions = get_section_instructions(section_limits)
    
    enhanced = f"""{base_prompt}

{instructions}

ESTRUCTURA REQUERIDA:
"""
    
    for i, (section, limits) in enumerate(section_limits.items(), 1):
        section_name = section.replace("_", " ").title()
        min_words = limits.get("min", 50)
        max_words = limits.get("max", 500)
        enhanced += f"\n{i}. **{section_name}** ({min_words}-{max_words} palabras)"
    
    if user_requirements:
        enhanced += f"\n\nREQUISITOS DEL USUARIO:\n{user_requirements}"
    
    enhanced += "\n\nCUENTA CUIDADOSAMENTE LAS PALABRAS DE CADA SECCIÓN. No excedas los límites."
    
    return enhanced
