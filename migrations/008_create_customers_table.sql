-- Migración 008: Crear tabla de clientes y relacionar con cotizaciones
-- Descripción: Implementación del módulo de Cartera de Clientes (CRM)

-- 1. Crear tabla customers
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(50) NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    dni_rif TEXT,
    main_address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Habilitar RLS para customers
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read access for customers" ON customers FOR SELECT USING (true);
CREATE POLICY "Public insert access for customers" ON customers FOR INSERT WITH CHECK (true);
CREATE POLICY "Public update access for customers" ON customers FOR UPDATE USING (true);


-- 2. Modificar tabla quotes para relacionar con customers
-- Agregamos la columna customer_id como FK
ALTER TABLE quotes 
ADD COLUMN IF NOT EXISTS customer_id UUID REFERENCES customers(id) ON DELETE SET NULL;

COMMENT ON COLUMN quotes.customer_id IS 'Referencia al cliente registrado (tabla customers)';


-- 3. Modificar tabla active_sessions
-- Para mantener el contexto del cliente durante la sesión
ALTER TABLE active_sessions
ADD COLUMN IF NOT EXISTS customer_id UUID REFERENCES customers(id) ON DELETE SET NULL;


-- 4. Indices para búsqueda rápida
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone_number);
CREATE INDEX IF NOT EXISTS idx_quotes_customer ON quotes(customer_id);
