@echo off
REM Script de inicio para Windows

echo.
echo ========================================
echo Dr. Sanal - Psychology Professor AI
echo UOC Application Launcher
echo ========================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no está instalado o no está en PATH
    echo Descarga Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✓ Python detectado

REM Verificar si venv existe
if not exist "venv" (
    echo.
    echo Creando entorno virtual...
    python -m venv venv
    echo ✓ Entorno virtual creado
)

REM Activar venv
echo.
echo Activando entorno virtual...
call venv\Scripts\activate.bat
echo ✓ Entorno virtual activado

REM Instalar/Actualizar dependencias
echo.
echo Verificando dependencias...
pip install -q -r requirements.txt
echo ✓ Dependencias listas

REM Verificar .env
echo.
if not exist ".env" (
    echo ADVERTENCIA: Archivo .env no encontrado
    echo Creando .env desde .env.example...
    copy .env.example .env
    echo.
    echo Por favor, edita el archivo .env y agrega tu OPENAI_API_KEY
    echo.
    pause
)

REM Ejecutar pruebas
echo.
echo Ejecutando verificación de configuración...
python test_setup.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: La verificación falló. Revisa los errores anteriores.
    pause
    exit /b 1
)

REM Iniciar aplicación
echo.
echo ========================================
echo Iniciando Dr. Sanal...
echo ========================================
echo.
echo La aplicación se abrirá en: http://localhost:8501
echo.
echo Para detener: Presiona CTRL+C
echo.

streamlit run main.py

pause
