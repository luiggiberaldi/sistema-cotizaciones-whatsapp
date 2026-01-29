-- Create business_info table
CREATE TABLE IF NOT EXISTS business_info (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('logistica', 'pagos', 'contacto', 'general')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE business_info ENABLE ROW LEVEL SECURITY;

-- Create policy to allow read access to everyone
CREATE POLICY "Public read access for business_info" 
ON business_info FOR SELECT 
USING (true);

-- Create policy to allow write access only to authenticated users (or service role)
CREATE POLICY "Authenticated update access for business_info" 
ON business_info FOR UPDATE 
USING (auth.role() = 'authenticated')
WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated insert access for business_info" 
ON business_info FOR INSERT 
WITH CHECK (auth.role() = 'authenticated');


-- Seed data (Upsert to avoid conflicts if re-run)
INSERT INTO business_info (key, value, category) VALUES
    ('direccion', 'Av. Principal, Edificio Azul, Piso 1', 'contacto'),
    ('horario', 'Lunes a Sábado de 9am a 6pm', 'contacto'),
    ('telefono_contacto', '+584121234567', 'contacto'),
    ('delivery_info', 'Sí, tenemos delivery en toda la ciudad', 'logistica'),
    ('delivery_precio', 'El costo depende de la zona, desde $3', 'logistica'),
    ('metodos_pago', 'Aceptamos Pago Móvil, Zelle, Efectivo y Binance', 'pagos'),
    ('pago_movil', 'Banco: Venezuela, Tel: 04121234567, CI: 12345678', 'pagos'),
    ('zelle', 'correo@empresa.com', 'pagos'),
    ('binance', 'ID: 12345678', 'pagos')
ON CONFLICT (key) DO UPDATE SET 
    value = EXCLUDED.value,
    category = EXCLUDED.category;
