# Script para verificar claves de Gemini (Versión Segura)
# Las claves deben estar en el archivo .env o ser pasadas como argumento.
# NO ESCRIBIR CLAVES REALES AQUÍ.

$keys = @(
    "YOUR_API_KEY_HERE_OR_READ_FROM_ENV"
)

Write-Host "Verificando $($keys.Count) claves..." -ForegroundColor Cyan

foreach ($key in $keys) {
    if ($key -eq "YOUR_API_KEY_HERE_OR_READ_FROM_ENV") {
        continue
    }
    
    $url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash?key=$key"
    try {
        $response = Invoke-RestMethod -Uri $url -Method Get -ErrorAction Stop
        Write-Host "✅ Clave OK: $key (Masked: $( $key.Substring(0,5) )...)" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Error con Clave: $key" -ForegroundColor Red
        Write-Host "   $($_.Exception.Message)" -ForegroundColor Gray
    }
}
