"""
AIPentest-MitL - Agente de Escaneo (ScanAgent)
Plano de Ejecución Táctica: enumeración detallada de puertos, servicios y vulnerabilidades.
"""
import asyncio
import os
import tempfile
import re
from typing import List, Optional, Dict
import logging

from core.config import settings
from core.websocket_manager import ws_manager
from parsers.nmap_parser import NmapParser, ParsedHost

logger = logging.getLogger(__name__)


class ScanAgent:
    """
    Agente de Escaneo Profundo.
    Responsable de la enumeración detallada de servicios y detección de vulnerabilidades
    mediante scripts NSE de Nmap.
    Opera en el Plano de Ejecución Táctica.
    """

    AGENT_NAME = "ScanAgent"

    # Perfiles de escaneo predefinidos
    SCAN_PROFILES = {
        "light": {
            "description": "Escaneo ligero: top 100 puertos, sin scripts vuln",
            "args": ["-sS", "-sV", "--top-ports", "100", "-T3", "--open"]
        },
        "standard": {
            "description": "Escaneo estándar: top 1000 puertos + scripts básicos",
            "args": ["-sS", "-sV", "-sC", "-O", "-T4", "--open"]
        },
        "full": {
            "description": "Escaneo completo: todos los puertos + scripts de vulnerabilidades",
            "args": ["-sS", "-sV", "-sC", "-O", "-p-", "-T4", "--open", "--script=vuln,exploit,auth"]
        },
        "smb": {
            "description": "Escaneo específico SMB/Windows",
            "args": ["-sS", "-sV", "-p", "135,139,445,3389,5985,5986",
                     "--script=smb-vuln*,smb-security-mode,smb2-security-mode,msrpc-enum", "-T4"]
        },
        "web": {
            "description": "Escaneo de servicios web",
            "args": ["-sS", "-sV", "-p", "80,443,8080,8443,8888,3000,8000,8008",
                     "--script=http-title,http-headers,http-methods,http-auth-finder", "-T4"]
        },
        "ftp_ssh": {
            "description": "Escaneo FTP y SSH",
            "args": ["-sS", "-sV", "-p", "21,22,23",
                     "--script=ftp-anon,ftp-syst,ftp-vsftpd-backdoor,ssh-auth-methods,ssh-brute", "-T4"]
        }
    }

    def __init__(self, session_id: str, db_session=None):
        self.session_id = session_id
        self.db = db_session
        self.nmap_path = settings.nmap_path

    async def _log(self, level: str, message: str, extra: dict = None):
        logger.info(f"[{self.AGENT_NAME}] {message}")
        await ws_manager.send_agent_log(
            session_id=self.session_id,
            agent=self.AGENT_NAME,
            level=level,
            message=message,
            extra=extra or {}
        )

    async def _run_nmap(self, args: List[str], target: str) -> Optional[str]:
        """Ejecuta Nmap y retorna el XML."""
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False, mode="w") as tmp:
            xml_output_path = tmp.name

        cmd = [self.nmap_path] + args + ["-oX", xml_output_path, target]
        cmd_str = " ".join(cmd)
        await self._log("info", f"Ejecutando: {cmd_str}")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                await self._log("warning", f"Nmap terminó con código {proc.returncode}")

            if os.path.exists(xml_output_path):
                with open(xml_output_path, "r", encoding="utf-8", errors="ignore") as f:
                    xml_content = f.read()
                os.unlink(xml_output_path)
                return xml_content
            return None

        except FileNotFoundError:
            await self._log("error", f"Nmap no encontrado en: {self.nmap_path}")
            return None
        except Exception as e:
            await self._log("error", f"Error ejecutando Nmap: {e}")
            return None

    async def deep_scan(self, target_ip: str, profile: str = "standard") -> Optional[ParsedHost]:
        """
        Escaneo profundo de un host individual.
        
        Args:
            target_ip: IP del host a escanear.
            profile: Perfil de escaneo a usar (ver SCAN_PROFILES).
        
        Returns:
            ParsedHost con información detallada del host.
        """
        if profile not in self.SCAN_PROFILES:
            profile = "standard"

        scan_config = self.SCAN_PROFILES[profile]
        await self._log("info", f"Iniciando escaneo '{profile}' en {target_ip}: {scan_config['description']}", {
            "target": target_ip,
            "profile": profile
        })

        xml_content = await self._run_nmap(scan_config["args"], target_ip)
        if not xml_content:
            return None

        hosts = NmapParser.parse_xml(xml_content)
        if not hosts:
            await self._log("warning", f"Sin resultados para {target_ip}")
            return None

        host = hosts[0]
        open_ports = [s for s in host.services if s.state == "open"]

        # Detectar vulnerabilidades en scripts NSE
        vulnerabilities = NmapParser.extract_vulnerabilities_from_scripts(host)

        await self._log("success", f"Escaneo completado: {target_ip} - {len(open_ports)} puertos abiertos, {len(vulnerabilities)} vulns detectadas", {
            "ip": target_ip,
            "open_ports": len(open_ports),
            "vulnerabilities": len(vulnerabilities),
            "os": host.os_name
        })

        # Notificar actualización de topología
        await ws_manager.send_topology_update(self.session_id, {
            "action": "host_scanned",
            "host": {
                "ip": host.ip_address,
                "os": host.os_name,
                "services": [
                    {"port": s.port, "name": s.service_name, "version": s.version}
                    for s in open_ports
                ],
                "vulnerabilities": vulnerabilities
            }
        })

        return host

    async def identify_attack_vectors(self, hosts: List[ParsedHost]) -> List[Dict]:
        """
        Analiza los servicios detectados e identifica posibles vectores de ataque.
        No ejecuta exploits, solo identifica oportunidades.
        
        Returns:
            Lista de vectores de ataque potenciales con sugerencias de módulos.
        """
        attack_vectors = []

        # Mapeo de servicios/versiones conocidas a vectores de ataque
        KNOWN_VECTORS = {
            ("vsftpd", "2.3.4"): {
                "module": "exploit/unix/ftp/vsftpd_234_backdoor",
                "description": "vsftpd 2.3.4 Backdoor",
                "mitre": "T1190",
                "risk": "critical"
            },
            ("ms-wbt-server", ""): {
                "module": "auxiliary/scanner/rdp/rdp_scanner",
                "description": "RDP expuesto - posible BlueKeep/DejaBlue",
                "mitre": "T1021.001",
                "risk": "high"
            },
            ("smb", ""): {
                "module": "exploit/windows/smb/ms17_010_eternalblue",
                "description": "SMB expuesto - verificar EternalBlue",
                "mitre": "T1210",
                "risk": "critical"
            },
            ("http", ""): {
                "module": "auxiliary/scanner/http/http_version",
                "description": "Servicio HTTP - enumerar directorios y tecnologías",
                "mitre": "T1595",
                "risk": "medium"
            },
            ("ftp", ""): {
                "module": "auxiliary/scanner/ftp/anonymous",
                "description": "FTP expuesto - verificar acceso anónimo",
                "mitre": "T1078",
                "risk": "medium"
            },
            ("ssh", ""): {
                "module": "auxiliary/scanner/ssh/ssh_version",
                "description": "SSH expuesto - verificar versión y credenciales débiles",
                "mitre": "T1078.004",
                "risk": "low"
            }
        }

        for host in hosts:
            for service in host.services:
                if service.state != "open":
                    continue

                svc_lower = service.service_name.lower()
                ver_lower = service.version.lower() if service.version else ""

                # Búsqueda exacta primero, luego parcial
                vector = None
                for (svc_key, ver_key), vec_data in KNOWN_VECTORS.items():
                    if svc_key in svc_lower:
                        if ver_key == "" or ver_key in ver_lower:
                            vector = {
                                **vec_data,
                                "target_ip": host.ip_address,
                                "target_port": service.port,
                                "service": service.service_name,
                                "version": service.version
                            }
                            break

                if vector:
                    attack_vectors.append(vector)

        await self._log("info", f"Identificados {len(attack_vectors)} vectores de ataque potenciales", {
            "vectors": [{"target": v["target_ip"], "module": v["module"], "risk": v["risk"]}
                       for v in attack_vectors]
        })

        return attack_vectors

    async def run(self, targets: List[str], profile: str = "standard") -> dict:
        """
        Punto de entrada principal del agente.
        
        Args:
            targets: Lista de IPs a escanear.
            profile: Perfil de escaneo (light, standard, full, smb, web, ftp_ssh).
        
        Returns:
            Diccionario con hosts escaneados, vectores de ataque y contexto para el LLM.
        """
        await self._log("info", f"=== ScanAgent iniciado: {len(targets)} objetivos, perfil '{profile}' ===")

        scanned_hosts = []
        for i, target_ip in enumerate(targets):
            await ws_manager.send_task_status(
                self.session_id, 0, "running",
                progress=int((i / len(targets)) * 100)
            )
            host = await self.deep_scan(target_ip, profile)
            if host:
                scanned_hosts.append(host)
            await asyncio.sleep(0.3)

        # Identificar vectores de ataque
        attack_vectors = await self.identify_attack_vectors(scanned_hosts)

        # Generar contexto resumido para el LLM
        llm_context = NmapParser.generate_llm_context(scanned_hosts)
        if attack_vectors:
            llm_context += f"\n\n=== Vectores de Ataque Identificados ({len(attack_vectors)}) ===\n"
            for v in attack_vectors:
                llm_context += f"- [{v['risk'].upper()}] {v['target_ip']}:{v['target_port']} {v['description']} | Módulo: {v['module']} | MITRE: {v['mitre']}\n"

        await self._log("success", f"=== ScanAgent completado: {len(scanned_hosts)} hosts, {len(attack_vectors)} vectores ===")

        return {
            "status": "completed",
            "hosts": scanned_hosts,
            "attack_vectors": attack_vectors,
            "llm_context": llm_context,
            "summary": {
                "hosts_scanned": len(scanned_hosts),
                "attack_vectors": len(attack_vectors)
            }
        }
