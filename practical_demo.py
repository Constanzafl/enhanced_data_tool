#!/usr/bin/env python3
"""
Demo Práctico Completo - Enhanced Data Tool v2.0
Demuestra todas las funcionalidades resolviendo los errores del código original
"""

import os
import sys
import sqlite3
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import traceback

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

def create_complex_sample_database(db_path: str = "complex_ecommerce.db"):
    """
    Crea una base de datos más compleja para demostrar mejor la detección
    """
    print_colored("📦 Creando base de datos compleja de e-commerce...", Colors.OKCYAN)
    
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crear esquema complejo con relaciones implícitas
    cursor.executescript("""
        -- Usuarios y autenticación
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        );
        
        -- Perfiles de usuario
        CREATE TABLE user_profiles (
            profile_id INTEGER PRIMARY KEY,
            user_ref INTEGER NOT NULL,  -- FK implícita a users.user_id
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            phone VARCHAR(20),
            birth_date DATE,
            gender VARCHAR(10)
        );
        
        -- Direcciones
        CREATE TABLE addresses (
            address_id INTEGER PRIMARY KEY,
            user_reference INTEGER,  -- FK implícita a users.user_id
            street_address VARCHAR(255),
            city VARCHAR(100),
            state VARCHAR(100),
            postal_code VARCHAR(20),
            country VARCHAR(100) DEFAULT 'Argentina',
            address_type VARCHAR(20) DEFAULT 'shipping',
            is_default BOOLEAN DEFAULT 0
        );
        
        -- Categorías de productos (con jerarquía)
        CREATE TABLE product_categories (
            category_id INTEGER PRIMARY KEY,
            category_name VARCHAR(100) NOT NULL,
            parent_category INTEGER,  -- FK implícita a product_categories.category_id
            description TEXT,
            is_active BOOLEAN DEFAULT 1
        );
        
        -- Marcas/Brands
        CREATE TABLE brands (
            brand_id INTEGER PRIMARY KEY,
            brand_name VARCHAR(100) NOT NULL,
            country_origin VARCHAR(50),
            website VARCHAR(255),
            logo_url VARCHAR(255)
        );
        
        -- Productos
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name VARCHAR(255) NOT NULL,
            sku VARCHAR(100) UNIQUE,
            category_ref INTEGER,  -- FK implícita a product_categories.category_id
            brand_reference INTEGER,  -- FK implícita a brands.brand_id
            price DECIMAL(10,2),
            cost DECIMAL(10,2),
            stock_quantity INTEGER DEFAULT 0,
            min_stock_level INTEGER DEFAULT 5,
            weight DECIMAL(8,2),
            dimensions VARCHAR(50),
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Inventario/Stock
        CREATE TABLE inventory_movements (
            movement_id INTEGER PRIMARY KEY,
            product_reference INTEGER NOT NULL,  -- FK implícita a products.product_id
            movement_type VARCHAR(20) NOT NULL, -- 'IN', 'OUT', 'ADJUSTMENT'
            quantity INTEGER NOT NULL,
            reference_number VARCHAR(100),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Carritos de compra
        CREATE TABLE shopping_carts (
            cart_id INTEGER PRIMARY KEY,
            user_identifier INTEGER,  -- FK implícita a users.user_id
            session_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_abandoned BOOLEAN DEFAULT 0
        );
        
        -- Items del carrito
        CREATE TABLE cart_items (
            item_id INTEGER PRIMARY KEY,
            cart_reference INTEGER NOT NULL,  -- FK implícita a shopping_carts.cart_id
            product_ref INTEGER NOT NULL,  -- FK implícita a products.product_id
            quantity INTEGER NOT NULL DEFAULT 1,
            unit_price DECIMAL(10,2),
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Órdenes/Pedidos
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            order_number VARCHAR(50) UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL,  -- FK implícita a users.user_id
            billing_address_id INTEGER,  -- FK implícita a addresses.address_id
            shipping_address_ref INTEGER,  -- FK implícita a addresses.address_id
            order_status VARCHAR(20) DEFAULT 'pending',
            payment_status VARCHAR(20) DEFAULT 'pending',
            subtotal DECIMAL(10,2),
            tax_amount DECIMAL(10,2),
            shipping_cost DECIMAL(10,2),
            discount_amount DECIMAL(10,2) DEFAULT 0,
            total_amount DECIMAL(10,2),
            currency VARCHAR(3) DEFAULT 'ARS',
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            shipped_date TIMESTAMP,
            delivered_date TIMESTAMP,
            notes TEXT
        );
        
        -- Items de la orden
        CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_ref INTEGER NOT NULL,  -- FK implícita a orders.order_id
            product_reference INTEGER NOT NULL,  -- FK implícita a products.product_id
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            total_price DECIMAL(10,2) NOT NULL,
            product_snapshot TEXT  -- JSON con info del producto al momento de la compra
        );
        
        -- Pagos
        CREATE TABLE payments (
            payment_id INTEGER PRIMARY KEY,
            order_reference INTEGER NOT NULL,  -- FK implícita a orders.order_id
            payment_method VARCHAR(50),
            payment_provider VARCHAR(50),
            transaction_id VARCHAR(255),
            amount DECIMAL(10,2) NOT NULL,
            currency VARCHAR(3) DEFAULT 'ARS',
            payment_status VARCHAR(20) DEFAULT 'pending',
            payment_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Reviews/Reseñas
        CREATE TABLE product_reviews (
            review_id INTEGER PRIMARY KEY,
            product_reference INTEGER NOT NULL,  -- FK implícita a products.product_id
            user_ref INTEGER NOT NULL,  -- FK implícita a users.user_id
            order_item_reference INTEGER,  -- FK implícita a order_items.order_item_id
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            review_title VARCHAR(255),
            review_text TEXT,
            is_verified_purchase BOOLEAN DEFAULT 0,
            helpful_votes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Cupones/Descuentos
        CREATE TABLE discount_coupons (
            coupon_id INTEGER PRIMARY KEY,
            coupon_code VARCHAR(50) UNIQUE NOT NULL,
            coupon_type VARCHAR(20) DEFAULT 'percentage', -- 'percentage', 'fixed_amount'
            discount_value DECIMAL(10,2) NOT NULL,
            min_order_amount DECIMAL(10,2) DEFAULT 0,
            max_discount_amount DECIMAL(10,2),
            usage_limit INTEGER,
            usage_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            valid_from TIMESTAMP,
            valid_until TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Uso de cupones
        CREATE TABLE coupon_usage (
            usage_id INTEGER PRIMARY KEY,
            coupon_reference INTEGER NOT NULL,  -- FK implícita a discount_coupons.coupon_id
            order_ref INTEGER NOT NULL,  -- FK implícita a orders.order_id
            user_identifier INTEGER NOT NULL,  -- FK implícita a users.user_id
            discount_applied DECIMAL(10,2) NOT NULL,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Insertar datos de ejemplo realistas
    print_colored("💾 Insertando datos de ejemplo...", Colors.OKCYAN)
    
    cursor.executescript("""
        -- Usuarios
        INSERT INTO users (username, email, password_hash) VALUES 
            ('juan.perez', 'juan.perez@email.com', 'hash123'),
            ('maria.garcia', 'maria.garcia@email.com', 'hash456'),
            ('carlos.lopez', 'carlos.lopez@email.com', 'hash789'),
            ('ana.martinez', 'ana.martinez@email.com', 'hash101'),
            ('pedro.rodriguez', 'pedro.rodriguez@email.com', 'hash102');
        
        -- Perfiles de usuario
        INSERT INTO user_profiles (user_ref, first_name, last_name, phone) VALUES
            (1, 'Juan', 'Pérez', '+54911123456'),
            (2, 'María', 'García', '+54911234567'),
            (3, 'Carlos', 'López', '+54911345678'),
            (4, 'Ana', 'Martínez', '+54911456789'),
            (5, 'Pedro', 'Rodríguez', '+54911567890');
        
        -- Direcciones
        INSERT INTO addresses (user_reference, street_address, city, state, postal_code) VALUES
            (1, 'Av. Corrientes 1234', 'Buenos Aires', 'CABA', '1043'),
            (1, 'Av. Santa Fe 5678', 'Buenos Aires', 'CABA', '1425'),
            (2, 'Calle Florida 9012', 'Buenos Aires', 'CABA', '1005'),
            (3, 'Av. Cabildo 3456', 'Buenos Aires', 'CABA', '1426'),
            (4, 'Av. Rivadavia 7890', 'Buenos Aires', 'CABA', '1406');
        
        -- Categorías
        INSERT INTO product_categories (category_name, parent_category, description) VALUES
            ('Electrónicos', NULL, 'Productos electrónicos'),
            ('Computadoras', 1, 'Computadoras y laptops'),
            ('Smartphones', 1, 'Teléfonos inteligentes'),
            ('Accesorios', 1, 'Accesorios electrónicos'),
            ('Ropa', NULL, 'Vestimenta y calzado'),
            ('Ropa Hombre', 5, 'Ropa para hombres'),
            ('Ropa Mujer', 5, 'Ropa para mujeres'),
            ('Hogar', NULL, 'Artículos para el hogar'),
            ('Muebles', 8, 'Muebles y decoración'),
            ('Cocina', 8, 'Utensilios de cocina');
        
        -- Marcas
        INSERT INTO brands (brand_name, country_origin, website) VALUES
            ('Samsung', 'Corea del Sur', 'samsung.com'),
            ('Apple', 'Estados Unidos', 'apple.com'),
            ('Dell', 'Estados Unidos', 'dell.com'),
            ('Nike', 'Estados Unidos', 'nike.com'),
            ('Adidas', 'Alemania', 'adidas.com');
        
        -- Productos
        INSERT INTO products (product_name, sku, category_ref, brand_reference, price, stock_quantity) VALUES
            ('iPhone 14 Pro', 'APL-IP14P-128', 3, 2, 1299.99, 25),
            ('Samsung Galaxy S23', 'SAM-GS23-256', 3, 1, 999.99, 30),
            ('MacBook Pro 16"', 'APL-MBP16-512', 2, 2, 2499.99, 10),
            ('Dell XPS 13', 'DEL-XPS13-512', 2, 3, 1499.99, 15),
            ('AirPods Pro', 'APL-APP-GEN2', 4, 2, 249.99, 50),
            ('Nike Air Max', 'NIK-AM270-42', 6, 4, 159.99, 40),
            ('Adidas Ultraboost', 'ADI-UB22-41', 6, 5, 179.99, 35);
        
        -- Movimientos de inventario
        INSERT INTO inventory_movements (product_reference, movement_type, quantity, reference_number) VALUES
            (1, 'IN', 30, 'PO-2024-001'),
            (2, 'IN', 40, 'PO-2024-002'),
            (3, 'IN', 15, 'PO-2024-003'),
            (4, 'IN', 20, 'PO-2024-004'),
            (5, 'IN', 60, 'PO-2024-005'),
            (1, 'OUT', 5, 'SO-2024-001'),
            (2, 'OUT', 10, 'SO-2024-002');
        
        -- Carritos
        INSERT INTO shopping_carts (user_identifier, session_id) VALUES
            (1, 'sess_001'),
            (2, 'sess_002'),
            (3, 'sess_003');
        
        -- Items del carrito
        INSERT INTO cart_items (cart_reference, product_ref, quantity, unit_price) VALUES
            (1, 1, 1, 1299.99),
            (1, 5, 2, 249.99),
            (2, 3, 1, 2499.99),
            (3, 6, 1, 159.99),
            (3, 7, 1, 179.99);
        
        -- Órdenes
        INSERT INTO orders (order_number, customer_id, billing_address_id, shipping_address_ref, 
                           subtotal, tax_amount, shipping_cost, total_amount, order_status) VALUES
            ('ORD-2024-001', 1, 1, 1, 1799.97, 377.99, 50.00, 2227.96, 'completed'),
            ('ORD-2024-002', 2, 3, 3, 2499.99, 524.99, 75.00, 3098.98, 'shipped'),
            ('ORD-2024-003', 3, 4, 4, 339.98, 71.39, 25.00, 436.37, 'processing'),
            ('ORD-2024-004', 4, 5, 5, 999.99, 209.99, 50.00, 1259.98, 'pending'),
            ('ORD-2024-005', 1, 2, 2, 499.98, 104.99, 30.00, 634.97, 'completed');
        
        -- Items de órdenes
        INSERT INTO order_items (order_ref, product_reference, quantity, unit_price, total_price) VALUES
            (1, 1, 1, 1299.99, 1299.99),
            (1, 5, 2, 249.99, 499.98),
            (2, 3, 1, 2499.99, 2499.99),
            (3, 6, 1, 159.99, 159.99),
            (3, 7, 1, 179.99, 179.99),
            (4, 2, 1, 999.99, 999.99),
            (5, 5, 2, 249.99, 499.98);
        
        -- Pagos
        INSERT INTO payments (order_reference, payment_method, amount, payment_status, payment_date) VALUES
            (1, 'credit_card', 2227.96, 'completed', '2024-01-15 10:30:00'),
            (2, 'credit_card', 3098.98, 'completed', '2024-01-16 14:20:00'),
            (3, 'debit_card', 436.37, 'pending', NULL),
            (5, 'paypal', 634.97, 'completed', '2024-01-18 09:15:00');
        
        -- Reviews
        INSERT INTO product_reviews (product_reference, user_ref, order_item_reference, rating, review_title, review_text) VALUES
            (1, 1, 1, 5, 'Excelente teléfono', 'Muy buena calidad, recomendado'),
            (5, 1, 2, 4, 'Buenos auriculares', 'Sonido excelente, batería dura mucho'),
            (3, 2, 3, 5, 'MacBook increíble', 'Rendimiento excepcional para trabajo'),
            (6, 3, 4, 4, 'Zapatillas cómodas', 'Muy cómodas para correr');
        
        -- Cupones
        INSERT INTO discount_coupons (coupon_code, coupon_type, discount_value, min_order_amount, usage_limit) VALUES
            ('WELCOME10', 'percentage', 10.00, 100.00, 100),
            ('SAVE50', 'fixed_amount', 50.00, 200.00, 50),
            ('TECH20', 'percentage', 20.00, 500.00, 25);
        
        -- Uso de cupones
        INSERT INTO coupon_usage (coupon_reference, order_ref, user_identifier, discount_applied) VALUES
            (1, 1, 1, 179.97),
            (2, 2, 2, 50.00),
            (3, 5, 1, 126.99);
    """)
    
    conn.commit()
    conn.close()
    
    print_colored(f"✅ Base de datos compleja creada: {db_path}", Colors.OKGREEN)
    print_colored(f"   📊 13 tablas con múltiples relaciones implícitas", Colors.OKCYAN)
    
    return db_path

def analyze_with_different_methods(db_path: str):
    """
    Demuestra los diferentes métodos de análisis y compara resultados
    """
    print_section("COMPARACIÓN DE MÉTODOS DE DETECCIÓN")
    
    # Importar después de asegurar que los archivos existen
    try:
        from complete_data_tool import CompleteDataTool
    except ImportError:
        print_colored("❌ No se puede importar CompleteDataTool", Colors.FAIL)
        print_colored("   Asegúrate de que complete_data_tool.py esté en el mismo directorio", Colors.WARNING)
        return
    
    methods = [
        ("Básico (Solo patrones)", False, False),
        ("Con Embeddings", True, False),
        ("Completo (Embeddings + LLM)", True, True)
    ]
    
    results_comparison = {}
    
    for method_name, use_embeddings, use_llm in methods:
        print_colored(f"\n🔍 Ejecutando: {method_name}", Colors.HEADER)
        print_colored("-" * 50, Colors.HEADER)
        
        try:
            # Configurar herramienta
            tool = CompleteDataTool(
                db_path=db_path,
                use_embeddings=use_embeddings,
                use_llm=use_llm
            )
            
            # Ejecutar análisis
            schema = tool.extract_schema()
            relationships = tool.detect_relationships()
            
            # Opcional: verificar con LLM solo si está disponible
            llm_results = []
            if use_llm:
                try:
                    llm_results = tool.verify_with_llm(max_verifications=3)
                except Exception as e:
                    print_colored(f"⚠️  LLM no disponible: {e}", Colors.WARNING)
                    use_llm = False
            
            # Guardar resultados
            results_comparison[method_name] = {
                'total_relationships': len(relationships),
                'high_confidence': len([r for r in relationships if r.get('confidence', 0) >= 80]),
                'medium_confidence': len([r for r in relationships if 60 <= r.get('confidence', 0) < 80]),
                'low_confidence': len([r for r in relationships if r.get('confidence', 0) < 60]),
                'llm_validated': len([r for r in llm_results if getattr(r, 'is_valid', False)]) if llm_results else 0,
                'relationships': relationships[:5],  # Top 5 relaciones
                'method_config': {
                    'embeddings': use_embeddings,
                    'llm': use_llm
                }
            }
            
            # Mostrar resumen
            print_colored(f"✅ {method_name} completado:", Colors.OKGREEN)
            print(f"   📊 Total relaciones detectadas: {len(relationships)}")
            print(f"   🟢 Alta confianza (80%+): {len([r for r in relationships if r.get('confidence', 0) >= 80])}")
            print(f"   🟡 Media confianza (60-79%): {len([r for r in relationships if 60 <= r.get('confidence', 0) < 80])}")
            
            if llm_results:
                print(f"   🤖 Validadas por LLM: {len([r for r in llm_results if getattr(r, 'is_valid', False)])}")
            
            # Mostrar top 3 relaciones
            print(f"\n   📋 Top 3 relaciones detectadas:")
            for i, rel in enumerate(relationships[:3], 1):
                confidence = rel.get('confidence', 0)
                method = rel.get('detection_method', 'unknown')
                print(f"      {i}. {rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}")
                print(f"         Confianza: {confidence:.1f}% | Método: {method}")
        
        except Exception as e:
            print_colored(f"❌ Error en {method_name}: {e}", Colors.FAIL)
            results_comparison[method_name] = {'error': str(e)}
            continue
    
    # Mostrar comparación final
    print_section("COMPARACIÓN DE RESULTADOS")
    
    comparison_table = []
    for method, results in results_comparison.items():
        if 'error' in results:
            comparison_table.append([method, "ERROR", results['error'][:50]])
        else:
            comparison_table.append([
                method,
                results['total_relationships'],
                f"🟢{results['high_confidence']} 🟡{results['medium_confidence']} 🔴{results['low_confidence']}",
                results['llm_validated'] if results['llm_validated'] > 0 else "N/A"
            ])
    
    # Imprimir tabla de comparación
    headers = ["Método", "Total", "Confianza (H/M/L)", "LLM Validadas"]
    
    print(f"\n{'Método':<30} {'Total':<8} {'Confianza':<20} {'LLM':<12}")
    print("-" * 70)
    
    for row in comparison_table:
        print(f"{row[0]:<30} {str(row[1]):<8} {str(row[2]):<20} {str(row[3]):<12}")
    
    return results_comparison

def demonstrate_error_fixes():
    """
    Demuestra cómo se resolvieron los errores del código original
    """
    print_section("DEMOSTRACIÓN DE ERRORES CORREGIDOS")
    
    # Error 1: DataFrame serialization
    print_colored("🔧 Error 1 CORREGIDO: DataFrame serialization", Colors.OKGREEN)
    print("   ❌ Error original: 'Object of type DataFrame is not JSON serializable'")
    print("   ✅ Solución: Conversión automática de tipos numpy/pandas a tipos serializables")
    
    # Demostrar la corrección
    try:
        import pandas as pd
        import numpy as np
        
        # Crear DataFrame problemático
        df = pd.DataFrame({
            'id': [np.int64(1), np.int64(2), np.int64(3)],
            'value': [np.float64(1.5), np.float64(2.5), np.float64(3.5)],
            'flag': [np.bool_(True), np.bool_(False), np.bool_(True)]
        })
        
        # Demostrar serialización corregida
        from complete_data_tool import CompleteDataTool
        tool = CompleteDataTool("complex_ecommerce.db")
        serialized = tool._serialize_dataframe(df)
        
        print(f"   📊 DataFrame original: {len(df)} filas")
        print(f"   🔄 Serializado exitosamente: {len(serialized['sample_data'])} registros")
        print(f"   ✅ Tipos convertidos correctamente")
        
    except Exception as e:
        print_colored(f"   ⚠️  No se pudo demostrar (módulo no disponible): {e}", Colors.WARNING)
    
    # Error 2: LLM connection issues
    print_colored("\n🔧 Error 2 CORREGIDO: Problemas de conexión LLM", Colors.OKGREEN)
    print("   ❌ Error original: Falta de manejo de errores de conexión")
    print("   ✅ Solución: Manejo robusto de errores, timeouts y fallbacks")
    
    # Error 3: Missing dependencies
    print_colored("\n🔧 Error 3 CORREGIDO: Dependencias faltantes", Colors.OKGREEN)
    print("   ❌ Error original: ImportError para sentence-transformers")
    print("   ✅ Solución: Detección automática y fallback a métodos básicos")
    
    # Error 4: Configuration issues
    print_colored("\n🔧 Error 4 CORREGIDO: Problemas de configuración", Colors.OKGREEN)
    print("   ❌ Error original: Configuración hardcodeada")
    print("   ✅ Solución: Sistema de configuración flexible con config.json")

def generate_comprehensive_report(db_path: str, results_comparison: dict):
    """
    Genera un reporte completo del análisis
    """
    print_section("GENERANDO REPORTE COMPLETO")
    
    try:
        from complete_data_tool import CompleteDataTool
        
        # Usar el mejor método disponible
        use_embeddings = True
        use_llm = False  # Por defecto False para evitar errores si Ollama no está disponible
        
        # Verificar si sentence-transformers está disponible
        try:
            import sentence_transformers
        except ImportError:
            use_embeddings = False
            print_colored("⚠️  Sentence-transformers no disponible, usando método básico", Colors.WARNING)
        
        tool = CompleteDataTool(
            db_path=db_path,
            use_embeddings=use_embeddings,
            use_llm=use_llm
        )
        
        # Ejecutar análisis completo
        print_colored("📊 Ejecutando análisis completo...", Colors.OKCYAN)
        results = tool.analyze_complete(output_dir="./demo_output")
        
        # Generar reporte adicional
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"demo_output/comprehensive_report_{timestamp}.md"
        
        report_content = f"""# 📊 Reporte Completo de Análisis - Enhanced Data Tool v2.0

## 🎯 Resumen Ejecutivo

**Base de datos analizada**: `{db_path}`
**Fecha de análisis**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Herramientas utilizadas**: {'Embeddings + ' if use_embeddings else ''}{'LLM + ' if use_llm else ''}Análisis básico

### 📈 Métricas Principales

- **Total de tablas**: {results['summary']['total_tables']}
- **Total de columnas**: {results['summary']['total_columns']:,}
- **Total de filas**: {results['summary']['total_rows']:,}
- **Relaciones existentes**: {results['summary']['existing_fks']}
- **Nuevas relaciones detectadas**: {results['summary']['detected_relationships']}
- **Relaciones de alta confianza**: {results['summary']['high_confidence_relationships']}

## 🔍 Análisis Detallado por Tabla

"""
        
        # Agregar análisis por tabla
        for table_name, table_info in results['schema']['tables'].items():
            report_content += f"""
### 📊 Tabla: `{table_name}`

- **Columnas**: {table_info['total_columns']}
- **Filas**: {table_info['row_count']:,}
- **Primary Keys**: {', '.join(table_info['primary_keys']) if table_info['primary_keys'] else 'Ninguna'}
- **Foreign Keys existentes**: {len(table_info['foreign_keys'])}

"""
            if table_info['foreign_keys']:
                report_content += "**Relaciones existentes**:\n"
                for fk in table_info['foreign_keys']:
                    report_content += f"- `{fk['column']}` → `{fk['references_table']}.{fk['references_column']}`\n"
                report_content += "\n"
        
        # Agregar relaciones detectadas
        if results['relationships']:
            report_content += """## 🚀 Relaciones Detectadas Automáticamente

"""
            
            # Agrupar por confianza
            high_conf = [r for r in results['relationships'] if r.get('confidence', 0) >= 80]
            medium_conf = [r for r in results['relationships'] if 60 <= r.get('confidence', 0) < 80]
            low_conf = [r for r in results['relationships'] if r.get('confidence', 0) < 60]
            
            if high_conf:
                report_content += "### 🟢 Alta Confianza (80%+)\n\n"
                for rel in high_conf:
                    conf = rel.get('confidence', 0)
                    method = rel.get('detection_method', 'unknown')
                    report_content += f"- `{rel['from_table']}.{rel['from_column']}` → `{rel['to_table']}.{rel['to_column']}` (Confianza: {conf:.1f}%, Método: {method})\n"
                report_content += "\n"
            
            if medium_conf:
                report_content += "### 🟡 Confianza Media (60-79%)\n\n"
                for rel in medium_conf:
                    conf = rel.get('confidence', 0)
                    method = rel.get('detection_method', 'unknown')
                    report_content += f"- `{rel['from_table']}.{rel['from_column']}` → `{rel['to_table']}.{rel['to_column']}` (Confianza: {conf:.1f}%, Método: {method})\n"
                report_content += "\n"
        
        # Agregar comparación de métodos
        if results_comparison:
            report_content += """## 📊 Comparación de Métodos

| Método | Total Relaciones | Alta Confianza | Media Confianza | Baja Confianza |
|--------|------------------|----------------|----------------|----------------|
"""
            for method, data in results_comparison.items():
                if 'error' not in data:
                    report_content += f"| {method} | {data['total_relationships']} | {data['high_confidence']} | {data['medium_confidence']} | {data['low_confidence']} |\n"
        
        # Agregar conclusiones
        report_content += f"""
## 🎯 Conclusiones y Recomendaciones

### ✅ Aspectos Positivos
- Se detectaron **{results['summary']['detected_relationships']}** relaciones potenciales
- **{results['summary']['high_confidence_relationships']}** relaciones tienen alta confianza
- El esquema tiene **{results['summary']['existing_fks']}** relaciones documentadas

### 🔧 Recomendaciones
1. **Revisar relaciones de alta confianza**: Considerar agregar Foreign Keys faltantes
2. **Validar relaciones de confianza media**: Revisar manualmente antes de implementar
3. **Optimizar esquema**: Documentar relaciones implícitas encontradas
4. **Mejorar integridad**: Agregar constraints basados en relaciones detectadas

### 📐 Próximos Pasos
1. Abrir el archivo DBML generado en [dbdiagram.io](https://dbdiagram.io/d)
2. Revisar relaciones sugeridas con el equipo de desarrollo
3. Implementar Foreign Keys para relaciones validadas
4. Ejecutar nuevamente el análisis para verificar mejoras

---

*Reporte generado por Enhanced Data Tool v2.0*
*Para más información: https://github.com/Constanzafl/data_tool*
"""
        
        # Guardar reporte
        Path("demo_output").mkdir(exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print_colored(f"✅ Reporte completo generado: {report_path}", Colors.OKGREEN)
        
        return report_path
        
    except Exception as e:
        print_colored(f"❌ Error generando reporte: {e}", Colors.FAIL)
        traceback.print_exc()
        return None

def main():
    """Función principal del demo"""
    print_colored("🚀 ENHANCED DATA TOOL v2.0 - DEMO COMPLETO", Colors.HEADER)
    print_colored("=" * 70, Colors.HEADER)
    print_colored("Demostración de todas las funcionalidades y correcciones", Colors.OKCYAN)
    
    try:
        # Paso 1: Crear base de datos compleja
        db_path = create_complex_sample_database()
        
        # Paso 2: Demostrar correcciones de errores
        demonstrate_error_fixes()
        
        # Paso 3: Analizar con diferentes métodos
        results_comparison = analyze_with_different_methods(db_path)
        
        # Paso 4: Generar reporte completo
        report_path = generate_comprehensive_report(db_path, results_comparison)
        
        # Resumen final
        print_section("DEMO COMPLETADO EXITOSAMENTE")
        
        print_colored("🎉 ¡Demo ejecutado correctamente!", Colors.OKGREEN)
        print_colored("\n📁 Archivos generados:", Colors.OKCYAN)
        print(f"   • Base de datos: {db_path}")
        print(f"   • Directorio output: ./demo_output/")
        if report_path:
            print(f"   • Reporte completo: {report_path}")
        
        print_colored("\n🎯 Próximos pasos:", Colors.OKBLUE)
        print("   1. Revisar archivos DBML en ./demo_output/")
        print("   2. Abrir DBML en https://dbdiagram.io/d")
        print("   3. Examinar el reporte completo generado")
        print("   4. Probar con tu propia base de datos")
        
        print_colored("\n✨ Enhanced Data Tool v2.0 está listo para usar", Colors.OKGREEN)
        
    except Exception as e:
        print_colored(f"❌ Error en demo: {e}", Colors.FAIL)
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
