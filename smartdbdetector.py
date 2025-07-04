import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Set, Any
from dataclasses import dataclass
from datetime import datetime
import re
from difflib import SequenceMatcher
from collections import Counter
import json

@dataclass
class ColumnProfile:
    """Perfil completo de una columna"""
    table_name: str
    column_name: str
    data_type: str
    unique_count: int
    null_count: int
    sample_values: List[Any]
    value_patterns: Dict[str, int]
    numeric_stats: Dict[str, float] = None

@dataclass
class RelationshipCandidate:
    """Candidato a relación entre columnas"""
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    confidence_score: float
    evidence: Dict[str, Any]

class SmartRelationshipDetector:
    def __init__(self, tables: Dict[str, pd.DataFrame]):
        self.tables = tables
        self.column_profiles = {}
        self.primary_keys = {}
        
        # Patrones comunes para identificar IDs
        self.common_id_patterns = [
            r'_id$', r'^id$', r'_key$', r'_code$', r'_no$', r'_number$',
            r'_uid$', r'^uid$', r'_uuid$', r'^uuid$', r'_guid$', r'^guid$',
            r'_pk$', r'^pk$', r'_identifier$', r'_ident$',
            r'codigo$', r'_cod$', r'_num$'
        ]
        
        # Palabras clave que indican IDs
        self.id_keywords = [
            'id', 'key', 'code', 'number', 'uid', 'uuid', 'guid', 
            'pk', 'identifier', 'ident', 'codigo', 'cod', 'num',
            'reference', 'ref'
        ]
        
        # Mapeos semánticos comunes
        self.common_name_mappings = {
            'patient': ['patient', 'person', 'individual', 'client', 'paciente'],
            'appointment': ['appointment', 'visit', 'booking', 'schedule', 'cita'],
            'medication': ['medication', 'medicine', 'drug', 'prescription', 'medicamento'],
            'doctor': ['doctor', 'physician', 'provider', 'staff', 'medico'],
            'pet': ['pet', 'animal', 'patient', 'mascota'],
            'owner': ['owner', 'client', 'customer', 'dueño', 'propietario']
        }
        
    def analyze_columns(self):
        """Analiza todas las columnas y crea perfiles detallados"""
        print("🔍 Analizando columnas de todas las tablas...")
        
        # Primero detectar las PKs probables
        self._detect_primary_keys()
        
        for table_name, df in self.tables.items():
            print(f"\nTabla: {table_name}")
            for column in df.columns:
                profile = self._create_column_profile(table_name, df, column)
                self.column_profiles[f"{table_name}.{column}"] = profile
                
                # Marcar si es PK
                is_pk = self.primary_keys.get(table_name) == column
                pk_marker = " (PK)" if is_pk else ""
                
                print(f"  - {column}{pk_marker}: {profile.data_type}, "
                      f"{profile.unique_count} únicos, "
                      f"{profile.null_count} nulos")
    
    def _detect_primary_keys(self):
        """Detecta las claves primarias probables de cada tabla"""
        print("\n🔑 Detectando claves primarias...")
        
        for table_name, df in self.tables.items():
            pk_candidates = []
            
            for column in df.columns:
                col_data = df[column]
                
                # Criterios para PK:
                # 1. No tiene nulos
                # 2. Todos los valores son únicos
                # 3. El nombre sugiere que es PK
                if (col_data.notna().all() and 
                    col_data.nunique() == len(df) and
                    len(df) > 0):
                    
                    col_lower = column.lower()
                    
                    # Prioridad máxima: nombres exactos comunes
                    if col_lower in ['id', 'uid', 'uuid', 'guid', 'pk']:
                        pk_candidates.insert(0, (column, 100))
                    
                    # Alta prioridad: columna con nombre de tabla + id
                    elif (col_lower == f"{table_name.lower()}_id" or 
                          col_lower == f"{table_name.lower()}id" or
                          col_lower == f"{table_name.rstrip('s').lower()}_id" or
                          col_lower == f"{table_name.rstrip('s').lower()}id"):
                        pk_candidates.insert(0, (column, 95))
                    
                    # Prioridad media-alta: contiene palabras clave de ID
                    elif any(keyword in col_lower for keyword in self.id_keywords):
                        # Verificar que sea probablemente la PK de esta tabla
                        if table_name.lower() in col_lower or table_name.rstrip('s').lower() in col_lower:
                            pk_candidates.append((column, 85))
                        else:
                            pk_candidates.append((column, 70))
                    
                    # Prioridad baja: columna numérica única sin nombre claro
                    elif pd.api.types.is_numeric_dtype(col_data):
                        pk_candidates.append((column, 40))
                    
                    # Muy baja prioridad: otras columnas únicas
                    else:
                        pk_candidates.append((column, 20))
            
            # Seleccionar la PK más probable
            if pk_candidates:
                pk_candidates.sort(key=lambda x: x[1], reverse=True)
                self.primary_keys[table_name] = pk_candidates[0][0]
                print(f"  - {table_name}: {pk_candidates[0][0]} (confianza: {pk_candidates[0][1]}%)")
            else:
                print(f"  - {table_name}: No se detectó PK clara")
    
    def _create_column_profile(self, table_name: str, df: pd.DataFrame, column: str) -> ColumnProfile:
        """Crea un perfil detallado de una columna"""
        col_data = df[column]
        
        # Obtener valores únicos no nulos
        non_null_data = col_data.dropna()
        sample_size = min(100, len(non_null_data))
        sample_values = non_null_data.sample(n=sample_size).tolist() if len(non_null_data) > 0 else []
        
        # Detectar patrones en los valores
        value_patterns = self._detect_value_patterns(non_null_data)
        
        # Estadísticas numéricas si aplica
        numeric_stats = None
        if pd.api.types.is_numeric_dtype(col_data):
            numeric_stats = {
                'min': float(col_data.min()) if len(non_null_data) > 0 else None,
                'max': float(col_data.max()) if len(non_null_data) > 0 else None,
                'mean': float(col_data.mean()) if len(non_null_data) > 0 else None
            }
        
        return ColumnProfile(
            table_name=table_name,
            column_name=column,
            data_type=str(col_data.dtype),
            unique_count=col_data.nunique(),
            null_count=col_data.isna().sum(),
            sample_values=sample_values,
            value_patterns=value_patterns,
            numeric_stats=numeric_stats
        )
    
    def _detect_value_patterns(self, data: pd.Series) -> Dict[str, int]:
        """Detecta patrones comunes en los valores"""
        patterns = {
            'numeric': 0,
            'uuid': 0,
            'email': 0,
            'date': 0,
            'phone': 0,
            'alphanumeric': 0
        }
        
        for value in data.dropna().astype(str).head(100):
            if re.match(r'^\d+$', value):
                patterns['numeric'] += 1
            elif re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', value, re.I):
                patterns['uuid'] += 1
            elif '@' in value and '.' in value:
                patterns['email'] += 1
            elif re.match(r'^\d{4}-\d{2}-\d{2}', value):
                patterns['date'] += 1
            elif re.match(r'^[\d\-\+\(\)]+$', value) and len(value) >= 7:
                patterns['phone'] += 1
            else:
                patterns['alphanumeric'] += 1
                
        return patterns
    
    def find_relationships(self) -> List[RelationshipCandidate]:
        """Encuentra relaciones potenciales entre columnas"""
        print("\n🔗 Buscando relaciones potenciales...")
        candidates = []
        
        # Primero, analizar columnas
        self.analyze_columns()
        
        # Comparar cada par de columnas de diferentes tablas
        for source_key, source_profile in self.column_profiles.items():
            for target_key, target_profile in self.column_profiles.items():
                # Skip si es la misma tabla
                if source_profile.table_name == target_profile.table_name:
                    continue
                
                # Evaluar si pueden estar relacionadas
                candidate = self._evaluate_relationship(source_profile, target_profile)
                if candidate and candidate.confidence_score > 0.3:  # Umbral mínimo
                    candidates.append(candidate)
        
        # Ordenar por confianza
        candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Eliminar duplicados (A->B y B->A)
        unique_candidates = self._remove_duplicate_relationships(candidates)
        
        return unique_candidates
    
    def _evaluate_relationship(self, source: ColumnProfile, target: ColumnProfile) -> RelationshipCandidate:
        """Evalúa si dos columnas pueden estar relacionadas"""
        evidence = {}
        scores = []
        
        # NUEVO: Verificar si ambas son PKs de sus respectivas tablas
        source_is_pk = self.primary_keys.get(source.table_name) == source.column_name
        target_is_pk = self.primary_keys.get(target.table_name) == target.column_name
        
        # Si ambas son PKs, muy probablemente NO están relacionadas
        if source_is_pk and target_is_pk:
            evidence['both_are_pks'] = True
            evidence['pk_penalty'] = -0.5
            scores.append(-0.5)  # Penalización fuerte
        
        # 1. Similitud semántica de nombres
        name_score = self._calculate_name_similarity(source, target)
        evidence['name_similarity'] = name_score
        scores.append(name_score * 0.3)  # 30% peso
        
        # 2. Compatibilidad de tipos de datos
        type_score = self._check_type_compatibility(source, target)
        evidence['type_compatibility'] = type_score
        scores.append(type_score * 0.1)  # 10% peso
        
        # 3. Coincidencia de valores
        value_score, value_overlap = self._calculate_value_overlap(source, target)
        evidence['value_overlap'] = {
            'score': value_score,
            'percentage': value_overlap
        }
        scores.append(value_score * 0.5)  # 50% peso - MUY IMPORTANTE
        
        # 4. Patrones de datos similares
        pattern_score = self._compare_patterns(source, target)
        evidence['pattern_similarity'] = pattern_score
        scores.append(pattern_score * 0.1)  # 10% peso
        
        # BONUS: Si detectamos un patrón FK clásico, dar bonus
        if target_is_pk and not source_is_pk:
            # Verificar si el nombre de source sugiere FK a target
            source_base = source.column_name.lower()
            for pattern in self.common_id_patterns:
                source_base = re.sub(pattern, '', source_base)
            
            target_table_name = target.table_name.lower().rstrip('s')
            if source_base == target_table_name or source_base + 's' == target.table_name.lower():
                evidence['fk_pattern_bonus'] = 0.2
                scores.append(0.2)  # Bonus por patrón FK clásico
        
        # Calcular score final
        confidence_score = sum(scores)
        
        # Solo crear candidato si hay alguna evidencia significativa
        if confidence_score > 0:
            return RelationshipCandidate(
                source_table=source.table_name,
                source_column=source.column_name,
                target_table=target.table_name,
                target_column=target.column_name,
                confidence_score=confidence_score,
                evidence=evidence
            )
        return None
    
    def _calculate_name_similarity(self, source: ColumnProfile, target: ColumnProfile) -> float:
        """Calcula similitud semántica entre nombres de columnas"""
        source_name = source.column_name.lower()
        target_name = target.column_name.lower()
        source_table = source.table_name.lower()
        target_table = target.table_name.lower()
        
        # REGLA 1: Evitar relacionar PKs genéricas entre tablas diferentes
        source_is_pk = self.primary_keys.get(source.table_name) == source.column_name
        target_is_pk = self.primary_keys.get(target.table_name) == target.column_name
        
        if source_is_pk and target_is_pk:
            return 0.0  # Las PKs de diferentes tablas NO están relacionadas
        
        # REGLA 2: Extraer componentes semánticos de los nombres
        source_components = self._extract_name_components(source_name)
        target_components = self._extract_name_components(target_name)
        
        # REGLA 3: Detectar patrones FK incluso con nombres no estándar
        if target_is_pk and not source_is_pk:
            # Buscar si el source contiene referencia a la tabla target
            for component in source_components['base_words']:
                # Verificar contra el nombre de la tabla y sus variaciones
                if self._words_are_related(component, target_table.rstrip('s')):
                    return 0.9
                
                # Verificar contra mapeos semánticos
                for concept, variations in self.common_name_mappings.items():
                    if component in variations:
                        for var in variations:
                            if self._words_are_related(var, target_table.rstrip('s')):
                                return 0.85
        
        # REGLA 4: Patrón inverso
        if source_is_pk and not target_is_pk:
            for component in target_components['base_words']:
                if self._words_are_related(component, source_table.rstrip('s')):
                    return 0.9
        
        # REGLA 5: Comparar componentes semánticos
        if (source_components['has_id_component'] and target_components['has_id_component']):
            shared_words = source_components['base_words'] & target_components['base_words']
            if shared_words:
                return 0.8
        
        # REGLA 6: Nombres idénticos (pero no genéricos)
        if source_name == target_name and not self._is_generic_column(source_name):
            return 0.9
        
        # REGLA 7: Evitar falsos positivos con columnas genéricas
        if self._is_generic_column(source_name) and self._is_generic_column(target_name):
            return 0.1
        
        # REGLA 8: Análisis de similitud más profundo para nombres complejos
        if not self._is_generic_column(source_name) or not self._is_generic_column(target_name):
            # Calcular similitud entre todas las palabras base
            max_similarity = 0.0
            for s_word in source_components['all_words']:
                for t_word in target_components['all_words']:
                    sim = SequenceMatcher(None, s_word, t_word).ratio()
                    if sim > max_similarity:
                        max_similarity = sim
            
            if max_similarity > 0.8:
                return max_similarity * 0.7  # Reducir un poco la confianza
        
        return 0.0
    
    def _extract_name_components(self, column_name: str) -> Dict:
        """Extrae componentes semánticos de un nombre de columna"""
        # Separar por guiones bajos, camelCase, y otros separadores
        parts = []
        
        # Primero separar por guiones bajos y guiones
        temp_parts = re.split(r'[_\-\s]+', column_name)
        
        # Luego separar camelCase y PascalCase
        for part in temp_parts:
            # Insertar espacios antes de mayúsculas
            spaced = re.sub(r'(?<!^)(?=[A-Z])', ' ', part)
            parts.extend(spaced.lower().split())
        
        # Filtrar partes vacías
        parts = [p for p in parts if p]
        
        # Identificar si tiene componente ID
        has_id = any(part in self.id_keywords for part in parts)
        
        # Obtener palabras base (sin keywords de ID)
        base_words = set()
        for part in parts:
            if part not in self.id_keywords:
                base_words.add(part)
                # También agregar versiones sin 's' final (plural)
                if part.endswith('s') and len(part) > 2:
                    base_words.add(part[:-1])
        
        return {
            'all_words': set(parts),
            'base_words': base_words,
            'has_id_component': has_id,
            'original': column_name
        }
    
    def _words_are_related(self, word1: str, word2: str) -> bool:
        """Verifica si dos palabras están relacionadas semánticamente"""
        # Coincidencia exacta
        if word1 == word2:
            return True
        
        # Una contiene a la otra (mínimo 3 caracteres)
        if len(word1) >= 3 and len(word2) >= 3:
            if word1 in word2 or word2 in word1:
                return True
        
        # Verificar plurales
        if word1 + 's' == word2 or word2 + 's' == word1:
            return True
        
        # Similitud alta
        if SequenceMatcher(None, word1, word2).ratio() > 0.85:
            return True
        
        # Verificar en mapeos semánticos
        for concept, variations in self.common_name_mappings.items():
            if word1 in variations and word2 in variations:
                return True
        
        return False
    
    def _is_generic_column(self, column_name: str) -> bool:
        """Determina si una columna es genérica"""
        generic_columns = [
            'id', 'uid', 'uuid', 'name', 'description', 'created_at', 
            'updated_at', 'status', 'type', 'date', 'time', 'timestamp',
            'active', 'deleted', 'enabled', 'visible'
        ]
        return column_name.lower() in generic_columns
    
    def _check_type_compatibility(self, source: ColumnProfile, target: ColumnProfile) -> float:
        """Verifica compatibilidad de tipos de datos"""
        source_type = source.data_type
        target_type = target.data_type
        
        # Mismos tipos
        if source_type == target_type:
            return 1.0
        
        # Tipos numéricos compatibles
        numeric_types = ['int', 'float', 'decimal', 'numeric']
        if any(t in source_type.lower() for t in numeric_types) and \
           any(t in target_type.lower() for t in numeric_types):
            return 0.8
        
        # String types compatibles
        string_types = ['object', 'string', 'varchar', 'text']
        if any(t in source_type.lower() for t in string_types) and \
           any(t in target_type.lower() for t in string_types):
            return 0.8
        
        return 0.0
    
    def _calculate_value_overlap(self, source: ColumnProfile, target: ColumnProfile) -> Tuple[float, float]:
        """Calcula el porcentaje de valores que coinciden entre columnas"""
        if not source.sample_values or not target.sample_values:
            return 0.0, 0.0
        
        # Obtener valores únicos de cada columna
        source_df = self.tables[source.table_name]
        target_df = self.tables[target.table_name]
        
        source_values = set(source_df[source.column_name].dropna().unique())
        target_values = set(target_df[target.column_name].dropna().unique())
        
        if not source_values or not target_values:
            return 0.0, 0.0
        
        # Calcular intersección
        intersection = source_values & target_values
        
        # Porcentaje de valores de source que están en target
        overlap_percentage = len(intersection) / len(source_values) * 100
        
        # Score basado en el overlap
        if overlap_percentage > 80:
            score = 1.0
        elif overlap_percentage > 50:
            score = 0.8
        elif overlap_percentage > 20:
            score = 0.5
        elif overlap_percentage > 5:
            score = 0.3
        else:
            score = overlap_percentage / 100
        
        return score, overlap_percentage
    
    def _compare_patterns(self, source: ColumnProfile, target: ColumnProfile) -> float:
        """Compara patrones de datos entre columnas"""
        if not source.value_patterns or not target.value_patterns:
            return 0.0
        
        # Encontrar el patrón dominante en cada columna
        source_dominant = max(source.value_patterns.items(), key=lambda x: x[1])[0]
        target_dominant = max(target.value_patterns.items(), key=lambda x: x[1])[0]
        
        if source_dominant == target_dominant:
            return 1.0
        
        # Patrones similares
        similar_patterns = {
            'numeric': ['numeric', 'alphanumeric'],
            'uuid': ['uuid', 'alphanumeric'],
            'email': ['email'],
            'date': ['date'],
            'phone': ['phone', 'numeric']
        }
        
        if source_dominant in similar_patterns:
            if target_dominant in similar_patterns[source_dominant]:
                return 0.7
        
        return 0.0
    
    def _remove_duplicate_relationships(self, candidates: List[RelationshipCandidate]) -> List[RelationshipCandidate]:
        """Elimina relaciones duplicadas (A->B y B->A)"""
        seen = set()
        unique = []
        
        for candidate in candidates:
            # Crear clave única ordenada
            key = tuple(sorted([
                f"{candidate.source_table}.{candidate.source_column}",
                f"{candidate.target_table}.{candidate.target_column}"
            ]))
            
            if key not in seen:
                seen.add(key)
                unique.append(candidate)
        
        return unique
    
    def print_results(self, candidates: List[RelationshipCandidate], top_n: int = 10):
        """Imprime los resultados de forma legible"""
        print(f"\n📊 Top {top_n} Relaciones Encontradas:")
        print("=" * 80)
        
        # Primero mostrar las PKs detectadas
        if self.primary_keys:
            print("\n🔑 Claves Primarias Detectadas:")
            for table, pk in self.primary_keys.items():
                print(f"  - {table}.{pk}")
            print()
        
        for i, candidate in enumerate(candidates[:top_n], 1):
            # Verificar si involucra PKs
            source_is_pk = self.primary_keys.get(candidate.source_table) == candidate.source_column
            target_is_pk = self.primary_keys.get(candidate.target_table) == candidate.target_column
            
            pk_info = ""
            if source_is_pk and target_is_pk:
                pk_info = " ⚠️ (Ambas son PKs - Probablemente incorrecta)"
            elif target_is_pk:
                pk_info = " ✓ (FK → PK)"
            elif source_is_pk:
                pk_info = " ⚠️ (PK → FK - Verificar dirección)"
            
            print(f"\n{i}. {candidate.source_table}.{candidate.source_column} → "
                  f"{candidate.target_table}.{candidate.target_column}{pk_info}")
            print(f"   Confianza: {candidate.confidence_score:.1%}")
            print("   Evidencia:")
            
            # Detalles de la evidencia
            evidence = candidate.evidence
            print(f"   - Similitud de nombres: {evidence['name_similarity']:.1%}")
            print(f"   - Compatibilidad de tipos: {evidence['type_compatibility']:.1%}")
            
            if 'value_overlap' in evidence:
                overlap = evidence['value_overlap']
                print(f"   - Coincidencia de valores: {overlap['percentage']:.1f}% "
                      f"(score: {overlap['score']:.1%})")
            
            print(f"   - Similitud de patrones: {evidence['pattern_similarity']:.1%}")
            
            # Mostrar información adicional si existe
            if evidence.get('both_are_pks'):
                print("   - ⚠️ ADVERTENCIA: Ambas columnas son claves primarias")
            if evidence.get('fk_pattern_bonus'):
                print(f"   - ✓ Bonus por patrón FK clásico: +{evidence['fk_pattern_bonus']:.1%}")
    
    def export_results(self, candidates: List[RelationshipCandidate], filename: str = "relationships.json"):
        """Exporta los resultados a JSON"""
        results = []
        for candidate in candidates:
            results.append({
                'source': f"{candidate.source_table}.{candidate.source_column}",
                'target': f"{candidate.target_table}.{candidate.target_column}",
                'confidence': round(candidate.confidence_score, 3),
                'evidence': candidate.evidence
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultados exportados a: {filename}")


# Función principal para usar el detector
def detect_relationships(tables: Dict[str, pd.DataFrame]):
    """Función principal para detectar relaciones"""
    detector = SmartRelationshipDetector(tables)
    candidates = detector.find_relationships()
    
    # Mostrar resultados
    detector.print_results(candidates, top_n=20)
    
    # Exportar resultados
    detector.export_results(candidates)
    
    return candidates


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de cómo usar
    print("Para usar este módulo:")
    print("1. Importa: from smartdbdetector import SmartRelationshipDetector")
    print("2. Carga tus tablas en un diccionario")
    print("3. Ejecuta: detector = SmartRelationshipDetector(tables)")
    print("4. Obtén candidatos: candidates = detector.find_relationships()")