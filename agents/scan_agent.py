import subprocess
import re
import json
from pathlib import Path
from typing import Dict, Any

def run_scan(target_ip: str, host_dir: Path = None) -> Dict[str, Any]:
    """
    Fase 2: Evaluación de Vulnerabilidades y Superficie (Scanning).
    Ejecuta un escaneo profundo en dos rondas:
    1. Escaneo TCP (Versiones y OS).
    2. Escaneo UDP rápido.
    Guarda los resultados en formato JSON en el directorio indicado.
    """
    host_data = {
        "ip": target_ip,
        "os": "Desconocido (Falta flag -O o privilegios root)",
        "ports": []
    }
    
    # -------------------------------------------------------------
    # RONDA 1: Escaneo TCP Profundo (Versiones y OS)
    # -------------------------------------------------------------
    try:
        # -sV: Versiones, -O: Sistema Operativo, -F: Puertos rápidos (top 100)
        result_tcp = subprocess.run(
            ["nmap", "-sV", "-O", "-F", "-T4", target_ip],
            capture_output=True,
            text=True,
            check=True
        )
        _parse_nmap_output(result_tcp.stdout, host_data, is_udp=False)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error ejecutando escaneo TCP en {target_ip}: {e.stderr.strip()}")

    # -------------------------------------------------------------
    # RONDA 2: Escaneo UDP Rápido
    # -------------------------------------------------------------
    try:
        # -sU: Escaneo UDP, -sV: Versiones, -F: Puertos rápidos (top 100)
        # Nota: El escaneo UDP es lento por naturaleza de Nmap, por eso el -F es clave.
        result_udp = subprocess.run(
            ["nmap", "-sU", "-sV", "-F", "-T4", target_ip],
            capture_output=True,
            text=True,
            check=True
        )
        _parse_nmap_output(result_udp.stdout, host_data, is_udp=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error ejecutando escaneo UDP en {target_ip} (Requisito: Sudo): {e.stderr.strip()}")
        
    # Guardar resultados en disco si se provee el directorio
    if host_dir:
        host_dir.mkdir(parents=True, exist_ok=True)
        output_file = host_dir / f"scan_{target_ip.replace('.', '_')}.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(host_data, f, indent=4)
        except IOError as e:
            print(f"[!] Error guardando el JSON de escaneo para {target_ip}: {e}")
            
    return host_data

def _parse_nmap_output(output: str, host_data: dict, is_udp: bool):
    """
    Función interna para parsear la salida de Nmap y unificarla en el diccionario del host.
    """
    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Buscar Sistema Operativo solo en la pasada TCP para evitar sobrescribir con errores de UDP
        if not is_udp:
            os_match = re.search(r'(?:OS details|Running|Aggressive OS guesses):\s+(.+)', line)
            if os_match and "Desconocido" in host_data["os"]:
                host_data["os"] = os_match.group(1).strip()
                continue
        
        # Buscar puertos (ej. 80/tcp open http Apache httpd 2.4.41)
        port_match = re.search(r'^(\d+)/(tcp|udp)\s+(\w+)\s+(\S+)(?:\s+(.*))?$', line)
        if port_match:
            state = port_match.group(3)
            # Para UDP, nmap suele devolver "open|filtered". Lo consideramos como posible vector.
            if state in ['open', 'open|filtered']:
                port_data = {
                    'portid': port_match.group(1),
                    'protocol': port_match.group(2),
                    'state': state,
                    'service': port_match.group(4),
                    'version': port_match.group(5).strip() if port_match.group(5) else "No especificada"
                }
                
                # Evitar duplicar puertos si nmap llega a listarlo dos veces
                if port_data not in host_data["ports"]:
                    host_data["ports"].append(port_data)
