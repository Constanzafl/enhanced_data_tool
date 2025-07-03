# 🔍 Smart Database Relationship Analyzer

Analizador inteligente de relaciones en bases de datos que combina análisis semántico, comparación de valores y validación con AI.

## 🚀 Características Principales

### 1. **Detección Inteligente de Relaciones**
- **Análisis semántico avanzado**: Detecta relaciones incluso con nombres no estándar
  - `pets.OwnerPatientCode` → `patients.PatientUID`
  - `appointments.pacienteIdentificador` → `patients.uid`
  - `prescriptions.MedicationCode` → `medications.MedicationUUID`
- **Detección de PKs flexible**: Identifica claves primarias con diversos nombres:
  - Estándar: `id`, `uid`, `uuid`, `guid`, `pk`
  - Compuestos: `PatientUID`, `AnimalIdentifier`, `CitaID`
  - CamelCase: `PatientIdentifier`, `BookingReference`
  - Otros idiomas: `identificador`, `codigo`, `numero`
- **Evita falsos positivos**: NO confunde PKs entre tablas
- **Comparación de valores**: Calcula el porcentaje de valores coincidentes
- **Descomposición inteligente de nombres**: Separa CamelCase, snake_case, etc.

### 2. **Sistema Anti-Confusión de PKs** 🔑
El sistema implementa reglas específicas para evitar errores comunes:

```
❌ INCORRECTO: pets.uid → patients.uid (ambas son PKs)
✅ CORRECTO: pets.PatientIdentifier → patients.uid (FK → PK)
✅ CORRECTO: appointments.pacienteIdentificador → patients.PatientUID
```

**Reglas implementadas:**
- Las PKs de diferentes tablas NO se relacionan entre sí
- Penalización de -50% al score si ambas columnas son PKs
- Bonus de +20% para patrones FK clásicos detectados semánticamente
- Análisis profundo de componentes del nombre

### 3. **Manejo de Nombres Complejos**
El sistema descompone nombres complejos para encontrar relaciones:

```python
'OwnerPatientCode' → ['owner', 'patient', 'code']
'pacienteIdentificador' → ['paciente', 'identificador']
'MedicationUUID' → ['medication', 'uuid']
```

Detecta relaciones incluso cuando:
- Los nombres usan diferentes idiomas
- Mezclan CamelCase, snake_case, PascalCase
- Usan abreviaciones o términos técnicos
- No siguen convenciones estándar

## 📋 Requisitos

```bash
pip install pandas numpy requests
```

Para la validación con AI:
```bash
# Instalar Ollama
curl https://ollama.ai/install.sh | sh

# Descargar un modelo
ollama pull llama2
```

## 🛠️ Uso Básico

### 1. Preparar tus datos

Coloca tus archivos CSV en el mismo directorio:
- `patients.csv`
- `appointments.csv`
- `medications.csv`
- etc.

### 2. Ejecutar el análisis

```python
python main_analyzer.py
```

### 3. Usar programáticamente

```python
import pandas as pd
from smart_detector import detect_relationships
from ai_validator import analyze_database_with_ai

# Cargar tablas
tables = {
    'patients': pd.read_csv('patients.csv'),
    'appointments': pd.read_csv('appointments.csv'),
    'medications': pd.read_csv('medications.csv')
}

# Opción 1: Solo detección
candidates = detect_relationships(tables)

# Opción 2: Detección + Validación AI
candidates, validations = analyze_database_with_ai(tables, top_n=10)
```

## 🎯 Cómo Funciona

### Fase 1: Detección de Claves Primarias
```
🔑 Detectando claves primarias...
  - patients: id (confianza: 100%)
  - pets: id (confianza: 100%)
  - appointments: id (confianza: 100%)
```

### Fase 2: Análisis de Columnas
```
🔍 Analizando columnas de todas las tablas...

Tabla: patients
  - id (PK): int64, 5 únicos, 0 nulos
  - name: object, 5 únicos, 0 nulos
  - email: object, 5 únicos, 0 nulos

Tabla: pets
  - id (PK): int64, 5 únicos, 0 nulos
  - patient_id: int64, 4 únicos, 0 nulos
  - name: object, 5 únicos, 0 nulos
```

### Fase 3: Detección de Relaciones
El sistema evalúa cada par de columnas considerando:

1. **Similitud de Nombres (30% peso)**
   - Coincidencia exacta: 100%
   - Contención: 80% (ej: `patient` en `patient_id`)
   - Patrones FK: 90% (ej: `pets.patient_id` → `patients.id`)
   - PKs entre tablas: 0% (ej: `pets.id` ↛ `patients.id`)

2. **Compatibilidad de Tipos (10% peso)**
   - Mismo tipo: 100%
   - Tipos compatibles: 80%

3. **Coincidencia de Valores (50% peso)** ⭐
   - >80% coincidencia: 100% score
   - 50-80% coincidencia: 80% score
   - 20-50% coincidencia: 50% score
   - <20% coincidencia: proporcional

4. **Similitud de Patrones (10% peso)**
   - Mismo patrón dominante: 100%
   - Patrones similares: 70%

### Fase 4: Validación con AI
```
🤖 VALIDACIÓN AI - Modelo: llama2:latest
============================================================

[1/5] Validando con AI:
   pets.patient_id → patients.patient_id
   🤖 Consultando llama2:latest...
   Resultado: ✅ VÁLIDA (Confianza AI: 95.0%)
   Explicación: La relación es correcta. La columna patient_id en pets 
   referencia a patient_id en patients, indicando qué paciente es dueño 
   de cada mascota...
```

## 📊 Salida Ejemplo

```
📊 Top 10 Relaciones Encontradas:
================================================================================

🔑 Claves Primarias Detectadas:
  - patients.id
  - pets.id
  - appointments.id

1. pets.patient_id → patients.id ✓ (FK → PK)
   Confianza: 95.0%
   Evidencia:
   - Similitud de nombres: 95.0%
   - Compatibilidad de tipos: 100.0%
   - Coincidencia de valores: 100.0% (score: 100.0%)
   - Similitud de patrones: 100.0%
   - ✓ Bonus por patrón FK clásico: +20.0%

2. appointments.patient_id → patients.id ✓ (FK → PK)
   Confianza: 92.5%
   Evidencia:
   - Similitud de nombres: 95.0%
   - Compatibilidad de tipos: 100.0%
   - Coincidencia de valores: 80.0% (score: 100.0%)
   - Similitud de patrones: 100.0%

3. appointments.pet_id → pets.id ✓ (FK → PK)
   Confianza: 91.0%
   Evidencia:
   - Similitud de nombres: 95.0%
   - Compatibilidad de tipos: 100.0%
   - Coincidencia de valores: 100.0% (score: 100.0%)
   - Similitud de patrones: 100.0%

❌ NO DETECTADAS (Correctamente evitadas):
- pets.id → patients.id (ambas son PKs)
- appointments.id → patients.id (ambas son PKs)
- pets.id → appointments.id (ambas son PKs)
```

## 🔧 Personalización

### Ajustar pesos de scoring
```python
# En SmartRelationshipDetector._evaluate_relationship()
scores.append(name_score * 0.3)     # Peso nombre
scores.append(type_score * 0.1)     # Peso tipo
scores.append(value_score * 0.5)    # Peso valores
scores.append(pattern_score * 0.1)  # Peso patrones
```

### Añadir patrones de ID personalizados
```python
detector = SmartRelationshipDetector(tables)

# Agregar patrones específicos de tu sistema
detector.common_id_patterns.extend([
    r'_codigo

## 📝 Archivos Generados

- `relationships.json`: Todas las relaciones detectadas con evidencia
- Logs en consola con detalles del análisis

## 🧪 Testing y Verificación

### Test de No-Confusión de PKs
Para verificar que el sistema no confunde PKs entre tablas:

```bash
python test_pk_detection.py
```

### Test de Nombres Complejos
Para probar con nombres no estándar:

```bash
python test_complex_names.py
```

Output esperado:
```
🧪 TEST: Detección con Nombres de Columnas No Estándar
======================================================================

🔑 Detectando claves primarias...
  - patients: PatientUID (confianza: 100%)
  - pets: AnimalIdentifier (confianza: 100%)
  - appointments: CitaID (confianza: 100%)

✅ ENCONTRADA: pets.OwnerPatientCode → patients.PatientUID
   Confianza: 96.5%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: appointments.pacienteIdentificador → patients.PatientUID
   Confianza: 94.0%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: prescriptions.MedicationCode → medications.MedicationUUID
   Confianza: 91.5%
   Coincidencia valores: 75.0%

📈 Resumen: 7/7 relaciones esperadas encontradas

🔤 Análisis de Descomposición de Nombres:
----------------------------------------------------------------------

'OwnerPatientCode':
  - Palabras: {'owner', 'patient', 'code'}
  - Palabras base: {'owner', 'patient'}
  - Tiene ID: True

'pacienteIdentificador':
  - Palabras: {'paciente', 'identificador'}
  - Palabras base: {'paciente'}
  - Tiene ID: True
```

## 📝 Ejemplos de Uso con Nombres No Estándar

### Ejemplo 1: Base de datos con nomenclatura mixta
```python
tables = {
    'Customers': pd.DataFrame({
        'CustomerUID': ['C001', 'C002', 'C003'],
        'FullName': ['John Doe', 'Jane Smith', 'Bob Johnson']
    }),
    'Orders': pd.DataFrame({
        'OrderIdentifier': ['O1001', 'O1002', 'O1003'],
        'ClientReference': ['C001', 'C002', 'C001']  # FK a Customers.CustomerUID
    })
}

detector = SmartRelationshipDetector(tables)
candidates = detector.find_relationships()

# Detectará: Orders.ClientReference → Customers.CustomerUID
```

### Ejemplo 2: Nombres en español/mixtos
```python
tables = {
    'pacientes': pd.DataFrame({
        'pacienteID': [1, 2, 3],
        'nombreCompleto': ['Juan', 'María', 'Carlos']
    }),
    'citas': pd.DataFrame({
        'citaNumero': [101, 102, 103],
        'pacienteIdentificador': [1, 2, 1]  # FK a pacientes.pacienteID
    })
}

# El sistema detectará la relación correctamente
```

### Ejemplo 3: CamelCase y términos técnicos
```python
tables = {
    'SystemUsers': pd.DataFrame({
        'UserGUID': ['550e8400-e29b-41d4-a716-446655440001', ...],
        'Username': ['admin', 'user1', 'user2']
    }),
    'AuditLogs': pd.DataFrame({
        'LogEntryID': [1, 2, 3],
        'PerformedByUserIdentifier': ['550e8400-e29b-41d4-a716-446655440001', ...]
    })
}

# Detectará: AuditLogs.PerformedByUserIdentifier → SystemUsers.UserGUID
```

## ⚠️ Consideraciones

1. **Performance**: El análisis de valores puede ser lento en tablas grandes
2. **Memoria**: Carga todas las tablas en memoria
3. **AI**: Requiere Ollama ejecutándose localmente
4. **Precisión**: Los resultados son sugerencias, siempre revisar manualmente

## 🐛 Solución de Problemas

### "Ollama no está disponible"
```bash
# Iniciar Ollama
ollama serve

# Verificar que esté corriendo
curl http://localhost:11434/api/tags
```

### "No se encontraron relaciones"
- Verificar que las columnas tengan valores coincidentes
- Ajustar el umbral mínimo de confianza (default: 0.3)
- Revisar los nombres de columnas

### "Se detectan relaciones incorrectas entre PKs"
El sistema ya incluye protección contra esto, pero si sucede:
- Verificar que las PKs se detecten correctamente
- Revisar el método `_calculate_name_similarity()`
- Aumentar la penalización para relaciones PK-PK

### Errores de memoria
- Procesar tablas más pequeñas
- Usar samples de datos
- Aumentar la memoria disponible

## 🔧 Cambios Clave para Manejar Nombres No Estándar

1. **Detección flexible de PKs**: El sistema identifica PKs con diversos patrones:
   ```python
   # Detecta como PKs:
   - id, uid, uuid, guid, pk
   - PatientUID, CustomerGUID, AnimalIdentifier
   - identificador, codigo, numero
   - Columnas únicas sin nulos con nombres sugestivos
   ```

2. **Descomposición inteligente de nombres**:
   ```python
   def _extract_name_components(self, column_name):
       # 'OwnerPatientCode' → ['owner', 'patient', 'code']
       # 'pacienteIdentificador' → ['paciente', 'identificador']
       # Separa CamelCase, snake_case, kebab-case
   ```

3. **Análisis semántico profundo**:
   ```python
   # Detecta relaciones aunque los nombres sean diferentes:
   - pets.OwnerPatientCode → patients.PatientUID
   - orders.ClientReference → customers.CustomerIdentifier
   - citas.pacienteIdentificador → pacientes.uid
   ```

4. **Verificación de palabras relacionadas**:
   ```python
   def _words_are_related(self, word1, word2):
       # Verifica: coincidencia exacta, contenido, plurales,
       # alta similitud (>85%), mapeos semánticos
   ```

5. **Sistema robusto anti-confusión**:
   - Detecta cuando ambas columnas son PKs → penalización
   - Identifica patrones FK semánticos → bonus
   - Prioriza coincidencia de valores (50% del peso)

## 🚀 Mejoras Futuras

- [ ] Soporte para más tipos de bases de datos
- [ ] Detección de relaciones N:M automática
- [ ] Embeddings para similitud semántica avanzada
- [ ] Detección de idioma automática para nombres de columnas
- [ ] Aprendizaje de patrones de nombres específicos del dominio
- [ ] Interfaz web interactiva
- [ ] API REST para integración
- [ ] Soporte para detección de relaciones compuestas
- [ ] Análisis de cardinalidad automático
- [ ] Generación de diagramas ER
- [ ] Exportación a formatos de modelado (DBM, SQL)
- [ ] Cache inteligente de análisis
- [ ] Procesamiento incremental para bases de datos grandes
- [ ] Integración con herramientas de documentación de BD
,     # Para sistemas en español
    r'_nummer

## 📝 Archivos Generados

- `relationships.json`: Todas las relaciones detectadas con evidencia
- Logs en consola con detalles del análisis

## 🧪 Testing y Verificación

### Test de No-Confusión de PKs
Para verificar que el sistema no confunde PKs entre tablas:

```bash
python test_pk_detection.py
```

### Test de Nombres Complejos
Para probar con nombres no estándar:

```bash
python test_complex_names.py
```

Output esperado:
```
🧪 TEST: Detección con Nombres de Columnas No Estándar
======================================================================

🔑 Detectando claves primarias...
  - patients: PatientUID (confianza: 100%)
  - pets: AnimalIdentifier (confianza: 100%)
  - appointments: CitaID (confianza: 100%)

✅ ENCONTRADA: pets.OwnerPatientCode → patients.PatientUID
   Confianza: 96.5%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: appointments.pacienteIdentificador → patients.PatientUID
   Confianza: 94.0%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: prescriptions.MedicationCode → medications.MedicationUUID
   Confianza: 91.5%
   Coincidencia valores: 75.0%

📈 Resumen: 7/7 relaciones esperadas encontradas

🔤 Análisis de Descomposición de Nombres:
----------------------------------------------------------------------

'OwnerPatientCode':
  - Palabras: {'owner', 'patient', 'code'}
  - Palabras base: {'owner', 'patient'}
  - Tiene ID: True

'pacienteIdentificador':
  - Palabras: {'paciente', 'identificador'}
  - Palabras base: {'paciente'}
  - Tiene ID: True
```

## 📝 Ejemplos de Uso con Nombres No Estándar

### Ejemplo 1: Base de datos con nomenclatura mixta
```python
tables = {
    'Customers': pd.DataFrame({
        'CustomerUID': ['C001', 'C002', 'C003'],
        'FullName': ['John Doe', 'Jane Smith', 'Bob Johnson']
    }),
    'Orders': pd.DataFrame({
        'OrderIdentifier': ['O1001', 'O1002', 'O1003'],
        'ClientReference': ['C001', 'C002', 'C001']  # FK a Customers.CustomerUID
    })
}

detector = SmartRelationshipDetector(tables)
candidates = detector.find_relationships()

# Detectará: Orders.ClientReference → Customers.CustomerUID
```

### Ejemplo 2: Nombres en español/mixtos
```python
tables = {
    'pacientes': pd.DataFrame({
        'pacienteID': [1, 2, 3],
        'nombreCompleto': ['Juan', 'María', 'Carlos']
    }),
    'citas': pd.DataFrame({
        'citaNumero': [101, 102, 103],
        'pacienteIdentificador': [1, 2, 1]  # FK a pacientes.pacienteID
    })
}

# El sistema detectará la relación correctamente
```

### Ejemplo 3: CamelCase y términos técnicos
```python
tables = {
    'SystemUsers': pd.DataFrame({
        'UserGUID': ['550e8400-e29b-41d4-a716-446655440001', ...],
        'Username': ['admin', 'user1', 'user2']
    }),
    'AuditLogs': pd.DataFrame({
        'LogEntryID': [1, 2, 3],
        'PerformedByUserIdentifier': ['550e8400-e29b-41d4-a716-446655440001', ...]
    })
}

# Detectará: AuditLogs.PerformedByUserIdentifier → SystemUsers.UserGUID
```

## ⚠️ Consideraciones

1. **Performance**: El análisis de valores puede ser lento en tablas grandes
2. **Memoria**: Carga todas las tablas en memoria
3. **AI**: Requiere Ollama ejecutándose localmente
4. **Precisión**: Los resultados son sugerencias, siempre revisar manualmente

## 🐛 Solución de Problemas

### "Ollama no está disponible"
```bash
# Iniciar Ollama
ollama serve

# Verificar que esté corriendo
curl http://localhost:11434/api/tags
```

### "No se encontraron relaciones"
- Verificar que las columnas tengan valores coincidentes
- Ajustar el umbral mínimo de confianza (default: 0.3)
- Revisar los nombres de columnas

### "Se detectan relaciones incorrectas entre PKs"
El sistema ya incluye protección contra esto, pero si sucede:
- Verificar que las PKs se detecten correctamente
- Revisar el método `_calculate_name_similarity()`
- Aumentar la penalización para relaciones PK-PK

### Errores de memoria
- Procesar tablas más pequeñas
- Usar samples de datos
- Aumentar la memoria disponible

## 🔧 Cambios Clave para Evitar Confusión de PKs

1. **Detección automática de PKs**: El sistema identifica columnas que son PKs basándose en:
   - Valores únicos para cada fila
   - Sin valores nulos
   - Nombres típicos ('id', 'tabla_id')

2. **Reglas de similitud mejoradas**:
   ```python
   # REGLA 1: PKs de diferentes tablas NO se relacionan
   if source_name == 'id' and target_name == 'id':
       return 0.0
   
   # REGLA 2: Patrón FK clásico obtiene alta puntuación
   # pets.patient_id → patients.id = 95% confianza
   ```

3. **Penalización en evaluación**:
   ```python
   # Si ambas son PKs, penalización fuerte
   if source_is_pk and target_is_pk:
       scores.append(-0.5)  # -50% al score total
   ```

4. **Bonus para patrones correctos**:
   ```python
   # Bonus si detectamos patrón FK → PK correcto
   if target_is_pk and not source_is_pk:
       if source_column.endswith(f"{target_table}_id"):
           scores.append(0.2)  # +20% bonus
   ```

## 🚀 Mejoras Futuras

- [ ] Soporte para más tipos de bases de datos
- [ ] Detección de relaciones N:M
- [ ] Embeddings para similitud semántica
- [ ] Interfaz web
- [ ] Procesamiento en paralelo
- [ ] Cache de resultados
,     # Para sistemas en alemán
    r'_ref

## 📝 Archivos Generados

- `relationships.json`: Todas las relaciones detectadas con evidencia
- Logs en consola con detalles del análisis

## 🧪 Testing y Verificación

### Test de No-Confusión de PKs
Para verificar que el sistema no confunde PKs entre tablas:

```bash
python test_pk_detection.py
```

### Test de Nombres Complejos
Para probar con nombres no estándar:

```bash
python test_complex_names.py
```

Output esperado:
```
🧪 TEST: Detección con Nombres de Columnas No Estándar
======================================================================

🔑 Detectando claves primarias...
  - patients: PatientUID (confianza: 100%)
  - pets: AnimalIdentifier (confianza: 100%)
  - appointments: CitaID (confianza: 100%)

✅ ENCONTRADA: pets.OwnerPatientCode → patients.PatientUID
   Confianza: 96.5%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: appointments.pacienteIdentificador → patients.PatientUID
   Confianza: 94.0%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: prescriptions.MedicationCode → medications.MedicationUUID
   Confianza: 91.5%
   Coincidencia valores: 75.0%

📈 Resumen: 7/7 relaciones esperadas encontradas

🔤 Análisis de Descomposición de Nombres:
----------------------------------------------------------------------

'OwnerPatientCode':
  - Palabras: {'owner', 'patient', 'code'}
  - Palabras base: {'owner', 'patient'}
  - Tiene ID: True

'pacienteIdentificador':
  - Palabras: {'paciente', 'identificador'}
  - Palabras base: {'paciente'}
  - Tiene ID: True
```

## 📝 Ejemplos de Uso con Nombres No Estándar

### Ejemplo 1: Base de datos con nomenclatura mixta
```python
tables = {
    'Customers': pd.DataFrame({
        'CustomerUID': ['C001', 'C002', 'C003'],
        'FullName': ['John Doe', 'Jane Smith', 'Bob Johnson']
    }),
    'Orders': pd.DataFrame({
        'OrderIdentifier': ['O1001', 'O1002', 'O1003'],
        'ClientReference': ['C001', 'C002', 'C001']  # FK a Customers.CustomerUID
    })
}

detector = SmartRelationshipDetector(tables)
candidates = detector.find_relationships()

# Detectará: Orders.ClientReference → Customers.CustomerUID
```

### Ejemplo 2: Nombres en español/mixtos
```python
tables = {
    'pacientes': pd.DataFrame({
        'pacienteID': [1, 2, 3],
        'nombreCompleto': ['Juan', 'María', 'Carlos']
    }),
    'citas': pd.DataFrame({
        'citaNumero': [101, 102, 103],
        'pacienteIdentificador': [1, 2, 1]  # FK a pacientes.pacienteID
    })
}

# El sistema detectará la relación correctamente
```

### Ejemplo 3: CamelCase y términos técnicos
```python
tables = {
    'SystemUsers': pd.DataFrame({
        'UserGUID': ['550e8400-e29b-41d4-a716-446655440001', ...],
        'Username': ['admin', 'user1', 'user2']
    }),
    'AuditLogs': pd.DataFrame({
        'LogEntryID': [1, 2, 3],
        'PerformedByUserIdentifier': ['550e8400-e29b-41d4-a716-446655440001', ...]
    })
}

# Detectará: AuditLogs.PerformedByUserIdentifier → SystemUsers.UserGUID
```

## ⚠️ Consideraciones

1. **Performance**: El análisis de valores puede ser lento en tablas grandes
2. **Memoria**: Carga todas las tablas en memoria
3. **AI**: Requiere Ollama ejecutándose localmente
4. **Precisión**: Los resultados son sugerencias, siempre revisar manualmente

## 🐛 Solución de Problemas

### "Ollama no está disponible"
```bash
# Iniciar Ollama
ollama serve

# Verificar que esté corriendo
curl http://localhost:11434/api/tags
```

### "No se encontraron relaciones"
- Verificar que las columnas tengan valores coincidentes
- Ajustar el umbral mínimo de confianza (default: 0.3)
- Revisar los nombres de columnas

### "Se detectan relaciones incorrectas entre PKs"
El sistema ya incluye protección contra esto, pero si sucede:
- Verificar que las PKs se detecten correctamente
- Revisar el método `_calculate_name_similarity()`
- Aumentar la penalización para relaciones PK-PK

### Errores de memoria
- Procesar tablas más pequeñas
- Usar samples de datos
- Aumentar la memoria disponible

## 🔧 Cambios Clave para Evitar Confusión de PKs

1. **Detección automática de PKs**: El sistema identifica columnas que son PKs basándose en:
   - Valores únicos para cada fila
   - Sin valores nulos
   - Nombres típicos ('id', 'tabla_id')

2. **Reglas de similitud mejoradas**:
   ```python
   # REGLA 1: PKs de diferentes tablas NO se relacionan
   if source_name == 'id' and target_name == 'id':
       return 0.0
   
   # REGLA 2: Patrón FK clásico obtiene alta puntuación
   # pets.patient_id → patients.id = 95% confianza
   ```

3. **Penalización en evaluación**:
   ```python
   # Si ambas son PKs, penalización fuerte
   if source_is_pk and target_is_pk:
       scores.append(-0.5)  # -50% al score total
   ```

4. **Bonus para patrones correctos**:
   ```python
   # Bonus si detectamos patrón FK → PK correcto
   if target_is_pk and not source_is_pk:
       if source_column.endswith(f"{target_table}_id"):
           scores.append(0.2)  # +20% bonus
   ```

## 🚀 Mejoras Futuras

- [ ] Soporte para más tipos de bases de datos
- [ ] Detección de relaciones N:M
- [ ] Embeddings para similitud semántica
- [ ] Interfaz web
- [ ] Procesamiento en paralelo
- [ ] Cache de resultados
,        # Referencias
    r'_fk

## 📝 Archivos Generados

- `relationships.json`: Todas las relaciones detectadas con evidencia
- Logs en consola con detalles del análisis

## 🧪 Testing y Verificación

### Test de No-Confusión de PKs
Para verificar que el sistema no confunde PKs entre tablas:

```bash
python test_pk_detection.py
```

### Test de Nombres Complejos
Para probar con nombres no estándar:

```bash
python test_complex_names.py
```

Output esperado:
```
🧪 TEST: Detección con Nombres de Columnas No Estándar
======================================================================

🔑 Detectando claves primarias...
  - patients: PatientUID (confianza: 100%)
  - pets: AnimalIdentifier (confianza: 100%)
  - appointments: CitaID (confianza: 100%)

✅ ENCONTRADA: pets.OwnerPatientCode → patients.PatientUID
   Confianza: 96.5%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: appointments.pacienteIdentificador → patients.PatientUID
   Confianza: 94.0%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: prescriptions.MedicationCode → medications.MedicationUUID
   Confianza: 91.5%
   Coincidencia valores: 75.0%

📈 Resumen: 7/7 relaciones esperadas encontradas

🔤 Análisis de Descomposición de Nombres:
----------------------------------------------------------------------

'OwnerPatientCode':
  - Palabras: {'owner', 'patient', 'code'}
  - Palabras base: {'owner', 'patient'}
  - Tiene ID: True

'pacienteIdentificador':
  - Palabras: {'paciente', 'identificador'}
  - Palabras base: {'paciente'}
  - Tiene ID: True
```

## 📝 Ejemplos de Uso con Nombres No Estándar

### Ejemplo 1: Base de datos con nomenclatura mixta
```python
tables = {
    'Customers': pd.DataFrame({
        'CustomerUID': ['C001', 'C002', 'C003'],
        'FullName': ['John Doe', 'Jane Smith', 'Bob Johnson']
    }),
    'Orders': pd.DataFrame({
        'OrderIdentifier': ['O1001', 'O1002', 'O1003'],
        'ClientReference': ['C001', 'C002', 'C001']  # FK a Customers.CustomerUID
    })
}

detector = SmartRelationshipDetector(tables)
candidates = detector.find_relationships()

# Detectará: Orders.ClientReference → Customers.CustomerUID
```

### Ejemplo 2: Nombres en español/mixtos
```python
tables = {
    'pacientes': pd.DataFrame({
        'pacienteID': [1, 2, 3],
        'nombreCompleto': ['Juan', 'María', 'Carlos']
    }),
    'citas': pd.DataFrame({
        'citaNumero': [101, 102, 103],
        'pacienteIdentificador': [1, 2, 1]  # FK a pacientes.pacienteID
    })
}

# El sistema detectará la relación correctamente
```

### Ejemplo 3: CamelCase y términos técnicos
```python
tables = {
    'SystemUsers': pd.DataFrame({
        'UserGUID': ['550e8400-e29b-41d4-a716-446655440001', ...],
        'Username': ['admin', 'user1', 'user2']
    }),
    'AuditLogs': pd.DataFrame({
        'LogEntryID': [1, 2, 3],
        'PerformedByUserIdentifier': ['550e8400-e29b-41d4-a716-446655440001', ...]
    })
}

# Detectará: AuditLogs.PerformedByUserIdentifier → SystemUsers.UserGUID
```

## ⚠️ Consideraciones

1. **Performance**: El análisis de valores puede ser lento en tablas grandes
2. **Memoria**: Carga todas las tablas en memoria
3. **AI**: Requiere Ollama ejecutándose localmente
4. **Precisión**: Los resultados son sugerencias, siempre revisar manualmente

## 🐛 Solución de Problemas

### "Ollama no está disponible"
```bash
# Iniciar Ollama
ollama serve

# Verificar que esté corriendo
curl http://localhost:11434/api/tags
```

### "No se encontraron relaciones"
- Verificar que las columnas tengan valores coincidentes
- Ajustar el umbral mínimo de confianza (default: 0.3)
- Revisar los nombres de columnas

### "Se detectan relaciones incorrectas entre PKs"
El sistema ya incluye protección contra esto, pero si sucede:
- Verificar que las PKs se detecten correctamente
- Revisar el método `_calculate_name_similarity()`
- Aumentar la penalización para relaciones PK-PK

### Errores de memoria
- Procesar tablas más pequeñas
- Usar samples de datos
- Aumentar la memoria disponible

## 🔧 Cambios Clave para Evitar Confusión de PKs

1. **Detección automática de PKs**: El sistema identifica columnas que son PKs basándose en:
   - Valores únicos para cada fila
   - Sin valores nulos
   - Nombres típicos ('id', 'tabla_id')

2. **Reglas de similitud mejoradas**:
   ```python
   # REGLA 1: PKs de diferentes tablas NO se relacionan
   if source_name == 'id' and target_name == 'id':
       return 0.0
   
   # REGLA 2: Patrón FK clásico obtiene alta puntuación
   # pets.patient_id → patients.id = 95% confianza
   ```

3. **Penalización en evaluación**:
   ```python
   # Si ambas son PKs, penalización fuerte
   if source_is_pk and target_is_pk:
       scores.append(-0.5)  # -50% al score total
   ```

4. **Bonus para patrones correctos**:
   ```python
   # Bonus si detectamos patrón FK → PK correcto
   if target_is_pk and not source_is_pk:
       if source_column.endswith(f"{target_table}_id"):
           scores.append(0.2)  # +20% bonus
   ```

## 🚀 Mejoras Futuras

- [ ] Soporte para más tipos de bases de datos
- [ ] Detección de relaciones N:M
- [ ] Embeddings para similitud semántica
- [ ] Interfaz web
- [ ] Procesamiento en paralelo
- [ ] Cache de resultados
          # Foreign keys explícitas
])

# Agregar palabras clave de ID
detector.id_keywords.extend([
    'referencia', 'clave', 'llave',  # Español
    'schlüssel', 'nummer',           # Alemán
    'chiave', 'codice'               # Italiano
])
```

### Añadir mapeos semánticos personalizados
```python
# Extender mapeos para tu dominio específico
detector.common_name_mappings.update({
    'student': ['student', 'alumno', 'estudiante', 'pupil'],
    'teacher': ['teacher', 'profesor', 'docente', 'instructor'],
    'course': ['course', 'curso', 'clase', 'subject', 'materia'],
    'employee': ['employee', 'empleado', 'worker', 'staff', 'personal']
})
```

### Crear detector personalizado para tu dominio
```python
class MedicalDatabaseDetector(SmartRelationshipDetector):
    def __init__(self, tables):
        super().__init__(tables)
        
        # Agregar términos médicos específicos
        self.common_name_mappings.update({
            'patient': ['patient', 'paciente', 'enfermo', 'case', 'subject'],
            'doctor': ['doctor', 'physician', 'medico', 'practitioner', 'provider'],
            'diagnosis': ['diagnosis', 'diagnostico', 'dx', 'finding'],
            'treatment': ['treatment', 'tratamiento', 'therapy', 'intervention']
        })
        
        # Patrones específicos del dominio médico
        self.medical_patterns = [
            r'_mrn

## 📝 Archivos Generados

- `relationships.json`: Todas las relaciones detectadas con evidencia
- Logs en consola con detalles del análisis

## 🧪 Testing y Verificación

### Test de No-Confusión de PKs
Para verificar que el sistema no confunde PKs entre tablas:

```bash
python test_pk_detection.py
```

### Test de Nombres Complejos
Para probar con nombres no estándar:

```bash
python test_complex_names.py
```

Output esperado:
```
🧪 TEST: Detección con Nombres de Columnas No Estándar
======================================================================

🔑 Detectando claves primarias...
  - patients: PatientUID (confianza: 100%)
  - pets: AnimalIdentifier (confianza: 100%)
  - appointments: CitaID (confianza: 100%)

✅ ENCONTRADA: pets.OwnerPatientCode → patients.PatientUID
   Confianza: 96.5%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: appointments.pacienteIdentificador → patients.PatientUID
   Confianza: 94.0%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: prescriptions.MedicationCode → medications.MedicationUUID
   Confianza: 91.5%
   Coincidencia valores: 75.0%

📈 Resumen: 7/7 relaciones esperadas encontradas

🔤 Análisis de Descomposición de Nombres:
----------------------------------------------------------------------

'OwnerPatientCode':
  - Palabras: {'owner', 'patient', 'code'}
  - Palabras base: {'owner', 'patient'}
  - Tiene ID: True

'pacienteIdentificador':
  - Palabras: {'paciente', 'identificador'}
  - Palabras base: {'paciente'}
  - Tiene ID: True
```

## 📝 Ejemplos de Uso con Nombres No Estándar

### Ejemplo 1: Base de datos con nomenclatura mixta
```python
tables = {
    'Customers': pd.DataFrame({
        'CustomerUID': ['C001', 'C002', 'C003'],
        'FullName': ['John Doe', 'Jane Smith', 'Bob Johnson']
    }),
    'Orders': pd.DataFrame({
        'OrderIdentifier': ['O1001', 'O1002', 'O1003'],
        'ClientReference': ['C001', 'C002', 'C001']  # FK a Customers.CustomerUID
    })
}

detector = SmartRelationshipDetector(tables)
candidates = detector.find_relationships()

# Detectará: Orders.ClientReference → Customers.CustomerUID
```

### Ejemplo 2: Nombres en español/mixtos
```python
tables = {
    'pacientes': pd.DataFrame({
        'pacienteID': [1, 2, 3],
        'nombreCompleto': ['Juan', 'María', 'Carlos']
    }),
    'citas': pd.DataFrame({
        'citaNumero': [101, 102, 103],
        'pacienteIdentificador': [1, 2, 1]  # FK a pacientes.pacienteID
    })
}

# El sistema detectará la relación correctamente
```

### Ejemplo 3: CamelCase y términos técnicos
```python
tables = {
    'SystemUsers': pd.DataFrame({
        'UserGUID': ['550e8400-e29b-41d4-a716-446655440001', ...],
        'Username': ['admin', 'user1', 'user2']
    }),
    'AuditLogs': pd.DataFrame({
        'LogEntryID': [1, 2, 3],
        'PerformedByUserIdentifier': ['550e8400-e29b-41d4-a716-446655440001', ...]
    })
}

# Detectará: AuditLogs.PerformedByUserIdentifier → SystemUsers.UserGUID
```

## ⚠️ Consideraciones

1. **Performance**: El análisis de valores puede ser lento en tablas grandes
2. **Memoria**: Carga todas las tablas en memoria
3. **AI**: Requiere Ollama ejecutándose localmente
4. **Precisión**: Los resultados son sugerencias, siempre revisar manualmente

## 🐛 Solución de Problemas

### "Ollama no está disponible"
```bash
# Iniciar Ollama
ollama serve

# Verificar que esté corriendo
curl http://localhost:11434/api/tags
```

### "No se encontraron relaciones"
- Verificar que las columnas tengan valores coincidentes
- Ajustar el umbral mínimo de confianza (default: 0.3)
- Revisar los nombres de columnas

### "Se detectan relaciones incorrectas entre PKs"
El sistema ya incluye protección contra esto, pero si sucede:
- Verificar que las PKs se detecten correctamente
- Revisar el método `_calculate_name_similarity()`
- Aumentar la penalización para relaciones PK-PK

### Errores de memoria
- Procesar tablas más pequeñas
- Usar samples de datos
- Aumentar la memoria disponible

## 🔧 Cambios Clave para Evitar Confusión de PKs

1. **Detección automática de PKs**: El sistema identifica columnas que son PKs basándose en:
   - Valores únicos para cada fila
   - Sin valores nulos
   - Nombres típicos ('id', 'tabla_id')

2. **Reglas de similitud mejoradas**:
   ```python
   # REGLA 1: PKs de diferentes tablas NO se relacionan
   if source_name == 'id' and target_name == 'id':
       return 0.0
   
   # REGLA 2: Patrón FK clásico obtiene alta puntuación
   # pets.patient_id → patients.id = 95% confianza
   ```

3. **Penalización en evaluación**:
   ```python
   # Si ambas son PKs, penalización fuerte
   if source_is_pk and target_is_pk:
       scores.append(-0.5)  # -50% al score total
   ```

4. **Bonus para patrones correctos**:
   ```python
   # Bonus si detectamos patrón FK → PK correcto
   if target_is_pk and not source_is_pk:
       if source_column.endswith(f"{target_table}_id"):
           scores.append(0.2)  # +20% bonus
   ```

## 🚀 Mejoras Futuras

- [ ] Soporte para más tipos de bases de datos
- [ ] Detección de relaciones N:M
- [ ] Embeddings para similitud semántica
- [ ] Interfaz web
- [ ] Procesamiento en paralelo
- [ ] Cache de resultados
,    # Medical Record Number
            r'_npi

## 📝 Archivos Generados

- `relationships.json`: Todas las relaciones detectadas con evidencia
- Logs en consola con detalles del análisis

## 🧪 Testing y Verificación

### Test de No-Confusión de PKs
Para verificar que el sistema no confunde PKs entre tablas:

```bash
python test_pk_detection.py
```

### Test de Nombres Complejos
Para probar con nombres no estándar:

```bash
python test_complex_names.py
```

Output esperado:
```
🧪 TEST: Detección con Nombres de Columnas No Estándar
======================================================================

🔑 Detectando claves primarias...
  - patients: PatientUID (confianza: 100%)
  - pets: AnimalIdentifier (confianza: 100%)
  - appointments: CitaID (confianza: 100%)

✅ ENCONTRADA: pets.OwnerPatientCode → patients.PatientUID
   Confianza: 96.5%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: appointments.pacienteIdentificador → patients.PatientUID
   Confianza: 94.0%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: prescriptions.MedicationCode → medications.MedicationUUID
   Confianza: 91.5%
   Coincidencia valores: 75.0%

📈 Resumen: 7/7 relaciones esperadas encontradas

🔤 Análisis de Descomposición de Nombres:
----------------------------------------------------------------------

'OwnerPatientCode':
  - Palabras: {'owner', 'patient', 'code'}
  - Palabras base: {'owner', 'patient'}
  - Tiene ID: True

'pacienteIdentificador':
  - Palabras: {'paciente', 'identificador'}
  - Palabras base: {'paciente'}
  - Tiene ID: True
```

## 📝 Ejemplos de Uso con Nombres No Estándar

### Ejemplo 1: Base de datos con nomenclatura mixta
```python
tables = {
    'Customers': pd.DataFrame({
        'CustomerUID': ['C001', 'C002', 'C003'],
        'FullName': ['John Doe', 'Jane Smith', 'Bob Johnson']
    }),
    'Orders': pd.DataFrame({
        'OrderIdentifier': ['O1001', 'O1002', 'O1003'],
        'ClientReference': ['C001', 'C002', 'C001']  # FK a Customers.CustomerUID
    })
}

detector = SmartRelationshipDetector(tables)
candidates = detector.find_relationships()

# Detectará: Orders.ClientReference → Customers.CustomerUID
```

### Ejemplo 2: Nombres en español/mixtos
```python
tables = {
    'pacientes': pd.DataFrame({
        'pacienteID': [1, 2, 3],
        'nombreCompleto': ['Juan', 'María', 'Carlos']
    }),
    'citas': pd.DataFrame({
        'citaNumero': [101, 102, 103],
        'pacienteIdentificador': [1, 2, 1]  # FK a pacientes.pacienteID
    })
}

# El sistema detectará la relación correctamente
```

### Ejemplo 3: CamelCase y términos técnicos
```python
tables = {
    'SystemUsers': pd.DataFrame({
        'UserGUID': ['550e8400-e29b-41d4-a716-446655440001', ...],
        'Username': ['admin', 'user1', 'user2']
    }),
    'AuditLogs': pd.DataFrame({
        'LogEntryID': [1, 2, 3],
        'PerformedByUserIdentifier': ['550e8400-e29b-41d4-a716-446655440001', ...]
    })
}

# Detectará: AuditLogs.PerformedByUserIdentifier → SystemUsers.UserGUID
```

## ⚠️ Consideraciones

1. **Performance**: El análisis de valores puede ser lento en tablas grandes
2. **Memoria**: Carga todas las tablas en memoria
3. **AI**: Requiere Ollama ejecutándose localmente
4. **Precisión**: Los resultados son sugerencias, siempre revisar manualmente

## 🐛 Solución de Problemas

### "Ollama no está disponible"
```bash
# Iniciar Ollama
ollama serve

# Verificar que esté corriendo
curl http://localhost:11434/api/tags
```

### "No se encontraron relaciones"
- Verificar que las columnas tengan valores coincidentes
- Ajustar el umbral mínimo de confianza (default: 0.3)
- Revisar los nombres de columnas

### "Se detectan relaciones incorrectas entre PKs"
El sistema ya incluye protección contra esto, pero si sucede:
- Verificar que las PKs se detecten correctamente
- Revisar el método `_calculate_name_similarity()`
- Aumentar la penalización para relaciones PK-PK

### Errores de memoria
- Procesar tablas más pequeñas
- Usar samples de datos
- Aumentar la memoria disponible

## 🔧 Cambios Clave para Evitar Confusión de PKs

1. **Detección automática de PKs**: El sistema identifica columnas que son PKs basándose en:
   - Valores únicos para cada fila
   - Sin valores nulos
   - Nombres típicos ('id', 'tabla_id')

2. **Reglas de similitud mejoradas**:
   ```python
   # REGLA 1: PKs de diferentes tablas NO se relacionan
   if source_name == 'id' and target_name == 'id':
       return 0.0
   
   # REGLA 2: Patrón FK clásico obtiene alta puntuación
   # pets.patient_id → patients.id = 95% confianza
   ```

3. **Penalización en evaluación**:
   ```python
   # Si ambas son PKs, penalización fuerte
   if source_is_pk and target_is_pk:
       scores.append(-0.5)  # -50% al score total
   ```

4. **Bonus para patrones correctos**:
   ```python
   # Bonus si detectamos patrón FK → PK correcto
   if target_is_pk and not source_is_pk:
       if source_column.endswith(f"{target_table}_id"):
           scores.append(0.2)  # +20% bonus
   ```

## 🚀 Mejoras Futuras

- [ ] Soporte para más tipos de bases de datos
- [ ] Detección de relaciones N:M
- [ ] Embeddings para similitud semántica
- [ ] Interfaz web
- [ ] Procesamiento en paralelo
- [ ] Cache de resultados
,    # National Provider Identifier
            r'_dx

## 📝 Archivos Generados

- `relationships.json`: Todas las relaciones detectadas con evidencia
- Logs en consola con detalles del análisis

## 🧪 Testing y Verificación

### Test de No-Confusión de PKs
Para verificar que el sistema no confunde PKs entre tablas:

```bash
python test_pk_detection.py
```

### Test de Nombres Complejos
Para probar con nombres no estándar:

```bash
python test_complex_names.py
```

Output esperado:
```
🧪 TEST: Detección con Nombres de Columnas No Estándar
======================================================================

🔑 Detectando claves primarias...
  - patients: PatientUID (confianza: 100%)
  - pets: AnimalIdentifier (confianza: 100%)
  - appointments: CitaID (confianza: 100%)

✅ ENCONTRADA: pets.OwnerPatientCode → patients.PatientUID
   Confianza: 96.5%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: appointments.pacienteIdentificador → patients.PatientUID
   Confianza: 94.0%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: prescriptions.MedicationCode → medications.MedicationUUID
   Confianza: 91.5%
   Coincidencia valores: 75.0%

📈 Resumen: 7/7 relaciones esperadas encontradas

🔤 Análisis de Descomposición de Nombres:
----------------------------------------------------------------------

'OwnerPatientCode':
  - Palabras: {'owner', 'patient', 'code'}
  - Palabras base: {'owner', 'patient'}
  - Tiene ID: True

'pacienteIdentificador':
  - Palabras: {'paciente', 'identificador'}
  - Palabras base: {'paciente'}
  - Tiene ID: True
```

## 📝 Ejemplos de Uso con Nombres No Estándar

### Ejemplo 1: Base de datos con nomenclatura mixta
```python
tables = {
    'Customers': pd.DataFrame({
        'CustomerUID': ['C001', 'C002', 'C003'],
        'FullName': ['John Doe', 'Jane Smith', 'Bob Johnson']
    }),
    'Orders': pd.DataFrame({
        'OrderIdentifier': ['O1001', 'O1002', 'O1003'],
        'ClientReference': ['C001', 'C002', 'C001']  # FK a Customers.CustomerUID
    })
}

detector = SmartRelationshipDetector(tables)
candidates = detector.find_relationships()

# Detectará: Orders.ClientReference → Customers.CustomerUID
```

### Ejemplo 2: Nombres en español/mixtos
```python
tables = {
    'pacientes': pd.DataFrame({
        'pacienteID': [1, 2, 3],
        'nombreCompleto': ['Juan', 'María', 'Carlos']
    }),
    'citas': pd.DataFrame({
        'citaNumero': [101, 102, 103],
        'pacienteIdentificador': [1, 2, 1]  # FK a pacientes.pacienteID
    })
}

# El sistema detectará la relación correctamente
```

### Ejemplo 3: CamelCase y términos técnicos
```python
tables = {
    'SystemUsers': pd.DataFrame({
        'UserGUID': ['550e8400-e29b-41d4-a716-446655440001', ...],
        'Username': ['admin', 'user1', 'user2']
    }),
    'AuditLogs': pd.DataFrame({
        'LogEntryID': [1, 2, 3],
        'PerformedByUserIdentifier': ['550e8400-e29b-41d4-a716-446655440001', ...]
    })
}

# Detectará: AuditLogs.PerformedByUserIdentifier → SystemUsers.UserGUID
```

## ⚠️ Consideraciones

1. **Performance**: El análisis de valores puede ser lento en tablas grandes
2. **Memoria**: Carga todas las tablas en memoria
3. **AI**: Requiere Ollama ejecutándose localmente
4. **Precisión**: Los resultados son sugerencias, siempre revisar manualmente

## 🐛 Solución de Problemas

### "Ollama no está disponible"
```bash
# Iniciar Ollama
ollama serve

# Verificar que esté corriendo
curl http://localhost:11434/api/tags
```

### "No se encontraron relaciones"
- Verificar que las columnas tengan valores coincidentes
- Ajustar el umbral mínimo de confianza (default: 0.3)
- Revisar los nombres de columnas

### "Se detectan relaciones incorrectas entre PKs"
El sistema ya incluye protección contra esto, pero si sucede:
- Verificar que las PKs se detecten correctamente
- Revisar el método `_calculate_name_similarity()`
- Aumentar la penalización para relaciones PK-PK

### Errores de memoria
- Procesar tablas más pequeñas
- Usar samples de datos
- Aumentar la memoria disponible

## 🔧 Cambios Clave para Evitar Confusión de PKs

1. **Detección automática de PKs**: El sistema identifica columnas que son PKs basándose en:
   - Valores únicos para cada fila
   - Sin valores nulos
   - Nombres típicos ('id', 'tabla_id')

2. **Reglas de similitud mejoradas**:
   ```python
   # REGLA 1: PKs de diferentes tablas NO se relacionan
   if source_name == 'id' and target_name == 'id':
       return 0.0
   
   # REGLA 2: Patrón FK clásico obtiene alta puntuación
   # pets.patient_id → patients.id = 95% confianza
   ```

3. **Penalización en evaluación**:
   ```python
   # Si ambas son PKs, penalización fuerte
   if source_is_pk and target_is_pk:
       scores.append(-0.5)  # -50% al score total
   ```

4. **Bonus para patrones correctos**:
   ```python
   # Bonus si detectamos patrón FK → PK correcto
   if target_is_pk and not source_is_pk:
       if source_column.endswith(f"{target_table}_id"):
           scores.append(0.2)  # +20% bonus
   ```

## 🚀 Mejoras Futuras

- [ ] Soporte para más tipos de bases de datos
- [ ] Detección de relaciones N:M
- [ ] Embeddings para similitud semántica
- [ ] Interfaz web
- [ ] Procesamiento en paralelo
- [ ] Cache de resultados
,     # Diagnosis code
            r'_rx

## 📝 Archivos Generados

- `relationships.json`: Todas las relaciones detectadas con evidencia
- Logs en consola con detalles del análisis

## 🧪 Testing y Verificación

### Test de No-Confusión de PKs
Para verificar que el sistema no confunde PKs entre tablas:

```bash
python test_pk_detection.py
```

### Test de Nombres Complejos
Para probar con nombres no estándar:

```bash
python test_complex_names.py
```

Output esperado:
```
🧪 TEST: Detección con Nombres de Columnas No Estándar
======================================================================

🔑 Detectando claves primarias...
  - patients: PatientUID (confianza: 100%)
  - pets: AnimalIdentifier (confianza: 100%)
  - appointments: CitaID (confianza: 100%)

✅ ENCONTRADA: pets.OwnerPatientCode → patients.PatientUID
   Confianza: 96.5%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: appointments.pacienteIdentificador → patients.PatientUID
   Confianza: 94.0%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: prescriptions.MedicationCode → medications.MedicationUUID
   Confianza: 91.5%
   Coincidencia valores: 75.0%

📈 Resumen: 7/7 relaciones esperadas encontradas

🔤 Análisis de Descomposición de Nombres:
----------------------------------------------------------------------

'OwnerPatientCode':
  - Palabras: {'owner', 'patient', 'code'}
  - Palabras base: {'owner', 'patient'}
  - Tiene ID: True

'pacienteIdentificador':
  - Palabras: {'paciente', 'identificador'}
  - Palabras base: {'paciente'}
  - Tiene ID: True
```

## 📝 Ejemplos de Uso con Nombres No Estándar

### Ejemplo 1: Base de datos con nomenclatura mixta
```python
tables = {
    'Customers': pd.DataFrame({
        'CustomerUID': ['C001', 'C002', 'C003'],
        'FullName': ['John Doe', 'Jane Smith', 'Bob Johnson']
    }),
    'Orders': pd.DataFrame({
        'OrderIdentifier': ['O1001', 'O1002', 'O1003'],
        'ClientReference': ['C001', 'C002', 'C001']  # FK a Customers.CustomerUID
    })
}

detector = SmartRelationshipDetector(tables)
candidates = detector.find_relationships()

# Detectará: Orders.ClientReference → Customers.CustomerUID
```

### Ejemplo 2: Nombres en español/mixtos
```python
tables = {
    'pacientes': pd.DataFrame({
        'pacienteID': [1, 2, 3],
        'nombreCompleto': ['Juan', 'María', 'Carlos']
    }),
    'citas': pd.DataFrame({
        'citaNumero': [101, 102, 103],
        'pacienteIdentificador': [1, 2, 1]  # FK a pacientes.pacienteID
    })
}

# El sistema detectará la relación correctamente
```

### Ejemplo 3: CamelCase y términos técnicos
```python
tables = {
    'SystemUsers': pd.DataFrame({
        'UserGUID': ['550e8400-e29b-41d4-a716-446655440001', ...],
        'Username': ['admin', 'user1', 'user2']
    }),
    'AuditLogs': pd.DataFrame({
        'LogEntryID': [1, 2, 3],
        'PerformedByUserIdentifier': ['550e8400-e29b-41d4-a716-446655440001', ...]
    })
}

# Detectará: AuditLogs.PerformedByUserIdentifier → SystemUsers.UserGUID
```

## ⚠️ Consideraciones

1. **Performance**: El análisis de valores puede ser lento en tablas grandes
2. **Memoria**: Carga todas las tablas en memoria
3. **AI**: Requiere Ollama ejecutándose localmente
4. **Precisión**: Los resultados son sugerencias, siempre revisar manualmente

## 🐛 Solución de Problemas

### "Ollama no está disponible"
```bash
# Iniciar Ollama
ollama serve

# Verificar que esté corriendo
curl http://localhost:11434/api/tags
```

### "No se encontraron relaciones"
- Verificar que las columnas tengan valores coincidentes
- Ajustar el umbral mínimo de confianza (default: 0.3)
- Revisar los nombres de columnas

### "Se detectan relaciones incorrectas entre PKs"
El sistema ya incluye protección contra esto, pero si sucede:
- Verificar que las PKs se detecten correctamente
- Revisar el método `_calculate_name_similarity()`
- Aumentar la penalización para relaciones PK-PK

### Errores de memoria
- Procesar tablas más pequeñas
- Usar samples de datos
- Aumentar la memoria disponible

## 🔧 Cambios Clave para Evitar Confusión de PKs

1. **Detección automática de PKs**: El sistema identifica columnas que son PKs basándose en:
   - Valores únicos para cada fila
   - Sin valores nulos
   - Nombres típicos ('id', 'tabla_id')

2. **Reglas de similitud mejoradas**:
   ```python
   # REGLA 1: PKs de diferentes tablas NO se relacionan
   if source_name == 'id' and target_name == 'id':
       return 0.0
   
   # REGLA 2: Patrón FK clásico obtiene alta puntuación
   # pets.patient_id → patients.id = 95% confianza
   ```

3. **Penalización en evaluación**:
   ```python
   # Si ambas son PKs, penalización fuerte
   if source_is_pk and target_is_pk:
       scores.append(-0.5)  # -50% al score total
   ```

4. **Bonus para patrones correctos**:
   ```python
   # Bonus si detectamos patrón FK → PK correcto
   if target_is_pk and not source_is_pk:
       if source_column.endswith(f"{target_table}_id"):
           scores.append(0.2)  # +20% bonus
   ```

## 🚀 Mejoras Futuras

- [ ] Soporte para más tipos de bases de datos
- [ ] Detección de relaciones N:M
- [ ] Embeddings para similitud semántica
- [ ] Interfaz web
- [ ] Procesamiento en paralelo
- [ ] Cache de resultados
      # Prescription
        ]
        self.common_id_patterns.extend(self.medical_patterns)
```

### Cambiar umbral de confianza
```python
# Por defecto es 0.3 (30%)
candidates = detector.find_relationships()

# Filtrar solo relaciones con alta confianza
high_confidence = [c for c in candidates if c.confidence_score > 0.7]

# O modificar en el código:
if candidate and candidate.confidence_score > 0.5:  # Cambiar umbral
    candidates.append(candidate)
```

### Cambiar modelo de AI
```python
analyze_database_with_ai(tables, ollama_model="codellama:latest")
```

## 📝 Archivos Generados

- `relationships.json`: Todas las relaciones detectadas con evidencia
- Logs en consola con detalles del análisis

## 🧪 Testing y Verificación

### Test de No-Confusión de PKs
Para verificar que el sistema no confunde PKs entre tablas:

```bash
python test_pk_detection.py
```

### Test de Nombres Complejos
Para probar con nombres no estándar:

```bash
python test_complex_names.py
```

Output esperado:
```
🧪 TEST: Detección con Nombres de Columnas No Estándar
======================================================================

🔑 Detectando claves primarias...
  - patients: PatientUID (confianza: 100%)
  - pets: AnimalIdentifier (confianza: 100%)
  - appointments: CitaID (confianza: 100%)

✅ ENCONTRADA: pets.OwnerPatientCode → patients.PatientUID
   Confianza: 96.5%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: appointments.pacienteIdentificador → patients.PatientUID
   Confianza: 94.0%
   Coincidencia valores: 80.0%

✅ ENCONTRADA: prescriptions.MedicationCode → medications.MedicationUUID
   Confianza: 91.5%
   Coincidencia valores: 75.0%

📈 Resumen: 7/7 relaciones esperadas encontradas

🔤 Análisis de Descomposición de Nombres:
----------------------------------------------------------------------

'OwnerPatientCode':
  - Palabras: {'owner', 'patient', 'code'}
  - Palabras base: {'owner', 'patient'}
  - Tiene ID: True

'pacienteIdentificador':
  - Palabras: {'paciente', 'identificador'}
  - Palabras base: {'paciente'}
  - Tiene ID: True
```

## 📝 Ejemplos de Uso con Nombres No Estándar

### Ejemplo 1: Base de datos con nomenclatura mixta
```python
tables = {
    'Customers': pd.DataFrame({
        'CustomerUID': ['C001', 'C002', 'C003'],
        'FullName': ['John Doe', 'Jane Smith', 'Bob Johnson']
    }),
    'Orders': pd.DataFrame({
        'OrderIdentifier': ['O1001', 'O1002', 'O1003'],
        'ClientReference': ['C001', 'C002', 'C001']  # FK a Customers.CustomerUID
    })
}

detector = SmartRelationshipDetector(tables)
candidates = detector.find_relationships()

# Detectará: Orders.ClientReference → Customers.CustomerUID
```

### Ejemplo 2: Nombres en español/mixtos
```python
tables = {
    'pacientes': pd.DataFrame({
        'pacienteID': [1, 2, 3],
        'nombreCompleto': ['Juan', 'María', 'Carlos']
    }),
    'citas': pd.DataFrame({
        'citaNumero': [101, 102, 103],
        'pacienteIdentificador': [1, 2, 1]  # FK a pacientes.pacienteID
    })
}

# El sistema detectará la relación correctamente
```

### Ejemplo 3: CamelCase y términos técnicos
```python
tables = {
    'SystemUsers': pd.DataFrame({
        'UserGUID': ['550e8400-e29b-41d4-a716-446655440001', ...],
        'Username': ['admin', 'user1', 'user2']
    }),
    'AuditLogs': pd.DataFrame({
        'LogEntryID': [1, 2, 3],
        'PerformedByUserIdentifier': ['550e8400-e29b-41d4-a716-446655440001', ...]
    })
}

# Detectará: AuditLogs.PerformedByUserIdentifier → SystemUsers.UserGUID
```

## ⚠️ Consideraciones

1. **Performance**: El análisis de valores puede ser lento en tablas grandes
2. **Memoria**: Carga todas las tablas en memoria
3. **AI**: Requiere Ollama ejecutándose localmente
4. **Precisión**: Los resultados son sugerencias, siempre revisar manualmente

## 🐛 Solución de Problemas

### "Ollama no está disponible"
```bash
# Iniciar Ollama
ollama serve

# Verificar que esté corriendo
curl http://localhost:11434/api/tags
```

### "No se encontraron relaciones"
- Verificar que las columnas tengan valores coincidentes
- Ajustar el umbral mínimo de confianza (default: 0.3)
- Revisar los nombres de columnas

### "Se detectan relaciones incorrectas entre PKs"
El sistema ya incluye protección contra esto, pero si sucede:
- Verificar que las PKs se detecten correctamente
- Revisar el método `_calculate_name_similarity()`
- Aumentar la penalización para relaciones PK-PK

### Errores de memoria
- Procesar tablas más pequeñas
- Usar samples de datos
- Aumentar la memoria disponible

## 🔧 Cambios Clave para Evitar Confusión de PKs

1. **Detección automática de PKs**: El sistema identifica columnas que son PKs basándose en:
   - Valores únicos para cada fila
   - Sin valores nulos
   - Nombres típicos ('id', 'tabla_id')

2. **Reglas de similitud mejoradas**:
   ```python
   # REGLA 1: PKs de diferentes tablas NO se relacionan
   if source_name == 'id' and target_name == 'id':
       return 0.0
   
   # REGLA 2: Patrón FK clásico obtiene alta puntuación
   # pets.patient_id → patients.id = 95% confianza
   ```

3. **Penalización en evaluación**:
   ```python
   # Si ambas son PKs, penalización fuerte
   if source_is_pk and target_is_pk:
       scores.append(-0.5)  # -50% al score total
   ```

4. **Bonus para patrones correctos**:
   ```python
   # Bonus si detectamos patrón FK → PK correcto
   if target_is_pk and not source_is_pk:
       if source_column.endswith(f"{target_table}_id"):
           scores.append(0.2)  # +20% bonus
   ```

## 🚀 Mejoras Futuras

- [ ] Soporte para más tipos de bases de datos
- [ ] Detección de relaciones N:M
- [ ] Embeddings para similitud semántica
- [ ] Interfaz web
- [ ] Procesamiento en paralelo
- [ ] Cache de resultados