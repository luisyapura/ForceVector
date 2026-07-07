import json
from .agent_utils import ask_ollama_exploit, interact_hitl

def run(vector: dict, config_data: dict):
    print("\033[96m[*] Delegado a DB Agent (MySQL, Postgres, MSSQL, Oracle)...\033[0m")
    
    sys_prompt = (
        "Eres especialista en Bases de Datos. Recibes un JSON con un puerto de base de datos objetivo. "
        "Genera comandos bash usando clientes nativos (ej. psql, mysql) o scripts de Nmap (--script) "
        "para enumerar el servicio. "
        "NO markdown. CERO explicaciones."
    )
    
    prompt = f"Vector: {json.dumps(vector)}"
    comando = ask_ollama_exploit(prompt, sys_prompt, config_data)
    
    if comando:
        interact_hitl(comando, is_msf_resource=False)
