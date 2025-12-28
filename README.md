# Dr. Sanal - Psychology Professor AI

System prompt y configuraciones para el Dr. Sanal, catedrático de psicología de la UOC.

## Instalación

1. Clonar el repositorio
2. Crear archivo `.env` con tu API key de OpenAI:
   ```
   OPENAI_API_KEY=tu_clave_aqui
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución

```bash
streamlit run main.py
```

## Características

- Chat interactivo con un profesor de psicología exigente
- Análisis de datos estadísticos (Excel/CSV)
- Lectura y análisis de PDFs (trabajos académicos)
- Análisis de imágenes (gráficos, diagramas)
- Generación de trabajos académicos con formato APA 7
- Integración con GPT-4o para razonamiento avanzado

## Estructura

- `main.py`: Aplicación principal de Streamlit
- `openai_handler.py`: Manejo de la API de OpenAI
- `file_processor.py`: Procesamiento de archivos
- `statistical_analyzer.py`: Análisis estadístico
- `prompts.py`: Definición del system prompt maestro del Dr. Sanal
