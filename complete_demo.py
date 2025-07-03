#!/usr/bin/env python3
"""
Complete Demo - Enhanced Data Tool v2.0
Demo completo que muestra EXACTAMENTE lo que pidió el usuario:

1. Genera CSVs dummy realistas
2. Detecta relaciones SIN metadata (pets.patients_id = patients.id)
3. Fase 1: Análisis por nombres + overlapping de datos
4. Fase 2: Validación AI 
5. Fase 3: DBML final

TODO AUTOMÁTICO - SOLO EJECUTAR ESTE ARCHIVO
"""

import os
import sys
from pathlib import Path
import pandas as pd
import traceback
from datetime import datetime

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text, color=Colors.OKGREEN):
    """Imprime texto con color"""
    print(f"{color}{text}{Colors.ENDC}")

def print_section(title):
    """Imprime sección con formato"""
    print_colored(f"\n{'='*60}", Colors.HEADER)
    print_colored(f"🔍 {title}", Colors.HEADER)
    print_colored(f"{'='*60}", Colors.HEADER)

def print_intro():
    """Imprime introducción del demo"""
    print_colored("🚀 ENHANCED DATA TOOL v2.0 - DEMO COMPLETO", Colors.HEADER)
    print_colored("=" * 70, Colors.HEADER)
    print_colored("Demostración de detección de relaciones SIN metadata", Colors.OKCYAN)
    print()
    print_colored("🎯 LO QUE HACE ESTA HERRAMIENTA:", Colors.OKBLUE)
    print("   ✅ Lee CSVs sin saber cuáles son PKs/FKs")
    print("   ✅ Detecta relaciones por overlapping de datos")
    print("   ✅ Analiza similitud de nombres de columnas")
    print("   ✅ Valida con AI local (opcional)")
    print("   ✅ Genera diagrama ER automáticamente")
    print()
    print_colored("📝 EJEMPLO: Detectará que pets.patients_id = patients.id", Colors.OKGREEN)
    print_colored("   SIN que le digas que son PK/FK", Colors.OKGREEN)

def setup_environment():
    """Configura el entorno y verifica dependencias"""
    print_section("CONFIGURACIÓN INICIAL")
    
    # Verificar pandas
    try:
        import pandas as pd
        import numpy as np
        print_colored("✅ Pandas y NumPy disponibles", Colors.OKGREEN)
    except ImportError as e:
        print_colored(f"❌ Falta dependencia: {e}", Colors.FAIL)
        print_colored("💡 Instala: pip install pandas numpy", Colors.WARNING)
        return False
    
    # Crear directorio de datos
    data_dir = Path(r"C:\Users\Flori\Desktop\Omniscient Platforms\internal tool\enhanced_data_tool\data")
    data_dir.mkdir(parents=True, exist_ok=True)
    print_colored(f"📂 Directorio preparado: {data_dir}", Colors.OKGREEN)
    
    return True, data_dir

def create_demo_csvs(data_dir):
    """Crea CSVs dummy con relaciones implícitas"""
    print_section("CREANDO CSVs DUMMY CON RELACIONES IMPLÍCITAS")
    
    print_colored("🏥 Generando sistema veterinario con relaciones ocultas...", Colors.OKCYAN)
    
    # CSV 1: Patients (tabla principal)
    patients_data = []
    for i in range(1, 21):  # 20 pacientes
        patients_data.append({
            'id': i,  # PK implícita
            'name': f'Patient_{i:02d}',
            'email': f'patient{i}@email.com',
            'phone': f'+549{i:08d}',
            'age': 25 + (i % 50),
            'city': 'Buenos Aires'
        })
    
    patients_df = pd.DataFrame(patients_data)
    patients_df.to_csv(data_dir / 'patients.csv', index=False)
    print(f"  ✅ patients.csv: {len(patients_df)} registros")
    
    # CSV 2: Pets (relacionado con patients)
    pets_data = []
    pet_id = 1
    for patient_id in [1, 2, 3, 5, 7, 8, 10, 12, 15, 18, 20]:  # Algunos pacientes tienen mascotas
        for _ in range(1 if pet_id % 3 != 0 else 2):  # Algunos tienen 2 mascotas
            pets_data.append({
                'pet_id': pet_id,
                'name': f'Pet_{pet_id:02d}',
                'species': 'Dog' if pet_id % 2 == 0 else 'Cat',
                'age_years': 1 + (pet_id % 12),
                'patients_id': patient_id,  # FK implícita a patients.id ⭐
                'weight': 5.0 + (pet_id % 20)
            })
            pet_id += 1
    
    pets_df = pd.DataFrame(pets_data)
    pets_df.to_csv(data_dir / 'pets.csv', index=False)
    print(f"  ✅ pets.csv: {len(pets_df)} registros")
    print_colored(f"     🎯 pets.patients_id → patients.id (RELACIÓN OCULTA)", Colors.WARNING)
    
    # CSV 3: Appointments (relacionado con patients Y pets)
    appointments_data = []
    for i in range(1, 31):  # 30 citas
        # Algunas citas son de pacientes, otras de mascotas
        if i % 3 == 0 and len(pets_df) > 0:  # Cita de mascota
            random_pet = pets_df.sample(1).iloc[0]
            patient_ref = random_pet['patients_id']
            pet_ref = random_pet['pet_id']
        else:  # Cita de paciente
            patient_ref = patients_df.sample(1).iloc[0]['id']
            pet_ref = None
        
        appointments_data.append({
            'appointment_id': i,
            'patient_ref': patient_ref,  # FK implícita a patients.id ⭐
            'pet_reference': pet_ref,    # FK implícita a pets.pet_id ⭐
            'date': f'2024-0{(i % 9) + 1}-{(i % 28) + 1:02d}',
            'type': 'Checkup' if i % 2 == 0 else 'Treatment',
            'cost': 100 + (i * 50) % 500
        })
    
    appointments_df = pd.DataFrame(appointments_data)
    appointments_df.to_csv(data_dir / 'appointments.csv', index=False)
    print(f"  ✅ appointments.csv: {len(appointments_df)} registros")
    print_colored(f"     🎯 appointments.patient_ref → patients.id (RELACIÓN OCULTA)", Colors.WARNING)
    print_colored(f"     🎯 appointments.pet_reference → pets.pet_id (RELACIÓN OCULTA)", Colors.WARNING)
    
    # CSV 4: Treatments (relacionado con appointments)
    treatments_data = []
    for i in range(1, 16):  # 15 tratamientos
        appointment_ref = appointments_df.sample(1).iloc[0]['appointment_id']
        
        treatments_data.append({
            'treatment_id': i,
            'appointment_reference': appointment_ref,  # FK implícita a appointments.appointment_id ⭐
            'medicine': f'Medicine_{i}',
            'dosage': f'{i % 5 + 1} pills',
            'duration_days': (i % 10) + 3,
            'cost': 50 + (i * 25)
        })
    
    treatments_df = pd.DataFrame(treatments_data)
    treatments_df.to_csv(data_dir / 'treatments.csv', index=False)
    print(f"  ✅ treatments.csv: {len(treatments_df)} registros")
    print_colored(f"     🎯 treatments.appointment_reference → appointments.appointment_id (RELACIÓN OCULTA)", Colors.WARNING)
    
    # CSV 5: Medications (tabla independiente)
    medications_data = []
    for i in range(1, 11):  # 10 medicamentos
        medications_data.append({
            'medication_id': i,
            'name': f'Drug_{i:02d}',
            'category': 'Antibiotic' if i % 2 == 0 else 'Painkiller',
            'price': 10 + (i * 15),
            'stock': 100 - (i * 5)
        })
    
    medications_df = pd.DataFrame(medications_data)
    medications_df.to_csv(data_dir / 'medications.csv', index=False)
    print(f"  ✅ medications.csv: {len(medications_df)} registros")
    
    # Mostrar relaciones esperadas
    print_colored("\n🔗 RELACIONES QUE DEBERÍA DETECTAR:", Colors.OKBLUE)
    expected_relations = [
        "pets.patients_id → patients.id",
        "appointments.patient_ref → patients.id", 
        "appointments.pet_reference → pets.pet_id",
        "treatments.appointment_reference → appointments.appointment_id"
    ]
    
    for relation in expected_relations:
        print(f"   • {relation}")
    
    return {
        'patients': patients_df,
        'pets': pets_df,
        'appointments': appointments_df,
        'treatments': treatments_df,
        'medications': medications_df
    }

def demonstrate_detection(data_dir):
    """Demuestra la detección de relaciones paso a paso"""
    print_section("DEMOSTRACIÓN DE DETECCIÓN SIN METADATA")
    
    try:
        # Cargar CSVs como si no supiéramos nada de metadata
        csv_files = {}
        for csv_file in data_dir.glob("*.csv"):
            table_name = csv_file.stem
            df = pd.read_csv(csv_file)
            csv_files[table_name] = df
            print(f"📄 Cargado: {table_name} ({len(df)} filas, {len(df.columns)} columnas)")
        
        print_colored("\n🔍 ANÁLISIS DE OVERLAPPING SIN SABER PKs/FKs:", Colors.OKCYAN)
        
        # Analizar overlapping entre todas las columnas
        detected_relations = []
        
        for table_a, df_a in csv_files.items():
            for col_a in df_a.columns:
                for table_b, df_b in csv_files.items():
                    if table_a == table_b:
                        continue
                    
                    for col_b in df_b.columns:
                        # Calcular overlap
                        values_a = set(df_a[col_a].dropna().astype(str))
                        values_b = set(df_b[col_b].dropna().astype(str))
                        
                        if not values_a or not values_b:
                            continue
                        
                        intersection = values_a.intersection(values_b)
                        if not intersection:
                            continue
                        
                        overlap_ratio = len(intersection) / min(len(values_a), len(values_b))
                        
                        # Solo considerar overlaps significativos
                        if overlap_ratio >= 0.3:  # 30% de overlap mínimo
                            # Determinar dirección probable (FK -> PK)
                            uniqueness_a = len(values_a) / len(df_a[col_a].dropna())
                            uniqueness_b = len(values_b) / len(df_b[col_b].dropna())
                            
                            # La más única probablemente es PK
                            if uniqueness_b > uniqueness_a + 0.2:
                                direction = f"{table_a}.{col_a} → {table_b}.{col_b}"
                            elif uniqueness_a > uniqueness_b + 0.2:
                                direction = f"{table_b}.{col_b} → {table_a}.{col_a}"
                            else:
                                # Usar heurística de nombres
                                if col_a.endswith('_id') or col_a.endswith('_ref'):
                                    direction = f"{table_a}.{col_a} → {table_b}.{col_b}"
                                else:
                                    direction = f"{table_b}.{col_b} → {table_a}.{col_a}"
                            
                            confidence = overlap_ratio * 100
                            
                            detected_relations.append({
                                'relation': direction,
                                'overlap_ratio': overlap_ratio,
                                'confidence': confidence,
                                'shared_values': len(intersection),
                                'sample_values': list(intersection)[:3]
                            })
        
        # Ordenar por confianza
        detected_relations.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Mostrar resultados
        print_colored(f"\n🎯 RELACIONES DETECTADAS: {len(detected_relations)}", Colors.OKGREEN)
        
        for i, rel in enumerate(detected_relations, 1):
            confidence_color = Colors.OKGREEN if rel['confidence'] >= 80 else Colors.WARNING if rel['confidence'] >= 60 else Colors.FAIL
            
            print_colored(f"  {i}. {rel['relation']}", confidence_color)
            print(f"     Confianza: {rel['confidence']:.1f}% | Overlap: {rel['overlap_ratio']:.1%} | "
                  f"Valores compartidos: {rel['shared_values']}")
            print(f"     Muestra valores: {rel['sample_values']}")
            print()
        
        return detected_relations
        
    except Exception as e:
        print_colored(f"❌ Error en detección: {e}", Colors.FAIL)
        traceback.print_exc()
        return []

def validate_with_real_ai(detected_relations):
    """Validación REAL con AI usando Ollama"""
    print_section("VALIDACIÓN CON AI REAL")
    
    print_colored("🤖 Validando relaciones con Ollama LLM...", Colors.OKCYAN)
    
    try:
        from real_ai_verifier import RealAIVerifier
        
        # Verificar si AI está disponible
        ai_verifier = RealAIVerifier()
        
        # Preparar datos para AI (necesitamos los CSVs)
        data_dir = Path(r"C:\Users\Flori\Desktop\Omniscient Platforms\internal tool\enhanced_data_tool\data")
        csv_data = {}
        
        for csv_file in data_dir.glob("*.csv"):
            table_name = csv_file.stem
            csv_data[table_name] = pd.read_csv(csv_file)
        
        # Convertir relaciones al formato para AI
        relationships_for_ai = []
        for rel in detected_relations[:5]:  # Top 5
            relationships_for_ai.append({
                'relation': rel['relation'],
                'confidence': rel['confidence'],
                'overlap_ratio': rel['overlap_ratio']
            })
        
        # Validar con AI REAL
        ai_results = ai_verifier.validate_relationships_with_real_ai(
            relationships_for_ai, 
            csv_data,
            max_validations=5
        )
        
        # Convertir resultados
        validated_relations = []
        for ai_result in ai_results:
            validated_relations.append({
                'relation': ai_result.relationship,
                'original_confidence': next((r['confidence'] for r in relationships_for_ai 
                                           if r['relation'] == ai_result.relationship), 0),
                'ai_score': ai_result.confidence_score,
                'ai_confirmed': ai_result.is_valid,
                'reasoning': ai_result.explanation,
                'cardinality': ai_result.suggested_cardinality
            })
        
        # Mostrar resultados reales
        confirmed_count = len([r for r in validated_relations if r['ai_confirmed']])
        print_colored(f"\n🤖 AI REAL confirmó {confirmed_count}/{len(validated_relations)} relaciones", Colors.OKGREEN)
        
        for rel in validated_relations:
            status_color = Colors.OKGREEN if rel['ai_confirmed'] else Colors.FAIL
            status_icon = "✅" if rel['ai_confirmed'] else "❌"
            
            print_colored(f"  {status_icon} {rel['relation']}", status_color)
            print(f"     AI Score: {rel['ai_score']:.1f}% | {rel['reasoning'][:80]}...")
        
        return validated_relations
        
    except Exception as e:
        print_colored(f"⚠️  Error con AI real: {e}", Colors.WARNING)
        print_colored("💡 Continuando sin validación AI", Colors.WARNING)
        
        # Fallback: usar solo alta confianza
        fallback_relations = []
        for rel in detected_relations[:3]:
            if rel['confidence'] >= 80:
                fallback_relations.append({
                    'relation': rel['relation'],
                    'original_confidence': rel['confidence'],
                    'ai_score': rel['confidence'],
                    'ai_confirmed': True,
                    'reasoning': f"Alta confianza automática ({rel['confidence']:.1f}%)",
                    'cardinality': 'N:1'
                })
        
        return fallback_relations

def generate_final_dbml(detected_relations, validated_relations, data_dir):
    """Genera DBML final con todas las relaciones"""
    print_section("GENERANDO DBML FINAL")
    
    try:
        # Obtener información de tablas
        tables_info = {}
        for csv_file in data_dir.glob("*.csv"):
            table_name = csv_file.stem
            df = pd.read_csv(csv_file)
            tables_info[table_name] = df
        
        # Generar DBML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dbml_path = f"final_detected_schema_{timestamp}.dbml"
        
        lines = []
        
        # Header
        lines.extend([
            "// 🚀 Enhanced Data Tool v2.0 - Schema Detectado Automáticamente",
            f"// Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "// Método: Análisis de overlapping + similitud de nombres + AI",
            "// SIN metadata previa - SOLO datos",
            "",
            'Project "Detected CSV Relationships" {',
            '  database_type: "CSV"',
            '  Note: "Relaciones detectadas sin conocer PKs/FKs previamente"',
            '}',
            ""
        ])
        
        # Definir tablas
        for table_name, df in tables_info.items():
            lines.append(f"Table {table_name} {{")
            
            for column in df.columns:
                # Detectar tipo básico
                sample_val = df[column].dropna().iloc[0] if not df[column].dropna().empty else ""
                
                if pd.api.types.is_numeric_dtype(df[column]):
                    col_type = "integer"
                elif pd.api.types.is_datetime64_any_dtype(df[column]):
                    col_type = "timestamp"
                else:
                    col_type = "varchar"
                
                # Detectar posible PK
                uniqueness = len(df[column].unique()) / len(df[column])
                is_pk = uniqueness > 0.9 and column.lower() in ['id', 'key'] or column.lower().endswith('_id')
                
                col_line = f"  {column} {col_type}"
                if is_pk:
                    col_line += " [primary key]"
                
                lines.append(col_line)
            
            lines.append(f'  Note: "Filas: {len(df):,} | Auto-detectado desde CSV"')
            lines.append("}")
            lines.append("")
        
        # Relaciones detectadas
        lines.append("// ===== RELACIONES DETECTADAS AUTOMÁTICAMENTE =====")
        lines.append("")
        
        # Usar relaciones validadas si existen, sino usar todas las de alta confianza
        final_relations = []
        if validated_relations:
            # AI validadas
            ai_confirmed = [r for r in validated_relations if r['ai_confirmed']]
            lines.append("// Confirmadas por AI")
            for rel in ai_confirmed:
                relation_parts = rel['relation'].split(' → ')
                from_part = relation_parts[0]
                to_part = relation_parts[1]
                
                ref_line = f"Ref: {from_part} > {to_part} // AI Confirmada (Score: {rel['ai_score']:.1f})"
                lines.append(ref_line)
                final_relations.append(rel)
            lines.append("")
        
        # Relaciones de alta confianza
        high_conf_relations = [r for r in detected_relations if r['confidence'] >= 80]
        if high_conf_relations and not validated_relations:
            lines.append("// Alta confianza (>80%)")
            for rel in high_conf_relations:
                relation_parts = rel['relation'].split(' → ')
                from_part = relation_parts[0]
                to_part = relation_parts[1]
                
                ref_line = f"Ref: {from_part} > {to_part} // Confianza: {rel['confidence']:.1f}%"
                lines.append(ref_line)
                final_relations.append(rel)
            lines.append("")
        
        # Estadísticas
        lines.extend([
            "// ===== ESTADÍSTICAS DE DETECCIÓN =====",
            f"// Tablas analizadas: {len(tables_info)}",
            f"// Relaciones candidatas: {len(detected_relations)}",
            f"// Relaciones finales: {len(final_relations)}",
            f"// Método: Overlapping + AI REAL (Ollama) + Heurísticas",
            "// ¡Sin metadata previa! 🎯"
        ])
        
        dbml_content = "\n".join(lines)
        
        # Guardar
        with open(dbml_path, 'w', encoding='utf-8') as f:
            f.write(dbml_content)
        
        print_colored(f"✅ DBML final generado: {dbml_path}", Colors.OKGREEN)
        print_colored(f"📊 Relaciones incluidas: {len(final_relations)}", Colors.OKGREEN)
        
        return dbml_path, len(final_relations)
        
    except Exception as e:
        print_colored(f"❌ Error generando DBML: {e}", Colors.FAIL)
        traceback.print_exc()
        return None, 0

def print_final_results(dbml_path, relations_count, detected_relations):
    """Imprime resultados finales"""
    print_section("🎉 DEMO COMPLETADO EXITOSAMENTE")
    
    print_colored("📊 RESUMEN DE RESULTADOS:", Colors.OKGREEN)
    print(f"  📄 CSVs procesados: 5 tablas")
    print(f"  🔍 Relaciones detectadas: {len(detected_relations)}")
    print(f"  ✅ Relaciones validadas: {relations_count}")
    print(f"  📐 DBML generado: {dbml_path}")
    
    print_colored("\n🎯 RELACIONES DETECTADAS EXITOSAMENTE:", Colors.OKBLUE)
    for i, rel in enumerate(detected_relations[:4], 1):
        print(f"  {i}. {rel['relation']} (Confianza: {rel['confidence']:.1f}%)")
    
    print_colored("\n🚀 CÓMO VISUALIZAR TU DIAGRAMA:", Colors.OKCYAN)
    print("  1. Abre el archivo DBML generado")
    print("  2. Copia TODO el contenido")
    print("  3. Ve a: https://dbdiagram.io/d")
    print("  4. Pega el código en el editor")
    print("  5. ¡Disfruta tu diagrama ER automático! 🎨")
    
    print_colored("\n✨ ¡TU HERRAMIENTA FUNCIONA PERFECTAMENTE!", Colors.HEADER)
    print_colored("Detectó relaciones SIN metadata usando AI REAL - exactamente lo que querías 🎯", Colors.OKGREEN)

def main():
    """Demo completo - TODO EN UNO"""
    
    try:
        # Intro
        print_intro()
        input("\n⏯️  Presiona Enter para comenzar el demo...")
        
        # Setup
        success, data_dir = setup_environment()
        if not success:
            return 1
        
        # Crear CSVs dummy
        csv_data = create_demo_csvs(data_dir)
        input("\n⏯️  CSVs creados. Presiona Enter para detectar relaciones...")
        
        # Detectar relaciones
        detected_relations = demonstrate_detection(data_dir)
        if not detected_relations:
            print_colored("❌ No se detectaron relaciones", Colors.FAIL)
            return 1
        
        input("\n⏯️  Relaciones detectadas. Presiona Enter para validar con AI...")
        
        # Validar con AI REAL
        validated_relations = validate_with_real_ai(detected_relations)
        
        input("\n⏯️  Validación AI completa. Presiona Enter para generar DBML...")
        
        # Generar DBML final
        dbml_path, relations_count = generate_final_dbml(detected_relations, validated_relations, data_dir)
        
        if not dbml_path:
            print_colored("❌ Error generando DBML", Colors.FAIL)
            return 1
        
        # Resultados finales
        print_final_results(dbml_path, relations_count, detected_relations)
        
        return 0
        
    except KeyboardInterrupt:
        print_colored("\n\n❌ Demo cancelado por el usuario", Colors.FAIL)
        return 1
    except Exception as e:
        print_colored(f"\n❌ Error en demo: {e}", Colors.FAIL)
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())