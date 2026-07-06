import subprocess
import re
from typing import List, Dict
from pathlib import Path

def run_recon(target_cidr: str, logs_path: Path) -> List[Dict[str, str]]:
    """
    Fase 1: Descubrimiento de hosts (Ping Sweep).
    Su única función es mapear la red, identificar hosts activos y preparar 
    el entorno de directorios para las evidencias. No busca vulnerabilidades.
    """
    hosts_found = []
    
    # Sanitizar el CIDR para nombres de carpeta (ej. 192.168.1.0/24 -> 192.168.1.0_24)
    safe_target = target_cidr.replace('/', '_')
    network_dir = logs_path / safe_target
    
    try:
        # Crear directorio base de la red
        network_dir.mkdir(parents=True, exist_ok=True)
        
        result = subprocess.run(
            ["nmap", "-sn", target_cidr],
            capture_output=True,
            text=True,
            check=True
        )
        
        output = result.stdout
        current_ip = None
        
        for line in output.split('\n'):
            ip_match = re.search(r'Nmap scan report for (?:\S+ \()?(\d+\.\d+\.\d+\.\d+)\)?', line)
            if ip_match:
                current_ip = ip_match.group(1)
                
            mac_match = re.search(r'MAC Address: ([0-9A-Fa-f:]+)', line)
            if mac_match and current_ip:
                hosts_found.append({
                    "ip": current_ip,
                    "mac": mac_match.group(1),
                    "status": "up"
                })
                # Crear subcarpeta para el host detectado
                host_dir = network_dir / current_ip
                host_dir.mkdir(exist_ok=True)
                current_ip = None 
                
        if current_ip and not any(h["ip"] == current_ip for h in hosts_found):
             hosts_found.append({
                    "ip": current_ip,
                    "mac": "Desconocida (Requiere sudo)",
                    "status": "up"
             })
             # Crear subcarpeta para el host detectado sin MAC
             host_dir = network_dir / current_ip
             host_dir.mkdir(exist_ok=True)

    except subprocess.CalledProcessError as e:
        print(f"[!] Error ejecutando nmap (recon): {e.stderr}")
    except FileNotFoundError:
        print("[!] Error crítico: El binario 'nmap' no está instalado.")

    return hosts_found
