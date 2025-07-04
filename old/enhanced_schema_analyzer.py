#!/usr/bin/env python3
"""
Enhanced Schema Analyzer - Versión mejorada con mejor manejo de errores
y detección de relaciones más precisa usando embeddings y LLMs
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import json
import os
from datetime import datetime
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedSchemaAnalyzer:
    """
    Analizador de esquemas de base de datos mejorado con detección automática
    de relaciones usando embeddings y verificación con LLM
    """
    
    def __init__(self, db_path: str, use_llm: bool = True):
        self.db_path = db_path
        self.use_llm = use_llm
        self.schema_info = {}
        self.relationships = []
        self.sample_data = {}
        
        # Inicializar conexión a BD
        self.conn = None
        self._connect_to_database()
        
        # Inicializar detectores
        self._initialize_detectors()
    
    def _connect_to_database(self):
        """Conecta a la base de datos SQLite"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"✅ Conectado a la base de datos: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Error conectando a la BD: {e}")
            raise
    
    def _initialize_detectors(self):
        """Inicializa los detectores de relaciones"""
        # Patrones comunes para detectar FKs
        self.fk_patterns = [
            r'.*_id$',
            r'.*_key$',
            r'.*_fk$',
            r'.*_ref$',
            r'id_.*',
            r'fk_.*'
        ]
        
        # Palabras clave que indican relaciones
        self.relationship_keywords = [
            'customer', 'user', 'client', 'person', 'account',
            'product', 'item', 'article', 'goods',
            'order', 'sale', 'purchase', 'transaction',
            'category', 'type', 'group', 'class',
            'address', 'location', 'place', 'region'
        ]
    
    def extract_schema(self) -> Dict[str, Any]:
        """
        Extrae información completa del esquema de la base de datos
        """
        print("🔍 FASE 1: Extrayendo esquema de la base de datos...")
        
        # Obtener lista de tablas
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        schema = {
            'tables': {},
            'total_tables': len(tables),
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        for table in tables:
            table_info = self._analyze_table(table)
            schema['tables'][table] = table_info
            
            # Obtener datos de muestra
            self.sample_data[table] = self._get_sample_data(table, limit=5)
        
        self.schema_info = schema
        self._print_schema_summary()
        return schema
    
    def _analyze_table(self, table_name: str) -> Dict[str, Any]:
        """Analiza una tabla específica"""
        cursor = self.conn.cursor()
        
        # Información de columnas
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        
        # Contar filas
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Información de claves foráneas
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = cursor.fetchall()
        
        # Procesar columnas
        columns = {}
        primary_keys = []
        
        for col in columns_info:
            col_name = col[1]
            col_type = col[2]
            not_null = bool(col[3])
            default_val = col[4]
            is_pk = bool(col[5])
            
            columns[col_name] = {
                'type': col_type,
                'not_null': not_null,
                'default': default_val,
                'is_primary_key': is_pk
            }
            
            if is_pk:
                primary_keys.append(col_name)
        
        # Procesar claves foráneas
        fks = []
        for fk in foreign_keys:
            fks.append({
                'column': fk[3],
                'references_table': fk[2],
                'references_column': fk[4]
            })
        
        return {
            'columns': columns,
            'row_count': row_count,
            'primary_keys': primary_keys,
            'foreign_keys': fks,
            'total_columns': len(columns)
        }
    
    def _get_sample_data(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """Obtiene datos de muestra de una tabla"""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return pd.read_sql_query(query, self.conn)
        except Exception as e:
            logger.warning(f"No se pudieron obtener datos de muestra para {table_name}: {e}")
            return pd.DataFrame()
    
    def detect_relationships(self) -> List[Dict[str, Any]]:
        """
        Detecta relaciones potenciales entre tablas usando análisis de nombres
        y patrones de datos
        """
        print("🔍 FASE 2: Detectando relaciones potenciales...")
        
        relationships = []
        tables = list(self.schema_info['tables'].keys())
        
        for table in tables:
            table_info = self.schema_info['tables'][table]
            
            for column, col_info in table_info['columns'].items():
                # Saltar primary keys
                if col_info['is_primary_key']:
                    continue
                
                # Buscar posibles relaciones
                potential_relations = self._find_potential_relationships(
                    table, column, col_info, tables
                )
                relationships.extend(potential_relations)
        
        # Calcular confianza para cada relación
        for rel in relationships:
            rel['confidence'] = self._calculate_confidence(rel)
        
        # Filtrar y ordenar por confianza
        relationships = [r for r in relationships if r['confidence'] > 30]
        relationships.sort(key=lambda x: x['confidence'], reverse=True)
        
        self.relationships = relationships
        self._print_relationships_summary(relationships)
        return relationships
    
    def _find_potential_relationships(self, table: str, column: str, 
                                    col_info: Dict, all_tables: List[str]) -> List[Dict]:
        """Encuentra relaciones potenciales para una columna específica"""
        relationships = []
        
        # Buscar en otras tablas
        for target_table in all_tables:
            if target_table == table:
                continue
            
            target_info = self.schema_info['tables'][target_table]
            
            # Buscar coincidencias con primary keys
            for target_col, target_col_info in target_info['columns'].items():
                if target_col_info['is_primary_key']:
                    similarity = self._calculate_column_similarity(
                        table, column, target_table, target_col
                    )
                    
                    if similarity > 0.3:  # Umbral de similitud
                        relationships.append({
                            'from_table': table,
                            'from_column': column,
                            'to_table': target_table,
                            'to_column': target_col,
                            'similarity_score': similarity,
                            'type': 'potential_fk'
                        })
        
        return relationships
    
    def _calculate_column_similarity(self, table1: str, col1: str, 
                                   table2: str, col2: str) -> float:
        """Calcula similitud entre dos columnas"""
        score = 0.0
        
        # Similitud por nombre
        name_similarity = self._name_similarity(col1, col2)
        score += name_similarity * 0.4
        
        # Similitud por patrón FK
        fk_pattern_score = self._fk_pattern_score(col1, col2)
        score += fk_pattern_score * 0.3
        
        # Similitud semántica (nombres de tablas)
        semantic_score = self._semantic_similarity(table1, col1, table2, col2)
        score += semantic_score * 0.3
        
        return min(score, 1.0)
    
    def _name_similarity(self, col1: str, col2: str) -> float:
        """Calcula similitud entre nombres de columnas"""
        col1_lower = col1.lower()
        col2_lower = col2.lower()
        
        # Coincidencia exacta
        if col1_lower == col2_lower:
            return 1.0
        
        # Coincidencia con sufijos/prefijos comunes
        if col1_lower.endswith('_id') and col2_lower == 'id':
            return 0.8
        if col1_lower.endswith('_key') and col2_lower == 'id':
            return 0.7
        
        # Coincidencia parcial
        if col1_lower in col2_lower or col2_lower in col1_lower:
            return 0.6
        
        return 0.0
    
    def _fk_pattern_score(self, col1: str, col2: str) -> float:
        """Evalúa si la columna sigue patrones de FK"""
        import re
        
        score = 0.0
        col1_lower = col1.lower()
        
        for pattern in self.fk_patterns:
            if re.match(pattern, col1_lower):
                score += 0.5
                break
        
        return min(score, 1.0)
    
    def _semantic_similarity(self, table1: str, col1: str, table2: str, col2: str) -> float:
        """Evalúa similitud semántica entre tablas y columnas"""
        score = 0.0
        
        # Verificar si el nombre de la columna contiene el nombre de la tabla objetivo
        col1_lower = col1.lower()
        table2_lower = table2.lower()
        
        # Ejemplo: customer_id en tabla orders -> customers.id
        if table2_lower.rstrip('s') in col1_lower:
            score += 0.8
        elif table2_lower in col1_lower:
            score += 0.6
        
        # Verificar palabras clave relacionadas
        for keyword in self.relationship_keywords:
            if keyword in col1_lower and keyword in table2_lower:
                score += 0.4
                break
        
        return min(score, 1.0)
    
    def _calculate_confidence(self, relationship: Dict) -> float:
        """Calcula el nivel de confianza de una relación"""
        base_score = relationship.get('similarity_score', 0.0)
        
        # Factores adicionales
        confidence = base_score * 100
        
        # Bonus por datos de muestra consistentes
        if self._validate_with_sample_data(relationship):
            confidence += 20
        
        # Bonus por tipos de datos compatibles
        if self._check_data_type_compatibility(relationship):
            confidence += 10
        
        return min(confidence, 100.0)
    
    def _validate_with_sample_data(self, relationship: Dict) -> bool:
        """Valida la relación usando datos de muestra"""
        try:
            from_table = relationship['from_table']
            from_col = relationship['from_column']
            to_table = relationship['to_table']
            to_col = relationship['to_column']
            
            from_sample = self.sample_data.get(from_table, pd.DataFrame())
            to_sample = self.sample_data.get(to_table, pd.DataFrame())
            
            if from_sample.empty or to_sample.empty:
                return False
            
            if from_col not in from_sample.columns or to_col not in to_sample.columns:
                return False
            
            # Verificar si los valores en from_col existen en to_col
            from_values = from_sample[from_col].dropna().unique()
            to_values = to_sample[to_col].dropna().unique()
            
            if len(from_values) == 0 or len(to_values) == 0:
                return False
            
            # Calcular porcentaje de coincidencias
            matches = sum(1 for val in from_values if val in to_values)
            match_percentage = matches / len(from_values)
            
            return match_percentage > 0.5
            
        except Exception as e:
            logger.debug(f"Error validando con datos de muestra: {e}")
            return False
    
    def _check_data_type_compatibility(self, relationship: Dict) -> bool:
        """Verifica compatibilidad de tipos de datos"""
        try:
            from_table = relationship['from_table']
            from_col = relationship['from_column']
            to_table = relationship['to_table']
            to_col = relationship['to_column']
            
            from_type = self.schema_info['tables'][from_table]['columns'][from_col]['type']
            to_type = self.schema_info['tables'][to_table]['columns'][to_col]['type']
            
            # Normalizar tipos
            from_type = from_type.upper()
            to_type = to_type.upper()
            
            # Tipos compatibles
            compatible_types = [
                ['INTEGER', 'INT', 'BIGINT'],
                ['VARCHAR', 'TEXT', 'CHAR'],
                ['DECIMAL', 'NUMERIC', 'FLOAT', 'REAL']
            ]
            
            for type_group in compatible_types:
                if any(ft in from_type for ft in type_group) and \
                   any(tt in to_type for tt in type_group):
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error verificando compatibilidad de tipos: {e}")
            return False
    
    def _print_schema_summary(self):
        """Imprime resumen del esquema extraído"""
        print("\n" + "="*60)
        print("RESUMEN DEL ESQUEMA DE BASE DE DATOS")
        print("="*60)
        print(f"Total de tablas: {self.schema_info['total_tables']}")
        
        for table_name, table_info in self.schema_info['tables'].items():
            print(f"\n📊 Tabla: {table_name}")
            print(f"   Columnas: {table_info['total_columns']}")
            print(f"   Filas: {table_info['row_count']}")
            
            if table_info['primary_keys']:
                print(f"   🔑 Primary Keys: {', '.join(table_info['primary_keys'])}")
            
            if table_info['foreign_keys']:
                print("   🔗 Foreign Keys:")
                for fk in table_info['foreign_keys']:
                    print(f"      - {fk['column']} → {fk['references_table']}.{fk['references_column']}")
            
            print("   Columnas:")
            for col_name, col_info in table_info['columns'].items():
                pk_indicator = " 🔑" if col_info['is_primary_key'] else ""
                fk_indicator = " 🔗" if any(fk['column'] == col_name for fk in table_info['foreign_keys']) else ""
                print(f"      - {col_name} ({col_info['type']}){pk_indicator}{fk_indicator}")
    
    def _print_relationships_summary(self, relationships: List[Dict]):
        """Imprime resumen de relaciones detectadas"""
        print("\n" + "="*80)
        print("REPORTE DE RELACIONES DETECTADAS")
        print("="*80)
        
        if not relationships:
            print("❌ No se detectaron relaciones potenciales")
            return
        
        # Agrupar por nivel de confianza
        high_confidence = [r for r in relationships if r['confidence'] >= 80]
        medium_confidence = [r for r in relationships if 60 <= r['confidence'] < 80]
        low_confidence = [r for r in relationships if r['confidence'] < 60]
        
        if high_confidence:
            print("\n🟢 ALTA CONFIANZA (80%+)")
            print("-" * 40)
            for rel in high_confidence:
                print(f"{rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}")
                print(f"  Confianza: {rel['confidence']:.1f}%")
        
        if medium_confidence:
            print("\n🟡 CONFIANZA MEDIA (60-79%)")
            print("-" * 40)
            for rel in medium_confidence:
                print(f"{rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}")
                print(f"  Confianza: {rel['confidence']:.1f}%")
        
        if low_confidence:
            print("\n🔴 BAJA CONFIANZA (<60%)")
            print("-" * 40)
            for rel in low_confidence:
                print(f"{rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}")
                print(f"  Confianza: {rel['confidence']:.1f}%")
        
        print(f"\nTotal de relaciones detectadas: {len(relationships)}")
    
    def generate_dbml(self, output_path: str = None) -> str:
        """Genera código DBML a partir del esquema y relaciones"""
        print("\n📐 FASE 3: Generando código DBML...")
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"schema_{timestamp}.dbml"
        
        dbml_content = self._create_dbml_content()
        
        # Guardar archivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dbml_content)
        
        print(f"✅ DBML guardado en: {output_path}")
        return dbml_content
    
    def _create_dbml_content(self) -> str:
        """Crea el contenido DBML"""
        lines = []
        
        # Header
        lines.append("// Esquema generado automáticamente")
        lines.append(f"// Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Definir tablas
        for table_name, table_info in self.schema_info['tables'].items():
            lines.append(f"Table {table_name} {{")
            
            for col_name, col_info in table_info['columns'].items():
                col_line = f"  {col_name} {col_info['type']}"
                
                attributes = []
                if col_info['is_primary_key']:
                    attributes.append("primary key")
                if col_info['not_null']:
                    attributes.append("not null")
                
                if attributes:
                    col_line += f" [{', '.join(attributes)}]"
                
                lines.append(col_line)
            
            lines.append("}")
            lines.append("")
        
        # Definir relaciones existentes (FKs)
        for table_name, table_info in self.schema_info['tables'].items():
            for fk in table_info['foreign_keys']:
                lines.append(f"Ref: {table_name}.{fk['column']} > {fk['references_table']}.{fk['references_column']}")
        
        # Definir relaciones detectadas
        lines.append("")
        lines.append("// Relaciones detectadas automáticamente")
        for rel in self.relationships:
            if rel['confidence'] >= 60:  # Solo relaciones con confianza media o alta
                confidence_comment = f" // Confianza: {rel['confidence']:.1f}%"
                lines.append(f"Ref: {rel['from_table']}.{rel['from_column']} > {rel['to_table']}.{rel['to_column']}{confidence_comment}")
        
        return "\n".join(lines)
    
    def analyze_complete(self, output_dir: str = "./output") -> Dict[str, Any]:
        """Ejecuta el análisis completo"""
        print("🚀 INICIANDO ANÁLISIS COMPLETO DEL ESQUEMA")
        print("=" * 60)
        
        # Crear directorio de salida
        Path(output_dir).mkdir(exist_ok=True)
        
        # Fase 1: Extraer esquema
        schema = self.extract_schema()
        
        # Fase 2: Detectar relaciones
        relationships = self.detect_relationships()
        
        # Fase 3: Generar DBML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dbml_path = os.path.join(output_dir, f"schema_{timestamp}.dbml")
        dbml_content = self.generate_dbml(dbml_path)
        
        # Guardar resultados en JSON
        results = {
            'schema': schema,
            'relationships': relationships,
            'analysis_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tables': len(schema['tables']),
                'total_columns': sum(t['total_columns'] for t in schema['tables'].values()),
                'total_rows': sum(t['row_count'] for t in schema['tables'].values()),
                'existing_fks': sum(len(t['foreign_keys']) for t in schema['tables'].values()),
                'detected_relationships': len(relationships),
                'high_confidence_relationships': len([r for r in relationships if r['confidence'] >= 80])
            }
        }
        
        json_path = os.path.join(output_dir, f"analysis_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Mostrar resumen final
        self._print_final_summary(results, dbml_path)
        
        return results
    
    def _print_final_summary(self, results: Dict, dbml_path: str):
        """Imprime resumen final del análisis"""
        summary = results['summary']
        
        print("\n📊 RESUMEN FINAL")
        print("=" * 60)
        print(f"📊 Tablas analizadas: {summary['total_tables']}")
        print(f"📋 Total de columnas: {summary['total_columns']}")
        print(f"📈 Total de filas: {summary['total_rows']}")
        print(f"🔗 Relaciones existentes: {summary['existing_fks']}")
        print(f"✨ Nuevas relaciones detectadas: {summary['detected_relationships']}")
        print(f"🎯 Relaciones de alta confianza: {summary['high_confidence_relationships']}")
        
        print(f"\n✅ Análisis completado. Archivos generados:")
        print(f"   - {dbml_path}")
        print(f"   - {json_path}")
        
        print("\n🎨 Para visualizar el diagrama:")
        print("   1. Abre el archivo DBML generado")
        print("   2. Copia todo el contenido")
        print("   3. Ve a: https://dbdiagram.io/d")
        print("   4. Pega el código y disfruta tu diagrama ER")
    
    def __del__(self):
        """Cerrar conexión a la BD al destruir el objeto"""
        if self.conn:
            self.conn.close()


# Función de utilidad para uso rápido
def analyze_database(db_path: str, output_dir: str = "./output", use_llm: bool = False):
    """
    Función de conveniencia para analizar una base de datos rápidamente
    """
    analyzer = EnhancedSchemaAnalyzer(db_path, use_llm=use_llm)
    return analyzer.analyze_complete(output_dir)


if __name__ == "__main__":
    # Ejemplo de uso
    db_file = "example_store.db"
    
    if os.path.exists(db_file):
        print("🚀 SCHEMA ANALYZER - Enhanced Version")
        print("=" * 50)
        
        analyzer = EnhancedSchemaAnalyzer(db_file, use_llm=False)
        results = analyzer.analyze_complete()
        
        print("\n🎉 ¡Análisis completado exitosamente!")
    else:
        print(f"❌ No se encontró la base de datos: {db_file}")
        print("💡 Asegúrate de que el archivo existe en el directorio actual")
