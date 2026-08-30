import json
from .agent_utils import ask_ollama_exploit, interact_hitl

def run(vector: dict, config_data: dict):
    print("\033[96m[*] Delegado a AD Agent (Active Directory & SMB)...\033[0m")
    
    sys_prompt = (
        "Eres experto en Active Directory y redes Windows. "
        "Genera comandos de la suite Impacket o NetExec (nxc) "
        "para enumerar o explotar SMB/LDAP/Kerberos basados en los datos del JSON. "
        "NO markdown. Solo devuelve el comando bash."
    )
    
    prompt = f"Vector: {json.dumps(vector)}"
    comando = ask_ollama_exploit(prompt, sys_prompt, config_data)
    
    if comando:
        interact_hitl(comando, is_msf_resource=False)
