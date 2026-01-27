-- ============================================
-- Script SQL para Supabase - Sistema de Cotizaciones
-- ============================================
-- Este script crea la tabla 'quotes' con ID autoincremental
-- y todas las configuraciones necesarias para Supabase

-- Eliminar tabla si existe (solo para desarrollo)
DROP TABLE IF EXISTS quotes CASCADE;

-- Crear tipo ENUM para el estado de las cotizaciones
CREATE TYPE quote_status AS ENUM ('draft', 'pending', 'approved', 'rejected', 'expired');

-- Crear tabla de cotizaciones
CREATE TABLE quotes (
    -- ID autoincremental (correlativo) - PRIMARY KEY
    id SERIAL PRIMARY KEY,
    
    -- Información del cliente
    client_phone VARCHAR(20) NOT NULL,
    
    -- Items de la cotización (almacenados como JSONB)
    items JSONB NOT NULL,
    
    -- Total de la cotización
    total DECIMAL(12, 2) NOT NULL CHECK (total >= 0),
    
    -- Estado de la cotización
    status quote_status NOT NULL DEFAULT 'draft',
    
    -- Notas adicionales
    notes TEXT,
    
    -- Timestamps automáticos
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ============================================
-- ÍNDICES para mejorar el rendimiento
-- ============================================

-- Índice para búsquedas por teléfono del cliente
CREATE INDEX idx_quotes_client_phone ON quotes(client_phone);

-- Índice para búsquedas por estado
CREATE INDEX idx_quotes_status ON quotes(status);

-- Índice para búsquedas por fecha de creación
CREATE INDEX idx_quotes_created_at ON quotes(created_at DESC);

-- Índice compuesto para búsquedas combinadas
CREATE INDEX idx_quotes_phone_status ON quotes(client_phone, status);

-- ============================================
-- TRIGGERS para actualizar updated_at automáticamente
-- ============================================

-- Función para actualizar el campo updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger que ejecuta la función antes de cada UPDATE
CREATE TRIGGER update_quotes_updated_at
    BEFORE UPDATE ON quotes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- POLÍTICAS DE SEGURIDAD (Row Level Security)
-- ============================================

-- Habilitar RLS en la tabla
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;

-- Política: Permitir lectura a todos los usuarios autenticados
CREATE POLICY "Permitir lectura a usuarios autenticados"
    ON quotes
    FOR SELECT
    TO authenticated
    USING (true);

-- Política: Permitir inserción a todos los usuarios autenticados
CREATE POLICY "Permitir inserción a usuarios autenticados"
    ON quotes
    FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- Política: Permitir actualización a todos los usuarios autenticados
CREATE POLICY "Permitir actualización a usuarios autenticados"
    ON quotes
    FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Política: Permitir eliminación a todos los usuarios autenticados
CREATE POLICY "Permitir eliminación a usuarios autenticados"
    ON quotes
    FOR DELETE
    TO authenticated
    USING (true);

-- ============================================
-- FUNCIONES AUXILIARES
-- ============================================

-- Función para obtener el siguiente número correlativo
CREATE OR REPLACE FUNCTION get_next_quote_id()
RETURNS INTEGER AS $$
DECLARE
    next_id INTEGER;
BEGIN
    SELECT COALESCE(MAX(id), 0) + 1 INTO next_id FROM quotes;
    RETURN next_id;
END;
$$ LANGUAGE plpgsql;

-- Función para validar el formato del teléfono
CREATE OR REPLACE FUNCTION validate_phone_format()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.client_phone !~ '^\+?[0-9\s\-\(\)]+$' THEN
        RAISE EXCEPTION 'Formato de teléfono inválido: %', NEW.client_phone;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para validar el teléfono antes de insertar o actualizar
CREATE TRIGGER validate_phone_before_insert_update
    BEFORE INSERT OR UPDATE ON quotes
    FOR EACH ROW
    EXECUTE FUNCTION validate_phone_format();

-- ============================================
-- DATOS DE EJEMPLO (opcional - comentar en producción)
-- ============================================

-- Insertar cotizaciones de ejemplo
INSERT INTO quotes (client_phone, items, total, status, notes) VALUES
(
    '+58 412-1234567',
    '[
        {
            "product_name": "Laptop Dell XPS 15",
            "quantity": 2,
            "unit_price": 1200.00,
            "subtotal": 2400.00,
            "description": "Laptop de alto rendimiento"
        },
        {
            "product_name": "Mouse Logitech MX Master 3",
            "quantity": 2,
            "unit_price": 99.99,
            "subtotal": 199.98,
            "description": "Mouse inalámbrico ergonómico"
        }
    ]'::jsonb,
    2599.98,
    'pending',
    'Cliente corporativo - descuento aplicado'
),
(
    '+58 424-9876543',
    '[
        {
            "product_name": "Monitor LG 27 pulgadas",
            "quantity": 1,
            "unit_price": 350.00,
            "subtotal": 350.00,
            "description": "Monitor 4K UHD"
        }
    ]'::jsonb,
    350.00,
    'approved',
    'Entrega urgente solicitada'
);

-- ============================================
-- VISTAS ÚTILES
-- ============================================

-- Vista para obtener cotizaciones con información resumida
CREATE OR REPLACE VIEW quotes_summary AS
SELECT 
    id,
    client_phone,
    jsonb_array_length(items) as items_count,
    total,
    status,
    created_at,
    updated_at
FROM quotes
ORDER BY created_at DESC;

-- ============================================
-- COMENTARIOS EN LA TABLA
-- ============================================

COMMENT ON TABLE quotes IS 'Tabla de cotizaciones del sistema';
COMMENT ON COLUMN quotes.id IS 'ID autoincremental (correlativo) de la cotización';
COMMENT ON COLUMN quotes.client_phone IS 'Teléfono del cliente (formato internacional permitido)';
COMMENT ON COLUMN quotes.items IS 'Items de la cotización en formato JSONB';
COMMENT ON COLUMN quotes.total IS 'Total de la cotización en formato decimal';
COMMENT ON COLUMN quotes.status IS 'Estado actual de la cotización';
COMMENT ON COLUMN quotes.notes IS 'Notas adicionales sobre la cotización';
COMMENT ON COLUMN quotes.created_at IS 'Fecha y hora de creación (automático)';
COMMENT ON COLUMN quotes.updated_at IS 'Fecha y hora de última actualización (automático)';

-- ============================================
-- VERIFICACIÓN
-- ============================================

-- Verificar que la tabla se creó correctamente
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'quotes'
ORDER BY ordinal_position;

-- Verificar secuencia del ID autoincremental
SELECT 
    sequence_name,
    last_value,
    increment_by
FROM quotes_id_seq;
