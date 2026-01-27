# 🚀 Inicio Rápido - Despliegue en Render

## Variables de Entorno Requeridas

Configura estas variables en el dashboard de Render después del despliegue:

### 🔐 Supabase (Base de Datos)

```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Dónde obtenerlas**:
1. Ir a [Supabase Dashboard](https://app.supabase.com)
2. Seleccionar tu proyecto
3. Settings → API
4. Copiar URL y anon/public key

---

### 📱 WhatsApp Cloud API

```
WHATSAPP_VERIFY_TOKEN=mi_token_secreto_verificacion_12345
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=123456789012345
```

**Dónde obtenerlas**:
1. Ir a [Meta for Developers](https://developers.facebook.com)
2. Seleccionar tu app
3. WhatsApp → API Setup
4. Copiar Access Token y Phone Number ID
5. Crear un token de verificación aleatorio y seguro

---

## 🔧 Configurar Webhook de WhatsApp

Después del despliegue en Render:

1. Copiar URL de tu app: `https://tu-app.onrender.com`
2. Ir a Meta Developer Console → WhatsApp → Configuration
3. Configurar webhook:
   - **Callback URL**: `https://tu-app.onrender.com/api/v1/webhook`
   - **Verify Token**: El mismo que configuraste en `WHATSAPP_VERIFY_TOKEN`
4. Seleccionar campo: `messages`
5. Hacer clic en "Verify and Save"

---

## ✅ Verificar Despliegue

### 1. Health Check
```bash
curl https://tu-app.onrender.com/
```

### 2. Documentación API
```
https://tu-app.onrender.com/docs
```

### 3. Webhook
```bash
curl "https://tu-app.onrender.com/api/v1/webhook?hub.mode=subscribe&hub.verify_token=TU_TOKEN&hub.challenge=123"
```

---

## 📋 Checklist

- [ ] Crear cuenta en Render
- [ ] Conectar repositorio
- [ ] Configurar `SUPABASE_URL`
- [ ] Configurar `SUPABASE_KEY`
- [ ] Configurar `WHATSAPP_VERIFY_TOKEN`
- [ ] Configurar `WHATSAPP_ACCESS_TOKEN`
- [ ] Configurar `WHATSAPP_PHONE_NUMBER_ID`
- [ ] Verificar health check
- [ ] Configurar webhook en Meta
- [ ] Probar envío de mensaje

---

Ver [DEPLOY.md](DEPLOY.md) para documentación completa.
