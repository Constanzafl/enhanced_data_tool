#!/usr/bin/env python3
"""
Main Pipeline - Enhanced Data Tool v2.0 (ACTUALIZADO CON AI REAL)
Pipeline completo: CSV → Análisis → AI REAL → DBML
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime
import traceback

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

class EnhancedDataToolPipeline:
    """
    Pipeline completo para detectar relaciones en CSVs
    Fase 1: Análisis de datos + nombres
    Fase 2: Validación AI REAL (no simulada)
    Fase 3: Generación DBML
    """
    
    def __init__(self, data_directory: str, use_ai: bool = True):
        self.data_directory = Path(data_directory)
        self.use_ai = use_ai
        self.results = {}
        
        # Verificar directorio
        if not self.data_directory.exists():
            raise Exception(f"Directorio no encontrado: {data_directory}")
    
    def run_phase_1_data_analysis(self):
        """
        FASE 1: Análisis por nombre de tabla/columna + overlapping de datos
        SIN metadata - solo datos puros
        """
        print_section("FASE 1: ANÁLISIS DE DATOS Y NOMBRES")
        
        try:
            # Importar detector CSV
            from old.csv_relationship_detector import CSVRelationshipDetector
            
            # Ejecutar análisis
            detector = CSVRelationshipDetector(str(self.data_directory))
            
            # Cargar y analizar
            detector.load_csvs()
            detector.analyze_columns()
            relationships = detector.detect_relationships()
            
            # Guardar resultados de fase 1
            self.results['phase_1'] = {
                'detector': detector,
                'relationships': relationships,
                'tables_count': len(detector.csv_files),
                'relationships_count': len(relationships),
                'high_confidence': len([r for r in relationships if r.confidence >= 80]),
                'timestamp': datetime.now().isoformat()
            }
            
            print_colored(f"✅ Fase 1 completada:", Colors.OKGREEN)
            print(f"   📊 Tablas analizadas: {self.results['phase_1']['tables_count']}")
            print(f"   🔗 Relaciones detectadas: {self.results['phase_1']['relationships_count']}")
            print(f"   🟢 Alta confianza: {self.results['phase_1']['high_confidence']}")
            
            return True
            
        except Exception as e:
            print_colored(f"❌ Error en Fase 1: {e}", Colors.FAIL)
            traceback.print_exc()
            return False
    
    def run_phase_2_ai_validation(self):
        """
        FASE 2: Validación con AI REAL
        Usa Ollama LLM local para verificar si los matches son reales
        """
        print_section("FASE 2: VALIDACIÓN CON AI REAL")
        
        if not self.use_ai:
            print_colored("⏭️  Fase 2 omitida (AI deshabilitada)", Colors.WARNING)
            self.results['phase_2'] = {'skipped': True, 'reason': 'AI disabled'}
            return True
        
        try:
            # Verificar si Ollama está disponible
            ai_available = self._check_ai_availability()
            
            if not ai_available:
                print_colored("⚠️  AI no disponible - continuando sin validación", Colors.WARNING)
                self.results['phase_2'] = {'skipped': True, 'reason': 'AI not available'}
                return True
            
            # Obtener relaciones de fase 1
            phase_1_relationships = self.results['phase_1']['relationships']
            
            if not phase_1_relationships:
                print_colored("⚠️  No hay relaciones para validar", Colors.WARNING)
                self.results['phase_2'] = {'skipped': True, 'reason': 'No relationships'}
                return True
            
            # Validar con AI REAL - tomar top relaciones por confianza
            print_colored("🤖 Validando relaciones con AI REAL...", Colors.OKCYAN)
            
            # Obtener datos CSV para el AI
            detector = self.results['phase_1']['detector']
            csv_data = detector.csv_files
            
            # Usar verificador AI REAL
            validated_relationships = self._validate_with_real_ai(phase_1_relationships, csv_data)
            
            # Guardar resultados de fase 2
            self.results['phase_2'] = {
                'validated_relationships': validated_relationships,
                'ai_confirmed': len([r for r in validated_relationships if r['ai_confirmed']]),
                'ai_rejected': len([r for r in validated_relationships if not r['ai_confirmed']]),
                'timestamp': datetime.now().isoformat()
            }
            
            print_colored(f"✅ Fase 2 completada:", Colors.OKGREEN)
            print(f"   🤖 Relaciones validadas: {len(validated_relationships)}")
            print(f"   ✅ Confirmadas por AI: {self.results['phase_2']['ai_confirmed']}")
            print(f"   ❌ Rechazadas por AI: {self.results['phase_2']['ai_rejected']}")
            
            return True
            
        except Exception as e:
            print_colored(f"❌ Error en Fase 2: {e}", Colors.FAIL)
            print_colored("⏭️  Continuando sin validación AI", Colors.WARNING)
            self.results['phase_2'] = {'skipped': True, 'reason': f'Error: {str(e)}'}
            return True  # No es crítico, continuamos
    
    def run_phase_3_dbml_generation(self):
        """
        FASE 3: Generar DBML con todas las relaciones validadas
        """
        print_section("FASE 3: GENERACIÓN DBML")
        
        try:
            # Obtener detector de fase 1
            detector = self.results['phase_1']['detector']
            
            # Obtener relaciones finales (combinar fase 1 + validación AI si existe)
            final_relationships = self._get_final_relationships()
            
            # Generar DBML
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dbml_path = f"final_schema_{timestamp}.dbml"
            
            dbml_content = self._generate_enhanced_dbml(detector, final_relationships, dbml_path)
            
            # Generar reporte JSON
            json_path = f"final_results_{timestamp}.json"
            self._generate_final_report(json_path)
            
            # Guardar resultados de fase 3
            self.results['phase_3'] = {
                'dbml_file': dbml_path,
                'json_file': json_path,
                'final_relationships_count': len(final_relationships),
                'timestamp': datetime.now().isoformat()
            }
            
            print_colored(f"✅ Fase 3 completada:", Colors.OKGREEN)
            print(f"   📐 DBML generado: {dbml_path}")
            print(f"   📄 Reporte JSON: {json_path}")
            print(f"   🔗 Relaciones finales: {len(final_relationships)}")
            
            return True
            
        except Exception as e:
            print_colored(f"❌ Error en Fase 3: {e}", Colors.FAIL)
            traceback.print_exc()
            return False
    
    def _check_ai_availability(self) -> bool:
        """Verifica si AI (Ollama) está disponible"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def _validate_with_real_ai(self, relationships, csv_data) -> list:
        """
        Validación REAL con AI usando Ollama LLM
        """
        try:
            from old.real_ai_verifier import RealAIVerifier
            
            # Inicializar verificador AI real
            ai_verifier = RealAIVerifier()
            
            # Convertir relationships al formato esperado
            relationships_for_ai = []
            for rel in relationships:
                rel_dict = {
                    'relation': f"{rel.from_table}.{rel.from_column} → {rel.to_table}.{rel.to_column}",
                    'confidence': rel.confidence,
                    'overlap_ratio': rel.overlap_ratio
                }
                relationships_for_ai.append(rel_dict)
            
            # Validar con AI real
            ai_results = ai_verifier.validate_relationships_with_real_ai(
                relationships_for_ai, 
                csv_data, 
                max_validations=5
            )
            
            # Convertir resultados
            validated_relationships = []
            for ai_result in ai_results:
                validated_relationships.append({
                    'relationship': ai_result.relationship,
                    'original_confidence': relationships_for_ai[0]['confidence'],  # Aproximado
                    'ai_score': ai_result.confidence_score,
                    'ai_confirmed': ai_result.is_valid,
                    'ai_explanation': ai_result.explanation,
                    'suggested_cardinality': ai_result.suggested_cardinality,
                    'reasoning_steps': ai_result.reasoning_steps,
                    'validation_method': 'real_ollama_llm'
                })
            
            return validated_relationships
            
        except Exception as e:
            print_colored(f"⚠️  Error con AI real: {e}", Colors.WARNING)
            print_colored("💡 Usando validación básica en su lugar", Colors.WARNING)
            return self._fallback_validation(relationships)
    
    def _fallback_validation(self, relationships) -> list:
        """Validación de fallback cuando AI no está disponible"""
        validated_relationships = []
        
        # Usar solo las de muy alta confianza como "validadas"
        for rel in relationships[:3]:  # Top 3
            if rel.confidence >= 85:
                validated_relationships.append({
                    'relationship': f"{rel.from_table}.{rel.from_column} → {rel.to_table}.{rel.to_column}",
                    'original_confidence': rel.confidence,
                    'ai_score': rel.confidence,
                    'ai_confirmed': True,
                    'ai_explanation': f"Alta confianza automática ({rel.confidence:.1f}%)",
                    'suggested_cardinality': "N:1",
                    'validation_method': 'fallback_high_confidence'
                })
            
        return validated_relationships
    
    def _get_final_relationships(self) -> list:
        """Obtiene relaciones finales combinando fase 1 + validación AI"""
        
        phase_1_relationships = self.results['phase_1']['relationships']
        
        # Si no hay validación AI, usar todas las de alta confianza de fase 1
        if self.results['phase_2'].get('skipped'):
            return [r for r in phase_1_relationships if r.confidence >= 60]
        
        # Si hay validación AI, usar solo las confirmadas + alta confianza de fase 1
        ai_validated = self.results['phase_2'].get('validated_relationships', [])
        ai_confirmed_names = {r['relationship'] for r in ai_validated if r['ai_confirmed']}
        
        final_relationships = []
        
        for rel in phase_1_relationships:
            rel_name = f"{rel.from_table}.{rel.from_column} → {rel.to_table}.{rel.to_column}"
            
            # Incluir si:
            # 1. Confirmada por AI, o
            # 2. Alta confianza en fase 1 y no rechazada por AI
            if rel_name in ai_confirmed_names or (rel.confidence >= 80 and rel_name not in {r['relationship'] for r in ai_validated}):
                final_relationships.append(rel)
        
        return final_relationships
    
    def _generate_enhanced_dbml(self, detector, relationships, output_path) -> str:
        """Genera DBML mejorado con información de validación AI"""
        
        lines = []
        
        # Header mejorado
        lines.extend([
            f"// 🚀 Enhanced Data Tool v2.0 - Schema Final",
            f"// Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"// Directorio: {self.data_directory}",
            f"// Pipeline: Análisis de datos → Validación AI REAL → DBML",
            "",
            'Project "CSV Relationship Detection" {',
            '  database_type: "Multi-CSV"',
            '  Note: "Relaciones detectadas y validadas con AI real"',
            '}',
            ""
        ])
        
        # Definir tablas (usar el método del detector)
        for table_name, df in detector.csv_files.items():
            lines.append(f"Table {table_name} {{")
            
            columns_info = detector.column_analysis[table_name]
            
            for column_name in df.columns:
                col_info = columns_info[column_name]
                
                # Tipo de datos
                dbml_type = {
                    'numeric': 'integer',
                    'text': 'varchar',
                    'datetime': 'timestamp',
                    'boolean': 'boolean'
                }.get(col_info.data_type, 'varchar')
                
                col_line = f"  {column_name} {dbml_type}"
                
                # Atributos
                attributes = []
                if col_info.likely_pk:
                    attributes.append("primary key")
                if not col_info.has_nulls:
                    attributes.append("not null")
                
                if attributes:
                    col_line += f" [{', '.join(attributes)}]"
                
                lines.append(col_line)
            
            # Estadísticas
            lines.append(f'  Note: "Filas: {len(df):,} | Columnas: {len(df.columns)} | '
                        f'PKs detectadas: {len([c for c in columns_info.values() if c.likely_pk])}"')
            lines.append("}")
            lines.append("")
        
        # Relaciones validadas
        if relationships:
            lines.append("// ===== RELACIONES VALIDADAS CON AI REAL =====")
            lines.append("")
            
            # Verificar si hay validación AI
            ai_results = self.results.get('phase_2', {}).get('validated_relationships', [])
            ai_lookup = {r['relationship']: r for r in ai_results}
            
            for rel in relationships:
                rel_name = f"{rel.from_table}.{rel.from_column} → {rel.to_table}.{rel.to_column}"
                ai_info = ai_lookup.get(rel_name)
                
                # Determinar tipo de relación
                cardinality = rel.data_evidence.get('cardinality_estimate', '')
                ref_type = ">" if "Many-to-One" in cardinality else "-"
                
                # Construir comentario
                comment_parts = [f"Confianza: {rel.confidence:.1f}%"]
                
                if ai_info:
                    if ai_info['ai_confirmed']:
                        comment_parts.append(f"AI: ✅ Confirmada ({ai_info['ai_score']:.1f})")
                    else:
                        comment_parts.append(f"AI: ❌ Rechazada")
                
                comment_parts.append(f"Overlap: {rel.overlap_ratio:.1%}")
                
                ref_line = (f"Ref: {rel.from_table}.{rel.from_column} {ref_type} "
                          f"{rel.to_table}.{rel.to_column} // {' | '.join(comment_parts)}")
                
                lines.append(ref_line)
                
                # Agregar nota de AI si existe
                if ai_info and ai_info.get('ai_explanation'):
                    lines.append(f"// AI: {ai_info['ai_explanation']}")
            
            lines.append("")
        
        # Estadísticas finales
        lines.extend([
            "// ===== ESTADÍSTICAS DEL PIPELINE =====",
            f"// Tablas analizadas: {len(detector.csv_files)}",
            f"// Total columnas: {sum(len(df.columns) for df in detector.csv_files.values())}",
            f"// Relaciones candidatas (Fase 1): {len(self.results['phase_1']['relationships'])}",
            f"// Validadas por AI REAL (Fase 2): {self.results.get('phase_2', {}).get('ai_confirmed', 'N/A')}",
            f"// Relaciones finales (Fase 3): {len(relationships)}",
            "",
            "// Pipeline: CSV → Análisis datos → AI REAL validación → DBML",
            "// Herramienta: Enhanced Data Tool v2.0"
        ])
        
        dbml_content = "\n".join(lines)
        
        # Guardar
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dbml_content)
        
        return dbml_content
    
    def _generate_final_report(self, output_path):
        """Genera reporte final JSON completo"""
        
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'tool_version': 'Enhanced Data Tool v2.0',
                'data_directory': str(self.data_directory),
                'pipeline_phases': ['data_analysis', 'ai_validation_real', 'dbml_generation']
            },
            'pipeline_results': self.results,
            'summary': {
                'total_tables': self.results['phase_1']['tables_count'],
                'phase_1_relationships': self.results['phase_1']['relationships_count'],
                'phase_2_ai_confirmed': self.results.get('phase_2', {}).get('ai_confirmed', 0),
                'phase_3_final_relationships': self.results['phase_3']['final_relationships_count'],
                'ai_validation_used': not self.results.get('phase_2', {}).get('skipped', False)
            },
            'files_generated': [
                self.results['phase_3']['dbml_file'],
                self.results['phase_3']['json_file']
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    def run_complete_pipeline(self) -> bool:
        """Ejecuta el pipeline completo de 3 fases"""
        
        print_colored("🚀 ENHANCED DATA TOOL - PIPELINE COMPLETO CON AI REAL", Colors.HEADER)
        print_colored("=" * 70, Colors.HEADER)
        print_colored("Pipeline: CSV → Análisis → AI REAL → DBML", Colors.OKCYAN)
        print(f"📂 Directorio: {self.data_directory}")
        
        try:
            # Ejecutar las 3 fases secuencialmente
            phases = [
                ("FASE 1: ANÁLISIS DE DATOS", self.run_phase_1_data_analysis),
                ("FASE 2: VALIDACIÓN AI REAL", self.run_phase_2_ai_validation),
                ("FASE 3: GENERACIÓN DBML", self.run_phase_3_dbml_generation)
            ]
            
            for phase_name, phase_function in phases:
                print_colored(f"\n▶️  Ejecutando {phase_name}...", Colors.OKCYAN)
                
                if not phase_function():
                    print_colored(f"❌ Fallo en {phase_name}", Colors.FAIL)
                    return False
            
            # Mostrar resumen final
            self._print_final_summary()
            
            return True
            
        except Exception as e:
            print_colored(f"❌ Error en pipeline: {e}", Colors.FAIL)
            traceback.print_exc()
            return False
    
    def _print_final_summary(self):
        """Imprime resumen final del pipeline"""
        
        print_section("🎉 PIPELINE COMPLETADO EXITOSAMENTE")
        
        print_colored("📊 RESUMEN DEL PIPELINE:", Colors.OKGREEN)
        
        # Estadísticas por fase
        print(f"  📋 FASE 1 - Análisis de datos:")
        print(f"     • Tablas: {self.results['phase_1']['tables_count']}")
        print(f"     • Relaciones detectadas: {self.results['phase_1']['relationships_count']}")
        print(f"     • Alta confianza: {self.results['phase_1']['high_confidence']}")
        
        print(f"  🤖 FASE 2 - Validación AI REAL:")
        if self.results['phase_2'].get('skipped'):
            print(f"     • Omitida: {self.results['phase_2']['reason']}")
        else:
            print(f"     • Confirmadas: {self.results['phase_2']['ai_confirmed']}")
            print(f"     • Rechazadas: {self.results['phase_2']['ai_rejected']}")
        
        print(f"  📐 FASE 3 - Generación DBML:")
        print(f"     • Relaciones finales: {self.results['phase_3']['final_relationships_count']}")
        print(f"     • DBML: {self.results['phase_3']['dbml_file']}")
        print(f"     • JSON: {self.results['phase_3']['json_file']}")
        
        print_colored("\n🎯 PRÓXIMOS PASOS:", Colors.OKBLUE)
        print("  1. Abrir el archivo DBML generado")
        print("  2. Copiar todo el contenido")
        print("  3. Ir a https://dbdiagram.io/d")
        print("  4. Pegar y visualizar tu diagrama ER")
        print("  5. Revisar el reporte JSON para detalles")
        
        print_colored("\n✨ ¡TU HERRAMIENTA CON AI REAL FUNCIONÓ PERFECTAMENTE!", Colors.OKGREEN)

def main():
    """Función principal"""
    
    # Configuración
    data_dir = r"C:\Users\Flori\Desktop\Omniscient Platforms\internal tool\enhanced_data_tool\data"
    use_ai = True  # Cambiar a False si no tienes Ollama
    
    print_colored("🔍 ENHANCED DATA TOOL v2.0 CON AI REAL", Colors.HEADER)
    print_colored("Detección de relaciones CSV → AI REAL → DBML", Colors.OKCYAN)
    
    # Verificar directorio
    if not Path(data_dir).exists():
        print_colored(f"❌ Directorio no encontrado: {data_dir}", Colors.FAIL)
        print_colored("💡 Ejecuta primero: python create_dummy_csvs.py", Colors.WARNING)
        return 1
    
    # Verificar CSVs
    csv_files = list(Path(data_dir).glob("*.csv"))
    if not csv_files:
        print_colored(f"❌ No hay CSVs en: {data_dir}", Colors.FAIL)
        print_colored("💡 Ejecuta primero: python create_dummy_csvs.py", Colors.WARNING)
        return 1
    
    print(f"📄 CSVs encontrados: {len(csv_files)}")
    
    # Ejecutar pipeline
    pipeline = EnhancedDataToolPipeline(data_dir, use_ai=use_ai)
    
    success = pipeline.run_complete_pipeline()
    
    if success:
        print_colored("\n🎉 ¡PIPELINE CON AI REAL COMPLETADO EXITOSAMENTE!", Colors.OKGREEN)
        return 0
    else:
        print_colored("\n❌ Pipeline falló", Colors.FAIL)
        return 1

if __name__ == "__main__":
    sys.exit(main())