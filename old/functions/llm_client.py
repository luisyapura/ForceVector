import json
import requests
import re
from functions.ui import COLOR_INFO, COLOR_ERROR, COLOR_SUCCESS, COLOR_RESET

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
        "REGLA CRÍTICA 1 (IDIOMA): TU ÚNICO IDIOMA ES EL ESPAÑOL NEUTRO.\n"
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
                    import psycopg2
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
                "No uses modismos. Limítate a interpretar los datos empíricos. No asumas datos fuera de los presentados."
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
