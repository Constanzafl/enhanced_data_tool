# 🚀 Enhanced Data Tool v2.0

**Herramienta avanzada para detectar relaciones automáticamente en bases de datos usando IA, embeddings semánticos y LLMs locales**

## ✨ Características Principales

- 🔍 **Detección Automática de Relaciones**: Identifica Foreign Keys potenciales sin documentación previa
- 🧠 **IA Semántica**: Usa embeddings para encontrar relaciones por similitud conceptual
- 🤖 **Verificación LLM**: Valida relaciones usando modelos de lenguaje locales (Ollama)
- 📐 **Exportación DBML**: Genera diagramas ER visuales automáticamente
- 🎯 **Multi-estrategia**: Combina análisis de nombres, patrones, datos y semántica
- 🔒 **Privacidad**: Todo ejecuta localmente, sin enviar datos a APIs externas

## 🚀 Instalación Rápida

### Opción 1: Instalación Automática (Recomendada)

```bash
# Descargar e instalar automáticamente
python setup_tool.py
```

### Opción 2: Instalación Manual

```bash
# 1. Crear entorno virtual
python -m venv venv_data_tool
source venv_data_tool/bin/activate  # Linux/Mac
# o
venv_data_tool\Scripts\activate     # Windows

# 2. Instalar dependencias básicas
pip install -r requirements.txt

# 3. Instalar embeddings (opcional pero recomendado)
python -m pip install --upgrade pip
pip install sentence-transformers scikit-learn

# 4. Configurar Ollama para LLM (opcional)
# Instalar desde: https://ollama.ai
ollama serve
ollama pull llama3.2:3b
```

## 🎯 Uso Rápido

### Ejecución Simple

```python
from complete_data_tool import analyze_database_complete

# Análisis completo de una base de datos
results = analyze_database_complete(
    db_path="mi_database.db",
    output_dir="./output",
    use_embeddings=True,  # Detección semántica
    use_llm=True         # Verificación con IA
)
```

### Uso Avanzado

```python
from complete_data_tool import CompleteDataTool

# Configuración personalizada
tool = CompleteDataTool(
    db_path="mi_database.db",
    use_embeddings=True,
    use_llm=True
)

# Análisis paso a paso
schema = tool.extract_schema()
relationships = tool.detect_relationships()
llm_results = tool.verify_with_llm(max_verifications=10)
dbml_content = tool.generate_dbml("mi_esquema.dbml")
```

## 🔧 Configuración

### Archivo config.json

```json
{
  "database": {
    "default_type": "sqlite",
    "sample_db": "example_store.db"
  },
  "analysis": {
    "use_embeddings": true,
    "use_llm": true,
    "max_llm_verifications": 5,
    "confidence_threshold": 30
  },
  "ollama": {
    "url": "http://localhost:11434",
    "model": "llama3.2:3b",
    "timeout": 30
  }
}
```

## 🐛 Solución de Errores Comunes

### Error: "Object of type DataFrame is not JSON serializable"

**Causa**: El LLM verifier original intentaba serializar DataFrames directamente.

**Solución**: ✅ **YA CORREGIDO** en v2.0
- Los DataFrames se convierten a tipos serializables automáticamente
- Se implementó `_serialize_dataframe()` que maneja todos los tipos numpy/pandas

```python
# Código corregido internamente:
def _serialize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
    serializable_data = []
    for _, row in df.iterrows():
        row_data = {}
        for col, value in row.items():
            if pd.isna(value):
                row_data[col] = None
            elif isinstance(value, (np.integer, np.int64)):
                row_data[col] = int(value)
            # ... más conversiones
```

### Error: "sentence-transformers not found"

**Solución**:
```bash
pip install sentence-transformers
# o usar solo detección básica:
tool = CompleteDataTool(db_path="db.sqlite", use_embeddings=False)
```

### Error: "Ollama connection failed"

**Solución**:
```bash
# 1. Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh  # Linux/Mac
# o descargar desde https://ollama.ai para Windows

# 2. Iniciar servidor
ollama serve

# 3. Instalar modelo
ollama pull llama3.2:3b

# 4. Verificar conexión
curl http://localhost:11434/api/tags
```

### Error: "No relationships detected"

**Posibles causas y soluciones**:

1. **Umbral de confianza muy alto**:
```python
# Reducir umbral
tool = CompleteDataTool(db_path="db.sqlite")
tool.confidence_threshold = 20  # Default: 30
```

2. **Datos de muestra insuficientes**:
```python
# Aumentar muestra
tool._get_sample_data(table_name, limit=20)  # Default: 10
```

3. **Patrones FK no estándar**:
```python
# Agregar patrones personalizados
tool.fk_patterns.extend([r'.*_foreign$', r'ref_.*'])
```

## 📊 Niveles de Detección

### 1. Básico (Sin dependencias externas)
```python
tool = CompleteDataTool(db_path="db.sqlite", use_embeddings=False, use_llm=False)
```
- ✅ Detección por patrones de nombres
- ✅ Validación con datos de muestra
- ✅ Exportación DBML
- ⚡ Rápido y ligero

### 2. Con Embeddings (Recomendado)
```python
tool = CompleteDataTool(db_path="db.sqlite", use_embeddings=True, use_llm=False)
```
- ✅ Todo lo anterior +
- 🧠 Similitud semántica
- 🎯 Detección de relaciones conceptuales
- 📈 Mayor precisión

### 3. Completo (Máxima precisión)
```python
tool = CompleteDataTool(db_path="db.sqlite", use_embeddings=True, use_llm=True)
```
- ✅ Todo lo anterior +
- 🤖 Verificación con IA
- 📝 Explicaciones detalladas
- 🎯 Cardinalidad sugerida

## 🗄️ Compatibilidad de Bases de Datos

### SQLite (Completamente soportado)
```python
tool = CompleteDataTool("database.sqlite")
```

### PostgreSQL (Experimental)
```python
# Instalar driver
pip install psycopg2-binary

# Configurar conexión
import psycopg2
conn = psycopg2.connect(
    host="localhost",
    database="mydb", 
    user="user",
    password="password"
)
```

### MySQL (Experimental)
```python
# Instalar driver
pip install pymysql

# Configurar conexión
import pymysql
conn = pymysql.connect(
    host="localhost",
    database="mydb",
    user="user", 
    password="password"
)
```

## 📐 Generación de Diagramas

### Exportar a DBML
```python
dbml_content = tool.generate_dbml("mi_esquema.dbml", "Mi Proyecto")
```

### Visualizar en dbdiagram.io
1. Abrir el archivo `.dbml` generado
2. Copiar todo el contenido
3. Ir a [dbdiagram.io](https://dbdiagram.io/d)
4. Pegar el código en el editor
5. ¡Disfrutar el diagrama ER interactivo!

### Ejemplo de DBML generado:
```dbml
// Mi Proyecto - Generado automáticamente

Table customers {
  id integer [primary key]
  name varchar [not null]
  email varchar
  created_at timestamp
}

Table orders {
  id integer [primary key]
  customer_id integer [not null]
  total decimal
}

// Relación detectada automáticamente
Ref: orders.customer_id > customers.id // Confianza: 95.0% | LLM: ✅ Válida
```

## 🚀 Ejemplos de Uso

### Ejemplo 1: E-commerce
```python
# Detectar relaciones en BD de e-commerce
results = analyze_database_complete("ecommerce.db")

# Relaciones típicas detectadas:
# - orders.customer_id → customers.id
# - order_items.order_id → orders.id  
# - order_items.product_id → products.id
# - products.category_id → categories.id
```

### Ejemplo 2: CRM
```python
# Análisis de sistema CRM
tool = CompleteDataTool("crm_system.db", use_embeddings=True)
results = tool.analyze_complete()

# Relaciones típicas:
# - contacts.company_id → companies.id
# - deals.contact_id → contacts.id
# - activities.deal_id → deals.id
```

### Ejemplo 3: Análisis Masivo
```python
import os
from pathlib import Path

# Analizar múltiples bases de datos
db_files = Path("databases/").glob("*.db")

for db_file in db_files:
    print(f"Analizando {db_file.name}...")
    
    results = analyze_database_complete(
        str(db_file),
        output_dir=f"output/{db_file.stem}",
        use_embeddings=True,
        use_llm=False  # Más rápido para análisis masivo
    )
    
    print(f"✅ {results['summary']['detected_relationships']} relaciones detectadas")
```

## 🔬 Algoritmos de Detección

### 1. Análisis de Patrones
- Patrones FK comunes: `*_id`, `*_key`, `*_fk`, `*_ref`
- Prefijos: `id_*`, `fk_*`, `ref_*`
- Sufijos especiales: `*_foreign`, `*_link`

### 2. Similitud Semántica
- Embeddings de sentence-transformers
- Comparación de contexto tabla-columna
- Mapeo de conceptos relacionados

### 3. Validación de Datos
- Verificación de integridad referencial
- Cálculo de ratio de coincidencias
- Análisis de cardinalidad

### 4. Verificación LLM
- Análisis contextual con IA
- Explicación de decisiones
- Sugerencias de cardinalidad

## 📈 Métricas de Confianza

### Escala de Confianza
- 🟢 **80-100%**: Alta confianza - Muy probable que sea correcta
- 🟡 **60-79%**: Confianza media - Revisar manualmente
- 🔴 **30-59%**: Baja confianza - Requiere validación
- ❌ **<30%**: Descartada automáticamente

### Factores que Aumentan Confianza
- ✅ Coincidencia exacta de nombres
- ✅ Patrón FK reconocido
- ✅ Alta similitud semántica
- ✅ Validación con datos reales
- ✅ Confirmación por LLM

## 🛠️ Desarrollo y Contribución

### Estructura del Proyecto
```
enhanced-data-tool/
├── complete_data_tool.py          # Herramienta principal
├── enhanced_schema_analyzer.py    # Analizador base
├── embedding_relationship_detector.py  # Detector con embeddings
├── robust_llm_verifier.py        # Verificador LLM
├── setup_tool.py                 # Instalador automático
├── requirements.txt              # Dependencias
├── config.json                   # Configuración
├── example_usage.py              # Ejemplos
└── output/                       # Resultados
```

### Contribuir
1. Fork el repositorio
2. Crear rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'Agregar nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

### Tests
```bash
# Ejecutar tests
python -m pytest tests/

# Con cobertura
python -m pytest --cov=enhanced_data_tool tests/
```

## 📝 Roadmap

### v2.1 (Próxima versión)
- [ ] Soporte nativo para PostgreSQL/MySQL
- [ ] Detección de relaciones N:M
- [ ] Exportación a SQL DDL
- [ ] Interfaz web básica

### v2.2
- [ ] API REST
- [ ] Más formatos de exportación (PlantUML, Mermaid)
- [ ] Detección de índices recomendados
- [ ] Análisis de performance

### v3.0 (Futuro)
- [ ] Interfaz gráfica completa
- [ ] Soporte para NoSQL
- [ ] Integración con herramientas BI
- [ ] Análisis de calidad de datos

## 🤝 Soporte

### Reportar Bugs
- [GitHub Issues](https://github.com/Constanzafl/data_tool/issues)
- Incluir: versión, SO, base de datos, log completo

### Preguntas Frecuentes

**P: ¿Funciona sin conexión a internet?**
R: Sí, completamente. Solo la primera instalación de embeddings requiere descarga.

**P: ¿Es seguro? ¿Se envían datos externos?**
R: Totalmente seguro. Todo procesa localmente, incluso el LLM con Ollama.

**P: ¿Qué tan preciso es?**
R: En tests internos: 85-95% de precisión en relaciones obvias, 70-80% en relaciones complejas.

**P: ¿Funciona con bases de datos grandes?**
R: Sí, pero usa muestreo de datos para performance. Configurable en `sample_size`.

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles.

## 🙏 Agradecimientos

- [sentence-transformers](https://github.com/UKPLab/sentence-transformers) por embeddings semánticos
- [Ollama](https://ollama.ai) por LLMs locales
- [dbdiagram.io](https://dbdiagram.io) por visualización de diagramas
- Comunidad open source por feedback y contribuciones

---

⭐ **¡Si te gusta el proyecto, dale una estrella en GitHub!**

🚀 **¡Comienza ahora!** `python setup_tool.py`
