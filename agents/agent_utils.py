import os
import tempfile
import requests
import subprocess

def ask_ollama_exploit(prompt: str, system_prompt: str, config_data: dict) -> str:
    """Inferencia al LLM orientada estrictamente a la generación de código/comandos."""
    host = config_data["server"]["host"]
    port = config_data["server"]["port"]
    model = config_data["models"].get("orchestrator")
    temp = config_data.get("models", {}).get("temperature_exploit", 0.0)
    
    url = f"http://{host}:{port}/api/generate"
    payload = {
        "model": model, 
        "prompt": prompt, 
        "system": system_prompt, 
        "stream": False,
        "options": {"num_ctx": 4096, "num_predict": 1024, "temperature": temp}
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 200:
            text = response.json().get("response", "").strip()
            if text.startswith("```"):
                lines = text.split("\n")
                if len(lines) >= 2:
                    text = "\n".join(lines[1:-1]).strip()
            return text
        return ""
    except requests.exceptions.RequestException as e:
        print(f"\033[91m[!] Error de conexión con el LLM: {e}\033[0m")
        return ""

def interact_hitl(command_text: str, is_msf_resource: bool = False):
    """Implementa el Human-in-the-Loop (HITL) para validación de comandos."""
    print(f"\n\033[38;5;220m[*] Código / Comando Propuesto por IA:\033[0m\n{command_text}\n")
    opcion = input("\033[96mAcción -> [E] Ejecutar | [M] Modificar (nano) | [A] Abortar: \033[0m").strip().upper()
    
    final_content = command_text
    
    if opcion == 'M':
        ext = ".rc" if is_msf_resource else ".sh"
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False, mode='w') as tf:
            tf.write(final_content)
            temp_path = tf.name
            
        editor = os.environ.get('EDITOR', 'nano')
        os.system(f"{editor} {temp_path}")
        
        with open(temp_path, 'r') as tf:
            final_content = tf.read().strip()
        os.remove(temp_path)
        opcion = 'E'
        
    if opcion == 'E':
        if is_msf_resource:
            with tempfile.NamedTemporaryFile(suffix=".rc", delete=False, mode='w') as tf:
                tf.write(final_content)
                rc_path = tf.name
            print("\033[92m[*] Lanzando Metasploit Framework con archivo de recursos...\033[0m")
            subprocess.run(["msfconsole", "-q", "-r", rc_path])
            os.remove(rc_path)
        else:
            print("\033[92m[*] Ejecutando comando Bash...\033[0m")
            subprocess.run(final_content, shell=True)
    else:
        print("\033[91m[-] Ejecución abortada por el operador.\033[0m")
