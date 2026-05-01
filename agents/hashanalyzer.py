import os
import hashlib
import requests
import subprocess
import json
import re
import sys
import time

# ---------------------------------------------------------
# CONFIGURACIÓN DE COLORES (ANSI) PARA EFECTO MATRIX
# ---------------------------------------------------------
C_MAIN = "\033[38;5;34m"
C_AGENT = "\033[36m"
C_TOOL = "\033[33m"
C_SUCCESS = "\033[1;32m"
C_ERROR = "\033[1;31m"
C_METRIC = "\033[38;5;141m"
C_HASH = "\033[1;31m"
RESET = "\033[0m"

# ---------------------------------------------------------
# CONFIGURACIÓN GENERAL DEL ENTORNO
# ---------------------------------------------------------
OLLAMA_SERVER = "http://192.168.159.1:11434"
MODELO = "mistral:7b-instruct-q4_K_M"

PASSWORDS_FILE = "PASSWORDS.md"
PLAIN_FILE = "plain.txt"
NEW_PASSWORDS_FILE = "new_passwords.txt"
UNRESOLVED_FILE = "hashesnoresueltos.txt"
WORDLIST = "/opt/lab2/realuniq.lst"

LOG_FILE = ""

HASHCAT_MODES = {
    "md5": "0",
    "sha1": "100",
    "sha256": "1400",
    "sha512": "1700",
    "ntlm": "1000"
}

# ---------------------------------------------------------
# FUNCIONALIDAD DE REGISTRO (LOGGING)
# ---------------------------------------------------------
def escribir_log(mensaje, es_error=False):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    prefijo = "[ERROR]" if es_error else "[INFO]"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{timestamp} {prefijo} {mensaje}\n")
    except Exception:
        pass

# ---------------------------------------------------------
# VERIFICACIÓN DE IA (OLLAMA)
# ---------------------------------------------------------
def verificar_ollama():
    try:
        r = requests.get(f"{OLLAMA_SERVER}/api/tags", timeout=5)
        modelos = [m["name"] for m in r.json().get("models", [])]
        print(f"{C_MAIN}[DEPURACIÓN] Modelos de IA detectados: {modelos}{RESET}")
        return MODELO in modelos
    except Exception as e:
        print(f"{C_ERROR}[ERROR FATAL] No se pudo establecer conexión con Ollama: {e}{RESET}")
        escribir_log(f"Fallo de conexión con Ollama: {e}", es_error=True)
        return False

# ---------------------------------------------------------
# FUNCIONES AUXILIARES DE PARSEO Y VISUALIZACIÓN
# ---------------------------------------------------------
def parsear_hashcat_masivo(hash_mode, archivo_hashes, hashes_crudos):
    resuel_hashes = {}
    try:
        result = subprocess.run(
            ["hashcat", "-m", hash_mode, archivo_hashes, "--show", "--quiet"],
            capture_output=True, text=True
        )
        
        for line in result.stdout.splitlines():
            for hash_valor in hashes_crudos:
                if not hash_valor:
                    continue
                if line.lower().startswith(hash_valor.lower() + ":"):
                    password = line.split(":", 1)[1].strip()
                    resuel_hashes[hash_valor.lower()] = password
                    break
                    
    except Exception as e:
        escribir_log(f"Error en parseo masivo para el modo {hash_mode}: {e}", es_error=True)
        
    return resuel_hashes

def mostrar_exito_matrix(hash_valor, tipo, password):
    print(f"\n{C_SUCCESS}╔══════════════════════════════════════════════════════════════════════╗")
    print(f"║ [TERMINAL DE ESTADO] DESCIFRADO EXITOSO")
    print(f"║ El Hash {C_HASH}{hash_valor}{C_SUCCESS}, tipo \"{tipo.upper()}\" corresponde a: {password}")
    print(f"╚══════════════════════════════════════════════════════════════════════╝{RESET}\n")

# ---------------------------------------------------------
# HERRAMIENTAS DE AUDITORÍA CON MONITOREO
# ---------------------------------------------------------
def ejecutar_hashcat_masivo(hash_mode):
    comando_args = [
        "hashcat", "-m", hash_mode, "-a", "0",
        PASSWORDS_FILE, WORDLIST,
        "--restore-disable", "--force"
    ]
    
    print(f"{C_TOOL}[Herramienta] Ejecutando comando subyacente: {' '.join(comando_args)}{RESET}")
    
    try:
        process = subprocess.Popen(
            comando_args, 
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True
        )

        for line in iter(process.stdout.readline, ''):
            clean_line = line.strip()
            if not clean_line:
                continue
            
            escribir_log(f"[Hashcat LOG] {clean_line}")
            print(f"{C_METRIC}[Hashcat RAW] {clean_line}{RESET}")

        process.wait()
        print() 
    except Exception as e:
        print(f"\n{C_ERROR}[ERROR Lote] Excepción detectada: {e}{RESET}")
        escribir_log(f"Error en Hashcat Masivo: {e}", es_error=True)

# ---------------------------------------------------------
# RE-HASHING DE SEGURIDAD (MODIFICADO)
# ---------------------------------------------------------
def calcular_nuevo_hash(password):
    """
    Genera un hash SHA-256 puro a partir de la contraseña plana.
    Se elimina la concatenación del 'Salt' para cumplir con el formato estricto
    y evitar confusiones visuales con los hashes originales.
    """
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------------------------------------------
# LÓGICA COGNITIVA DEL AGENTE LLM (CONTROL DETERMINISTA ESTRICTO)
# ---------------------------------------------------------
def razonar_con_llm_masivo(hashes_crudos):
    longitudes = {len(h) for h in hashes_crudos if h}
    
    algoritmos_sugeridos = []
    if any(l == 32 for l in longitudes):
        algoritmos_sugeridos.append("md5")
    if any(l == 40 for l in longitudes):
        algoritmos_sugeridos.append("sha1")
    if any(l == 64 for l in longitudes):
        algoritmos_sugeridos.append("sha256")
    if any(l == 128 for l in longitudes):
        algoritmos_sugeridos.append("sha512")
    
    if not algoritmos_sugeridos:
        algoritmos_sugeridos = ["md5"] 

    prompt = f"""
Eres un agente experto en ciberseguridad. Analiza el siguiente lote de hashes:
{json.dumps([h for h in hashes_crudos if h][:10])} (Muestra limitada)

INSTRUCCIONES OBLIGATORIAS:
1. Python ya determinó matemáticamente que los algoritmos a utilizar son: {json.dumps(algoritmos_sugeridos)}. Da una explicacion detallada de porque se produce esto
2. Basado en la longitud, determina la lista de algoritmos posibles según las reglas. 
3. Elige la estrategia ("dictionary", "rules"). 
4. Explica lógicamente tu análisis. Si es ambiguo (32 chars), indícalo explícitamente.
5. Responder siempre en español jamas en otro idioma.

Responde EXCLUSIVAMENTE con la siguiente estructura JSON, reemplazando el contenido entre los signos <> por tu propia generación:
{{
  "herramienta": "hashcat",
  "strategy": "<dictionary o rules>",
  "razonamiento": "<Genera aquí tu reporte analítico bien detallado. Analiza la muestra y justifica técnica y operativamente tu decisión, analiza tipo de hashes y propuestas con HashCat si el analisis indica que se puede usar para la resolucion.>"
}}
"""
    try:
        r = requests.post(
            f"{OLLAMA_SERVER}/api/generate",
            json={"model": MODELO, "prompt": prompt, "stream": False},
            timeout=60
        )
        data = r.json()
        text = data.get("response", "")
        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if match:
            obj = json.loads(match.group())
            
            tipos = algoritmos_sugeridos
            estrategia = obj.get("strategy", "dictionary")
            herramienta = obj.get("herramienta", "hashcat")
            razonamiento = obj.get("razonamiento", "Procesamiento estándar según longitud.")
            
            print(f"{C_AGENT}[Agente LLM] Razonamiento analítico: {razonamiento}{RESET}")
            print(f"{C_AGENT}[Agente LLM] Herramienta designada: {herramienta.upper()}{RESET}")
            
            return tipos, estrategia
    except Exception:
        pass
    
    return algoritmos_sugeridos, "dictionary"

# ---------------------------------------------------------
# BUCLE PRINCIPAL (PUNTO DE ENTRADA)
# ---------------------------------------------------------
def procesar():
    global PASSWORDS_FILE, WORDLIST, LOG_FILE
    os.system('cls' if os.name == 'nt' else 'clear')

    print(f"{C_MAIN}╔════════════════════════════════════════╗")
    print(f"║    INICIANDO AGENTE DE ANALISIS DE IA    ║")
    print(f"╚════════════════════════════════════════╝{RESET}\n")

    arch_in = input(f"Archivo de volcado de hashes (Presione Enter para '{PASSWORDS_FILE}'): ").strip()
    if arch_in:
        PASSWORDS_FILE = arch_in

    LOG_FILE = f"{PASSWORDS_FILE}.log"
    escribir_log(f"--- SESIÓN INICIADA: Analizando {PASSWORDS_FILE} ---")

    print(f"\nConfiguración del Wordlist:")
    print(f"1) Usar diccionario del sistema operativo ({WORDLIST})")
    print(f"2) Definir una ruta personalizada absoluta")
    opc = input(f"Seleccione (1 o 2): ").strip()
    
    if opc == "2":
        dict_in = input(f"Ruta absoluta al diccionario: ").strip()
        if os.path.exists(dict_in):
            WORDLIST = dict_in
        else:
            print(f"{C_TOOL}[ADVERTENCIA] Archivo no detectado. Revirtiendo al valor por defecto: {WORDLIST}{RESET}")
    
    print(f"\n{C_MAIN}=========================================={RESET}")

    if not verificar_ollama():
        sys.exit(1)

    if not os.path.exists(PASSWORDS_FILE):
        print(f"{C_ERROR}[ERROR FATAL] El documento '{PASSWORDS_FILE}' no se encuentra en el directorio.{RESET}")
        sys.exit(1)

    with open(PASSWORDS_FILE) as f:
        hashes_crudos = [l.strip() for l in f.readlines()]

    print(f"{C_AGENT}[Agente] Razonando sobre el lote masivo...{RESET}")
    tipos, estrategia = razonar_con_llm_masivo(hashes_crudos)

    print(f"{C_AGENT}[Agente] Estrategia masiva confirmada -> Algoritmos: {tipos} | Modo: {estrategia}{RESET}")

    hashes_resueltos_global = {}

    for tipo in tipos:
        hash_mode = HASHCAT_MODES.get(tipo.lower(), "0")
        ejecutar_hashcat_masivo(hash_mode)
        
        resultados_lote = parsear_hashcat_masivo(hash_mode, PASSWORDS_FILE, hashes_crudos)
        
        for h_lower, pwd in resultados_lote.items():
            if h_lower not in hashes_resueltos_global:
                hashes_resueltos_global[h_lower] = (pwd, tipo)

    encontrados = 0
    total_validos = sum(1 for h in hashes_crudos if h)

    # Escritura mapeada 1:1 con el archivo de origen (línea por línea)
    with open(PLAIN_FILE, "w") as f_plain, open(NEW_PASSWORDS_FILE, "w") as f_new, open(UNRESOLVED_FILE, "w") as f_unres:
        for h in hashes_crudos:
            if not h:
                f_plain.write("\n")
                f_new.write("\n")
                continue

            h_lower = h.lower()
            if h_lower in hashes_resueltos_global:
                pwd, tipo = hashes_resueltos_global[h_lower]
                mostrar_exito_matrix(h, tipo, pwd)
                
                f_plain.write(pwd + "\n")
                # Se utiliza la función modificada para grabar solo el SHA-256
                f_new.write(calcular_nuevo_hash(pwd) + "\n")
                
                escribir_log(f"RESUELTO: {h} -> {pwd} (Modo: {tipo})")
                encontrados += 1
            else:
                f_plain.write("\n")
                f_new.write("\n")
                f_unres.write(h + "\n")
                escribir_log(f"FALLIDO: {h}", es_error=True)

    print(f"\n{C_MAIN}[SISTEMA] SECUENCIA DE AUDITORÍA FINALIZADA. Compromisos totales: {encontrados} / {total_validos}{RESET}")
    escribir_log("--- SESIÓN FINALIZADA ---")

if __name__ == "__main__":
    procesar()
