# 🚀 Guía Rápida de Despliegue - Producción

## Backend en Render

### 1. Conectar Repositorio
- Ir a [Render Dashboard](https://dashboard.render.com)
- New + → Blueprint
- Conectar repositorio Git
- Render detectará `render.yaml`

### 2. Variables de Entorno
Configurar en Render Dashboard:

```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
WHATSAPP_VERIFY_TOKEN=mi_token_secreto_12345
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=123456789012345
```

### 3. Configurar Webhook
- URL: `https://tu-app.onrender.com/api/v1/webhook`
- Token: El mismo que `WHATSAPP_VERIFY_TOKEN`

---

## Frontend en Vercel

### 1. Conectar Repositorio
- Ir a [Vercel Dashboard](https://vercel.com/dashboard)
- Import Project
- Root Directory: `frontend`

### 2. Variable de Entorno
```bash
VITE_API_URL=https://tu-app.onrender.com/api/v1
```

### 3. Deploy
- Click Deploy
- Esperar build (~2 min)
- URL: `https://tu-proyecto.vercel.app`

---

## ✅ Verificar

### Backend
```bash
curl https://tu-app.onrender.com/
curl https://tu-app.onrender.com/docs
```

### Frontend
```bash
# Abrir en navegador
https://tu-proyecto.vercel.app
```

### Integración
1. Abrir frontend
2. Ver tabla de cotizaciones
3. Seleccionar clientes
4. Enviar mensaje plantilla

---

## 📚 Documentación Completa

- Backend: [`docs/DEPLOY.md`](../docs/DEPLOY.md)
- Frontend: [`frontend/DEPLOY_VERCEL.md`](../frontend/DEPLOY_VERCEL.md)
- Webhook: [`docs/WHATSAPP_WEBHOOK.md`](../docs/WHATSAPP_WEBHOOK.md)
