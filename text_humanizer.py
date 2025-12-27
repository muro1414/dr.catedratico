"""
Funciones para humanizar texto generado por IA
Evita detectores de IA eliminando patrones típicos
"""

import re
import random


def humanize_text(text: str, quality_level: int = 7, target_words: int = None) -> str:
    """
    Humaniza el texto generado por IA según nivel de calidad.
    Intenta pasar detectores de IA con -15% de probabilidad de detección.
    
    Args:
        text: Texto a humanizar
        quality_level: 5-10 (5=muy natural, 10=muy técnico)
        target_words: Número objetivo de palabras (ajusta el texto)
    
    Returns:
        Texto humanizado y ajustado al conteo de palabras
    """
    
    text = _remove_ia_patterns(text)

    if quality_level <= 6:
        text = _increase_naturalness(text)
    elif quality_level <= 7:
        text = _balance_academic_natural(text)
    elif quality_level >= 9:
        text = _increase_technical_density(text)

    # Aplicar técnicas anti-IA agresivas
    text = _inject_micro_irregularities(text)
    text = _humanize_sentence_structure(text)
    text = _add_human_errors_and_corrections(text)
    text = _improve_flow(text)
    text = _vary_vocabulary(text)

    # Ajustar al conteo de palabras si es especificado
    if target_words:
        text = adjust_to_word_count(text, target_words)

    return text


def adjust_sections_to_word_counts(
    text: str,
    section_limits: dict,
    language: str = "es"
) -> str:
    """
    Ajusta cada sección del trabajo a su límite de palabras.
    
    Args:
        text: Texto completo
        section_limits: Dict {sección: {min: X, max: Y}}
        language: Idioma
    
    Returns:
        Texto ajustado por sección
    """
    
    from validators import extract_sections, count_words_in_sections
    
    sections = extract_sections(text, language=language)
    word_counts = count_words_in_sections(text)
    
    # Procesar cada sección
    modified_sections = {}
    
    for section_name, content in sections.items():
        if section_name not in section_limits:
            modified_sections[section_name] = content
            continue
        
        limits = section_limits[section_name]
        min_words = limits.get("min", 0)
        max_words = limits.get("max", 9999)
        current_words = len(content.split())
        
        # Si está fuera del rango, ajustar
        if current_words < min_words:
            # Expandir
            content = _expand_section(content, min_words - current_words)
        elif current_words > max_words:
            # Reducir
            content = _reduce_section(content, current_words - max_words)
        
        modified_sections[section_name] = content
    
    # Reconstruir el texto
    result = []
    for section_name, content in modified_sections.items():
        if content:
            result.append(content)
    
    return "\n\n".join(result)


def _expand_section(text: str, words_needed: int) -> str:
    """Expande una sección agregando detalles."""
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    expansions = [
        "Es relevante mencionar que ",
        "Cabe destacar que ",
        "Adicionalmente, ",
        "En este contexto, es importante notar que ",
        "Específicamente, ",
    ]
    
    added = 0
    for i in range(1, len(sentences)):
        if added >= words_needed:
            break
        
        expansion = random.choice(expansions)
        sentences.insert(i, expansion)
        added += len(expansion.split())
    
    return " ".join(sentences)


def _reduce_section(text: str, words_to_remove: int) -> str:
    """Reduce una sección eliminando contenido redundante."""
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Eliminar frases menos importantes
    removed = 0
    i = 0
    while removed < words_to_remove and i < len(sentences):
        sent = sentences[i]
        
        # Frases que es seguro eliminar
        if any(phrase in sent.lower() for phrase in
               ['además', 'sin embargo', 'por otro lado', 'en conclusión',
                'podría argumentarse', 'es interesante notar']):
            removed += len(sent.split())
            sentences.pop(i)
            continue
        
        i += 1
    
    return " ".join(sentences)


def adjust_to_word_count(text: str, target_words: int, tolerance: int = 15) -> str:
    """
    Ajusta el texto al número objetivo de palabras.
    
    Args:
        text: Texto a ajustar
        target_words: Número objetivo de palabras
        tolerance: Margen permitido (+/- palabras)
    
    Returns:
        Texto ajustado al conteo de palabras
    """
    current_words = len(text.split())
    diff = current_words - target_words
    
    # Si está dentro del margen, no cambiar
    if abs(diff) <= tolerance:
        return text
    
    if diff > 0:  # Hay que reducir
        text = _reduce_text(text, diff)
    else:  # Hay que expandir
        text = _expand_text(text, abs(diff))
    
    return text


def _reduce_text(text: str, words_to_remove: int) -> str:
    """Reduce el texto eliminando frases redundantes."""
    
    # Separar por párrafos
    paragraphs = text.split('\n\n')
    
    while words_to_remove > 0 and len(paragraphs) > 1:
        # Encontrar párrafo más largo
        longest_idx = max(range(len(paragraphs)), 
                         key=lambda i: len(paragraphs[i].split()))
        
        sentences = re.split(r'(?<=[.!?])\s+', paragraphs[longest_idx])
        
        # Eliminar frases introductoras o conectores
        for i, sent in enumerate(sentences):
            if any(word in sent.lower() for word in 
                   ['en conclusión', 'por lo tanto', 'además', 'sin embargo', 
                    'no obstante', 'en resumen', 'así pues', 'podría argumentarse']):
                removed_words = len(sent.split())
                sentences.pop(i)
                words_to_remove -= removed_words
                break
        
        paragraphs[longest_idx] = ' '.join(sentences)
    
    return '\n\n'.join([p for p in paragraphs if p.strip()])


def _expand_text(text: str, words_to_add: int) -> str:
    """Expande el texto agregando detalles y ejemplos."""
    
    paragraphs = text.split('\n\n')
    expansions = [
        "Es relevante destacar que ",
        "Cabe mencionar que ",
        "A nivel metodológico, ",
        "Desde una perspectiva analítica, ",
        "En este contexto, ",
        "Resulta pertinente señalar que ",
        "Específicamente, "
    ]
    
    # Intentar agregar frases expansivas
    remaining = words_to_add
    for i, para in enumerate(paragraphs):
        if remaining <= 0:
            break
        if len(para.split()) > 30:  # Solo en párrafos largos
            sentences = re.split(r'(?<=[.!?])\s+', para)
            if len(sentences) > 1:
                # Agregar frase expansiva después de segunda oración
                insert_idx = min(2, len(sentences))
                expansion = random.choice(expansions)
                sentences.insert(insert_idx, expansion + sentences[insert_idx].lower())
                paragraphs[i] = ' '.join(sentences)
                remaining -= len(expansion.split()) + 5
    
    return '\n\n'.join(paragraphs)


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


def _humanize_sentence_structure(text: str) -> str:
    """Varía la estructura de oraciones para parecer más humano."""
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Variar largo de oraciones
    for i, sent in enumerate(sentences):
        words = sent.split()
        
        # Ocasionalmente fragmentar oraciones largas
        if len(words) > 25 and random.random() < 0.3:
            mid = len(words) // 2
            sentences[i] = ' '.join(words[:mid]) + '. ' + ' '.join(words[mid:])
        
        # Ocasionalmente combinar oraciones cortas
        if i < len(sentences) - 1 and len(words) < 10:
            next_words = sentences[i+1].split()
            if len(next_words) < 10 and random.random() < 0.2:
                sentences[i] = sent + ' ' + sentences[i+1]
                sentences[i+1] = ''
    
    text = ' '.join([s for s in sentences if s.strip()])
    return text


def _add_human_errors_and_corrections(text: str) -> str:
    """Agrega pequeños 'errores' humanos que luego corrige para parecer más natural."""
    
    paragraphs = text.split('\n\n')
    result = []
    
    for para in paragraphs:
        if random.random() < 0.15 and len(para.split()) > 50:
            # Agregar una frase ligeramente redundante que alguien podría escribir
            # pero que no es obvia como error
            additions = [
                "No es menor destacar que ",
                "Resulta interesante notar que ",
                "Esto cobra relevancia en tanto que ",
            ]
            
            sentences = re.split(r'(?<=[.!?])\s+', para)
            if len(sentences) > 2:
                insert_idx = random.randint(1, len(sentences)-2)
                sentences.insert(insert_idx, random.choice(additions))
                para = ' '.join(sentences)
        
        result.append(para)
    
    return '\n\n'.join(result)


def _vary_vocabulary(text: str) -> str:
    """Varía el vocabulario para evitar repeticiones detectables por IA."""
    
    # Sinónimos para palabras frecuentes en textos académicos
    replacements = {
        r'\bestudio\b': ['investigación', 'análisis', 'trabajo', 'proyecto'],
        r'\bconsideración\b': ['reflexión', 'análisis', 'evaluación'],
        r'\bimportancia\b': ['relevancia', 'trascendencia', 'significación'],
        r'\bperspectiva\b': ['óptica', 'enfoque', 'ángulo'],
        r'\bseñala\b': ['indica', 'plantea', 'propone'],
        r'\bdemuestra\b': ['evidencia', 'sugiere', 'manifiesta'],
        r'\bfactor\b': ['elemento', 'aspecto', 'componente'],
        r'\bcontexto\b': ['marco', 'escenario', 'ámbito'],
    }
    
    for pattern, synonyms in replacements.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        # Reemplazar algunos (no todos) con sinónimos
        for i, match in enumerate(matches):
            if random.random() < 0.6:  # 60% de probabilidad
                text = text[:match.start()] + random.choice(synonyms) + text[match.end():]
    
    return text


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
