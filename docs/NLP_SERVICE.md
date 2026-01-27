# Servicio de Generación de Cotizaciones con NLP

## 🎯 Descripción

Este servicio permite generar cotizaciones automáticamente desde **texto libre** usando NLP ligero (costo cero). El usuario puede escribir algo como _"Quiero 2 zapatos y 1 camisa"_ y el sistema generará una cotización completa con precios y totales calculados exactamente.

## 🧠 Tecnología NLP

### Librería Usada: `thefuzz`

- **Fuzzy matching** para tolerancia a typos
- **Costo cero** (librería open source)
- **Rápido y eficiente**
- **No requiere modelos de ML pesados**

### Componentes

1. **TextParser** (`src/domain/services/text_parser.py`)
   - Extrae productos y cantidades del texto
   - Usa regex para detectar patrones
   - Fuzzy matching para mapear a productos del catálogo
   - Normalización de texto (acentos, mayúsculas)

2. **QuoteService** (`src/domain/services/quote_service.py`)
   - Orquesta el proceso de generación
   - Cálculos precisos con `Decimal` (sin errores de punto flotante)
   - Validación de datos con Pydantic

3. **Catálogo de Productos** (`data/products_catalog.json`)
   - 10 productos de ejemplo
   - Cada producto tiene aliases para mejor matching
   - Precios y categorías

## 📝 Ejemplos de Uso

### Texto Simple

```
Input: "Quiero 2 zapatos"
Output: Cotización con 2 zapatos @ $45.99 = $91.98
```

### Texto Complejo

```
Input: "necesito 3 camisas, 2 pantalones y 5 gorras"
Output: Cotización con:
  - 3 camisas @ $25.50 = $76.50
  - 2 pantalones @ $35.00 = $70.00
  - 5 gorras @ $15.00 = $75.00
  Total: $221.50
```

### Con Números en Palabras

```
Input: "dame dos zapatos y una camisa"
Output: Cotización con 2 zapatos y 1 camisa
```

### Con Typos (Fuzzy Matching)

```
Input: "Quiero 2 sapatos"  (typo: sapatos → zapatos)
Output: Cotización con 2 zapatos @ $45.99 = $91.98
```

## 🔧 API Endpoints

### 1. Generar Cotización desde Texto

**POST** `/api/v1/generate/quote-from-text`

```json
{
  "text": "Quiero 2 zapatos y 1 camisa",
  "client_phone": "+58 412-1234567",
  "fuzzy_threshold": 70,
  "status": "draft",
  "notes": "Cliente VIP"
}
```

**Respuesta:**

```json
{
  "quote": {
    "id": null,
    "client_phone": "+58 412-1234567",
    "items": [
      {
        "product_name": "Zapatos",
        "quantity": 2,
        "unit_price": 45.99,
        "subtotal": 91.98,
        "description": "Categoría: calzado"
      },
      {
        "product_name": "Camisa",
        "quantity": 1,
        "unit_price": 25.50,
        "subtotal": 25.50,
        "description": "Categoría: ropa"
      }
    ],
    "total": 117.48,
    "status": "draft",
    "notes": "Cliente VIP"
  },
  "parsing_details": [
    {
      "product": "Zapatos",
      "matched_text": "zapatos",
      "matched_to": "zapato",
      "confidence": 95
    },
    {
      "product": "Camisa",
      "matched_text": "camisa",
      "matched_to": "camisa",
      "confidence": 100
    }
  ]
}
```

### 2. Listar Productos Disponibles

**GET** `/api/v1/generate/products`

### 3. Buscar Producto

**POST** `/api/v1/generate/search-product`

```json
{
  "query": "zapatos",
  "threshold": 70
}
```

## ✅ Tests

### Cobertura: 41 Tests (100% PASSED)

#### Tests de Cálculos Matemáticos (26 tests)

- ✅ Cálculo exacto con un solo item
- ✅ Cálculo exacto con múltiples items
- ✅ Cálculo complejo con múltiples cantidades
- ✅ Precisión decimal sin errores de redondeo
- ✅ Cantidades grandes
- ✅ Total = suma de subtotales (siempre)
- ✅ Sin errores de punto flotante

#### Tests de Parsing (8 tests)

- ✅ Parsear texto con números
- ✅ Parsear texto con palabras (dos, tres, etc.)
- ✅ Case-insensitive
- ✅ Manejo de acentos
- ✅ Fuzzy matching con typos
- ✅ Reconocimiento de aliases

#### Tests de Validación (7 tests)

- ✅ Texto vacío lanza error
- ✅ Texto sin productos lanza error
- ✅ Teléfono inválido lanza error
- ✅ Validación de formato de teléfono

### Ejecutar Tests

```bash
# Todos los tests
python -m pytest tests/ -v

# Solo QuoteService
python -m pytest tests/test_quote_service.py -v

# Solo TextParser
python -m pytest tests/test_text_parser.py -v

# Con cobertura
python -m pytest tests/ --cov=src
```

## 🎨 Arquitectura

```
┌─────────────────────────────────────────┐
│         API REST (FastAPI)              │
│  POST /generate/quote-from-text         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         QuoteService                    │
│  - generate_quote_from_text()           │
│  - Cálculos con Decimal                 │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         TextParser (NLP)                │
│  - Regex para extraer cantidades        │
│  - Fuzzy matching (thefuzz)             │
│  - Normalización de texto               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    Catálogo de Productos (JSON)         │
│  - 10 productos con precios             │
│  - Aliases para mejor matching          │
└─────────────────────────────────────────┘
```

## 🔢 Precisión Matemática

### Problema de Punto Flotante

```python
# ❌ Problema común con float
0.1 + 0.2 == 0.3  # False! (0.30000000000000004)
```

### Solución: Decimal

```python
# ✅ Nuestra solución con Decimal
from decimal import Decimal
Decimal('0.1') + Decimal('0.2') == Decimal('0.3')  # True!
```

### Implementación

```python
def _calculate_precise_decimal(self, value: float) -> Decimal:
    """Calcular valor decimal preciso."""
    return Decimal(str(value)).quantize(
        Decimal('0.01'), 
        rounding=ROUND_HALF_UP
    )
```

## 📊 Catálogo de Productos

Ubicación: `data/products_catalog.json`

### Estructura

```json
{
  "products": [
    {
      "id": 1,
      "name": "Zapatos",
      "aliases": ["zapato", "calzado", "shoes", "tenis"],
      "price": 45.99,
      "category": "calzado"
    }
  ]
}
```

### Productos Disponibles

1. **Zapatos** - $45.99
2. **Camisa** - $25.50
3. **Pantalón** - $35.00
4. **Chaqueta** - $55.00
5. **Gorra** - $15.00
6. **Bolso** - $40.00
7. **Cinturón** - $20.00
8. **Medias** - $8.00
9. **Vestido** - $48.00
10. **Corbata** - $18.00

## 🚀 Uso Programático

### Python

```python
from src.domain.services import QuoteService

# Inicializar servicio
service = QuoteService()

# Generar cotización
quote = service.generate_quote_from_text(
    text="Quiero 2 zapatos y 1 camisa",
    client_phone="+58 412-1234567"
)

print(f"Total: ${quote.total}")
# Output: Total: $117.48
```

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/generate/quote-from-text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Quiero 2 zapatos y 1 camisa",
    "client_phone": "+58 412-1234567"
  }'
```

## 🎯 Próximas Mejoras

1. **Integración con Base de Datos**
   - Cargar productos desde Supabase
   - Actualizar precios dinámicamente

2. **NLP Avanzado**
   - Soporte para más idiomas
   - Detección de intención (compra vs consulta)
   - Manejo de descuentos ("10% de descuento")

3. **Validaciones Adicionales**
   - Stock disponible
   - Límites de cantidad
   - Precios especiales por cliente

4. **Mejoras de UX**
   - Sugerencias de productos similares
   - Corrección automática de typos
   - Confirmación antes de generar
