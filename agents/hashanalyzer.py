import os
import hashlib
import requests
import subprocess
import json
import re
import sys
import time

# ---------------------------------------------------------
# CONFIGURACIÓN DE COLORES (ANSI)
# ---------------------------------------------------------
# Definición de colores para salida en terminal (mejora UX)
C_MAIN = "\033[38;5;34m"      # Verde principal
C_AGENT = "\033[36m"          # Cyan (agente)
C_TOOL = "\033[33m"           # Amarillo (herramientas)
C_SUCCESS = "\033[1;32m"      # Verde brillante (éxito)
C_ERROR = "\033[1;31m"        # Rojo brillante (errores)
C_METRIC = "\033[38;5;141m"   # Morado (métricas)
C_HASH = "\033[1;31m"         # Rojo (hash)
RESET = "\033[0m"             # Reset color

# ---------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------------------------------------
OLLAMA_SERVER = "http://192.168.159.1:11434"  # Endpoint del servidor Ollama
MODELO = "mistral:7b-instruct-q4_K_M"         # Modelo LLM utilizado

# Archivos de entrada/salida
PASSWORDS_FILE = "PASSWORDS.md"   # Archivo con hashes
PLAIN_FILE = "plain.txt"          # Contraseñas en texto plano
NEW_PASSWORDS_FILE = "new_passwords.txt"  # Hashes nuevos con salt

# Diccionario para ataques
WORDLIST = "/usr/share/wordlists/rockyou.txt"

# Modos de hashcat por tipo de hash
HASHCAT_MODES = {
    "md5": "0",
    "sha1": "100",
    "sha256": "1400",
    "sha512": "1700",
    "ntlm": "1000"
}

# Formatos compatibles con John the Ripper
JOHN_FORMATS = {
    "md5": "raw-md5",
    "sha1": "raw-sha1",
    "sha256": "raw-sha256",
    "sha512": "raw-sha512",
    "ntlm": "nt"
}

# ---------------------------------------------------------
# DETECCIÓN DE REGLAS DE HASHCAT
# ---------------------------------------------------------
def obtener_rule():
    """
    Busca reglas de mutación de hashcat en rutas comunes del sistema.

    Las rules permiten generar variaciones de palabras (ej: añadir números,
    cambiar mayúsculas, etc.) aumentando la probabilidad de crackeo.

    Retorna:
        str | None -> Ruta de la rule encontrada o None si no hay
    """
    rutas = [
        "/usr/share/hashcat/rules/rockyou-30000.rule",
        "/usr/share/hashcat/rules/d3ad0ne.rule",
        "/usr/share/hashcat/rules/best64.rule"
    ]
    for r in rutas:
        if os.path.exists(r):
            print(f"{C_MAIN}[INIT] Rule detectada: {r}{RESET}")
            return r

    print(f"{C_TOOL}[WARN] No se encontraron rules de hashcat{RESET}")
    return None

RULES = obtener_rule()

# ---------------------------------------------------------
# VERIFICACIÓN DE OLLAMA
# ---------------------------------------------------------
def verificar_ollama():
    """
    Verifica conectividad con el servidor Ollama y disponibilidad del modelo.

    Retorna:
        bool -> True si el modelo está disponible, False si no
    """
    try:
        r = requests.get(f"{OLLAMA_SERVER}/api/tags", timeout=5)
        modelos = [m["name"] for m in r.json().get("models", [])]

        print(f"{C_MAIN}[DEBUG] Modelos disponibles: {modelos}{RESET}")
        return MODELO in modelos

    except Exception as e:
        print(f"{C_ERROR}[ERROR] No se puede conectar a Ollama: {e}{RESET}")
        return False

# ---------------------------------------------------------
# PARSEO DE RESULTADOS DE HASHCAT
# ---------------------------------------------------------
def parsear_hashcat(hash_valor, hash_mode):
    """
    Recupera la contraseña crackeada desde hashcat (--show).

    Parámetros:
        hash_valor (str): hash original
        hash_mode (str): modo hashcat

    Retorna:
        str | None -> contraseña si se encontró
    """
    result = subprocess.run(
        ["hashcat", "-m", hash_mode, hash_valor, "--show"],
        capture_output=True, text=True
    )

    for line in result.stdout.splitlines():
        if line.lower().startswith(hash_valor.lower() + ":"):
            return line.split(":", 1)[1].strip()

    return None

# ---------------------------------------------------------
# MENSAJE DE ÉXITO
# ---------------------------------------------------------
def mostrar_exito_matrix(hash_valor, tipo, password):
    """
    Muestra un bloque visual indicando que el hash fue resuelto.
    """
    print(f"\n{C_SUCCESS}╔══════════════════════════════════════════════════════════════════════╗")
    print(f"║ [ÉXITO] HASH RESUELTO")
    print(f"║ Hash: {C_HASH}{hash_valor}{C_SUCCESS}")
    print(f"║ Tipo: {tipo.upper()}")
    print(f"║ Password: {password}")
    print(f"╚══════════════════════════════════════════════════════════════════════╝{RESET}\n")

# ---------------------------------------------------------
# HASHCAT - ATAQUE DICCIONARIO
# ---------------------------------------------------------
def hashcat_diccionario(hash_valor, hash_mode, tipo):
    """
    Ejecuta ataque de diccionario puro con hashcat.

    Estrategia:
        - Prueba cada palabra del diccionario sin mutaciones

    Retorna:
        str | None
    """
    print(f"{C_TOOL}[Tool] Ejecutando Hashcat (diccionario) para {tipo.upper()}...{RESET}")
    start_time = time.time()

    try:
        process = subprocess.Popen([
            "hashcat", "-m", hash_mode, "-a", "0",
            hash_valor, WORDLIST,
            "--potfile-disable", "--status", "--status-timer=1"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # Monitor en tiempo real
        for line in iter(process.stdout.readline, ''):
            match = re.search(r'\(\s*(\d+\.\d+)%\s*\)', line)
            if match:
                t = int(time.time() - start_time)
                sys.stdout.write(f"\r{C_TOOL} └─ Progreso: {match.group(1)}% | Tiempo: {t}s {RESET}")
                sys.stdout.flush()

        process.wait()
        print()

        return parsear_hashcat(hash_valor, hash_mode)

    except Exception as e:
        print(f"\n{C_ERROR}[ERROR diccionario] {e}{RESET}")
        return None

# ---------------------------------------------------------
# HASHCAT - ATAQUE CON REGLAS
# ---------------------------------------------------------
def hashcat_reglas(hash_valor, hash_mode, tipo):
    """
    Ejecuta ataque con reglas (mutaciones sobre diccionario).

    Retorna:
        str | None
    """
    if not RULES:
        print(f"{C_TOOL}[SKIP] No hay rules disponibles{RESET}")
        return None

    print(f"{C_TOOL}[Tool] Ejecutando Hashcat (rules) para {tipo.upper()}...{RESET}")
    start_time = time.time()

    try:
        process = subprocess.Popen([
            "hashcat", "-m", hash_mode, "-a", "0",
            hash_valor, WORDLIST,
            "-r", RULES, "--status", "--status-timer=1"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        for line in iter(process.stdout.readline, ''):
            if "No such file" in line:
                print(f"{C_ERROR}[ERROR] Rule inválida{RESET}")
                process.terminate()
                return None

            match = re.search(r'\(\s*(\d+\.\d+)%\s*\)', line)
            if match:
                t = int(time.time() - start_time)
                sys.stdout.write(f"\r{C_TOOL} └─ Progreso: {match.group(1)}% | Tiempo: {t}s {RESET}")
                sys.stdout.flush()

        process.wait()
        print()

        return parsear_hashcat(hash_valor, hash_mode)

    except Exception as e:
        print(f"{C_ERROR}[ERROR rules] {e}{RESET}")
        return None

# ---------------------------------------------------------
# FALLBACK - JOHN THE RIPPER
# ---------------------------------------------------------
def ejecutar_john(hash_valor, tipo):
    """
    Ejecuta John the Ripper como fallback cuando hashcat falla.

    Retorna:
        str | None
    """
    john_format = JOHN_FORMATS.get(tipo.lower(), "raw-md5")
    print(f"{C_TOOL}[Tool] Ejecutando John (formato: {john_format})...{RESET}")

    start_time = time.time()

    try:
        with open("temp_hash.txt", "w") as f:
            f.write(hash_valor)

        process = subprocess.Popen(
            ["john", f"--format={john_format}", "temp_hash.txt"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        while process.poll() is None:
            t = int(time.time() - start_time)
            sys.stdout.write(f"\r{C_TOOL} └─ Analizando... Tiempo: {t}s {RESET}")
            sys.stdout.flush()
            time.sleep(1)

        print()

        result = subprocess.run(
            ["john", "--show", "temp_hash.txt"],
            capture_output=True, text=True
        )

        for line in result.stdout.splitlines():
            if ":" in line and "cracked" not in line.lower():
                return line.split(":", 1)[1].strip()

    except Exception as e:
        print(f"{C_ERROR}[ERROR john] {e}{RESET}")

    return None

# ---------------------------------------------------------
# GENERACIÓN DE HASH SEGURO
# ---------------------------------------------------------
def calcular_sha256_salt(password):
    """
    Genera un nuevo hash SHA256 con salt aleatorio.

    Retorna:
        str -> formato salt:hash
    """
    salt = os.urandom(16).hex()
    hash_val = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hash_val}"

# ---------------------------------------------------------
# LLM - RAZONAMIENTO
# ---------------------------------------------------------
def razonar_con_llm(hash_valor):
    """
    Usa un LLM para inferir:
        - Tipo de hash
        - Estrategia de ataque

    Retorna:
        (list, str)
    """
    prompt = f"""Analiza el hash: {hash_valor} y responde en JSON."""

    try:
        r = requests.post(
            f"{OLLAMA_SERVER}/api/generate",
            json={"model": MODELO, "prompt": prompt, "stream": False},
            timeout=60
        )

        text = r.json().get("response", "")
        match = re.search(r'\{.*?\}', text, re.DOTALL)

        if match:
            obj = json.loads(match.group())
            tipos = obj.get("tipos", ["md5"])
            estrategia = obj.get("strategy", "dictionary")

            print(f"{C_AGENT}[LLM] {obj.get('razonamiento','')}{RESET}")

            return tipos, estrategia

    except Exception as e:
        print(f"{C_ERROR}[ERROR LLM] {e}{RESET}")

    return ["md5"], "dictionary"

# ---------------------------------------------------------
# MOTOR PRINCIPAL DE RESOLUCIÓN
# ---------------------------------------------------------
def resolver_hash(hash_valor):
    """
    Orquesta el proceso completo de cracking:

    1. Consulta LLM
    2. Ejecuta estrategias
    3. Aplica fallback

    Retorna:
        str | None
    """
    print(f"{C_AGENT}[Agente] Analizando hash: {C_HASH}{hash_valor}{RESET}")

    tipos, estrategia = razonar_con_llm(hash_valor)

    for tipo in tipos:
        hash_mode = HASHCAT_MODES.get(tipo.lower(), "0")

        if estrategia == "dictionary":
            p = hashcat_diccionario(hash_valor, hash_mode, tipo)
            if p: return p

            p = hashcat_reglas(hash_valor, hash_mode, tipo)
            if p: return p

        elif estrategia == "rules":
            p = hashcat_reglas(hash_valor, hash_mode, tipo)
            if p: return p

        p = ejecutar_john(hash_valor, tipo)
        if p: return p

    return None

# ---------------------------------------------------------
# FUNCIÓN PRINCIPAL
# ---------------------------------------------------------
def procesar():
    """
    Flujo principal del programa:

    - Lee hashes
    - Ejecuta cracking
    - Guarda resultados
    - Muestra métricas
    """
    global PASSWORDS_FILE, WORDLIST

    os.system('cls' if os.name == 'nt' else 'clear')

    print(f"{C_MAIN}[INIT] Inicializando sistema de cracking{RESET}\n")

    if not verificar_ollama():
        print(f"{C_ERROR}[ERROR] Ollama no disponible{RESET}")
        sys.exit(1)

    if not os.path.exists(PASSWORDS_FILE):
        print(f"{C_ERROR}[ERROR] Archivo no encontrado{RESET}")
        return

    with open(PASSWORDS_FILE) as f:
        hashes = [l.strip() for l in f.readlines()]

    total = len([h for h in hashes if h])
    analizados = 0
    encontrados = 0

    with open(PLAIN_FILE, "w") as f_plain, open(NEW_PASSWORDS_FILE, "w") as f_new:

        for h in hashes:
            if not h:
                continue

            analizados += 1
            password = resolver_hash(h)

            if password:
                encontrados += 1
                f_plain.write(password + "\n")
                f_new.write(calcular_sha256_salt(password) + "\n")

            porcentaje = (analizados / total) * 100
            print(f"{C_METRIC}[PROGRESO] {porcentaje:.2f}% | {encontrados} encontrados{RESET}")

    print(f"{C_MAIN}[FIN] Proceso completado{RESET}")


if __name__ == "__main__":
    procesar()
