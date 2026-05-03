# ByTCJ
# Requiere ejecución con privilegios de Administrador

# 0. Definición de modelos a verificar/instalar
$Models = @(
    "mistral:7b-instruct-q4_K_M",
    "mixtral:8x7b-instruct-q4_K_M",
    "deepseek-coder:6.7b-instruct-q4_K_M"
)

$OllamaUrl = "https://ollama.com/download/OllamaSetup.exe"
$InstallerPath = "$env:TEMP\OllamaSetup.exe"

Write-Host "[*] Iniciando auditoría de entorno y despliegue de modelos..."

# 1. Verificación de binario Ollama
if (Get-Command "ollama" -ErrorAction SilentlyContinue) {
    Write-Host "[+] Binario de Ollama detectado."
} else {
    Write-Host "[-] Ollama no detectado. Procediendo con la instalación..."
    Invoke-WebRequest -Uri $OllamaUrl -OutFile $InstallerPath
    Start-Process -FilePath $InstallerPath -ArgumentList "/SILENT" -Wait -NoNewWindow
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# 2. Configuración de Red y Persistencia
Write-Host "[*] Aplicando configuración OLLAMA_HOST=0.0.0.0..."
Stop-Process -Name "ollama", "ollama app" -Force -ErrorAction SilentlyContinue

$env:OLLAMA_HOST = "0.0.0.0"
[Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0", "User")

# Inicialización del servicio para permitir comunicación con la API
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 5 

# 3. Verificación e Instalación Iterativa de Modelos
$LocalModels = ollama list

foreach ($Model in $Models) {
    Write-Host "[*] Analizando estado de: $Model"
    if ($LocalModels -match $Model) {
        Write-Host "[+] $Model ya se encuentra en el almacenamiento local."
    } else {
        Write-Host "[-] $Model no detectado. Iniciando descarga (pull)..."
        ollama pull $Model
    }
}

# 4. Finalización
Write-Host "[+] Despliegue completado. Modelos listos para inferencia."
Write-Host "[*] Puede verificar el estado con el comando: ollama list"
