"""
Validadores para asegurar que los trabajos cumplen las pautas
"""

import re
from typing import Dict, Optional, Tuple


def extract_sections(
    text: str,
    section_names: list = None,
    language: str = "es"
) -> Dict[str, str]:
    """
    Extrae secciones del texto basado en títulos.
    
    Args:
        text: Texto completo del trabajo
        section_names: Nombres esperados de secciones (ej: ['introducción', 'método'])
        language: Idioma ('es' para español, 'ca' para catalán)
    
    Returns:
        Dict con secciones extraídas {nombre_sección: contenido}
    """
    
    sections = {}
    text_lower = text.lower()
    
    # Patrones de secciones en español
    patterns_es = {
        "título": r"^([A-Z][^\n]*[a-z].*?)(?=\n\n(?:resumen|abstract|introducción))",
        "resumen": r"(?:resumen|abstract)[:\s]*\n+(.*?)(?=\nintroducción|introduction)",
        "introducción": r"(?:introducción|introduction|intro)[:\s]*\n+(.*?)(?=\nmétodo|method|m[eé]todo)",
        "método": r"(?:m[eé]todo|método|methodology|metodología)[:\s]*\n+(.*?)(?=\nresultado|result|hallazgo)",
        "resultados": r"(?:resultado|resultados|resultado|result|hallazgo|hallazgos)[:\s]*\n+(.*?)(?=\ndiscusión|discussion)",
        "discusión": r"(?:discusión|discussion)[:\s]*\n+(.*?)(?=\nreferencia|conclusion)",
        "conclusión": r"(?:conclusión|conclusion)[:\s]*\n+(.*?)(?=\nreferencia)",
        "referencias": r"(?:referencias|references|bibliografía)[:\s]*\n+(.*?)$",
    }
    
    # Patrones de secciones en catalán
    patterns_ca = {
        "títol": r"^([A-Z][^\n]*[a-z].*?)(?=\n\n(?:resum|abstract|introducció))",
        "resum": r"(?:resum|abstract)[:\s]*\n+(.*?)(?=\nintroduccí|introduction)",
        "introducció": r"(?:introducci[oó]|introduction|intro)[:\s]*\n+(.*?)(?=\nm[eè]tode|method)",
        "mètode": r"(?:m[eè]tode|metode|methodology|metodologia)[:\s]*\n+(.*?)(?=\nresultat|result|descobriment)",
        "resultats": r"(?:resultat|resultats|result|descobriment|descobriments)[:\s]*\n+(.*?)(?=\ndiscussió|discussion)",
        "discussió": r"(?:discussió|discussion)[:\s]*\n+(.*?)(?=\nreferència|conclusió)",
        "conclusió": r"(?:conclusió|conclusion)[:\s]*\n+(.*?)(?=\nreferència)",
        "referències": r"(?:refer[eè]ncies|references|bibliografia)[:\s]*\n+(.*?)$",
    }
    
    patterns = patterns_ca if language == "ca" else patterns_es
    
    for section_name, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            content = match.group(1) if match.lastindex else match.group(0)
            sections[section_name] = content.strip()
    
    return sections


def count_words_in_sections(text: str, section_names: list = None) -> Dict[str, int]:
    """
    Cuenta palabras en cada sección del texto.
    
    Args:
        text: Texto del trabajo
        section_names: Nombres de secciones a contar
    
    Returns:
        Dict {nombre_sección: cantidad_palabras}
    """
    
    sections = extract_sections(text)
    word_counts = {}
    
    for section_name, content in sections.items():
        words = len(content.split())
        word_counts[section_name] = words
    
    return word_counts


def validate_section_word_counts(
    text: str,
    section_limits: Dict[str, Dict[str, int]],
    language: str = "es"
) -> Dict:
    """
    Valida que cada sección cumpla con los límites de palabras.
    
    Args:
        text: Texto del trabajo
        section_limits: Dict con límites {sección: {min: X, max: Y}}
        language: Idioma
    
    Returns:
        Dict con resultados de validación por sección
    """
    
    word_counts = count_words_in_sections(text)
    validation = {
        'total_words': len(text.split()),
        'sections': {},
        'compliant_sections': 0,
        'non_compliant_sections': 0,
        'issues': []
    }
    
    for section_name, expected_limits in section_limits.items():
        actual_count = word_counts.get(section_name, 0)
        min_words = expected_limits.get("min", 0)
        max_words = expected_limits.get("max", 9999)
        
        is_compliant = min_words <= actual_count <= max_words
        
        validation['sections'][section_name] = {
            'actual': actual_count,
            'min': min_words,
            'max': max_words,
            'compliant': is_compliant,
            'difference': actual_count - max_words if actual_count > max_words else (min_words - actual_count if actual_count < min_words else 0)
        }
        
        if is_compliant:
            validation['compliant_sections'] += 1
        else:
            validation['non_compliant_sections'] += 1
            if actual_count < min_words:
                validation['issues'].append(
                    f"{section_name}: Muy corta ({actual_count} palabras, mínimo {min_words}). "
                    f"Faltan {min_words - actual_count} palabras."
                )
            else:
                validation['issues'].append(
                    f"{section_name}: Muy larga ({actual_count} palabras, máximo {max_words}). "
                    f"Excede {actual_count - max_words} palabras."
                )
    
    return validation


def validate_work(
    text: str,
    target_words: int = None,
    tolerance: int = 15,
    language: str = "es"
) -> dict:
    """
    Valida que el trabajo cumpla las pautas especificadas.
    
    Args:
        text: Texto a validar
        target_words: Número objetivo de palabras (None = sin validación)
        tolerance: Margen permitido para palabras (+/- palabras)
        language: Idioma ('es' para español, 'ca' para catalán)
    
    Returns:
        Dict con resultados de validación:
        {
            'is_valid': bool,
            'word_count': int,
            'word_count_ok': bool,
            'has_title': bool,
            'has_abstract': bool,
            'has_introduction': bool,
            'has_method': bool,
            'has_results': bool,
            'has_discussion': bool,
            'has_references': bool,
            'issues': [list of issues],
            'warnings': [list of warnings]
        }
    """
    
    issues = []
    warnings = []
    
    # Contar palabras
    words = text.split()
    word_count = len(words)
    word_count_ok = True
    
    if target_words:
        diff = abs(word_count - target_words)
        word_count_ok = diff <= tolerance
        if not word_count_ok:
            issues.append(
                f"Conteo de palabras: {word_count} (objetivo: {target_words}±{tolerance}). "
                f"Diferencia: {diff} palabras."
            )
    else:
        if word_count < 100:
            issues.append(f"Texto muy corto: {word_count} palabras")
    
    # Verificar estructura académica
    text_lower = text.lower()
    
    # Patrones para español
    if language == "es":
        has_title = bool(re.search(r'^[A-Z][^.\n]*[a-z]', text, re.MULTILINE))
        has_abstract = bool(re.search(r'(resumen|abstract)', text_lower))
        has_introduction = bool(re.search(r'(introducción|introducci[oó]n)', text_lower))
        has_method = bool(re.search(r'(método|m[eé]todo|metodolog[ií]a)', text_lower))
        has_results = bool(re.search(r'(resultado|resultados|hallazgo|hallazgos)', text_lower))
        has_discussion = bool(re.search(r'(discusión|discusi[oó]n)', text_lower))
        has_references = bool(re.search(r'(referencias|referencias bibliogr[aá]ficas|bibliografía)', text_lower))
    
    # Patrones para catalán
    elif language == "ca":
        has_title = bool(re.search(r'^[A-Z][^.\n]*[a-z]', text, re.MULTILINE))
        has_abstract = bool(re.search(r'(resum|abstract)', text_lower))
        has_introduction = bool(re.search(r'(introducci[oó]|introducció)', text_lower))
        has_method = bool(re.search(r'(m[eè]tode|metodologia)', text_lower))
        has_results = bool(re.search(r'(resultat|resultats|descobriment|descobriments)', text_lower))
        has_discussion = bool(re.search(r'(discussió|discussio)', text_lower))
        has_references = bool(re.search(r'(refer[eè]ncies|bibliografia|referències bibliogr[àa]fiques)', text_lower))
    
    else:
        has_title = has_abstract = has_introduction = has_method = has_results = has_discussion = has_references = False
    
    # Validar estructura
    structure_elements = [
        ('Título', has_title),
        ('Resumen/Abstract', has_abstract),
        ('Introducción', has_introduction),
        ('Método', has_method),
        ('Resultados', has_results),
        ('Discusión', has_discussion),
        ('Referencias', has_references)
    ]
    
    missing = [name for name, present in structure_elements if not present]
    
    if missing:
        if len(missing) >= 4:
            issues.append(f"Faltan secciones críticas: {', '.join(missing)}")
        else:
            warnings.append(f"Secciones faltantes: {', '.join(missing)}")
    
    # Validar formato APA básico
    # Buscar comillas abiertas sin cerrar
    open_quotes = text.count('"') % 2
    if open_quotes != 0:
        warnings.append("Posibles comillas sin cerrar")
    
    # Validar párrafos
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) < 3:
        warnings.append("Muy pocos párrafos para trabajo académico")
    
    # Revisar repetición excesiva de palabras
    words_list = re.findall(r'\b[a-záéíóúàèìòùäëïöüñ]{4,}\b', text_lower)
    if words_list:
        word_freq = {}
        for word in words_list:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Si alguna palabra se repite más del 5% del total
        max_freq = max(word_freq.values())
        if max_freq > len(words_list) * 0.05:
            most_repeated = max(word_freq, key=word_freq.get)
            warnings.append(
                f"Palabra muy repetida: '{most_repeated}' "
                f"(aparece {max_freq} veces)"
            )
    
    # Validar que no parece totalmente generado por IA
    # Buscar patrones típicos de IA
    ai_patterns = [
        (r'En conclusión, en esta \w+', 'Patrón típico de IA'),
        (r'Es importante destacar que.*?que.*?que.*?que', 'Repetición de estructura'),
        (r'El presente \w+ analiza.*?Se puede concluir', 'Estructura muy sistemática'),
    ]
    
    for pattern, description in ai_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Posible patrón de IA: {description}")
    
    # Determinar validez general
    is_valid = len(issues) == 0
    
    return {
        'is_valid': is_valid,
        'word_count': word_count,
        'word_count_ok': word_count_ok,
        'has_title': has_title,
        'has_abstract': has_abstract,
        'has_introduction': has_introduction,
        'has_method': has_method,
        'has_results': has_results,
        'has_discussion': has_discussion,
        'has_references': has_references,
        'paragraph_count': len(paragraphs),
        'issues': issues,
        'warnings': warnings,
        'summary': f"✓ Válido" if is_valid else f"✗ {len(issues)} problemas encontrados"
    }


def format_section_validation_report(validation: dict) -> str:
    """
    Formatea un reporte de validación por secciones.
    
    Args:
        validation: Resultado de validate_section_word_counts()
    
    Returns:
        String formateado para mostrar al usuario
    """
    
    report = []
    report.append("📊 VALIDACIÓN DE LÍMITES POR SECCIÓN")
    report.append("=" * 60)
    
    # Resumen general
    total = validation['compliant_sections'] + validation['non_compliant_sections']
    compliant_pct = (validation['compliant_sections'] / total * 100) if total > 0 else 0
    
    status = "✓ CUMPLE" if validation['non_compliant_sections'] == 0 else "✗ INCUMPLE"
    report.append(f"\n{status} - {validation['compliant_sections']}/{total} secciones válidas ({compliant_pct:.0f}%)")
    report.append(f"Total de palabras: {validation['total_words']}")
    
    # Detalles por sección
    report.append("\n📋 POR SECCIÓN:")
    report.append("-" * 60)
    
    for section_name, details in validation['sections'].items():
        actual = details['actual']
        min_w = details['min']
        max_w = details['max']
        compliant = details['compliant']
        
        # Mostrar como progreso visual
        symbol = "✓" if compliant else "✗"
        section_display = section_name.replace("_", " ").title()
        
        report.append(f"{symbol} {section_display}")
        report.append(f"   Palabras: {actual} (rango: {min_w}-{max_w})")
        
        if not compliant:
            if actual < min_w:
                report.append(f"   ⚠️ Falta: {min_w - actual} palabras")
            else:
                report.append(f"   ⚠️ Exceso: {actual - max_w} palabras")
        report.append("")
    
    # Problemas encontrados
    if validation['issues']:
        report.append("\n🔴 PROBLEMAS ENCONTRADOS:")
        for issue in validation['issues']:
            report.append(f"   • {issue}")
    else:
        report.append("\n✅ Todas las secciones cumplen los límites")
    
    return "\n".join(report)


def format_validation_report(validation: dict) -> str:
    """
    Formatea un reporte de validación para mostrar al usuario.
    
    Args:
        validation: Resultado de validate_work()
    
    Returns:
        String formateado para mostrar
    """
    
    report = []
    report.append("📊 REPORTE DE VALIDACIÓN")
    report.append("=" * 50)
    
    # Resumen
    report.append(f"\n{validation['summary']}")
    
    # Conteo de palabras
    report.append(f"\n📝 Conteo de palabras: {validation['word_count']}")
    if not validation['word_count_ok']:
        report.append("   ⚠️ NO CUMPLE conteo objetivo")
    
    # Estructura
    report.append("\n📋 Estructura:")
    structure = [
        ('Título', validation['has_title']),
        ('Resumen', validation['has_abstract']),
        ('Introducción', validation['has_introduction']),
        ('Método', validation['has_method']),
        ('Resultados', validation['has_results']),
        ('Discusión', validation['has_discussion']),
        ('Referencias', validation['has_references']),
    ]
    
    for name, present in structure:
        symbol = "✓" if present else "✗"
        report.append(f"   {symbol} {name}")
    
    # Problemas
    if validation['issues']:
        report.append("\n🔴 PROBLEMAS (críticos):")
        for issue in validation['issues']:
            report.append(f"   • {issue}")
    
    # Advertencias
    if validation['warnings']:
        report.append("\n🟡 ADVERTENCIAS:")
        for warning in validation['warnings']:
            report.append(f"   • {warning}")
    
    return "\n".join(report)


def check_against_requirements(text: str, requirements: str) -> dict:
    """
    Verifica que el trabajo cumpla los requisitos específicos del usuario.
    
    Args:
        text: Texto generado
        requirements: String con requisitos (ej: "Debe incluir X, debe analizar Y")
    
    Returns:
        Dict con verificación de requisitos
    """
    
    compliance = {
        'requirements_text': requirements,
        'checks': [],
        'compliance_score': 0
    }
    
    # Buscar keywords clave en los requisitos
    requirement_lines = [r.strip() for r in requirements.split('\n') if r.strip()]
    
    for req in requirement_lines:
        # Extraer palabras clave (simples)
        keywords = re.findall(r'\b[a-záéíóúàèìòùäëïöüñ]{4,}\b', req.lower())
        
        if not keywords:
            continue
        
        # Verificar si al menos algunas palabras están en el texto
        text_lower = text.lower()
        found_keywords = [kw for kw in keywords if kw in text_lower]
        
        compliance_pct = (len(found_keywords) / len(keywords) * 100) if keywords else 0
        
        compliance['checks'].append({
            'requirement': req[:100],
            'found_keywords': found_keywords,
            'compliance': compliance_pct
        })
    
    if compliance['checks']:
        avg_compliance = sum(c['compliance'] for c in compliance['checks']) / len(compliance['checks'])
        compliance['compliance_score'] = avg_compliance
    
    return compliance
