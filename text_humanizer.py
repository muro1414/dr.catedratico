"""
Funciones para humanizar texto generado por IA
Evita detectores de IA eliminando patrones típicos
"""

import re
import random


def humanize_text(text: str, quality_level: int = 7) -> str:
    """
    Humaniza el texto generado por IA según nivel de calidad.
    
    Args:
        text: Texto a humanizar
        quality_level: 5-10 (5=muy natural, 10=muy técnico)
    
    Returns:
        Texto humanizado
    """
    
    text = _remove_ia_patterns(text)

    if quality_level <= 6:
        text = _increase_naturalness(text)
    elif quality_level <= 7:
        text = _balance_academic_natural(text)
    elif quality_level >= 9:
        text = _increase_technical_density(text)

    text = _inject_micro_irregularities(text)
    text = _improve_flow(text)

    return text


def _remove_ia_patterns(text: str) -> str:
    """Elimina patrones típicos de IA generada."""
    
    # Eliminar puntos suspensivos innecesarios
    text = re.sub(r'(\w)\s*\.\.\.\s*(\w)', r'\1 \2', text)
    
    # Eliminar múltiples asteriscos de énfasis
    text = re.sub(r'\*{2,}(.+?)\*{2,}', r'\1', text)
    
    # Reducir conectores excesivos al inicio de párrafos
    excessive_connectors = [
        r'^Por lo tanto,',
        r'^En conclusión,',
        r'^Además,',
        r'^Sin embargo,',
        r'^No obstante,',
        r'^Finalmente,',
        r'^En resumen,'
    ]
    
    for connector in excessive_connectors:
        # Eliminar algunos (no todos) para parecer más natural
        matches = re.findall(connector, text, re.MULTILINE)
        if len(matches) > 3:
            # Si hay muchos, eliminar algunos
            text = re.sub(connector, '', text, count=len(matches)//2)
    
    # Eliminar emojis o símbolos especiales
    text = re.sub(r'[^\w\s\.,;:\'\"-()]', '', text)
    
    return text


def _increase_naturalness(text: str) -> str:
    """Aumenta lo conversacional del texto para nivel 5-6."""
    
    # Dividir en párrafos
    paragraphs = text.split('\n\n')
    result = []
    
    for para in paragraphs:
        # Ocasionalmente acortar párrafos muy largos
        if len(para) > 400 and random.random() < 0.3:
            # Dividir en dos
            sentences = re.split(r'(?<=[.!?])\s+', para)
            mid = len(sentences) // 2
            para = '\n\n'.join([
                ' '.join(sentences[:mid]),
                ' '.join(sentences[mid:])
            ])
        
        result.append(para)
    
    return '\n\n'.join(result)


def _balance_academic_natural(text: str) -> str:
    """Balance entre académico y natural para nivel 7."""
    
    # Mantener una buena estructura pero con variación
    paragraphs = text.split('\n\n')
    tweaked = []
    for p in paragraphs:
        if len(p.split()) > 120 and random.random() < 0.25:
            sentences = re.split(r'(?<=[.!?])\s+', p)
            random.shuffle(sentences)
            p = ' '.join(sentences)
        tweaked.append(p)
    return '\n\n'.join(tweaked)


def _increase_technical_density(text: str) -> str:
    """Aumenta la densidad técnica para nivel 9-10."""
    
    # Este texto ya es técnico, solo asegurar que tiene complejidad
    paragraphs = text.split('\n\n')
    
    for i, para in enumerate(paragraphs):
        # Asegurar que los párrafos tienen múltiples conceptos
        if len(para) < 200 and i > 0:
            # Fusionar con párrafo anterior si es muy corto
            paragraphs[i-1] += ' ' + para
            paragraphs[i] = ''
    
    return '\n\n'.join([p for p in paragraphs if p.strip()])


def _inject_micro_irregularities(text: str) -> str:
    """Introduce pequeñas irregularidades para evitar patrones detectables."""
    paragraphs = text.split('\n\n')
    result = []
    fillers = [
        "En lo esencial,", "Dicho esto,", "Aun así,", "Vale subrayar lo central.", "En síntesis breve,"
    ]
    for p in paragraphs:
        if random.random() < 0.3 and len(p.split()) > 40:
            # Insertar una frase corta al inicio
            p = random.choice(fillers) + ' ' + p
        result.append(p)
    return '\n\n'.join(result)


def _improve_flow(text: str) -> str:
    """Mejora la fluidez general del texto."""
    
    # Reemplazar conectores repetidos con variantes
    connector_variations = {
        r'\bAdicionalmente,': ['Asimismo,', 'De igual forma,', 'Simultáneamente,', 'También,'],
        r'\bEsta investigación': ['El presente estudio', 'Este análisis', 'La investigación'],
        r'\bsiguiendo a': ['conforme a', 'de acuerdo con', 'según'],
        r'\bse puede argumentar': ['cabe argumentar', 'es posible plantear', 'se podría sostener'],
        r'\bEn conclusión,': ['En suma,', 'En breve,', 'En definitiva,'],
    }
    
    for pattern, variations in connector_variations.items():
        matches = re.findall(pattern, text)
        if len(matches) > 1:
            # Reemplazar algunos con variantes
            for match in matches[1:]:
                replacement = random.choice(variations)
                text = re.sub(pattern, replacement, text, count=1)
    
    return text


def add_academic_variety(text: str) -> str:
    """Agrega variedad académica al texto."""
    
    # Agregar ocasionales referencias indirectas
    indirect_references = [
        "Según la literatura en cuestión,",
        "Desde diversas perspectivas teóricas,",
        "En el contexto académico,",
        "Desde una óptica crítica,",
        "Considerando el panorama actual,"
    ]
    
    # Dividir en párrafos
    paragraphs = text.split('\n\n')
    
    # Ocasionalmente comenzar párrafo con referencia indirecta
    for i in range(1, len(paragraphs)):
        if random.random() < 0.1 and not paragraphs[i].strip().startswith(('Por', 'Sin', 'No', 'En')):
            paragraphs[i] = random.choice(indirect_references) + ' ' + paragraphs[i]
    
    return '\n\n'.join(paragraphs)


def ensure_proper_formatting(text: str) -> str:
    """Asegura formato APA 7 correcto sin símbolos de IA."""
    
    # Asegurar espaciado correcto
    text = re.sub(r' +', ' ', text)  # Espacios múltiples -> uno
    text = re.sub(r'\n{3,}', '\n\n', text)  # Múltiples saltos -> dos
    
    # Asegurar puntuación correcta
    text = re.sub(r' +([.,;:])', r'\1', text)  # Espacio antes de puntuación
    
    # Comillas correctas
    text = re.sub(r'"([^"]*)"', r'"\1"', text)
    
    return text
