#!/usr/bin/env python3
"""
Analizador Principal de Relaciones en Base de Datos
Combina detección inteligente + validación con AI
"""

import pandas as pd
import os
from typing import Dict
from smart_detector import SmartRelationshipDetector, detect_relationships
from ai_validator import AIRelationshipValidator, analyze_database_with_ai

def load_sample_data() -> Dict[str, pd.DataFrame]:
    """Carga datos de ejemplo o tus propios CSVs"""
    tables = {}
    
    # Opción 1: Cargar desde archivos CSV
    csv_files = {
        'patients': 'patients.csv',
        'appointments': 'appointments.csv',
        'medications': 'medications.csv',
        'pets': 'pets.csv',
        'doctors': 'doctors.csv'
    }
    
    for table_name, file_path in csv_files.items():
        if os.path.exists(file_path):
            print(f"📁 Cargando {table_name} desde {file_path}")
            tables[table_name] = pd.read_csv(file_path)
        else:
            print(f"⚠️  Archivo {file_path} no encontrado")
    
    # Opción 2: Crear datos de ejemplo si no hay archivos
    if not tables:
        print("\n📝 Creando datos de ejemplo...")
        
        # Patients
        tables['patients'] = pd.DataFrame({
            'patient_id': [1, 2, 3, 4, 5],
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Davis'],
            'age': [30, 25, 45, 35, 28],
            'email': ['john@email.com', 'jane@email.com', 'bob@email.com', 'alice@email.com', 'charlie@email.com']
        })
        
        # Pets (para clínica veterinaria)
        tables['pets'] = pd.DataFrame({
            'pet_id': [101, 102, 103, 104],
            'patient_id': [1, 1, 2, 3],  # Referencias a patients
            'name': ['Fluffy', 'Max', 'Luna', 'Rocky'],
            'species': ['Cat', 'Dog', 'Cat', 'Dog'],
            'breed': ['Persian', 'Labrador', 'Siamese', 'Bulldog']
        })
        
        # Appointments
        tables['appointments'] = pd.DataFrame({
            'appointment_id': [1001, 1002, 1003, 1004, 1005],
            'patient_id': [1, 2, 1, 3, 4],  # Referencias a patients
            'pet_id': [101, 103, 102, 104, None],  # Referencias a pets
            'date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19'],
            'reason': ['Checkup', 'Vaccination', 'Surgery', 'Checkup', 'Consultation']
        })
        
        # Medications
        tables['medications'] = pd.DataFrame({
            'medication_id': [2001, 2002, 2003, 2004],
            'name': ['Antibiotics', 'Pain Relief', 'Vaccine A', 'Vitamin D'],
            'type': ['Antibiotic', 'Analgesic', 'Vaccine', 'Supplement']
        })
        
        # Prescriptions (tabla de unión)
        tables['prescriptions'] = pd.DataFrame({
            'prescription_id': [3001, 3002, 3003, 3004, 3005],
            'appointment_id': [1001, 1001, 1002, 1003, 1004],  # Referencias a appointments
            'medication_id': [2001, 2002, 2003, 2002, 2004],  # Referencias a medications
            'dosage': ['2 pills/day', '1 pill/8h', '1 dose', '2 pills/day', '1 pill/day']
        })
    
    return tables

def main():
    """Función principal"""
    print("🔍 ANALIZADOR INTELIGENTE DE RELACIONES EN BD")
    print("=" * 60)
    
    # Cargar datos
    tables = load_sample_data()
    
    if not tables:
        print("❌ No se pudieron cargar datos. Verifica tus archivos CSV.")
        return
    
    print(f"\n✅ Se cargaron {len(tables)} tablas:")
    for name, df in tables.items():
        print(f"   - {name}: {df.shape[0]} filas, {df.shape[1]} columnas")
    
    # Menú de opciones
    while True:
        print("\n📋 OPCIONES:")
        print("1. Detección rápida de relaciones (sin AI)")
        print("2. Análisis completo con validación AI")
        print("3. Análisis personalizado")
        print("4. Salir")
        
        choice = input("\nElige una opción (1-4): ").strip()
        
        if choice == '1':
            # Solo detección
            print("\n" + "="*60)
            candidates = detect_relationships(tables)
            
        elif choice == '2':
            # Análisis completo
            print("\n" + "="*60)
            
            # Verificar si Ollama está disponible
            try:
                import requests
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    models = [m['name'] for m in response.json().get('models', [])]
                    if models:
                        print(f"✅ Modelos disponibles en Ollama: {', '.join(models)}")
                        model = input(f"¿Qué modelo usar? (default: llama2:latest): ").strip()
                        if not model:
                            model = "llama2:latest"
                    else:
                        print("⚠️ No hay modelos instalados en Ollama")
                        print("Instala uno con: ollama pull llama2")
                        continue
                else:
                    raise Exception("Ollama no responde")
                    
            except Exception as e:
                print("❌ Ollama no está disponible. Asegúrate de que esté ejecutándose.")
                print("   Inicia Ollama con: ollama serve")
                continue
            
            # Ejecutar análisis
            top_n = input("¿Cuántas relaciones validar con AI? (default: 10): ").strip()
            top_n = int(top_n) if top_n.isdigit() else 10
            
            candidates, validations = analyze_database_with_ai(
                tables,
                top_n=top_n,
                ollama_model=model
            )
            
        elif choice == '3':
            # Análisis personalizado
            print("\n🔧 ANÁLISIS PERSONALIZADO")
            
            # Mostrar tablas disponibles
            print("\nTablas disponibles:")
            for i, name in enumerate(tables.keys(), 1):
                print(f"{i}. {name}")
            
            # Seleccionar tabla origen
            source_idx = input("\nSelecciona tabla origen (número): ").strip()
            if not source_idx.isdigit() or int(source_idx) < 1 or int(source_idx) > len(tables):
                print("❌ Selección inválida")
                continue
            
            source_table = list(tables.keys())[int(source_idx) - 1]
            
            # Mostrar columnas
            print(f"\nColumnas de {source_table}:")
            columns = list(tables[source_table].columns)
            for i, col in enumerate(columns, 1):
                print(f"{i}. {col}")
            
            # Seleccionar columna
            col_idx = input("\nSelecciona columna (número): ").strip()
            if not col_idx.isdigit() or int(col_idx) < 1 or int(col_idx) > len(columns):
                print("❌ Selección inválida")
                continue
            
            source_column = columns[int(col_idx) - 1]
            
            # Buscar relaciones para esa columna específica
            detector = SmartRelationshipDetector(tables)
            detector.analyze_columns()
            
            print(f"\n🔍 Buscando relaciones para {source_table}.{source_column}...")
            
            # Filtrar candidatos
            all_candidates = detector.find_relationships()
            filtered = [c for c in all_candidates 
                       if c.source_table == source_table and c.source_column == source_column]
            
            if filtered:
                detector.print_results(filtered, top_n=10)
            else:
                print("No se encontraron relaciones potenciales.")
            
        elif choice == '4':
            print("\n👋 ¡Hasta luego!")
            break
        
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()
