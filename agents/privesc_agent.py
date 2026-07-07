import json
from .agent_utils import ask_ollama_exploit, interact_hitl

def run(vector: dict, config_data: dict):
    print("\033[96m[*] Delegado a PrivEsc Agent (Post-Explotación y Escalamiento)...\033[0m")
    
    sys_prompt = (
        "Eres un experto en Post-Explotación. Asume que ya tenemos acceso de bajo nivel al sistema "
        "detallado en el JSON. Genera un one-liner en bash para enumeración local (ej. linpeas, "
        "búsqueda de SUIDs, sudo -l). NO markdown. Solo el comando."
    )
    
    prompt = f"Contexto: {json.dumps(vector)}"
    comando = ask_ollama_exploit(prompt, sys_prompt, config_data)
    
    if comando:
        interact_hitl(comando, is_msf_resource=False)
