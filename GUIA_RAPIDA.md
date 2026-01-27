# Guía Rápida de Uso

## 🚀 Inicio Rápido

### 1. Configurar el Entorno

```bash
# Clonar o navegar al proyecto
cd "c:\Users\luigg\Desktop\sistema correlativo"

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (Windows)
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

Copiar `.env.example` a `.env` y configurar las credenciales de Supabase:

```bash
copy .env.example .env
```

Editar `.env` con tus credenciales:

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-clave-anon-publica
SUPABASE_SERVICE_KEY=tu-clave-service-role
SECRET_KEY=genera-una-clave-secreta-segura
```

### 3. Ejecutar Migración SQL en Supabase

1. Ir a [Supabase Dashboard](https://app.supabase.com)
2. Abrir **SQL Editor**
3. Copiar y ejecutar el contenido de `migrations/001_create_quotes_table.sql`

### 4. Ejecutar la Aplicación

```bash
# Modo desarrollo (con hot-reload)
uvicorn src.main:app --reload

# O usando Python directamente
python -m src.main
```

La API estará disponible en: **http://localhost:8000**

### 5. Probar la API

Abrir la documentación interactiva:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐳 Usando Docker

### Opción 1: Solo la aplicación

```bash
# Construir imagen
docker build -t sistema-correlativo .

# Ejecutar contenedor
docker run -p 8000:8000 --env-file .env sistema-correlativo
```

### Opción 2: Con Docker Compose (incluye PostgreSQL local)

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down
```

## 📝 Ejemplos de Uso de la API

### Crear una Cotización

```bash
curl -X POST "http://localhost:8000/api/v1/quotes" \
  -H "Content-Type: application/json" \
  -d '{
    "client_phone": "+58 412-1234567",
    "items": [
      {
        "product_name": "Laptop Dell XPS 15",
        "quantity": 1,
        "unit_price": 1200.00,
        "subtotal": 1200.00,
        "description": "Laptop de alto rendimiento"
      }
    ],
    "total": 1200.00,
    "status": "draft",
    "notes": "Cliente VIP"
  }'
```

### Obtener una Cotización

```bash
curl -X GET "http://localhost:8000/api/v1/quotes/1"
```

### Listar Cotizaciones

```bash
# Todas las cotizaciones
curl -X GET "http://localhost:8000/api/v1/quotes"

# Con paginación
curl -X GET "http://localhost:8000/api/v1/quotes?skip=0&limit=10"

# Filtrar por estado
curl -X GET "http://localhost:8000/api/v1/quotes?status=pending"
```

### Actualizar una Cotización

```bash
curl -X PUT "http://localhost:8000/api/v1/quotes/1" \
  -H "Content-Type: application/json" \
  -d '{
    "client_phone": "+58 412-1234567",
    "items": [
      {
        "product_name": "Laptop Dell XPS 15",
        "quantity": 2,
        "unit_price": 1200.00,
        "subtotal": 2400.00
      }
    ],
    "total": 2400.00,
    "status": "approved"
  }'
```

### Eliminar una Cotización

```bash
curl -X DELETE "http://localhost:8000/api/v1/quotes/1"
```

### Obtener Cotizaciones por Teléfono

```bash
curl -X GET "http://localhost:8000/api/v1/quotes/phone/+58%20412-1234567"
```

## 🧪 Ejecutar Tests

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=src

# Tests específicos
pytest tests/test_quote_entity.py

# Con verbose
pytest -v
```

## 📁 Estructura del Proyecto

```
sistema-correlativo/
├── src/
│   ├── domain/              # Lógica de negocio
│   │   ├── entities/        # Entidades (Quote, QuoteItem)
│   │   └── repositories/    # Interfaces (Puertos)
│   ├── application/         # Casos de uso
│   │   └── use_cases/       # Lógica de aplicación
│   ├── infrastructure/      # Adaptadores
│   │   ├── database/        # Supabase adapter
│   │   ├── api/             # REST API (FastAPI)
│   │   └── config/          # Configuración
│   └── main.py             # Punto de entrada
├── migrations/             # Scripts SQL
├── tests/                  # Tests unitarios
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

## 🔑 Características Principales

✅ **Arquitectura Hexagonal** - Separación clara de capas  
✅ **Validación Estricta** - Pydantic con validación de tipos  
✅ **ID Autoincremental** - Correlativo generado por PostgreSQL  
✅ **API REST Completa** - CRUD completo para cotizaciones  
✅ **Documentación Automática** - Swagger UI y ReDoc  
✅ **Docker Ready** - Containerización lista para producción  
✅ **Tests Incluidos** - Tests unitarios con pytest  
✅ **Supabase Integration** - Backend as a Service

## 🛠️ Solución de Problemas

### Error: "ModuleNotFoundError"
```bash
# Asegurarse de que el entorno virtual está activado
venv\Scripts\activate

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error: "Connection refused" a Supabase
- Verificar que las credenciales en `.env` son correctas
- Verificar que el proyecto de Supabase está activo
- Verificar la conexión a internet

### Error: "Table 'quotes' does not exist"
- Ejecutar el script SQL en Supabase: `migrations/001_create_quotes_table.sql`

## 📚 Recursos Adicionales

- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de Pydantic](https://docs.pydantic.dev/)
- [Documentación de Supabase](https://supabase.com/docs)
- [Arquitectura Hexagonal](https://alistair.cockburn.us/hexagonal-architecture/)
