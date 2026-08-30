# ByTCJ
# Requiere ejecución con privilegios de Administrador

$Models = @(
    "mistral:7b-instruct-q4_K_M",
    "mixtral:8x7b",
    "deepseek-coder:6.7b-instruct-q4_K_M"
)

$OllamaUrl = "https://ollama.com/download/OllamaSetup.exe"
$InstallerPath = "$env:TEMP\OllamaSetup.exe"

Write-Host "[*] Iniciando verificación de entorno..."

# 1. Detección de ruta personalizada de Ollama
$OllamaModelsPath = $env:OLLAMA_MODELS

if (-not $OllamaModelsPath) {
    # Si la variable no está definida, usamos la ruta por defecto en Windows
    $OllamaModelsPath = Join-Path $env:USERPROFILE ".ollama\models"
    Write-Host "[i] Variable OLLAMA_MODELS no detectada. Usando ruta por defecto: $OllamaModelsPath"
} else {
    Write-Host "[+] Ruta personalizada de modelos detectada: $OllamaModelsPath"
}

# 2. Verificación de binario Ollama
if (Get-Command "ollama" -ErrorAction SilentlyContinue) {
    Write-Host "[+] Binario de Ollama detectado."
} else {
    Write-Host "[-] Ollama no detectado. Instalando..."
    Invoke-WebRequest -Uri $OllamaUrl -OutFile $InstallerPath
    Start-Process -FilePath $InstallerPath -ArgumentList "/SILENT" -Wait -NoNewWindow
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# 3. Configuración de Red
Write-Host "[*] Aplicando configuración OLLAMA_HOST=0.0.0.0..."
Stop-Process -Name "ollama", "ollama app" -Force -ErrorAction SilentlyContinue
$env:OLLAMA_HOST = "0.0.0.0"
[Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0", "User")

Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 5 

# 4. Verificación de modelos en el PATH correcto
foreach ($Model in $Models) {
    Write-Host "[*] Analizando estado de: $Model"
    
    # Reemplazar los dos puntos ':' en el nombre del modelo por guiones bajos '_' 
    # que es el estándar interno de directorios de Ollama para el almacenamiento en disco.
    $FolderModelName = $Model -replace ':', '-'
    
    # Comprobamos la existencia física de la carpeta o manifiesto en la ruta real
    $ModelPath = Join-Path $OllamaModelsPath "manifests\registry.ollama.ai\library\$FolderModelName"
    
    if (Test-Path $ModelPath) {
        Write-Host "[+] $Model ya se encuentra en el almacenamiento local ($ModelPath)."
    } else {
        Write-Host "[-] $Model no detectado en la ruta. Iniciando descarga (pull)..."
        ollama pull $Model
    }
}

Write-Host "[+] Despliegue completado."
