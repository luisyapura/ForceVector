#!/usr/bin/env python3
import os
import sys
import json
import requests
import re
from pathlib import Path

# Intentar importar el conector de PostgreSQL
try:
    import psycopg2
except ImportError:
    print("\033[91m[!] Error: Librería psycopg2 no encontrada. Ejecuta: pip install psycopg2-binary\033[0m")
    sys.exit(1)

# Constantes de color ANSI
COLOR_NEON_GREEN = "\033[38;5;82m"
COLOR_RESET = "\033[0m"
COLOR_INFO = "\033[96m"
COLOR_ERROR = "\033[91m"
COLOR_SUCCESS = "\033[92m"

BANNER = """
 ███████╗ ██████╗ ██████╗  ██████╗███████╗██╗   ██╗███████╗ ██████╗████████╗ ██████╗ ██████╗ 
 ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██║   ██║██╔════╝██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗
 █████╗  ██║   ██║██████╔╝██║     █████╗  ██║   ██║█████╗  ██║        ██║   ██║   ██║██████╔╝
 ██╔══╝  ██║   ██║██╔══██╗██║     ██╔══╝  ██║   ██║██╔══╝  ██║        ██║   ██║   ██║██╔══██╗
 ██║     ╚██████╔╝██║  ██║╚██████╗███████╗╚██████╔╝███████╗╚██████╗   ██║   ╚██████╔╝██║  ██║
 
               		  	[ FORCE VECTOR // IA PENTESTING ]
              			     [ MODO: ETHICAL MODE ]       
"""

def print_banner():
    """Imprime la cabecera en color verde neón estilo Metasploit."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{COLOR_NEON_GREEN}{BANNER}{COLOR_RESET}")

def check_directory_structure(base_path: Path):
    """Verifica y crea la estructura de directorios requerida."""
    directories = [
        "config",
        "agents",
        "logs",
        "projects"
    ]
    
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)

    init_py = base_path / "projects" / "__init__.py"
    if not init_py.exists():
        init_py.touch()

    client_py = base_path / "projects" / "ollama_client.py"
    if not client_py.exists():
        client_py.touch()

def generate_config(config_path: Path):
    """Solicita los datos al usuario y genera el archivo config.json."""
    print(f"\n{COLOR_INFO}[!] Archivo config.json no encontrado. Iniciando configuración...{COLOR_RESET}")
    
    server_host = input("  > IP del servidor Ollama [Ej. 192.168.1.50]: ").strip()
    server_port = input("  > Puerto del servidor Ollama [11434]: ").strip() or 11434
    keep_alive = input("  > Tiempo Keep Alive en segundos [0]: ").strip() or 0
    
    model_orch = input("  > Modelo Orquestador [Ej. qwen2.5-coder:7b-instruct]: ").strip()
    model_analy = input("  > Modelo Analizador [Ej. llama3.1:8b]: ").strip()

    print(f"\n{COLOR_INFO}[!] Configuración de Base de Datos (PostgreSQL Vectorial){COLOR_RESET}")
    db_host = input("  > Host PostgreSQL [127.0.0.1]: ").strip() or "127.0.0.1"
    db_port = input("  > Puerto PostgreSQL [5432]: ").strip() or 5432
    db_user = input("  > Usuario PostgreSQL [postgres]: ").strip() or "postgres"
    db_pass = input("  > Contraseña PostgreSQL: ").strip()
    db_name = input("  > Nombre de la Base de Datos [forcevector_db]: ").strip() or "forcevector_db"

    config_data = {
        "server": {
            "host": server_host,
            "port": int(server_port),
            "keep_alive_seconds": int(keep_alive)
        },
        "models": {
            "orchestrator": model_orch,
            "analyzer": model_analy
        },
        "database": {
            "host": db_host,
            "port": int(db_port),
            "user": db_user,
            "password": db_pass,
            "dbname": db_name
        }
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"{COLOR_SUCCESS}[+] Configuración guardada en {config_path}{COLOR_RESET}")
    return config_data

def check_ollama_connection(config_data, silent=False):
    """Comprueba la conectividad con la API del servidor Ollama."""
    host = config_data["server"]["host"]
    port = config_data["server"]["port"]
    url = f"http://{host}:{port}/api/tags"
    
    if not silent:
        print(f"[*] Verificando conexión con Ollama ({host}:{port})...", end=" ")
        
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            if not silent: print(f"{COLOR_SUCCESS}[ OK ]{COLOR_RESET}")
            return True
        else:
            if not silent: print(f"{COLOR_ERROR}[ FAIL ] (HTTP {response.status_code}){COLOR_RESET}")
            return False
    except requests.exceptions.RequestException as e:
        if not silent: print(f"{COLOR_ERROR}[ ERROR ] {e}{COLOR_RESET}")
        return False

def verify_and_configure_models(config_data, config_path: Path):
    """Obtiene los modelos de Ollama y valida que los configurados existan en el servidor."""
    host = config_data["server"]["host"]
    port = config_data["server"]["port"]
    url = f"http://{host}:{port}/api/tags"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            models_data = response.json().get("models", [])
            installed_models = [m["name"] for m in models_data]
        else:
            return config_data
    except requests.exceptions.RequestException:
        return config_data

    roles = ["orchestrator", "analyzer"]
    if "models" not in config_data:
        config_data["models"] = {}

    updated = False
    
    for role in roles:
        configured_model = config_data["models"].get(role, "")
        
        # Validar si falta configuración o si el modelo configurado no está instalado
        if not configured_model or configured_model not in installed_models:
            print(f"\n{COLOR_INFO}[*] Modelos instalados en Ollama: {', '.join(installed_models) if installed_models else 'Ninguno'}{COLOR_RESET}")
            if not configured_model:
                print(f"{COLOR_ERROR}[!] El rol '{role}' no tiene un modelo asignado en config.json.{COLOR_RESET}")
            else:
                print(f"{COLOR_ERROR}[!] El modelo '{configured_model}' configurado para el rol '{role}' no se encuentra instalado en el servidor.{COLOR_RESET}")
            
            respuesta = input(f"  > ¿Deseas configurar un modelo para '{role}' ahora? (s/n): ").strip().lower()
            if respuesta == 's':
                sugerencia = installed_models[0] if installed_models else "llama3.1:8b"
                nuevo_modelo = input(f"  > Introduce el nombre del modelo (ej. {sugerencia}): ").strip()
                config_data["models"][role] = nuevo_modelo
                updated = True
            else:
                print(f"{COLOR_INFO}[i] Advertencia: La ejecución del agente '{role}' podría fallar debido a falta de modelo.{COLOR_RESET}")

    # Guardar cambios si hubo actualizaciones
    if updated:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        print(f"{COLOR_SUCCESS}[+] Archivo config.json actualizado con éxito.{COLOR_RESET}")
        
    return config_data

def check_postgres_connection(config_data, silent=False):
    """Comprueba la conectividad con la base de datos PostgreSQL."""
    db_conf = config_data.get("database", {})
    
    if not silent:
        print(f"[*] Verificando conexión con PostgreSQL ({db_conf.get('host')}:{db_conf.get('port')})...", end=" ")
        
    try:
        conn = psycopg2.connect(
            host=db_conf.get("host"),
            port=db_conf.get("port"),
            user=db_conf.get("user"),
            password=db_conf.get("password"),
            dbname=db_conf.get("dbname"),
            connect_timeout=5
        )
        conn.close()
        if not silent: print(f"{COLOR_SUCCESS}[ OK ]{COLOR_RESET}")
        return True
    except psycopg2.OperationalError as e:
        error_msg = str(e).split('\n')[0]
        if not silent: print(f"{COLOR_ERROR}[ ERROR ] {error_msg}{COLOR_RESET}")
        return False

def setup_vector_database(config_data):
    """Establece la conexión persistente y prepara la extensión pgvector y tablas base."""
    db_conf = config_data.get("database", {})
    try:
        conn = psycopg2.connect(
            host=db_conf.get("host"),
            port=db_conf.get("port"),
            user=db_conf.get("user"),
            password=db_conf.get("password"),
            dbname=db_conf.get("dbname")
        )
        # Modo autocommit activado para evitar bloqueos por consultas abortadas
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS agent_memory (
                    id bigserial PRIMARY KEY,
                    task_id varchar(255),
                    content text,
                    embedding vector(4096)
                );
            """)
        return conn
    except psycopg2.Error as e:
        print(f"\n{COLOR_ERROR}[!] Error inicializando la base de datos vectorial: {e}{COLOR_RESET}")
        return None

def ask_ollama(prompt: str, config_data: dict, db_conn=None):
    """Envía el comando del usuario a Ollama, intercepta SQL si se genera, lo ejecuta e inyecta resultados."""
    host = config_data["server"]["host"]
    port = config_data["server"]["port"]
    model = config_data["models"].get("orchestrator")
    
    if not model:
        print(f"{COLOR_ERROR}[!] No hay un modelo orquestador configurado en config.json.{COLOR_RESET}")
        return

    url = f"http://{host}:{port}/api/generate"
    
    # Nuevo prompt de sistema que instruye el comportamiento "Agentic" y provee el esquema de BD
    system_prompt = (
        "Eres el Orquestador de ForceVector, un sistema avanzado de IA para auditorías técnicas. "
        "INSTRUCCIÓN CRÍTICA: Tienes conexión directa a PostgreSQL (pgvector). "
        "Para generar consultas SQL, DEBES basarte estrictamente en el siguiente esquema de base de datos:\n"
        "- Tabla 'cves': cve_id (PK VARCHAR), state, assigner, date_published, date_updated, embedding (vector)\n"
        "- Tabla 'cve_descriptions': id (PK SERIAL), cve_id (FK VARCHAR), lang, value (TEXT)\n"
        "- Tabla 'cve_affected': id (PK SERIAL), cve_id (FK VARCHAR), vendor, product, version, status\n"
        "- Tabla 'cve_references': id (PK SERIAL), cve_id (FK VARCHAR), url, name, refsource\n"
        "- Tabla 'agent_memory': id (PK BIGSERIAL), task_id, content, embedding (vector)\n\n"
        "Si el usuario pregunta por datos que requieren una consulta (ej. 'cuántos cve tenemos', 'listar vulnerabilidades'), "
        "NO asumas los datos ni le pidas al usuario que ejecute comandos. "
        "En su lugar, responde ÚNICA Y EXCLUSIVAMENTE con la consulta SQL válida para PostgreSQL envuelta en etiquetas ```sql y ```. "
        "El motor interceptará tu consulta, la ejecutará y te devolverá los resultados reales para que des la respuesta final. "
        "Si no necesitas hacer consultas, responde al usuario directamente de forma técnica y concisa en español neutro."
    )

    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": True
    }

    try:
        print(f"{COLOR_INFO}[Orquestador ({model})] > {COLOR_RESET}", end="", flush=True)
        response = requests.post(url, json=payload, stream=True, timeout=120)
        
        full_response = ""
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    print(chunk, end="", flush=True)
                    full_response += chunk
                    if data.get("done"):
                        print()
        else:
            print(f"\n{COLOR_ERROR}[!] Error HTTP {response.status_code} desde Ollama.{COLOR_RESET}")
            return

        # Interceptación: Comprobar si el modelo emitió una petición SQL
        sql_match = re.search(r'```sql\s*(.*?)\s*```', full_response, re.IGNORECASE | re.DOTALL)
        
        if sql_match and db_conn:
            sql_query = sql_match.group(1).strip()
            print(f"\n{COLOR_SUCCESS}[*] Interceptando operación de base de datos...{COLOR_RESET}")
            print(f"{COLOR_INFO}[*] Ejecutando: {sql_query}{COLOR_RESET}")
            
            try:
                with db_conn.cursor() as cur:
                    cur.execute(sql_query)
                    
                    if cur.description: # Hay resultados de retorno
                        results = cur.fetchall()
                        columns = [desc[0] for desc in cur.description]
                        
                        res_str = f"Columnas: {', '.join(columns)}\nResultados:\n"
                        for row in results[:15]: # Límite para no saturar tokens
                            res_str += str(row) + "\n"
                        if len(results) > 15:
                            res_str += f"... (y {len(results)-15} registros más ocultos)\n"
                    else:
                        res_str = "Consulta ejecutada correctamente (no hay filas de retorno)."
                
                print(f"{COLOR_SUCCESS}[+] Datos extraídos. Transfiriendo contexto al Orquestador...{COLOR_RESET}\n")
                
                # Segundo prompt: Reinyección RAG
                followup_prompt = (
                    f"El usuario te pidió: '{prompt}'. Ejecutaste la consulta requerida y la base de datos "
                    f"PostgreSQL devolvió los siguientes resultados verídicos:\n\n{res_str}\n\n"
                    "Con base estricta en estos datos, elabora la respuesta final al usuario, "
                    "no indiques que acabas de ejecutar la consulta, tan solo responde directamente con rigor técnico."
                )
                
                payload["prompt"] = followup_prompt
                print(f"{COLOR_INFO}[Orquestador ({model})] > {COLOR_RESET}", end="", flush=True)
                
                response2 = requests.post(url, json=payload, stream=True, timeout=120)
                if response2.status_code == 200:
                    for line in response2.iter_lines():
                        if line:
                            data = json.loads(line)
                            print(data.get("response", ""), end="", flush=True)
                            if data.get("done"):
                                print()
                                
            except psycopg2.Error as db_error:
                print(f"{COLOR_ERROR}[!] Error emitido por PostgreSQL: {db_error}{COLOR_RESET}")

    except requests.exceptions.RequestException as e:
        print(f"\n{COLOR_ERROR}[!] Fallo en la comunicación con Ollama: {e}{COLOR_RESET}")


def main():
    base_dir = Path.home() / "forcevector"
    config_file = base_dir / "config" / "config.json"

    # Preparativos silenciosos
    check_directory_structure(base_dir)

    # Cargar o generar configuración (con banner para contexto si necesita input)
    if not config_file.exists():
        print_banner()
        config_data = generate_config(config_file)
    else:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError:
            print(f"{COLOR_ERROR}[!] Error: config.json está corrupto. Verifica su sintaxis.{COLOR_RESET}")
            sys.exit(1)

    # Verificaciones previas que requieren interacción (prompts) antes de dibujar el bloque final
    if check_ollama_connection(config_data, silent=True):
        config_data = verify_and_configure_models(config_data, config_file)

    # Dibujado del bloque de estado operativo
    print_banner()
    print(" ─────────────────────────────────────────────────────────────────────────────")
    
    sys.stdout.write("  [*] Inicializando motor de reconocimiento (Recon Engine)............ ")
    sys.stdout.flush()
    print(f"{COLOR_SUCCESS}[  OK  ]{COLOR_RESET}")

    sys.stdout.write("  [*] Sincronizando base de conocimiento IA........................... ")
    sys.stdout.flush()
    if check_ollama_connection(config_data, silent=True):
        print(f"{COLOR_SUCCESS}[  OK  ]{COLOR_RESET}")
    else:
        print(f"{COLOR_ERROR}[ FAIL ]{COLOR_RESET}")

    sys.stdout.write("  [*] Analizando vulnerabilidades (Ethical Mode)...................... ")
    sys.stdout.flush()
    if "database" in config_data and check_postgres_connection(config_data, silent=True):
        print(f"{COLOR_SUCCESS}[  OK  ]{COLOR_RESET}")
    else:
        print(f"{COLOR_ERROR}[ FAIL ]{COLOR_RESET}")

    sys.stdout.write("  [*] Construyendo vectores de ataque (Safe Mode)..................... ")
    sys.stdout.flush()
    if config_data.get("models", {}).get("orchestrator"):
        print(f"{COLOR_SUCCESS}[  OK  ]{COLOR_RESET}")
    else:
        print(f"{COLOR_ERROR}[ FAIL ]{COLOR_RESET}")

    print(" ─────────────────────────────────────────────────────────────────────────────\n")
    print('  [i] "QUE LA FUERZA DEL CONOCIMIENTO TE GUÍE."\n')
    print(f"  {COLOR_NEON_GREEN}SISTEMA LISTO Y OPERATIVO.{COLOR_RESET}\n")

    # Establecer conexión persistente con la BD Vectorial
    db_conn = None
    if "database" in config_data:
        db_conn = setup_vector_database(config_data)
        if db_conn:
            print(f"[*] Conexión persistente a PostgreSQL (pgvector) establecida y lista para RAG.")

    print("[*] Entregando control al orquestador principal...")
    
    # Bucle principal para evitar el cierre (REPL)
    try:
        while True:
            comando = input(f"\n{COLOR_NEON_GREEN}ForceVector > {COLOR_RESET}").strip()

            if comando.lower() in ['exit', 'quit', 'salir']:
                print(f"{COLOR_INFO}[*] Finalizando procesos de Force Vector. Desconectando...{COLOR_RESET}")
                if db_conn and not db_conn.closed:
                    db_conn.close()
                break
            
            if not comando:
                continue

            if comando.lower() == 'status':
                db_status = "Conectada" if db_conn and not db_conn.closed else "Desconectada"
                print(f"[*] Estado: Orquestador en línea. Agentes en standby. Base de datos: {db_status}")
            else:
                print(f"[*] Evaluando objetivo de auditoría: {comando}")
                ask_ollama(comando, config_data, db_conn)

    except KeyboardInterrupt:
        print(f"\n{COLOR_INFO}[*] Interrupción manual (Ctrl+C) detectada. Cerrando de forma segura...{COLOR_RESET}")
        if db_conn and not db_conn.closed:
            db_conn.close()
        sys.exit(0)
    except Exception as e:
        print(f"\n{COLOR_ERROR}[!] Excepción crítica en el orquestador: {e}{COLOR_RESET}")
        if db_conn and not db_conn.closed:
            db_conn.close()
        sys.exit(1)

if __name__ == "__main__":
    main()
