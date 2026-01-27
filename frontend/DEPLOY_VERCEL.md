# Despliegue del Frontend en Vercel

## 🚀 Configuración de Producción

El frontend está configurado para desplegarse en **Vercel** con soporte para variables de entorno y CORS.

---

## 📋 Pre-requisitos

1. **Cuenta en Vercel**: [Crear cuenta gratuita](https://vercel.com/signup)
2. **Backend desplegado**: URL del backend en Render (ej: `https://tu-app.onrender.com`)

---

## 🔧 Configuración

### 1. Variables de Entorno

El frontend usa la variable `VITE_API_URL` para conectarse al backend.

**Archivo**: `frontend/src/services/api.js`

```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';
```

**Comportamiento**:
- **Desarrollo**: Usa proxy local (`/api/v1` → `http://localhost:8000/api/v1`)
- **Producción**: Usa `VITE_API_URL` configurada en Vercel

---

### 2. Configurar en Vercel

#### Opción 1: Durante el Despliegue

1. Ir a [Vercel Dashboard](https://vercel.com/dashboard)
2. **Import Project** → Conectar repositorio
3. Seleccionar carpeta `frontend`
4. En **Environment Variables**:
   - Key: `VITE_API_URL`
   - Value: `https://tu-app.onrender.com/api/v1`
5. Deploy

#### Opción 2: Después del Despliegue

1. Ir a tu proyecto en Vercel
2. **Settings** → **Environment Variables**
3. Agregar:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://tu-app.onrender.com/api/v1`
   - **Environments**: Production, Preview, Development
4. **Redeploy** para aplicar cambios

---

## 📝 Archivo vercel.json

**Ubicación**: `frontend/vercel.json`

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

**Características**:
- ✅ **Rewrites**: Redirige todas las rutas a `index.html` (SPA)
- ✅ **Cache**: Headers de cache para assets estáticos
- ✅ **Framework**: Detecta Vite automáticamente

---

## 🔐 Configuración de CORS

El backend está configurado para permitir requests desde Vercel.

**Archivo**: `src/main.py`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://*.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Permite**:
- ✅ Localhost (desarrollo)
- ✅ Cualquier subdominio de Vercel (`*.vercel.app`)
- ✅ Dominio personalizado (agregar manualmente)

---

## 🚀 Despliegue Paso a Paso

### 1. Preparar Repositorio

```bash
# Asegurarse de que frontend/.env.example existe
cd frontend
cat .env.example

# Debería mostrar:
# VITE_API_URL=http://localhost:8000/api/v1
```

### 2. Conectar con Vercel

1. Ir a [Vercel Dashboard](https://vercel.com/dashboard)
2. **Add New...** → **Project**
3. **Import Git Repository**
4. Seleccionar tu repositorio
5. **Root Directory**: `frontend`
6. **Framework Preset**: Vite (detectado automáticamente)

### 3. Configurar Variables

En la sección **Environment Variables**:

| Key | Value | Environments |
|-----|-------|--------------|
| `VITE_API_URL` | `https://tu-app.onrender.com/api/v1` | Production, Preview, Development |

**Importante**: Reemplazar `tu-app.onrender.com` con tu URL real de Render.

### 4. Deploy

1. Hacer clic en **Deploy**
2. Esperar a que termine el build (~2 minutos)
3. Vercel asignará una URL: `https://tu-proyecto.vercel.app`

---

## ✅ Verificar Despliegue

### 1. Abrir Frontend

```
https://tu-proyecto.vercel.app
```

### 2. Verificar Conexión con Backend

1. Abrir DevTools (F12)
2. Ir a **Network**
3. Recargar página
4. Verificar requests a `https://tu-app.onrender.com/api/v1/quotes`

**Esperado**: Status 200 OK

### 3. Probar Funcionalidad

1. Ver tabla de cotizaciones
2. Seleccionar clientes
3. Crear lista de difusión
4. Enviar mensaje plantilla

---

## 🔄 Auto-Deploy

Vercel está configurado para auto-deploy:

- ✅ **Push a main** → Deploy a producción
- ✅ **Pull Request** → Deploy preview
- ✅ **Comentarios en PR** con URL de preview

---

## 🌐 Dominio Personalizado

### Configurar Dominio

1. Ir a **Settings** → **Domains**
2. Agregar dominio: `tu-dominio.com`
3. Configurar DNS según instrucciones de Vercel
4. Esperar propagación (~24 horas)

### Actualizar CORS en Backend

Editar `src/main.py`:

```python
allow_origins=[
    "http://localhost:5173",
    "https://*.vercel.app",
    "https://tu-dominio.com",  # Agregar dominio personalizado
],
```

Redesplegar backend en Render.

---

## 🐛 Troubleshooting

### Error: "Failed to fetch"

**Causa**: CORS bloqueado o URL incorrecta

**Solución**:
1. Verificar `VITE_API_URL` en Vercel
2. Verificar CORS en backend
3. Ver logs del backend en Render

### Error: "404 Not Found" en rutas

**Causa**: Rewrites no configurados

**Solución**:
1. Verificar que `vercel.json` existe
2. Verificar rewrites:
   ```json
   "rewrites": [{"source": "/(.*)", "destination": "/index.html"}]
   ```

### Error: Variables de entorno no se aplican

**Causa**: No se redesplegó después de agregar variables

**Solución**:
1. Ir a **Deployments**
2. Hacer clic en **...** → **Redeploy**
3. Seleccionar **Use existing Build Cache**: No

---

## 📊 Monitoreo

### Analytics de Vercel

1. Ir a **Analytics**
2. Ver:
   - Page views
   - Unique visitors
   - Top pages
   - Performance metrics

### Logs

1. Ir a **Deployments**
2. Seleccionar deployment
3. Ver **Build Logs** y **Function Logs**

---

## 💰 Costos

### Plan Hobby (Gratis)

- ✅ Despliegues ilimitados
- ✅ 100 GB bandwidth/mes
- ✅ HTTPS automático
- ✅ Auto-deploy desde Git
- ✅ Preview deployments

### Plan Pro ($20/mes)

- ✅ 1 TB bandwidth/mes
- ✅ Más recursos de build
- ✅ Analytics avanzados

---

## 🔒 Seguridad

### Mejores Prácticas

1. **Variables de entorno**: Nunca commitear `.env`
2. **CORS**: Limitar origins en producción
3. **HTTPS**: Habilitado automáticamente por Vercel
4. **Headers de seguridad**: Configurados en `vercel.json`

---

## 📚 Recursos

- [Documentación de Vercel](https://vercel.com/docs)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [Vercel CLI](https://vercel.com/docs/cli)

---

## ✅ Checklist de Despliegue

- [ ] Backend desplegado en Render
- [ ] Obtener URL del backend
- [ ] Crear cuenta en Vercel
- [ ] Conectar repositorio
- [ ] Configurar Root Directory: `frontend`
- [ ] Agregar variable `VITE_API_URL`
- [ ] Deploy
- [ ] Verificar conexión con backend
- [ ] Probar funcionalidades
- [ ] Configurar dominio personalizado (opcional)
- [ ] Actualizar CORS en backend si es necesario

---

## 🎯 URLs de Ejemplo

**Desarrollo**:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

**Producción**:
- Frontend: `https://tu-proyecto.vercel.app`
- Backend: `https://tu-app.onrender.com`
- API: `https://tu-app.onrender.com/api/v1`

---

## 🔄 Actualizar Despliegue

### Cambios en Código

```bash
git add .
git commit -m "Update frontend"
git push origin main
```

Vercel desplegará automáticamente.

### Cambios en Variables de Entorno

1. Ir a **Settings** → **Environment Variables**
2. Editar variable
3. **Save**
4. **Redeploy** desde **Deployments**

---

## 📝 Notas Importantes

1. **VITE_API_URL** debe incluir `/api/v1` al final
2. **CORS** debe estar configurado en el backend
3. **Rewrites** son necesarios para SPA (React Router)
4. **Cache headers** mejoran performance de assets estáticos
5. **Preview deployments** son útiles para testing antes de producción
