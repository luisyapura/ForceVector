import json
import re
import traceback
from pathlib import Path

from functions.ui import COLOR_INFO, COLOR_ERROR, COLOR_SUCCESS, COLOR_YELLOW, COLOR_RESET
from functions.llm_client import direct_ollama_query

# Carga segura de módulos de los agentes
try:
    from agents import recon_agent
    from agents import scan_agent
except Exception as e:
    recon_agent = None
    scan_agent = None


def execute_autonomous_flow(target: str, config_data: dict, db_conn, logs_path: Path, skip_recon: bool = False):
    """Controlador del Flujo Operativo Autónomo Fases 1 a 3."""
    if not recon_agent or not scan_agent:
        print(f"{COLOR_ERROR}[!] Módulos de Fases 1/2 no cargados.{COLOR_RESET}")
        return

    hosts_activos = []
        
    if not skip_recon:
        print(f"\n{COLOR_INFO}=== INICIANDO FASE 1: RECONOCIMIENTO (Descubrimiento) ==={COLOR_RESET}")
        print(f"{COLOR_INFO}[*] Mapeando red con Ping Sweep: {target}...{COLOR_RESET}")
        
        try:
            hosts_activos = recon_agent.run_recon(target, logs_path)
        except Exception as e:
            print(f"{COLOR_ERROR}[!] Error en agente de reconocimiento: {e}{COLOR_RESET}")
            return
        
        if not hosts_activos:
            print(f"{COLOR_ERROR}[-] No se detectaron hosts activos. Abortando flujo.{COLOR_RESET}")
            return
            
        print(f"{COLOR_SUCCESS}[+] Fase 1 completada. {len(hosts_activos)} hosts activos detectados.{COLOR_RESET}")
    else:
        print(f"\n{COLOR_INFO}[*] Omitiendo Fase 1 (Reconocimiento). Apuntando directamente al host: {target}{COLOR_RESET}")
        hosts_activos = [{"ip": target, "mac": "Desconocida (Escaneo Directo)"}]
    
    print(f"\n{COLOR_INFO}=== INICIANDO FASE 2: ESCANEO (Vulnerability Assessment) ==={COLOR_RESET}")
    
    vectores_guardados = 0
    if db_conn:
        try:
            import psycopg2
            with db_conn.cursor() as cur:
                cur.execute("DELETE FROM agent_memory WHERE task_id = 'recon_port_vector'")
                
                for idx, host in enumerate(hosts_activos, 1):
                    ip = host.get("ip")
                    mac = host.get("mac")
                    
                    if skip_recon:
                        host_dir = logs_path / "scans_directos" / target.replace('/', '_')
                    else:
                        host_dir = logs_path / target.replace('/', '_') / ip
                        
                    print(f"\n{COLOR_INFO}[*] Lanzando escaneo profundo en objetivo [{idx}/{len(hosts_activos)}]: {ip}{COLOR_RESET}")
                    
                    scan_data = scan_agent.run_scan(ip, host_dir)
                    os_info = scan_data.get("os", "Desconocido")
                    ports = scan_data.get("ports", [])
                    
                    print(f"    └─ MAC: {mac:<17} | OS: {os_info}")
                    
                    if ports:
                        print(f"    └─ Puertos/Servicios detectados:")
                        for p in ports:
                            color_proto = COLOR_YELLOW if p.get('protocol') == 'udp' else COLOR_RESET
                            print(f"       - {p.get('portid'):>5}/{p.get('protocol'):<4} : {color_proto}{p.get('service'):<12}{COLOR_RESET} ({p.get('version')})")
                            
                            content_vector = json.dumps({
                                "ip": ip, "os": os_info,
                                "puerto": p.get('portid'), "protocolo": p.get('protocol'),
                                "servicio": p.get('service'), "version": p.get('version')
                            })
                            cur.execute("INSERT INTO agent_memory (task_id, content) VALUES (%s, %s)", ("recon_port_vector", content_vector))
                            vectores_guardados += 1
                    else:
                        print(f"    └─ No se detectaron puertos abiertos filtrables.")
                        
            print(f"\n{COLOR_SUCCESS}[+] Fase 2 completada. Se han almacenado {vectores_guardados} vectores individuales en PostgreSQL.{COLOR_RESET}")
        except Exception as e:
            print(f"{COLOR_ERROR}[!] Error en BD durante escaneo: {e}{COLOR_RESET}")
            return

    print(f"\n{COLOR_INFO}=== INICIANDO FASE 3: MODELADO DE AMENAZAS (LLM Iterativo) ==={COLOR_RESET}")
    
    objetivos_analizados = []
    
    if db_conn:
        try:
            with db_conn.cursor() as cur:
                cur.execute("SELECT content FROM agent_memory WHERE task_id = 'recon_port_vector';")
                vectores_crudos = cur.fetchall()
                
            if not vectores_crudos:
                print(f"{COLOR_YELLOW}[*] No existen vectores de puertos válidos para analizar en Fase 3.{COLOR_RESET}")
                return
                
            for idx, vec in enumerate(vectores_crudos, 1):
                vec_data = json.loads(vec[0])
                ip, port, proto = vec_data['ip'], vec_data['puerto'], vec_data['protocolo']
                srv, ver = vec_data['servicio'], vec_data['version']
                
                print(f"\n{COLOR_INFO}[*] Analizando Vector [{idx}/{len(vectores_crudos)}]: {ip} -> {port}/{proto} ({srv} - {ver}){COLOR_RESET}")
                
                prompt_iterativo = (
                    "Analiza el siguiente vector de ataque.\n"
                    "REGLAS CRÍTICAS: Devuelve ÚNICA Y EXCLUSIVAMENTE formato JSON. "
                    "Correlaciona la versión con identificadores CVE reales.\n"
                    f"DATOS: {json.dumps(vec_data)}\n\n"
                    "FORMATO JSON: {\"cve_identificados\": [\"CVE-XXXX\"], \"vectores_ataque\": \"Descripción...\", \"herramienta_sugerida\": \"comando\", \"categoria_vector\": \"rce\"}"
                )
                
                resultado_llm = direct_ollama_query(prompt_iterativo, config_data)
                
                try:
                    json_match = re.search(r'\{.*\}', resultado_llm, re.DOTALL)
                    clean_json = json_match.group(0) if json_match else "{}"
                    analisis_vector = json.loads(clean_json)
                    vector_completo = {**vec_data, **analisis_vector}
                    objetivos_analizados.append(vector_completo)
                except json.JSONDecodeError:
                    pass
            
            with db_conn.cursor() as cur:
                cur.execute("DELETE FROM agent_memory WHERE task_id = 'threat_model_results'")
                cur.execute("INSERT INTO agent_memory (task_id, content) VALUES (%s, %s)", 
                            ("threat_model_results", json.dumps(objetivos_analizados)))
            
            print(f"\n{COLOR_SUCCESS}[+] Fase 3: Análisis finalizado y persistido en la Base de Datos.{COLOR_RESET}")

            modelos_por_ip = {}
            for obj in objetivos_analizados:
                ip = obj['ip']
                if ip not in modelos_por_ip:
                    modelos_por_ip[ip] = []
                modelos_por_ip[ip].append(obj)

            print(f"{COLOR_INFO}[*] Generando archivos de contexto para la Fase 4 (Enumeración)...{COLOR_RESET}")
            for ip, modelos in modelos_por_ip.items():
                if skip_recon:
                    host_dir = logs_path / "scans_directos" / target.replace('/', '_')
                else:
                    host_dir = logs_path / target.replace('/', '_') / ip
                
                host_dir.mkdir(parents=True, exist_ok=True)
                output_file = host_dir / f"threat_model_{ip.replace('.', '_')}.json"
                
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(modelos, f, indent=4)
                    print(f"{COLOR_SUCCESS}    └─ Reporte de amenazas guardado: {output_file}{COLOR_RESET}")
                except IOError as e:
                    print(f"{COLOR_ERROR}    └─ [!] Error guardando contexto para {ip}: {e}{COLOR_RESET}")

            print(f"\n{COLOR_YELLOW}[*] Fases completadas. Ejecuta 'exploit <IP>' para iniciar la Fase 4 y 5.{COLOR_RESET}")
            
        except Exception as e:
            print(f"{COLOR_ERROR}[!] Error en operaciones PostgreSQL Fase 3: {e}{COLOR_RESET}")

def execute_exploitation_phase(target_ip: str, config_data: dict, logs_path: Path):
    print(f"\n{COLOR_INFO}=== INICIANDO FASES 4 Y 5: EXPLOTACIÓN SUPERVISADA (HITL) ==={COLOR_RESET}")
    print(f"{COLOR_INFO}[*] Recuperando contexto persistente para {target_ip}...{COLOR_RESET}")
    
    target_filename = f"threat_model_{target_ip.replace('.', '_')}.json"
    encontrados = list(logs_path.rglob(target_filename))
    
    if not encontrados:
        print(f"{COLOR_ERROR}[-] Contexto no encontrado para {target_ip}. Debes ejecutar 'recon' o 'scan' primero.{COLOR_RESET}")
        return
        
    threat_model_path = encontrados[0]
    print(f"{COLOR_SUCCESS}[+] Contexto cargado exitosamente desde: {threat_model_path}{COLOR_RESET}")
    
    try:
        from agents import exploit_agent
        
        print(f"{COLOR_INFO}[*] Ejecutando plan de explotación (Delegado a MSFRPC / Jobs)...{COLOR_RESET}")
        exploit_agent.run_exploitation_plan(str(threat_model_path), config_data)
        
        # Transición automática: El agente de post-explotación buscará sesiones activas en MSFRPC
        print(f"\n{COLOR_SUCCESS}[+] Explotación delegada. Iniciando Post-Explotación automáticamente...{COLOR_RESET}")
        execute_post_exploitation_phase(target_ip, config_data)
            
    except Exception as e:
        print(f"\n{COLOR_ERROR}[!] Error crítico al cargar o ejecutar el Agente de Explotación.{COLOR_RESET}")
        print(f"{COLOR_YELLOW}[DEBUG] Traza del error:\n{traceback.format_exc()}{COLOR_RESET}")

def execute_post_exploitation_phase(target_ip: str, config_data: dict):
    """Fase 6: Delegación hacia el Agente Post-Explotación para Situational Awareness"""
    try:
        from agents import post_exploit_agent
        post_exploit_agent.run_post_exploitation(target_ip, config_data)
    except Exception as e:
        print(f"\n{COLOR_ERROR}[!] Error al cargar el Agente de Post-Explotación: {e}{COLOR_RESET}")
        print(f"{COLOR_YELLOW}[DEBUG] Traza:\n{traceback.format_exc()}{COLOR_RESET}")

def execute_report_phase(target_ip: str, base_dir: Path, logs_path: Path):
    print(f"\n{COLOR_INFO}=== INICIANDO FASE 7: GENERACIÓN DE REPORTE ({target_ip}) ==={COLOR_RESET}")
    print(f"{COLOR_INFO}[*] Recuperando contexto persistente y evidencias...{COLOR_RESET}")
    
    target_filename = f"threat_model_{target_ip.replace('.', '_')}.json"
    encontrados = list(logs_path.rglob(target_filename))
    
    if not encontrados:
        print(f"{COLOR_ERROR}[-] Contexto no encontrado para {target_ip}. No hay datos auditados para documentar.{COLOR_RESET}")
        return
        
    threat_model_path = encontrados[0]
    
    try:
        from agents import report_agent
        report_agent.generate_pdf_report(str(base_dir), str(threat_model_path))
    except ImportError as e:
        print(f"{COLOR_ERROR}[!] Error: Módulo report_agent o dependencias (Jinja2/WeasyPrint) no encontradas.\nDetalle: {e}{COLOR_RESET}")
    except Exception as e:
        print(f"\n{COLOR_ERROR}[!] Error crítico al generar el reporte: {e}{COLOR_RESET}")
        print(f"{COLOR_YELLOW}[DEBUG] Traza:\n{traceback.format_exc()}{COLOR_RESET}")
