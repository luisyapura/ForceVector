# ByTCJ
# Requiere ejecución con privilegios de Administrador

$ModelName = "mistral:7b-instruct-q4_K_M"
$OllamaUrl = "https://ollama.com/download/OllamaSetup.exe"
$InstallerPath = "$env:TEMP\OllamaSetup.exe"

Write-Host "[*] Iniciando proceso de verificación y despliegue..."

# 1. Verificación e Instalación del binario de Ollama
if (Get-Command "ollama" -ErrorAction SilentlyContinue) {
    Write-Host "[+] Ollama ya se encuentra instalado en el sistema. Omitiendo descarga."
} else {
    Write-Host "[-] Ollama no detectado. Iniciando descarga del instalador..."
    Invoke-WebRequest -Uri $OllamaUrl -OutFile $InstallerPath
    
    Write-Host "[*] Ejecutando instalación silenciosa..."
    Start-Process -FilePath $InstallerPath -ArgumentList "/SILENT" -Wait -NoNewWindow
    
    # Actualizar el PATH en la sesión actual para reconocer el comando inmediatamente
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# 2. Reconfiguración de Red (0.0.0.0)
Write-Host "[*] Deteniendo instancias previas de Ollama para aplicar nueva configuración de red..."
Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "ollama app" -Force -ErrorAction SilentlyContinue

Write-Host "[*] Configurando OLLAMA_HOST a 0.0.0.0..."
# Variable temporal para la sesión actual
$env:OLLAMA_HOST = "0.0.0.0"
# Variable persistente para el usuario
[Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0", "User")

# 3. Inicialización del Servidor
Write-Host "[*] Levantando el servicio Ollama en 0.0.0.0..."
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 5 # Tiempo técnico requerido para la apertura del socket

# 4. Verificación y Descarga del Modelo
Write-Host "[*] Verificando la existencia del modelo local: $ModelName..."
# Se captura la salida del comando list para buscar coincidencias
$InstalledModels = ollama list
if ($InstalledModels -match $ModelName) {
    Write-Host "[+] El modelo $ModelName ya está presente en el almacenamiento local. Omitiendo 'pull'."
} else {
    Write-Host "[-] El modelo no se encuentra. Iniciando descarga (pull)..."
    ollama pull $ModelName
}

# 5. Ejecución
Write-Host "[*] Ejecutando el modelo interactivo..."
ollama run $ModelName
