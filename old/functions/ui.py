import os

# Constantes de color ANSI
COLOR_NEON_GREEN = "\033[38;5;82m"
COLOR_RESET = "\033[0m"
COLOR_INFO = "\033[96m"
COLOR_ERROR = "\033[91m"
COLOR_SUCCESS = "\033[92m"
COLOR_YELLOW = "\033[38;5;220m"

BANNER = """
 ███████╗ ██████╗ ██████╗  ██████╗███████╗██╗   ██╗███████╗ ██████╗████████╗ ██████╗ ██████╗ 
 ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██║   ██║██╔════╝██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗
 █████╗  ██║   ██║██████╔╝██║     █████╗  ██║   ██║█████╗  ██║        ██║   ██║   ██║██████╔╝
 ██╔══╝  ██║   ██║██╔══██╗██║     ██╔══╝  ██║   ██║██╔══╝  ██║        ██║   ██║   ██║██╔══██╗
 ██║     ╚██████╔╝██║  ██║╚██████╗███████╗╚██████╔╝███████╗╚██████╗   ██║   ╚██████╔╝██║  ██║
 
                              [ FORCE VECTOR // IA PENTESTING ]
                                  [ MODO: ETHICAL MODE ]       
"""

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{COLOR_NEON_GREEN}{BANNER}{COLOR_RESET}")

def print_operational_flow():
    print(f"\n{COLOR_INFO}=== FLUJO OPERATIVO ==={COLOR_RESET}")
    print(f"{'Fase':<25} | {'Automatización':<15}")
    print("-" * 43)
    print(f"{'1. Reconocimiento (Descubrimiento)':<25} | {COLOR_NEON_GREEN}Autónoma{COLOR_RESET}")
    print(f"{'2. Escaneo (Superficie/Versiones)':<25} | {COLOR_NEON_GREEN}Autónoma{COLOR_RESET}")
    print(f"{'3. Modelado de amenazas':<25} | {COLOR_NEON_GREEN}Autónoma (Ciclo FOR){COLOR_RESET}")
    print(f"{'4. Enumeración':<25} | {COLOR_NEON_GREEN}Autónoma{COLOR_RESET}")
    print(f"{'5. Explotación':<25} | {COLOR_YELLOW}Supervisada (HITL){COLOR_RESET}")
    print(f"{'6. Post-explotación/Pivot':<25} | {COLOR_YELLOW}Supervisada (MSF RPC){COLOR_RESET}")
    print(f"{'7. Reporte':<25} | {COLOR_NEON_GREEN}Autónoma{COLOR_RESET}")
    print("-" * 43)
