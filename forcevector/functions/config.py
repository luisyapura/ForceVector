import json
import requests
from pathlib import Path
from functions.ui import COLOR_INFO, COLOR_ERROR, COLOR_SUCCESS, COLOR_RESET

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

    print(f"\n{COLOR_INFO}[!] Configuración RPC Metasploit (Para Fase 6 - Pivoting){COLOR_RESET}")
    rpc_host = input("  > Host MSFRPC [127.0.0.1]: ").strip() or "127.0.0.1"
    rpc_port = input("  > Puerto MSFRPC [55552]: ").strip() or 55552
    rpc_pass = input("  > Contraseña MSFRPC [msf]: ").strip() or "msf"

    config_data = {
        "server": {"host": server_host, "port": int(server_port), "keep_alive_seconds": int(keep_alive)},
        "models": {
            "orchestrator": model_orch, 
            "analyzer": model_analy,
            "temperature_orch": 0.1,
            "temperature_exploit": 0.0
        },
        "database": {"host": db_host, "port": int(db_port), "user": db_user, "password": db_pass, "dbname": db_name},
        "msfrpc": {"host": rpc_host, "port": int(rpc_port), "password": rpc_pass, "ssl": False}
    }
    with open(config_path, 'w', encoding='utf-8') as f: 
        json.dump(config_data, f, indent=2)
    print(f"{COLOR_SUCCESS}[+] Configuración guardada en {config_path}{COLOR_RESET}")
    return config_data

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
        with open(config_path, 'w', encoding='utf-8') as f: 
            json.dump(config_data, f, indent=2)
    return config_data
