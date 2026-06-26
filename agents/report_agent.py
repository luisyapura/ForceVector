"""
AIPentest-MitL - Agente de Reportes (ReportAgent)
Genera informes estructurados en Markdown/HTML/PDF con los hallazgos del pentest.
"""
import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

from core.websocket_manager import ws_manager
from core.llm_client import llm_client

logger = logging.getLogger(__name__)

REPORT_TEMPLATE = """
# Informe de Prueba de Penetración
**Proyecto:** {session_name}  
**Fecha:** {date}  
**Clasificación:** CONFIDENCIAL - USO INTERNO

---

## Resumen Ejecutivo

{executive_summary}

---

## Estadísticas del Engagement

| Métrica | Valor |
|---------|-------|
| Hosts descubiertos | {total_hosts} |
| Hosts comprometidos | {compromised_hosts} |
| Servicios enumerados | {total_services} |
| Vulnerabilidades críticas | {critical_vulns} |
| Vulnerabilidades altas | {high_vulns} |
| Vulnerabilidades medias | {medium_vulns} |
| Vectores de ataque probados | {tested_vectors} |

---

## Hallazgos por Host

{host_findings}

---

## Vectores de Ataque y Exploits

{exploit_findings}

---

## Análisis MITRE ATT&CK

{mitre_analysis}

---

## Recomendaciones de Remediación

{remediation}

---

## Metodología

Este informe ha sido generado automáticamente por el sistema AIPentest-MitL, 
un framework de pruebas de penetración asistido por IA que integra el modelo de lenguaje 
local **{llm_model}** para el análisis semántico y la generación de contexto.

Todas las acciones de explotación fueron previamente aprobadas por el operador 
mediante el mecanismo **Man-in-the-Loop (MitL)**.

---
*Generado por AIPentest-MitL | {date}*
"""


class ReportAgent:
    """
    Agente de Generación de Reportes.
    Consolida todos los hallazgos de la sesión en un informe profesional.
    """

    AGENT_NAME = "ReportAgent"

    def __init__(self, session_id: str, db_session=None):
        self.session_id = session_id
        self.db = db_session

    async def _log(self, level: str, message: str, extra: dict = None):
        logger.info(f"[{self.AGENT_NAME}] {message}")
        await ws_manager.send_agent_log(
            session_id=self.session_id,
            agent=self.AGENT_NAME,
            level=level,
            message=message,
            extra=extra or {}
        )

    def _generate_host_findings(self, hosts: List[dict]) -> str:
        """Genera la sección de hallazgos por host."""
        if not hosts:
            return "_No se encontraron hosts activos._"

        sections = []
        for host in hosts:
            ip = host.get("ip_address", "N/A")
            hostname = host.get("hostname", "")
            os_name = host.get("os_name", "Desconocido")
            compromised = "⚠️ **COMPROMETIDO**" if host.get("is_compromised") else "✅ Sin comprometer"

            section = [f"### Host: {ip} {'(' + hostname + ')' if hostname else ''}"]
            section.append(f"- **Estado:** {compromised}")
            section.append(f"- **Sistema Operativo:** {os_name}")

            services = host.get("services", [])
            if services:
                section.append(f"- **Servicios ({len(services)}):**")
                for svc in services:
                    section.append(f"  - `{svc.get('port')}/{svc.get('protocol', 'tcp')}` {svc.get('service_name', '')} `{svc.get('version', '')}`")

            vulns = host.get("vulnerabilities", [])
            if vulns:
                section.append(f"- **Vulnerabilidades ({len(vulns)}):**")
                for vuln in vulns:
                    severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "🔵"}.get(
                        vuln.get("severity", "info"), "⚪"
                    )
                    cve = f" `{vuln['cve_id']}`" if vuln.get("cve_id") else ""
                    section.append(f"  - {severity_icon} **{vuln.get('title', 'N/A')}**{cve}")

            sections.append("\n".join(section))

        return "\n\n".join(sections)

    def _generate_exploit_findings(self, exploits: List[dict]) -> str:
        """Genera la sección de exploits."""
        if not exploits:
            return "_No se realizaron intentos de explotación._"

        sections = []
        for exploit in exploits:
            status_icon = "✅" if exploit.get("status") == "success" else "❌"
            section = [
                f"#### {status_icon} {exploit.get('tool', 'N/A')} - {exploit.get('module', 'N/A')}",
                f"- **Objetivo:** {exploit.get('target', 'N/A')}",
                f"- **Estado:** {exploit.get('status', 'N/A')}",
                f"- **Fecha:** {exploit.get('executed_at', 'N/A')}",
            ]
            if exploit.get("output"):
                section.append(f"- **Resultado:** `{exploit['output'][:200]}`")
            sections.append("\n".join(section))

        return "\n\n".join(sections)

    def _generate_mitre_analysis(self, findings: dict) -> str:
        """Genera el análisis de tácticas y técnicas MITRE ATT&CK."""
        techniques = {}

        for vuln in findings.get("vulnerabilities", []):
            tech = vuln.get("mitre_technique")
            if tech:
                techniques[tech] = techniques.get(tech, 0) + 1

        for exploit in findings.get("exploits", []):
            # Los exploits tienen técnica T1190 por defecto
            techniques["T1190"] = techniques.get("T1190", 0) + 1

        if not techniques:
            return "_No se identificaron técnicas MITRE ATT&CK específicas._"

        lines = ["| Técnica | Ocurrencias |", "|---------|-------------|"]
        for tech, count in sorted(techniques.items()):
            lines.append(f"| {tech} | {count} |")

        return "\n".join(lines)

    async def generate_report(self, session_data: dict) -> str:
        """
        Genera el informe completo en formato Markdown.
        
        Args:
            session_data: Datos de la sesión con hosts, vulns y exploits.
        
        Returns:
            Contenido del informe en Markdown.
        """
        await self._log("info", "Iniciando generación de informe...")

        hosts = session_data.get("hosts", [])
        exploits = session_data.get("exploits", [])
        vulns = []
        for host in hosts:
            vulns.extend(host.get("vulnerabilities", []))

        # Estadísticas
        total_hosts = len(hosts)
        compromised = sum(1 for h in hosts if h.get("is_compromised"))
        total_services = sum(len(h.get("services", [])) for h in hosts)
        critical_vulns = sum(1 for v in vulns if v.get("severity") == "critical")
        high_vulns = sum(1 for v in vulns if v.get("severity") == "high")
        medium_vulns = sum(1 for v in vulns if v.get("severity") == "medium")

        # Generar resumen ejecutivo con LLM
        await self._log("info", "Generando resumen ejecutivo con LLM...")
        executive_summary = await llm_client.generate_report_summary({
            "total_hosts": total_hosts,
            "compromised_hosts": compromised,
            "critical_vulnerabilities": critical_vulns,
            "high_vulnerabilities": high_vulns,
            "exploits_attempted": len(exploits),
            "exploits_successful": sum(1 for e in exploits if e.get("status") == "success")
        })

        # Generar secciones
        host_findings = self._generate_host_findings(hosts)
        exploit_findings = self._generate_exploit_findings(exploits)
        mitre_analysis = self._generate_mitre_analysis({"vulnerabilities": vulns, "exploits": exploits})

        remediation = """
### Prioridades de Remediación

1. **CRÍTICO** - Aplicar parches de seguridad para vulnerabilidades con CVSS ≥ 9.0 inmediatamente.
2. **ALTO** - Revisar configuraciones de servicios expuestos y deshabilitar versiones obsoletas.
3. **MEDIO** - Implementar autenticación multifactor en servicios de acceso remoto (SSH, RDP).
4. **BAJO** - Revisar políticas de contraseñas y configuración de protocolos no seguros.
"""

        report = REPORT_TEMPLATE.format(
            session_name=session_data.get("name", "Sesión de Pentest"),
            date=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            executive_summary=executive_summary,
            total_hosts=total_hosts,
            compromised_hosts=compromised,
            total_services=total_services,
            critical_vulns=critical_vulns,
            high_vulns=high_vulns,
            medium_vulns=medium_vulns,
            tested_vectors=len(exploits),
            host_findings=host_findings,
            exploit_findings=exploit_findings,
            mitre_analysis=mitre_analysis,
            remediation=remediation,
            llm_model="Llama 3 / Mistral (Ollama)"
        )

        await self._log("success", "Informe generado correctamente")
        return report

    async def save_report(self, report_content: str, session_id: str) -> str:
        """Guarda el informe en disco."""
        reports_dir = "./reports"
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"pentest_report_{session_id}_{timestamp}.md"
        filepath = os.path.join(reports_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_content)

        await self._log("success", f"Informe guardado en: {filepath}")
        return filepath

    async def run(self, session_data: dict) -> dict:
        """Punto de entrada principal del agente."""
        await self._log("info", "=== ReportAgent iniciado ===")

        report_content = await self.generate_report(session_data)
        filepath = await self.save_report(report_content, self.session_id)

        return {
            "status": "completed",
            "report_path": filepath,
            "report_content": report_content,
            "summary": "Informe generado correctamente"
        }
