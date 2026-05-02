import os
import hashlib
import requests
import subprocess
import json
import re
import sys
import time
from collections import Counter

# ---------------------------------------------------------
# CONFIGURACIÓN DE COLORES (ANSI) PARA INTERFAZ VISUAL
# ---------------------------------------------------------
# Se definen códigos de escape ANSI para una interfaz visual técnica y profesional en la consola.
# Estos valores modifican la salida estándar (stdout) y deben reiniciarse con RESET en cada impresión
# para evitar que el color se propague a las entradas del usuario o a la terminal misma tras el cierre.
C_MAIN = "\033[38;5;34m"      # Verde (Principal) - Usado para bordes y títulos de secciones.
C_AGENT = "\033[36m"          # Cian (IA/Agente) - Usado para diferenciar las respuestas del LLM.
C_TOOL = "\033[33m"           # Amarillo (Herramientas/Avisos) - Usado para comandos subyacentes.
C_SUCCESS = "\033[1;32m"      # Verde Brillante (Éxito) - Indica confirmaciones positivas.
C_ERROR = "\033[1;31m"        # Rojo (Errores Fatales) - Usado en excepciones o fallas críticas.
C_METRIC = "\033[38;5;141m"   # Púrpura (Métricas de Hashcat) - Aísla la salida cruda de la herramienta.
C_HASH = "\033[1;31m"         # Rojo (Resaltado de Hashes) - Destaca visualmente el string cifrado.
RESET = "\033[0m"             # Restablecer formato - Crucial para no 'manchar' el resto de la consola.

# ---------------------------------------------------------
# CONFIGURACIÓN GENERAL DEL ENTORNO Y PERSISTENCIA
# ---------------------------------------------------------
# Variables globales de conexión a la API REST de Ollama.
# OLLAMA_SERVER apunta al host donde se ejecuta el motor de inferencia.
OLLAMA_SERVER = "http://192.168.159.1:11434"
# MODELO especifica el LLM exacto a utilizar para el razonamiento cognitivo.
MODELO = "mistral:7b-instruct-q4_K_M"

# Archivos por defecto para la lectura, persistencia de datos y resultados de la auditoría.
PASSWORDS_FILE = "PASSWORDS.md"            # Archivo objetivo por defecto que contiene los hashes crudos.
PLAIN_FILE = "plain.txt"                   # Salida: listado de contraseñas resueltas en texto plano.
NEW_PASSWORDS_FILE = "new_passwords.txt"   # Salida: hashes re-asegurados utilizando el algoritmo SHA-256.
UNRESOLVED_FILE = "hashesnoresueltos.txt"  # Salida: hashes que resistieron todas las fases del ataque.
WORDLIST = "/opt/lab2/realuniq.lst"        # Diccionario base predeterminado del sistema (fallback del LLM).

LOG_FILE = "" # Esta variable se inicializará dinámicamente usando el nombre del archivo objetivo.

# Diccionario técnico de referencia (Constantes de Validación). 
# Contiene los códigos de modo internos que requiere Hashcat ("mode") y 
# las longitudes físicas estandarizadas en caracteres hexadecimales ("len").
# Esto permite a Python tener una base empírica estricta para validar las hipótesis del LLM.
HASHCAT_MODES = {
    "md5": {"mode": "0", "len": 32},
    "sha1": {"mode": "100", "len": 40},
    "sha256": {"mode": "1400", "len": 64},
    "sha512": {"mode": "1700", "len": 128},
    "ntlm": {"mode": "1000", "len": 32}
}

# ---------------------------------------------------------
# FUNCIONALIDAD DE REGISTRO (LOGGING)
# ---------------------------------------------------------
def escribir_log(mensaje, es_error=False):
    """
    Registra eventos secuenciales en un archivo de log con marca de tiempo precisa.
    Permite auditar el comportamiento del script, el flujo de Hashcat y trazar 
    excepciones sin depender de la consola estándar.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    prefijo = "[ERROR]" if es_error else "[INFO]"
    try:
        # Modo 'a' (append) para añadir líneas al final del archivo sin sobrescribir el historial.
        with open(LOG_FILE, "a") as f:
            f.write(f"{timestamp} {prefijo} {mensaje}\n")
    except Exception:
        # Se omite silenciosamente si no hay permisos de escritura, evitando interrupciones fatales en el flujo principal.
        pass

# ---------------------------------------------------------
# VERIFICACIÓN DE INFRAESTRUCTURA (OLLAMA)
# ---------------------------------------------------------
def verificar_ollama():
    """
    Valida la conectividad de red y disponibilidad con el servidor de inferencia local (Ollama).
    Asegura que el modelo configurado (MODELO) esté cargado en memoria antes de iniciar la carga computacional pesada.
    Actúa como un mecanismo de fail-safe temprano.
    """
    try:
        # Petición GET al endpoint nativo de Ollama para listar los modelos instalados actualmente.
        r = requests.get(f"{OLLAMA_SERVER}/api/tags", timeout=5)
        modelos = [m["name"] for m in r.json().get("models", [])]
        print(f"{C_MAIN}[AGENTE] Modelos de IA detectados: {modelos}{RESET}")
        
        # Retorna True solo si el modelo deseado está en la lista de modelos disponibles.
        return MODELO in modelos
    except Exception as e:
        # Captura errores de conexión (ConnectionRefused, Timeout, etc.)
        print(f"{C_ERROR}[ERROR FATAL] No se pudo establecer conexión con Ollama: {e}{RESET}")
        escribir_log(f"Fallo de conexión con Ollama: {e}", es_error=True)
        return False

# ---------------------------------------------------------
# FUNCIONES AUXILIARES DE PARSEO Y VISUALIZACIÓN
# ---------------------------------------------------------
def parsear_hashcat_masivo(hash_mode, archivo_hashes, hashes_crudos):
    """
    Extrae las contraseñas resueltas consultando el archivo de sesión interno (potfile) de Hashcat.
    Realiza una comparación estricta entre el hash crudo auditado y la salida formateada 
    estándar devuelta por Hashcat (formato 'hash:password').
    """
    resuel_hashes = {}
    try:
        # Ejecutamos Hashcat con el flag --show. Esta operación no consume GPU/CPU para crackear,
        # simplemente vuelca los resultados que ya existen en caché para el modo especificado.
        result = subprocess.run(
            ["hashcat", "-m", hash_mode, archivo_hashes, "--show", "--quiet"],
            capture_output=True, text=True
        )
        
        # Procesamos la salida estándar línea por línea para evitar sobrecargas de memoria en diccionarios grandes.
        for line in result.stdout.splitlines():
            for hash_valor in hashes_crudos:
                if not hash_valor: continue
                # Verificación estricta (case-insensitive): comprobamos que el hash objetivo coincida exactamente con el prefijo de la línea resuelta.
                if line.lower().startswith(hash_valor.lower() + ":"):
                    # Dividimos el string por el primer separador ":" y limpiamos espacios residuales.
                    password = line.split(":", 1)[1].strip()
                    resuel_hashes[hash_valor.lower()] = password
                    break
                    
    except Exception as e:
        # El fallo en esta etapa compromete la recolección de resultados, se debe registrar rigurosamente.
        escribir_log(f"Error en parseo masivo para el modo {hash_mode}: {e}", es_error=True)
        
    return resuel_hashes

def mostrar_exito_auditoria(hash_valor, tipo, password, num_linea=1):
    """
    Formatea y muestra en la terminal el resultado individual de un crackeo exitoso.
    Recibe e imprime el número de línea original para mantener la trazabilidad exacta respecto al archivo auditado.
    """
    print(f"Línea {num_linea}: El Hash {C_HASH}{hash_valor}{C_SUCCESS}, tipo \"{tipo.upper()}\" corresponde a: {password}{RESET}")

# ---------------------------------------------------------
# HERRAMIENTAS DE AUDITORÍA CON MONITOREO DINÁMICO
# ---------------------------------------------------------
def ejecutar_hashcat_masivo(hash_mode, target_file, estrategia="dictionary", parametro_extra=""):
    """
    Orquesta la ejecución del binario de Hashcat en un subproceso del sistema operativo.
    Construye los argumentos de ataque de forma dinámica y condicional basándose en el análisis cognitivo previo dictado por el LLM.
    """
    # Base inmutable del comando: binario, modo de ataque y archivo objetivo.
    comando_args = ["hashcat", "-m", hash_mode, target_file]
    
    # Lógica de construcción condicional para el payload del comando.
    if estrategia == "rules" and parametro_extra:
        # Estrategia de ataque de diccionario mutado mediante un archivo de reglas (ej. best64.rule, dive.rule).
        comando_args.extend([WORDLIST, "-r", parametro_extra])
    elif estrategia == "mask" and parametro_extra:
        # Estrategia de ataque de fuerza bruta posicional mediante una máscara predefinida (ej. ?u?l?l?d?d).
        # El argumento -a 3 indica a Hashcat que debe procesar máscaras.
        comando_args.extend(["-a", "3", parametro_extra])
    else:
        # Estrategia por defecto: Ataque de diccionario simple o estricto.
        comando_args.extend(["-a", "0", WORDLIST])
        
    # Añadimos flags de control operativos:
    # --restore-disable: Evita colisiones si hay una sesión previa abortada.
    # --force: Ignora advertencias sobre la falta de OpenCL nativo o drivers en entornos virtuales.
    comando_args.extend(["--restore-disable", "--force"])
    
    # Imprime en terminal la construcción final para transparencia del operador.
    print(f"{C_TOOL}[Herramienta] Ejecutando comando sobre {target_file}: {' '.join(comando_args)}{RESET}")
    
    try:
        # Popen se utiliza en lugar de run() para iterar y monitorear el flujo de salida estándar (stdout) 
        # en tiempo real mientras el subproceso subyacente sigue activo.
        process = subprocess.Popen(
            comando_args, 
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True
        )

        # Iterador que lee cada línea que el motor de Hashcat emite.
        for line in iter(process.stdout.readline, ''):
            clean_line = line.strip()
            if not clean_line: continue
            
            # Registrar y mostrar la métrica generada, manteniendo el feedback visual del avance.
            escribir_log(f"[Hashcat LOG] {clean_line}")
            print(f"{C_METRIC}[Hashcat RAW] {clean_line}{RESET}")

        # Bloquea la ejecución de Python hasta que el subproceso de Hashcat finalice.
        process.wait()
        print() 
    except Exception as e:
        # Manejo de fallas de hardware, falta de dependencias u errores binarios.
        print(f"\n{C_ERROR}[ERROR Lote] Excepción detectada en subproceso: {e}{RESET}")
        escribir_log(f"Error en Hashcat Masivo: {e}", es_error=True)

# ---------------------------------------------------------
# RE-HASHING DE SEGURIDAD (POST-PROCESAMIENTO)
# ---------------------------------------------------------
def calcular_nuevo_hash(password):
    """
    Genera un hash SHA-256 matemáticamente puro a partir de la contraseña plana recuperada.
    Se utiliza para exportar los datos a 'new_passwords.txt' elevando el estándar de 
    seguridad de contraseñas vulneradas previamente en algoritmos obsoletos (MD5/SHA1).
    """
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------------------------------------------
# GESTIÓN DE DUPLICADOS Y ANÁLISIS FÍSICO (CAPA DE OPTIMIZACIÓN)
# ---------------------------------------------------------
def verificar_duplicados(hashes_crudos):
    """
    Analiza linealmente el archivo objetivo para identificar redundancias criptográficas.
    Filtrar duplicados reduce significativamente los ciclos de reloj desperdiciados por la GPU/CPU durante el crackeo.
    Retorna la lista limpia, el conteo total de omisiones y el mapeo de líneas originales para trazabilidad.
    """
    print(f"{C_AGENT}[Agente] Iniciando verificación de duplicados...{RESET}")
    mapeo_lineas = {}
    # enumerate(..., 1) nos da el índice real basado en 1 (número de línea) del archivo original.
    for i, h in enumerate(hashes_crudos, 1):
        if not h: continue
        if h not in mapeo_lineas:
            mapeo_lineas[h] = []
        mapeo_lineas[h].append(i) # Persistimos todas las líneas donde aparece el mismo hash para el reporte final.
    
    # Extraemos y agrupamos solo los hashes cuya lista de apariciones sea estrictamente mayor a 1.
    duplicados = {h: lineas for h, lineas in mapeo_lineas.items() if len(lineas) > 1}
    
    # Muestra un desglose exhaustivo de las redundancias encontradas.
    if duplicados:
        print(f"{C_TOOL}[INFO] Se detectaron {len(duplicados)} hashes con duplicados:{RESET}")
        for h, lineas in duplicados.items():
            print(f"  - Hash {C_HASH}{h}{RESET} aparece {len(lineas)} veces en líneas: {lineas}")
    else:
        print(f"{C_SUCCESS}[INFO] No se detectaron hashes duplicados.{RESET}")
    
    # Genera la lista definitiva y única de objetivos.
    lista_unicos = list(mapeo_lineas.keys())
    # Cálculo aritmético exacto para el reporte estadístico de redundancias omitidas en la ejecución final.
    total_duplicados = sum(len(lineas) - 1 for lineas in mapeo_lineas.values())
    return lista_unicos, total_duplicados, mapeo_lineas

def analizar_longitudes_fisicas(lista_unicos):
    """
    Realiza una medición empírica de la longitud de caracteres para cada hash único de la muestra.
    La distribución física es el pilar para que Python pueda validar o desmentir 
    las suposiciones abstractas del Agente LLM en el segundo paso del flujo agéntico.
    """
    stats_longitud = Counter(len(h) for h in lista_unicos if h)
    print(f"{C_AGENT}[Agente] Distribución física de longitudes detectada:{RESET}")
    for length, count in stats_longitud.items():
        print(f"  - Longitud {length} caracteres: {count} ocurrencias")
    return stats_longitud

# ---------------------------------------------------------
# LÓGICA COGNITIVA DEL AGENTE LLM (FLUJO: IA ANALIZA -> PYTHON VALIDA)
# ---------------------------------------------------------
def razonar_con_llm_masivo(hashes_crudos, stats_longitud):
    """
    PRIMER PASO DEL FLUJO AGÉNTICO: FASE HEURÍSTICA Y COGNITIVA.
    El LLM recibe una muestra (máx 10) de los datos en crudo y aplica reconocimiento de patrones visuales 
    (presencia de prefijos, estructura de base de datos) para inferir algoritmos viables.
    """
    prompt = f"""
Eres un agente experto en ciberseguridad. Analiza esta muestra de hashes:
{json.dumps([h for h in hashes_crudos if h][:10])}

REGLAS ESTRICTAS OBLIGATORIAS:
1. Basándote ÚNICAMENTE en la estructura visual y prefijos, identifica qué algoritmos podrían ser.
2. Deduce el contexto probable del sistema (ej. Base de datos web, Directorio Activo).
3. Propón una lista de algoritmos ("md5", "sha1", "sha256", "sha512", "ntlm").
4. Selecciona la estrategia primaria ("dictionary", "rules"). 
5. Sugiere la ruta de un diccionario de Kali Linux (ej. /usr/share/wordlists/rockyou.txt).
6. Si eliges "rules", indica el archivo de reglas de Kali en 'parametro_extra'.
7. REDACTA TODO TU RAZONAMIENTO ÚNICA Y EXCLUSIVAMENTE EN ESPAÑOL NEUTRO. BAJO NINGÚN CONCEPTO USES INGLÉS.

Responde EXCLUSIVAMENTE con JSON:
{{
  "propuesta_algoritmos": ["tipo1", "tipo2"],
  "strategy": "<dictionary o rules>",
  "parametro_extra": "<regla si aplica, sino vacío>",
  "kali_wordlist": "<ruta_diccionario>",
  "razonamiento": "<Análisis detallado sobre el origen y lógica de la muestra EN ESPAÑOL NEUTRO.>"
}}
"""
    try:
        # Se lanza la solicitud POST bloqueante al servidor Ollama local.
        r = requests.post(
            f"{OLLAMA_SERVER}/api/generate",
            json={"model": MODELO, "prompt": prompt, "stream": False},
            timeout=60
        )
        data = r.json()
        
        # CORRECCIÓN DE PARSEO JSON: 
        # Se cambia la regex a modo greedy (.*) para asegurar que se captura todo el bloque JSON sin importar saltos de línea internos.
        match = re.search(r'\{.*\}', data.get("response", ""), re.DOTALL)
        if match:
            json_str = match.group()
            # Se añade strict=False para tolerar caracteres de control no escapados que Mistral:7b a veces inserta.
            obj = json.loads(json_str, strict=False)
            print(f"{C_AGENT}[Agente LLM] Hipótesis analítica: {obj.get('razonamiento')}{RESET}")
            return obj
        else:
            escribir_log("El agente LLM no devolvió un formato JSON válido en la fase primaria.", es_error=True)
    except Exception as e:
        # El registro de errores aquí previene la falla silenciosa observada previamente.
        escribir_log(f"Fallo en el razonamiento cognitivo (Timeout o Parseo): {str(e)}", es_error=True)
        pass
    
    # Fallback determinista en caso de error de timeout, desconexión o incapacidad de parsear el JSON.
    return {"propuesta_algoritmos": ["md5"], "strategy": "dictionary", "kali_wordlist": "/usr/share/wordlists/rockyou.txt"}

def validar_hipotesis_ia(propuesta_algoritmos, stats_longitud):
    """
    SEGUNDO PASO DEL FLUJO AGÉNTICO: FASE DE VERIFICACIÓN DETERMINISTA.
    Python cruza las suposiciones teóricas derivadas del LLM con las constantes de física del archivo.
    Esto mitiga el problema de "alucinación" donde la IA podría sugerir crackear algoritmos inexistentes en la muestra.
    """
    print(f"{C_TOOL}[SISTEMA] Verificando propuestas de IA contra validación física de longitudes...{RESET}")
    tipos_validados = []
    
    for tipo in propuesta_algoritmos:
        t_low = tipo.lower()
        if t_low in HASHCAT_MODES:
            longitud_requerida = HASHCAT_MODES[t_low]["len"]
            # Iteramos sobre la distribución física pre-calculada. Si la longitud requerida existe, la hipótesis es válida.
            if any(l == longitud_requerida for l in stats_longitud.keys()):
                tipos_validados.append(t_low)
            else:
                print(f"{C_ERROR}[RECHAZADO] La IA sugirió '{tipo}', pero no hay hashes de {longitud_requerida} chars en la muestra real.{RESET}")
    
    # Fallback de seguridad: Si la IA alucinó por completo, Python asume MD5 por defecto estadístico.
    if not tipos_validados:
        print(f"{C_TOOL}[AVISO] Ninguna hipótesis de la IA fue validada. Se procederá con MD5 por defecto de seguridad.{RESET}")
        return ["md5"]
    
    return tipos_validados

def razonar_fallos_con_llm(hashes_fallidos):
    """
    TERCER PASO: BUCLE DE RETROALIMENTACIÓN (FEEDBACK LOOP).
    Si la ejecución primaria no alcanzó un compromiso del 100%, el LLM evalúa los hashes sobrevivientes
    (Muestra residual) y formula una estrategia secundaria y de mayor intensidad (máscaras y reglas complejas).
    """
    prompt = f"""
Auditaste un lote pero estos {len(hashes_fallidos)} hashes no se resolvieron.
Muestra residual: {json.dumps(hashes_fallidos[:5])}

REGLAS ESTRICTAS OBLIGATORIAS:
1. Propón en JSON una estrategia secundaria agresiva ("mask" o "rules").
2. Justifica por qué el diccionario inicial pudo fallar.
3. REDACTA TU JUSTIFICACIÓN ÚNICA Y EXCLUSIVAMENTE EN ESPAÑOL NEUTRO. NO USES INGLÉS.

Responde EXCLUSIVAMENTE con JSON:
{{
  "strategy": "<mask o rules>",
  "parametro_extra": "<máscara o ruta de regla>",
  "razonamiento": "<Justificación técnica del ataque secundario EN ESPAÑOL NEUTRO.>"
}}
"""
    try:
        r = requests.post(
            f"{OLLAMA_SERVER}/api/generate",
            json={"model": MODELO, "prompt": prompt, "stream": False},
            timeout=60
        )
        # CORRECCIÓN DE PARSEO SECUNDARIO: 
        # Utilizando regex greedy y json.loads con tolerancia a caracteres de control (strict=False).
        match = re.search(r'\{.*\}', r.json().get("response", ""), re.DOTALL)
        if match:
            json_str = match.group()
            obj = json.loads(json_str, strict=False)
            print(f"{C_AGENT}[Agente LLM Secundario] {obj.get('razonamiento')}{RESET}")
            return obj.get("strategy", ""), obj.get("parametro_extra", "")
    except Exception as e: 
        escribir_log(f"Fallo en el razonamiento secundario (Feedback Loop): {str(e)}", es_error=True)
        pass
    
    return None, None

def generar_reporte_cierre(total, resueltos, tipos, wordlist, porcentaje):
    """
    FASE FINAL: REPORTING ASISTIDO POR IA.
    Genera la conclusión narrativa y semántica del proceso. Se inyectan las métricas finales (Variables Matemáticas) 
    dentro del prompt bajo un esquema de "REGLAS ESTRICTAS" para evitar alucinaciones operativas comunes.
    """
    prompt = f"""
Auditoría técnica finalizada.
Datos reales a utilizar:
- Total de hashes objetivo: {total}
- Hashes resueltos: {resueltos}
- Eficacia matemática calculada: {porcentaje:.2f}%
- Algoritmos atacados: {tipos}
- Diccionario utilizado: {wordlist}

REGLAS ESTRICTAS OBLIGATORIAS:
1. Escribir única y exclusivamente en español neutro. Bajo ningún concepto uses inglés.
2. NO inventar, suponer, ni alucinar nombres de archivos, carpetas o extensiones. Cíñete a los datos provistos.
3. NO realizar cálculos matemáticos independientes. Utiliza el porcentaje de eficacia exacto proporcionado ({porcentaje:.2f}%).
4. Redacta una conclusión técnica rigurosa (máximo 3 líneas) analizando la efectividad operativa y la resiliencia criptográfica del objetivo basado en estos datos.
5. No uses formato de salida tipo JSON, redacta libremente en texto plano.
"""
    try:
        # Disminución intencionada del timeout debido a la simplicidad computacional requerida para generar texto libre.
        r = requests.post(f"{OLLAMA_SERVER}/api/generate", json={"model": MODELO, "prompt": prompt, "stream": False}, timeout=40)
        return r.json().get("response", "Ejecución finalizada satisfactoriamente.").strip()
    except Exception as e: 
        escribir_log(f"Error al generar reporte de cierre: {str(e)}", es_error=True)
        return "Conclusión no disponible por pérdida temporal de conexión con el agente de Inteligencia Artificial."

# ---------------------------------------------------------
# BUCLE PRINCIPAL DE EJECUCIÓN (ORQUESTADOR MAESTRO)
# ---------------------------------------------------------
def procesar():
    """
    Flujo de control principal. Gobierna las fases de análisis, decisión, ejecución subyacente de Hashcat
    y renderizado de resultados estadísticos y reportes visuales en consola.
    """
    global PASSWORDS_FILE, WORDLIST, LOG_FILE
    
    # Limpieza visual y contextual de la terminal según el sistema operativo subyacente.
    os.system('cls' if os.name == 'nt' else 'clear')

    print(f"{C_MAIN}╔════════════════════════════════════════╗")
    print(f"║   INICIANDO AGENTE DE ANALISIS DE IA   ║")
    print(f"╚════════════════════════════════════════╝{RESET}\n")

    # 1. Selección y carga a memoria del archivo objetivo
    arch_in = input(f"Archivo de volcado de hashes (Enter para '{PASSWORDS_FILE}'): ").strip()
    if arch_in: PASSWORDS_FILE = arch_in

    # Vincula el archivo de bitácora directamente con el nombre del objetivo auditado.
    LOG_FILE = f"{PASSWORDS_FILE}.log"
    escribir_log(f"--- SESIÓN INICIADA: Analizando {PASSWORDS_FILE} ---")

    # Validaciones críticas de estado e integridad para prevenir excepciones profundas o fallas críticas no manejadas.
    if not verificar_ollama(): sys.exit(1)
    if not os.path.exists(PASSWORDS_FILE):
        print(f"{C_ERROR}[ERROR FATAL] El documento requerido '{PASSWORDS_FILE}' no existe en el sistema de archivos.{RESET}")
        sys.exit(1)

    # Carga lineal y saneamiento (strip) del archivo fuente de contraseñas.
    with open(PASSWORDS_FILE) as f:
        hashes_crudos_originales = [l.strip() for l in f.readlines()]

    # 2. Gestión de Redundancia y Filtrado de Duplicados (Capa de Optimización)
    # Extraemos la lista limpia. Esto reduce el scope de procesamiento y agiliza el crackeo en sistemas sin GPU.
    lista_unicos, total_duplicados, mapeo_lineas = verificar_duplicados(hashes_crudos_originales)
    
    # 3. Análisis Computacional y Físico de Estructuras
    # Extraemos las medidas que dictarán qué algoritmos permite evaluar el sistema determinista de Python.
    stats_longitud = analizar_longitudes_fisicas(lista_unicos)
    
    # Generación de la ruta del archivo único optimizado. 
    # El archivo adopta la convención obligatoria dictada en iteraciones anteriores.
    nombre_base, ext = os.path.splitext(PASSWORDS_FILE)
    UNIQUE_FILE = f"{nombre_base}_nd{ext}"
    
    # Persistencia del scope limpio en el almacenamiento local.
    with open(UNIQUE_FILE, "w") as f_u:
        for hu in lista_unicos: f_u.write(hu + "\n")
    print(f"{C_SUCCESS}[SISTEMA] Archivo de hashes únicos generado y optimizado: {UNIQUE_FILE}{RESET}")

    # 4. Flujo Agéntico (Paso Cognitivo)
    # Cedemos el contexto a la IA para inferencias heurísticas. 
    print(f"{C_AGENT}[Agente] Razonando sobre el lote masivo...{RESET}")
    propuesta_ia = razonar_con_llm_masivo(lista_unicos, stats_longitud)
    
    # 5. Validación de Python (Cruce Lógico vs Datos Reales)
    # Garantizamos que la IA no introduzca directivas de ataque inválidas a la ejecución de Hashcat.
    tipos_finales = validar_hipotesis_ia(propuesta_ia.get("propuesta_algoritmos", []), stats_longitud)
    estrategia_primaria = propuesta_ia.get("strategy", "dictionary")
    param_extra_primario = propuesta_ia.get("parametro_extra", "")
    dict_sugerido = propuesta_ia.get("kali_wordlist", "/usr/share/wordlists/rockyou.txt")

    # 6. Intervención Humana (Configuración Operativa)
    # Permite al auditor modificar los diccionarios si el sugerido por la IA no convence o no está presente.
    print(f"\n{C_MAIN}--- SELECCIÓN DE DICCIONARIO ---{RESET}")
    print(f"{C_AGENT}[Agente LLM] Sugerencia de diccionario basada en contexto: {dict_sugerido}{RESET}")
    print(f"1) Usar recomendación técnica del Agente ({dict_sugerido})")
    print(f"2) Definir ruta personalizada del sistema de archivos")
    opc = input(f"Seleccione la opción requerida (1 o 2): ").strip()
    if opc == "1": WORDLIST = dict_sugerido
    elif opc == "2":
        dict_in = input(f"Ruta absoluta de origen: ").strip()
        if os.path.exists(dict_in): WORDLIST = dict_in

    # 7. Auditoría Primaria (Ejecución en Subproceso Base)
    # Itera de forma individual sobre los diferentes motores o algoritmos válidos.
    hashes_resueltos_global = {}
    for tipo in tipos_finales:
        hash_mode = HASHCAT_MODES[tipo]["mode"]
        # Llamada asíncrona pero bloqueante a los recursos del hardware mediante Hashcat.
        ejecutar_hashcat_masivo(hash_mode, UNIQUE_FILE, estrategia_primaria, param_extra_primario)
        
        # Una vez culminado el run, leemos en caché (--show) los verdaderos aciertos del algoritmo evaluado.
        resultados_lote = parsear_hashcat_masivo(hash_mode, UNIQUE_FILE, lista_unicos)
        for h_lower, pwd in resultados_lote.items():
            if h_lower not in hashes_resueltos_global:
                hashes_resueltos_global[h_lower] = (pwd, tipo)

    # 8. Auditoría Secundaria (Bucle de Retroalimentación Cognitiva)
    hashes_faltantes = [h for h in lista_unicos if h.lower() not in hashes_resueltos_global]
    if hashes_faltantes:
        # CORRECCIÓN 1: Aislar los residuos en un archivo físico ANTES de llamar a la IA o a Hashcat
        RESIDUAL_FILE = f"{nombre_base}_residual{ext}"
        with open(RESIDUAL_FILE, "w") as f_res:
            for h in hashes_faltantes: f_res.write(h + "\n")

        print(f"\n{C_MAIN}--- FASE SECUNDARIA (RESIDUALES) ---{RESET}")
        print(f"{C_TOOL}[INFO] Se aislaron {len(hashes_faltantes)} hashes sin resolver en el archivo objetivo: {RESIDUAL_FILE}{RESET}")
        
        opc_continuar = input(f"¿Desea iniciar la auditoría secundaria asistida por IA sobre este archivo? (s/n): ").strip().lower()
        
        if opc_continuar == 's':
            print(f"\nDiccionario en uso: {WORDLIST}")
            print("1) Mantener el diccionario actual")
            print("2) Definir una nueva ruta absoluta para el diccionario")
            opc_dic = input("Seleccione (1 o 2): ").strip()
            
            if opc_dic == '2':
                dict_in = input("Nueva ruta absoluta de origen: ").strip()
                if os.path.exists(dict_in):
                    WORDLIST = dict_in
                    print(f"{C_SUCCESS}[SISTEMA] Diccionario actualizado a: {WORDLIST}{RESET}")
                else:
                    print(f"{C_ERROR}[ADVERTENCIA] Ruta no detectada en el sistema de archivos. Se mantendrá: {WORDLIST}{RESET}")
            
            print(f"\n{C_AGENT}[Agente] Evaluando la muestra residual para proponer vector de ataque...{RESET}")
            estrategia_sec, param_sec = razonar_fallos_con_llm(hashes_faltantes)
            
            if estrategia_sec:
                for tipo in tipos_finales:
                    hash_mode = HASHCAT_MODES[tipo]["mode"]
                    # CORRECCIÓN 2: Apuntar la ejecución de Hashcat estrictamente al archivo residual
                    ejecutar_hashcat_masivo(hash_mode, RESIDUAL_FILE, estrategia_sec, param_sec)
                    resultados_sec = parsear_hashcat_masivo(hash_mode, RESIDUAL_FILE, hashes_faltantes)
                    
                    for h_l, pwd in resultados_sec.items():
                        if h_l not in hashes_resueltos_global:
                            hashes_resueltos_global[h_l] = (pwd, tipo)
            else:
                # CORRECCIÓN 3: Notificación explícita si la IA falla al generar el patrón de ataque
                print(f"{C_ERROR}[ADVERTENCIA] El Agente IA no logró estructurar una estrategia secundaria válida. Fase abortada.{RESET}")
        else:
            print(f"{C_TOOL}[INFO] Auditoría secundaria omitida por instrucción del operador.{RESET}")

    # 9. Generación Persistente de Salidas de Disco y Trazabilidad Lineal Matemática
    encontrados = 0
    total_validos = len(lista_unicos)

    # Escribimos los archivos de salidas línea a línea en espejo al documento de hashes auditados original.
    with open(PLAIN_FILE, "w") as f_p, open(NEW_PASSWORDS_FILE, "w") as f_n, open(UNRESOLVED_FILE, "w") as f_un:
        for h in lista_unicos:
            if not h: continue
            h_low = h.lower()
            
            # Recueperamos la primera aparición cronológica del hash en crudo en el archivo original auditado.
            linea_original = mapeo_lineas[h][0]
            
            # Si existió compromiso confirmamos su escritura; caso contrario mantenemos las tabulaciones.
            if h_low in hashes_resueltos_global:
                pwd, tipo = hashes_resueltos_global[h_low]
                
                # Reporte Visual del acierto: el Agente emplea la trazabilidad calculada previament en memoria 
                # e inyecta la línea real a ser notificada.
                mostrar_exito_auditoria(h, tipo, pwd, num_linea=linea_original) 
                f_p.write(pwd + "\n")
                f_n.write(calcular_nuevo_hash(pwd) + "\n")
                
                # Incremento atómico exclusivo. Garantiza la integridad de la base estadística global de rendimiento.
                encontrados += 1 
            else:
                # Sincronización topológica de los resultados fallidos (blancos, saltos y dump residual)
                f_p.write("\n"); f_n.write("\n"); f_un.write(h + "\n")

    # 10. Resumen Ejecutivo de Auditoría y Exportación de la Conclusión Asistida del LLM.
    # Se impone una matemática precisa desde Python para bloquear cualquier alucinación conceptual de cálculos que un LLM puede intentar.
    porcentaje = (encontrados / total_validos * 100) if total_validos > 0 else 0
    concl = generar_reporte_cierre(total_validos, encontrados, tipos_finales, WORDLIST, porcentaje)
    
    # Cuadro visual finalizado con efectos matriz
    print(f"\n{C_MAIN}╔════════════════════════════════════════╗")
    print(f"║   SECUENCIA DE AUDITORÍA FINALIZADA    ║")
    print(f"╠════════════════════════════════════════╣")
    print(f"║ Compromisos únicos:   {encontrados:16} ║")
    print(f"║ Objetivo del lote:    {total_validos:16} ║")
    print(f"║ Registros duplicados: {total_duplicados:16} ║")
    print(f"║ Eficacia del Agente:  {porcentaje:15.2f}% ║")
    print(f"╚════════════════════════════════════════╝{RESET}")
    print(f"\n{C_AGENT}[Conclusión Técnica LLM]{RESET}\n{concl}\n")
    
    # Cierre de auditoría y detención del logger de eventos subyacentes.
    escribir_log("--- SESIÓN FINALIZADA LOGICAMENTE SIN ERRORES FATALES ---")

# Inicialización obligatoria como Script principal
if __name__ == "__main__":
    procesar()
