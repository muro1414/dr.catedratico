#!/bin/bash
# Script de inicio para macOS/Linux

echo ""
echo "========================================"
echo "Dr. Sanal - Psychology Professor AI"
echo "UOC Application Launcher"
echo "========================================"
echo ""

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 no está instalado"
    echo "Descarga desde: https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python detectado: $(python3 --version)"

# Verificar si venv existe
if [ ! -d "venv" ]; then
    echo ""
    echo "Creando entorno virtual..."
    python3 -m venv venv
    echo "✓ Entorno virtual creado"
fi

# Activar venv
echo ""
echo "Activando entorno virtual..."
source venv/bin/activate
echo "✓ Entorno virtual activado"

# Instalar/Actualizar dependencias
echo ""
echo "Verificando dependencias..."
pip install -q -r requirements.txt
echo "✓ Dependencias listas"

# Verificar .env
echo ""
if [ ! -f ".env" ]; then
    echo "ADVERTENCIA: Archivo .env no encontrado"
    echo "Creando .env desde .env.example..."
    cp .env.example .env
    echo ""
    echo "Por favor, edita el archivo .env y agrega tu OPENAI_API_KEY"
    echo ""
    read -p "Presiona Enter para continuar..."
fi

# Ejecutar pruebas
echo ""
echo "Ejecutando verificación de configuración..."
python test_setup.py
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: La verificación falló. Revisa los errores anteriores."
    exit 1
fi

# Iniciar aplicación
echo ""
echo "========================================"
echo "Iniciando Dr. Sanal..."
echo "========================================"
echo ""
echo "La aplicación se abrirá en: http://localhost:8501"
echo ""
echo "Para detener: Presiona CTRL+C"
echo ""

streamlit run main.py
