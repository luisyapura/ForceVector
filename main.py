#!/usr/bin/env python3
import os
import sys
import json
import requests
import re
import traceback
from pathlib import Path

# Añadir directorio actual al PATH para asegurar resolución del paquete 'agents'
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Intentar importar dependencias core y Fases 1/2
try:
    import psycopg2
except ImportError:
    print("\033[91m[!] Error: Librería psycopg2 no encontrada. Ejecuta: pip install psycopg2-binary\033[0m")
    sys.exit(1)

try:
    from agents import recon_agent
    from agents import scan_agent
except Exception as e:
    print(f"\033[91m[!] Error cargando agentes base: {e}\033[0m")
    recon_agent = None
    scan_agent = None

# Constantes de color ANSI
COLOR_NEON_GREEN = "\033[38;5;82m"
COLOR_RESET = "\033[0m"
COLOR_INFO = "\033[96m"
COLOR_ERROR = "\033[91m"
COLOR_SUCCESS = "\033[92m"
COLOR_YELLOW = "\033[38;5;220m"

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
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{COLOR_NEON_GREEN}{BANNER}{COLOR_RESET}")

def print_operational_flow():
    print(f"\n{COLOR_INFO}=== FLUJO OPERATIVO ==={COLOR_RESET}")
    print(f"{'Fase':<25} | {'Automatización':<15}")
    print("-" * 43)
    print(f"{'1. Reconocimiento (Descubrimiento)':<25} | {COLOR_NEON_GREEN}Autónoma{COLOR_RESET}")
    print(f"{'2. Escaneo (Superficie/Versiones)':<25} | {COLOR_NEON_GREEN}Autónoma{COLOR_RESET}")
    print(f"{'3. Modelado de amenazas':<25} | {COLOR_NEON_GREEN}Autónoma (Ciclo FOR){COLOR_RESET}")
    print(f"{'4. Enumeración':<25} | {COLOR_NEON_GREEN}Autónoma{COLOR_RESET}")
    print(f"{'5. Explotación':<25} | {COLOR_YELLOW}Supervisada (HITL){COLOR_RESET}")
    print(f"{'6. Post-explotación':<25} | {COLOR_YELLOW}Supervisada{COLOR_RESET}")
    print(f"{'7. Reporte':<25} | {COLOR_NEON_GREEN}Autónoma{COLOR_RESET}")
    print("-" * 43)

def check_directory_structure(base_path: Path):
    directories = ["config", "agents", "logs", "projects"]
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    (base_path / "projects" / "__init__.py").touch(exist_ok=True)
    (base_path / "agents" / "__init__.py").touch(exist_ok=True)
    (base_path / "projects" / "ollama_client.py").touch(exist_ok=True)

def generate_config(config_path: Path):
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
        "server": {"host": server_host, "port": int(server_port), "keep_alive_seconds": int(keep_alive)},
        "models": {
            "orchestrator": model_orch, 
            "analyzer": model_analy,
            "temperature_orch": 0.1,
            "temperature_exploit": 0.0
        },
        "database": {"host": db_host, "port": int(db_port), "user": db_user, "password": db_pass, "dbname": db_name}
    }
    with open(config_path, 'w', encoding='utf-8') as f: json.dump(config_data, f, indent=2)
    print(f"{COLOR_SUCCESS}[+] Configuración guardada en {config_path}{COLOR_RESET}")
    return config_data

def check_ollama_connection(config_data, silent=False):
    host, port = config_data["server"]["host"], config_data["server"]["port"]
    url = f"http://{host}:{port}/api/tags"
    if not silent: print(f"[*] Verificando conexión con Ollama ({host}:{port})...", end=" ")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            if not silent: print(f"{COLOR_SUCCESS}[ OK ]{COLOR_RESET}")
            return True
        if not silent: print(f"{COLOR_ERROR}[ FAIL ] (HTTP {response.status_code}){COLOR_RESET}")
        return False
    except requests.exceptions.RequestException as e:
        if not silent: print(f"{COLOR_ERROR}[ ERROR ] {e}{COLOR_RESET}")
        return False

def verify_and_configure_models(config_data, config_path: Path):
    host, port = config_data["server"]["host"], config_data["server"]["port"]
    url = f"http://{host}:{port}/api/tags"
    try:
        response = requests.get(url, timeout=5)
        installed_models = [m["name"] for m in response.json().get("models", [])] if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        return config_data

    updated = False
    for role in ["orchestrator", "analyzer"]:
        configured_model = config_data.get("models", {}).get(role, "")
        if not configured_model or configured_model not in installed_models:
            print(f"\n{COLOR_INFO}[*] Modelos instalados en Ollama: {', '.join(installed_models) if installed_models else 'Ninguno'}{COLOR_RESET}")
            print(f"{COLOR_ERROR}[!] Falla de validación en modelo para el rol '{role}'.{COLOR_RESET}")
            if input(f"  > ¿Configurar un modelo para '{role}' ahora? (s/n): ").strip().lower() == 's':
                config_data["models"][role] = input(f"  > Nombre del modelo: ").strip()
                updated = True
    
    if "temperature_orch" not in config_data["models"]:
        config_data["models"]["temperature_orch"] = 0.1
        config_data["models"]["temperature_exploit"] = 0.0
        updated = True

    if updated:
        with open(config_path, 'w', encoding='utf-8') as f: json.dump(config_data, f, indent=2)
    return config_data

def check_postgres_connection(config_data, silent=False):
    db_conf = config_data.get("database", {})
    if not silent: print(f"[*] Verificando conexión con PostgreSQL ({db_conf.get('host')}:{db_conf.get('port')})...", end=" ")
    try:
        conn = psycopg2.connect(
            host=db_conf.get("host"), port=db_conf.get("port"),
            user=db_conf.get("user"), password=db_conf.get("password"),
            dbname=db_conf.get("dbname"), connect_timeout=5
        )
        conn.close()
        if not silent: print(f"{COLOR_SUCCESS}[ OK ]{COLOR_RESET}")
        return True
    except psycopg2.OperationalError as e:
        error_msg = str(e).split('\n')[0]
        if not silent: print(f"{COLOR_ERROR}[ ERROR ] {error_msg}{COLOR_RESET}")
        return False

def setup_vector_database(config_data):
    db_conf = config_data.get("database", {})
    try:
        conn = psycopg2.connect(
            host=db_conf.get("host"), port=db_conf.get("port"),
            user=db_conf.get("user"), password=db_conf.get("password"), dbname=db_conf.get("dbname")
        )
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

def direct_ollama_query(prompt: str, config_data: dict) -> str:
    host, port = config_data["server"]["host"], config_data["server"]["port"]
    model = config_data["models"].get("analyzer")
    temp = config_data.get("models", {}).get("temperature_orch", 0.1)

    url = f"http://{host}:{port}/api/generate"
    
    payload = {
        "model": model, 
        "prompt": prompt,
        "system": "Eres un analista de ciberseguridad riguroso. Tu salida DEBE SER EXCLUSIVAMENTE un objeto JSON válido. No incluyas explicaciones en texto plano, saludos ni etiquetas markdown ajenas al JSON.",
        "stream": True,
        "options": {"temperature": temp, "num_predict": 2048}
    }
    
    full_response = ""
    try:
        print(f"{COLOR_INFO}    └─ [Analista IA] procesando vector... {COLOR_RESET}", end="", flush=True)
        response = requests.post(url, json=payload, stream=True, timeout=180)
        
        if response.status_code == 200:
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        data = json.loads(line)
                        chunk = data.get("response", "")
                        print(chunk, end="", flush=True)
                        full_response += chunk
                    except json.JSONDecodeError:
                        pass
        print()
        return full_response
    except requests.exceptions.RequestException:
        print(f"{COLOR_ERROR}\n    └─ [!] Error de conexión con el LLM en iteración.{COLOR_RESET}")
        return ""

def execute_autonomous_flow(target: str, config_data: dict, db_conn, logs_path: Path, skip_recon: bool = False):
    """
    Controlador del Flujo Operativo Autónomo Fases 1 a 3.
    """
    if not recon_agent or not scan_agent:
        print(f"{COLOR_ERROR}[!] Módulos de Fases 1/2 no cargados.{COLOR_RESET}")
        return

    hosts_activos = []
        
    # ---------------------------------------------------------
    # FASE 1: RECONOCIMIENTO
    # ---------------------------------------------------------
    if not skip_recon:
        print(f"\n{COLOR_INFO}=== INICIANDO FASE 1: RECONOCIMIENTO (Descubrimiento) ==={COLOR_RESET}")
        print(f"{COLOR_INFO}[*] Mapeando red con Ping Sweep: {target}...{COLOR_RESET}")
        
        try:
            hosts_activos = recon_agent.run_recon(target, logs_path)
        except Exception as e:
            print(f"{COLOR_ERROR}[!] Error en agente de reconocimiento: {e}{COLOR_RESET}")
            return
        
        if not hosts_activos:
            print(f"{COLOR_ERROR}[-] No se detectaron hosts activos. Abortando flujo.{COLOR_RESET}")
            return
            
        print(f"{COLOR_SUCCESS}[+] Fase 1 completada. {len(hosts_activos)} hosts activos detectados.{COLOR_RESET}")
    else:
        print(f"\n{COLOR_INFO}[*] Omitiendo Fase 1 (Reconocimiento). Apuntando directamente al host: {target}{COLOR_RESET}")
        hosts_activos = [{"ip": target, "mac": "Desconocida (Escaneo Directo)"}]
    
    # ---------------------------------------------------------
    # FASE 2: ESCANEO
    # ---------------------------------------------------------
    print(f"\n{COLOR_INFO}=== INICIANDO FASE 2: ESCANEO (Vulnerability Assessment) ==={COLOR_RESET}")
    
    vectores_guardados = 0
    if db_conn:
        try:
            with db_conn.cursor() as cur:
                cur.execute("DELETE FROM agent_memory WHERE task_id = 'recon_port_vector'")
                
                for idx, host in enumerate(hosts_activos, 1):
                    ip = host.get("ip")
                    mac = host.get("mac")
                    
                    if skip_recon:
                        host_dir = logs_path / "scans_directos" / target.replace('/', '_')
                    else:
                        host_dir = logs_path / target.replace('/', '_') / ip
                        
                    print(f"\n{COLOR_INFO}[*] Lanzando escaneo profundo en objetivo [{idx}/{len(hosts_activos)}]: {ip}{COLOR_RESET}")
                    
                    scan_data = scan_agent.run_scan(ip, host_dir)
                    os_info = scan_data.get("os", "Desconocido")
                    ports = scan_data.get("ports", [])
                    
                    print(f"    └─ MAC: {mac:<17} | OS: {os_info}")
                    
                    if ports:
                        print(f"    └─ Puertos/Servicios detectados:")
                        for p in ports:
                            color_proto = COLOR_YELLOW if p.get('protocol') == 'udp' else COLOR_RESET
                            print(f"       - {p.get('portid'):>5}/{p.get('protocol'):<4} : {color_proto}{p.get('service'):<12}{COLOR_RESET} ({p.get('version')})")
                            
                            content_vector = json.dumps({
                                "ip": ip, "os": os_info,
                                "puerto": p.get('portid'), "protocolo": p.get('protocol'),
                                "servicio": p.get('service'), "version": p.get('version')
                            })
                            cur.execute("INSERT INTO agent_memory (task_id, content) VALUES (%s, %s)", ("recon_port_vector", content_vector))
                            vectores_guardados += 1
                    else:
                        print(f"    └─ No se detectaron puertos abiertos filtrables.")
                        
            print(f"\n{COLOR_SUCCESS}[+] Fase 2 completada. Se han almacenado {vectores_guardados} vectores individuales en PostgreSQL.{COLOR_RESET}")
        except psycopg2.Error as e:
            print(f"{COLOR_ERROR}[!] Error en BD durante escaneo: {e}{COLOR_RESET}")
            return

    # ---------------------------------------------------------
    # FASE 3: MODELADO DE AMENAZAS
    # ---------------------------------------------------------
    print(f"\n{COLOR_INFO}=== INICIANDO FASE 3: MODELADO DE AMENAZAS (LLM Iterativo) ==={COLOR_RESET}")
    
    objetivos_analizados = []
    
    if db_conn:
        try:
            with db_conn.cursor() as cur:
                cur.execute("SELECT content FROM agent_memory WHERE task_id = 'recon_port_vector';")
                vectores_crudos = cur.fetchall()
                
            if not vectores_crudos:
                print(f"{COLOR_YELLOW}[*] No existen vectores de puertos válidos para analizar en Fase 3.{COLOR_RESET}")
                return
                
            for idx, vec in enumerate(vectores_crudos, 1):
                vec_data = json.loads(vec[0])
                ip, port, proto = vec_data['ip'], vec_data['puerto'], vec_data['protocolo']
                srv, ver = vec_data['servicio'], vec_data['version']
                
                print(f"\n{COLOR_INFO}[*] Analizando Vector [{idx}/{len(vectores_crudos)}]: {ip} -> {port}/{proto} ({srv} - {ver}){COLOR_RESET}")
                
                prompt_iterativo = (
                    "Analiza el siguiente vector de ataque.\n"
                    "REGLAS CRÍTICAS: Devuelve ÚNICA Y EXCLUSIVAMENTE formato JSON. "
                    "Correlaciona la versión con identificadores CVE reales.\n"
                    f"DATOS: {json.dumps(vec_data)}\n\n"
                    "FORMATO JSON: {\"cve_identificados\": [\"CVE-XXXX\"], \"vectores_ataque\": \"Descripción...\", \"herramienta_sugerida\": \"comando\", \"categoria_vector\": \"rce\"}"
                )
                
                resultado_llm = direct_ollama_query(prompt_iterativo, config_data)
                
                try:
                    json_match = re.search(r'\{.*\}', resultado_llm, re.DOTALL)
                    clean_json = json_match.group(0) if json_match else "{}"
                    analisis_vector = json.loads(clean_json)
                    vector_completo = {**vec_data, **analisis_vector}
                    objetivos_analizados.append(vector_completo)
                except json.JSONDecodeError:
                    pass
            
            with db_conn.cursor() as cur:
                cur.execute("DELETE FROM agent_memory WHERE task_id = 'threat_model_results'")
                cur.execute("INSERT INTO agent_memory (task_id, content) VALUES (%s, %s)", 
                            ("threat_model_results", json.dumps(objetivos_analizados)))
            
            print(f"\n{COLOR_SUCCESS}[+] Fase 3: Análisis finalizado y persistido en la Base de Datos.{COLOR_RESET}")

            modelos_por_ip = {}
            for obj in objetivos_analizados:
                ip = obj['ip']
                if ip not in modelos_por_ip:
                    modelos_por_ip[ip] = []
                modelos_por_ip[ip].append(obj)

            print(f"{COLOR_INFO}[*] Generando archivos de contexto para la Fase 4 (Enumeración)...{COLOR_RESET}")
            for ip, modelos in modelos_por_ip.items():
                if skip_recon:
                    host_dir = logs_path / "scans_directos" / target.replace('/', '_')
                else:
                    host_dir = logs_path / target.replace('/', '_') / ip
                
                host_dir.mkdir(parents=True, exist_ok=True)
                output_file = host_dir / f"threat_model_{ip.replace('.', '_')}.json"
                
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(modelos, f, indent=4)
                    print(f"{COLOR_SUCCESS}    └─ Reporte de amenazas guardado: {output_file}{COLOR_RESET}")
                except IOError as e:
                    print(f"{COLOR_ERROR}    └─ [!] Error guardando contexto para {ip}: {e}{COLOR_RESET}")

            print(f"\n{COLOR_YELLOW}[*] Fases completadas. Ejecuta 'exploit <IP>' para iniciar la Fase 4 y 5.{COLOR_RESET}")
            
        except psycopg2.Error as e:
            print(f"{COLOR_ERROR}[!] Error en operaciones PostgreSQL Fase 3: {e}{COLOR_RESET}")

def execute_exploitation_phase(target_ip: str, config_data: dict, logs_path: Path):
    """
    Fases 4 y 5: Implementa carga perezosa y aislada (lazy loading) 
    para proteger el arranque de dependencias erróneas.
    """
    print(f"\n{COLOR_INFO}=== INICIANDO FASES 4 Y 5: EXPLOTACIÓN SUPERVISADA (HITL) ==={COLOR_RESET}")
    print(f"{COLOR_INFO}[*] Recuperando contexto persistente para {target_ip}...{COLOR_RESET}")
    
    target_filename = f"threat_model_{target_ip.replace('.', '_')}.json"
    encontrados = list(logs_path.rglob(target_filename))
    
    if not encontrados:
        print(f"{COLOR_ERROR}[-] Contexto no encontrado para {target_ip}. Debes ejecutar 'recon' o 'scan' primero.{COLOR_RESET}")
        return
        
    threat_model_path = encontrados[0]
    print(f"{COLOR_SUCCESS}[+] Contexto cargado exitosamente desde: {threat_model_path}{COLOR_RESET}")
    
    try:
        from agents import exploit_agent
        exploit_agent.run_exploitation_plan(str(threat_model_path), config_data)
    except Exception as e:
        print(f"\n{COLOR_ERROR}[!] Error crítico al cargar o ejecutar el Agente de Explotación.{COLOR_RESET}")
        print(f"{COLOR_YELLOW}[DEBUG] Traza del error para corregir tu código:\n{traceback.format_exc()}{COLOR_RESET}")

def execute_report_phase(target_ip: str, base_dir: Path, logs_path: Path):
    """
    Fase 7: Generación de reporte profesional automatizado basado en evidencias.
    Implementa lazy-loading de dependencias para no bloquear el script base.
    """
    print(f"\n{COLOR_INFO}=== INICIANDO FASE 7: GENERACIÓN DE REPORTE ({target_ip}) ==={COLOR_RESET}")
    print(f"{COLOR_INFO}[*] Recuperando contexto persistente y evidencias...{COLOR_RESET}")
    
    target_filename = f"threat_model_{target_ip.replace('.', '_')}.json"
    encontrados = list(logs_path.rglob(target_filename))
    
    if not encontrados:
        print(f"{COLOR_ERROR}[-] Contexto no encontrado para {target_ip}. No hay datos auditados para documentar.{COLOR_RESET}")
        return
        
    threat_model_path = encontrados[0]
    
    try:
        from agents import report_agent
        report_agent.generate_pdf_report(str(base_dir), str(threat_model_path))
    except ImportError as e:
        print(f"{COLOR_ERROR}[!] Error: Módulo report_agent o dependencias (Jinja2/WeasyPrint) no encontradas.\nDetalle: {e}{COLOR_RESET}")
        print(f"{COLOR_YELLOW}[i] Ejecuta: sudo apt update && sudo apt install -y python3-jinja2 python3-weasyprint{COLOR_RESET}")
    except Exception as e:
        print(f"\n{COLOR_ERROR}[!] Error crítico al generar el reporte: {e}{COLOR_RESET}")
        print(f"{COLOR_YELLOW}[DEBUG] Traza:\n{traceback.format_exc()}{COLOR_RESET}")

def ask_ollama(prompt: str, config_data: dict, db_conn=None, follow_up_task=None):
    host, port = config_data["server"]["host"], config_data["server"]["port"]
    model = config_data["models"].get("orchestrator")
    temp = config_data.get("models", {}).get("temperature_orch", 0.1)
    
    if not model:
        print(f"{COLOR_ERROR}[!] Orquestador no configurado.{COLOR_RESET}")
        return ""

    url = f"http://{host}:{port}/api/generate"
    
    system_prompt = (
        "Eres el Orquestador de ForceVector, un sistema avanzado de IA para auditorías técnicas.\n"
        "REGLA CRÍTICA 1 (IDIOMA): TU ÚNICO IDIOMA ES EL ESPAÑOL.\n"
        "REGLA CRÍTICA 2 (BD): Tienes conexión directa a PostgreSQL. Las operaciones DROP, DELETE, TRUNCATE están denegadas.\n"
        "REGLA CRÍTICA 3 (FORMATO): Si necesitas buscar datos, tu respuesta DEBE ser ÚNICA Y EXCLUSIVAMENTE el bloque ```sql y ```."
    )

    payload = {
        "model": model, "prompt": prompt, "system": system_prompt, "stream": True,
        "options": {"num_ctx": 8192, "num_predict": 4096, "temperature": temp}
    }

    try:
        print(f"{COLOR_INFO}[Orquestador] > {COLOR_RESET}", end="", flush=True)
        response = requests.post(url, json=payload, stream=True, timeout=300)
        
        full_response = ""
        is_done = False
        
        if response.status_code == 200:
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        data = json.loads(line)
                        chunk = data.get("response", "")
                        print(chunk, end="", flush=True)
                        full_response += chunk
                        if data.get("done"):
                            is_done = True
                            print()
                    except json.JSONDecodeError: pass
            
            if not is_done:
                print(f"\n{COLOR_ERROR}[!] Interrupción anormal de Ollama.{COLOR_RESET}")
        else:
            print(f"\n{COLOR_ERROR}[!] Error HTTP {response.status_code}{COLOR_RESET}")
            return ""

        sql_match = re.search(r'```sql\s*(.*?)\s*```', full_response, re.IGNORECASE | re.DOTALL)
        if sql_match and db_conn:
            sql_query = sql_match.group(1).strip()
            print(f"\n{COLOR_SUCCESS}[*] Interceptando consulta de base de datos extraída del Orquestador...{COLOR_RESET}")
            
            if re.search(r'\b(drop|delete|truncate|alter|grant|revoke)\b', sql_query, re.IGNORECASE):
                res_str = "ERROR: Operación destructiva denegada."
            else:
                print(f"{COLOR_INFO}[*] Ejecutando en pgvector: {sql_query}{COLOR_RESET}")
                try:
                    with db_conn.cursor() as cur:
                        cur.execute(sql_query)
                        if cur.description:
                            results = cur.fetchall()
                            res_str = f"Columnas: {', '.join([desc[0] for desc in cur.description])}\nResultados:\n"
                            for row in results[:15]:
                                res_str += str(tuple([str(item)[:8000] + "..." if len(str(item)) > 8000 else str(item) for item in row])) + "\n"
                        else:
                            res_str = "Consulta ejecutada correctamente (sin retorno)."
                    print(f"{COLOR_SUCCESS}[+] Datos extraídos de PostgreSQL. Transfiriendo contexto técnico al Analista LLM...{COLOR_RESET}\n")
                except psycopg2.Error as e:
                    res_str = f"ERROR EN POSTGRESQL: {e}"

            payload["system"] = (
                "Eres el Analista de ForceVector. Analiza resultados de base de datos y responde de forma técnica en ESPAÑOL NEUTRO. "
                "No uses modismos. Limítate a interpretar los datos empíricos."
            )
            
            if follow_up_task:
                payload["prompt"] = f"Resultados de la Base de Datos:\n{res_str}\n\nInstrucción Estratégica: {follow_up_task}"
            else:
                payload["prompt"] = f"Petición original: '{prompt}'\nResultados BD:\n{res_str}\n\nInstrucción: Formula tu análisis y recomendaciones basadas estrictamente en estos datos."
                
            print(f"{COLOR_INFO}[Analista LLM] > {COLOR_RESET}", end="", flush=True)
            
            response2 = requests.post(url, json=payload, stream=True, timeout=300)
            full_response2 = ""
            if response2.status_code == 200:
                for line in response2.iter_lines(decode_unicode=True):
                    if line:
                        try:
                            data = json.loads(line)
                            chunk = data.get("response", "")
                            print(chunk, end="", flush=True)
                            full_response2 += chunk
                            if data.get("done"): print()
                        except json.JSONDecodeError: pass
            
            return full_response2

        return full_response

    except requests.exceptions.RequestException as e:
        print(f"\n{COLOR_ERROR}[!] Fallo en Ollama: {e}{COLOR_RESET}")
        return ""

def main():
    base_dir = Path.home() / "forcevector"
    config_file = base_dir / "config" / "config.json"
    logs_dir = base_dir / "logs"

    check_directory_structure(base_dir)

    if not config_file.exists():
        print_banner()
        config_data = generate_config(config_file)
    else:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError:
            print(f"{COLOR_ERROR}[!] Error: config.json corrupto.{COLOR_RESET}")
            sys.exit(1)

    if check_ollama_connection(config_data, silent=True):
        config_data = verify_and_configure_models(config_data, config_file)

    print_banner()
    print(" ─────────────────────────────────────────────────────────────────────────────")
    
    # Comprobación de estado física (solo mira si el archivo existe en disco)
    agents_dir = base_dir / "agents"
    recon_ok = (agents_dir / "recon_agent.py").exists()
    scan_ok = (agents_dir / "scan_agent.py").exists()
    exploit_ok = (agents_dir / "exploit_agent.py").exists()
    report_ok = (agents_dir / "report_agent.py").exists()
    
    sys.stdout.write("  [*] Inicializando motor de reconocimiento (Recon Engine)............ ")
    sys.stdout.flush()
    print(f"{COLOR_SUCCESS}[  OK  ]{COLOR_RESET}" if recon_ok else f"{COLOR_ERROR}[ FAIL ]{COLOR_RESET}")

    sys.stdout.write("  [*] Inicializando motor de escaneo profundo (Scan Engine)........... ")
    sys.stdout.flush()
    print(f"{COLOR_SUCCESS}[  OK  ]{COLOR_RESET}" if scan_ok else f"{COLOR_ERROR}[ FAIL ]{COLOR_RESET}")
    
    sys.stdout.write("  [*] Inicializando motor de explotación (Exploit Engine)............. ")
    sys.stdout.flush()
    print(f"{COLOR_SUCCESS}[  OK  ]{COLOR_RESET}" if exploit_ok else f"{COLOR_YELLOW}[ WARN ]{COLOR_RESET}")

    sys.stdout.write("  [*] Inicializando motor de reportes (Report Engine)................. ")
    sys.stdout.flush()
    print(f"{COLOR_SUCCESS}[  OK  ]{COLOR_RESET}" if report_ok else f"{COLOR_YELLOW}[ WARN ]{COLOR_RESET}")

    sys.stdout.write("  [*] Sincronizando base de conocimiento IA........................... ")
    sys.stdout.flush()
    print(f"{COLOR_SUCCESS}[  OK  ]{COLOR_RESET}" if check_ollama_connection(config_data, silent=True) else f"{COLOR_ERROR}[ FAIL ]{COLOR_RESET}")

    sys.stdout.write("  [*] Analizando vulnerabilidades (Ethical Mode)...................... ")
    sys.stdout.flush()
    print(f"{COLOR_SUCCESS}[  OK  ]{COLOR_RESET}" if "database" in config_data and check_postgres_connection(config_data, silent=True) else f"{COLOR_ERROR}[ FAIL ]{COLOR_RESET}")
    print(" ─────────────────────────────────────────────────────────────────────────────\n")
    print('  [i] "QUE LA FUERZA DEL CONOCIMIENTO TE GUÍE."')
    print(f"  [i] Comandos: 'flow' | 'recon <CIDR>' | 'scan <IP>' | 'exploit <IP>' | 'report <IP>'\n")
    
    db_conn = setup_vector_database(config_data) if "database" in config_data else None

    try:
        while True:
            comando = input(f"\n{COLOR_NEON_GREEN}ForceVector > {COLOR_RESET}").strip()

            if comando.lower() in ['exit', 'quit', 'salir']:
                print(f"{COLOR_INFO}[*] Desconectando...{COLOR_RESET}")
                break
                
            if not comando:
                continue
                
            if comando.lower() == 'status':
                db_status = "Conectada" if db_conn and not db_conn.closed else "Desconectada"
                print(f"[*] Estado: Orquestador en línea. Agentes en standby. BD: {db_status}")
            elif comando.lower() == 'flow':
                print_operational_flow()
            elif comando.lower().startswith('recon '):
                target = comando.split(' ', 1)[1].strip()
                execute_autonomous_flow(target, config_data, db_conn, logs_dir, skip_recon=False)
            elif comando.lower().startswith('scan '):
                target = comando.split(' ', 1)[1].strip()
                execute_autonomous_flow(target, config_data, db_conn, logs_dir, skip_recon=True)
            elif comando.lower().startswith('exploit '):
                target = comando.split(' ', 1)[1].strip()
                execute_exploitation_phase(target, config_data, logs_dir)
            elif comando.lower().startswith('report '):
                target = comando.split(' ', 1)[1].strip()
                execute_report_phase(target, base_dir, logs_dir)
            else:
                print(f"[*] Evaluando objetivo de auditoría: {comando}")
                ask_ollama(comando, config_data, db_conn)

    except KeyboardInterrupt:
        print(f"\n{COLOR_INFO}[*] Interrupción manual (Ctrl+C). Cerrando...{COLOR_RESET}")
    except Exception as e:
        print(f"\n{COLOR_ERROR}[!] Excepción crítica en el orquestador: {e}{COLOR_RESET}")
    finally:
        if db_conn and not db_conn.closed:
            db_conn.close()
        sys.exit(0)

if __name__ == "__main__":
    main()
