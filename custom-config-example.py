#!/usr/bin/env python3
"""
Ejemplo de configuración personalizada para diferentes dominios y nomenclaturas
"""

import pandas as pd
from smart_detector import SmartRelationshipDetector

class CustomDomainDetector(SmartRelationshipDetector):
    """Detector personalizado para un dominio específico"""
    
    def __init__(self, tables, domain='general'):
        super().__init__(tables)
        
        # Configurar según el dominio
        if domain == 'medical':
            self._configure_medical()
        elif domain == 'ecommerce':
            self._configure_ecommerce()
        elif domain == 'education':
            self._configure_education()
        elif domain == 'financial':
            self._configure_financial()
        
        print(f"✅ Configurado para dominio: {domain}")
    
    def _configure_medical(self):
        """Configuración para sistemas médicos"""
        # Patrones de ID médicos
        self.common_id_patterns.extend([
            r'_mrn$',           # Medical Record Number
            r'_npi$',           # National Provider Identifier
            r'_dx$',            # Diagnosis code
            r'_rx$',            # Prescription
            r'_cpt$',           # CPT code
            r'_icd\d*$',        # ICD codes
            r'_hl7$',           # HL7 identifier
            r'historiaclinica$', # Spanish
            r'expediente$'      # Spanish
        ])
        
        # Palabras clave médicas
        self.id_keywords.extend([
            'mrn', 'npi', 'license', 'provider', 'practitioner',
            'expediente', 'historia', 'ficha', 'registro'
        ])
        
        # Mapeos semánticos médicos
        self.common_name_mappings.update({
            'patient': ['patient', 'paciente', 'enfermo', 'case', 'subject', 'persona'],
            'doctor': ['doctor', 'physician', 'medico', 'practitioner', 'provider', 'profesional'],
            'diagnosis': ['diagnosis', 'diagnostico', 'dx', 'finding', 'condition'],
            'treatment': ['treatment', 'tratamiento', 'therapy', 'intervention', 'procedure'],
            'medication': ['medication', 'medicine', 'drug', 'medicamento', 'farmaco', 'rx'],
            'appointment': ['appointment', 'visit', 'cita', 'consulta', 'encuentro'],
            'insurance': ['insurance', 'seguro', 'coverage', 'plan', 'cobertura']
        })
    
    def _configure_ecommerce(self):
        """Configuración para sistemas de e-commerce"""
        self.common_id_patterns.extend([
            r'_sku$',           # Stock Keeping Unit
            r'_upc$',           # Universal Product Code
            r'_ean$',           # European Article Number
            r'_asin$',          # Amazon Standard ID
            r'ordernum$',       # Order number variations
            r'pedido$',         # Spanish
            r'factura$'         # Spanish invoice
        ])
        
        self.id_keywords.extend([
            'sku', 'upc', 'ean', 'asin', 'barcode', 'serial',
            'pedido', 'orden', 'factura', 'tracking'
        ])
        
        self.common_name_mappings.update({
            'customer': ['customer', 'client', 'cliente', 'buyer', 'comprador', 'user'],
            'order': ['order', 'pedido', 'purchase', 'compra', 'transaction'],
            'product': ['product', 'item', 'producto', 'articulo', 'merchandise', 'goods'],
            'cart': ['cart', 'basket', 'carrito', 'cesta', 'bag'],
            'payment': ['payment', 'pago', 'transaction', 'transaccion', 'billing'],
            'shipping': ['shipping', 'envio', 'delivery', 'entrega', 'dispatch']
        })
    
    def _configure_education(self):
        """Configuración para sistemas educativos"""
        self.common_id_patterns.extend([
            r'_matricula$',     # Spanish enrollment
            r'_legajo$',        # Spanish file number
            r'studentid$',      # Student ID variations
            r'enrollmentno$',   # Enrollment number
            r'_sid$',           # Student ID
            r'_tid$'            # Teacher ID
        ])
        
        self.id_keywords.extend([
            'matricula', 'legajo', 'enrollment', 'registro',
            'student', 'alumno', 'estudiante', 'pupil'
        ])
        
        self.common_name_mappings.update({
            'student': ['student', 'alumno', 'estudiante', 'pupil', 'learner', 'aprendiz'],
            'teacher': ['teacher', 'profesor', 'docente', 'instructor', 'educator', 'maestro'],
            'course': ['course', 'curso', 'class', 'clase', 'subject', 'materia', 'asignatura'],
            'grade': ['grade', 'nota', 'calificacion', 'score', 'mark', 'puntaje'],
            'enrollment': ['enrollment', 'matricula', 'inscripcion', 'registration'],
            'semester': ['semester', 'semestre', 'term', 'periodo', 'trimester', 'cuatrimestre']
        })
    
    def _configure_financial(self):
        """Configuración para sistemas financieros"""
        self.common_id_patterns.extend([
            r'_account$',       # Account number
            r'_acct$',          # Account abbreviation
            r'_trans$',         # Transaction
            r'_ref$',           # Reference
            r'cuenta$',         # Spanish account
            r'_iban$',          # International Bank Account
            r'_swift$',         # SWIFT code
            r'_routing$'        # Routing number
        ])
        
        self.id_keywords.extend([
            'account', 'cuenta', 'transaction', 'transaccion',
            'reference', 'referencia', 'folio', 'voucher'
        ])
        
        self.common_name_mappings.update({
            'account': ['account', 'cuenta', 'acc', 'acct'],
            'customer': ['customer', 'client', 'cliente', 'holder', 'titular'],
            'transaction': ['transaction', 'transaccion', 'trans', 'movement', 'movimiento'],
            'balance': ['balance', 'saldo', 'amount', 'monto', 'importe'],
            'branch': ['branch', 'sucursal', 'office', 'oficina', 'agency'],
            'card': ['card', 'tarjeta', 'debit', 'credit', 'credito', 'debito']
        })

# Ejemplo de uso con diferentes dominios
def demo_custom_detectors():
    """Demuestra el uso de detectores personalizados"""
    
    # Ejemplo 1: Sistema médico con nomenclatura mixta
    print("\n🏥 EJEMPLO 1: Sistema Médico")
    print("=" * 60)
    
    medical_tables = {
        'Pacientes': pd.DataFrame({
            'HistoriaClinicaNum': ['HC001', 'HC002', 'HC003'],
            'NombreCompleto': ['Juan Pérez', 'María García', 'Carlos López'],
            'FechaNacimiento': ['1980-01-15', '1975-03-22', '1990-07-08']
        }),
        'Medicos': pd.DataFrame({
            'NPINumber': ['1234567890', '0987654321', '1122334455'],
            'NombreProfesional': ['Dr. Smith', 'Dra. Johnson', 'Dr. Williams'],
            'Especialidad': ['Cardiología', 'Pediatría', 'Neurología']
        }),
        'Consultas': pd.DataFrame({
            'ConsultaID': [1001, 1002, 1003],
            'PacienteHC': ['HC001', 'HC002', 'HC001'],  # FK a Pacientes
            'MedicoNPI': ['1234567890', '0987654321', '1234567890'],  # FK a Medicos
            'FechaConsulta': ['2024-01-15', '2024-01-16', '2024-01-17']
        })
    }
    
    detector = CustomDomainDetector(medical_tables, domain='medical')
    candidates = detector.find_relationships()
    detector.print_results(candidates[:5])
    
    # Ejemplo 2: Sistema de e-commerce multiidioma
    print("\n\n🛒 EJEMPLO 2: Sistema E-Commerce")
    print("=" * 60)
    
    ecommerce_tables = {
        'Clientes': pd.DataFrame({
            'ClienteUID': ['CLI-001', 'CLI-002', 'CLI-003'],
            'Email': ['juan@email.com', 'maria@email.com', 'carlos@email.com']
        }),
        'Productos': pd.DataFrame({
            'ProductSKU': ['LAPTOP-001', 'MOUSE-002', 'KEYB-003'],
            'NombreProducto': ['Laptop Pro', 'Mouse Wireless', 'Teclado Mecánico'],
            'PrecioUnitario': [999.99, 29.99, 89.99]
        }),
        'Pedidos': pd.DataFrame({
            'NumeroPedido': ['PED-2024-001', 'PED-2024-002', 'PED-2024-003'],
            'ClienteReferencia': ['CLI-001', 'CLI-002', 'CLI-001'],  # FK
            'FechaPedido': ['2024-01-15', '2024-01-16', '2024-01-17']
        }),
        'DetallesPedido': pd.DataFrame({
            'DetalleID': [1, 2, 3, 4],
            'PedidoNum': ['PED-2024-001', 'PED-2024-001', 'PED-2024-002', 'PED-2024-003'],
            'ArticuloSKU': ['LAPTOP-001', 'MOUSE-002', 'KEYB-003', 'LAPTOP-001'],
            'Cantidad': [1, 2, 1, 1]
        })
    }
    
    detector = CustomDomainDetector(ecommerce_tables, domain='ecommerce')
    candidates = detector.find_relationships()
    detector.print_results(candidates[:5])
    
    # Ejemplo 3: Sistema educativo
    print("\n\n🎓 EJEMPLO 3: Sistema Educativo")
    print("=" * 60)
    
    education_tables = {
        'Estudiantes': pd.DataFrame({
            'MatriculaNum': ['MAT-2024-001', 'MAT-2024-002', 'MAT-2024-003'],
            'NombreAlumno': ['Ana López', 'Pedro Martín', 'Laura Sánchez']
        }),
        'Profesores': pd.DataFrame({
            'LegajoDocente': ['DOC-001', 'DOC-002', 'DOC-003'],
            'NombreProfesor': ['Prof. García', 'Prof. Rodríguez', 'Prof. Fernández']
        }),
        'Cursos': pd.DataFrame({
            'CodigoCurso': ['MAT-101', 'FIS-201', 'QUI-301'],
            'NombreMateria': ['Matemáticas I', 'Física II', 'Química III'],
            'ProfesorAsignado': ['DOC-001', 'DOC-002', 'DOC-003']  # FK
        }),
        'Inscripciones': pd.DataFrame({
            'InscripcionID': [1, 2, 3, 4, 5],
            'EstudianteMatricula': ['MAT-2024-001', 'MAT-2024-001', 'MAT-2024-002', 'MAT-2024-003', 'MAT-2024-003'],
            'CursoInscrito': ['MAT-101', 'FIS-201', 'MAT-101', 'QUI-301', 'FIS-201']  # FK
        })
    }
    
    detector = CustomDomainDetector(education_tables, domain='education')
    candidates = detector.find_relationships()
    detector.print_results(candidates[:5])

# Función para analizar tu propia base de datos con dominio específico
def analyze_custom_database(csv_files, domain='general'):
    """
    Analiza una base de datos con configuración de dominio específico
    
    Args:
        csv_files: Dict con nombres de tabla y rutas de archivo
        domain: 'medical', 'ecommerce', 'education', 'financial', 'general'
    """
    # Cargar tablas
    tables = {}
    for table_name, file_path in csv_files.items():
        try:
            tables[table_name] = pd.read_csv(file_path)
            print(f"✅ Cargado: {table_name} ({tables[table_name].shape[0]} filas)")
        except Exception as e:
            print(f"❌ Error cargando {file_path}: {e}")
    
    if not tables:
        print("No se pudieron cargar tablas")
        return
    
    # Crear detector personalizado
    detector = CustomDomainDetector(tables, domain=domain)
    
    # Encontrar relaciones
    candidates = detector.find_relationships()
    
    # Mostrar resultados
    detector.print_results(candidates, top_n=20)
    
    # Exportar resultados
    detector.export_results(candidates, f"relationships_{domain}.json")
    
    return candidates

if __name__ == "__main__":
    # Ejecutar demos
    demo_custom_detectors()
    
    # Ejemplo de uso con tus propios archivos
    # my_files = {
    #     'pacientes': 'data/pacientes.csv',
    #     'consultas': 'data/consultas.csv',
    #     'medicos': 'data/medicos.csv'
    # }
    # analyze_custom_database(my_files, domain='medical')
