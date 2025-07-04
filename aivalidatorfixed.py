import pandas as pd
import requests
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass
import time

@dataclass
class ValidationResult:
    """Resultado de validación con AI"""
    source: str
    target: str
    is_valid: bool
    confidence: float
    explanation: str
    raw_response: str

class AIRelationshipValidator:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama2:latest"):
        self.ollama_url = ollama_url
        self.model = model
        self.tables_data = {}
        
    def load_tables(self, tables: Dict[str, pd.DataFrame]):
        """Carga las tablas y prepara información para el contexto"""
        self.tables_data = {}
        for table_name, df in tables.items():
            self.tables_data[table_name] = {
                'columns': list(df.columns),
                'shape': df.shape,
                'sample': df.head(5).to_dict('records'),
                'dtypes': df.dtypes.to_dict()
            }
    
    def validate_relationship(self, source_table: str, source_column: str, 
                            target_table: str, target_column: str,
                            confidence_score: float, evidence: Dict) -> ValidationResult:
        """Valida una relación específica usando AI"""
        
        # Preparar el contexto con información correcta
        context = self._prepare_context(source_table, source_column, target_table, target_column, evidence)
        
        # Crear prompt mejorado
        prompt = f"""Analiza la siguiente relación potencial entre columnas de base de datos:

RELACIÓN PROPUESTA:
- Columna origen: {source_table}.{source_column}
- Columna destino: {target_table}.{target_column}

CONTEXTO DE LAS TABLAS:
{context}

EVIDENCIA ENCONTRADA:
- Similitud de nombres: {evidence.get('name_similarity', 0):.1%}
- Compatibilidad de tipos: {evidence.get('type_compatibility', 0):.1%}
- Coincidencia de valores: {evidence.get('value_overlap', {}).get('percentage', 0):.1f}%
- Score de confianza calculado: {confidence_score:.1%}

PREGUNTA: ¿Es válida y lógica esta relación desde el punto de vista del negocio?

Considera:
1. ¿Los nombres de las columnas sugieren una relación lógica?
2. ¿Los tipos de datos son compatibles?
3. ¿El porcentaje de valores coincidentes es significativo?
4. ¿La relación tiene sentido en el contexto del dominio (médico/veterinario)?

IMPORTANTE: Devuelve un JSON válido, en una sola línea, sin saltos de línea dentro de strings.
{{
    "es_valida": true/false,
    "confianza_ai": 0-100,
    "explicacion": "Explicación detallada",
    "tipo_relacion": "1:1|1:N|N:M",
    "recomendacion": "Usar como FK|Revisar manualmente|Descartar"
}}"""
        
        try:
            # Llamar a Ollama
            response = self._call_ollama(prompt)
            
            # Parsear respuesta
            result = self._parse_ai_response(response, source_table, source_column, 
                                           target_table, target_column)
            
            return result
            
        except Exception as e:
            print(f"❌ Error al validar con AI: {e}")
            return ValidationResult(
                source=f"{source_table}.{source_column}",
                target=f"{target_table}.{target_column}",
                is_valid=False,
                confidence=0.0,
                explanation=f"Error: {str(e)}",
                raw_response=""
            )
    
    def _prepare_context(self, source_table: str, source_column: str,
                        target_table: str, target_column: str, evidence: Dict) -> str:
        """Prepara el contexto con información correcta de las tablas"""
        context_parts = []
        
        # Información de la tabla/columna origen
        if source_table in self.tables_data:
            source_info = self.tables_data[source_table]
            context_parts.append(f"\nTabla {source_table}:")
            context_parts.append(f"- Columnas: {', '.join(source_info['columns'])}")
            context_parts.append(f"- Registros: {source_info['shape'][0]}")
            
            # Tipo de dato de la columna específica
            if source_column in source_info['dtypes']:
                context_parts.append(f"- Tipo de {source_column}: {source_info['dtypes'][source_column]}")
            
            # Mostrar algunos valores de ejemplo
            sample_values = []
            for record in source_info['sample'][:3]:
                if source_column in record and record[source_column] is not None:
                    sample_values.append(str(record[source_column]))
            if sample_values:
                context_parts.append(f"- Valores ejemplo de {source_column}: {', '.join(sample_values)}")
        
        # Información de la tabla/columna destino
        if target_table in self.tables_data:
            target_info = self.tables_data[target_table]
            context_parts.append(f"\nTabla {target_table}:")
            context_parts.append(f"- Columnas: {', '.join(target_info['columns'])}")
            context_parts.append(f"- Registros: {target_info['shape'][0]}")
            
            # Tipo de dato de la columna específica
            if target_column in target_info['dtypes']:
                context_parts.append(f"- Tipo de {target_column}: {target_info['dtypes'][target_column]}")
            
            # Mostrar algunos valores de ejemplo
            sample_values = []
            for record in target_info['sample'][:3]:
                if target_column in record and record[target_column] is not None:
                    sample_values.append(str(record[target_column]))
            if sample_values:
                context_parts.append(f"- Valores ejemplo de {target_column}: {', '.join(sample_values)}")
        
        return '\n'.join(context_parts)
    
    def _call_ollama(self, prompt: str) -> str:
        """Llama a Ollama y obtiene la respuesta"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1  # Baja temperatura para respuestas más consistentes
                },
                timeout=30
            )
            
            if response.status_code == 200:
                raw= response.json()['response']
                print(f"\n📥 Respuesta AI cruda:\n{raw}\n")
                return raw
            else:
                raise Exception(f"Error HTTP: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            raise Exception("No se puede conectar con Ollama. Asegúrate de que esté ejecutándose.")
        except Exception as e:
            raise Exception(f"Error al llamar a Ollama: {str(e)}")
    
    def _parse_ai_response(self, response: str, source_table: str, source_column: str,
                          target_table: str, target_column: str) -> ValidationResult:
        """Parsea la respuesta de la AI"""
        try:
            # Intentar extraer JSON de la respuesta
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                data = json.loads(json_str)
                
                return ValidationResult(
                    source=f"{source_table}.{source_column}",
                    target=f"{target_table}.{target_column}",
                    is_valid=data.get('es_valida', False),
                    confidence=data.get('confianza_ai', 0) / 100,
                    explanation=data.get('explicacion', 'Sin explicación'),
                    raw_response=response
                )
            else:
                # Si no hay JSON, intentar interpretar la respuesta
                is_valid = 'válida' in response.lower() or 'correcta' in response.lower()
                return ValidationResult(
                    source=f"{source_table}.{source_column}",
                    target=f"{target_table}.{target_column}",
                    is_valid=is_valid,
                    confidence=0.5,
                    explanation=response[:200],
                    raw_response=response
                )
                
        except Exception as e:
            print(f"⚠️ Error parseando respuesta AI: {e}")
            return ValidationResult(
                source=f"{source_table}.{source_column}",
                target=f"{target_table}.{target_column}",
                is_valid=False,
                confidence=0.0,
                explanation=f"Error parseando: {str(e)}",
                raw_response=response
            )
    
    def validate_batch(self, relationships: List[Tuple], tables: Dict[str, pd.DataFrame]) -> List[ValidationResult]:
        """Valida un batch de relaciones"""
        # Cargar información de las tablas
        self.load_tables(tables)
        
        results = []
        total = len(relationships)
        
        print(f"\n🤖 VALIDACIÓN AI - Modelo: {self.model}")
        print("=" * 60)
        
        for i, (source, target, confidence, evidence) in enumerate(relationships, 1):
            source_parts = source.split('.')
            target_parts = target.split('.')
            
            if len(source_parts) == 2 and len(target_parts) == 2:
                print(f"\n[{i}/{total}] Validando con AI:")
                print(f"   {source} → {target}")
                print(f"   🤖 Consultando {self.model}...")
                
                result = self.validate_relationship(
                    source_parts[0], source_parts[1],
                    target_parts[0], target_parts[1],
                    confidence, evidence
                )
                
                # Mostrar resultado
                status = "✅ VÁLIDA" if result.is_valid else "❌ NO VÁLIDA"
                print(f"   Resultado: {status} (Confianza AI: {result.confidence:.1%})")
                print(f"   Explicación: {result.explanation[:200]}...")
                
                results.append(result)
                
                # Pequeña pausa para no sobrecargar
                time.sleep(0.5)
        
        return results


# Función de integración completa
def analyze_database_with_ai(tables: Dict[str, pd.DataFrame], 
                           top_n: int = 10,
                           ollama_model: str = "llama2:latest"):
    """Análisis completo: detección + validación con AI"""
    
    print("🚀 ANÁLISIS COMPLETO DE BASE DE DATOS")
    print("=" * 60)
    
    # Fase 1: Detección inteligente
    from smartdbdetector import SmartRelationshipDetector
    
    detector = SmartRelationshipDetector(tables)
    candidates = detector.find_relationships()
    
    print(f"\n✅ Se encontraron {len(candidates)} relaciones potenciales")
    
    # Fase 2: Validación con AI de las top N
    validator = AIRelationshipValidator(model=ollama_model)
    
    # Preparar datos para validación
    relationships_to_validate = []
    for candidate in candidates[:top_n]:
        relationships_to_validate.append((
            f"{candidate.source_table}.{candidate.source_column}",
            f"{candidate.target_table}.{candidate.target_column}",
            candidate.confidence_score,
            candidate.evidence
        ))
    
    # Validar con AI
    validation_results = validator.validate_batch(relationships_to_validate, tables)
    
    # Resumen final
    print("\n📊 RESUMEN FINAL")
    print("=" * 60)
    
    valid_count = sum(1 for r in validation_results if r.is_valid)
    print(f"Relaciones validadas por AI: {valid_count}/{len(validation_results)}")
    
    print("\n✅ Relaciones confirmadas:")
    for result in validation_results:
        if result.is_valid:
            print(f"  - {result.source} → {result.target} (AI: {result.confidence:.1%})")
    
    return candidates, validation_results


# Ejemplo de uso
if __name__ == "__main__":
    # # Cargar tablas
    # tables = {
    #     'patients': pd.read_csv('patients.csv'),
    #     'appointments': pd.read_csv('appointments.csv'),
    #     'medications': pd.read_csv('medications.csv'),
    #     'pets': pd.read_csv('pets.csv')
    # }
    # 
    # # Ejecutar análisis completo
    # candidates, validations = analyze_database_with_ai(
    #     tables, 
    #     top_n=10,
    #     ollama_model="llama2:latest"
    # )
    pass
