#!/usr/bin/env python3
"""
Detector de Relaciones con Embeddings - Versión avanzada que usa
sentence transformers para detectar relaciones semánticas
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RelationshipCandidate:
    """Clase para representar una relación candidata"""
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    confidence: float
    similarity_scores: Dict[str, float]
    reasoning: List[str]
    relationship_type: str = "foreign_key"

class EmbeddingRelationshipDetector:
    """
    Detector avanzado de relaciones que usa embeddings semánticos
    para identificar relaciones potenciales entre tablas
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Inicializa el detector con un modelo de embeddings
        
        Args:
            model_name: Nombre del modelo de sentence-transformers a usar
        """
        self.model_name = model_name
        self.model = None
        self._initialize_model()
        
        # Patrones y reglas mejoradas
        self.fk_patterns = [
            r'.*_id$', r'.*_key$', r'.*_fk$', r'.*_ref$', r'.*_reference$',
            r'id_.*', r'fk_.*', r'ref_.*', r'.*_foreign$', r'.*_link$'
        ]
        
        self.relationship_context_words = {
            'customer': ['user', 'client', 'account', 'person', 'buyer'],
            'product': ['item', 'article', 'goods', 'merchandise'],
            'order': ['sale', 'purchase', 'transaction', 'invoice'],
            'category': ['type', 'class', 'group', 'classification'],
            'address': ['location', 'place', 'region', 'area'],
            'payment': ['transaction', 'billing', 'invoice', 'charge'],
            'employee': ['staff', 'worker', 'person', 'user'],
            'company': ['organization', 'business', 'firm', 'enterprise']
        }
    
    def _initialize_model(self):
        """Inicializa el modelo de embeddings"""
        try:
            print(f"🤖 Cargando modelo de embeddings: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            print("✅ Modelo de embeddings cargado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error cargando modelo de embeddings: {e}")
            print("💡 Instalando sentence-transformers: pip install sentence-transformers")
            raise
    
    def detect_relationships(self, schema_info: Dict, sample_data: Dict[str, pd.DataFrame]) -> List[RelationshipCandidate]:
        """
        Detecta relaciones potenciales usando múltiples estrategias
        
        Args:
            schema_info: Información del esquema de la BD
            sample_data: Datos de muestra para validación
            
        Returns:
            Lista de relaciones candidatas ordenadas por confianza
        """
        print("🔍 Detectando relaciones con embeddings semánticos...")
        
        candidates = []
        tables = schema_info['tables']
        
        # Generar embeddings para todas las tablas y columnas
        embeddings_cache = self._generate_embeddings_cache(tables)
        
        # Detectar relaciones usando diferentes estrategias
        for from_table, from_table_info in tables.items():
            for from_column, from_col_info in from_table_info['columns'].items():
                
                # Saltar primary keys (no pueden ser FKs)
                if from_col_info['is_primary_key']:
                    continue
                
                # Buscar relaciones potenciales
                table_candidates = self._find_candidates_for_column(
                    from_table, from_column, from_col_info,
                    tables, embeddings_cache, sample_data
                )
                candidates.extend(table_candidates)
        
        # Filtrar y ordenar candidatos
        candidates = self._filter_and_rank_candidates(candidates)
        
        print(f"✅ Se detectaron {len(candidates)} relaciones potenciales")
        return candidates
    
    def _generate_embeddings_cache(self, tables: Dict) -> Dict[str, np.ndarray]:
        """Genera y cachea embeddings para tablas y columnas"""
        cache = {}
        
        print("🧠 Generando embeddings semánticos...")
        
        # Embeddings para nombres de tablas
        table_names = list(tables.keys())
        table_descriptions = [self._create_table_description(name, tables[name]) for name in table_names]
        table_embeddings = self.model.encode(table_descriptions)
        
        for i, table_name in enumerate(table_names):
            cache[f"table_{table_name}"] = table_embeddings[i]
        
        # Embeddings para columnas
        for table_name, table_info in tables.items():
            column_names = list(table_info['columns'].keys())
            column_descriptions = [
                self._create_column_description(table_name, col_name, table_info['columns'][col_name])
                for col_name in column_names
            ]
            
            if column_descriptions:
                column_embeddings = self.model.encode(column_descriptions)
                for i, col_name in enumerate(column_names):
                    cache[f"column_{table_name}_{col_name}"] = column_embeddings[i]
        
        return cache
    
    def _create_table_description(self, table_name: str, table_info: Dict) -> str:
        """Crea una descripción textual de una tabla para embeddings"""
        # Usar el nombre de la tabla y sus primary keys
        pk_info = ""
        if table_info['primary_keys']:
            pk_info = f" with primary key {', '.join(table_info['primary_keys'])}"
        
        return f"database table named {table_name}{pk_info} containing {table_info['total_columns']} columns"
    
    def _create_column_description(self, table_name: str, column_name: str, column_info: Dict) -> str:
        """Crea una descripción textual de una columna para embeddings"""
        type_info = column_info['type']
        role_info = ""
        
        if column_info['is_primary_key']:
            role_info = " primary key"
        elif self._matches_fk_pattern(column_name):
            role_info = " foreign key reference"
        
        return f"column {column_name} of type {type_info}{role_info} in table {table_name}"
    
    def _find_candidates_for_column(self, from_table: str, from_column: str, 
                                  from_col_info: Dict, all_tables: Dict,
                                  embeddings_cache: Dict, sample_data: Dict) -> List[RelationshipCandidate]:
        """Encuentra candidatos de relación para una columna específica"""
        candidates = []
        
        for to_table, to_table_info in all_tables.items():
            if to_table == from_table:
                continue
            
            for to_column, to_col_info in to_table_info['columns'].items():
                # Solo considerar primary keys como targets
                if not to_col_info['is_primary_key']:
                    continue
                
                # Calcular múltiples puntuaciones de similitud
                similarity_scores = self._calculate_comprehensive_similarity(
                    from_table, from_column, from_col_info,
                    to_table, to_column, to_col_info,
                    embeddings_cache, sample_data
                )
                
                # Calcular confianza total
                confidence, reasoning = self._calculate_confidence_with_reasoning(
                    similarity_scores, from_table, from_column, to_table, to_column
                )
                
                # Filtrar candidatos de baja confianza
                if confidence >= 30:  # Umbral mínimo
                    candidates.append(RelationshipCandidate(
                        from_table=from_table,
                        from_column=from_column,
                        to_table=to_table,
                        to_column=to_column,
                        confidence=confidence,
                        similarity_scores=similarity_scores,
                        reasoning=reasoning
                    ))
        
        return candidates
    
    def _calculate_comprehensive_similarity(self, from_table: str, from_column: str, from_col_info: Dict,
                                         to_table: str, to_column: str, to_col_info: Dict,
                                         embeddings_cache: Dict, sample_data: Dict) -> Dict[str, float]:
        """Calcula múltiples puntuaciones de similitud"""
        scores = {}
        
        # 1. Similitud por nombres exactos
        scores['name_exact'] = self._exact_name_similarity(from_column, to_column)
        
        # 2. Similitud por patrones FK
        scores['fk_pattern'] = self._fk_pattern_similarity(from_column, to_column, to_table)
        
        # 3. Similitud semántica usando embeddings
        scores['semantic'] = self._semantic_similarity_embeddings(
            from_table, from_column, to_table, to_column, embeddings_cache
        )
        
        # 4. Similitud contextual (relaciones entre conceptos)
        scores['contextual'] = self._contextual_similarity(from_table, from_column, to_table, to_column)
        
        # 5. Validación con datos de muestra
        scores['data_validation'] = self._data_validation_score(
            from_table, from_column, to_table, to_column, sample_data
        )
        
        # 6. Compatibilidad de tipos de datos
        scores['type_compatibility'] = self._type_compatibility_score(from_col_info, to_col_info)
        
        return scores
    
    def _exact_name_similarity(self, from_column: str, to_column: str) -> float:
        """Similitud por nombres exactos o muy similares"""
        from_col_lower = from_column.lower()
        to_col_lower = to_column.lower()
        
        if from_col_lower == to_col_lower:
            return 1.0
        
        # Casos comunes: customer_id -> id, user_id -> id, etc.
        if to_col_lower == 'id' and from_col_lower.endswith('_id'):
            base_name = from_col_lower[:-3]  # Remover '_id'
            return 0.9
        
        if to_col_lower == 'id' and from_col_lower.endswith('_key'):
            return 0.8
        
        # Similitud por substring
        if from_col_lower in to_col_lower or to_col_lower in from_col_lower:
            return 0.7
        
        return 0.0
    
    def _fk_pattern_similarity(self, from_column: str, to_column: str, to_table: str) -> float:
        """Similitud basada en patrones de foreign keys"""
        score = 0.0
        from_col_lower = from_column.lower()
        to_table_lower = to_table.lower()
        
        # Verificar patrones FK
        for pattern in self.fk_patterns:
            if re.match(pattern, from_col_lower):
                score += 0.3
                break
        
        # Bonus si el nombre de la columna contiene el nombre de la tabla
        table_singular = to_table_lower.rstrip('s')  # users -> user
        if table_singular in from_col_lower:
            score += 0.6
        elif to_table_lower in from_col_lower:
            score += 0.5
        
        return min(score, 1.0)
    
    def _semantic_similarity_embeddings(self, from_table: str, from_column: str,
                                      to_table: str, to_column: str,
                                      embeddings_cache: Dict) -> float:
        """Similitud semántica usando embeddings"""
        try:
            # Obtener embeddings de las columnas
            from_key = f"column_{from_table}_{from_column}"
            to_key = f"column_{to_table}_{to_column}"
            
            if from_key not in embeddings_cache or to_key not in embeddings_cache:
                return 0.0
            
            from_embedding = embeddings_cache[from_key].reshape(1, -1)
            to_embedding = embeddings_cache[to_key].reshape(1, -1)
            
            # Calcular similitud coseno
            similarity = cosine_similarity(from_embedding, to_embedding)[0][0]
            
            # Normalizar a rango [0, 1]
            return max(0, similarity)
            
        except Exception as e:
            logger.debug(f"Error calculando similitud semántica: {e}")
            return 0.0
    
    def _contextual_similarity(self, from_table: str, from_column: str,
                             to_table: str, to_column: str) -> float:
        """Similitud basada en contexto y relaciones conceptuales"""
        score = 0.0
        
        from_table_lower = from_table.lower()
        from_column_lower = from_column.lower()
        to_table_lower = to_table.lower()
        
        # Buscar relaciones conceptuales conocidas
        for concept, related_words in self.relationship_context_words.items():
            # Si la tabla destino es del concepto
            if concept in to_table_lower or to_table_lower in concept:
                # Y la columna origen contiene palabras relacionadas
                for word in [concept] + related_words:
                    if word in from_column_lower or word in from_table_lower:
                        score += 0.4
                        break
            
            # Viceversa
            if concept in from_column_lower or concept in from_table_lower:
                for word in [concept] + related_words:
                    if word in to_table_lower:
                        score += 0.3
                        break
        
        return min(score, 1.0)
    
    def _data_validation_score(self, from_table: str, from_column: str,
                             to_table: str, to_column: str,
                             sample_data: Dict) -> float:
        """Validación usando datos de muestra"""
        try:
            from_df = sample_data.get(from_table, pd.DataFrame())
            to_df = sample_data.get(to_table, pd.DataFrame())
            
            if from_df.empty or to_df.empty:
                return 0.0
            
            if from_column not in from_df.columns or to_column not in to_df.columns:
                return 0.0
            
            # Obtener valores únicos (sin NaN)
            from_values = set(from_df[from_column].dropna().astype(str))
            to_values = set(to_df[to_column].dropna().astype(str))
            
            if not from_values or not to_values:
                return 0.0
            
            # Calcular intersección
            intersection = from_values.intersection(to_values)
            
            if not intersection:
                return 0.0
            
            # Calcular porcentaje de coincidencias
            match_ratio = len(intersection) / len(from_values)
            
            # Bonificar si hay alta coincidencia
            if match_ratio >= 0.8:
                return 1.0
            elif match_ratio >= 0.6:
                return 0.8
            elif match_ratio >= 0.4:
                return 0.6
            elif match_ratio >= 0.2:
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            logger.debug(f"Error en validación de datos: {e}")
            return 0.0
    
    def _type_compatibility_score(self, from_col_info: Dict, to_col_info: Dict) -> float:
        """Compatibilidad de tipos de datos"""
        from_type = from_col_info['type'].upper()
        to_type = to_col_info['type'].upper()
        
        # Grupos de tipos compatibles
        integer_types = ['INTEGER', 'INT', 'BIGINT', 'SMALLINT', 'TINYINT']
        string_types = ['VARCHAR', 'CHAR', 'TEXT', 'STRING']
        decimal_types = ['DECIMAL', 'NUMERIC', 'FLOAT', 'REAL', 'DOUBLE']
        
        type_groups = [integer_types, string_types, decimal_types]
        
        for group in type_groups:
            from_matches = any(t in from_type for t in group)
            to_matches = any(t in to_type for t in group)
            
            if from_matches and to_matches:
                return 1.0
        
        return 0.0
    
    def _matches_fk_pattern(self, column_name: str) -> bool:
        """Verifica si una columna coincide con patrones de FK"""
        for pattern in self.fk_patterns:
            if re.match(pattern, column_name.lower()):
                return True
        return False
    
    def _calculate_confidence_with_reasoning(self, similarity_scores: Dict[str, float],
                                           from_table: str, from_column: str,
                                           to_table: str, to_column: str) -> Tuple[float, List[str]]:
        """Calcula confianza total y proporciona razonamiento"""
        reasoning = []
        
        # Pesos para diferentes tipos de similitud
        weights = {
            'name_exact': 0.25,
            'fk_pattern': 0.20,
            'semantic': 0.20,
            'contextual': 0.15,
            'data_validation': 0.15,
            'type_compatibility': 0.05
        }
        
        # Calcular puntuación ponderada
        total_score = 0.0
        for score_type, score_value in similarity_scores.items():
            weight = weights.get(score_type, 0.0)
            total_score += score_value * weight
            
            # Agregar explicaciones
            if score_value > 0.5:
                if score_type == 'name_exact':
                    reasoning.append(f"Nombres similares: {from_column} ≈ {to_column}")
                elif score_type == 'fk_pattern':
                    reasoning.append(f"Patrón FK detectado en {from_column}")
                elif score_type == 'semantic':
                    reasoning.append("Alta similitud semántica")
                elif score_type == 'contextual':
                    reasoning.append("Relación contextual encontrada")
                elif score_type == 'data_validation':
                    reasoning.append("Validado con datos de muestra")
                elif score_type == 'type_compatibility':
                    reasoning.append("Tipos de datos compatibles")
        
        # Convertir a porcentaje
        confidence = min(total_score * 100, 100.0)
        
        # Ajustes adicionales
        if similarity_scores.get('data_validation', 0) > 0.8:
            confidence += 10  # Bonus por validación sólida con datos
            reasoning.append("Fuerte validación con datos reales")
        
        if similarity_scores.get('name_exact', 0) == 1.0:
            confidence += 5  # Bonus por coincidencia exacta de nombres
        
        return confidence, reasoning
    
    def _filter_and_rank_candidates(self, candidates: List[RelationshipCandidate]) -> List[RelationshipCandidate]:
        """Filtra y ordena candidatos por confianza"""
        # Filtrar candidatos de muy baja confianza
        filtered = [c for c in candidates if c.confidence >= 30]
        
        # Eliminar duplicados (misma relación detectada múltiples veces)
        seen = set()
        unique_candidates = []
        
        for candidate in filtered:
            key = (candidate.from_table, candidate.from_column, 
                   candidate.to_table, candidate.to_column)
            if key not in seen:
                seen.add(key)
                unique_candidates.append(candidate)
        
        # Ordenar por confianza descendente
        unique_candidates.sort(key=lambda x: x.confidence, reverse=True)
        
        return unique_candidates
    
    def print_detection_results(self, candidates: List[RelationshipCandidate]):
        """Imprime resultados de detección formateados"""
        if not candidates:
            print("❌ No se detectaron relaciones potenciales")
            return
        
        print(f"\n🔍 RELACIONES DETECTADAS CON EMBEDDINGS")
        print("=" * 70)
        
        # Agrupar por nivel de confianza
        high_conf = [c for c in candidates if c.confidence >= 80]
        medium_conf = [c for c in candidates if 60 <= c.confidence < 80]
        low_conf = [c for c in candidates if c.confidence < 60]
        
        for group, title, emoji in [
            (high_conf, "ALTA CONFIANZA (80%+)", "🟢"),
            (medium_conf, "CONFIANZA MEDIA (60-79%)", "🟡"),
            (low_conf, "BAJA CONFIANZA (30-59%)", "🔴")
        ]:
            if group:
                print(f"\n{emoji} {title}")
                print("-" * 50)
                
                for candidate in group:
                    print(f"{candidate.from_table}.{candidate.from_column} → {candidate.to_table}.{candidate.to_column}")
                    print(f"  Confianza: {candidate.confidence:.1f}%")
                    if candidate.reasoning:
                        print(f"  Razones: {', '.join(candidate.reasoning)}")
                    print()
        
        print(f"Total de relaciones detectadas: {len(candidates)}")


# Función de utilidad
def detect_relationships_with_embeddings(schema_info: Dict, sample_data: Dict,
                                        model_name: str = "all-MiniLM-L6-v2") -> List[RelationshipCandidate]:
    """
    Función de conveniencia para detectar relaciones usando embeddings
    """
    detector = EmbeddingRelationshipDetector(model_name)
    return detector.detect_relationships(schema_info, sample_data)


if __name__ == "__main__":
    # Ejemplo de uso básico
    print("🤖 Detector de Relaciones con Embeddings")
    print("Instala las dependencias: pip install sentence-transformers scikit-learn")
