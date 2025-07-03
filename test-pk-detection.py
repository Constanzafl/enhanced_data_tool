#!/usr/bin/env python3
"""
Script de prueba para demostrar que el sistema NO confunde
pets.id con patients.id, y detecta correctamente pets.patient_id → patients.id
"""

import pandas as pd
from smart_detector import SmartRelationshipDetector

def create_test_data():
    """Crea datos de prueba que demuestran el problema"""
    
    # Tabla patients
    patients = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],  # PK de patients
        'name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Davis'],
        'email': ['john@email.com', 'jane@email.com', 'bob@email.com', 'alice@email.com', 'charlie@email.com'],
        'phone': ['555-0001', '555-0002', '555-0003', '555-0004', '555-0005']
    })
    
    # Tabla pets
    pets = pd.DataFrame({
        'id': [101, 102, 103, 104, 105],  # PK de pets (IDs diferentes a patients!)
        'patient_id': [1, 1, 2, 3, 4],     # FK a patients.id
        'name': ['Fluffy', 'Max', 'Luna', 'Rocky', 'Bella'],
        'species': ['Cat', 'Dog', 'Cat', 'Dog', 'Cat'],
        'age': [3, 5, 2, 7, 4]
    })
    
    # Tabla appointments
    appointments = pd.DataFrame({
        'id': [1001, 1002, 1003, 1004, 1005],  # PK de appointments
        'patient_id': [1, 2, 1, 3, 4],         # FK a patients.id
        'pet_id': [101, 103, 102, 104, 105],  # FK a pets.id
        'date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19'],
        'reason': ['Checkup', 'Vaccination', 'Surgery', 'Checkup', 'Consultation']
    })
    
    return {
        'patients': patients,
        'pets': pets,
        'appointments': appointments
    }

def test_pk_detection():
    """Prueba la detección de PKs y relaciones"""
    print("🧪 TEST: Detección de Claves Primarias y Relaciones")
    print("=" * 60)
    
    # Crear datos de prueba
    tables = create_test_data()
    
    # Mostrar los datos
    print("\n📊 Datos de Prueba:")
    for name, df in tables.items():
        print(f"\n{name}:")
        print(df.head())
    
    # Ejecutar el detector
    detector = SmartRelationshipDetector(tables)
    candidates = detector.find_relationships()
    
    # Buscar específicamente las relaciones que nos interesan
    print("\n\n🔍 Verificando Relaciones Específicas:")
    print("-" * 60)
    
    # 1. Verificar que pets.id NO se relaciona con patients.id
    pets_id_to_patients_id = None
    for c in candidates:
        if (c.source_table == 'pets' and c.source_column == 'id' and
            c.target_table == 'patients' and c.target_column == 'id'):
            pets_id_to_patients_id = c
            break
    
    if pets_id_to_patients_id:
        print("\n❌ ERROR: Se detectó incorrectamente pets.id → patients.id")
        print(f"   Confianza: {pets_id_to_patients_id.confidence_score:.1%}")
        print(f"   Evidencia: {pets_id_to_patients_id.evidence}")
    else:
        print("\n✅ CORRECTO: NO se detectó pets.id → patients.id")
    
    # 2. Verificar que SÍ detecta pets.patient_id → patients.id
    pets_patient_id_to_patients_id = None
    for c in candidates:
        if (c.source_table == 'pets' and c.source_column == 'patient_id' and
            c.target_table == 'patients' and c.target_column == 'id'):
            pets_patient_id_to_patients_id = c
            break
    
    if pets_patient_id_to_patients_id:
        print("\n✅ CORRECTO: Se detectó pets.patient_id → patients.id")
        print(f"   Confianza: {pets_patient_id_to_patients_id.confidence_score:.1%}")
        print(f"   Coincidencia de valores: {pets_patient_id_to_patients_id.evidence['value_overlap']['percentage']:.1f}%")
    else:
        print("\n❌ ERROR: NO se detectó pets.patient_id → patients.id")
    
    # 3. Mostrar todas las relaciones detectadas
    print("\n\n📋 Todas las Relaciones Detectadas (ordenadas por confianza):")
    print("-" * 60)
    detector.print_results(candidates, top_n=15)
    
    # 4. Análisis de PKs vs FKs
    print("\n\n🔑 Análisis de Tipos de Relaciones:")
    print("-" * 60)
    
    pk_to_pk = []
    fk_to_pk = []
    other = []
    
    for c in candidates[:10]:
        source_is_pk = detector.primary_keys.get(c.source_table) == c.source_column
        target_is_pk = detector.primary_keys.get(c.target_table) == c.target_column
        
        if source_is_pk and target_is_pk:
            pk_to_pk.append(c)
        elif not source_is_pk and target_is_pk:
            fk_to_pk.append(c)
        else:
            other.append(c)
    
    print(f"\nFK → PK (Correctas): {len(fk_to_pk)}")
    for c in fk_to_pk[:5]:
        print(f"  ✓ {c.source_table}.{c.source_column} → {c.target_table}.{c.target_column} ({c.confidence_score:.1%})")
    
    print(f"\nPK → PK (Probablemente incorrectas): {len(pk_to_pk)}")
    for c in pk_to_pk[:5]:
        print(f"  ⚠️  {c.source_table}.{c.source_column} → {c.target_table}.{c.target_column} ({c.confidence_score:.1%})")
    
    print(f"\nOtras: {len(other)}")
    for c in other[:5]:
        print(f"  ? {c.source_table}.{c.source_column} → {c.target_table}.{c.target_column} ({c.confidence_score:.1%})")

if __name__ == "__main__":
    test_pk_detection()
