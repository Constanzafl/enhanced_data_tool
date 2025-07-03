#!/usr/bin/env python3
"""
Generador de CSVs Dummy para Enhanced Data Tool
Crea datos realistas con relaciones implícitas sin metadata
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
from pathlib import Path

def create_data_directory():
    """Crea el directorio de datos"""
    data_path = Path(r"C:\Users\Flori\Desktop\Omniscient Platforms\internal tool\enhanced_data_tool\data")
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path

def generate_patients_csv(data_path, num_patients=50):
    """Genera CSV de pacientes (tabla principal)"""
    
    # Nombres y apellidos argentinos
    nombres = ['Juan', 'María', 'Carlos', 'Ana', 'Pedro', 'Lucía', 'Diego', 'Sofía', 
               'Fernando', 'Valentina', 'Gabriel', 'Camila', 'Sebastián', 'Victoria', 
               'Nicolás', 'Martina', 'Alejandro', 'Florencia', 'Matías', 'Agustina']
    
    apellidos = ['García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez', 
                 'Sánchez', 'Pérez', 'Gómez', 'Martín', 'Jiménez', 'Ruiz', 'Díaz', 
                 'Moreno', 'Muñoz', 'Álvarez', 'Romero', 'Gutiérrez', 'Navarro', 'Torres']
    
    # Generar datos
    patients_data = []
    for i in range(1, num_patients + 1):
        nombre = random.choice(nombres)
        apellido = random.choice(apellidos)
        
        # Fecha nacimiento (20-80 años)
        birth_year = random.randint(1944, 2004)
        birth_date = datetime(birth_year, random.randint(1, 12), random.randint(1, 28))
        
        # Email basado en nombre
        email = f"{nombre.lower()}.{apellido.lower()}{random.randint(1, 999)}@email.com"
        
        patients_data.append({
            'id': i,  # Esta es la PK implícita
            'first_name': nombre,
            'last_name': apellido,
            'email': email,
            'phone': f"+5491{random.randint(10000000, 99999999)}",
            'birth_date': birth_date.strftime('%Y-%m-%d'),
            'gender': random.choice(['M', 'F']),
            'registration_date': (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
            'is_active': random.choice([True, False]),
            'insurance_number': f"INS{i:06d}"
        })
    
    df = pd.DataFrame(patients_data)
    df.to_csv(data_path / 'patients.csv', index=False)
    print(f"✅ Creado: patients.csv ({len(df)} registros)")
    return df

def generate_pets_csv(data_path, patients_df):
    """Genera CSV de mascotas (relacionado con patients)"""
    
    pet_names = ['Max', 'Bella', 'Luna', 'Charlie', 'Lucy', 'Cooper', 'Molly', 'Buddy', 
                 'Daisy', 'Rocky', 'Coco', 'Simba', 'Lola', 'Jack', 'Milo', 'Nala']
    
    pet_species = ['Dog', 'Cat', 'Bird', 'Rabbit', 'Hamster']
    dog_breeds = ['Labrador', 'Golden Retriever', 'Bulldog', 'Pastor Alemán', 'Beagle']
    cat_breeds = ['Siamés', 'Persa', 'Maine Coon', 'British Shorthair', 'Angora']
    
    pets_data = []
    pet_id = 1
    
    # 70% de pacientes tienen mascotas
    for _, patient in patients_df.sample(frac=0.7).iterrows():
        # Algunos pacientes tienen múltiples mascotas
        num_pets = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
        
        for _ in range(num_pets):
            species = random.choice(pet_species)
            
            if species == 'Dog':
                breed = random.choice(dog_breeds)
            elif species == 'Cat':
                breed = random.choice(cat_breeds)
            else:
                breed = species
            
            # Edad de la mascota
            age_years = random.randint(0, 15)
            registration_date = datetime.now() - timedelta(days=random.randint(0, 180))
            
            pets_data.append({
                'pet_id': pet_id,
                'name': random.choice(pet_names),
                'species': species,
                'breed': breed,
                'age_years': age_years,
                'weight_kg': round(random.uniform(0.5, 50.0), 1),
                'color': random.choice(['Brown', 'Black', 'White', 'Golden', 'Gray', 'Mixed']),
                'patients_id': patient['id'],  # FK implícita a patients.id
                'registration_date': registration_date.strftime('%Y-%m-%d'),
                'is_vaccinated': random.choice([True, False]),
                'microchip_number': f"MC{pet_id:08d}"
            })
            pet_id += 1
    
    df = pd.DataFrame(pets_data)
    df.to_csv(data_path / 'pets.csv', index=False)
    print(f"✅ Creado: pets.csv ({len(df)} registros)")
    return df

def generate_appointments_csv(data_path, patients_df, pets_df):
    """Genera CSV de citas médicas"""
    
    appointment_types = ['Consulta General', 'Vacunación', 'Cirugía', 'Control', 
                        'Emergencia', 'Chequeo Anual', 'Tratamiento']
    
    statuses = ['Scheduled', 'Completed', 'Cancelled', 'No-Show']
    
    appointments_data = []
    appointment_id = 1
    
    # Generar citas para los últimos 6 meses
    start_date = datetime.now() - timedelta(days=180)
    
    # Mezclar citas de pacientes y mascotas
    all_entities = []
    
    # Citas de pacientes (sin mascotas)
    for _, patient in patients_df.sample(frac=0.4).iterrows():
        all_entities.append(('patient', patient['id'], None))
    
    # Citas de mascotas
    for _, pet in pets_df.sample(frac=0.8).iterrows():
        all_entities.append(('pet', pet['patients_id'], pet['pet_id']))
    
    for entity_type, patient_id, pet_id in all_entities:
        # Número de citas por entidad
        num_appointments = random.choices([1, 2, 3, 4], weights=[40, 30, 20, 10])[0]
        
        for _ in range(num_appointments):
            appointment_date = start_date + timedelta(days=random.randint(0, 180))
            
            appointments_data.append({
                'appointment_id': appointment_id,
                'patient_ref': patient_id,  # FK implícita a patients.id
                'pet_reference': pet_id if pet_id else None,  # FK implícita a pets.pet_id
                'appointment_date': appointment_date.strftime('%Y-%m-%d'),
                'appointment_time': f"{random.randint(8, 17):02d}:{random.choice(['00', '30'])}",
                'appointment_type': random.choice(appointment_types),
                'status': random.choice(statuses),
                'duration_minutes': random.choice([30, 45, 60, 90]),
                'notes': f"Consulta programada para {appointment_date.strftime('%B')}",
                'doctor_name': random.choice(['Dr. González', 'Dra. Martínez', 'Dr. López', 'Dra. Silva'])
            })
            appointment_id += 1
    
    df = pd.DataFrame(appointments_data)
    df.to_csv(data_path / 'appointments.csv', index=False)
    print(f"✅ Creado: appointments.csv ({len(df)} registros)")
    return df

def generate_treatments_csv(data_path, appointments_df):
    """Genera CSV de tratamientos (relacionado con appointments)"""
    
    treatments = ['Antibióticos', 'Antiinflamatorios', 'Vitaminas', 'Desparasitación',
                 'Vacuna Rabia', 'Vacuna Triple', 'Cirugía Menor', 'Limpieza Dental',
                 'Análisis de Sangre', 'Radiografía', 'Ecografía']
    
    treatments_data = []
    treatment_id = 1
    
    # 60% de las citas tienen tratamientos
    completed_appointments = appointments_df[appointments_df['status'] == 'Completed']
    
    for _, appointment in completed_appointments.sample(frac=0.6).iterrows():
        # Algunos tratamientos múltiples
        num_treatments = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
        
        for _ in range(num_treatments):
            treatment = random.choice(treatments)
            
            treatments_data.append({
                'treatment_id': treatment_id,
                'appointment_reference': appointment['appointment_id'],  # FK implícita
                'treatment_name': treatment,
                'description': f"Aplicación de {treatment.lower()}",
                'cost': round(random.uniform(500, 5000), 2),
                'currency': 'ARS',
                'applied_date': appointment['appointment_date'],
                'applied_by': appointment['doctor_name'],
                'follow_up_required': random.choice([True, False]),
                'follow_up_days': random.choice([7, 14, 30]) if random.choice([True, False]) else None
            })
            treatment_id += 1
    
    df = pd.DataFrame(treatments_data)
    df.to_csv(data_path / 'treatments.csv', index=False)
    print(f"✅ Creado: treatments.csv ({len(df)} registros)")
    return df

def generate_veterinarians_csv(data_path):
    """Genera CSV de veterinarios"""
    
    vet_names = ['Dr. García', 'Dra. Martínez', 'Dr. López', 'Dra. Silva', 'Dr. González',
                'Dra. Rodríguez', 'Dr. Fernández', 'Dra. Pérez', 'Dr. Morales', 'Dra. Ruiz']
    
    specialties = ['Medicina General', 'Cirugía', 'Dermatología', 'Cardiología', 
                  'Oftalmología', 'Medicina Interna', 'Traumatología']
    
    vets_data = []
    for i, vet_name in enumerate(vet_names, 1):
        # Extraer nombre sin título
        name_parts = vet_name.replace('Dr. ', '').replace('Dra. ', '')
        
        vets_data.append({
            'vet_id': i,
            'full_name': vet_name,
            'license_number': f"VET{i:05d}",
            'specialty': random.choice(specialties),
            'years_experience': random.randint(2, 25),
            'email': f"{name_parts.lower().replace(' ', '.')}@vetclinic.com",
            'phone': f"+5491{random.randint(10000000, 99999999)}",
            'is_active': random.choice([True, True, True, False]),  # 75% activos
            'clinic_schedule': random.choice(['Morning', 'Afternoon', 'Full Day', 'Weekend'])
        })
    
    df = pd.DataFrame(vets_data)
    df.to_csv(data_path / 'veterinarians.csv', index=False)
    print(f"✅ Creado: veterinarians.csv ({len(df)} registros)")
    return df

def generate_medications_csv(data_path):
    """Genera CSV de medicamentos"""
    
    medications = [
        'Amoxicilina', 'Meloxicam', 'Prednisolona', 'Ivermectina', 'Doxiciclina',
        'Tramadol', 'Furosemida', 'Enalapril', 'Metacam', 'Baytril',
        'Frontline', 'Revolution', 'Advocate', 'Nexgard', 'Bravecto'
    ]
    
    meds_data = []
    for i, med_name in enumerate(medications, 1):
        meds_data.append({
            'medication_id': i,
            'name': med_name,
            'generic_name': med_name.lower(),
            'category': random.choice(['Antibiótico', 'Antiinflamatorio', 'Antiparasitario', 
                                     'Analgésico', 'Vitamina', 'Vacuna']),
            'dosage_form': random.choice(['Tableta', 'Jarabe', 'Inyección', 'Tópico']),
            'strength': f"{random.randint(5, 500)}mg",
            'manufacturer': random.choice(['Laboratorio A', 'Laboratorio B', 'Veterinaria Plus']),
            'price_per_unit': round(random.uniform(50, 2000), 2),
            'stock_quantity': random.randint(0, 100),
            'expiry_date': (datetime.now() + timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d'),
            'requires_prescription': random.choice([True, False])
        })
    
    df = pd.DataFrame(meds_data)
    df.to_csv(data_path / 'medications.csv', index=False)
    print(f"✅ Creado: medications.csv ({len(df)} registros)")
    return df

def generate_prescriptions_csv(data_path, treatments_df, medications_df):
    """Genera CSV de prescripciones (relaciona treatments con medications)"""
    
    prescriptions_data = []
    prescription_id = 1
    
    # 40% de tratamientos tienen prescripciones
    for _, treatment in treatments_df.sample(frac=0.4).iterrows():
        # Algunos tratamientos tienen múltiples medicamentos
        num_meds = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
        
        selected_meds = medications_df.sample(n=min(num_meds, len(medications_df)))
        
        for _, medication in selected_meds.iterrows():
            prescriptions_data.append({
                'prescription_id': prescription_id,
                'treatment_ref': treatment['treatment_id'],  # FK implícita
                'medication_reference': medication['medication_id'],  # FK implícita
                'dosage': f"{random.randint(1, 3)} {random.choice(['tableta', 'ml', 'aplicación'])}",
                'frequency': random.choice(['Cada 8 horas', 'Cada 12 horas', 'Una vez al día', 'Cada 3 días']),
                'duration_days': random.randint(3, 21),
                'instructions': 'Administrar con comida' if random.choice([True, False]) else 'Administrar en ayunas',
                'prescribed_date': treatment['applied_date'],
                'prescribed_by': treatment['applied_by'],
                'total_quantity': random.randint(1, 30)
            })
            prescription_id += 1
    
    df = pd.DataFrame(prescriptions_data)
    df.to_csv(data_path / 'prescriptions.csv', index=False)
    print(f"✅ Creado: prescriptions.csv ({len(df)} registros)")
    return df

def generate_lab_results_csv(data_path, appointments_df):
    """Genera CSV de resultados de laboratorio"""
    
    test_types = ['Hemograma Completo', 'Química Sanguínea', 'Análisis de Orina',
                 'Perfil Hepático', 'Perfil Renal', 'Hormonas Tiroideas', 'Coprológico']
    
    results_data = []
    result_id = 1
    
    # 25% de citas tienen análisis de laboratorio
    lab_appointments = appointments_df[
        appointments_df['appointment_type'].isin(['Consulta General', 'Chequeo Anual'])
    ].sample(frac=0.25)
    
    for _, appointment in lab_appointments.iterrows():
        # Número de análisis por cita
        num_tests = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
        
        selected_tests = random.sample(test_types, min(num_tests, len(test_types)))
        
        for test_type in selected_tests:
            # Simular fecha de resultado (1-5 días después de la cita)
            result_date = datetime.strptime(appointment['appointment_date'], '%Y-%m-%d') + \
                         timedelta(days=random.randint(1, 5))
            
            results_data.append({
                'result_id': result_id,
                'appointment_ref': appointment['appointment_id'],  # FK implícita
                'patient_identifier': appointment['patient_ref'],  # FK implícita redundante
                'test_type': test_type,
                'test_date': appointment['appointment_date'],
                'result_date': result_date.strftime('%Y-%m-%d'),
                'result_value': round(random.uniform(10, 200), 2),
                'reference_range': f"{random.randint(10, 50)}-{random.randint(100, 200)}",
                'unit': random.choice(['mg/dL', 'g/L', 'mmol/L', 'U/L', '%']),
                'status': random.choice(['Normal', 'Anormal', 'Borderline']),
                'notes': 'Valores dentro del rango esperado' if random.choice([True, False]) else 'Requiere seguimiento',
                'lab_technician': random.choice(['Téc. González', 'Téc. Martínez', 'Téc. López'])
            })
            result_id += 1
    
    df = pd.DataFrame(results_data)
    df.to_csv(data_path / 'lab_results.csv', index=False)
    print(f"✅ Creado: lab_results.csv ({len(df)} registros)")
    return df

def create_relationships_map():
    """Crea un mapa de las relaciones esperadas para validación"""
    expected_relations = {
        'pets.patients_id': 'patients.id',
        'appointments.patient_ref': 'patients.id',
        'appointments.pet_reference': 'pets.pet_id',
        'treatments.appointment_reference': 'appointments.appointment_id',
        'prescriptions.treatment_ref': 'treatments.treatment_id',
        'prescriptions.medication_reference': 'medications.medication_id',
        'lab_results.appointment_ref': 'appointments.appointment_id',
        'lab_results.patient_identifier': 'patients.id'
    }
    
    return expected_relations

def main():
    """Genera todos los CSVs dummy"""
    print("🏥 GENERANDO CSVs DUMMY PARA SISTEMA VETERINARIO")
    print("=" * 60)
    
    # Crear directorio
    data_path = create_data_directory()
    print(f"📂 Directorio creado: {data_path}")
    
    # Generar CSVs en orden de dependencias
    print("\n📊 Generando tablas principales...")
    patients_df = generate_patients_csv(data_path)
    pets_df = generate_pets_csv(data_path, patients_df)
    veterinarians_df = generate_veterinarians_csv(data_path)
    medications_df = generate_medications_csv(data_path)
    
    print("\n📊 Generando tablas relacionales...")
    appointments_df = generate_appointments_csv(data_path, patients_df, pets_df)
    treatments_df = generate_treatments_csv(data_path, appointments_df)
    prescriptions_df = generate_prescriptions_csv(data_path, treatments_df, medications_df)
    lab_results_df = generate_lab_results_csv(data_path, appointments_df)
    
    # Mostrar resumen
    print("\n📋 RESUMEN DE DATOS GENERADOS:")
    print("=" * 40)
    
    csv_files = [
        ('patients.csv', len(patients_df), 'Tabla principal'),
        ('pets.csv', len(pets_df), 'pets.patients_id → patients.id'),
        ('appointments.csv', len(appointments_df), 'appointments.patient_ref → patients.id'),
        ('treatments.csv', len(treatments_df), 'treatments.appointment_reference → appointments.appointment_id'),
        ('prescriptions.csv', len(prescriptions_df), 'prescriptions.treatment_ref → treatments.treatment_id'),
        ('lab_results.csv', len(lab_results_df), 'lab_results.appointment_ref → appointments.appointment_id'),
        ('veterinarians.csv', len(veterinarians_df), 'Tabla independiente'),
        ('medications.csv', len(medications_df), 'Tabla independiente')
    ]
    
    for filename, count, relation in csv_files:
        print(f"  📄 {filename:<20} {count:>3} registros | {relation}")
    
    # Mostrar relaciones esperadas
    print(f"\n🔗 RELACIONES IMPLÍCITAS ESPERADAS:")
    expected_relations = create_relationships_map()
    for fk, pk in expected_relations.items():
        print(f"  • {fk} → {pk}")
    
    print(f"\n✅ ¡DATOS GENERADOS EXITOSAMENTE!")
    print(f"📂 Ubicación: {data_path}")
    print(f"🎯 Ahora ejecuta: python csv_relationship_detector.py")
    
    return data_path, expected_relations

if __name__ == "__main__":
    main()
