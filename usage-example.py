#!/usr/bin/env python3
"""
Ejemplo completo de uso del detector inteligente de relaciones
"""

import pandas as pd
from smart_detector import SmartRelationshipDetector
from ai_validator import AIRelationshipValidator

# Ejemplo 1: Datos de clínica veterinaria
def veterinary_clinic_example():
    """Ejemplo con datos de clínica veterinaria"""
    print("\n🏥 EJEMPLO: Clínica Veterinaria")
    print("=" * 60)
    
    # Crear tablas de ejemplo
    tables = {
        'owners': pd.DataFrame({
            'owner_id': [1, 2, 3, 4, 5],
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Davis'],
            'email': ['john@email.com', 'jane@email.com', 'bob@email.com', 'alice@email.com', 'charlie@email.com'],
            'phone': ['555-0001', '555-0002', '555-0003', '555-0004', '555-0005']
        }),
        
        'pets': pd.DataFrame({
            'pet_id': [101, 102, 103, 104, 105, 106],
            'owner_id': [1, 1, 2, 3, 4, 5],  # FK a owners.owner_id
            'name': ['Fluffy', 'Max', 'Luna', 'Rocky', 'Bella', 'Charlie'],
            'species': ['Cat', 'Dog', 'Cat', 'Dog', 'Cat', 'Dog'],
            'breed': ['Persian', 'Labrador', 'Siamese', 'Bulldog', 'Maine Coon', 'Beagle'],
            'birth_date': ['2020-03-15', '2018-07-22', '2021-01-10', '2016-11-30', '2019-05-05', '2020-09-18']
        }),
        
        'vets': pd.DataFrame({
            'vet_id': [201, 202, 203],
            'name': ['Dr. Sarah Wilson', 'Dr. Mike Johnson', 'Dr. Emily Chen'],
            'specialization': ['General', 'Surgery', 'Dentistry'],
            'license_number': ['VET-001', 'VET-002', 'VET-003']
        }),
        
        'appointments': pd.DataFrame({
            'appointment_id': [1001, 1002, 1003, 1004, 1005, 1006],
            'pet_id': [101, 103, 102, 104, 105, 106],      # FK a pets.pet_id
            'vet_id': [201, 201, 202, 201, 203, 202],      # FK a vets.vet_id
            'appointment_date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19', '2024-01-20'],
            'reason': ['Checkup', 'Vaccination', 'Surgery', 'Checkup', 'Dental cleaning', 'X-ray'],
            'status': ['completed', 'completed', 'scheduled', 'completed', 'scheduled', 'scheduled']
        }),
        
        'treatments': pd.DataFrame({
            'treatment_id': [3001, 3002, 3003, 3004],
            'appointment_id': [1001, 1002, 1004, 1001],    # FK a appointments.appointment_id
            'description': ['General checkup', 'Rabies vaccine', 'Wellness exam', 'Blood test'],
            'cost': [50.00, 35.00, 50.00, 75.00]
        })
    }
    
    # Ejecutar análisis
    detector = SmartRelationshipDetector(tables)
    candidates = detector.find_relationships()
    
    # Mostrar resultados
    print("\n📊 Relaciones Detectadas:")
    detector.print_results(candidates, top_n=10)
    
    return tables, candidates

# Ejemplo 2: Sistema de e-commerce
def ecommerce_example():
    """Ejemplo con datos de e-commerce"""
    print("\n🛒 EJEMPLO: Sistema E-Commerce")
    print("=" * 60)
    
    tables = {
        'customers': pd.DataFrame({
            'customer_id': [1, 2, 3, 4, 5],
            'email': ['john@email.com', 'jane@email.com', 'bob@email.com', 'alice@email.com', 'charlie@email.com'],
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Davis'],
            'registration_date': ['2023-01-15', '2023-02-20', '2023-03-10', '2023-04-05', '2023-05-12']
        }),
        
        'products': pd.DataFrame({
            'product_id': [101, 102, 103, 104, 105],
            'sku': ['LAPTOP-001', 'MOUSE-002', 'KEYB-003', 'MONITOR-004', 'CABLE-005'],
            'name': ['Laptop Pro', 'Wireless Mouse', 'Mechanical Keyboard', '27" Monitor', 'USB-C Cable'],
            'category_id': [1, 2, 2, 1, 3],  # FK a categories
            'price': [999.99, 29.99, 89.99, 299.99, 19.99]
        }),
        
        'categories': pd.DataFrame({
            'category_id': [1, 2, 3],
            'name': ['Electronics', 'Accessories', 'Cables'],
            'parent_category_id': [None, 1, 1]  # Self-referencing
        }),
        
        'orders': pd.DataFrame({
            'order_id': [1001, 1002, 1003, 1004],
            'customer_id': [1, 2, 1, 3],  # FK a customers.customer_id
            'order_date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18'],
            'total_amount': [1029.98, 89.99, 319.98, 999.99],
            'status': ['shipped', 'processing', 'delivered', 'processing']
        }),
        
        'order_items': pd.DataFrame({
            'order_item_id': [2001, 2002, 2003, 2004, 2005],
            'order_id': [1001, 1001, 1002, 1003, 1004],     # FK a orders.order_id
            'product_id': [101, 102, 103, 104, 101],        # FK a products.product_id
            'quantity': [1, 1, 1, 1, 1],
            'unit_price': [999.99, 29.99, 89.99, 299.99, 999.99]
        })
    }
    
    # Ejecutar análisis
    detector = SmartRelationshipDetector(tables)
    candidates = detector.find_relationships()
    
    # Mostrar resultados
    print("\n📊 Relaciones Detectadas:")
    detector.print_results(candidates, top_n=10)
    
    return tables, candidates

# Función principal con menú
def main():
    """Menú principal de ejemplos"""
    print("🔍 EJEMPLOS DE DETECCIÓN DE RELACIONES")
    print("=" * 60)
    
    while True:
        print("\n📋 Selecciona un ejemplo:")
        print("1. Clínica Veterinaria")
        print("2. Sistema E-Commerce")
        print("3. Cargar tus propios CSVs")
        print("4. Salir")
        
        choice = input("\nOpción (1-4): ").strip()
        
        if choice == '1':
            tables, candidates = veterinary_clinic_example()
            
            # Preguntar si quiere validar con AI
            if input("\n¿Validar con AI? (s/n): ").lower() == 's':
                validator = AIRelationshipValidator()
                print("\n🤖 Validando con AI las top 5 relaciones...")
                
                # Preparar relaciones para validar
                relationships = []
                for c in candidates[:5]:
                    relationships.append((
                        f"{c.source_table}.{c.source_column}",
                        f"{c.target_table}.{c.target_column}",
                        c.confidence_score,
                        c.evidence
                    ))
                
                validator.validate_batch(relationships, tables)
                
        elif choice == '2':
            tables, candidates = ecommerce_example()
            
        elif choice == '3':
            print("\n📁 Carga de archivos CSV")
            print("Coloca tus archivos CSV en el directorio actual.")
            
            tables = {}
            while True:
                filename = input("\nNombre del archivo (o 'fin' para terminar): ").strip()
                if filename.lower() == 'fin':
                    break
                
                try:
                    if not filename.endswith('.csv'):
                        filename += '.csv'
                    
                    table_name = filename.replace('.csv', '')
                    tables[table_name] = pd.read_csv(filename)
                    print(f"✅ Cargado: {table_name} ({tables[table_name].shape[0]} filas)")
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            if tables:
                detector = SmartRelationshipDetector(tables)
                candidates = detector.find_relationships()
                detector.print_results(candidates, top_n=20)
            
        elif choice == '4':
            print("\n👋 ¡Hasta luego!")
            break
        
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()
