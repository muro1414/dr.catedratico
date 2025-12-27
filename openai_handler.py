"""
Manejo de la API de OpenAI para GPT-4o
"""

import os
import base64
from typing import Optional, List, Dict
from openai import OpenAI
from text_humanizer import humanize_text, ensure_proper_formatting
from prompts import DR_VALDES_SYSTEM_PROMPT, GENERATION_VALDES_STRICT_PROMPT, GENERATION_VALDES_HARD_PROMPT




def get_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no encontrada en el entorno")
    return OpenAI(api_key=api_key)

client = get_client()



def sanitize_output(text: str) -> str:
    """
    Elimina frases de meta-discurso y encabezados redundantes del texto generado.
    
    Args:
        text: Texto generado por el modelo
        
    Returns:
        Texto limpio sin meta-discurso
    """
    import re
    
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
    
    # Encabezados redundantes (si no fueron solicitados explícitamente)
    redundant_headers = [
        r"^Nom i cognoms:.*?\n",
        r"^Nombre y apellidos:.*?\n",
        r"^Assignatura:.*?\n",
        r"^Asignatura:.*?\n",
    ]
    
    # Limpiar texto
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


def build_context_block(attachments: List[Dict]) -> str:
    """Convierte adjuntos heterogéneos en un bloque de texto para el modelo."""
    if not attachments:
        return ""

    lines = ["ADJUNTOS DEL ESTUDIANTE:"]
    for i, att in enumerate(attachments, start=1):
        kind = att.get("kind", "desconocido")
        name = att.get("name", f"archivo_{i}")
        summary = att.get("summary", "(sin resumen)")

        if kind == "data":
            preview = att.get("dataframe_info", summary)
            lines.append(f"[{i}] {name} (datos):\n{preview}")
        elif kind in {"pdf", "docx", "text"}:
            content = att.get("content", summary)
            lines.append(f"[{i}] {name} ({kind}):\n{content}")
        elif kind == "image":
            info = summary
            lines.append(f"[{i}] {name} (imagen): {info}\nNota: la imagen se proporciona como base64 si es necesario para análisis de visión.")
        else:
            lines.append(f"[{i}] {name} ({kind}): {summary}")

    return "\n\n".join(lines)


def chat_with_valdez(
    messages: list,
    system_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """
    Envía un mensaje a GPT-4o con la personalidad del Dr. Valdés.
    
    Args:
        messages: Lista de mensajes en formato OpenAI
        system_prompt: Prompt del sistema personalizado
        temperature: Temperatura para variabilidad (0.7 es buena para el sarcasmo)
        max_tokens: Máximo de tokens de respuesta
    
    Returns:
        La respuesta del Dr. Valdés
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                *messages
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error en la API: {str(e)}"


def analyze_image_with_valdez(
    image_path: str,
    system_prompt: str,
    query: str = "Analiza este gráfico o imagen. Incluye aspectos metodológicos, estadísticos si aplica."
) -> str:
    """
    Analiza una imagen usando GPT-4o vision.
    
    Args:
        image_path: Ruta a la imagen
        system_prompt: Prompt del sistema
        query: Pregunta o instrucción sobre la imagen
    
    Returns:
        Análisis de la imagen
    """
    try:
        with open(image_path, "rb") as image_file:
            image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")
        
        # Determinar tipo de imagen
        ext = image_path.lower().split(".")[-1]
        media_type_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp"
        }
        media_type = media_type_map.get(ext, "image/jpeg")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": query
                        }
                    ]
                }
            ],
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analizando imagen: {str(e)}"


def extract_text_from_pdf_with_valdez(
    pdf_text: str,
    system_prompt: str,
    custom_query: Optional[str] = None
) -> str:
    """
    Analiza el contenido de un PDF usando GPT-4o.
    
    Args:
        pdf_text: Contenido extraído del PDF
        system_prompt: Prompt del sistema (usualmente ANALYSIS_SYSTEM_PROMPT)
        custom_query: Pregunta específica del usuario
    
    Returns:
        Análisis del PDF
    """
    try:
        query = custom_query or "Analiza este trabajo académico. Incluye: errores APA 7, fortalezas metodológicas, debilidades, sugerencias de mejora."
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Aquí está el contenido del PDF:\n\n{pdf_text}\n\n{query}"
                }
            ],
            temperature=0.7,
            max_tokens=2500,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analizando PDF: {str(e)}"


def generate_academic_work(
    topic: str,
    requirements: str,
    grade_band: str,
    language_hint: Optional[str] = None,
    word_count: Optional[int] = None,
    quality_level: int = 7,
    temperature: float = 0.8,
) -> str:
    """
    Genera un trabajo académico usando un proceso de dos pasos:
    1. Esquema interno con decisiones metodológicas
    2. Trabajo completo basado en ese esquema
    
    Args:
        topic: Tema del trabajo
        requirements: Requisitos específicos del usuario
        grade_band: Banda de nota objetivo (0-4, 5-6, 7-8, 9-10)
        language_hint: Código de idioma (ca, es, en)
        word_count: Palabras estimadas
        quality_level: 5-10 (para humanización del texto)
        temperature: Temperatura del modelo
    
    Returns:
        El trabajo académico generado, humanizado y sanitizado
    """
    try:
        # PASO A: Generar esquema interno con decisiones metodológicas
        length_line = f"Longitud aproximada: {word_count} palabras" if word_count else "Longitud: según necesario para el tema"
        idioma_line = f"Idioma objetivo: {language_hint}" if language_hint else "Idioma: automático (igual que el usuario)"
        
        schema_prompt = f"""
NOTA_OBJETIVO: {grade_band}

TEMA DEL TRABAJO:
{topic}

REQUISITOS ADICIONALES:
{requirements}

{idioma_line}

INSTRUCCIÓN ESPECIAL - PASO A (ESQUEMA INTERNO):
Genera un esquema realista con las decisiones metodológicas clave. NO escribas el trabajo completo todavía.
Incluye:
- Pregunta de recerca i hipòtesi operacionalitzada
- Disseny (experimental, quasi-experimental, correlacional, etc.) amb justificació
- Variables dependents/independents identificades
- Mostra: n aproximada, criteri reclutament, criteris inclusió/exclusió
- Instruments: què mesuren, α de Cronbach o validesa coneguda
- Procediment amb passos concrets
- Pla d'anàlisi correcte pel disseny
- Consideracions ètiques concretes
- Si NO hi ha dades reals: especifica que resultats seran "esperats/planificats" sense p-valors ni d numèrica

Respon NOMÉS amb aquest esquema, sense el treball complet.
"""

        # Generar esquema
        schema_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": GENERATION_VALDES_HARD_PROMPT},
                {"role": "user", "content": schema_prompt}
            ],
            temperature=temperature * 0.8,  # Ligeramente más determinista para el esquema
            max_tokens=1500,
        )
        
        schema = schema_response.choices[0].message.content
        
        # PASO B: Generar trabajo completo basado en el esquema
        work_prompt = f"""
NOTA_OBJETIVO: {grade_band}

TEMA DEL TRABAJO:
{topic}

REQUISITOS ADICIONALES:
{requirements}

{idioma_line}
{length_line}

ESQUEMA METODOLÓGICO QUE HAS DE SEGUIR:
{schema}

INSTRUCCIÓN ESPECIAL - PASO B (TRABAJO COMPLETO):
Genera el trabajo académico completo siguiendo el esquema metodológico anterior.
- Comença DIRECTAMENT amb el **TÍTOL:** sense preàmbuls.
- Estructura completa: Títol, Resum, Introducció, Mètode (segueix l'esquema), Resultats, Discussió, Referències (APA 7).
- Al final: "Checklist de coherència i punts a defensar" (6–10 bullets).
- Mantén coherència amb l'esquema en tot moment.
"""

        work_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": GENERATION_VALDES_HARD_PROMPT},
                {"role": "user", "content": work_prompt}
            ],
            temperature=temperature,
            max_tokens=4000,
        )
        
        work = work_response.choices[0].message.content
        
        # Sanitizar meta-discurso
        work = sanitize_output(work)
        
        # Humanizar el texto según nivel especificado
        work = humanize_text(work, quality_level=quality_level)
        work = ensure_proper_formatting(work)
        
        return work
    except Exception as e:
        return f"Error generando trabajo: {str(e)}"


def _make_draft_prompt(topic: str, requirements: str, language: str, word_count: Optional[int]) -> str:
    length_line = f"Longitud orientativa: {word_count} paraules" if word_count else "Longitud: la que correspongui al tema"
    return f"""
BORRADOR INICIAL (no perfecte):
- Estil humà natural.
- Coherent però amb imperfeccions intel·lectuals.
- No busquis excel·lència; evita simetries i pulit excessiu.
- Sense punts suspensius ni asteriscs; puntuació estàndard.

Idioma: {language}
{length_line}

Tema:
{topic}

Requisits:
{requirements}
"""


def _make_eval_prompt(grade_target: str, language: str, draft: str) -> str:
    return f"""
Avalua com a professor universitari real.
Tono: sec, directe, acadèmic.

Punts:
- Fortaleses sense condescendència.
- Debilitats conceptuals.
- Crítica metodològica si escau.
- Problemes d'estructura o profunditat.

Nota objectiu: {grade_target}
Idioma: {language}

Borrador a evaluar:
{draft}
"""


def _make_rewrite_prompt(grade_target: str, language: str, topic: str, requirements: str, draft: str, comments: str, word_count: Optional[int]) -> str:
    length_line = f"Longitud final: {word_count} paraules (aprox.)" if word_count else "Longitud final: segons les instruccions de l'usuari"
    return f"""
Reescriu el treball com a VERSIÓ FINAL coherent amb la nota objectiu.
- Mantén veu d'estudiant humà.
- Integra implícitament els comentaris del professor.
- Qualitat coherent amb la nota seleccionada.
- Evita semblar escrit "d'una sola vegada".
- Sense punts suspensius ni asteriscs; puntuació estàndard.
- No expliquis el procés, entrega directament el treball final.

Estructura: Títol, Resum, Introducció, Mètode, Resultats, Discussió, Referències (APA 7).
{length_line}
Idioma: {language}
Nota objectiu: {grade_target}

Tema:
{topic}

Requisits:
{requirements}

Comentaris del professor:
{comments}

Borrador original:
{draft}
"""


def generate_work_pipeline(
    topic: str,
    requirements: str,
    grade_target: str,
    language: str,
    word_count: Optional[int],
    temperature: float,
    quality_level: int,
) -> Dict[str, str]:
    """Genera borrador, evalúa y reescribe versión final. Devuelve {'final','comments'}.
    """
    try:
        # 1. Borrador
        draft_prompt = _make_draft_prompt(topic, requirements, language, word_count)
        draft_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": GENERATION_VALDES_STRICT_PROMPT},
                {"role": "user", "content": draft_prompt},
            ],
            temperature=temperature,
            max_tokens=2800,
        )
        draft = draft_resp.choices[0].message.content

        # 2. Evaluación
        eval_prompt = _make_eval_prompt(grade_target, language, draft)
        eval_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": GENERATION_VALDES_STRICT_PROMPT},
                {"role": "user", "content": eval_prompt},
            ],
            temperature=max(0.3, temperature - 0.2),
            max_tokens=1200,
        )
        comments = eval_resp.choices[0].message.content

        # 3. Reescritura final
        rewrite_prompt = _make_rewrite_prompt(grade_target, language, topic, requirements, draft, comments, word_count)
        final_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": GENERATION_VALDES_STRICT_PROMPT},
                {"role": "user", "content": rewrite_prompt},
            ],
            temperature=temperature,
            max_tokens=4000,
        )
        final_text = final_resp.choices[0].message.content

        final_text = humanize_text(final_text, quality_level=quality_level)
        final_text = ensure_proper_formatting(final_text)

        return {"final": final_text, "comments": comments}
    except Exception as e:
        return {"final": f"Error generant el treball: {str(e)}", "comments": ""}



