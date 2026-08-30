import os
import sys
import time
import tempfile
import requests
import subprocess
import re
import json

try:
    import pty
except ImportError:
    pty = None

def ask_ollama_exploit(prompt: str, system_prompt: str, config_data: dict) -> str:
    """Inferencia al LLM orientada estrictamente a la generación de código/comandos."""
    host = config_data["server"]["host"]
    port = config_data["server"]["port"]
    model = config_data["models"].get("orchestrator")
    temp = config_data.get("models", {}).get("temperature_exploit", 0.0)
    
    # --- REFUERZO DE CONTEXTO (GUARDARRAÍL MSF) ---
    if "metasploit" in system_prompt.lower() or ".rc" in system_prompt.lower():
        system_prompt += (
            "\n\nREGLAS ESTRICTAS DE PARÁMETROS METASPLOIT:\n"
            "1. MÓDULOS LOCALES/POST: Si el exploit es 'local' o 'post' (ej. exploits/linux/local/...), "
            "NUNCA configures 'RHOST' o 'RPORT'. DEBES configurar obligatoriamente 'set SESSION 1' (asume ID 1 si no se provee otro).\n"
            "2. MÓDULOS REMOTOS: Usa 'RHOST' ÚNICAMENTE para exploits que atacan a través de la red.\n"
            "3. NO inventes opciones inexistentes. Apégate estrictamente a los requerimientos del módulo.\n"
            "4. Responde siempre en ESPAÑOL NEUTRO.\n"
        )
    
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

def interact_hitl(command_text: str, is_msf_resource: bool = False, config_data: dict = None):
    """
    Implementa el Human-in-the-Loop (HITL) para validación de comandos.
    Las ejecuciones [E] y [R] aprovisionan entornos Sandbox para aislamiento.
    """
    print(f"\n\033[38;5;220m[*] Código / Comando Propuesto por IA:\033[0m\n{command_text}\n")
    
    prompt_msg = "\033[96mAcción -> [E] Ejecutar Local | [M] Modificar (nano) "
    has_rpc = False
    
    if is_msf_resource and config_data and "msfrpc" in config_data:
        has_rpc = True
        prompt_msg += "| \033[93m[R] Ejecutar vía MSF RPC (Background)\033[96m "
        
    prompt_msg += "| [A] Abortar: \033[0m"

    opcion = input(prompt_msg).strip().upper()
    
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
        
    if opcion == 'R' and has_rpc:
        # FIX DE PERSISTENCIA: Forzar ejecución sin interacción (-z). RETIRAMOS '-j'.
        if is_msf_resource:
            final_content = re.sub(r'(?im)^(exploit|run).*$', r'\1 -z', final_content)

        try:
            rpc_conf = config_data.get("msfrpc", {})
            pwd = rpc_conf.get("password", "msf")
            port = rpc_conf.get("port", 55552)
            ssl_val = rpc_conf.get("ssl", False)
            
            # Serialización para el entorno aislado
            config_json_str = json.dumps(config_data)
            forcevector_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            if os.environ.get("DISPLAY"):
                print("\033[92m[*] Aprovisionando entorno Sandbox interactivo para MSF RPC (Nueva ventana)...\033[0m")
                
                # Generar script de Python temporal como Wrapper con REPL integrado
                # AÑADIDO: Bloque Try/Except global para evitar que la ventana crashee silenciosamente
                rpc_script_code = f"""import time
import os
import sys
import json
import traceback

try:
    # Asegurar resolución de módulos ForceVector
    sys.path.insert(0, {repr(forcevector_dir)})

    from pymetasploit3.msfrpc import MsfRpcClient
    # FIX RUTA: Importamos desde la nueva estructura modular
    from agents.post_exploitation.agent import run_post_exploitation

    config_data = json.loads({repr(config_json_str)})

    print("\\033[92m[*] Conectando al demonio MSF RPC local...\\033[0m")
    try:
        client = MsfRpcClient('{pwd}', port={port}, ssl={ssl_val})
        console = client.consoles.console()
        
        print("\\033[96m[*] Consola RPC creada. Inyectando script de explotación en BACKGROUND (-z)...\\033[0m\\n")
        console.write({repr(final_content)} + '\\n')
        
        print("\\033[93m[*] Monitoreando progreso de I/O efímero (timeout 30s)...\\033[0m\\n")
        for _ in range(60):
            data = console.read()
            if data and data.get('data'):
                print(data['data'], end='')
            time.sleep(0.5)
            
        print("\\n\\033[92m[*] Ejecución inicial completada. Destruyendo consola efímera. Sesiones globales retenidas en daemon.\\033[0m")
        console.destroy()
    except Exception as e:
        print(f"\\n\\033[91m[!] Error en cliente RPC o Timeout: {{e}}\\033[0m")

    print("\\n\\033[93m[i] Fase 5 de Orquestador pausada. Sandbox Interactivo Activo.\\033[0m")
    print("\\033[93m[i] TIP: Escribe 'post <IP>' aquí para ejecutar la Fase 6 sobre tu sesión activa.\\033[0m")

    # Mini-REPL para operar sin abandonar el Sandbox
    while True:
        try:
            cmd = input("\\n\\033[96mForceVector (Sandbox RPC) > \\033[0m").strip()
            if cmd.lower() in ['exit', 'quit']:
                print("\\033[92m[*] Cerrando Sandbox y retornando control al Orquestador...\\033[0m")
                break
            elif cmd.lower().startswith('post '):
                target = cmd.split(' ', 1)[1].strip()
                run_post_exploitation(target, config_data)
            elif cmd:
                os.system(cmd)
        except KeyboardInterrupt:
            print("\\n\\033[92m[*] Cerrando Sandbox...\\033[0m")
            break
        except Exception as e:
            print(f"\\033[91m[!] Error: {{e}}\\033[0m")
except Exception as fatal_e:
    print("\\n\\033[91m[!] ERROR FATAL CRÍTICO EN EL SANDBOX:\\033[0m")
    traceback.print_exc()
    input("\\n[!] Presiona ENTER para cerrar esta ventana y revisar el código...")
"""
                with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w') as tf:
                    tf.write(rpc_script_code)
                    rpc_script_path = tf.name
                
                subprocess.Popen(["x-terminal-emulator", "-e", f"python3 {rpc_script_path}"])
                input("\033[93m[i] Sandbox Interactivo abierto en ventana externa. \n[!] Presione ENTER aquí ÚNICAMENTE cuando haya finalizado su operatoria y cerrado el Sandbox para continuar...\033[0m")
                
                try:
                    os.remove(rpc_script_path)
                except OSError:
                    pass
            else:
                # Fallback a monitoreo inline
                from pymetasploit3.msfrpc import MsfRpcClient
                client = MsfRpcClient(pwd, port=port, ssl=ssl_val)
                print("\033[92m[*] Conectado a MSF RPC. Creando consola de control temporal...\033[0m")
                console = client.consoles.console()
                
                console.write(final_content + '\n')
                
                print("\033[93m[*] Monitoreando salida del demonio MSFRPC (15 segundos)...\033[0m")
                for _ in range(30):
                    data = console.read()
                    if data and data.get('data'):
                        print(data['data'], end='')
                    time.sleep(0.5)
                        
                print("\n\033[96m[*] Tarea delegada exitosamente al Demonio. La sesión sigue viva en background.\033[0m")
                console.destroy()
                
        except ImportError:
            print("\033[91m[!] pymetasploit3 no está instalado. Fallback a ejecución local [E].\033[0m")
            opcion = 'E'
        except Exception as e:
            print(f"\033[91m[!] Error delegando a MSF RPC: {e}. Fallback a ejecución local [E].\033[0m")
            opcion = 'E'

    if opcion == 'E':
        if is_msf_resource:
            final_content = re.sub(r'(?im)^.*AutoRunScript.*$\n?', '', final_content)
            tty_fixes = "setg CommandShellPty true\n"
            final_content = tty_fixes + final_content
            
            with tempfile.NamedTemporaryFile(suffix=".rc", delete=False, mode='w') as tf:
                tf.write(final_content)
                rc_path = tf.name
                
            print("\033[92m[*] Ejecutando Metasploit Framework localmente...\033[0m")
            try:
                if os.environ.get("DISPLAY"):
                    print("\033[92m[*] Aprovisionando entorno Sandbox (Aislamiento de TTY en nueva ventana)...\033[0m")
                    subprocess.Popen(["x-terminal-emulator", "-e", f"msfconsole -q -r {rc_path}"])
                    input("\033[93m[i] Ejecución en ventana externa. \n[!] Presione ENTER aquí ÚNICAMENTE cuando haya cerrado Metasploit para continuar...\033[0m")
                else:
                    print("\033[93m[-] Entorno gráfico no detectado. Fallback a ejecución inline con PTY...\033[0m")
                    if pty and os.name == 'posix':
                        pty.spawn(["msfconsole", "-q", "-r", rc_path])
                    else:
                        subprocess.run(["msfconsole", "-q", "-r", rc_path], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
            except KeyboardInterrupt:
                pass 
            except Exception as e:
                print(f"\033[91m[-] Error lanzando entorno local: {e}\033[0m")
            finally:
                try:
                    os.remove(rc_path)
                except OSError:
                    pass
                if os.name == 'posix':
                    os.system("stty sane 2>/dev/null")
        else:
            with tempfile.NamedTemporaryFile(suffix=".sh", delete=False, mode='w') as tf:
                tf.write(final_content)
                sh_path = tf.name
            os.chmod(sh_path, 0o755)
            
            print("\033[92m[*] Ejecutando comando Bash localmente...\033[0m")
            try:
                if os.environ.get("DISPLAY"):
                    print("\033[92m[*] Aprovisionando entorno Sandbox (Nueva ventana)...\033[0m")
                    subprocess.Popen(["x-terminal-emulator", "-e", sh_path])
                    input("\033[93m[i] Ejecución en ventana externa. \n[!] Presione ENTER aquí al finalizar para continuar...\033[0m")
                else:
                    print("\033[93m[-] Entorno gráfico no detectado. Fallback a ejecución inline...\033[0m")
                    if pty and os.name == 'posix':
                        pty.spawn(["/bin/bash", "-c", final_content])
                    else:
                        subprocess.run(final_content, shell=True, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
            except KeyboardInterrupt:
                pass
            except Exception as e:
                print(f"\033[91m[-] Error lanzando entorno local: {e}\033[0m")
            finally:
                try:
                    os.remove(sh_path)
                except OSError:
                    pass
                if os.name == 'posix':
                    os.system("stty sane 2>/dev/null")
                    
    elif opcion not in ['E', 'R']:
        print("\033[91m[-] Ejecución abortada por el operador.\033[0m")

    return opcion
