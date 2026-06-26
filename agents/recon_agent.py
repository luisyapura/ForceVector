"""
AIPentest-MitL - Agente de Reconocimiento (ReconAgent)
Plano de Ejecución Táctica: ejecuta Nmap para descubrir hosts activos.
"""
import asyncio
import subprocess
import os
import tempfile
from datetime import datetime
from typing import List, Optional
import logging

from core.config import settings
from core.websocket_manager import ws_manager
from parsers.nmap_parser import NmapParser, ParsedHost

logger = logging.getLogger(__name__)


class ReconAgent:
    """
    Agente de Reconocimiento de Red.
    Responsable del descubrimiento inicial de hosts en el segmento objetivo.
    Opera en el Plano de Ejecución Táctica.
    """

    AGENT_NAME = "ReconAgent"

    def __init__(self, session_id: str, db_session=None):
        self.session_id = session_id
        self.db = db_session
        self.nmap_path = settings.nmap_path

    async def _log(self, level: str, message: str, extra: dict = None):
        """Envía un log en tiempo real a la UI."""
        logger.info(f"[{self.AGENT_NAME}] {message}")
        await ws_manager.send_agent_log(
            session_id=self.session_id,
            agent=self.AGENT_NAME,
            level=level,
            message=message,
            extra=extra or {}
        )

    async def _run_nmap(self, args: List[str], target: str) -> Optional[str]:
        """
        Ejecuta Nmap como subproceso y retorna el XML resultante.
        El output XML se guarda en un archivo temporal para evitar llenar la memoria.
        """
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
                await self._log("warning", f"Nmap terminó con código {proc.returncode}: {stderr.decode()[:200]}")

            # Leer XML resultado
            if os.path.exists(xml_output_path):
                with open(xml_output_path, "r", encoding="utf-8", errors="ignore") as f:
                    xml_content = f.read()
                os.unlink(xml_output_path)
                return xml_content
            return None

        except FileNotFoundError:
            await self._log("error", f"Nmap no encontrado en: {self.nmap_path}. Verifica la instalación.")
            return None
        except Exception as e:
            await self._log("error", f"Error ejecutando Nmap: {e}")
            return None

    async def discover_hosts(self, target: str) -> List[ParsedHost]:
        """
        Fase 1: Descubrimiento de hosts activos en el segmento de red.
        Usa Nmap con ping scan (-sn) para evitar intrusión prematura.
        
        Args:
            target: Segmento CIDR (ej: '192.168.1.0/24') o IP individual.
        
        Returns:
            Lista de ParsedHost con los hosts activos descubiertos.
        """
        await self._log("info", f"Iniciando descubrimiento de hosts en: {target}")

        # Ping scan + detección ARP (sin escaneo de puertos)
        args = ["-sn", "--send-eth", "-T4"]

        xml_content = await self._run_nmap(args, target)
        if not xml_content:
            await self._log("error", "No se pudo obtener resultados de Nmap")
            return []

        hosts = NmapParser.parse_xml(xml_content)
        active_hosts = [h for h in hosts if h.status == "up"]

        await self._log("success", f"Descubiertos {len(active_hosts)} hosts activos de {len(hosts)} totales", {
            "total_scanned": len(hosts),
            "active": len(active_hosts),
            "target": target
        })

        # Notificar a la UI sobre los nuevos hosts
        for host in active_hosts:
            await ws_manager.send_topology_update(self.session_id, {
                "action": "host_discovered",
                "host": {
                    "ip": host.ip_address,
                    "mac": host.mac_address,
                    "hostname": host.hostname,
                    "status": host.status
                }
            })

        return active_hosts

    async def quick_port_scan(self, target_ip: str) -> List[ParsedHost]:
        """
        Escaneo rápido de puertos más comunes para un host individual.
        Útil para clasificar rápidamente los hosts descubiertos.
        
        Args:
            target_ip: IP del host objetivo.
        
        Returns:
            Lista de ParsedHost con puertos y servicios básicos.
        """
        await self._log("info", f"Escaneo rápido de puertos en: {target_ip}")

        # Escaneo de los 1000 puertos más comunes con detección básica de servicios
        args = ["-sS", "-sV", "--version-intensity", "2", "-T4", "--open"]

        xml_content = await self._run_nmap(args, target_ip)
        if not xml_content:
            return []

        hosts = NmapParser.parse_xml(xml_content)

        if hosts:
            host = hosts[0]
            service_count = len([s for s in host.services if s.state == "open"])
            await self._log("success", f"Host {target_ip}: {service_count} puertos abiertos encontrados", {
                "services": [{"port": s.port, "name": s.service_name, "version": s.version}
                             for s in host.services if s.state == "open"]
            })

        return hosts

    async def run(self, target: str, quick_scan: bool = False) -> dict:
        """
        Punto de entrada principal del agente.
        
        Args:
            target: IP, rango CIDR o hostname objetivo.
            quick_scan: Si True, también realiza un escaneo rápido de puertos.
        
        Returns:
            Diccionario con los resultados y el contexto para el LLM.
        """
        await self._log("info", f"=== ReconAgent iniciado para objetivo: {target} ===")

        # Fase 1: Descubrimiento de hosts
        discovered_hosts = await self.discover_hosts(target)

        if not discovered_hosts:
            return {
                "status": "no_hosts",
                "hosts": [],
                "llm_context": f"No se encontraron hosts activos en el segmento {target}.",
                "summary": {"total": 0, "active": 0}
            }

        # Fase 2 (opcional): Escaneo rápido de puertos
        if quick_scan:
            await self._log("info", "Iniciando escaneo rápido de puertos en hosts descubiertos...")
            detailed_hosts = []
            for host in discovered_hosts[:10]:  # Límite de 10 para quick scan
                detailed = await self.quick_port_scan(host.ip_address)
                if detailed:
                    detailed_hosts.extend(detailed)
                await asyncio.sleep(0.5)  # Pequeña pausa entre escaneos
            discovered_hosts = detailed_hosts if detailed_hosts else discovered_hosts

        # Generar contexto para el LLM (ABSTRACTO, no crudo)
        llm_context = NmapParser.generate_llm_context(discovered_hosts)

        await self._log("success", "=== ReconAgent completado ===", {
            "hosts_found": len(discovered_hosts)
        })

        return {
            "status": "completed",
            "hosts": discovered_hosts,
            "llm_context": llm_context,
            "summary": {
                "total_scanned": target,
                "active": len(discovered_hosts)
            }
        }
