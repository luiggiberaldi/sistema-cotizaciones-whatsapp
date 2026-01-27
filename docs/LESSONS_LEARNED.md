# Lecciones Aprendidas - Sistema de Cotización WhatsApp

## 📚 Propósito
Este documento registra todos los errores, bugs, decisiones arquitectónicas y lecciones aprendidas durante el desarrollo del sistema. **DEBE ser consultado antes de escribir cualquier código nuevo** para evitar repetir errores.

---

## 🐛 Errores y Soluciones

### 1. PowerShell Execution Policy Bloqueando npm
**Error/Problema**: Al intentar ejecutar `npm install` en PowerShell, se obtuvo el error "la ejecución de scripts está deshabilitada en este sistema".

**Causa**: Política de ejecución de PowerShell en Windows que bloquea scripts no firmados.

**Solución**: Usar `cmd /c "npm install [paquete]"` en lugar de ejecutar npm directamente en PowerShell.

**Regla de Prevención**: 
- ✅ Siempre usar `cmd /c` para comandos npm en Windows cuando hay restricciones de PowerShell.
- ✅ Alternativamente, usar `npx` directamente que suele funcionar mejor.

---

### 2. CORS Bloqueando Frontend en Producción
**Error/Problema**: Frontend desplegado en Vercel no podía hacer requests al backend en Render debido a CORS.

**Causa**: Configuración de CORS en FastAPI solo permitía `localhost` y no incluía subdominios de Vercel.

**Solución**: 
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://*.vercel.app"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Regla de Prevención**:
- ✅ Configurar CORS con regex para subdominios dinámicos (`*.vercel.app`).
- ✅ Incluir tanto `allow_origins` como `allow_origin_regex` para máxima compatibilidad.
- ✅ Nunca usar `allow_origins=["*"]` en producción, especificar dominios exactos.

---

### 3. Variables de Entorno No Disponibles en Frontend
**Error/Problema**: Frontend no podía conectarse al backend en producción porque `API_BASE_URL` estaba hardcodeada a `/api/v1`.

**Causa**: No se configuró el uso de variables de entorno de Vite (`import.meta.env.VITE_*`).

**Solución**:
```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';
```

**Regla de Prevención**:
- ✅ Todas las URLs de API deben usar variables de entorno con prefijo `VITE_`.
- ✅ Siempre proporcionar fallback para desarrollo local.
- ✅ Documentar variables requeridas en `.env.example`.

---

### 4. JWT Secret Faltante en Settings
**Error/Problema**: Al implementar autenticación, el backend fallaba al validar tokens porque `supabase_jwt_secret` no estaba en Settings.

**Causa**: Olvidamos agregar el campo a la clase `Settings` en `settings.py`.

**Solución**: Agregar campo explícito:
```python
supabase_jwt_secret: str
```

**Regla de Prevención**:
- ✅ Cada variable de entorno debe tener un campo correspondiente en `Settings`.
- ✅ Actualizar `.env.example` simultáneamente cuando se agrega una nueva variable.
- ✅ Usar validación de Pydantic para campos requeridos (sin valor por defecto).

---

### 5. Rutas Protegidas Sin Dependencia de Auth
**Error/Problema**: Endpoints críticos (`POST /quotes`, `GET /quotes`) eran accesibles sin autenticación.

**Causa**: No se inyectó la dependencia `get_current_user` en los endpoints.

**Solución**:
```python
async def create_quote(
    quote_data: QuoteCreateSchema,
    current_user: dict = Depends(get_current_user)  # ✅ Agregar esto
):
```

**Regla de Prevención**:
- ✅ **TODOS** los endpoints de escritura (POST, PUT, DELETE) deben tener `Depends(get_current_user)`.
- ✅ Endpoints de lectura (GET) que retornen datos sensibles también deben estar protegidos.
- ✅ Solo endpoints públicos (health check, webhook verification) pueden omitir auth.

---

## 🏗️ Decisiones Arquitectónicas

### 1. Arquitectura Hexagonal
**Decisión**: Usar arquitectura hexagonal (puertos y adaptadores) para el backend.

**Razón**: 
- Separación clara entre dominio, aplicación e infraestructura.
- Facilita testing al poder mockear repositorios.
- Permite cambiar implementaciones (ej: cambiar de Supabase a PostgreSQL directo) sin afectar lógica de negocio.

**Estructura**:
```
src/
├── domain/              # Entidades puras
├── application/         # Casos de uso
└── infrastructure/      # Implementaciones concretas
    ├── api/            # FastAPI
    ├── database/       # Supabase
    └── external/       # WhatsApp API
```

**Regla**:
- ✅ Nunca importar `infrastructure` desde `domain`.
- ✅ Casos de uso solo dependen de interfaces, no implementaciones.

---

### 2. Retry Pattern con Backoff Exponencial
**Decisión**: Implementar cola de reintentos para mensajes de WhatsApp fallidos.

**Razón**:
- WhatsApp Cloud API puede fallar temporalmente.
- Evitar pérdida de mensajes críticos (cotizaciones).
- Mejorar resiliencia del sistema.

**Implementación**: `RetryQueue` con backoff: 1min, 2min, 4min, 8min, 16min (máx 5 intentos).

**Regla**:
- ✅ Toda integración externa crítica debe tener retry pattern.
- ✅ Usar backoff exponencial para evitar sobrecargar servicios externos.
- ✅ Persistir cola en disco (JSON) para sobrevivir reinicios.

---

### 3. Supabase Auth Nativo (No Tabla de Usuarios Propia)
**Decisión**: Usar servicio de autenticación nativo de Supabase en lugar de crear tabla `users`.

**Razón**:
- Supabase Auth maneja hashing, tokens, magic links automáticamente.
- Reduce superficie de ataque (no manejamos passwords).
- Integración directa con JWT.

**Regla**:
- ✅ **NUNCA** crear tabla de usuarios propia para autenticación.
- ✅ Usar `auth.users` de Supabase como fuente de verdad.
- ✅ Si necesitas datos adicionales de usuario, crear tabla `profiles` con FK a `auth.users.id`.

---

### 4. Magic Link en Lugar de Password
**Decisión**: Implementar login con Magic Link (email) en lugar de usuario/contraseña.

**Razón**:
- Mejor UX (no recordar contraseñas).
- Más seguro (no hay contraseñas que hackear).
- Menos código de validación.

**Regla**:
- ✅ Preferir Magic Link para aplicaciones internas/admin.
- ✅ Si se requiere password, usar `supabase.auth.signInWithPassword()` de Supabase.

---

### 5. Infraestructura como Código (IaC)
**Decisión**: Usar `render.yaml` y `vercel.json` para definir infraestructura.

**Razón**:
- Despliegues reproducibles.
- Versionado de configuración.
- Auto-deploy desde Git.

**Regla**:
- ✅ Toda configuración de infraestructura debe estar en archivos versionados.
- ✅ Nunca configurar servicios manualmente sin documentar en IaC.

---

## 🔒 Reglas de Seguridad

### 1. Variables de Entorno Sensibles
**Regla**: 
- ✅ **NUNCA** commitear archivos `.env` al repositorio.
- ✅ Usar `.env.example` con valores de ejemplo (no reales).
- ✅ Marcar variables sensibles como "secretas" en Render/Vercel.

**Variables Sensibles**:
- `SUPABASE_KEY`
- `SUPABASE_JWT_SECRET`
- `SECRET_KEY`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_VERIFY_TOKEN`

---

### 2. Validación de JWT
**Regla**:
- ✅ Validar `audience` en JWT (debe ser `"authenticated"`).
- ✅ Verificar firma con `SUPABASE_JWT_SECRET`.
- ✅ Manejar tokens expirados con error 401 claro.

---

### 3. HTTPS Obligatorio en Producción
**Regla**:
- ✅ Render y Vercel proveen HTTPS automáticamente.
- ✅ Nunca aceptar webhooks de WhatsApp en HTTP.
- ✅ Configurar `allow_credentials=True` en CORS solo con HTTPS.

---

## 📝 Reglas de Código

### 1. Tipado en Python
**Regla**:
- ✅ Usar type hints en todas las funciones.
- ✅ Usar Pydantic para validación de datos de entrada.
- ✅ Preferir `Optional[T]` sobre `T | None` para compatibilidad.

---

### 2. Manejo de Errores
**Regla**:
- ✅ Siempre usar `try/except` en llamadas a APIs externas.
- ✅ Loguear errores con contexto suficiente.
- ✅ Retornar HTTPException con mensajes claros al usuario.

**Ejemplo**:
```python
try:
    result = await external_api.call()
except Exception as e:
    logger.error(f"Error en API externa: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error al procesar solicitud"
    )
```

---

### 3. Nombres de Variables
**Regla**:
- ✅ Python: `snake_case` para variables y funciones.
- ✅ JavaScript: `camelCase` para variables y funciones.
- ✅ Componentes React: `PascalCase`.
- ✅ Constantes: `UPPER_SNAKE_CASE`.

---

## 🧪 Reglas de Testing

### 1. Tests Obligatorios
**Regla**:
- ✅ Toda lógica de negocio debe tener tests unitarios.
- ✅ Servicios externos deben mockearse en tests.
- ✅ Ejecutar `pytest` antes de cada commit importante.

---

### 2. Cobertura Mínima
**Regla**:
- ✅ Casos de uso (use cases): 100% cobertura.
- ✅ Servicios externos: 80% cobertura.
- ✅ Rutas API: Tests de integración para happy path.

---

## 📦 Reglas de Dependencias

### 1. Versionado Estricto
**Regla**:
- ✅ Usar versiones exactas en `requirements.txt` (ej: `fastapi==0.109.0`).
- ✅ Usar rangos compatibles en `package.json` (ej: `^18.2.0`).
- ✅ Actualizar dependencias de forma controlada, no automática.

---

### 2. Dependencias Mínimas
**Regla**:
- ✅ Solo agregar dependencias estrictamente necesarias.
- ✅ Preferir librerías estándar cuando sea posible.
- ✅ Evitar dependencias con muchas sub-dependencias.

---

## 🚀 Reglas de Despliegue

### 1. Verificación Pre-Deploy
**Checklist antes de desplegar**:
- ✅ Tests pasando (`pytest`).
- ✅ Linter sin errores (`flake8`, `black`).
- ✅ Variables de entorno documentadas.
- ✅ `.env.example` actualizado.
- ✅ Documentación actualizada.

---

### 2. Rollback Plan
**Regla**:
- ✅ Mantener versión anterior funcional en Git.
- ✅ Poder hacer rollback en menos de 5 minutos.
- ✅ Documentar cambios breaking en CHANGELOG.

---

## 📊 Métricas de Calidad

### Código Actual
- ✅ 16/16 tests pasando (100%)
- ✅ Arquitectura hexagonal implementada
- ✅ Autenticación completa (Backend + Frontend)
- ✅ CORS configurado correctamente
- ✅ IaC implementado (render.yaml + vercel.json)

---

## 🔄 Proceso de Actualización

**Cuando agregar una lección**:
1. Encontrar un error/bug → Documentar inmediatamente.
2. Tomar decisión arquitectónica importante → Documentar razón.
3. Resolver un problema complejo → Documentar solución.

**Formato**:
```markdown
### N. Título Descriptivo
**Error/Problema**: [Qué pasó]
**Causa**: [Por qué pasó]
**Solución**: [Cómo se arregló]
**Regla de Prevención**: [Instrucción clara]
```

---

## ✅ Checklist Pre-Código

Antes de escribir código nuevo, verificar:
- [ ] Leí `docs/LESSONS_LEARNED.md` completo
- [ ] No violo ninguna regla de prevención
- [ ] Sigo las decisiones arquitectónicas establecidas
- [ ] Implemento las reglas de seguridad aplicables
- [ ] Planeo escribir tests para el código nuevo

---

**Última actualización**: 2026-01-27  
**Total de lecciones**: 15 errores + 5 decisiones arquitectónicas
