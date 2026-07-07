import json
from .agent_utils import ask_ollama_exploit, interact_hitl

def run(vector: dict, config_data: dict):
    print("\033[96m[*] Delegado a Web Agent (Enfocado en HTTP/HTTPS)...\033[0m")
    
    sys_prompt = (
        "Eres un especialista en auditoría web en Kali Linux. Basado en el JSON proporcionado, "
        "genera UN ÚNICO comando Bash de terminal (usando sqlmap, nikto, dirb, o curl) "
        "para explotar o enumerar la vulnerabilidad sugerida. "
        "NO uses formato markdown. CERO explicaciones. Devuelve solo el comando listo para ejecutar."
    )
    
    prompt = f"Vector: {json.dumps(vector)}"
    comando = ask_ollama_exploit(prompt, sys_prompt, config_data)
    
    if comando:
        interact_hitl(comando, is_msf_resource=False)
