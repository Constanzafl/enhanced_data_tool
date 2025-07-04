#!/usr/bin/env python3
"""
Prueba del detector con nombres de columnas complejos y no estándar
"""

import pandas as pd
import numpy as np
from smartdbdetector import SmartRelationshipDetector

def create_complex_test_data():
    """Crea datos de prueba con nombres de columnas no estándar"""
    
    # Tabla patients con nombres no estándar
    patients = pd.DataFrame({
        'PatientUID': ['P001', 'P002', 'P003', 'P004', 'P005'],  # PK no estándar
        'FullName': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Davis'],
        'ContactEmail': ['john@email.com', 'jane@email.com', 'bob@email.com', 'alice@email.com', 'charlie@email.com'],
        'DateOfBirth': ['1990-01-15', '1985-03-22', '1978-11-30', '1992-07-08', '1995-12-25']
    })
    
    # Tabla pets con referencias no obvias
    pets = pd.DataFrame({
        'AnimalIdentifier': ['A101', 'A102', 'A103', 'A104', 'A105'],  # PK
        'OwnerPatientCode': ['P001', 'P001', 'P002', 'P003', 'P004'],  # FK a patients.PatientUID
        'PetName': ['Fluffy', 'Max', 'Luna', 'Rocky', 'Bella'],
        'AnimalType': ['Feline', 'Canine', 'Feline', 'Canine', 'Feline']
    })
    
    # Tabla appointments con mezcla de idiomas
    appointments = pd.DataFrame({
        'CitaID': [1001, 1002, 1003, 1004, 1005],  # PK en español
        'pacienteIdentificador': ['P001', 'P002', 'P001', 'P003', 'P004'],  # FK mixto
        'MascotaCodigo': ['A101', 'A103', 'A102', 'A104', 'A105'],  # FK en español
        'FechaCita': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19'],
        'MotivoConsulta': ['Checkup', 'Vaccination', 'Surgery', 'Checkup', 'Consultation']
    })
    
    # Tabla medications con nombres muy técnicos
    medications = pd.DataFrame({
        'MedicationUUID': ['MED-550e8400', 'MED-550e8401', 'MED-550e8402', 'MED-550e8403'],  # PK tipo UUID
        'DrugName': ['Amoxicillin', 'Rimadyl', 'Frontline', 'Vitamin K'],
        'PharmaceuticalCategory': ['Antibiotic', 'NSAID', 'Antiparasitic', 'Supplement']
    })
    
    # Tabla prescriptions con nombres en camelCase
    prescriptions = pd.DataFrame({
        'PrescriptionNumber': [3001, 3002, 3003, 3004, 3005],  # PK
        'AppointmentReference': [1001, 1002, 1003, 1004, 1005],  # FK a appointments.CitaID
        'MedicationCode': ['MED-550e8400', 'MED-550e8401', 'MED-550e8402', 'MED-550e8403', 'MED-550e8400'],  # FK
        'DosageInstructions': ['2 pills/day', '1 pill/8h', '1 application/month', '1 pill/day', '3 pills/day']
    })
    
    # Tabla staff con nombres completamente diferentes
    staff = pd.DataFrame({
        'EmployeeGUID': ['EMP-001', 'EMP-002', 'EMP-003'],  # PK
        'StaffFullName': ['Dr. Sarah Wilson', 'Dr. Mike Johnson', 'Dr. Emily Chen'],
        'ProfessionalLicense': ['VET-001', 'VET-002', 'VET-003']
    })
    
    # Tabla con relación al staff
    appointment_staff = pd.DataFrame({
        'ScheduleEntryID': [5001, 5002, 5003, 5004, 5005],  # PK
        'BookingReference': [1001, 1002, 1003, 1004, 1005],  # FK a appointments.CitaID
        'AssignedProfessional': ['EMP-001', 'EMP-001', 'EMP-002', 'EMP-003', 'EMP-002']  # FK a staff.EmployeeGUID
    })
    
    return {
        'patients': patients,
        'pets': pets,
        'appointments': appointments,
        'medications': medications,
        'prescriptions': prescriptions,
        'staff': staff,
        'appointment_staff': appointment_staff
    }

def test_complex_names():
    """Prueba el detector con nombres complejos"""
    print("🧪 TEST: Detección con Nombres de Columnas No Estándar")
    print("=" * 70)
    
    # Crear datos
    tables = create_complex_test_data()
    
    # Mostrar estructura
    print("\n📊 Estructura de las Tablas:")
    for name, df in tables.items():
        print(f"\n{name}:")
        print(f"  Columnas: {', '.join(df.columns)}")
        print(f"  Ejemplo: {dict(df.iloc[0])}")
    
    # Ejecutar detector
    print("\n" + "="*70)
    detector = SmartRelationshipDetector(tables)
    candidates = detector.find_relationships()
    
    # Verificar relaciones específicas esperadas
    print("\n\n🔍 Verificando Detección de Relaciones Complejas:")
    print("-" * 70)
    
    expected_relations = [
        ('pets', 'OwnerPatientCode', 'patients', 'PatientUID'),
        ('appointments', 'pacienteIdentificador', 'patients', 'PatientUID'),
        ('appointments', 'MascotaCodigo', 'pets', 'AnimalIdentifier'),
        ('prescriptions', 'AppointmentReference', 'appointments', 'CitaID'),
        ('prescriptions', 'MedicationCode', 'medications', 'MedicationUUID'),
        ('appointment_staff', 'BookingReference', 'appointments', 'CitaID'),
        ('appointment_staff', 'AssignedProfessional', 'staff', 'EmployeeGUID')
    ]
    
    found_count = 0
    for src_table, src_col, tgt_table, tgt_col in expected_relations:
        found = False
        for c in candidates:
            if (c.source_table == src_table and c.source_column == src_col and
                c.target_table == tgt_table and c.target_column == tgt_col):
                found = True
                found_count += 1
                print(f"\n✅ ENCONTRADA: {src_table}.{src_col} → {tgt_table}.{tgt_col}")
                print(f"   Confianza: {c.confidence_score:.1%}")
                print(f"   Coincidencia valores: {c.evidence['value_overlap']['percentage']:.1f}%")
                break
        
        if not found:
            print(f"\n❌ NO ENCONTRADA: {src_table}.{src_col} → {tgt_table}.{tgt_col}")
    
    print(f"\n\n📈 Resumen: {found_count}/{len(expected_relations)} relaciones esperadas encontradas")
    
    # Mostrar todas las relaciones detectadas
    print("\n\n📋 Todas las Relaciones Detectadas:")
    print("-" * 70)
    detector.print_results(candidates, top_n=20)
    
    # Análisis de nombres complejos
    print("\n\n🔤 Análisis de Descomposición de Nombres:")
    print("-" * 70)
    
    test_names = [
        'PatientUID',
        'OwnerPatientCode', 
        'pacienteIdentificador',
        'MascotaCodigo',
        'MedicationUUID',
        'AssignedProfessional'
    ]
    
    for name in test_names:
        components = detector._extract_name_components(name.lower())
        print(f"\n'{name}':")
        print(f"  - Palabras: {components['all_words']}")
        print(f"  - Palabras base: {components['base_words']}")
        print(f"  - Tiene ID: {components['has_id_component']}")

def compare_detection_methods():
    """Compara detección con nombres estándar vs no estándar"""
    print("\n\n📊 COMPARACIÓN: Nombres Estándar vs No Estándar")
    print("=" * 70)
    
    # Datos con nombres estándar
    standard_tables = {
        'patients': pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['John', 'Jane', 'Bob']
        }),
        'appointments': pd.DataFrame({
            'id': [101, 102, 103],
            'patient_id': [1, 2, 1]
        })
    }
    
    # Datos con nombres no estándar (mismos datos, diferentes nombres)
    complex_tables = {
        'patients': pd.DataFrame({
            'PatientIdentifier': [1, 2, 3],
            'FullName': ['John', 'Jane', 'Bob']
        }),
        'appointments': pd.DataFrame({
            'BookingUID': [101, 102, 103],
            'PatientReference': [1, 2, 1]
        })
    }
    
    # Detectar en ambos
    print("\n1️⃣ Con nombres estándar:")
    detector1 = SmartRelationshipDetector(standard_tables)
    candidates1 = detector1.find_relationships()
    print(f"   Relaciones encontradas: {len(candidates1)}")
    for c in candidates1[:3]:
        print(f"   - {c.source_table}.{c.source_column} → {c.target_table}.{c.target_column} ({c.confidence_score:.1%})")
    
    print("\n2️⃣ Con nombres no estándar:")
    detector2 = SmartRelationshipDetector(complex_tables)
    candidates2 = detector2.find_relationships()
    print(f"   Relaciones encontradas: {len(candidates2)}")
    for c in candidates2[:3]:
        print(f"   - {c.source_table}.{c.source_column} → {c.target_table}.{c.target_column} ({c.confidence_score:.1%})")

if __name__ == "__main__":
    # Ejecutar pruebas
    test_complex_names()
    compare_detection_methods()
