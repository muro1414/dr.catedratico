"""
Procesamiento de archivos: PDF, Excel/CSV, imágenes y textos.
"""

import base64
import os
import tempfile
from typing import Dict, List, Optional, Tuple

import pandas as pd
from PIL import Image
from pypdf import PdfReader
from docx import Document


PREVIEW_CHAR_LIMIT = 5000  # evitamos prompts gigantes


def process_pdf(pdf_file) -> str:
    """
    Extrae texto de un PDF.
    
    Args:
        pdf_file: Objeto de archivo PDF desde Streamlit
    
    Returns:
        Texto extraído del PDF
    """
    try:
        # Guardar temporalmente el archivo
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_file.read())
            tmp_path = tmp.name
        
        # Leer PDF
        reader = PdfReader(tmp_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        # Limpiar
        os.unlink(tmp_path)
        
        return text if text.strip() else "El PDF no contiene texto extractable."
    except Exception as e:
        return f"Error procesando PDF: {str(e)}"


def process_docx(docx_file) -> str:
    """
    Extrae texto de un DOCX.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(docx_file.read())
            tmp_path = tmp.name

        document = Document(tmp_path)
        paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
        os.unlink(tmp_path)
        text = "\n".join(paragraphs)
        return text if text.strip() else "El DOCX no contiene texto legible."
    except Exception as e:
        return f"Error procesando DOCX: {str(e)}"


def process_text(text_file) -> str:
    """
    Lee archivos de texto plano o markdown.
    """
    try:
        content = text_file.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")
        return content
    except Exception as e:
        return f"Error procesando texto: {str(e)}"


def process_excel_csv(file) -> Tuple[pd.DataFrame, str]:
    """
    Lee un archivo Excel o CSV.
    
    Args:
        file: Objeto de archivo desde Streamlit
    
    Returns:
        Tuple (DataFrame, descripción)
    """
    try:
        filename = file.name.lower()
        
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(file)
        elif filename.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            return None, "Formato no soportado. Use .xlsx, .xls o .csv"
        
        # Información básica
        info = f"""
        Datos cargados exitosamente.
        - Dimensiones: {df.shape[0]} filas × {df.shape[1]} columnas
        - Columnas: {', '.join(df.columns.tolist())}
        - Tipos de datos: {df.dtypes.to_dict()}
        
        Primeras filas:
        {df.head().to_string()}
        """

        return df, info
    except Exception as e:
        return None, f"Error procesando archivo: {str(e)}"


def process_image(image_file) -> Tuple[Optional[str], str]:
    """
    Procesa una imagen JPG/PNG.
    
    Args:
        image_file: Objeto de archivo imagen desde Streamlit
    
    Returns:
        Tuple (ruta temporal, descripción)
    """
    try:
        # Guardar temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_file.read())
            tmp_path = tmp.name

        # Validar que es imagen
        img = Image.open(tmp_path)
        info = f"Imagen cargada: {img.format} {img.size[0]}×{img.size[1]} px"

        return tmp_path, info
    except Exception as e:
        return None, f"Error procesando imagen: {str(e)}"


def get_dataframe_info(df: pd.DataFrame) -> dict:
    """
    Obtiene información estadística básica del DataFrame.
    
    Args:
        df: DataFrame a analizar
    
    Returns:
        Diccionario con información
    """
    return {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.to_dict(),
        "missing": df.isnull().sum().to_dict(),
        "describe": df.describe().to_dict(),
        "correlation": df.corr(numeric_only=True).to_dict() if len(df.select_dtypes(include=['number']).columns) > 1 else {}
    }


def _truncate(text: str, limit: int = PREVIEW_CHAR_LIMIT) -> str:
    return text if len(text) <= limit else text[:limit] + "\n...[truncado]"


def _encode_image_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def prepare_context_from_files(files: List) -> List[Dict]:
    """
    Procesa múltiples archivos subidos y devuelve una lista de contextos homogéneos
    para alimentar al modelo.
    """
    contexts = []
    for file in files:
        name = getattr(file, "name", "archivo_sin_nombre")
        lower = name.lower()
        ctx: Dict = {"name": name}

        try:
            if lower.endswith(".pdf"):
                text = process_pdf(file)
                ctx.update({
                    "kind": "pdf",
                    "summary": _truncate(text),
                    "content": _truncate(text)
                })
            elif lower.endswith((".docx")):
                text = process_docx(file)
                ctx.update({
                    "kind": "docx",
                    "summary": _truncate(text),
                    "content": _truncate(text)
                })
            elif lower.endswith((".txt", ".md")):
                text = process_text(file)
                ctx.update({
                    "kind": "text",
                    "summary": _truncate(text),
                    "content": _truncate(text)
                })
            elif lower.endswith((".csv", ".xlsx", ".xls")):
                df, info = process_excel_csv(file)
                preview = info if info else "No se pudo generar preview"
                ctx.update({
                    "kind": "data",
                    "summary": _truncate(preview),
                    "dataframe_info": preview,
                })
            elif lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
                path, info = process_image(file)
                b64 = _encode_image_base64(path) if path else None
                if path and os.path.exists(path):  # limpiar temporal
                    os.unlink(path)
                ctx.update({
                    "kind": "image",
                    "summary": info,
                    "base64": b64,
                })
            else:
                ctx.update({
                    "kind": "unknown",
                    "summary": "Formato no soportado aún. Adjunta PDF, DOCX, TXT, CSV/XLSX, JPG/PNG.",
                })
        except Exception as e:  # protegemos la sesión si un archivo falla
            ctx.update({
                "kind": "error",
                "summary": f"Error procesando {name}: {str(e)}"
            })

        contexts.append(ctx)

    return contexts
