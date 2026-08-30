#!/usr/bin/env python3
import os
import sys
import json
import socket
import time
from pathlib import Path

# Cargar soporte nativo de TTY (fundamental para historial y flechas en Linux)
try:
    import readline
except ImportError:
    pass

# Añadir directorio actual al PATH para asegurar resolución de paquetes locales
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Importaciones segmentadas desde la capa de funciones / core
from functions.ui import (
    print_banner, print_operational_flow, 
    COLOR_NEON_GREEN, COLOR_RESET, COLOR_INFO, COLOR_ERROR, COLOR_SUCCESS, COLOR_YELLOW
)
from functions.config import check_directory_structure, generate_config, verify_and_configure_models
from functions.database import setup_vector_database, check_postgres_connection
from functions.llm_client import check_ollama_connection, ask_ollama
from functions.orchestrator import (
    execute_autonomous_flow, 
    execute_exploitation_phase, 
    execute_post_exploitation_phase, 
    execute_report_phase
)

def _print_check(mensaje: str, estado: bool, warning_only: bool = False):
    """Función auxiliar para imprimir estados de forma alineada y vistosa."""
    sys.stdout.write(f"  [*] {mensaje:<52} ")
    sys.stdout.flush()
    time.sleep(0.1) # Pequeño efecto visual de diagnóstico
    
    if estado:
        print(f"[{COLOR_SUCCESS}  OK  {COLOR_RESET}]")
    else:
        if warning_only:
            print(f"[{COLOR_YELLOW} WARN {COLOR_RESET}]")
        else:
            print(f"[{COLOR_ERROR} FAIL {COLOR_RESET}]")

def main():
    base_dir = Path(current_dir)
    config_file = base_dir / "config" / "config.json"
    logs_dir = base_dir / "logs"

    # Preparar el entorno de directorios
    check_directory_structure(base_dir)

    # Carga o creación de configuración silenciosa
    if not config_file.exists():
        print_banner()
        config_data = generate_config(config_file)
    else:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError:
            print(f"{COLOR_ERROR}[!] Error: config.json corrupto. Bórralo y reinicia.{COLOR_RESET}")
            sys.exit(1)

    # Verificar configuración de modelos
    if check_ollama_connection(config_data, silent=True):
        config_data = verify_and_configure_models(config_data, config_file)

    # --- INICIO DE INTERFAZ GRÁFICA ---
    print_banner()
    
    print(f"{COLOR_INFO} ┌─[ DIAGNÓSTICO DE SISTEMA ]─────────────────────────────────────────────────┐{COLOR_RESET}")
    
    # 1. Comprobación de existencia de los agentes de fase
    print(f" {COLOR_INFO}├─[ Módulos Lógicos ]{COLOR_RESET}")
    agents_dir = base_dir / "agents"
    recon_ok = (agents_dir / "recon_agent.py").exists()
    scan_ok = (agents_dir / "scan_agent.py").exists()
    exploit_ok = (agents_dir / "exploit_agent.py").exists()
    post_ok = (agents_dir / "post_exploitation" / "agent.py").exists()
    
    _print_check("Motor de reconocimiento (Recon Engine)", recon_ok)
    _print_check("Motor de escaneo profundo (Scan Engine)", scan_ok)
    _print_check("Motor de explotación (Exploit Engine)", exploit_ok, warning_only=True)
    _print_check("Motor de post-explotación (Modular Engine)", post_ok, warning_only=True)

    # 2. Infraestructura Core (Bloqueos Críticos)
    print(f" {COLOR_INFO}├─[ Infraestructura Core ]{COLOR_RESET}")
    
    # Ollama Check
    ollama_ok = check_ollama_connection(config_data, silent=True)
    _print_check("Conexión con Cerebro Cognitivo (Ollama API)", ollama_ok)
    
    # PostgreSQL Check
    db_ok = False
    if "database" in config_data:
        db_ok = check_postgres_connection(config_data, silent=True)
    _print_check("Conexión con Memoria Vectorial (PostgreSQL)", db_ok)

    # EVALUACIÓN DE BLOQUEO (Hard-Stop)
    if not ollama_ok or not db_ok:
        print(f" {COLOR_INFO}└────────────────────────────────────────────────────────────────────────┘{COLOR_RESET}\n")
        print(f"{COLOR_ERROR}[!] SECUENCIA DE INICIO ABORTADA: INFRAESTRUCTURA CORE INACCESIBLE.{COLOR_RESET}")
        if not ollama_ok:
            print(f"{COLOR_YELLOW}  -> El servidor Ollama no responde. Inícia el servidor principal{COLOR_RESET}")
        if not db_ok:
            print(f"{COLOR_YELLOW}  -> PostgreSQL no responde. Inícialo con: systemctl start postgresql{COLOR_RESET}")
        print("\nSaliendo...")
        sys.exit(1)

    # 3. Servicios de Pivoting (MSF RPC)
    print(f" {COLOR_INFO}├─[ Servicios Tácticos Externos ]{COLOR_RESET}")
    rpc_conf = config_data.get("msfrpc", {"password": "msf", "port": 55552, "ssl": False})
    config_data["msfrpc"] = rpc_conf
    port = rpc_conf["port"]
    pwd = rpc_conf["password"]
    
    rpc_ok = False
    sys.stdout.write(f"  [*] Demonio MSF RPC (Pivoting Backend).................. ")
    sys.stdout.flush()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('127.0.0.1', port)) == 0:
            rpc_ok = True
            print(f"[{COLOR_SUCCESS}  OK  {COLOR_RESET}] (Activo)")
            
    if not rpc_ok:
        # Lanzamiento del demonio en background
        os.system(f"msfrpcd -P {pwd} -p {port} -a 127.0.0.1 -S >/dev/null 2>&1")
        for _ in range(15):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('127.0.0.1', port)) == 0:
                    rpc_ok = True
                    break
            time.sleep(1)
        if rpc_ok:
            print(f"[{COLOR_SUCCESS}  OK  {COLOR_RESET}] (Iniciado)")
        else:
            print(f"[{COLOR_YELLOW} WARN {COLOR_RESET}] (Fallo al iniciar msfrpcd)")

    # Guardar estado actualizado en la config
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4)
        
    print(f" {COLOR_INFO}└────────────────────────────────────────────────────────────────────────────┘{COLOR_RESET}\n")
    print('  [i] "QUE LA FUERZA DEL CONOCIMIENTO TE GUÍE."')
    print(f"  [i] Comandos: 'flow' | 'recon <CIDR>' | 'scan <IP>' | 'exploit <IP>' | 'post <IP>' | 'report <IP>'\n")
    
    # Setup final de base de datos
    db_conn = setup_vector_database(config_data) if "database" in config_data else None

    # --- BUCLE REPL INTERACTIVO ---
    try:
        while True:
            # Forzar saneamiento de la terminal de Linux antes del input
            if os.name == 'posix':
                os.system('stty sane 2>/dev/null')
                
            if 'readline' in sys.modules:
                readline.redisplay()

            comando = input(f"\n{COLOR_NEON_GREEN}ForceVector > {COLOR_RESET}").strip()

            if comando.lower() in ['exit', 'quit', 'salir']:
                print(f"{COLOR_INFO}[*] Desconectando agentes y cerrando...{COLOR_RESET}")
                break
                
            if not comando:
                continue
                
            if comando.lower() == 'status':
                print(f"[*] Estado: Orquestador en línea. Agentes en standby. DB conectada.")
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
            elif comando.lower().startswith('post '):
                target = comando.split(' ', 1)[1].strip()
                execute_post_exploitation_phase(target, config_data)
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
        if os.name == 'posix':
            os.system('stty sane 2>/dev/null')
        if db_conn and not db_conn.closed:
            db_conn.close()
        sys.exit(0)

if __name__ == "__main__":
    main()
