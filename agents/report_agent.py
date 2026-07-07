import os
import json
import re
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

def clean_ansi_escape_sequences(text: str) -> str:
    """
    Elimina los códigos de color ANSI y caracteres de control de la terminal
    para que el texto sea legible en el PDF final.
    """
    # Regex para capturar secuencias de escape ANSI de 7 y 8 bits
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    texto_limpio = ansi_escape.sub('', text)
    
    # Eliminar otros caracteres de control extraños (excepto saltos de línea y tabulaciones)
    texto_limpio = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\x85\xA0-\uD7FF\uE000-\uFFFD\U00010000-\U0010ffff]', '', texto_limpio)
    return texto_limpio

def generate_pdf_report(base_dir: str, threat_model_path: str):
    """
    Genera un informe de Pentesting profesional en PDF.
    """
    print("\n\033[96m[*] (Report Agent) Saneando telemetría y generando reporte final...\033[0m")
    
    base_path = Path(base_dir)
    logo_path = base_path / "img" / "logo_forcevector.png"
    templates_dir = base_path / "templates"
    sessions_dir = base_path / "logs" / "sessions"
    output_pdf = base_path / f"Informe_Auditoria_FV_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    # 1. Cargar el Threat Model (Vulnerabilidades)
    threat_model_data = []
    if os.path.exists(threat_model_path):
        try:
            with open(threat_model_path, 'r', encoding='utf-8') as f:
                threat_model_data = json.load(f)
        except Exception as e:
            print(f"\033[91m[-] Error leyendo el Threat Model para el reporte: {e}\033[0m")
    else:
        print(f"\033[93m[!] No se encontró el Threat Model en {threat_model_path}\033[0m")

    # 2. Cargar las Evidencias y Sanear ANSI
    sessions_data = []
    if sessions_dir.exists():
        for log_file in sorted(sessions_dir.glob("*.txt")):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    raw_content = f.read()
                    
                    # Limpieza de secuencias de terminal
                    clean_content = clean_ansi_escape_sequences(raw_content)
                    
                    # Truncar logs masivos
                    if len(clean_content) > 8000:
                        clean_content = clean_content[:8000] + "\n\n[... TRUNCADO: EL REGISTRO SUPERA LA LONGITUD MÁXIMA PARA EL REPORTE ...]"
                    
                    sessions_data.append({
                        "filename": log_file.name,
                        "content": clean_content.strip()
                    })
            except Exception as e:
                print(f"\033[93m[-] Error procesando archivo de sesión {log_file.name}: {e}\033[0m")

    # 3. Renderizar Plantilla
    print("\033[92m[*] Renderizando estructura documental (Jinja2)...\033[0m")
    try:
        env = Environment(loader=FileSystemLoader(str(templates_dir)))
        template = env.get_template('report_template.html')
        
        html_out = template.render(
            logo_path=str(logo_path.absolute()),
            date=datetime.now().strftime("%d de %B de %Y"),
            total_vectores=len(threat_model_data),
            threat_model=threat_model_data,
            sessions=sessions_data
        )
    except Exception as e:
        print(f"\033[91m[-] Error en el motor de plantillas: {e}\033[0m")
        return

    # 4. Exportar a PDF
    print(f"\033[92m[*] Compilando documento PDF con WeasyPrint...\033[0m")
    try:
        # Añadir CSS base opcional de WeasyPrint si es necesario
        HTML(string=html_out, base_url=str(base_path)).write_pdf(str(output_pdf))
        print(f"\033[38;5;82m[+] ¡INFORME PROFESIONAL GENERADO CON ÉXITO!\033[0m")
        print(f"\033[38;5;82m[+] Ruta: {output_pdf}\033[0m")
    except Exception as e:
        print(f"\033[91m[-] Error crítico generando el PDF (Revisa dependencias de WeasyPrint): {e}\033[0m")

if __name__ == "__main__":
    base_project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tm_path = os.path.join(base_project_dir, "logs", "threat_model_192_168_139_128.json") # Ajustar ruta para test
    generate_pdf_report(base_project_dir, tm_path)
