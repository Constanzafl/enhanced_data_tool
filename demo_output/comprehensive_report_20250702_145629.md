# 📊 Reporte Completo de Análisis - Enhanced Data Tool v2.0

## 🎯 Resumen Ejecutivo

**Base de datos analizada**: `complex_ecommerce.db`
**Fecha de análisis**: 2025-07-02 14:56:29
**Herramientas utilizadas**: Embeddings + Análisis básico

### 📈 Métricas Principales

- **Total de tablas**: 15
- **Total de columnas**: 129
- **Total de filas**: 78
- **Relaciones existentes**: 0
- **Nuevas relaciones detectadas**: 389
- **Relaciones de alta confianza**: 0

## 🔍 Análisis Detallado por Tabla


### 📊 Tabla: `users`

- **Columnas**: 7
- **Filas**: 5
- **Primary Keys**: user_id
- **Foreign Keys existentes**: 0


### 📊 Tabla: `user_profiles`

- **Columnas**: 7
- **Filas**: 5
- **Primary Keys**: profile_id
- **Foreign Keys existentes**: 0


### 📊 Tabla: `addresses`

- **Columnas**: 9
- **Filas**: 5
- **Primary Keys**: address_id
- **Foreign Keys existentes**: 0


### 📊 Tabla: `product_categories`

- **Columnas**: 5
- **Filas**: 10
- **Primary Keys**: category_id
- **Foreign Keys existentes**: 0


### 📊 Tabla: `brands`

- **Columnas**: 5
- **Filas**: 5
- **Primary Keys**: brand_id
- **Foreign Keys existentes**: 0


### 📊 Tabla: `products`

- **Columnas**: 14
- **Filas**: 7
- **Primary Keys**: product_id
- **Foreign Keys existentes**: 0


### 📊 Tabla: `inventory_movements`

- **Columnas**: 7
- **Filas**: 7
- **Primary Keys**: movement_id
- **Foreign Keys existentes**: 0


### 📊 Tabla: `shopping_carts`

- **Columnas**: 6
- **Filas**: 3
- **Primary Keys**: cart_id
- **Foreign Keys existentes**: 0


### 📊 Tabla: `cart_items`

- **Columnas**: 6
- **Filas**: 5
- **Primary Keys**: item_id
- **Foreign Keys existentes**: 0


### 📊 Tabla: `orders`

- **Columnas**: 17
- **Filas**: 5
- **Primary Keys**: order_id
- **Foreign Keys existentes**: 0


### 📊 Tabla: `order_items`

- **Columnas**: 7
- **Filas**: 7
- **Primary Keys**: order_item_id
- **Foreign Keys existentes**: 0


### 📊 Tabla: `payments`

- **Columnas**: 10
- **Filas**: 4
- **Primary Keys**: payment_id
- **Foreign Keys existentes**: 0


### 📊 Tabla: `product_reviews`

- **Columnas**: 11
- **Filas**: 4
- **Primary Keys**: review_id
- **Foreign Keys existentes**: 0


### 📊 Tabla: `discount_coupons`

- **Columnas**: 12
- **Filas**: 3
- **Primary Keys**: coupon_id
- **Foreign Keys existentes**: 0


### 📊 Tabla: `coupon_usage`

- **Columnas**: 6
- **Filas**: 3
- **Primary Keys**: usage_id
- **Foreign Keys existentes**: 0

## 🚀 Relaciones Detectadas Automáticamente

### 🟡 Confianza Media (60-79%)

- `products.brand_reference` → `brands.brand_id` (Confianza: 76.3%, Método: embeddings)
- `order_items.order_ref` → `orders.order_id` (Confianza: 72.9%, Método: embeddings)
- `user_profiles.user_ref` → `users.user_id` (Confianza: 72.6%, Método: embeddings)
- `product_reviews.product_reference` → `products.product_id` (Confianza: 71.9%, Método: embeddings)
- `order_items.product_reference` → `products.product_id` (Confianza: 71.8%, Método: embeddings)
- `cart_items.product_ref` → `products.product_id` (Confianza: 71.7%, Método: embeddings)
- `addresses.user_reference` → `users.user_id` (Confianza: 71.4%, Método: embeddings)
- `shopping_carts.user_identifier` → `users.user_id` (Confianza: 71.1%, Método: embeddings)
- `coupon_usage.user_identifier` → `users.user_id` (Confianza: 70.9%, Método: embeddings)
- `product_reviews.order_item_reference` → `order_items.order_item_id` (Confianza: 70.4%, Método: embeddings)
- `payments.order_reference` → `orders.order_id` (Confianza: 69.8%, Método: embeddings)
- `orders.billing_address_id` → `addresses.address_id` (Confianza: 69.5%, Método: embeddings)
- `coupon_usage.order_ref` → `orders.order_id` (Confianza: 69.0%, Método: embeddings)
- `inventory_movements.product_reference` → `products.product_id` (Confianza: 69.0%, Método: embeddings)
- `product_reviews.user_ref` → `users.user_id` (Confianza: 66.4%, Método: embeddings)
- `product_reviews.order_item_reference` → `orders.order_id` (Confianza: 65.7%, Método: embeddings)
- `orders.customer_id` → `order_items.order_item_id` (Confianza: 65.6%, Método: embeddings)
- `orders.billing_address_id` → `payments.payment_id` (Confianza: 64.9%, Método: embeddings)
- `orders.customer_id` → `users.user_id` (Confianza: 64.6%, Método: embeddings)
- `orders.customer_id` → `payments.payment_id` (Confianza: 64.5%, Método: embeddings)
- `orders.customer_id` → `addresses.address_id` (Confianza: 63.3%, Método: embeddings)
- `orders.billing_address_id` → `order_items.order_item_id` (Confianza: 63.1%, Método: embeddings)
- `orders.customer_id` → `brands.brand_id` (Confianza: 63.0%, Método: embeddings)
- `orders.customer_id` → `shopping_carts.cart_id` (Confianza: 62.5%, Método: embeddings)
- `orders.customer_id` → `cart_items.item_id` (Confianza: 61.6%, Método: embeddings)
- `orders.billing_address_id` → `shopping_carts.cart_id` (Confianza: 60.5%, Método: embeddings)

## 📊 Comparación de Métodos

| Método | Total Relaciones | Alta Confianza | Media Confianza | Baja Confianza |
|--------|------------------|----------------|----------------|----------------|
| Básico (Solo patrones) | 28 | 0 | 28 | 0 |
| Con Embeddings | 389 | 0 | 26 | 363 |
| Completo (Embeddings + LLM) | 389 | 0 | 26 | 363 |

## 🎯 Conclusiones y Recomendaciones

### ✅ Aspectos Positivos
- Se detectaron **389** relaciones potenciales
- **0** relaciones tienen alta confianza
- El esquema tiene **0** relaciones documentadas

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
