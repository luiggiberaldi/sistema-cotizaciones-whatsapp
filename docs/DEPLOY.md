# Guía de Despliegue en Render

## 🚀 Despliegue Automático con render.yaml

Este proyecto está configurado para despliegue automático en [Render](https://render.com) usando **Infraestructura como Código (IaC)**.

---

## 📋 Pre-requisitos

1. **Cuenta en Render**: [Crear cuenta gratuita](https://dashboard.render.com/register)
2. **Repositorio Git**: Código en GitHub, GitLab o Bitbucket
3. **Credenciales de servicios externos**:
   - Supabase (base de datos)
   - WhatsApp Cloud API (Meta)

---

## 🔧 Configuración Inicial

### 1. Conectar Repositorio

1. Ir a [Render Dashboard](https://dashboard.render.com)
2. Hacer clic en **"New +"** → **"Blueprint"**
3. Conectar tu repositorio de Git
4. Render detectará automáticamente el archivo `render.yaml`

### 2. Variables de Entorno Requeridas

Render creará el servicio automáticamente, pero **debes configurar manualmente** las siguientes variables de entorno en el dashboard:

#### 🔐 Variables Críticas (Configurar Manualmente)

| Variable | Descripción | Dónde Obtenerla | Ejemplo |
|----------|-------------|-----------------|---------|
| `SUPABASE_URL` | URL de tu proyecto Supabase | [Supabase Dashboard](https://app.supabase.com) → Project Settings → API | `https://xxxxx.supabase.co` |
| `SUPABASE_KEY` | API Key de Supabase (anon/public) | Supabase Dashboard → Project Settings → API → `anon` `public` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `WHATSAPP_VERIFY_TOKEN` | Token de verificación del webhook | Crear uno aleatorio seguro | `mi_token_secreto_verificacion_12345` |
| `WHATSAPP_ACCESS_TOKEN` | Token de acceso de WhatsApp Cloud API | [Meta Developer Console](https://developers.facebook.com) → WhatsApp → API Setup | `EAAxxxxxxxxxxxxxxx` |
| `WHATSAPP_PHONE_NUMBER_ID` | ID del número de teléfono de WhatsApp | Meta Developer Console → WhatsApp → Phone Numbers | `123456789012345` |

#### ✅ Variables Auto-configuradas

Estas variables ya están configuradas en `render.yaml`:

- `SECRET_KEY` - Generado automáticamente por Render
- `ALGORITHM` - `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES` - `30`
- `WHATSAPP_API_VERSION` - `v18.0`
- `WHATSAPP_API_URL` - `https://graph.facebook.com`
- `API_V1_PREFIX` - `/api/v1`
- `PROJECT_NAME` - `Sistema Correlativo API`
- `VERSION` - `1.0.0`
- `BACKEND_CORS_ORIGINS` - `["*"]`

---

## 📝 Pasos para Configurar Variables

### Opción 1: Durante la Creación del Blueprint

1. Después de seleccionar el repositorio, Render mostrará las variables
2. Llenar las variables marcadas como `sync: false`
3. Hacer clic en **"Apply"**

### Opción 2: Después del Despliegue

1. Ir a tu servicio en Render Dashboard
2. Ir a **"Environment"** en el menú lateral
3. Hacer clic en **"Add Environment Variable"**
4. Agregar cada variable crítica:
   - Key: `SUPABASE_URL`
   - Value: `https://xxxxx.supabase.co`
   - Hacer clic en **"Save Changes"**
5. Repetir para todas las variables críticas
6. El servicio se redesplegará automáticamente

---

## 🗄️ Configurar Supabase

### 1. Crear Proyecto en Supabase

1. Ir a [Supabase](https://app.supabase.com)
2. Crear nuevo proyecto
3. Esperar a que se inicialice (2-3 minutos)

### 2. Obtener Credenciales

1. Ir a **Project Settings** → **API**
2. Copiar:
   - **URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### 3. Ejecutar Migraciones

```bash
# Localmente (opcional)
# Las migraciones se pueden ejecutar desde Supabase SQL Editor

# O usar CLI de Supabase
supabase db push
```

---

## 📱 Configurar WhatsApp Cloud API

### 1. Crear App en Meta

1. Ir a [Meta for Developers](https://developers.facebook.com)
2. Crear nueva app → **Business** → **WhatsApp**
3. Configurar nombre y detalles

### 2. Obtener Credenciales

1. Ir a **WhatsApp** → **API Setup**
2. Copiar:
   - **Temporary Access Token** (o generar permanente)
   - **Phone Number ID**

### 3. Configurar Webhook

1. En WhatsApp → **Configuration** → **Webhook**
2. **Callback URL**: `https://tu-app.onrender.com/api/v1/webhook`
3. **Verify Token**: El mismo que configuraste en `WHATSAPP_VERIFY_TOKEN`
4. **Webhook Fields**: Seleccionar `messages`
5. Hacer clic en **"Verify and Save"**

---

## 🔍 Verificar Despliegue

### 1. Health Check

```bash
curl https://tu-app.onrender.com/
```

**Respuesta esperada**:
```json
{
  "message": "Sistema Correlativo API",
  "version": "1.0.0",
  "status": "healthy"
}
```

### 2. Documentación API

Abrir en navegador:
```
https://tu-app.onrender.com/docs
```

Deberías ver la documentación interactiva de FastAPI (Swagger UI).

### 3. Verificar Webhook de WhatsApp

```bash
curl "https://tu-app.onrender.com/api/v1/webhook?hub.mode=subscribe&hub.verify_token=TU_TOKEN&hub.challenge=123456"
```

**Respuesta esperada**: `123456`

---

## 🔄 Auto-Deploy

El servicio está configurado con `autoDeploy: true`, lo que significa que:

- ✅ Cada push a la rama `main` desplegará automáticamente
- ✅ Render ejecutará `pip install -r requirements.txt`
- ✅ Render iniciará el servidor con `uvicorn`
- ✅ Health checks se ejecutarán cada 30 segundos

---

## 📊 Monitoreo

### Logs en Tiempo Real

1. Ir a tu servicio en Render Dashboard
2. Hacer clic en **"Logs"**
3. Ver logs en tiempo real

### Métricas

1. Ir a **"Metrics"**
2. Ver:
   - CPU usage
   - Memory usage
   - Request count
   - Response times

---

## 🚨 Troubleshooting

### Error: "Application failed to respond"

**Causa**: Variables de entorno faltantes

**Solución**:
1. Verificar que todas las variables críticas están configuradas
2. Revisar logs para ver qué variable falta
3. Agregar variable y redesplegar

### Error: "Build failed"

**Causa**: Dependencias faltantes o incompatibles

**Solución**:
```bash
# Verificar requirements.txt localmente
pip install -r requirements.txt

# Si funciona localmente, verificar versión de Python en Render
# Debe ser Python 3.12
```

### Error: "Webhook verification failed"

**Causa**: Token de verificación incorrecto

**Solución**:
1. Verificar que `WHATSAPP_VERIFY_TOKEN` en Render coincide con el configurado en Meta
2. Verificar que la URL del webhook es correcta
3. Revisar logs para ver el error específico

---

## 🔐 Seguridad

### Mejores Prácticas

1. **Nunca commitear** archivos `.env` al repositorio
2. **Usar secretos** para tokens y keys sensibles
3. **Rotar tokens** periódicamente
4. **Limitar CORS** en producción:
   ```yaml
   - key: BACKEND_CORS_ORIGINS
     value: '["https://tu-frontend.com"]'
   ```
5. **Habilitar HTTPS** (Render lo hace automáticamente)

### Variables Sensibles

Marcar como **secretas** en Render:
- `SUPABASE_KEY`
- `SECRET_KEY`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_VERIFY_TOKEN`

---

## 💰 Costos

### Plan Free

- ✅ 750 horas/mes gratis
- ✅ Auto-sleep después de 15 min de inactividad
- ✅ HTTPS incluido
- ✅ Auto-deploy incluido
- ⚠️ Servicio puede tardar ~30s en despertar

### Plan Starter ($7/mes)

- ✅ Sin auto-sleep
- ✅ Más recursos (512 MB RAM)
- ✅ Mejor rendimiento

---

## 🔄 Actualizar Configuración

### Modificar render.yaml

1. Editar `render.yaml` localmente
2. Commit y push a `main`
3. Render detectará cambios y actualizará la configuración

### Agregar Nueva Variable

```yaml
envVars:
  - key: MI_NUEVA_VARIABLE
    value: mi_valor
```

O marcar como manual:
```yaml
envVars:
  - key: MI_VARIABLE_SECRETA
    sync: false  # Configurar manualmente en dashboard
```

---

## 📚 Recursos Adicionales

- [Documentación de Render](https://render.com/docs)
- [Render Blueprint Spec](https://render.com/docs/blueprint-spec)
- [Supabase Docs](https://supabase.com/docs)
- [WhatsApp Cloud API Docs](https://developers.facebook.com/docs/whatsapp/cloud-api)

---

## ✅ Checklist de Despliegue

- [ ] Crear cuenta en Render
- [ ] Crear proyecto en Supabase
- [ ] Crear app en Meta for Developers
- [ ] Conectar repositorio en Render
- [ ] Configurar variables de entorno:
  - [ ] `SUPABASE_URL`
  - [ ] `SUPABASE_KEY`
  - [ ] `WHATSAPP_VERIFY_TOKEN`
  - [ ] `WHATSAPP_ACCESS_TOKEN`
  - [ ] `WHATSAPP_PHONE_NUMBER_ID`
- [ ] Verificar health check
- [ ] Configurar webhook en Meta
- [ ] Probar envío de mensaje de WhatsApp
- [ ] Verificar logs en Render
- [ ] Configurar dominio personalizado (opcional)

---

## 🎯 Próximos Pasos

1. **Dominio personalizado**: Configurar en Render → Settings → Custom Domain
2. **CI/CD avanzado**: Agregar tests antes del deploy
3. **Staging environment**: Crear servicio separado para testing
4. **Monitoring**: Integrar con Sentry o similar
5. **Backups**: Configurar backups automáticos de Supabase
