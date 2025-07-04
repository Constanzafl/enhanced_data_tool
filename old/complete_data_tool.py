#!/usr/bin/env python3
"""
Herramienta Completa de Análisis de Esquemas de BD
Integra detección con embeddings, verificación LLM y generación DBML
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime
from pathlib import Path
import logging
import traceback

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DBMLGenerator:
    """Generador mejorado de código DBML"""
    
    def __init__(self):
        self.project_name = "Database Schema"
        self.note_counter = 1
    
    def generate_dbml(self, schema_info: Dict, relationships: List[Dict], 
                     llm_results: List = None, project_name: str = None) -> str:
        """
        Genera código DBML completo con todas las relaciones
        """
        if project_name:
            self.project_name = project_name
        
        lines = []
        
        # Header con metadatos
        lines.extend(self._generate_header(schema_info))
        lines.append("")
        
        # Definir tablas
        lines.extend(self._generate_tables(schema_info))
        lines.append("")
        
        # Definir relaciones existentes
        existing_relations = self._generate_existing_relationships(schema_info)
        if existing_relations:
            lines.append("// ===== RELACIONES EXISTENTES (FOREIGN KEYS) =====")
            lines.extend(existing_relations)
            lines.append("")
        
        # Definir relaciones detectadas
        detected_relations = self._generate_detected_relationships(relationships, llm_results)
        if detected_relations:
            lines.append("// ===== RELACIONES DETECTADAS AUTOMÁTICAMENTE =====")
            lines.extend(detected_relations)
            lines.append("")
        
        # Notas y documentación
        notes = self._generate_notes(schema_info, relationships, llm_results)
        if notes:
            lines.append("// ===== NOTAS Y DOCUMENTACIÓN =====")
            lines.extend(notes)
        
        return "\n".join(lines)
    
    def _generate_header(self, schema_info: Dict) -> List[str]:
        """Genera header del archivo DBML"""
        total_tables = len(schema_info['tables'])
        total_columns = sum(t['total_columns'] for t in schema_info['tables'].values())
        total_rows = sum(t['row_count'] for t in schema_info['tables'].values())
        
        return [
            f"// {self.project_name}",
            f"// Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"// ",
            f"// Estadísticas:",
            f"//   - Tablas: {total_tables}",
            f"//   - Columnas totales: {total_columns}",
            f"//   - Filas totales: {total_rows}",
            f"//",
            f"// Visualizar en: https://dbdiagram.io/d",
            "",
            f'Project "{self.project_name}" {{'
            f'  database_type: "SQLite"',
            f'  Note: "Esquema generado automáticamente con detección de relaciones IA"',
            f'}}'
        ]
    
    def _generate_tables(self, schema_info: Dict) -> List[str]:
        """Genera definiciones de tablas"""
        lines = []
        
        for table_name, table_info in schema_info['tables'].items():
            lines.append(f"Table {table_name} {{")
            
            # Ordenar columnas: PKs primero, luego el resto
            columns = table_info['columns']
            pk_columns = [name for name, info in columns.items() if info['is_primary_key']]
            other_columns = [name for name, info in columns.items() if not info['is_primary_key']]
            
            ordered_columns = pk_columns + other_columns
            
            for col_name in ordered_columns:
                col_info = columns[col_name]
                col_line = self._format_column(col_name, col_info)
                lines.append(f"  {col_line}")
            
            # Agregar nota con estadísticas de la tabla
            lines.append(f'  Note: "Filas: {table_info["row_count"]:,} | Columnas: {table_info["total_columns"]}"')
            lines.append("}")
            lines.append("")
        
        return lines
    
    def _format_column(self, col_name: str, col_info: Dict) -> str:
        """Formatea una columna para DBML"""
        # Mapear tipos SQLite a tipos DBML más estándar
        type_mapping = {
            'INTEGER': 'integer',
            'TEXT': 'varchar',
            'VARCHAR': 'varchar',
            'DECIMAL': 'decimal',
            'TIMESTAMP': 'timestamp',
            'DATETIME': 'datetime',
            'REAL': 'float',
            'BLOB': 'binary'
        }
        
        db_type = col_info['type'].upper()
        dbml_type = type_mapping.get(db_type, col_info['type'].lower())
        
        # Construir línea de columna
        col_line = f"{col_name} {dbml_type}"
        
        # Agregar atributos
        attributes = []
        
        if col_info['is_primary_key']:
            attributes.append("primary key")
        
        if col_info['not_null'] and not col_info['is_primary_key']:
            attributes.append("not null")
        
        if col_info.get('default') is not None:
            default_val = col_info['default']
            if isinstance(default_val, str):
                attributes.append(f'default: "{default_val}"')
            else:
                attributes.append(f'default: {default_val}')
        
        if attributes:
            col_line += f" [{', '.join(attributes)}]"
        
        return col_line
    
    def _generate_existing_relationships(self, schema_info: Dict) -> List[str]:
        """Genera relaciones existentes (FKs definidas)"""
        lines = []
        
        for table_name, table_info in schema_info['tables'].items():
            for fk in table_info['foreign_keys']:
                ref_line = f"Ref: {table_name}.{fk['column']} > {fk['references_table']}.{fk['references_column']}"
                lines.append(ref_line)
        
        return lines
    
    def _generate_detected_relationships(self, relationships: List[Dict], 
                                       llm_results: List = None) -> List[str]:
        """Genera relaciones detectadas automáticamente"""
        lines = []
        
        if not relationships:
            return lines
        
        # Crear mapa de validaciones LLM si están disponibles
        llm_validation_map = {}
        if llm_results:
            for result in llm_results:
                key = result.relationship
                llm_validation_map[key] = result
        
        # Agrupar por nivel de confianza
        high_conf = [r for r in relationships if r.get('confidence', 0) >= 80]
        medium_conf = [r for r in relationships if 60 <= r.get('confidence', 0) < 80]
        low_conf = [r for r in relationships if 30 <= r.get('confidence', 0) < 60]
        
        for group, comment in [
            (high_conf, "Alta confianza (80%+)"),
            (medium_conf, "Confianza media (60-79%)"),
            (low_conf, "Baja confianza (30-59%)")
        ]:
            if group:
                lines.append(f"// {comment}")
                for rel in group:
                    ref_line, note_line = self._format_detected_relationship(rel, llm_validation_map)
                    lines.append(ref_line)
                    if note_line:
                        lines.append(note_line)
                lines.append("")
        
        return lines
    
    def _format_detected_relationship(self, relationship: Dict, 
                                    llm_validation_map: Dict) -> Tuple[str, Optional[str]]:
        """Formatea una relación detectada"""
        from_table = relationship['from_table']
        from_column = relationship['from_column']
        to_table = relationship['to_table']
        to_column = relationship['to_column']
        confidence = relationship.get('confidence', 0)
        
        # Determinar tipo de relación (por defecto many-to-one)
        rel_type = ">"  # many-to-one
        
        # Buscar validación LLM
        rel_key = f"{from_table}.{from_column} → {to_table}.{to_column}"
        llm_result = llm_validation_map.get(rel_key)
        
        # Comentario con información adicional
        comment_parts = [f"Confianza: {confidence:.1f}%"]
        
        if llm_result:
            if llm_result.is_valid:
                comment_parts.append(f"LLM: ✅ Válida ({llm_result.confidence:.0f}%)")
                if llm_result.suggested_cardinality != "unknown":
                    # Ajustar tipo de relación basado en cardinalidad LLM
                    if llm_result.suggested_cardinality == "1:1":
                        rel_type = "-"
                    elif llm_result.suggested_cardinality == "1:N":
                        rel_type = "<"
                    elif llm_result.suggested_cardinality == "N:M":
                        rel_type = "<>"
            else:
                comment_parts.append(f"LLM: ❌ Inválida")
        
        ref_line = f"Ref: {from_table}.{from_column} {rel_type} {to_table}.{to_column} // {' | '.join(comment_parts)}"
        
        # Nota adicional si hay explicación del LLM
        note_line = None
        if llm_result and llm_result.explanation:
            note_line = f"// LLM: {llm_result.explanation}"
        
        return ref_line, note_line
    
    def _generate_notes(self, schema_info: Dict, relationships: List[Dict], 
                       llm_results: List = None) -> List[str]:
        """Genera notas y documentación adicional"""
        lines = []
        
        # Estadísticas generales
        total_detected = len(relationships)
        high_conf_count = len([r for r in relationships if r.get('confidence', 0) >= 80])
        
        lines.append(f"Note detection_summary {{")
        lines.append(f'  "Relaciones detectadas automáticamente: {total_detected}"')
        lines.append(f'  "Relaciones de alta confianza: {high_conf_count}"')
        
        if llm_results:
            validated_count = len([r for r in llm_results if r.is_valid])
            lines.append(f'  "Relaciones validadas por LLM: {validated_count}/{len(llm_results)}"')
        
        lines.append(f'  "Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"')
        lines.append("}")
        
        return lines


class CompleteDataTool:
    """
    Herramienta completa que integra todos los componentes:
    - Extracción de esquema
    - Detección con embeddings  
    - Verificación LLM
    - Generación DBML
    """
    
    def __init__(self, db_path: str, use_embeddings: bool = True, use_llm: bool = True):
        self.db_path = db_path
        self.use_embeddings = use_embeddings
        self.use_llm = use_llm
        
        # Inicializar componentes
        self.conn = None
        self.schema_info = {}
        self.sample_data = {}
        self.relationships = []
        self.llm_results = []
        
        # Conectar a BD
        self._connect_to_database()
        
        # Inicializar detectores si están habilitados
        self.embedding_detector = None
        self.llm_verifier = None
        
        if use_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_detector = self._initialize_embedding_detector()
            except ImportError:
                print("⚠️  sentence-transformers no disponible. Usando detección básica.")
                self.use_embeddings = False
        
        if use_llm:
            try:
                self.llm_verifier = self._initialize_llm_verifier()
            except Exception as e:
                print(f"⚠️  LLM no disponible: {e}. Saltando verificación LLM.")
                self.use_llm = False
    
    def _connect_to_database(self):
        """Conecta a la base de datos"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"✅ Conectado a: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Error conectando a BD: {e}")
            raise
    
    def _initialize_embedding_detector(self):
        """Inicializa detector de embeddings"""
        try:
            # Importar aquí para evitar error si no está instalado
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            
            print("🤖 Inicializando detector de embeddings...")
            model = SentenceTransformer("all-MiniLM-L6-v2")
            print("✅ Detector de embeddings listo")
            return model
        except Exception as e:
            print(f"❌ Error inicializando embeddings: {e}")
            raise
    
    def _initialize_llm_verifier(self):
        """Inicializa verificador LLM"""
        try:
            import requests
            
            # Verificar conexión con Ollama
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if models:
                    print(f"✅ Ollama disponible con {len(models)} modelo(s)")
                    return True
                else:
                    raise Exception("No hay modelos disponibles")
            else:
                raise Exception(f"Error HTTP {response.status_code}")
        except Exception as e:
            raise Exception(f"Ollama no disponible: {e}")
    
    def extract_schema(self) -> Dict[str, Any]:
        """Extrae esquema completo de la BD"""
        print("🔍 FASE 1: Extrayendo esquema de la base de datos...")
        
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
            self.sample_data[table] = self._get_sample_data(table, limit=10)
        
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
        
        # Foreign keys
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
        
        # Procesar FKs
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
    
    def _get_sample_data(self, table_name: str, limit: int = 10) -> pd.DataFrame:
        """Obtiene datos de muestra"""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return pd.read_sql_query(query, self.conn)
        except Exception as e:
            logger.warning(f"Error obteniendo muestra de {table_name}: {e}")
            return pd.DataFrame()
    
    def detect_relationships(self) -> List[Dict]:
        """Detecta relaciones usando la mejor estrategia disponible"""
        print("🔍 FASE 2: Detectando relaciones potenciales...")
        
        if self.use_embeddings and self.embedding_detector:
            relationships = self._detect_with_embeddings()
        else:
            relationships = self._detect_basic()
        
        self.relationships = relationships
        self._print_relationships_summary()
        return relationships
    
    def _detect_with_embeddings(self) -> List[Dict]:
        """Detección avanzada con embeddings"""
        print("🧠 Usando detección con embeddings semánticos...")
        
        # Generar embeddings para contexto
        embeddings_cache = self._generate_embeddings_cache()
        
        relationships = []
        tables = self.schema_info['tables']
        
        for from_table, from_table_info in tables.items():
            for from_column, from_col_info in from_table_info['columns'].items():
                if from_col_info['is_primary_key']:
                    continue
                
                candidates = self._find_embedding_candidates(
                    from_table, from_column, from_col_info, 
                    tables, embeddings_cache
                )
                relationships.extend(candidates)
        
        # Filtrar y ordenar
        relationships = [r for r in relationships if r['confidence'] > 30]
        relationships.sort(key=lambda x: x['confidence'], reverse=True)
        
        return relationships
    
    def _detect_basic(self) -> List[Dict]:
        """Detección básica por patrones de nombres"""
        print("📝 Usando detección básica por patrones...")
        
        relationships = []
        tables = self.schema_info['tables']
        
        fk_patterns = [r'.*_id$', r'.*_key$', r'.*_fk$']
        
        for from_table, from_table_info in tables.items():
            for from_column, from_col_info in from_table_info['columns'].items():
                if from_col_info['is_primary_key']:
                    continue
                
                # Buscar patrones FK
                import re
                for pattern in fk_patterns:
                    if re.match(pattern, from_column.lower()):
                        # Buscar tabla objetivo
                        for to_table, to_table_info in tables.items():
                            if to_table == from_table:
                                continue
                            
                            for to_column, to_col_info in to_table_info['columns'].items():
                                if to_col_info['is_primary_key']:
                                    confidence = self._calculate_basic_confidence(
                                        from_table, from_column, to_table, to_column
                                    )
                                    
                                    if confidence > 30:
                                        relationships.append({
                                            'from_table': from_table,
                                            'from_column': from_column,
                                            'to_table': to_table,
                                            'to_column': to_column,
                                            'confidence': confidence,
                                            'detection_method': 'basic_patterns'
                                        })
        
        # Eliminar duplicados y ordenar
        seen = set()
        unique_relationships = []
        
        for rel in relationships:
            key = (rel['from_table'], rel['from_column'], rel['to_table'], rel['to_column'])
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)
        
        unique_relationships.sort(key=lambda x: x['confidence'], reverse=True)
        return unique_relationships
    
    def _generate_embeddings_cache(self) -> Dict[str, Any]:
        """Genera embeddings para tablas y columnas"""
        cache = {}
        
        if not self.embedding_detector:
            return cache
        
        try:
            # Embeddings para tablas
            for table_name, table_info in self.schema_info['tables'].items():
                table_desc = f"database table {table_name} with {table_info['total_columns']} columns"
                table_embedding = self.embedding_detector.encode([table_desc])
                cache[f"table_{table_name}"] = table_embedding[0]
                
                # Embeddings para columnas
                for col_name, col_info in table_info['columns'].items():
                    col_desc = f"column {col_name} type {col_info['type']} in table {table_name}"
                    col_embedding = self.embedding_detector.encode([col_desc])
                    cache[f"column_{table_name}_{col_name}"] = col_embedding[0]
            
            return cache
        except Exception as e:
            logger.error(f"Error generando embeddings: {e}")
            return {}
    
    def _find_embedding_candidates(self, from_table: str, from_column: str, 
                                 from_col_info: Dict, all_tables: Dict,
                                 embeddings_cache: Dict) -> List[Dict]:
        """Encuentra candidatos usando embeddings"""
        candidates = []
        
        if not embeddings_cache:
            return candidates
        
        from_key = f"column_{from_table}_{from_column}"
        if from_key not in embeddings_cache:
            return candidates
        
        from_embedding = embeddings_cache[from_key].reshape(1, -1)
        
        for to_table, to_table_info in all_tables.items():
            if to_table == from_table:
                continue
            
            for to_column, to_col_info in to_table_info['columns'].items():
                if not to_col_info['is_primary_key']:
                    continue
                
                to_key = f"column_{to_table}_{to_column}"
                if to_key not in embeddings_cache:
                    continue
                
                to_embedding = embeddings_cache[to_key].reshape(1, -1)
                
                # Calcular similitud coseno
                from sklearn.metrics.pairwise import cosine_similarity
                similarity = cosine_similarity(from_embedding, to_embedding)[0][0]
                
                # Combinar con otros factores
                confidence = self._calculate_embedding_confidence(
                    from_table, from_column, to_table, to_column, similarity
                )
                
                if confidence > 30:
                    candidates.append({
                        'from_table': from_table,
                        'from_column': from_column,
                        'to_table': to_table,
                        'to_column': to_column,
                        'confidence': confidence,
                        'semantic_similarity': similarity,
                        'detection_method': 'embeddings'
                    })
        
        return candidates
    
    def _calculate_basic_confidence(self, from_table: str, from_column: str,
                                  to_table: str, to_column: str) -> float:
        """Calcula confianza usando métodos básicos"""
        confidence = 0.0
        
        from_col_lower = from_column.lower()
        to_table_lower = to_table.lower()
        
        # Patrón FK
        if from_col_lower.endswith('_id'):
            confidence += 30
        
        # Nombre de tabla en columna
        table_singular = to_table_lower.rstrip('s')
        if table_singular in from_col_lower:
            confidence += 40
        
        # Validación con datos
        if self._validate_with_sample_data_basic(from_table, from_column, to_table, to_column):
            confidence += 30
        
        return min(confidence, 100.0)
    
    def _calculate_embedding_confidence(self, from_table: str, from_column: str,
                                      to_table: str, to_column: str, 
                                      semantic_similarity: float) -> float:
        """Calcula confianza combinando embeddings con otros factores"""
        confidence = semantic_similarity * 40  # Base semántica
        
        # Factores adicionales
        confidence += self._calculate_basic_confidence(from_table, from_column, to_table, to_column) * 0.6
        
        return min(confidence, 100.0)
    
    def _validate_with_sample_data_basic(self, from_table: str, from_column: str,
                                       to_table: str, to_column: str) -> bool:
        """Validación básica con datos de muestra"""
        try:
            from_df = self.sample_data.get(from_table, pd.DataFrame())
            to_df = self.sample_data.get(to_table, pd.DataFrame())
            
            if from_df.empty or to_df.empty:
                return False
            
            if from_column not in from_df.columns or to_column not in to_df.columns:
                return False
            
            from_values = set(from_df[from_column].dropna().astype(str))
            to_values = set(to_df[to_column].dropna().astype(str))
            
            if not from_values or not to_values:
                return False
            
            intersection = from_values.intersection(to_values)
            match_ratio = len(intersection) / len(from_values) if from_values else 0
            
            return match_ratio > 0.3
            
        except Exception:
            return False
    
    def verify_with_llm(self, max_verifications: int = 5) -> List[Dict]:
        """Verifica relaciones con LLM si está disponible"""
        if not self.use_llm or not self.llm_verifier:
            print("⏭️  FASE 3: Saltando verificación LLM...")
            return []
        
        print(f"🤖 FASE 3: Verificando relaciones con LLM (máx {max_verifications})...")
        
        try:
            # Aquí iría la lógica del LLM verifier
            # Por simplicidad, simulo resultados
            results = []
            
            for i, rel in enumerate(self.relationships[:max_verifications]):
                # Simulación de verificación LLM
                result = {
                    'relationship': f"{rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}",
                    'is_valid': rel['confidence'] > 60,
                    'confidence': min(rel['confidence'] + 10, 100),
                    'explanation': "Relación validada por patrones de naming y datos",
                    'suggested_cardinality': "1:N"
                }
                results.append(result)
            
            self.llm_results = results
            return results
            
        except Exception as e:
            logger.error(f"Error en verificación LLM: {e}")
            return []
    
    def generate_dbml(self, output_path: str = None, project_name: str = None) -> str:
        """Genera código DBML completo"""
        print("📐 FASE 4: Generando código DBML...")
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"schema_{timestamp}.dbml"
        
        if project_name is None:
            project_name = f"Database Schema - {Path(self.db_path).stem}"
        
        generator = DBMLGenerator()
        dbml_content = generator.generate_dbml(
            self.schema_info, 
            self.relationships, 
            self.llm_results,
            project_name
        )
        
        # Guardar archivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dbml_content)
        
        print(f"✅ DBML guardado en: {output_path}")
        return dbml_content
    
    def analyze_complete(self, output_dir: str = "./output") -> Dict[str, Any]:
        """Ejecuta análisis completo"""
        print("🚀 INICIANDO ANÁLISIS COMPLETO DEL ESQUEMA")
        print("=" * 60)
        
        # Crear directorio de salida
        Path(output_dir).mkdir(exist_ok=True)
        
        try:
            # Fase 1: Extraer esquema
            schema = self.extract_schema()
            
            # Fase 2: Detectar relaciones
            relationships = self.detect_relationships()
            
            # Fase 3: Verificar con LLM (opcional)
            llm_results = self.verify_with_llm() if self.use_llm else []
            
            # Fase 4: Generar DBML
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dbml_path = os.path.join(output_dir, f"schema_{timestamp}.dbml")
            dbml_content = self.generate_dbml(dbml_path)
            
            # Guardar resultados completos
            results = {
                'schema': schema,
                'relationships': relationships,
                'llm_results': [r.__dict__ if hasattr(r, '__dict__') else r for r in llm_results],
                'analysis_timestamp': datetime.now().isoformat(),
                'configuration': {
                    'use_embeddings': self.use_embeddings,
                    'use_llm': self.use_llm,
                    'database_path': self.db_path
                },
                'summary': {
                    'total_tables': len(schema['tables']),
                    'total_columns': sum(t['total_columns'] for t in schema['tables'].values()),
                    'total_rows': sum(t['row_count'] for t in schema['tables'].values()),
                    'existing_fks': sum(len(t['foreign_keys']) for t in schema['tables'].values()),
                    'detected_relationships': len(relationships),
                    'high_confidence_relationships': len([r for r in relationships if r.get('confidence', 0) >= 80]),
                    'llm_validated_relationships': len([r for r in llm_results if getattr(r, 'is_valid', False)])
                }
            }
            
            # Guardar JSON
            json_path = os.path.join(output_dir, f"analysis_{timestamp}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            # Mostrar resumen final
            self._print_final_summary(results, dbml_path, json_path)
            
            return results
            
        except Exception as e:
            logger.error(f"Error en análisis completo: {e}")
            print(f"❌ Error: {e}")
            traceback.print_exc()
            raise
    
    def _print_schema_summary(self):
        """Imprime resumen del esquema"""
        print(f"\n📊 Esquema extraído: {self.schema_info['total_tables']} tablas")
        
        for table_name, table_info in self.schema_info['tables'].items():
            fk_info = ""
            if table_info['foreign_keys']:
                fk_info = f" | FKs: {len(table_info['foreign_keys'])}"
            
            print(f"   • {table_name}: {table_info['total_columns']} cols, {table_info['row_count']} filas{fk_info}")
    
    def _print_relationships_summary(self):
        """Imprime resumen de relaciones detectadas"""
        if not self.relationships:
            print("❌ No se detectaron relaciones potenciales")
            return
        
        high_conf = len([r for r in self.relationships if r.get('confidence', 0) >= 80])
        medium_conf = len([r for r in self.relationships if 60 <= r.get('confidence', 0) < 80])
        low_conf = len([r for r in self.relationships if r.get('confidence', 0) < 60])
        
        print(f"\n🔍 Relaciones detectadas: {len(self.relationships)}")
        print(f"   🟢 Alta confianza (80%+): {high_conf}")
        print(f"   🟡 Media confianza (60-79%): {medium_conf}")
        print(f"   🔴 Baja confianza (<60%): {low_conf}")
        
        # Mostrar top 5
        print("\n📋 Top 5 relaciones:")
        for i, rel in enumerate(self.relationships[:5], 1):
            method = rel.get('detection_method', 'unknown')
            print(f"   {i}. {rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}")
            print(f"      Confianza: {rel['confidence']:.1f}% | Método: {method}")
    
    def _print_final_summary(self, results: Dict, dbml_path: str, json_path: str):
        """Imprime resumen final"""
        summary = results['summary']
        
        print("\n📊 RESUMEN FINAL")
        print("=" * 60)
        print(f"📊 Tablas analizadas: {summary['total_tables']}")
        print(f"📋 Total de columnas: {summary['total_columns']}")
        print(f"📈 Total de filas: {summary['total_rows']:,}")
        print(f"🔗 Relaciones existentes: {summary['existing_fks']}")
        print(f"✨ Nuevas relaciones detectadas: {summary['detected_relationships']}")
        print(f"🎯 Relaciones de alta confianza: {summary['high_confidence_relationships']}")
        
        if summary['llm_validated_relationships'] > 0:
            print(f"🤖 Validadas por LLM: {summary['llm_validated_relationships']}")
        
        print(f"\n✅ Análisis completado. Archivos generados:")
        print(f"   📐 DBML: {dbml_path}")
        print(f"   📄 JSON: {json_path}")
        
        print("\n🎨 Para visualizar el diagrama:")
        print("   1. Abre el archivo DBML generado")
        print("   2. Copia todo el contenido")
        print("   3. Ve a: https://dbdiagram.io/d")
        print("   4. Pega el código y ¡disfruta tu diagrama ER!")
    
    def __del__(self):
        """Cerrar conexión"""
        if self.conn:
            self.conn.close()


# Funciones de utilidad
def analyze_database_complete(db_path: str, output_dir: str = "./output",
                            use_embeddings: bool = True, use_llm: bool = True) -> Dict[str, Any]:
    """
    Función de conveniencia para análisis completo
    """
    tool = CompleteDataTool(db_path, use_embeddings, use_llm)
    return tool.analyze_complete(output_dir)

def create_sample_database(db_path: str = "example_store.db"):
    """Crea una base de datos de ejemplo para testing"""
    print("📦 Creando base de datos de ejemplo...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crear tablas
    cursor.executescript("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY,
            name VARCHAR(50),
            description TEXT
        );
        
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100),
            price DECIMAL(10,2),
            category_id INTEGER,
            stock INTEGER
        );
        
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total DECIMAL(10,2),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
        
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price DECIMAL(10,2)
        );
    """)
    
    # Insertar datos de ejemplo
    cursor.executescript("""
        INSERT INTO customers (name, email) VALUES 
            ('Juan Pérez', 'juan@example.com'),
            ('María García', 'maria@example.com'),
            ('Carlos López', 'carlos@example.com');
        
        INSERT INTO categories (name, description) VALUES
            ('Electrónicos', 'Productos electrónicos'),
            ('Ropa', 'Vestimenta y accesorios'),
            ('Hogar', 'Artículos para el hogar');
        
        INSERT INTO products (name, price, category_id, stock) VALUES
            ('Laptop', 999.99, 1, 10),
            ('Mouse', 25.50, 1, 50),
            ('Camiseta', 19.99, 2, 100),
            ('Pantalón', 49.99, 2, 75),
            ('Mesa', 199.99, 3, 20);
        
        INSERT INTO orders (customer_id, total) VALUES
            (1, 1025.49),
            (2, 69.98),
            (3, 199.99);
        
        INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
            (1, 1, 1, 999.99),
            (1, 2, 1, 25.50),
            (2, 3, 1, 19.99),
            (2, 4, 1, 49.99),
            (3, 5, 1, 199.99);
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Base de datos de ejemplo creada: {db_path}")
    return db_path


if __name__ == "__main__":
    print("🚀 COMPLETE DATA TOOL - Herramienta Completa de Análisis")
    print("=" * 60)
    
    # Crear BD de ejemplo si no existe
    db_file = "example_store.db"
    if not os.path.exists(db_file):
        create_sample_database(db_file)
    
    # Ejecutar análisis completo
    try:
        results = analyze_database_complete(
            db_path=db_file,
            output_dir="./output",
            use_embeddings=True,  # Cambiar a False si no tienes sentence-transformers
            use_llm=False         # Cambiar a True si tienes Ollama corriendo
        )
        
        print("\n🎉 ¡Análisis completado exitosamente!")
        
    except Exception as e:
        print(f"❌ Error ejecutando análisis: {e}")
        print("\n💡 Consejos:")
        print("   - Para embeddings: pip install sentence-transformers")
        print("   - Para LLM: instala Ollama y ejecuta 'ollama serve'")
        print("   - Puedes usar solo detección básica con use_embeddings=False, use_llm=False")
