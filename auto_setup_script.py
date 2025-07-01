#!/usr/bin/env python3
"""
Script de instalación automática para Enhanced Data Tool
Resuelve automáticamente los problemas de dependencias y configuración
"""

import os
import sys
import subprocess
import platform
import requests
from pathlib import Path
import json
import time

class Colors:
    """Colores para terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(text, color=Colors.OKGREEN):
    """Imprime texto con color"""
    print(f"{color}{text}{Colors.ENDC}")

def print_step(step_num, description):
    """Imprime paso de instalación"""
    print_colored(f"\n📋 PASO {step_num}: {description}", Colors.HEADER)

def run_command(command, description="", check=True):
    """Ejecuta comando y maneja errores"""
    try:
        print_colored(f"🔄 Ejecutando: {description or command}", Colors.OKCYAN)
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print_colored(f"✅ {description or 'Comando'} completado", Colors.OKGREEN)
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print_colored(f"❌ Error en: {description or command}", Colors.FAIL)
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print_colored(f"❌ Excepción ejecutando comando: {e}", Colors.FAIL)
        return False

def check_python_version():
    """Verifica versión de Python"""
    print_step(1, "Verificando Python")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_colored("❌ Python 3.8+ requerido", Colors.FAIL)
        print_colored(f"   Versión actual: {version.major}.{version.minor}", Colors.WARNING)
        return False
    
    print_colored(f"✅ Python {version.major}.{version.minor}.{version.micro} OK", Colors.OKGREEN)
    return True

def setup_virtual_environment():
    """Configura entorno virtual"""
    print_step(2, "Configurando entorno virtual")
    
    venv_path = Path("venv_data_tool")
    
    if venv_path.exists():
        print_colored("⚠️  Entorno virtual ya existe", Colors.WARNING)
        response = input("¿Recrear entorno virtual? (y/N): ")
        if response.lower() == 'y':
            import shutil
            shutil.rmtree(venv_path)
        else:
            print_colored("✅ Usando entorno virtual existente", Colors.OKGREEN)
            return True
    
    # Crear entorno virtual
    if not run_command(f"python -m venv {venv_path}", "Creando entorno virtual"):
        return False
    
    # Activar entorno virtual
    if platform.system() == "Windows":
        activate_cmd = f"{venv_path}\\Scripts\\activate"
        pip_cmd = f"{venv_path}\\Scripts\\pip"
    else:
        activate_cmd = f"source {venv_path}/bin/activate"
        pip_cmd = f"{venv_path}/bin/pip"
    
    print_colored(f"📝 Para activar manualmente: {activate_cmd}", Colors.OKCYAN)
    return True

def install_basic_dependencies():
    """Instala dependencias básicas"""
    print_step(3, "Instalando dependencias básicas")
    
    # Determinar pip path
    if platform.system() == "Windows":
        pip_cmd = "venv_data_tool\\Scripts\\pip"
    else:
        pip_cmd = "venv_data_tool/bin/pip"
    
    basic_packages = [
        "pandas>=1.5.0",
        "numpy>=1.20.0", 
        "requests>=2.25.0",
        "python-dotenv>=0.19.0",
        "tqdm>=4.64.0",
        "colorama>=0.4.4",
        "tabulate>=0.9.0"
    ]
    
    # Upgrade pip first
    run_command(f"{pip_cmd} install --upgrade pip", "Actualizando pip")
    
    for package in basic_packages:
        if not run_command(f"{pip_cmd} install {package}", f"Instalando {package.split('>=')[0]}"):
            print_colored(f"⚠️  Error instalando {package}, continuando...", Colors.WARNING)
    
    return True

def install_optional_dependencies():
    """Instala dependencias opcionales"""
    print_step(4, "Instalando dependencias opcionales")
    
    if platform.system() == "Windows":
        pip_cmd = "venv_data_tool\\Scripts\\pip"
    else:
        pip_cmd = "venv_data_tool/bin/pip"
    
    # Preguntar por embeddings
    print_colored("🤖 ¿Instalar dependencias para detección con embeddings? (recomendado)", Colors.OKCYAN)
    print("   Esto instalará sentence-transformers, scikit-learn y torch (~2GB)")
    response = input("   Instalar embeddings? (Y/n): ")
    
    if response.lower() != 'n':
        embedding_packages = [
            "sentence-transformers>=2.2.0",
            "scikit-learn>=1.1.0"
        ]
        
        for package in embedding_packages:
            print_colored(f"📦 Instalando {package.split('>=')[0]}...", Colors.OKCYAN)
            if not run_command(f"{pip_cmd} install {package}", f"Instalando {package}", check=False):
                print_colored(f"⚠️  Error con {package}, se puede instalar manualmente después", Colors.WARNING)
    
    # Preguntar por bases de datos adicionales
    print_colored("\n🗄️  ¿Instalar soporte para PostgreSQL/MySQL?", Colors.OKCYAN)
    response = input("   Instalar drivers de BD adicionales? (y/N): ")
    
    if response.lower() == 'y':
        db_packages = ["psycopg2-binary>=2.9.0", "pymysql>=1.0.0"]
        for package in db_packages:
            run_command(f"{pip_cmd} install {package}", f"Instalando {package}", check=False)
    
    return True

def setup_ollama():
    """Configura Ollama para verificación LLM"""
    print_step(5, "Configurando Ollama (LLM local)")
    
    print_colored("🤖 Ollama permite verificar relaciones usando IA local", Colors.OKCYAN)
    response = input("¿Instalar y configurar Ollama? (Y/n): ")
    
    if response.lower() == 'n':
        print_colored("⏭️  Saltando instalación de Ollama", Colors.WARNING)
        return True
    
    # Verificar si Ollama ya está instalado
    if run_command("ollama --version", "Verificando Ollama", check=False):
        print_colored("✅ Ollama ya está instalado", Colors.OKGREEN)
    else:
        print_colored("📥 Descargando Ollama...", Colors.OKCYAN)
        
        system = platform.system().lower()
        if system == "darwin":  # macOS
            print_colored("🍎 Instalando en macOS...", Colors.OKCYAN)
            run_command("curl -fsSL https://ollama.ai/install.sh | sh", "Instalando Ollama")
        elif system == "linux":
            print_colored("🐧 Instalando en Linux...", Colors.OKCYAN)
            run_command("curl -fsSL https://ollama.ai/install.sh | sh", "Instalando Ollama")
        elif system == "windows":
            print_colored("🪟 Para Windows, descarga desde: https://ollama.ai/download", Colors.WARNING)
            print_colored("   Ejecuta el instalador y luego continúa", Colors.WARNING)
            input("   Presiona Enter cuando hayas instalado Ollama...")
        
    # Verificar instalación
    if not run_command("ollama --version", "Verificando instalación de Ollama", check=False):
        print_colored("❌ Ollama no se instaló correctamente", Colors.FAIL)
        return False
    
    # Iniciar servidor Ollama
    print_colored("🚀 Iniciando servidor Ollama...", Colors.OKCYAN)
    
    # Intentar iniciar en background
    if system == "windows":
        subprocess.Popen("ollama serve", shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        subprocess.Popen("ollama serve", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(3)  # Esperar a que inicie
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print_colored("✅ Servidor Ollama iniciado correctamente", Colors.OKGREEN)
        else:
            raise Exception("Servidor no responde")
    except Exception:
        print_colored("⚠️  Servidor Ollama no responde, inicia manualmente: ollama serve", Colors.WARNING)
    
    # Descargar modelo
    print_colored("📦 Descargando modelo LLM...", Colors.OKCYAN)
    print("   Opciones disponibles:")
    print("   1. llama3.2:1b (1GB) - Rápido, menos preciso")
    print("   2. llama3.2:3b (2GB) - Balanceado (RECOMENDADO)")
    print("   3. llama2:latest (3.8GB) - Más preciso")
    
    choice = input("   Elige modelo (1-3, default=2): ").strip()
    
    models = {
        "1": "llama3.2:1b",
        "2": "llama3.2:3b", 
        "3": "llama2:latest"
    }
    
    model = models.get(choice, "llama3.2:3b")
    
    print_colored(f"📥 Descargando modelo {model}...", Colors.OKCYAN)
    if run_command(f"ollama pull {model}", f"Descargando {model}", check=False):
        print_colored(f"✅ Modelo {model} instalado correctamente", Colors.OKGREEN)
    else:
        print_colored("⚠️  Error descargando modelo, se puede hacer manualmente después", Colors.WARNING)
    
    return True

def create_sample_files():
    """Crea archivos de ejemplo y configuración"""
    print_step(6, "Creando archivos de configuración")
    
    # Crear directorio de output
    Path("output").mkdir(exist_ok=True)
    
    # Crear archivo de configuración
    config = {
        "database": {
            "default_type": "sqlite",
            "sample_db": "example_store.db"
        },
        "analysis": {
            "use_embeddings": True,
            "use_llm": True,
            "max_llm_verifications": 5,
            "confidence_threshold": 30
        },
        "output": {
            "directory": "./output",
            "generate_json": True,
            "generate_dbml": True
        },
        "ollama": {
            "url": "http://localhost:11434",
            "model": "llama3.2:3b",
            "timeout": 30
        }
    }
    
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print_colored("✅ Archivo config.json creado", Colors.OKGREEN)
    
    # Crear script de ejemplo
    example_script = '''#!/usr/bin/env python3
"""
Ejemplo de uso de Enhanced Data Tool
"""

from complete_data_tool import CompleteDataTool, create_sample_database
import os

def main():
    print("🚀 Enhanced Data Tool - Ejemplo de Uso")
    print("=" * 50)
    
    # Crear BD de ejemplo si no existe
    db_file = "example_store.db"
    if not os.path.exists(db_file):
        create_sample_database(db_file)
    
    # Analizar con diferentes configuraciones
    configurations = [
        ("Análisis Básico", False, False),
        ("Con Embeddings", True, False),
        ("Completo (Embeddings + LLM)", True, True)
    ]
    
    for name, use_embeddings, use_llm in configurations:
        print(f"\\n🔍 {name}")
        print("-" * 30)
        
        try:
            tool = CompleteDataTool(
                db_path=db_file,
                use_embeddings=use_embeddings,
                use_llm=use_llm
            )
            
            results = tool.analyze_complete(
                output_dir=f"./output/{name.lower().replace(' ', '_')}"
            )
            
            print(f"✅ {name} completado")
            
        except Exception as e:
            print(f"❌ Error en {name}: {e}")
            continue

if __name__ == "__main__":
    main()
'''
    
    with open("example_usage.py", "w", encoding="utf-8") as f:
        f.write(example_script)
    
    print_colored("✅ Archivo example_usage.py creado", Colors.OKGREEN)
    
    return True

def run_tests():
    """Ejecuta tests básicos para verificar instalación"""
    print_step(7, "Ejecutando tests de verificación")
    
    if platform.system() == "Windows":
        python_cmd = "venv_data_tool\\Scripts\\python"
    else:
        python_cmd = "venv_data_tool/bin/python"
    
    # Test 1: Importar pandas
    test_code = """
import pandas as pd
import numpy as np
print("✅ Pandas y NumPy OK")
"""
    
    if not run_command(f'{python_cmd} -c "{test_code}"', "Test básico de pandas/numpy"):
        return False
    
    # Test 2: Probar embeddings si están instalados
    embedding_test = """
try:
    from sentence_transformers import SentenceTransformer
    print("✅ Sentence Transformers OK")
except ImportError:
    print("⚠️  Sentence Transformers no disponible")
"""
    
    run_command(f'{python_cmd} -c "{embedding_test}"', "Test de embeddings", check=False)
    
    # Test 3: Probar conexión a Ollama
    ollama_test = """
import requests
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=2)
    if response.status_code == 200:
        models = response.json().get('models', [])
        print(f"✅ Ollama OK - {len(models)} modelo(s) disponible(s)")
    else:
        print("⚠️  Ollama servidor no responde")
except:
    print("⚠️  Ollama no disponible")
"""
    
    run_command(f'{python_cmd} -c "{ollama_test}"', "Test de Ollama", check=False)
    
    return True

def create_run_scripts():
    """Crea scripts de ejecución convenientes"""
    print_step(8, "Creando scripts de ejecución")
    
    # Script para Windows
    windows_script = '''@echo off
echo 🚀 Enhanced Data Tool
echo.

cd /d "%~dp0"

REM Activar entorno virtual
call venv_data_tool\\Scripts\\activate

REM Ejecutar herramienta
python complete_data_tool.py

pause
'''
    
    with open("run_tool.bat", "w") as f:
        f.write(windows_script)
    
    # Script para Linux/Mac
    unix_script = '''#!/bin/bash
echo "🚀 Enhanced Data Tool"
echo

# Cambiar al directorio del script
cd "$(dirname "$0")"

# Activar entorno virtual
source venv_data_tool/bin/activate

# Ejecutar herramienta
python complete_data_tool.py

echo
echo "Presiona Enter para salir..."
read
'''
    
    with open("run_tool.sh", "w") as f:
        f.write(unix_script)
    
    # Hacer ejecutable en Unix
    if platform.system() != "Windows":
        os.chmod("run_tool.sh", 0o755)
    
    print_colored("✅ Scripts de ejecución creados:", Colors.OKGREEN)
    print_colored("   Windows: run_tool.bat", Colors.OKCYAN)
    print_colored("   Linux/Mac: ./run_tool.sh", Colors.OKCYAN)
    
    return True

def print_final_instructions():
    """Imprime instrucciones finales"""
    print_colored("\n🎉 ¡INSTALACIÓN COMPLETADA!", Colors.HEADER)
    print_colored("=" * 50, Colors.HEADER)
    
    print_colored("\n📋 CÓMO USAR LA HERRAMIENTA:", Colors.OKBLUE)
    
    print_colored("\n1️⃣  Ejecución rápida:", Colors.OKCYAN)
    if platform.system() == "Windows":
        print("   • Doble click en: run_tool.bat")
    else:
        print("   • Ejecutar: ./run_tool.sh")
    
    print_colored("\n2️⃣  Ejecución manual:", Colors.OKCYAN)
    if platform.system() == "Windows":
        print("   • venv_data_tool\\Scripts\\activate")
    else:
        print("   • source venv_data_tool/bin/activate")
    print("   • python complete_data_tool.py")
    
    print_colored("\n3️⃣  Usando desde código:", Colors.OKCYAN)
    print("   • python example_usage.py")
    
    print_colored("\n📁 ARCHIVOS CREADOS:", Colors.OKBLUE)
    files = [
        "venv_data_tool/         # Entorno virtual",
        "config.json            # Configuración",
        "example_usage.py       # Ejemplo de uso",
        "output/                # Directorio de resultados",
        "run_tool.bat/sh        # Scripts de ejecución"
    ]
    
    for file in files:
        print(f"   • {file}")
    
    print_colored("\n🔧 CONFIGURACIÓN OPCIONAL:", Colors.OKBLUE)
    print("   • Edita config.json para ajustar configuraciones")
    print("   • Para PostgreSQL/MySQL: instala drivers adicionales")
    print("   • Para mejores embeddings: considera modelos más grandes")
    
    print_colored("\n⚠️  SOLUCIÓN DE PROBLEMAS:", Colors.WARNING)
    print("   • Si Ollama no funciona: ollama serve")
    print("   • Si faltan embeddings: pip install sentence-transformers")
    print("   • Si hay errores de serialización: usa use_llm=False")
    
    print_colored("\n✨ ¡LISTO PARA USAR!", Colors.OKGREEN)

def main():
    """Función principal de instalación"""
    print_colored("🚀 ENHANCED DATA TOOL - INSTALADOR AUTOMÁTICO", Colors.HEADER)
    print_colored("=" * 60, Colors.HEADER)
    print_colored("Este script instalará y configurará automáticamente todas las dependencias", Colors.OKCYAN)
    
    # Verificar sistema
    print_colored(f"\n💻 Sistema: {platform.system()} {platform.release()}", Colors.OKCYAN)
    
    steps = [
        check_python_version,
        setup_virtual_environment,
        install_basic_dependencies,
        install_optional_dependencies,
        setup_ollama,
        create_sample_files,
        run_tests,
        create_run_scripts
    ]
    
    failed_steps = []
    
    for i, step in enumerate(steps, 1):
        try:
            if not step():
                failed_steps.append(f"Paso {i}: {step.__name__}")
        except Exception as e:
            print_colored(f"❌ Error en paso {i}: {e}", Colors.FAIL)
            failed_steps.append(f"Paso {i}: {step.__name__} - {e}")
    
    # Resumen final
    if failed_steps:
        print_colored(f"\n⚠️  INSTALACIÓN COMPLETADA CON ADVERTENCIAS", Colors.WARNING)
        print_colored("Pasos con problemas:", Colors.WARNING)
        for step in failed_steps:
            print(f"   • {step}")
        print_colored("\nLa herramienta debería funcionar con funcionalidad básica", Colors.OKCYAN)
    else:
        print_colored(f"\n✅ INSTALACIÓN COMPLETADA EXITOSAMENTE", Colors.OKGREEN)
    
    print_final_instructions()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\n❌ Instalación cancelada por el usuario", Colors.FAIL)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n\n❌ Error inesperado: {e}", Colors.FAIL)
        sys.exit(1)