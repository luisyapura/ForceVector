import json
from .agent_utils import ask_ollama_exploit, interact_hitl

def run(vector: dict, config_data: dict):
    print("\033[96m[*] Delegado a Auth Agent (Fuerza Bruta / Credentials)...\033[0m")
    
    sys_prompt = (
        "Eres un experto en cracking de credenciales. Recibes datos de un servicio (SSH, FTP, etc). "
        "Genera un comando de 'hydra', 'medusa' o 'ncrack' para realizar fuerza bruta."
        "Utiliza listas de Kali Linux como /usr/share/wordlists/rockyou.txt o seclists. "
        "NO uses markdown. Solo devuelve el comando."
    )
    
    prompt = f"Vector: {json.dumps(vector)}"
    comando = ask_ollama_exploit(prompt, sys_prompt, config_data)
    
    if comando:
        interact_hitl(comando, is_msf_resource=False)
