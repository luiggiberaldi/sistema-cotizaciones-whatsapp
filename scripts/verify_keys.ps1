$keys = @(
    "AIzaSyChvvi8Uj5QjjJqR_MiVkpqZsBiFDJvHJk",
    "AIzaSyCS6UBbkakLvYOXNNBdeP2HPBw8ZLZgetE",
    "AIzaSyALM4oHJ9-0H0yCrr1Bs4MpifesCwi2Hk8",
    "AIzaSyB7XToGQMnn5H1QRPosCP1sE8fe3zJHPnk",
    "AIzaSyAEP0WANsMsfgvHwMdgpBBFn6QRjt2uXh8"
)

$modelsToTest = @("gemini-1.5-flash", "gemini-2.5-flash", "gemini-pro")

foreach ($key in $keys) {
    Write-Host "---------------------------------------------------"
    Write-Host "Checking Key: $($key.Substring(0,5))..." -ForegroundColor Cyan
    
    # 1. Check Permissions (List Models)
    $listUrl = "https://generativelanguage.googleapis.com/v1beta/models?key=$key"
    try {
        $listResponse = Invoke-RestMethod -Uri $listUrl -Method Get -ErrorAction Stop
        Write-Host "  [v] Key is VALID (Models listed)" -ForegroundColor Green
        
        # Filter relevant models
        $availableModels = $listResponse.models | Where-Object { $_.name -match "gemini" -and $_.supportedGenerationMethods -contains "generateContent" } | Select-Object -ExpandProperty name
        # Write-Host "  Available Models: $($availableModels -join ', ')" -ForegroundColor Gray
    } catch {
        Write-Host "  [x] Key validation FAILED: $_" -ForegroundColor Red
        continue
    }

    # 2. Check Quota (Generate Content)
    foreach ($model in $modelsToTest) {
        $genUrl = "https://generativelanguage.googleapis.com/v1beta/models/$($model):generateContent?key=$key"
        $body = @{ contents = @( @{ parts = @( @{ text = "Hi" } ) } ) } | ConvertTo-Json -Depth 5
        
        try {
            $response = Invoke-RestMethod -Uri $genUrl -Method Post -Body $body -ContentType "application/json" -ErrorAction Stop
            Write-Host "    [v] Model ${model}: WORKING (Quota OK)" -ForegroundColor Green
        } catch {
            $err = $_
            if ($err.Exception.Response.StatusCode -eq "TooManyRequests") {
                 Write-Host "    [!] Model ${model}: QUOTA EXCEEDED (429)" -ForegroundColor Yellow
            } elseif ($err.Exception.Response.StatusCode -eq "NotFound" -or $err.ToString().Contains("400")) {
                 Write-Host "    [x] Model ${model}: NOT FOUND/SUPPORTED" -ForegroundColor DarkGray
            } else {
                 Write-Host "    [x] Model ${model}: ERROR - $($err.Exception.Message)" -ForegroundColor Red
            }
        }
    }
}
Write-Host "---------------------------------------------------"
