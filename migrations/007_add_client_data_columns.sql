-- Migración 007: Agregar columnas para datos del cliente
-- Fecha: 2026-01-27

-- 1. Actualizar tabla active_sessions
-- Agregar conversation_step (default 'shopping')
ALTER TABLE active_sessions 
ADD COLUMN IF NOT EXISTS conversation_step TEXT DEFAULT 'shopping';

-- Agregar client_data (default '{}')
ALTER TABLE active_sessions 
ADD COLUMN IF NOT EXISTS client_data JSONB DEFAULT '{}'::jsonb;

-- 2. Actualizar tabla quotes
-- Agregar datos del cliente para facturación/recibo
ALTER TABLE quotes 
ADD COLUMN IF NOT EXISTS client_name TEXT,
ADD COLUMN IF NOT EXISTS client_dni TEXT,
ADD COLUMN IF NOT EXISTS client_address TEXT;

-- Comentarios para documentación
COMMENT ON COLUMN active_sessions.conversation_step IS 'Paso actual de la conversación (shopping, asking_name, asking_dni, asking_address, confirming)';
COMMENT ON COLUMN active_sessions.client_data IS 'Datos temporales del cliente durante el wizard de checkout';
COMMENT ON COLUMN quotes.client_name IS 'Nombre o Razón Social del cliente';
COMMENT ON COLUMN quotes.client_dni IS 'Cédula o RIF del cliente';
COMMENT ON COLUMN quotes.client_address IS 'Dirección fiscal o de entrega';
