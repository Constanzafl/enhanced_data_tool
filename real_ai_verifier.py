#!/usr/bin/env python3
"""
Real AI Verifier - Enhanced Data Tool v2.0
Verificador REAL usando Ollama LLM (no simulado)
"""

import requests
import json
import pandas as pd
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class AIValidationResult:
    """Resultado real de validación AI"""
    relationship: str
    is_valid: bool
    confidence_score: float
    explanation: str
    suggested_cardinality: str
    reasoning_steps: List[str]
    llm_raw_response: str
    validation_timestamp: str

class RealAIVerifier:
    """
    Verificador AI REAL usando Ollama
    Hace llamadas reales al LLM para validar relaciones
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434", 
                 model_name: str = "llama3.2:3b", timeout: int = 60):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.timeout = timeout
        self.available_models = []
        
        # Verificar conexión real
        self._check_ollama_connection()
    
    def _check_ollama_connection(self) -> bool:
        """Verifica conexión REAL con Ollama"""
        try:
            print("🔍 Verificando conexión con Ollama...")
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            
            if response.status_code == 200:
                models_data = response.json()
                self.available_models = [model['name'] for model in models_data.get('models', [])]
                
                print(f"✅ Ollama conectado exitosamente")
                print(f"🤖 Modelos disponibles: {self.available_models}")
                
                # Verificar si el modelo deseado está disponible
                if self.model_name not in self.available_models:
                    if self.available_models:
                        print(f"⚠️  Modelo {self.model_name} no encontrado")
                        self.model_name = self.available_models[0]
                        print(f"✅ Usando: {self.model_name}")
                    else:
                        raise Exception("No hay modelos instalados en Ollama")
                
                return True
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error conectando a Ollama: {e}")
            print("💡 Soluciones:")
            print("   1. Instalar Ollama: https://ollama.ai")
            print("   2. Iniciar servidor: ollama serve")
            print("   3. Instalar modelo: ollama pull llama3.2:3b")
            raise Exception(f"Ollama no disponible: {e}")
    
    def validate_relationships_with_real_ai(self, relationships: List[Dict], 
                                          csv_data: Dict[str, pd.DataFrame],
                                          max_validations: int = 5) -> List[AIValidationResult]:
        """
        Valida relaciones usando LLM REAL
        """
        print(f"\n🤖 VALIDACIÓN AI REAL - Modelo: {self.model_name}")
        print("=" * 60)
        
        results = []
        
        # Tomar las mejores relaciones para validar
        sorted_relationships = sorted(relationships, 
                                    key=lambda x: x.get('confidence', 0), 
                                    reverse=True)
        
        for i, relationship in enumerate(sorted_relationships[:max_validations]):
            print(f"\n[{i+1}/{max_validations}] Validando con AI:")
            print(f"   {relationship['relation']}")
            
            try:
                # Llamada REAL al LLM
                ai_result = self._validate_single_relationship_real(relationship, csv_data)
                results.append(ai_result)
                
                # Mostrar resultado
                status = "✅ VÁLIDA" if ai_result.is_valid else "❌ INVÁLIDA"
                print(f"   Resultado: {status} (Confianza AI: {ai_result.confidence_score:.1f}%)")
                print(f"   Explicación: {ai_result.explanation}")
                
                # Pausa entre llamadas para no sobrecargar
                if i < max_validations - 1:
                    time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Error con AI: {e}")
                # Crear resultado de error
                error_result = AIValidationResult(
                    relationship=relationship['relation'],
                    is_valid=False,
                    confidence_score=0.0,
                    explanation=f"Error en validación AI: {str(e)}",
                    suggested_cardinality="unknown",
                    reasoning_steps=[f"Error técnico: {str(e)}"],
                    llm_raw_response="",
                    validation_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
                )
                results.append(error_result)
        
        # Resumen de validación AI
        valid_count = len([r for r in results if r.is_valid])
        print(f"\n🤖 RESUMEN VALIDACIÓN AI:")
        print(f"   Total validadas: {len(results)}")
        print(f"   ✅ Confirmadas: {valid_count}")
        print(f"   ❌ Rechazadas: {len(results) - valid_count}")
        
        return results
    
    def _validate_single_relationship_real(self, relationship: Dict, 
                                         csv_data: Dict[str, pd.DataFrame]) -> AIValidationResult:
        """Valida UNA relación usando LLM REAL"""
        
        # Preparar contexto para el LLM
        context = self._prepare_context_for_llm(relationship, csv_data)
        
        # Crear prompt especializado
        prompt = self._create_relationship_validation_prompt(context)
        
        # Llamada REAL a Ollama
        llm_response = self._call_ollama_real(prompt)
        
        # Parsear respuesta del LLM
        validation_result = self._parse_llm_response_real(llm_response, relationship)
        
        return validation_result
    
    def _prepare_context_for_llm(self, relationship: Dict, 
                                csv_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Prepara contexto rico para el LLM"""
        
        # Extraer información de la relación
        relation_parts = relationship['relation'].split(' → ')
        from_table_col = relation_parts[0].split('.')
        to_table_col = relation_parts[1].split('.')
        
        from_table, from_col = from_table_col[0], from_table_col[1]
        to_table, to_col = to_table_col[0], to_table_col[1]
        
        # Obtener datos reales
        from_df = csv_data[from_table]
        to_df = csv_data[to_table]
        
        # Análisis de datos
        from_values = from_df[from_col].dropna()
        to_values = to_df[to_col].dropna()
        
        # Muestras de datos (sin problemas de serialización)
        from_sample = from_values.head(5).astype(str).tolist()
        to_sample = to_values.head(5).astype(str).tolist()
        
        # Intersección
        intersection = set(from_values.astype(str)).intersection(set(to_values.astype(str)))
        shared_sample = list(intersection)[:5]
        
        # Estadísticas
        context = {
            'relationship': relationship['relation'],
            'confidence': relationship.get('confidence', 0),
            'overlap_ratio': relationship.get('overlap_ratio', 0),
            'from_table_info': {
                'name': from_table,
                'column': from_col,
                'total_rows': len(from_df),
                'unique_values': len(from_values.unique()),
                'sample_values': from_sample,
                'data_type': str(from_values.dtype)
            },
            'to_table_info': {
                'name': to_table,
                'column': to_col,
                'total_rows': len(to_df),
                'unique_values': len(to_values.unique()),
                'sample_values': to_sample,
                'data_type': str(to_values.dtype)
            },
            'relationship_evidence': {
                'shared_values_count': len(intersection),
                'shared_values_sample': shared_sample,
                'overlap_percentage': len(intersection) / len(from_values.unique()) * 100 if len(from_values.unique()) > 0 else 0
            }
        }
        
        return context
    
    def _create_relationship_validation_prompt(self, context: Dict[str, Any]) -> str:
        """Crea prompt especializado para validación de relaciones"""
        
        relationship = context['relationship']
        from_info = context['from_table_info']
        to_info = context['to_table_info']
        evidence = context['relationship_evidence']
        
        prompt = f"""Eres un experto en bases de datos y análisis de relaciones. Analiza si la siguiente relación entre tablas CSV es válida y lógica.

RELACIÓN PROPUESTA:
{relationship}

INFORMACIÓN DE TABLAS:
Tabla origen: {from_info['name']}
- Columna: {from_info['column']}
- Tipo: {from_info['data_type']}
- Filas totales: {from_info['total_rows']}
- Valores únicos: {from_info['unique_values']}
- Muestra de valores: {from_info['sample_values']}

Tabla destino: {to_info['name']}
- Columna: {to_info['column']}
- Tipo: {to_info['data_type']}
- Filas totales: {to_info['total_rows']}
- Valores únicos: {to_info['unique_values']}
- Muestra de valores: {to_info['sample_values']}

EVIDENCIA DE RELACIÓN:
- Valores compartidos: {evidence['shared_values_count']}
- Porcentaje de overlap: {evidence['overlap_percentage']:.1f}%
- Muestra de valores compartidos: {evidence['shared_values_sample']}
- Confianza algoritmo: {context['confidence']:.1f}%

INSTRUCCIONES:
Analiza esta relación considerando:
1. ¿Los nombres de columnas sugieren una relación lógica?
2. ¿Los tipos de datos son compatibles?
3. ¿El overlap de valores es suficiente y lógico?
4. ¿La cardinalidad tiene sentido (muchos a uno, uno a muchos, etc.)?
5. ¿En qué contexto de negocio tendría sentido esta relación?

Responde en formato JSON ESTRICTO:
{{
  "is_valid": true/false,
  "confidence_score": 0-100,
  "explanation": "Explicación clara de por qué es válida o inválida",
  "suggested_cardinality": "1:1" o "1:N" o "N:1" o "N:M" o "unknown",
  "reasoning_steps": ["paso 1", "paso 2", "paso 3"],
  "business_context": "En qué contexto de negocio tiene sentido"
}}

Sé riguroso en tu análisis. Una relación es válida solo si hay evidencia clara."""

        return prompt
    
    def _call_ollama_real(self, prompt: str) -> str:
        """Hace llamada REAL a Ollama"""
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Baja temperatura para respuestas consistentes
                "top_p": 0.9,
                "num_predict": 1000,  # Máximo tokens
                "stop": ["Human:", "Assistant:", "\n\n\n"]
            }
        }
        
        try:
            print(f"   🤖 Consultando {self.model_name}...")
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get('response', '').strip()
                
                if not llm_response:
                    raise Exception("Respuesta vacía del LLM")
                
                return llm_response
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            raise Exception(f"Timeout después de {self.timeout}s")
        except requests.exceptions.ConnectionError:
            raise Exception("Error de conexión con Ollama")
        except Exception as e:
            raise Exception(f"Error llamando a Ollama: {str(e)}")
    
    def _parse_llm_response_real(self, llm_response: str, relationship: Dict) -> AIValidationResult:
        """Parsea respuesta REAL del LLM"""
        
        try:
            # Buscar JSON en la respuesta
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                
                # Limpiar JSON (remover comentarios, etc.)
                json_str = self._clean_json_response(json_str)
                
                parsed = json.loads(json_str)
                
                return AIValidationResult(
                    relationship=relationship['relation'],
                    is_valid=bool(parsed.get('is_valid', False)),
                    confidence_score=float(parsed.get('confidence_score', 0)),
                    explanation=str(parsed.get('explanation', 'Sin explicación')),
                    suggested_cardinality=str(parsed.get('suggested_cardinality', 'unknown')),
                    reasoning_steps=list(parsed.get('reasoning_steps', [])),
                    llm_raw_response=llm_response,
                    validation_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
                )
            else:
                # Si no hay JSON válido, analizar texto
                return self._fallback_text_analysis(llm_response, relationship)
                
        except json.JSONDecodeError as e:
            print(f"   ⚠️  Error parseando JSON: {e}")
            return self._fallback_text_analysis(llm_response, relationship)
        except Exception as e:
            print(f"   ⚠️  Error procesando respuesta: {e}")
            return self._fallback_text_analysis(llm_response, relationship)
    
    def _clean_json_response(self, json_str: str) -> str:
        """Limpia respuesta JSON del LLM"""
        # Remover comentarios y texto extra
        lines = json_str.split('\n')
        clean_lines = []
        
        for line in lines:
            # Remover comentarios
            if '//' in line:
                line = line[:line.index('//')]
            clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    def _fallback_text_analysis(self, llm_response: str, relationship: Dict) -> AIValidationResult:
        """Análisis de fallback cuando no hay JSON válido"""
        
        response_lower = llm_response.lower()
        
        # Buscar indicadores de validez
        positive_indicators = ['válida', 'valid', 'correcto', 'correct', 'sí', 'yes', 'lógico', 'logical']
        negative_indicators = ['inválida', 'invalid', 'incorrecto', 'incorrect', 'no', 'ilógico']
        
        positive_score = sum(1 for indicator in positive_indicators if indicator in response_lower)
        negative_score = sum(1 for indicator in negative_indicators if indicator in response_lower)
        
        is_valid = positive_score > negative_score
        confidence = min(60 + positive_score * 10, 90) if is_valid else max(40 - negative_score * 10, 10)
        
        return AIValidationResult(
            relationship=relationship['relation'],
            is_valid=is_valid,
            confidence_score=float(confidence),
            explanation="Análisis basado en respuesta de texto (JSON no válido)",
            suggested_cardinality="unknown",
            reasoning_steps=["Análisis de texto de respuesta LLM"],
            llm_raw_response=llm_response,
            validation_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )

def test_real_ai_verifier():
    """Test rápido del verificador AI real"""
    
    print("🧪 TESTING VERIFICADOR AI REAL")
    print("=" * 40)
    
    try:
        # Inicializar verificador
        verifier = RealAIVerifier()
        
        # Datos dummy para test
        test_data = {
            'patients': pd.DataFrame({
                'id': [1, 2, 3],
                'name': ['John', 'Jane', 'Bob']
            }),
            'pets': pd.DataFrame({
                'pet_id': [1, 2],
                'patients_id': [1, 2],
                'name': ['Fluffy', 'Rex']
            })
        }
        
        # Relación test
        test_relationship = {
            'relation': 'pets.patients_id → patients.id',
            'confidence': 95.0,
            'overlap_ratio': 0.85
        }
        
        # Validar con AI real
        result = verifier._validate_single_relationship_real(test_relationship, test_data)
        
        print(f"✅ Test completado:")
        print(f"   Relación: {result.relationship}")
        print(f"   Válida: {result.is_valid}")
        print(f"   Confianza AI: {result.confidence_score}")
        print(f"   Explicación: {result.explanation}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test falló: {e}")
        return False

if __name__ == "__main__":
    test_real_ai_verifier()
