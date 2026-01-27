# Frontend React - Guía de Uso

## 🚀 Inicio Rápido

### Instalación

```bash
cd frontend
npm install
```

### Ejecutar en Desarrollo

```bash
# Terminal 1: Backend
cd c:\Users\luigg\Desktop\sistema correlativo
python -m uvicorn src.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Abrir en el navegador: `http://localhost:5173`

---

## 📋 Funcionalidades

### 1. Tabla de Cotizaciones

- **Visualización**: Muestra todas las cotizaciones ordenadas por número correlativo (ID descendente)
- **Columnas**: ID, Cliente, Teléfono, Total, Estado, Fecha
- **Selección**: Checkbox para seleccionar clientes
- **Responsive**: Adaptable a móviles y tablets

### 2. Lista de Difusión

- **Botón**: "Crear Lista de Difusión" (solo activo con clientes seleccionados)
- **Modal**: Formulario para configurar el mensaje
- **Templates**: Selección de plantillas aprobadas por Meta
- **Parámetros**: Campos dinámicos para variables del template
- **Envío**: Broadcast a todos los clientes seleccionados

### 3. Resultados del Envío

- **Feedback visual**: Indicador de éxito/error por cliente
- **Detalles**: Message ID o error específico
- **Estados**: Loading, Success, Error

---

## 🎨 Componentes

### App.jsx

Componente principal que gestiona:
- Estado global de cotizaciones
- Clientes seleccionados
- Modal de broadcast
- Carga y actualización de datos

### QuotesTable.jsx

Tabla de cotizaciones con:
- Ordenamiento por ID
- Selección múltiple
- Formateo de moneda y fechas
- Badges de estado

### BroadcastListModal.jsx

Modal para envío masivo con:
- Lista de clientes seleccionados
- Configuración de template
- Parámetros dinámicos
- Resultados del envío

---

## 🔌 API Endpoints Usados

### GET /api/v1/quotes

Obtiene todas las cotizaciones

**Respuesta**:
```json
[
  {
    "id": 1,
    "client_phone": "+58 412-1234567",
    "items": [...],
    "total": 117.48,
    "status": "draft",
    "created_at": "2024-01-27T10:00:00Z"
  }
]
```

### POST /api/v1/broadcast/send-template

Envía template a múltiples clientes

**Request**:
```json
{
  "clients": [
    {"phone": "+58 412-1234567", "name": "Cliente 1", "quote_id": 1}
  ],
  "template_name": "hello_world",
  "language_code": "es",
  "parameters": []
}
```

**Respuesta**:
```json
{
  "status": "completed",
  "total_clients": 1,
  "successful": 1,
  "failed": 0,
  "results": [
    {
      "phone": "+58 412-1234567",
      "success": true,
      "message_id": "wamid.xxx"
    }
  ]
}
```

---

## 🎯 Templates Disponibles

### 1. hello_world

Template simple sin parámetros

**Uso**:
- Template: `hello_world`
- Idioma: `es`
- Parámetros: ninguno

### 2. quote_notification

Notificación de cotización generada

**Uso**:
- Template: `quote_notification`
- Idioma: `es`
- Parámetros: `nombre_cliente, total`

**Ejemplo**: `Juan Pérez, $117.48`

### 3. payment_reminder

Recordatorio de pago pendiente

**Uso**:
- Template: `payment_reminder`
- Idioma: `es`
- Parámetros: `nombre_cliente, monto, fecha_vencimiento`

**Ejemplo**: `María García, $250.00, 31/01/2024`

---

## 🛠️ Configuración

### Proxy de API

El frontend está configurado para hacer proxy de `/api` al backend en `http://localhost:8000`.

**Archivo**: `vite.config.js`

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

### Tailwind CSS

Tema personalizado con colores primary (verde).

**Archivo**: `tailwind.config.js`

---

## 🐛 Solución de Problemas

### Error: "Error al cargar las cotizaciones"

**Causa**: Backend no está corriendo

**Solución**:
```bash
cd c:\Users\luigg\Desktop\sistema correlativo
python -m uvicorn src.main:app --reload --port 8000
```

### Error: "Cannot find module"

**Causa**: Dependencias no instaladas

**Solución**:
```bash
cd frontend
npm install
```

### Error: Scripts deshabilitados en PowerShell

**Causa**: Política de ejecución de PowerShell

**Solución**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

O ejecutar con:
```bash
npx vite
```

---

## 📦 Build para Producción

```bash
cd frontend
npm run build
```

Los archivos se generarán en `frontend/dist/`

### Servir Build

```bash
npm run preview
```

---

## 🌐 Despliegue en Producción

### Vercel (Recomendado)

Ver [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md) para instrucciones completas.

**Inicio rápido**:

1. **Conectar repositorio** en [Vercel](https://vercel.com)
2. **Root Directory**: `frontend`
3. **Variable de entorno**:
   - `VITE_API_URL` = `https://tu-backend.onrender.com/api/v1`
4. **Deploy** ✅

### Variables de Entorno

**Desarrollo** (`.env`):
```bash
VITE_API_URL=http://localhost:8000/api/v1
```

**Producción** (Vercel):
```bash
VITE_API_URL=https://tu-backend.onrender.com/api/v1
```

---

## 🎨 Personalización

### Cambiar Colores

Editar `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        500: '#tu-color',
        600: '#tu-color-oscuro',
        // ...
      }
    }
  }
}
```

### Agregar Nuevo Template

1. Editar `BroadcastListModal.jsx`:

```jsx
<option value="mi_template">Mi Template</option>
```

2. Crear template en Meta Business Manager

3. Actualizar backend en `broadcast_routes.py`

---

## 📱 Responsive Design

El frontend está optimizado para:
- ✅ Desktop (1920px+)
- ✅ Laptop (1366px+)
- ✅ Tablet (768px+)
- ✅ Mobile (320px+)

---

## 🔐 Seguridad

- ✅ CORS configurado en backend
- ✅ Validación de datos con Pydantic
- ✅ Sanitización de números de teléfono
- ✅ Manejo de errores robusto

---

## 📊 Estados de Cotización

| Estado | Color | Descripción |
|--------|-------|-------------|
| draft | Gris | Borrador |
| sent | Azul | Enviado |
| approved | Verde | Aprobado |
| rejected | Rojo | Rechazado |

---

## 🚀 Próximas Mejoras

1. **Filtros**: Filtrar por estado, fecha, cliente
2. **Búsqueda**: Buscar por teléfono o ID
3. **Paginación**: Paginar tabla de cotizaciones
4. **Exportar**: Exportar a Excel/PDF
5. **Historial**: Ver historial de mensajes enviados
6. **Templates dinámicos**: Crear templates desde UI
7. **Programar envíos**: Agendar mensajes para después
8. **Estadísticas**: Dashboard con métricas
