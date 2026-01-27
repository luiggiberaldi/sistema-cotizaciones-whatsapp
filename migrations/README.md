# Migraciones de Base de Datos

Este directorio contiene los scripts SQL para crear y mantener el esquema de la base de datos en Supabase.

## Orden de Ejecución

1. `001_create_quotes_table.sql` - Crea la tabla de cotizaciones con todas las configuraciones

## Cómo Ejecutar en Supabase

### Opción 1: Dashboard de Supabase

1. Ir a tu proyecto en [Supabase Dashboard](https://app.supabase.com)
2. Navegar a **SQL Editor** en el menú lateral
3. Crear una nueva query
4. Copiar y pegar el contenido del archivo SQL
5. Ejecutar la query

### Opción 2: CLI de Supabase

```bash
# Instalar Supabase CLI
npm install -g supabase

# Login
supabase login

# Ejecutar migración
supabase db push
```

### Opción 3: Cliente PostgreSQL

```bash
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" -f migrations/001_create_quotes_table.sql
```

## Verificación

Después de ejecutar la migración, verifica que todo esté correcto:

```sql
-- Ver estructura de la tabla
\d quotes

-- Ver datos de ejemplo
SELECT * FROM quotes;

-- Ver vista resumida
SELECT * FROM quotes_summary;
```

## Notas Importantes

- El campo `id` es **SERIAL** (autoincremental), no necesitas proporcionarlo al insertar
- El campo `items` usa **JSONB** para almacenar arrays de objetos
- Los timestamps `created_at` y `updated_at` se manejan automáticamente
- Las políticas RLS están habilitadas para seguridad
