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
# Se definen los códigos de escape ANSI para dar formato y color a la terminal.
C_MAIN = "\033[38;5;34m"     # Verde oscuro clásico (texto general y estructura)
C_AGENT = "\033[36m"         # Cian (identifica el razonamiento de la IA y el Agente)
C_TOOL = "\033[33m"          # Amarillo (identifica la ejecución y avance de herramientas)
C_SUCCESS = "\033[1;32m"     # Verde brillante (resalta los descifrados exitosos)
C_ERROR = "\033[1;31m"       # Rojo (resalta fallos, excepciones o reglas inválidas)
C_METRIC = "\033[38;5;141m"  # Púrpura suave (estadísticas de avance global)
C_HASH = "\033[1;31m"        # Rojo brillante en negrita (resalta el hash en pantalla)
RESET = "\033[0m"            # Restablece el color de la terminal a su valor por defecto

# ---------------------------------------------------------
# CONFIGURACIÓN GENERAL DEL ENTORNO
# ---------------------------------------------------------
# Parámetros de conexión con la API local de Ollama
OLLAMA_SERVER = "http://192.168.159.1:11434"
MODELO = "mistral:7b-instruct-q4_K_M"

# Archivos de entrada y salida por defecto
PASSWORDS_FILE = "PASSWORDS.md"            # Archivo fuente con los hashes a auditar
PLAIN_FILE = "plain.txt"                   # Salida de contraseñas rotas en texto plano
NEW_PASSWORDS_FILE = "new_passwords.txt"   # Salida de contraseñas re-hasheadas (SHA256+Salt)
WORDLIST = "/usr/share/wordlists/rockyou.txt" # Ruta por defecto del diccionario base en Kali Linux

# Mapeo de identificadores de algoritmos requeridos por el binario Hashcat (-m)
HASHCAT_MODES = {
    "md5": "0",
    "sha1": "100",
    "sha256": "1400",
    "sha512": "1700",
    "ntlm": "1000"
}

# Mapeo de formatos descriptivos requeridos por el binario John the Ripper (--format)
JOHN_FORMATS = {
    "md5": "raw-md5",
    "sha1": "raw-sha1",
    "sha256": "raw-sha256",
    "sha512": "raw-sha512",
    "ntlm": "nt"
}

# ---------------------------------------------------------
# DETECCIÓN DINÁMICA DE REGLAS (RULES)
# ---------------------------------------------------------
def obtener_rule():
    """
    Busca archivos de reglas de mutación estándar de Hashcat en el sistema.
    Retorna la ruta absoluta del primer archivo de reglas disponible para usar en ataques.
    """
    rutas = [
        "/usr/share/hashcat/rules/rockyou-30000.rule",
        "/usr/share/hashcat/rules/d3ad0ne.rule",
        "/usr/share/hashcat/rules/best64.rule"
    ]
    for r in rutas:
        if os.path.exists(r):
            print(f"{C_MAIN}[INICIO] Regla de mutación detectada: {r}{RESET}")
            return r
    print(f"{C_TOOL}[ADVERTENCIA] No se encontraron reglas de Hashcat en las rutas estándar.{RESET}")
    return None

# Instancia global de la regla a utilizar durante toda la ejecución
RULES = obtener_rule()

# ---------------------------------------------------------
# VERIFICACIÓN DE IA (OLLAMA)
# ---------------------------------------------------------
def verificar_ollama():
    """
    Comprueba si el servidor local de Ollama responde a peticiones HTTP
    y si el modelo requerido se encuentra descargado en la máquina host.
    """
    try:
        r = requests.get(f"{OLLAMA_SERVER}/api/tags", timeout=5)
        modelos = [m["name"] for m in r.json().get("models", [])]
        print(f"{C_MAIN}[DEPURACIÓN] Modelos de IA detectados: {modelos}{RESET}")
        return MODELO in modelos
    except Exception as e:
        print(f"{C_ERROR}[ERROR FATAL] No se pudo establecer conexión con Ollama: {e}{RESET}")
        return False

# ---------------------------------------------------------
# FUNCIONES AUXILIARES DE PARSEO
# ---------------------------------------------------------
def parsear_hashcat(hash_valor, hash_mode):
    """
    Extrae la contraseña en texto plano desde el potfile interno de Hashcat.
    Se lee la salida estándar mediante subprocesos y se filtra línea por línea.
    """
    result = subprocess.run(
        ["hashcat", "-m", hash_mode, hash_valor, "--show"],
        capture_output=True, text=True
    )
    
    for line in result.stdout.splitlines():
        # Búsqueda estricta: la línea debe iniciar obligatoriamente con el hash (evita falsos positivos de errores)
        if line.lower().startswith(hash_valor.lower() + ":"):
            return line.split(":", 1)[1].strip()
            
    return None

def mostrar_exito_matrix(hash_valor, tipo, password):
    """
    Renderiza un recuadro visual en la terminal para notificar un éxito al descifrar,
    manteniendo la paleta de colores y el formato solicitado.
    """
    print(f"\n{C_SUCCESS}╔══════════════════════════════════════════════════════════════════════╗")
    print(f"║ [TERMINAL DE ESTADO] DESCIFRADO EXITOSO")
    print(f"║ El Hash {C_HASH}{hash_valor}{C_SUCCESS}, tipo \"{tipo.upper()}\" corresponde a: {password}")
    print(f"╚══════════════════════════════════════════════════════════════════════╝{RESET}\n")

# ---------------------------------------------------------
# HERRAMIENTAS DE AUDITORÍA CON MONITOREO
# ---------------------------------------------------------
def hashcat_diccionario(hash_valor, hash_mode, tipo):
    """
    (Fase 1) Ejecuta un ataque de diccionario puro (comparación 1:1) sin mutaciones.
    El parámetro --status-timer=1 obliga a Hashcat a emitir el avance por consola.
    """
    print(f"{C_TOOL}[Herramienta] Iniciando Hashcat (Diccionario) para el tipo {tipo.upper()}...{RESET}")
    start_time = time.time()
    try:
        process = subprocess.Popen([
            "hashcat", "-m", hash_mode, "-a", "0",
            hash_valor, WORDLIST,
            "--potfile-disable", "--status", "--status-timer=1"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # Iteración sobre el buffer de salida estándar (stdout) en tiempo real
        for line in iter(process.stdout.readline, ''):
            # Extracción del porcentaje con una expresión regular
            match = re.search(r'\(\s*(\d+\.\d+)%\s*\)', line)
            if match:
                t = int(time.time() - start_time)
                # '\r' sobrescribe la línea actual en la terminal, creando el efecto de actualización
                sys.stdout.write(f"\r{C_TOOL} └─ [SISTEMA] Motor: Hashcat Diccionario | Avance: {match.group(1)}% | Tiempo: {t}s {RESET}  ")
                sys.stdout.flush()

        process.wait()
        print() # Salto de línea para limpiar la salida de la terminal
        return parsear_hashcat(hash_valor, hash_mode)

    except Exception as e:
        print(f"\n{C_ERROR}[ERROR diccionario] Excepción detectada: {e}{RESET}")
        return None

def hashcat_reglas(hash_valor, hash_mode, tipo):
    """
    (Fase 2) Ejecuta un ataque combinando el diccionario con reglas de mutación complejas.
    Se utiliza si el ataque de diccionario primario es evadido.
    """
    if not RULES:
        print(f"{C_TOOL}[OMITIDO] No existen reglas de mutación configuradas en el sistema.{RESET}")
        return None

    print(f"{C_TOOL}[Herramienta] Iniciando Hashcat (Reglas) para el tipo {tipo.upper()}...{RESET}")
    start_time = time.time()
    try:
        process = subprocess.Popen([
            "hashcat", "-m", hash_mode, "-a", "0",
            hash_valor, WORDLIST,
            "-r", RULES, "--status", "--status-timer=1"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        for line in iter(process.stdout.readline, ''):
            # Captura un error fatal interno de Hashcat si la regla declarada no se puede leer
            if "No such file" in line:
                print(f"\n{C_ERROR}[ERROR] El archivo de reglas es inválido o corrupto.{RESET}")
                process.terminate()
                return None
                
            match = re.search(r'\(\s*(\d+\.\d+)%\s*\)', line)
            if match:
                t = int(time.time() - start_time)
                sys.stdout.write(f"\r{C_TOOL} └─ [SISTEMA] Motor: Hashcat Reglas | Avance: {match.group(1)}% | Tiempo: {t}s {RESET}  ")
                sys.stdout.flush()

        process.wait()
        print()
        return parsear_hashcat(hash_valor, hash_mode)

    except Exception as e:
        print(f"\n{C_ERROR}[ERROR reglas] Excepción detectada: {e}{RESET}")
        return None

def ejecutar_john(hash_valor, tipo):
    """
    (Fase 3 - Respaldo) Delega la tarea a John the Ripper.
    Como JtR no emite progreso continuo sin una TTY interactiva, se provee
    una salida visual ('Analizando...') y un contador de tiempo transcurrido en segundos.
    """
    john_format = JOHN_FORMATS.get(tipo.lower(), "raw-md5")
    print(f"{C_TOOL}[Herramienta] Iniciando Motor de Respaldo John the Ripper (Formato: {john_format})...{RESET}")
    start_time = time.time()
    try:
        # Se requiere generar un fichero temporal con el hash para que John lo procese
        with open("temp_hash.txt", "w") as f:
            f.write(hash_valor)

        process = subprocess.Popen(
            ["john", f"--format={john_format}", "temp_hash.txt"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Bucle de espera activa midiendo el tiempo de ejecución de John
        while process.poll() is None:
            t = int(time.time() - start_time)
            sys.stdout.write(f"\r{C_TOOL} └─ [SISTEMA] Motor: John | Avance: Analizando... | Tiempo: {t}s {RESET}  ")
            sys.stdout.flush()
            time.sleep(1) # Intervalo de actualización en la terminal
        print()

        # Validación del potfile interno de John
        result = subprocess.run(
            ["john", "--show", "temp_hash.txt"],
            capture_output=True, text=True
        )

        # Filtro estricto para extraer solo el hash resuelto y no la metadata generada
        for line in result.stdout.splitlines():
            if ":" in line and "password hashes cracked" not in line and "error" not in line.lower():
                return line.split(":", 1)[1].strip()

    except Exception as e:
        print(f"\n{C_ERROR}[ERROR john] Excepción detectada: {e}{RESET}")

    return None

# ---------------------------------------------------------
# RE-HASHING DE SEGURIDAD
# ---------------------------------------------------------
def calcular_sha256_salt(password):
    """
    Genera un nuevo hash moderno y seguro (SHA-256) combinando la contraseña
    descubierta con un salt criptográfico de 16 bytes (mitigación de Rainbow Tables).
    """
    salt = os.urandom(16).hex()
    hash_val = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hash_val}"

# ---------------------------------------------------------
# LÓGICA COGNITIVA DEL AGENTE LLM (HÍBRIDA DETERMINISTA)
# ---------------------------------------------------------
def razonar_con_llm(hash_valor):
    """
    Función central del agente. Calcula la longitud del hash vía Python (O(1)) para evitar 
    alucinaciones matemáticas del LLM. Se proporcionan las instrucciones de análisis y se exige
    la respuesta estrictamente en JSON y en español.
    """
    longitud_real = len(hash_valor)
    
    # Mapeo inmutable de algoritmos probables según la longitud de la cadena
    if longitud_real == 32:
        algoritmos_posibles = '["md5", "ntlm"]'
    elif longitud_real == 40:
        algoritmos_posibles = '["sha1"]'
    elif longitud_real == 64:
        algoritmos_posibles = '["sha256"]'
    elif longitud_real == 128:
        algoritmos_posibles = '["sha512"]'
    else:
        algoritmos_posibles = '["desconocido"]'

    # Prompt instruccional con las inyecciones directas solicitadas por el usuario
    prompt = f"""
Eres un agente experto en ciberseguridad. Analiza el hash: {hash_valor}

INSTRUCCIONES OBLIGATORIAS:
1. Cuenta los caracteres exactos del hash proporcionado. 
2. Basado en la longitud, determina la lista de algoritmos posibles según las reglas. 
3. Elige la estrategia ("dictionary", "rules", "fallback_john"). 
4. Explica lógicamente tu análisis. Si es ambiguo (32 chars), indícalo explícitamente.
5. Responder siempre en español jamas en otro idioma.

Responde ÚNICAMENTE en formato JSON estricto respetando este esquema:
{{"tipos": {algoritmos_posibles}, "strategy": "dictionary", "razonamiento": "Al contar los caracteres, el hash posee {longitud_real} posiciones..."}}
"""
    try:
        r = requests.post(
            f"{OLLAMA_SERVER}/api/generate",
            json={"model": MODELO, "prompt": prompt, "stream": False},
            timeout=60
        )

        data = r.json()
        text = data.get("response", "")
        
        # Parseo seguro buscando llaves de apertura y cierre
        match = re.search(r'\{.*?\}', text, re.DOTALL)

        if match:
            json_limpio = match.group()
            obj = json.loads(json_limpio)
            
            # Se aplica fallback a la lógica de Python si la IA altera la lista de tipos
            tipos = obj.get("tipos", json.loads(algoritmos_posibles))
            estrategia = obj.get("strategy", obj.get("estrategia", "diccionario"))
            razonamiento = obj.get("razonamiento", "Sin justificación provista por el modelo.")
            
            print(f"{C_AGENT}[Agente LLM] Razonamiento lógico: {razonamiento}{RESET}")
            
            return tipos, estrategia

    except Exception as e:
        print(f"{C_ERROR}[ERROR LLM] Fallo en la comunicación de inferencia: {e}{RESET}")

    # Retorno en modo seguro si el servidor LLM está caído temporalmente
    return json.loads(algoritmos_posibles), "diccionario"

# ---------------------------------------------------------
# ORQUESTADOR TÁCTICO
# ---------------------------------------------------------
def resolver_hash(hash_valor):
    """
    Implementa la cascada de ejecución. Itera sobre los algoritmos posibles
    y escala automáticamente de Diccionario a Reglas, respetando la estrategia 
    inicial dictaminada por la inteligencia artificial.
    """
    print(f"\n{C_MAIN}──────────────────────────────────────────────────────────────────{RESET}")
    print(f"{C_AGENT}[Agente] Procesando hash objetivo: {C_HASH}{hash_valor}{RESET}")

    tipos, estrategia = razonar_con_llm(hash_valor)
    
    # Estandarización de formato para prevenir errores si la IA devuelve un string en vez de array
    if isinstance(tipos, str):
        tipos = [tipos]
        
    tipos_str = ", ".join(tipos).upper()

    # Traducción de la variable en inglés devuelta por la IA (por la directiva "dictionary") a español visual
    mapa_traduccion = {
        "dictionary": "diccionario",
        "rules": "reglas",
        "fallback_john": "respaldo_john"
    }
    estrategia_visual = mapa_traduccion.get(estrategia.lower(), estrategia)

    print(f"{C_AGENT}[Agente] Estrategia definida -> Tipos Posibles: {tipos_str} | Ataque Inicial: {estrategia_visual.upper()}{RESET}")

    for tipo in tipos:
        hash_mode = HASHCAT_MODES.get(tipo.lower(), "0")
        print(f"\n{C_AGENT}[Agente] ---> Ejecutando secuencia técnica para el algoritmo: {tipo.upper()}{RESET}")

        # Bloque de ejecución principal, tolerante a llaves en inglés o español por seguridad
        if estrategia.lower() in ["dictionary", "diccionario"]:
            p = hashcat_diccionario(hash_valor, hash_mode, tipo)
            if p:
                mostrar_exito_matrix(hash_valor, tipo, p)
                return p
            
            # Comportamiento automático: Escalada de privilegios a reglas si el diccionario es ineficaz
            print(f"{C_AGENT}[Agente] Diccionario simple evadido. Escalando ataque a permutación por reglas...{RESET}")
            p = hashcat_reglas(hash_valor, hash_mode, tipo)
            if p:
                mostrar_exito_matrix(hash_valor, tipo, p)
                return p

        elif estrategia.lower() in ["rules", "reglas"]:
            p = hashcat_reglas(hash_valor, hash_mode, tipo)
            if p:
                mostrar_exito_matrix(hash_valor, tipo, p)
                return p

        # Bloque de contingencia si los motores primarios fallan
        print(f"{C_AGENT}[Agente] Motores principales evadidos. Desviando ejecución al motor de respaldo (John the Ripper)...{RESET}")
        p = ejecutar_john(hash_valor, tipo)
        if p:
            mostrar_exito_matrix(hash_valor, tipo, p)
            return p

    return None

# ---------------------------------------------------------
# BUCLE PRINCIPAL (PUNTO DE ENTRADA)
# ---------------------------------------------------------
def procesar():
    """
    Controla el flujo maestro del sistema: interactúa con el usuario, valida la integridad 
    de los archivos necesarios, calcula métricas e invoca al orquestador (resolver_hash).
    Aplica técnicas de fsync para asegurar la integridad de datos en el sistema de archivos.
    """
    global PASSWORDS_FILE, WORDLIST

    # Limpia la terminal según el sistema operativo (Windows/Linux) para efecto visual
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"{C_MAIN}╔════════════════════════════════════════╗")
    print(f"║   INICIANDO AGENTE DE ANALISIS DE IA   ║")
    print(f"╚════════════════════════════════════════╝{RESET}\n")

    # Obtención dinámica de rutas y configuración de usuario
    arch_in = input(f"Archivo de volcado de hashes (Presione Enter para '{PASSWORDS_FILE}'): ").strip()
    if arch_in:
        PASSWORDS_FILE = arch_in

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

    # Validación de dependencias críticas antes de iniciar procesos pesados
    if not verificar_ollama():
        print(f"{C_ERROR}[ERROR FATAL] La conexión con el LLM local ha sido rechazada.{RESET}")
        sys.exit(1)

    if not os.path.exists(PASSWORDS_FILE):
        print(f"{C_ERROR}[ERROR FATAL] El documento '{PASSWORDS_FILE}' no se encuentra en el directorio.{RESET}")
        return

    # Extracción de las cadenas objetivo en la memoria principal
    with open(PASSWORDS_FILE) as f:
        hashes_crudos = [l.strip() for l in f.readlines()]
        
    # Inicialización de contadores estadísticos
    total_validos = sum(1 for h in hashes_crudos if h)
    analizados = 0
    encontrados = 0

    with open(PLAIN_FILE, "w") as f_plain, open(NEW_PASSWORDS_FILE, "w") as f_new:

        for h in hashes_crudos:
            # Preservación de líneas y espacios en blanco de los archivos origen
            if not h:
                f_plain.write("\n")
                f_new.write("\n")
                f_plain.flush()
                f_new.flush()
                os.fsync(f_plain.fileno())
                os.fsync(f_new.fileno())
                continue

            analizados += 1
            
            # Llamada síncrona al orquestador para resolución del hash actual
            password = resolver_hash(h)

            if password:
                encontrados += 1
                f_plain.write(password + "\n")
                f_new.write(calcular_sha256_salt(password) + "\n")
            else:
                print(f"{C_ERROR}[FALLO DE AUDITORÍA] No se logró comprometer el hash: {C_HASH}{h}{RESET}")
                f_plain.write("\n")
                f_new.write("\n")

            # Cálculo en coma flotante del porcentaje total procesado
            porcentaje = (analizados / total_validos) * 100
            print(f"{C_METRIC}[MÉTRICAS GLOBALES] Progreso de Lote: {porcentaje:.2f}% | Hashes Auditados: {analizados}/{total_validos} | Compromisos: {encontrados}{RESET}")

            # Forzado estricto al búfer del kernel del SO para escribir físicamente en disco
            f_plain.flush()
            f_new.flush()
            os.fsync(f_plain.fileno())
            os.fsync(f_new.fileno())

    print(f"\n{C_MAIN}[SISTEMA] SECUENCIA DE AUDITORÍA FINALIZADA.{RESET}")

if __name__ == "__main__":
    procesar()
