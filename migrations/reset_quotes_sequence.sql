-- ============================================
-- Script para Reiniciar el Correlativo de Cotizaciones
-- ============================================
-- Ejecuta este script en el Editor SQL de Supabase para reiniciar el contador a 1.

-- Reiniciar la secuencia
ALTER SEQUENCE quotes_id_seq RESTART WITH 1;

-- Si quieres asegurarte que empiece desde el próximo ID disponible (si no has borrado todo):
-- SELECT setval('quotes_id_seq', (SELECT MAX(id) FROM quotes));
