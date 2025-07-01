#!/usr/bin/env python3
"""
Verificador LLM Robusto - Verifica relaciones detectadas usando LLM local
sin errores de serialización JSON
"""

import json
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass, asdict
import time
import traceback

logger = logging.getLogger(__name__)

@dataclass
class LLMVerificationResult:
    """Resultado de verificación por LLM"""
    relationship: str
    is_valid: bool
    confidence: float
    explanation: str
    suggested_cardinality: str
    concerns: List[str]
    llm_reasoning: str

class RobustLLMVerifier:
    """
    Verificador que usa LLM local (Ollama) para validar relaciones detectadas
    Maneja correctamente la serialización de datos y errores de conexión
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434", 
                 model_name: str = "llama2:latest", timeout: int = 30):
        """
        Inicializa el verificador LLM
        
        Args:
            ollama_url: URL del servidor Ollama
            model_name: Nombre del modelo a usar
            timeout: Timeout para las peticiones en segundos
        """
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.timeout = timeout
        self.available_models = []
        
        # Verificar conexión
        self._check_ollama_connection()
    
    def _check_ollama_connection(self) -> bool:
        """Verifica conexión con Ollama y obtiene modelos disponibles"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                self.available_models = [model['name'] for model in models_data.get('models', [])]
                
                if self.model_name not in self.available_models:
                    logger.warning(f"⚠️  Modelo {self.model_name} no disponible")
                    if self.available_models:
                        self.model_name = self.available_models[0]
                        logger.info(f"✅ Usando modelo alternativo: {self.model_name}")
                    else:
                        raise Exception("No hay modelos disponibles en Ollama")
                
                print(f"✅ Ollama conectado. Modelos disponibles: {self.available_models}")
                return True
            else:
                raise Exception(f"Error HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error conectando a Ollama: {e}")
            print("💡 Asegúrate de que Ollama esté corriendo: ollama serve")
            print("💡 Y que tengas un modelo instalado: ollama pull llama2")
            raise
    
    def verify_relationships(self, relationships: List[Dict], 
                           schema_info: Dict, 
                           sample_data: Dict[str, pd.DataFrame],
                           max_verifications: int = 5) -> List[LLMVerificationResult]:
        """
        Verifica una lista de relaciones usando el LLM
        
        Args:
            relationships: Lista de relaciones a verificar
            schema_info: Información del esquema
            sample_data: Datos de muestra
            max_verifications: Máximo número de relaciones a verificar
            
        Returns:
            Lista de resultados de verificación
        """
        print(f"🤖 FASE 3: Verificando relaciones con LLM (máx {max_verifications})...")
        
        results = []
        count = 0
        
        # Ordenar por confianza y tomar las top N
        sorted_relationships = sorted(relationships, 
                                    key=lambda x: x.get('confidence', 0), 
                                    reverse=True)
        
        for i, relationship in enumerate(sorted_relationships[:max_verifications]):
            count += 1
            print(f"  [{count}/{min(len(relationships), max_verifications)}] {relationship['from_table']}.{relationship['from_column']} → {relationship['to_table']}.{relationship['to_column']}")
            
            try:
                result = self._verify_single_relationship(relationship, schema_info, sample_data)
                results.append(result)
                
                # Pequeña pausa entre peticiones para no sobrecargar
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error verificando relación: {e}")
                # Crear resultado de error
                error_result = LLMVerificationResult(
                    relationship=f"{relationship['from_table']}.{relationship['from_column']} → {relationship['to_table']}.{relationship['to_column']}",
                    is_valid=False,
                    confidence=0.0,
                    explanation="Error en verificación LLM",
                    suggested_cardinality="unknown",
                    concerns=[f"Error técnico: {str(e)}"],
                    llm_reasoning="No se pudo obtener respuesta del LLM"
                )
                results.append(error_result)
        
        self._print_verification_results(results)
        return results
    
    def _verify_single_relationship(self, relationship: Dict, 
                                  schema_info: Dict,
                                  sample_data: Dict[str, pd.DataFrame]) -> LLMVerificationResult:
        """Verifica una sola relación usando el LLM"""
        
        # Preparar contexto para el LLM (SIN DataFrames)
        context = self._prepare_llm_context(relationship, schema_info, sample_data)
        
        # Crear prompt
        prompt = self._create_verification_prompt(context)
        
        # Llamar al LLM
        llm_response = self._call_ollama(prompt)
        
        # Parsear respuesta
        return self._parse_llm_response(llm_response, relationship)
    
    def _prepare_llm_context(self, relationship: Dict, 
                           schema_info: Dict,
                           sample_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Prepara contexto para el LLM convirtiendo DataFrames a texto/JSON serializable
        """
        from_table = relationship['from_table']
        from_column = relationship['from_column']
        to_table = relationship['to_table']
        to_column = relationship['to_column']
        
        context = {
            'relationship': {
                'from': f"{from_table}.{from_column}",
                'to': f"{to_table}.{to_column}",
                'confidence': relationship.get('confidence', 0)
            },
            'schema': {
                'from_table': self._serialize_table_info(schema_info['tables'][from_table]),
                'to_table': self._serialize_table_info(schema_info['tables'][to_table])
            },
            'sample_data': {
                'from_table_sample': self._serialize_dataframe(sample_data.get(from_table, pd.DataFrame())),
                'to_table_sample': self._serialize_dataframe(sample_data.get(to_table, pd.DataFrame()))
            }
        }
        
        return context
    
    def _serialize_table_info(self, table_info: Dict) -> Dict[str, Any]:
        """Serializa información de tabla para el LLM"""
        return {
            'total_columns': table_info['total_columns'],
            'row_count': table_info['row_count'],
            'primary_keys': table_info['primary_keys'],
            'columns': {
                col_name: {
                    'type': col_info['type'],
                    'is_primary_key': col_info['is_primary_key'],
                    'not_null': col_info['not_null']
                }
                for col_name, col_info in table_info['columns'].items()
            }
        }
    
    def _serialize_dataframe(self, df: pd.DataFrame, max_rows: int = 3) -> Dict[str, Any]:
        """
        Convierte DataFrame a formato serializable JSON eliminando el error de serialización
        """
        if df.empty:
            return {'empty': True, 'columns': [], 'data': []}
        
        try:
            # Tomar solo las primeras filas y convertir a tipos serializables
            sample_df = df.head(max_rows).copy()
            
            # Convertir todos los valores a tipos serializables
            serializable_data = []
            for _, row in sample_df.iterrows():
                row_data = {}
                for col, value in row.items():
                    # Convertir tipos numpy/pandas a tipos Python nativos
                    if pd.isna(value) or value is None:
                        row_data[col] = None
                    elif isinstance(value, (np.integer, np.int64, np.int32)):
                        row_data[col] = int(value)
                    elif isinstance(value, (np.floating, np.float64, np.float32)):
                        row_data[col] = float(value)
                    elif isinstance(value, np.bool_):
                        row_data[col] = bool(value)
                    else:
                        row_data[col] = str(value)
                
                serializable_data.append(row_data)
            
            return {
                'empty': False,
                'columns': list(df.columns),
                'row_count': len(df),
                'sample_data': serializable_data
            }
            
        except Exception as e:
            logger.debug(f"Error serializando DataFrame: {e}")
            return {
                'empty': True,
                'columns': list(df.columns) if not df.empty else [],
                'data': [],
                'error': f"Serialization error: {str(e)}"
            }
    
    def _create_verification_prompt(self, context: Dict[str, Any]) -> str:
        """Crea el prompt para verificación de relaciones"""
        relationship = context['relationship']
        from_table_info = context['schema']['from_table']
        to_table_info = context['schema']['to_table']
        from_sample = context['sample_data']['from_table_sample']
        to_sample = context['sample_data']['to_table_sample']
        
        prompt = f"""
Eres un experto en bases de datos. Analiza si la siguiente relación foreign key es válida:

RELACIÓN PROPUESTA:
{relationship['from']} → {relationship['to']}
Confianza detectada: {relationship['confidence']:.1f}%

INFORMACIÓN DE ESQUEMA:
Tabla origen: {relationship['from'].split('.')[0]}
- Columnas: {len(from_table_info['columns'])}
- Filas: {from_table_info['row_count']}
- Primary keys: {from_table_info['primary_keys']}

Tabla destino: {relationship['to'].split('.')[0]}  
- Columnas: {len(to_table_info['columns'])}
- Filas: {to_table_info['row_count']}
- Primary keys: {to_table_info['primary_keys']}

DATOS DE MUESTRA:
Tabla origen ({relationship['from'].split('.')[0]}):
{self._format_sample_data(from_sample)}

Tabla destino ({relationship['to'].split('.')[0]}):
{self._format_sample_data(to_sample)}

INSTRUCCIONES:
Analiza la relación y responde SOLO en formato JSON con esta estructura exacta:
{{
    "is_valid": true/false,
    "confidence": 0-100,
    "explanation": "Explicación breve de por qué es válida o no",
    "cardinality": "1:1" o "1:N" o "N:M" o "unknown",
    "concerns": ["lista", "de", "posibles", "problemas"],
    "reasoning": "Razonamiento detallado del análisis"
}}

Considera:
1. ¿Los nombres de columnas sugieren una relación FK?
2. ¿Los tipos de datos son compatibles?
3. ¿Los datos de muestra validan la relación?
4. ¿La cardinalidad es lógica?
5. ¿Hay problemas potenciales?
"""
        
        return prompt.strip()
    
    def _format_sample_data(self, sample_data: Dict[str, Any]) -> str:
        """Formatea datos de muestra para el prompt"""
        if sample_data.get('empty', True):
            return "No hay datos de muestra disponibles"
        
        try:
            formatted = f"Columnas: {', '.join(sample_data['columns'])}\n"
            formatted += f"Filas totales: {sample_data['row_count']}\n"
            
            if sample_data.get('sample_data'):
                formatted += "Muestra de datos:\n"
                for i, row in enumerate(sample_data['sample_data'], 1):
                    row_str = ', '.join(f"{k}={v}" for k, v in row.items())
                    formatted += f"  Fila {i}: {row_str}\n"
            
            return formatted
        except Exception as e:
            return f"Error formateando datos: {str(e)}"
    
    def _call_ollama(self, prompt: str) -> str:
        """Llama al API de Ollama"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Baja temperatura para respuestas más consistentes
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            raise Exception("Timeout en petición al LLM")
        except requests.exceptions.ConnectionError:
            raise Exception("Error de conexión con Ollama")
        except Exception as e:
            raise Exception(f"Error llamando a Ollama: {str(e)}")
    
    def _parse_llm_response(self, response: str, relationship: Dict) -> LLMVerificationResult:
        """Parsea la respuesta del LLM"""
        try:
            # Intentar extraer JSON de la respuesta
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)
                
                return LLMVerificationResult(
                    relationship=f"{relationship['from_table']}.{relationship['from_column']} → {relationship['to_table']}.{relationship['to_column']}",
                    is_valid=parsed.get('is_valid', False),
                    confidence=float(parsed.get('confidence', 0)),
                    explanation=parsed.get('explanation', ''),
                    suggested_cardinality=parsed.get('cardinality', 'unknown'),
                    concerns=parsed.get('concerns', []),
                    llm_reasoning=parsed.get('reasoning', response)
                )
            else:
                # Si no hay JSON válido, crear respuesta de fallback
                return self._create_fallback_result(response, relationship)
                
        except json.JSONDecodeError as e:
            logger.debug(f"Error parseando JSON del LLM: {e}")
            return self._create_fallback_result(response, relationship)
        except Exception as e:
            logger.error(f"Error procesando respuesta del LLM: {e}")
            return self._create_fallback_result(response, relationship)
    
    def _create_fallback_result(self, response: str, relationship: Dict) -> LLMVerificationResult:
        """Crea resultado de fallback cuando no se puede parsear la respuesta"""
        # Análisis simple basado en palabras clave
        response_lower = response.lower()
        
        is_valid = any(word in response_lower for word in ['valid', 'correct', 'good', 'yes', 'true'])
        confidence = 50.0  # Confianza media por defecto
        
        return LLMVerificationResult(
            relationship=f"{relationship['from_table']}.{relationship['from_column']} → {relationship['to_table']}.{relationship['to_column']}",
            is_valid=is_valid,
            confidence=confidence,
            explanation="Respuesta del LLM no estructurada",
            suggested_cardinality="unknown",
            concerns=["Respuesta del LLM no seguía el formato esperado"],
            llm_reasoning=response[:500]  # Truncar respuesta larga
        )
    
    def _print_verification_results(self, results: List[LLMVerificationResult]):
        """Imprime resultados de verificación"""
        if not results:
            print("❌ No se pudieron verificar relaciones")
            return
        
        print(f"\n🤖 RESULTADOS DE VERIFICACIÓN LLM")
        print("=" * 70)
        
        valid_count = sum(1 for r in results if r.is_valid)
        
        for result in results:
            status = "✅ VÁLIDA" if result.is_valid else "❌ INVÁLIDA"
            print(f"\n{status} - {result.relationship}")
            print(f"  Confianza LLM: {result.confidence:.1f}%")
            print(f"  Explicación: {result.explanation}")
            
            if result.suggested_cardinality != "unknown":
                print(f"  Cardinalidad sugerida: {result.suggested_cardinality}")
            
            if result.concerns:
                print(f"  Preocupaciones: {', '.join(result.concerns)}")
        
        print(f"\nResumen: {valid_count}/{len(results)} relaciones validadas por LLM")


# Función de utilidad
def verify_relationships_with_llm(relationships: List[Dict], 
                                schema_info: Dict,
                                sample_data: Dict[str, pd.DataFrame],
                                ollama_url: str = "http://localhost:11434",
                                model_name: str = "llama2:latest",
                                max_verifications: int = 5) -> List[LLMVerificationResult]:
    """
    Función de conveniencia para verificar relaciones con LLM
    """
    verifier = RobustLLMVerifier(ollama_url, model_name)
    return verifier.verify_relationships(relationships, schema_info, sample_data, max_verifications)


if __name__ == "__main__":
    print("🤖 Verificador LLM Robusto")
    print("Asegúrate de tener Ollama corriendo: ollama serve")
    print("Y un modelo instalado: ollama pull llama2")
