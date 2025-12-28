"""
Manejo simplificado de la API de OpenAI - Dr. Sanal
Sin límites artificiales de palabras ni bandas de notas.
"""

import os
import base64
from typing import Optional, List, Dict, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from text_humanizer import humanize_text_light, sanitize_meta_discourse
from prompts import DR_SANAL_SYSTEM_PROMPT
from config import MODEL_SELECTION_RULES, DEFAULT_MODEL, AVAILABLE_MODELS
import tiktoken
import time

load_dotenv()


def get_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no encontrada en el entorno")
    return OpenAI(api_key=api_key)


client = get_client()

# === Token & Rate Limiting Utilities ===

def _enc():
    return tiktoken.get_encoding("cl100k_base")


def estimate_tokens(text: str) -> int:
    try:
        return len(_enc().encode(text or ""))
    except Exception:
        return len(text or "") // 4


def estimate_message_tokens(messages: List[Dict]) -> int:
    total = 0
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, list):
            joined = "\n".join(part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text")
            total += estimate_tokens(joined)
        else:
            total += estimate_tokens(str(content))
    return total


def truncate_text_to_tokens(text: str, max_tokens: int) -> str:
    enc = _enc()
    ids = enc.encode(text or "")
    if len(ids) <= max_tokens:
        return text
    return enc.decode(ids[:max_tokens])


class TokenRateLimiter:
    def __init__(self, tpm_limit: int = None):
        self.tpm_limit = tpm_limit or int(os.getenv("OPENAI_TPM_LIMIT", "100000"))
        self.window_tokens: List[Tuple[float, int]] = []

    def allow(self, planned_tokens: int):
        now = time.time()
        # Purge entries older than 60s
        self.window_tokens = [(ts, tok) for ts, tok in self.window_tokens if now - ts < 60]
        used = sum(tok for _, tok in self.window_tokens)
        if used + planned_tokens <= self.tpm_limit:
            self.window_tokens.append((now, planned_tokens))
            return
        # Sleep until enough capacity
        deficit = used + planned_tokens - self.tpm_limit
        sleep_s = max(1.0, (deficit / max(1, self.tpm_limit)) * 60)
        time.sleep(sleep_s)
        # After sleeping, register
        now2 = time.time()
        self.window_tokens = [(ts, tok) for ts, tok in self.window_tokens if now2 - ts < 60]
        self.window_tokens.append((now2, planned_tokens))


rate_limiter = TokenRateLimiter()


def build_attachments_summary(attachments: List[Dict], max_tokens: int = 3000) -> str:
    lines = ["ADJUNTOS DEL ESTUDIANTE (resumen):"]
    for i, att in enumerate(attachments or [], start=1):
        kind = att.get("kind", "?")
        name = att.get("name", f"archivo_{i}")
        summary = att.get("summary", "")
        if kind == "data":
            preview = att.get("dataframe_info", summary)
            content = f"[{i}] {name} (datos):\n{preview}"
        elif kind in {"pdf", "docx", "text"}:
            content = f"[{i}] {name} ({kind}):\n{summary}"
        elif kind == "image":
            content = f"[{i}] {name} (imagen): {summary}"
        else:
            content = f"[{i}] {name} ({kind}): {summary}"
        lines.append(content)
    text = "\n\n".join(lines)
    return truncate_text_to_tokens(text, max_tokens)


def looks_truncated(text: str) -> bool:
    if not text or len(text) < 200:
        return False
    tail = text[-200:]
    ends_ok = any(text.strip().endswith(p) for p in [".", "!", "?", ")", "]", "\""])
    has_heading = any(h in tail.lower() for h in ["referencias", "bibliografía", "discusión", "resultados"])
    mid_word_cut = tail.endswith(" ") and not ends_ok
    return (not ends_ok) or mid_word_cut or has_heading


def select_model(
    context: str = "chat",
    complexity: float = 0.5,
    force_model: Optional[str] = None
) -> str:
    """
    Selecciona el modelo GPT más apropiado según el contexto y complejidad.
    
    Args:
        context: Tipo de tarea ('chat', 'analysis', 'generation', 'vision', 'simple')
        complexity: Nivel de complejidad (0.0-1.0, donde 1.0 es máxima)
        force_model: Si se proporciona, ignora la selección automática
    
    Returns:
        Nombre del modelo a usar
    """
    if force_model and force_model in AVAILABLE_MODELS:
        return force_model
    
    base_model = MODEL_SELECTION_RULES.get(context, DEFAULT_MODEL)
    
    if complexity > 0.8:
        return "gpt-4-turbo"
    elif complexity < 0.3:
        return "gpt-3.5-turbo"
    
    return base_model


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


def chat_with_sanal(
    messages: list,
    system_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 3000,
    context: str = "chat",
    complexity: float = 0.5,
    force_model: Optional[str] = None,
) -> str:
    """
    Envía un mensaje a OpenAI con la personalidad del Dr. Sanal.
    Selecciona automáticamente el mejor modelo según el contexto.
    
    Args:
        messages: Lista de mensajes en formato OpenAI
        system_prompt: Prompt del sistema personalizado
        temperature: Temperatura para variabilidad (0.7 es buena para el sarcasmo)
        max_tokens: Máximo de tokens de respuesta
        context: Tipo de tarea ('chat', 'analysis', 'generation', 'vision', 'simple')
        complexity: Nivel de complejidad (0.0-1.0)
        force_model: Fuerza un modelo específico
    
    Returns:
        La respuesta del Dr. Sanal
    """
    model = select_model(context=context, complexity=complexity, force_model=force_model)
    
    try:
        response = client.chat.completions.create(
            model=model,
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


def analyze_image_with_sanal(
    image_path: str,
    system_prompt: str,
    query: str = "Analiza este gráfico o imagen. Incluye aspectos metodológicos, estadísticos si aplica.",
    force_model: Optional[str] = None,
) -> str:
    """
    Analiza una imagen usando GPT con visión.
    Usa gpt-4o por defecto ya que tiene mejor visión.
    
    Args:
        image_path: Ruta a la imagen
        system_prompt: Prompt del sistema
        query: Pregunta o instrucción sobre la imagen
        force_model: Fuerza un modelo específico (recomendado: gpt-4o)
    
    Returns:
        Análisis de la imagen
    """
    model = force_model or select_model(context="vision")
    
    try:
        with open(image_path, "rb") as image_file:
            image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")
        
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
            model=model,
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
            max_tokens=3000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analizando imagen: {str(e)}"


def extract_text_from_pdf_with_sanal(
    pdf_text: str,
    system_prompt: str,
    custom_query: Optional[str] = None,
    complexity: float = 0.7,
    force_model: Optional[str] = None
) -> str:
    """
    Analiza el contenido de un PDF usando el mejor modelo según complejidad.
    
    Args:
        pdf_text: Contenido extraído del PDF
        system_prompt: Prompt del sistema
        custom_query: Pregunta específica del usuario
        complexity: Nivel de complejidad del análisis (0.0-1.0)
        force_model: Fuerza un modelo específico
    
    Returns:
        Análisis del PDF
    """
    model = select_model(context="analysis", complexity=complexity, force_model=force_model)
    
    try:
        query = custom_query or "Analiza este trabajo académico. Incluye: errores APA 7, fortalezas metodológicas, debilidades, sugerencias de mejora. Proporciona una nota 0-10 REAL basada en criterios UOC."
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Aquí está el contenido del PDF:\n\n{pdf_text}\n\n{query}"
                }
            ],
            temperature=0.7,
            max_tokens=3000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analizando PDF: {str(e)}"


# === Generación en 3 Fases (obligatoria) ===

def _language_instruction(language_hint: Optional[str]) -> str:
    if language_hint:
        lang_map = {"ca": "català", "es": "castellano", "en": "inglés"}
        return f"Idioma obligatorio: {lang_map.get(language_hint, language_hint)}."
    return "Responde en el idioma del estudiante."


def phase0_analyze_assignment(topic: str, requirements: str, attachments: List[Dict]) -> str:
    """
    FASE 0 (NUEVA): Analiza qué pide la consigna Y detecta el patrón humano del estudiante.
    - Detecta el tipo de trabajo (teórico, reflexivo, investigación, etc.)
    - Identifica las restricciones de los PDFs
    - Determina qué se PUEDE hacer y qué NO
    - CLAVE: Analiza el trabajo humano como referencia de ESTILO y PROFUNDIDAD
    """
    model = "gpt-4o-mini"
    att_summary = build_attachments_summary(attachments, max_tokens=2500)
    
    user_prompt = f"""
ANÁLISIS DE CONSIGNA Y PATRÓN HUMANO - FASE 0

TEMA SOLICITADO:
{topic}

REQUISITOS:
{requirements}

ADJUNTOS DEL ESTUDIANTE (análisis crítico):
{att_summary}

INSTRUCCIÓN CRÍTICA:
Tu rol es PROTEGER al estudiante de generar un trabajo que:
1) No responda a la consigna real
2) Sea artificialmente perfecto (no parezca humano)
3) Incluya elementos que un estudiante real no escribiría

ANÁLISIS OBLIGATORIO:

1) TIPO Y PROPÓSITO DE TRABAJO
   - ¿Es teórico, reflexivo, crítico, empírico, análisis de casos, investigación?
   - ¿Qué estructura y profundidad es NATURAL para estos PDFs?
   - ¿Qué nivel de formalidad espera la asignatura?

2) CONTENIDO DE LOS PDFS
   - ¿Hay datos reales? ¿Hay metodología descrita? ¿Hay literatura?
   - ¿Qué autoridades, conceptos y enfoques aparecen?
   - ¿Cuál es la extensión y detalle típico?

3) PATRÓN HUMANO DE REFERENCIA (MUY IMPORTANTE)
   - Si hay trabajo del estudiante: ¿cómo escribe? (formal, casual, reflexivo, técnico)
   - ¿Qué nivel de detalle usa? (breve, exhaustivo, selectivo)
   - ¿Qué tono mantiene? (seguro, dudoso, condicional, académico)
   - ¿Usa citas densas o referencias sueltas?
   - ¿Cómo estructura párrafos y argumentos?

4) RESTRICCIONES ESTRICTAS
   - ¿Puedo inventar metodologías? NO, excepto si hay base explícita.
   - ¿Puedo añadir datos estadísticos? NO si no hay datos reales en PDFs.
   - ¿Puedo usar marcos teóricos externos? NO, solo lo que está en PDFs.
   - ¿Puedo añadir un checklist final? NO, eso es artificial.
   - ¿Puedo hacer el trabajo "más perfecto"? NO, debe sonar a estudiante real.

5) PROHIBICIONES CLARAS DE ARTIFICIO
   - NO: checklists finales, listas de autoevaluación, secciones estándar innecesarias.
   - NO: cifras exactas sin justificación (evita 95.2%, 3.4, etc.).
   - NO: detalles metodológicos excesivos si la asignatura no los pide.
   - NO: tono de "projecte científic idealitzat" o investigación de laboratorio.
   - SÍ: prudencia, matices, límites reales y naturales.

6) CLAVE PARA CREDIBILIDAD
   - ¿Qué aspectos NO se abordan? Decláralo naturalmente.
   - ¿Qué decisiones se tomaron por falta de datos o tiempo? Menciónalo sin dramatizar.
   - ¿Qué alternativas metodológicas existían? Justifica la elegida sin ser exhaustivo.
   
Devuelve tu análisis en formato claro, punto por punto:
- Tipo de trabajo exacto que se pide
- Qué está explícito en los PDFs
- Cómo escribe el estudiante (si hay referencia)
- Prohibiciones CLARAS (qué NO inventar)
- Instrucciones de credibilidad (cómo sonar a estudiante real)
"""
    
    messages = [
        {"role": "system", "content": DR_SANAL_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    planned = estimate_message_tokens(messages) + 1500
    rate_limiter.allow(planned)
    
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.5,
        max_tokens=1500,
    )
    analysis = resp.choices[0].message.content
    return sanitize_meta_discourse(analysis)


def phase1_analyze_and_outline(topic: str, requirements: str, attachments: List[Dict], language_hint: Optional[str], assignment_analysis: str) -> str:
    """Fase 1: esquema que RESPETA la consigna y el patrón humano. PROHIBIDO redactar."""
    model = "gpt-4o-mini"
    att_summary = build_attachments_summary(attachments, max_tokens=1800)
    user_prompt = f"""
CONSIGNA ANALIZADA (Fase 0):
{assignment_analysis}

TEMA:
{topic}

REQUISITOS:
{requirements}

ADJUNTOS:
{att_summary}

INSTRUCCIÓN CRÍTICA PARA ESQUEMA:
- Elabora un ESQUEMA DETALLADO que RESPONDA a la consigna real, no a un ideal de investigación.
- RESPETA estrictamente las restricciones identificadas en Fase 0:
  - NO inventes metodologías, datos ni marcos teóricos ajenos a los PDFs.
  - NO incluyas secciones estándar (Método/Resultados/Discusión) a menos que se pidan explícitamente.
- ADOPTA el patrón humano de referencia:
  - Nivel de formalidad: el mismo que el estudiante usa
  - Estructura: similar a la del trabajo de referencia
  - Profundidad: ni exhaustiva ni superficial, proporcional a la consigna
- Estructura natural: sigue el tipo de trabajo que piden los PDFs.
- Inclúye DÓNDE Y CÓMO vas a introducir renuncias reales y naturales (no decorativas).
- PROHIBIDO redactar el texto final; solo esquema y decisiones.
- {_language_instruction(language_hint)}
"""
    messages = [
        {"role": "system", "content": DR_SANAL_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    planned = estimate_message_tokens(messages) + 1200
    rate_limiter.allow(planned)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.4,
        max_tokens=1200,
    )
    schema = resp.choices[0].message.content
    return sanitize_meta_discourse(schema)


def _section_instruction(section: str) -> str:
    base = {
        "Introducción": "Presenta el problema, contexto, objetivos y relevancia académica.",
        "Método": "Describe diseño, hipótesis, variables, muestra, instrumentos, procedimiento y análisis.",
        "Resultados": "Presenta hallazgos con honestidad; si no hay datos reales, expón resultados esperados y limitaciones.",
        "Discusión": "Interpreta resultados, compara con literatura y limita inferencias.",
        "Conclusiones": "Sintetiza aportes, implicaciones y futuras líneas de trabajo.",
    }
    return base.get(section, "Redacta la sección solicitada con rigor académico.")


def phase2_write_sections(schema: str, attachments: List[Dict], language_hint: Optional[str], assignment_analysis: str) -> Dict[str, str]:
    """Fase 2: redacción por sección, respetando consigna y patrón humano."""
    sections = ["Introducción", "Método", "Resultados", "Discusión", "Conclusiones"]
    model = "gpt-4o"
    att_summary = build_attachments_summary(attachments, max_tokens=2400)
    results: Dict[str, str] = {}
    for sec in sections:
        user_prompt = f"""
RESTRICCIONES Y PATRÓN (CRÍTICO):
{assignment_analysis}

ESQUEMA APROBADO (Fase 1):
{schema}

SECCIÓN A REDACTAR: {sec}
- {_section_instruction(sec)}
- Usa SOLO información de los adjuntos.
- NO inventes nada que no esté explícito en los PDFs.

CLAVE: ESCRIBE COMO ESTUDIANTE REAL
- Lenguaje prudente, condicional, matizado.
- Usa expresiones que marquen alcance: "aquest treball se centra en…", "no es pretén…"
- Introduce dudas razonadas cuando sea apropiado.
- EVITA perfección artificial: evita cifras exactas innecesarias, detalles metodológicos si no se piden.
- Mantén el MISMO NIVEL Y TONO que el patrón humano analizado en Fase 0.
- Inclúye renuncias naturales (no decorativas) donde corresponda.

Si no hay datos en los PDFs: usa análisis cualitativo o plantea escenarios EXPLÍCITAMENTE hipotéticos.

- {_language_instruction(language_hint)}
- No incluyas otras secciones.
"""
        messages = [
            {"role": "system", "content": DR_SANAL_SYSTEM_PROMPT},
            {"role": "user", "content": f"{att_summary}\n\n{user_prompt}"},
        ]
        planned = estimate_message_tokens(messages) + 3600
        rate_limiter.allow(planned)
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=3600,
        )
        text = resp.choices[0].message.content
        text = humanize_text_light(sanitize_meta_discourse(text))
        # Continuación automática si quedó cortado
        while looks_truncated(text):
            cont_prompt = f"""
Continúa EXACTAMENTE la sección {sec} desde donde se quedó.
No repitas contenido. Mantén el tono y estructura.
"""
            cont_messages = [
                {"role": "system", "content": DR_SANAL_SYSTEM_PROMPT},
                {"role": "user", "content": f"{att_summary}\n\n{cont_prompt}\n\nTEXTO ACTUAL:\n{text}"},
            ]
            planned2 = estimate_message_tokens(cont_messages) + 1800
            rate_limiter.allow(planned2)
            resp2 = client.chat.completions.create(
                model=model,
                messages=cont_messages,
                temperature=0.7,
                max_tokens=1800,
            )
            add = resp2.choices[0].message.content
            add = humanize_text_light(sanitize_meta_discourse(add))
            text = text + "\n" + add
        results[sec] = text
    return results


def phase3_coherence_pass(full_text: str, attachments: List[Dict], language_hint: Optional[str], assignment_analysis: str) -> str:
    """Fase 3: revisión ligera, SIN agregar elementos artificiales. Solo suavizar coherencia."""
    model = "gpt-4o-mini"
    att_summary = build_attachments_summary(attachments, max_tokens=1000)
    context_text = truncate_text_to_tokens(full_text, 6000)
    user_prompt = f"""
RESTRICCIONES FINALES (CRÍTICO):
{assignment_analysis}

Objetivo: revisión LIGERA de coherencia global y transiciones.
NO reescribas completamente. NO agregues elementos artificiales (checklists, listas de autoevaluación, etc.).
NO inventes nada; respeta lo que el estudiante proporcionó.

SOLO:
- Suaviza transiciones entre párrafos si es necesario.
- Corrígeme pequeños giros de redacción para mejorar fluidez (sin cambiar voz o nivel).
- Verifica consistencia de terminología.

PROHIBIDO:
- Agregar secciones nuevas.
- Inyectar detalles metodológicos.
- Hacer el trabajo "más perfecto" o "más académico".
- Cambiar el tono o nivel de formalidad del patrón original.

Devuelve el TEXTO MEJORADO directamente, sin comentarios.
- {_language_instruction(language_hint)}
"""
    messages = [
        {"role": "system", "content": DR_SANAL_SYSTEM_PROMPT},
        {"role": "user", "content": f"{att_summary}\n\n{user_prompt}\n\nTEXTO:\n{context_text}"},
    ]
    planned = estimate_message_tokens(messages) + 1000
    rate_limiter.allow(planned)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        max_tokens=1000,
    )
    improved = resp.choices[0].message.content
    return humanize_text_light(sanitize_meta_discourse(improved))


def generate_academic_work_phased(
    topic: str,
    requirements: str,
    attachments: List[Dict],
    language_hint: Optional[str] = None,
) -> str:
    """Orquesta las 4 fases: análisis de consigna + esquema + secciones + coherencia."""
    try:
        # FASE 0: Análisis de consigna
        assignment_analysis = phase0_analyze_assignment(topic, requirements, attachments)
        
        # FASE 1: Esquema respetando consigna
        schema = phase1_analyze_and_outline(topic, requirements, attachments, language_hint, assignment_analysis)
        
        # FASE 2: Redacción de secciones
        section_texts = phase2_write_sections(schema, attachments, language_hint, assignment_analysis)
        
        # Montar documento
        final_parts = []
        for sec in ["Introducción", "Método", "Resultados", "Discusión", "Conclusiones"]:
            if sec in section_texts:
                final_parts.append(f"## {sec}\n\n{section_texts[sec].strip()}\n")
        assembled = "\n".join(final_parts).strip()
        
        # FASE 3: Coherencia
        final_text = phase3_coherence_pass(assembled, attachments, language_hint, assignment_analysis)
        return final_text
    except Exception as e:
        return f"Error en generación por fases: {str(e)}"


# Compatibilidad: redirige a la generación por fases (sin adjuntos explícitos)

def generate_academic_work(
    topic: str,
    requirements: str,
    language_hint: Optional[str] = None,
    word_count: Optional[int] = None,
    temperature: float = 0.8,
    complexity: float = 0.8,
    force_model: Optional[str] = None,
) -> str:
    return generate_academic_work_phased(topic, requirements, attachments=[], language_hint=language_hint)



