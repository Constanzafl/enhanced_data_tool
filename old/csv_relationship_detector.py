#!/usr/bin/env python3
"""
CSV Relationship Detector - Enhanced Data Tool v2.0
Detecta relaciones entre CSVs sin metadata previa
SOLO por análisis de datos y nombres de columnas
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import json
from dataclasses import dataclass, asdict
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

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

@dataclass
class ColumnInfo:
    """Información de una columna"""
    table_name: str
    column_name: str
    data_type: str
    unique_values: int
    total_values: int
    sample_values: List[Any]
    uniqueness_ratio: float
    has_nulls: bool
    null_percentage: float
    likely_pk: bool = False
    
@dataclass
class RelationshipCandidate:
    """Candidato de relación entre columnas"""
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    confidence: float
    overlap_ratio: float
    name_similarity: float
    data_evidence: Dict[str, Any]
    reasoning: List[str]

class CSVRelationshipDetector:
    """
    Detector de relaciones entre CSVs basado SOLO en datos
    Sin asumir metadata de PKs/FKs
    """
    
    def __init__(self, data_directory: str):
        self.data_directory = Path(data_directory)
        self.csv_files = {}
        self.column_analysis = {}
        self.relationships = []
        
        # Patrones para detectar posibles PKs/FKs por nombre
        self.pk_patterns = [
            r'^id$', r'^.*_id$', r'^.*_key$', r'^.*_pk$',
            r'^\w+id$', r'^key_.*', r'^pk_.*'
        ]
        
        self.fk_patterns = [
            r'.*_id$', r'.*_ref$', r'.*_reference$', r'.*_key$',
            r'.*_fk$', r'.*_foreign$', r'.*identifier$'
        ]
        
        # Umbralles de detección
        self.min_overlap_ratio = 0.3  # 30% de valores compartidos
        self.min_confidence = 40.0    # Confianza mínima
        self.pk_uniqueness_threshold = 0.85  # 85% de valores únicos para ser PK
    
    def load_csvs(self) -> Dict[str, pd.DataFrame]:
        """Carga todos los CSVs del directorio"""
        print_section("FASE 1: CARGANDO ARCHIVOS CSV")
        
        csv_files = list(self.data_directory.glob("*.csv"))
        
        if not csv_files:
            raise Exception(f"No se encontraron CSVs en: {self.data_directory}")
        
        print(f"📂 Directorio: {self.data_directory}")
        print(f"📄 Archivos encontrados: {len(csv_files)}")
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                table_name = csv_file.stem  # nombre sin extensión
                self.csv_files[table_name] = df
                
                print(f"  ✅ {table_name}.csv: {len(df)} filas, {len(df.columns)} columnas")
                
            except Exception as e:
                print_colored(f"  ❌ Error cargando {csv_file.name}: {e}", Colors.FAIL)
        
        print(f"\n📊 Total tablas cargadas: {len(self.csv_files)}")
        return self.csv_files
    
    def analyze_columns(self) -> Dict[str, Dict[str, ColumnInfo]]:
        """Analiza cada columna para entender sus características"""
        print_section("FASE 2: ANÁLISIS DE COLUMNAS")
        
        for table_name, df in self.csv_files.items():
            print(f"\n🔍 Analizando tabla: {table_name}")
            
            self.column_analysis[table_name] = {}
            
            for column in df.columns:
                col_info = self._analyze_single_column(table_name, column, df[column])
                self.column_analysis[table_name][column] = col_info
                
                # Indicador visual
                pk_indicator = " 🔑" if col_info.likely_pk else ""
                fk_indicator = " 🔗" if self._matches_fk_pattern(column) else ""
                
                print(f"  📋 {column}: {col_info.data_type} | "
                      f"Únicos: {col_info.unique_values}/{col_info.total_values} "
                      f"({col_info.uniqueness_ratio:.1%}){pk_indicator}{fk_indicator}")
        
        return self.column_analysis
    
    def _analyze_single_column(self, table_name: str, column_name: str, 
                             series: pd.Series) -> ColumnInfo:
        """Analiza una columna específica"""
        
        # Información básica
        total_values = len(series)
        non_null_series = series.dropna()
        unique_values = len(non_null_series.unique())
        uniqueness_ratio = unique_values / len(non_null_series) if len(non_null_series) > 0 else 0
        
        # Detectar tipo de datos
        data_type = self._detect_data_type(non_null_series)
        
        # Muestra de valores (primeros 5 únicos)
        sample_values = non_null_series.unique()[:5].tolist()
        
        # Información de nulos
        has_nulls = series.isnull().any()
        null_percentage = series.isnull().mean()
        
        # Determinar si es posible PK
        likely_pk = self._is_likely_primary_key(column_name, series, uniqueness_ratio)
        
        return ColumnInfo(
            table_name=table_name,
            column_name=column_name,
            data_type=data_type,
            unique_values=unique_values,
            total_values=total_values,
            sample_values=sample_values,
            uniqueness_ratio=uniqueness_ratio,
            has_nulls=has_nulls,
            null_percentage=null_percentage,
            likely_pk=likely_pk
        )
    
    def _detect_data_type(self, series: pd.Series) -> str:
        """Detecta el tipo de datos de una serie"""
        if len(series) == 0:
            return "empty"
        
        # Intentar convertir a numérico
        try:
            pd.to_numeric(series.iloc[:min(100, len(series))])
            return "numeric"
        except:
            pass
        
        # Verificar si es fecha
        try:
            pd.to_datetime(series.iloc[:min(10, len(series))])
            return "datetime"
        except:
            pass
        
        # Verificar boolean
        unique_vals = set(str(v).lower() for v in series.unique())
        if unique_vals.issubset({'true', 'false', '1', '0', 'yes', 'no'}):
            return "boolean"
        
        return "text"
    
    def _is_likely_primary_key(self, column_name: str, series: pd.Series, 
                             uniqueness_ratio: float) -> bool:
        """Determina si una columna es probablemente una PK"""
        
        # Chequeos básicos
        if uniqueness_ratio < self.pk_uniqueness_threshold:
            return False
        
        if series.isnull().any():  # PKs no pueden tener nulos
            return False
        
        # Patrones de nombre
        if self._matches_pk_pattern(column_name):
            return True
        
        # Si es numérica secuencial
        if self._is_sequential_numeric(series):
            return True
        
        return False
    
    def _matches_pk_pattern(self, column_name: str) -> bool:
        """Verifica si el nombre coincide con patrones de PK"""
        col_lower = column_name.lower()
        return any(re.match(pattern, col_lower) for pattern in self.pk_patterns)
    
    def _matches_fk_pattern(self, column_name: str) -> bool:
        """Verifica si el nombre coincide con patrones de FK"""
        col_lower = column_name.lower()
        return any(re.match(pattern, col_lower) for pattern in self.fk_patterns)
    
    def _is_sequential_numeric(self, series: pd.Series) -> bool:
        """Verifica si es una secuencia numérica (común en PKs)"""
        try:
            numeric_series = pd.to_numeric(series)
            if len(numeric_series) < 3:
                return False
            
            # Verificar si es secuencial (aproximadamente)
            sorted_vals = sorted(numeric_series.unique())
            diffs = [sorted_vals[i+1] - sorted_vals[i] for i in range(len(sorted_vals)-1)]
            
            # Si las diferencias son consistentes (ej: 1,2,3 o 10,20,30)
            if len(set(diffs)) <= 2:  # Máximo 2 diferencias distintas
                return True
                
        except:
            pass
        
        return False
    
    def detect_relationships(self) -> List[RelationshipCandidate]:
        """
        Detecta relaciones entre columnas basándose SOLO en datos
        """
        print_section("FASE 3: DETECCIÓN DE RELACIONES")
        
        candidates = []
        
        # Obtener todas las combinaciones de columnas
        all_columns = []
        for table_name, columns in self.column_analysis.items():
            for column_name, col_info in columns.items():
                all_columns.append(col_info)
        
        print(f"🔍 Analizando {len(all_columns)} columnas en busca de relaciones...")
        
        # Comparar cada columna con todas las demás
        for i, col_a in enumerate(all_columns):
            for j, col_b in enumerate(all_columns):
                # No comparar columna consigo misma o misma tabla
                if i >= j or col_a.table_name == col_b.table_name:
                    continue
                
                # Analizar posible relación
                relationship = self._analyze_potential_relationship(col_a, col_b)
                
                if relationship and relationship.confidence >= self.min_confidence:
                    candidates.append(relationship)
        
        # Ordenar por confianza
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        
        self.relationships = candidates
        self._print_relationship_summary(candidates)
        
        return candidates
    
    def _analyze_potential_relationship(self, col_a: ColumnInfo, 
                                     col_b: ColumnInfo) -> Optional[RelationshipCandidate]:
        """Analiza si dos columnas pueden tener una relación"""
        
        # Obtener datos reales
        df_a = self.csv_files[col_a.table_name]
        df_b = self.csv_files[col_b.table_name]
        
        series_a = df_a[col_a.column_name].dropna()
        series_b = df_b[col_b.column_name].dropna()
        
        # Verificaciones básicas
        if len(series_a) == 0 or len(series_b) == 0:
            return None
        
        # Mismo tipo de datos
        if col_a.data_type != col_b.data_type:
            return None
        
        # Calcular overlap de valores
        values_a = set(series_a.astype(str))
        values_b = set(series_b.astype(str))
        
        intersection = values_a.intersection(values_b)
        
        if not intersection:
            return None
        
        # Calcular ratios de overlap
        overlap_ratio_a = len(intersection) / len(values_a)
        overlap_ratio_b = len(intersection) / len(values_b)
        
        # Para FK->PK: muchos valores de FK deben existir en PK
        # Usamos el overlap ratio más conservador
        overlap_ratio = min(overlap_ratio_a, overlap_ratio_b)
        
        if overlap_ratio < self.min_overlap_ratio:
            return None
        
        # Determinar dirección de la relación (FK -> PK)
        from_col, to_col = self._determine_relationship_direction(col_a, col_b)
        
        if not from_col:  # No se pudo determinar dirección
            return None
        
        # Calcular similitud de nombres
        name_similarity = self._calculate_name_similarity(from_col.column_name, 
                                                        to_col.column_name,
                                                        from_col.table_name,
                                                        to_col.table_name)
        
        # Calcular confianza total
        confidence, reasoning = self._calculate_relationship_confidence(
            from_col, to_col, overlap_ratio, name_similarity, intersection
        )
        
        # Evidencia de datos
        data_evidence = {
            'shared_values_count': len(intersection),
            'shared_values_sample': list(intersection)[:5],
            'from_unique_values': from_col.unique_values,
            'to_unique_values': to_col.unique_values,
            'cardinality_estimate': self._estimate_cardinality(from_col, to_col, df_a, df_b)
        }
        
        return RelationshipCandidate(
            from_table=from_col.table_name,
            from_column=from_col.column_name,
            to_table=to_col.table_name,
            to_column=to_col.column_name,
            confidence=confidence,
            overlap_ratio=overlap_ratio,
            name_similarity=name_similarity,
            data_evidence=data_evidence,
            reasoning=reasoning
        )
    
    def _determine_relationship_direction(self, col_a: ColumnInfo, 
                                        col_b: ColumnInfo) -> Tuple[Optional[ColumnInfo], Optional[ColumnInfo]]:
        """Determina la dirección FK -> PK de la relación"""
        
        # Regla 1: Si una es likely_pk, esa es el target
        if col_b.likely_pk and not col_a.likely_pk:
            return col_a, col_b  # col_a FK -> col_b PK
        
        if col_a.likely_pk and not col_b.likely_pk:
            return col_b, col_a  # col_b FK -> col_a PK
        
        # Regla 2: La que tiene mayor uniqueness ratio es PK
        if col_b.uniqueness_ratio > col_a.uniqueness_ratio + 0.2:  # Diferencia significativa
            return col_a, col_b
        
        if col_a.uniqueness_ratio > col_b.uniqueness_ratio + 0.2:
            return col_b, col_a
        
        # Regla 3: Patrones de nombres
        if self._matches_fk_pattern(col_a.column_name) and not self._matches_fk_pattern(col_b.column_name):
            return col_a, col_b
        
        if self._matches_fk_pattern(col_b.column_name) and not self._matches_fk_pattern(col_a.column_name):
            return col_b, col_a
        
        # Regla 4: La que tiene más valores únicos probablemente es PK
        if col_b.unique_values > col_a.unique_values:
            return col_a, col_b
        
        if col_a.unique_values > col_b.unique_values:
            return col_b, col_a
        
        # No se puede determinar dirección clara
        return None, None
    
    def _calculate_name_similarity(self, from_col: str, to_col: str,
                                 from_table: str, to_table: str) -> float:
        """Calcula similitud entre nombres de columnas y tablas"""
        score = 0.0
        
        from_col_lower = from_col.lower()
        to_col_lower = to_col.lower()
        from_table_lower = from_table.lower()
        to_table_lower = to_table.lower()
        
        # Coincidencia exacta
        if from_col_lower == to_col_lower:
            score += 1.0
        
        # Patrones FK comunes
        if to_col_lower == 'id' and from_col_lower.endswith('_id'):
            score += 0.8
            
            # Si el prefijo del FK coincide con la tabla
            prefix = from_col_lower[:-3]  # remover '_id'
            if prefix in to_table_lower or to_table_lower.startswith(prefix):
                score += 0.9
        
        # Si FK contiene nombre de tabla target
        if to_table_lower.rstrip('s') in from_col_lower:  # patients -> patient
            score += 0.7
        
        if to_table_lower in from_col_lower:
            score += 0.6
        
        # Similitud por substring
        if from_col_lower in to_col_lower or to_col_lower in from_col_lower:
            score += 0.5
        
        return min(score, 1.0)
    
    def _calculate_relationship_confidence(self, from_col: ColumnInfo, to_col: ColumnInfo,
                                         overlap_ratio: float, name_similarity: float,
                                         intersection: set) -> Tuple[float, List[str]]:
        """Calcula confianza de la relación y proporciona razonamiento"""
        
        confidence = 0.0
        reasoning = []
        
        # Factor 1: Overlap de datos (peso: 40%)
        overlap_score = overlap_ratio * 40
        confidence += overlap_score
        
        if overlap_ratio > 0.8:
            reasoning.append(f"Muy alto overlap de datos ({overlap_ratio:.1%})")
        elif overlap_ratio > 0.6:
            reasoning.append(f"Alto overlap de datos ({overlap_ratio:.1%})")
        else:
            reasoning.append(f"Overlap moderado de datos ({overlap_ratio:.1%})")
        
        # Factor 2: Similitud de nombres (peso: 30%)
        name_score = name_similarity * 30
        confidence += name_score
        
        if name_similarity > 0.8:
            reasoning.append("Nombres muy similares")
        elif name_similarity > 0.5:
            reasoning.append("Nombres relacionados")
        
        # Factor 3: Características de PK/FK (peso: 20%)
        if to_col.likely_pk:
            confidence += 15
            reasoning.append("Target es probable PK")
        
        if self._matches_fk_pattern(from_col.column_name):
            confidence += 10
            reasoning.append("Source sigue patrón FK")
        
        # Factor 4: Ratio de unicidad apropiado (peso: 10%)
        if to_col.uniqueness_ratio > from_col.uniqueness_ratio + 0.3:
            confidence += 10
            reasoning.append("Target más único que source")
        
        # Bonificaciones
        if len(intersection) > 10:  # Suficientes valores compartidos
            confidence += 5
            reasoning.append("Suficientes valores compartidos")
        
        if not from_col.has_nulls and not to_col.has_nulls:
            confidence += 5
            reasoning.append("Sin valores nulos")
        
        return min(confidence, 100.0), reasoning
    
    def _estimate_cardinality(self, from_col: ColumnInfo, to_col: ColumnInfo,
                            df_a: pd.DataFrame, df_b: pd.DataFrame) -> str:
        """Estima la cardinalidad de la relación"""
        
        # Calcular ratios
        avg_occurrences_in_from = len(df_a) / from_col.unique_values if from_col.unique_values > 0 else 0
        avg_occurrences_in_to = len(df_b) / to_col.unique_values if to_col.unique_values > 0 else 0
        
        if avg_occurrences_in_from > 1.5 and avg_occurrences_in_to <= 1.2:
            return "Many-to-One (N:1)"
        elif avg_occurrences_in_from <= 1.2 and avg_occurrences_in_to <= 1.2:
            return "One-to-One (1:1)"
        elif avg_occurrences_in_from > 1.5 and avg_occurrences_in_to > 1.5:
            return "Many-to-Many (N:M)"
        else:
            return "One-to-Many (1:N)"
    
    def _print_relationship_summary(self, relationships: List[RelationshipCandidate]):
        """Imprime resumen de relaciones detectadas"""
        
        if not relationships:
            print_colored("❌ No se detectaron relaciones", Colors.FAIL)
            return
        
        print(f"\n🔗 RELACIONES DETECTADAS: {len(relationships)}")
        print("=" * 50)
        
        # Agrupar por confianza
        high_conf = [r for r in relationships if r.confidence >= 80]
        medium_conf = [r for r in relationships if 60 <= r.confidence < 80]
        low_conf = [r for r in relationships if r.confidence < 60]
        
        for group, title, emoji in [
            (high_conf, "ALTA CONFIANZA (80%+)", "🟢"),
            (medium_conf, "CONFIANZA MEDIA (60-79%)", "🟡"),
            (low_conf, "BAJA CONFIANZA (40-59%)", "🔴")
        ]:
            if group:
                print_colored(f"\n{emoji} {title}", Colors.OKBLUE)
                print("-" * 40)
                
                for rel in group:
                    cardinality = rel.data_evidence.get('cardinality_estimate', 'Unknown')
                    shared_count = rel.data_evidence.get('shared_values_count', 0)
                    
                    print(f"  {rel.from_table}.{rel.from_column} → {rel.to_table}.{rel.to_column}")
                    print(f"    Confianza: {rel.confidence:.1f}% | Overlap: {rel.overlap_ratio:.1%} | "
                          f"Valores compartidos: {shared_count} | {cardinality}")
                    print(f"    Razones: {', '.join(rel.reasoning[:2])}")
                    print()
    
    def generate_dbml(self, output_path: str = None) -> str:
        """Genera código DBML basado en las relaciones detectadas"""
        print_section("FASE 4: GENERANDO CÓDIGO DBML")
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"detected_schema_{timestamp}.dbml"
        
        lines = []
        
        # Header
        lines.extend([
            f"// Schema detectado automáticamente desde CSVs",
            f"// Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"// Directorio fuente: {self.data_directory}",
            "",
            'Project "CSV Schema Detection" {',
            '  database_type: "CSV"',
            '  Note: "Relaciones detectadas automáticamente sin metadata previa"',
            '}',
            ""
        ])
        
        # Definir tablas
        for table_name, df in self.csv_files.items():
            lines.append(f"Table {table_name} {{")
            
            columns_info = self.column_analysis[table_name]
            
            for column_name in df.columns:
                col_info = columns_info[column_name]
                
                # Mapear tipos de datos
                dbml_type = {
                    'numeric': 'integer',
                    'text': 'varchar',
                    'datetime': 'timestamp',
                    'boolean': 'boolean'
                }.get(col_info.data_type, 'varchar')
                
                # Construir línea de columna
                col_line = f"  {column_name} {dbml_type}"
                
                # Agregar atributos
                attributes = []
                if col_info.likely_pk:
                    attributes.append("primary key")
                
                if not col_info.has_nulls:
                    attributes.append("not null")
                
                if attributes:
                    col_line += f" [{', '.join(attributes)}]"
                
                lines.append(col_line)
            
            # Nota con estadísticas
            lines.append(f'  Note: "Filas: {len(df):,} | Columnas: {len(df.columns)}"')
            lines.append("}")
            lines.append("")
        
        # Definir relaciones detectadas
        if self.relationships:
            lines.append("// ===== RELACIONES DETECTADAS =====")
            lines.append("")
            
            # Agrupar por confianza
            high_conf = [r for r in self.relationships if r.confidence >= 80]
            medium_conf = [r for r in self.relationships if 60 <= r.confidence < 80]
            low_conf = [r for r in self.relationships if r.confidence < 60]
            
            for group, comment in [
                (high_conf, "Alta confianza (80%+)"),
                (medium_conf, "Confianza media (60-79%)"),
                (low_conf, "Baja confianza (40-59%)")
            ]:
                if group:
                    lines.append(f"// {comment}")
                    for rel in group:
                        # Determinar tipo de relación
                        cardinality = rel.data_evidence.get('cardinality_estimate', '')
                        ref_type = ">" if "Many-to-One" in cardinality else "-"
                        
                        ref_line = (f"Ref: {rel.from_table}.{rel.from_column} {ref_type} "
                                  f"{rel.to_table}.{rel.to_column} "
                                  f"// Confianza: {rel.confidence:.1f}% | "
                                  f"Overlap: {rel.overlap_ratio:.1%}")
                        
                        lines.append(ref_line)
                    lines.append("")
        
        # Estadísticas finales
        lines.extend([
            "// ===== ESTADÍSTICAS =====",
            f"// Tablas analizadas: {len(self.csv_files)}",
            f"// Relaciones detectadas: {len(self.relationships)}",
            f"// Alta confianza: {len([r for r in self.relationships if r.confidence >= 80])}",
            f"// Detección basada en: overlapping de datos + similitud de nombres"
        ])
        
        dbml_content = "\n".join(lines)
        
        # Guardar archivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dbml_content)
        
        print_colored(f"✅ DBML generado: {output_path}", Colors.OKGREEN)
        print_colored("🎨 Para visualizar:", Colors.OKCYAN)
        print("   1. Abre el archivo DBML")
        print("   2. Copia todo el contenido") 
        print("   3. Ve a https://dbdiagram.io/d")
        print("   4. Pega y visualiza tu diagrama ER")
        
        return dbml_content
    
    def save_results(self, output_path: str = None) -> str:
        """Guarda resultados completos en JSON"""
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"detection_results_{timestamp}.json"
        
        # Preparar datos para serialización
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'data_directory': str(self.data_directory),
            'tables_analyzed': {
                name: {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'columns_info': {
                        col_name: asdict(col_info) 
                        for col_name, col_info in self.column_analysis[name].items()
                    }
                }
                for name, df in self.csv_files.items()
            },
            'relationships_detected': [asdict(rel) for rel in self.relationships],
            'summary': {
                'total_tables': len(self.csv_files),
                'total_relationships': len(self.relationships),
                'high_confidence': len([r for r in self.relationships if r.confidence >= 80]),
                'medium_confidence': len([r for r in self.relationships if 60 <= r.confidence < 80]),
                'low_confidence': len([r for r in self.relationships if r.confidence < 60])
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print_colored(f"💾 Resultados guardados: {output_path}", Colors.OKGREEN)
        return output_path
    
    def run_complete_analysis(self) -> Dict[str, Any]:
        """Ejecuta análisis completo"""
        print_colored("🚀 CSV RELATIONSHIP DETECTOR - ANÁLISIS COMPLETO", Colors.HEADER)
        print_colored("=" * 70, Colors.HEADER)
        
        try:
            # Fase 1: Cargar CSVs
            self.load_csvs()
            
            # Fase 2: Analizar columnas
            self.analyze_columns()
            
            # Fase 3: Detectar relaciones
            self.detect_relationships()
            
            # Fase 4: Generar outputs
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dbml_file = f"schema_{timestamp}.dbml"
            json_file = f"results_{timestamp}.json"
            
            dbml_content = self.generate_dbml(dbml_file)
            json_path = self.save_results(json_file)
            
            # Resumen final
            print_section("ANÁLISIS COMPLETADO")
            
            summary = {
                'total_tables': len(self.csv_files),
                'total_relationships': len(self.relationships),
                'high_confidence': len([r for r in self.relationships if r.confidence >= 80]),
                'medium_confidence': len([r for r in self.relationships if 60 <= r.confidence < 80]),
                'files_generated': [dbml_file, json_file]
            }
            
            print_colored("📊 RESUMEN FINAL:", Colors.OKGREEN)
            print(f"  📄 Tablas analizadas: {summary['total_tables']}")
            print(f"  🔗 Relaciones detectadas: {summary['total_relationships']}")
            print(f"  🟢 Alta confianza: {summary['high_confidence']}")
            print(f"  🟡 Media confianza: {summary['medium_confidence']}")
            print(f"  📁 Archivos generados: {', '.join(summary['files_generated'])}")
            
            return summary
            
        except Exception as e:
            print_colored(f"❌ Error en análisis: {e}", Colors.FAIL)
            import traceback
            traceback.print_exc()
            raise

def main():
    """Función principal"""
    
    # Path específico solicitado
    data_dir = r"C:\Users\Flori\Desktop\Omniscient Platforms\internal tool\enhanced_data_tool\data"
    
    print_colored("🔍 CSV RELATIONSHIP DETECTOR", Colors.HEADER)
    print_colored("Detecta relaciones entre CSVs sin metadata previa", Colors.OKCYAN)
    print(f"📂 Directorio: {data_dir}")
    
    # Verificar si existe el directorio
    if not Path(data_dir).exists():
        print_colored(f"❌ Directorio no encontrado: {data_dir}", Colors.FAIL)
        print_colored("💡 Ejecuta primero: python create_dummy_csvs.py", Colors.WARNING)
        return
    
    # Ejecutar análisis
    detector = CSVRelationshipDetector(data_dir)
    results = detector.run_complete_analysis()
    
    print_colored("\n🎉 ¡Análisis completado exitosamente!", Colors.OKGREEN)

if __name__ == "__main__":
    main()
