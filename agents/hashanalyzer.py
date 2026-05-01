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
C_MAIN = "\033[38;5;34m"     # Verde oscuro clásico (texto general)
C_AGENT = "\033[36m"         # Cian (identifica las acciones de la IA y el Agente)
C_TOOL = "\033[33m"          # Amarillo (identifica la ejecución de herramientas externas)
C_SUCCESS = "\033[1;32m"     # Verde brillante (resalta los descifrados exitosos)
C_ERROR = "\033[1;31m"       # Rojo (resalta fallos o excepciones)
C_METRIC = "\033[38;5;141m"  # Púrpura suave (estadísticas y porcentajes)
C_HASH = "\033[1;31m"        # Rojo brillante en negrita (resalta el hash en pantalla)
RESET = "\033[0m"            # Restablece el color de la terminal a su valor por defecto

# ---------------------------------------------------------
# CONFIGURACIÓN GENERAL DEL ENTORNO
# ---------------------------------------------------------
# Parámetros de conexión con la API local de Ollama
OLLAMA_SERVER = "http://192.168.159.1:11434"
MODELO = "mistral:7b-instruct-q4_K_M"

# Archivos de entrada y salida por defecto
PASSWORDS_FILE = "PASSWORDS.md"            # Archivo que contiene los hashes a romper
PLAIN_FILE = "plain.txt"                   # Archivo donde se guardan las contraseñas en texto plano
NEW_PASSWORDS_FILE = "new_passwords.txt"   # Archivo donde se guardan las contraseñas hasheadas en SHA256+Salt
WORDLIST = "/usr/share/wordlists/rockyou.txt" # Ruta por defecto del diccionario

# Mapeo de identificadores de algoritmos para Hashcat
HASHCAT_MODES = {
    "md5": "0",
    "sha1": "100",
    "sha256": "1400",
    "sha512": "1700",
    "ntlm": "1000"
}

# Mapeo de formatos requeridos por John the Ripper
JOHN_FORMATS = {
    "md5": "raw-md5",
    "sha1": "raw-sha1",
    "sha256": "raw-sha256",
    "sha512": "raw-sha512",
    "ntlm": "nt"
}

# ---------------------------------------------------------
# DETECCIÓN DINÁMICA DE REGLAS (RULES) DE HASHCAT
# ---------------------------------------------------------
def obtener_rule():
    """
    Busca reglas de mutación comunes de Hashcat en el sistema.
    Retorna la ruta absoluta de la primera regla que encuentre disponible.
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

# Variable global que almacena la ruta de la regla detectada
RULES = obtener_rule()

# ---------------------------------------------------------
# VERIFICACIÓN DE IA (OLLAMA)
# ---------------------------------------------------------
def verificar_ollama():
    """
    Comprueba si el servidor de Ollama está activo y si el modelo especificado
    se encuentra descargado y disponible en el entorno local.
    """
    try:
        # Petición a la API para listar los modelos instalados
        r = requests.get(f"{OLLAMA_SERVER}/api/tags", timeout=5)
        modelos = [m["name"] for m in r.json().get("models", [])]
        print(f"{C_MAIN}[DEPURACIÓN] Modelos de IA disponibles: {modelos}{RESET}")
        
        # Retorna True si el modelo objetivo está en la lista
        return MODELO in modelos
    except Exception as e:
        print(f"{C_ERROR}[ERROR] No se pudo establecer conexión con Ollama: {e}{RESET}")
        return False

# ---------------------------------------------------------
# FUNCIONES AUXILIARES (HELPERS) DE PARSEO
# ---------------------------------------------------------
def parsear_hashcat(hash_valor, hash_mode):
    """
    Consulta la base de datos de contraseñas rotas (potfile) de Hashcat
    utilizando el comando '--show'. Busca una coincidencia estricta para evitar falsos positivos.
    """
    result = subprocess.run(
        ["hashcat", "-m", hash_mode, hash_valor, "--show"],
        capture_output=True, text=True
    )
    
    # Se analiza línea por línea para evitar tomar errores del binario como contraseñas
    for line in result.stdout.splitlines():
        if line.lower().startswith(hash_valor.lower() + ":"):
            # Si la línea empieza con el hash, se extrae el texto plano ubicado después de los dos puntos
            return line.split(":", 1)[1].strip()
            
    return None

def mostrar_exito_matrix(hash_valor, tipo, password):
    """
    Imprime un bloque visual destacado cuando se logra descifrar un hash,
    manteniendo la estética verde de "Matrix".
    """
    print(f"\n{C_SUCCESS}╔══════════════════════════════════════════════════════════════════════╗")
    print(f"║ [TERMINAL DE NODO] DESCIFRADO EXITOSO")
    print(f"║ El Hash {C_HASH}{hash_valor}{C_SUCCESS}, tipo \"{tipo.upper()}\" corresponde a: {password}")
    print(f"╚══════════════════════════════════════════════════════════════════════╝{RESET}\n")

# ---------------------------------------------------------
# HERRAMIENTAS DE AUDITORÍA CON MONITOREO EN TIEMPO REAL
# ---------------------------------------------------------
def hashcat_diccionario(hash_valor, hash_mode, tipo):
    """
    Ejecuta un ataque de diccionario puro (Modo -a 0) con Hashcat.
    Lee el flujo de salida estándar (stdout) para capturar y mostrar el porcentaje de avance.
    """
    print(f"{C_TOOL}[Herramienta] Iniciando Hashcat (Diccionario) para tipo {tipo.upper()}...{RESET}")
    start_time = time.time()
    try:
        # subprocess.Popen permite leer la salida de la consola en tiempo real
        process = subprocess.Popen([
            "hashcat", "-m", hash_mode, "-a", "0",
            hash_valor, WORDLIST,
            "--potfile-disable", "--status", "--status-timer=1" # --status fuerza a mostrar el progreso
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # Bucle que lee las líneas arrojadas por Hashcat mientras se ejecuta
        for line in iter(process.stdout.readline, ''):
            # Expresión regular para buscar el patrón de porcentaje: ( xx.xx% )
            match = re.search(r'\(\s*(\d+\.\d+)%\s*\)', line)
            if match:
                t = int(time.time() - start_time)
                # La secuencia \r reescribe la misma línea en la terminal
                sys.stdout.write(f"\r{C_TOOL} └─ [SISTEMA] Herramienta: Hashcat Diccionario | Avance: {match.group(1)}% | Tiempo: {t}s {RESET}  ")
                sys.stdout.flush()

        process.wait() # Espera a que termine el binario
        print() # Salto de línea limpio al finalizar
        
        # Una vez terminado, verifica si se logró recuperar la contraseña
        return parsear_hashcat(hash_valor, hash_mode)

    except Exception as e:
        print(f"\n{C_ERROR}[ERROR diccionario] Excepción detectada: {e}{RESET}")
        return None

def hashcat_reglas(hash_valor, hash_mode, tipo):
    """
    Ejecuta un ataque de diccionario aplicando reglas de mutación.
    Útil para contraseñas que tienen variaciones de números, mayúsculas o símbolos.
    """
    if not RULES:
        print(f"{C_TOOL}[OMITIDO] No hay reglas de mutación configuradas.{RESET}")
        return None

    print(f"{C_TOOL}[Herramienta] Iniciando Hashcat (Reglas) para tipo {tipo.upper()}...{RESET}")
    start_time = time.time()
    try:
        process = subprocess.Popen([
            "hashcat", "-m", hash_mode, "-a", "0",
            hash_valor, WORDLIST,
            "-r", RULES, "--status", "--status-timer=1"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        for line in iter(process.stdout.readline, ''):
            # Captura de errores internos de hashcat si falla la carga de la regla
            if "No such file" in line:
                print(f"\n{C_ERROR}[ERROR] Archivo de regla inválido.{RESET}")
                process.terminate()
                return None
                
            match = re.search(r'\(\s*(\d+\.\d+)%\s*\)', line)
            if match:
                t = int(time.time() - start_time)
                sys.stdout.write(f"\r{C_TOOL} └─ [SISTEMA] Herramienta: Hashcat Reglas | Avance: {match.group(1)}% | Tiempo: {t}s {RESET}  ")
                sys.stdout.flush()

        process.wait()
        print()
        return parsear_hashcat(hash_valor, hash_mode)

    except Exception as e:
        print(f"\n{C_ERROR}[ERROR reglas] Excepción detectada: {e}{RESET}")
        return None

def ejecutar_john(hash_valor, tipo):
    """
    Ejecuta John The Ripper como mecanismo de respaldo.
    John no soporta el análisis de un solo hash en la línea de comando fácilmente,
    por lo que el hash se escribe en un archivo temporal (temp_hash.txt) para su análisis.
    """
    john_format = JOHN_FORMATS.get(tipo.lower(), "raw-md5")
    print(f"{C_TOOL}[Herramienta] Iniciando Respaldo John the Ripper (Formato: {john_format})...{RESET}")
    start_time = time.time()
    try:
        # Se genera el archivo temporal que leerá JtR
        with open("temp_hash.txt", "w") as f:
            f.write(hash_valor)

        # Ejecución silenciada de John
        process = subprocess.Popen(
            ["john", f"--format={john_format}", "temp_hash.txt"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Bucle para medir el tiempo transcurrido (John no emite % fácilmente en un pipe estándar)
        while process.poll() is None:
            t = int(time.time() - start_time)
            sys.stdout.write(f"\r{C_TOOL} └─ [SISTEMA] Herramienta: John | Avance: Analizando... | Tiempo: {t}s {RESET}  ")
            sys.stdout.flush()
            time.sleep(1)
        print()

        # Ejecución del comando '--show' para ver si fue resuelto
        result = subprocess.run(
            ["john", "--show", "temp_hash.txt"],
            capture_output=True, text=True
        )

        # Filtrado estricto para no capturar avisos estadísticos o de error como resultados
        for line in result.stdout.splitlines():
            if ":" in line and "password hashes cracked" not in line and "error" not in line.lower():
                return line.split(":", 1)[1].strip()

    except Exception as e:
        print(f"\n{C_ERROR}[ERROR john] Excepción detectada: {e}{RESET}")

    return None

# ---------------------------------------------------------
# SEGURIDAD DE NUEVAS CONTRASEÑAS (RE-HASHING)
# ---------------------------------------------------------
def calcular_sha256_salt(password):
    """
    Genera un nuevo hash mucho más seguro a partir del texto plano recuperado.
    Utiliza SHA-256 junto con un 'salt' aleatorio de 16 bytes para evitar ataques
    futuros mediante tablas arcoíris.
    """
    salt = os.urandom(16).hex()
    hash_val = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hash_val}"

# ---------------------------------------------------------
# LÓGICA COGNITIVA DEL AGENTE LLM
# ---------------------------------------------------------
def razonar_con_llm(hash_valor):
    """
    Interactúa con el modelo LLM local para analizar el hash.
    Se inyecta la longitud exacta calculada en Python para evitar alucinaciones,
    obligando al LLM a seguir reglas deterministas para deducir el tipo.
    """
    # Cálculo determinista del sistema operativo (O(1)). Inmune a errores.
    longitud_real = len(hash_valor)

    # Prompt instruccional en español estricto
    prompt = f"""
Eres un agente experto en ciberseguridad. Analiza el hash: {hash_valor}
Longitud exacta verificada por el sistema: {longitud_real} caracteres.

REGLAS ESTRICTAS DE IDENTIFICACIÓN:
- 32 caracteres = AMBIGUO. Devuelve la lista ["md5", "ntlm"] para probar ambos de forma secuencial.
- 40 caracteres = ["sha1"]
- 64 caracteres = ["sha256"]
- 128 caracteres = ["sha512"]

INSTRUCCIONES:
1. Utiliza la longitud exacta proporcionada por el sistema para determinar la lista de algoritmos posibles.
2. Elige la estrategia inicial ("diccionario", "reglas", "respaldo_john").
3. Explica lógicamente tu análisis basándote exclusivamente en la longitud brindada.

Responde SOLO en formato JSON estricto respetando las claves:
{{"tipos": ["md5", "ntlm"], "estrategia": "diccionario", "razonamiento": "El sistema indica 32 caracteres exactos. Como MD5 y NTLM son indistinguibles, se probarán ambos de forma secuencial."}}
"""
    try:
        r = requests.post(
            f"{OLLAMA_SERVER}/api/generate",
            json={"model": MODELO, "prompt": prompt, "stream": False},
            timeout=60
        )

        data = r.json()
        text = data.get("response", "")
        
        # Extracción del bloque JSON crudo utilizando expresiones regulares
        match = re.search(r'\{.*?\}', text, re.DOTALL)

        if match:
            json_limpio = match.group()
            obj = json.loads(json_limpio)
            
            # Se parsean las variables asegurando un valor por defecto si falla la IA
            tipos = obj.get("tipos", ["md5"])
            estrategia = obj.get("estrategia", "diccionario")
            razonamiento = obj.get("razonamiento", "No provisto.")
            
            # Muestra en consola el análisis lógico de la IA
            print(f"{C_AGENT}[Agente LLM] Razonamiento lógico: {razonamiento}{RESET}")
            
            return tipos, estrategia

    except Exception as e:
        print(f"{C_ERROR}[ERROR LLM] Falla en inferencia: {e}{RESET}")

    # Retorno de seguridad (Fallback) si falla la conexión HTTP con Ollama
    return ["md5"], "diccionario"

# ---------------------------------------------------------
# NÚCLEO DE RESOLUCIÓN (ORQUESTADOR)
# ---------------------------------------------------------
def resolver_hash(hash_valor):
    """
    Función orquestadora. Toma el hash, solicita el análisis a la IA,
    e itera sobre los tipos de hash posibles ejecutando las herramientas de ataque
    en cascada según la estrategia elegida.
    """
    print(f"\n{C_MAIN}──────────────────────────────────────────────────────────────────{RESET}")
    print(f"{C_AGENT}[Agente] Analizando hash objetivo: {C_HASH}{hash_valor}{RESET}")

    # Llama a la IA para obtener la matriz de algoritmos posibles y el vector de ataque
    tipos, estrategia = razonar_con_llm(hash_valor)
    tipos_str = ", ".join(tipos).upper()

    print(f"{C_AGENT}[Agente] Parámetros extraídos -> Posibles Tipos: {tipos_str} | Estrategia: {estrategia.upper()}{RESET}")

    # Bucle secuencial: Prueba cada tipo de algoritmo sugerido por la IA
    for tipo in tipos:
        hash_mode = HASHCAT_MODES.get(tipo.lower(), "0") # Si falla, usa '0' (MD5) por defecto
        print(f"\n{C_AGENT}[Agente] ---> Ejecutando secuencia técnica para tipo: {tipo.upper()}{RESET}")

        # Se ejecuta el flujo basado en la decisión táctica de la IA
        if estrategia == "diccionario":
            p = hashcat_diccionario(hash_valor, hash_mode, tipo)
            if p:
                mostrar_exito_matrix(hash_valor, tipo, p)
                return p

            # Si falla el diccionario directo, intenta mutarlo con reglas
            p = hashcat_reglas(hash_valor, hash_mode, tipo)
            if p:
                mostrar_exito_matrix(hash_valor, tipo, p)
                return p

        elif estrategia == "reglas":
            # Fuerza el uso directo de reglas
            p = hashcat_reglas(hash_valor, hash_mode, tipo)
            if p:
                mostrar_exito_matrix(hash_valor, tipo, p)
                return p

        # Último recurso (Fallback): Se delega a John the Ripper si todo lo anterior falla
        p = ejecutar_john(hash_valor, tipo)
        if p:
            mostrar_exito_matrix(hash_valor, tipo, p)
            return p

    # Si itera sobre todas las herramientas y tipos sin éxito, retorna nulo
    return None

# ---------------------------------------------------------
# BUCLE PRINCIPAL (MAIN LOOP)
# ---------------------------------------------------------
def procesar():
    """
    Punto de entrada de la aplicación.
    Configura el entorno interactivo, valida archivos y procesa la carga de trabajo.
    """
    global PASSWORDS_FILE, WORDLIST

    # Limpia la terminal del sistema operativo para realzar el efecto visual
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"{C_MAIN}╔════════════════════════════════════════╗")
    print(f"║       INICIANDO AGENTE MATRIX          ║")
    print(f"╚════════════════════════════════════════╝{RESET}\n")

    # Interfaz de usuario por consola para configuración de parámetros
    arch_in = input(f"Archivo de hashes (Presione Enter para usar '{PASSWORDS_FILE}'): ").strip()
    if arch_in:
        PASSWORDS_FILE = arch_in

    print(f"\nSelección de diccionario base:")
    print(f"1) Usar ruta por defecto ({WORDLIST})")
    print(f"2) Configurar un diccionario personalizado")
    opc = input(f"Opción (1/2): ").strip()
    
    if opc == "2":
        dict_in = input(f"Ingrese la ruta absoluta del archivo: ").strip()
        if os.path.exists(dict_in):
            WORDLIST = dict_in
        else:
            print(f"{C_TOOL}[ADVERTENCIA] Ruta no válida. Se utilizará el archivo predeterminado: {WORDLIST}{RESET}")
    
    print(f"\n{C_MAIN}=========================================={RESET}")

    # Validaciones críticas pre-ejecución
    if not verificar_ollama():
        print(f"{C_ERROR}[ERROR FATAL] La instancia de IA no está respondiendo.{RESET}")
        sys.exit(1)

    if not os.path.exists(PASSWORDS_FILE):
        print(f"{C_ERROR}[ERROR FATAL] El archivo de contraseñas '{PASSWORDS_FILE}' no existe en el disco.{RESET}")
        return

    # Carga del archivo en memoria, ignorando saltos de línea crudos
    with open(PASSWORDS_FILE) as f:
        hashes_crudos = [l.strip() for l in f.readlines()]
        
    # Cálculo estadístico (se ignoran líneas vacías para el total)
    total_validos = sum(1 for h in hashes_crudos if h)
    analizados = 0
    encontrados = 0

    # Apertura de descriptores de archivos para registro de resultados
    with open(PLAIN_FILE, "w") as f_plain, open(NEW_PASSWORDS_FILE, "w") as f_new:

        # Iteración principal sobre cada hash documentado
        for h in hashes_crudos:
            
            # Si la línea está vacía, se mantiene el espaciado en los archivos de salida
            if not h:
                f_plain.write("\n")
                f_new.write("\n")
                # Escritura forzada en disco (fsync)
                f_plain.flush()
                f_new.flush()
                os.fsync(f_plain.fileno())
                os.fsync(f_new.fileno())
                continue

            analizados += 1
            
            # Invocación del orquestador
            password = resolver_hash(h)

            # Lógica de almacenamiento
            if password:
                encontrados += 1
                f_plain.write(password + "\n")
                f_new.write(calcular_sha256_salt(password) + "\n")
            else:
                print(f"{C_ERROR}[FALLO] No se logró descifrar el hash: {C_HASH}{h}{RESET}")
                f_plain.write("\n")
                f_new.write("\n")

            # Actualización de métricas generales del proceso
            porcentaje = (analizados / total_validos) * 100
            print(f"{C_METRIC}[MÉTRICAS DEL SISTEMA] Procesado: {porcentaje:.2f}% | Hashes analizados: {analizados}/{total_validos} | Descifrados: {encontrados}{RESET}")

            # Persistencia estricta en tiempo real (evita pérdida de datos si el script se interrumpe)
            f_plain.flush()
            f_new.flush()
            os.fsync(f_plain.fileno())
            os.fsync(f_new.fileno())

    print(f"\n{C_MAIN}[SISTEMA] SECUENCIA DE AUDITORÍA COMPLETADA{RESET}")

# ---------------------------------------------------------
# EJECUCIÓN DEL SCRIPT
# ---------------------------------------------------------
if __name__ == "__main__":
    procesar()
