# ForceVector v2.0

> **Framework de Pruebas de Penetración Asistido por IA con Man-in-the-Loop**  
> Trabajo de Fin de Máster | Arquitectura Distribuida | LLM Local GPU (Ollama)

---

## Hardware Objetivo

| Componente | Especificación |
|---|---|
| **CPU** | AMD Ryzen 9 9950X3D (16 cores, 3D V-Cache 128 MB) |
| **RAM** | 64 GB DDR5 |
| **GPU** | NVIDIA GeForce RTX 5080 (16 GB VRAM) |
| **Almacenamiento** | 4 TB NVMe SSD |

---

## Arquitectura v2.0 — Dos Nodos

```
┌──────────────────────────────────────────────────────────────────┐
│  SERVIDOR WINDOWS (AMD 9950X3D + RTX 5080)                      │
│                                                                  │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │  Ollama (GPU)  │  │ PostgreSQL 18 +  │  │  FastAPI v2.0   │  │
│  │  llama3.3 70B  │  │    pgvector      │  │  + React UI     │  │
│  │  qwen2.5 32B   │  │  CVE + Exploit-DB│  │  + Redis        │  │
│  └────────────────┘  └──────────────────┘  └─────────────────┘  │
│                                                                  │
└────────────────────────────┬─────────────────────────────────────┘
                             │ REST API / WebSocket + JWT
                             │ LAN o WireGuard VPN
┌────────────────────────────┴─────────────────────────────────────┐
│  NODO KALI LINUX (VM VMware Workstation Pro)                     │
│                                                                  │
│  ┌──────────────┐  ┌─────────────────┐  ┌────────────────────┐  │
│  │  ReconAgent  │  │   ScanAgent     │  │  ExploitAgent      │  │
│  │  nmap/masscan│  │  nmap NSE/vuln  │  │  Metasploit RPC    │  │
│  └──────────────┘  └─────────────────┘  └────────────────────┘  │
│  ┌──────────────┐  ┌─────────────────┐                          │
│  │  AuthAgent   │  │  ReportAgent    │                          │
│  │  hydra/cmxec │  │  Markdown/PDF   │                          │
│  └──────────────┘  └─────────────────┘                          │
│                                                                  │
└────────────────────────────┬─────────────────────────────────────┘
                             │ Ataques controlados (MitL)
                             ▼
                    [Red Objetivo — VMs laboratorio]
```

---

## Instalación

### Nodo 1: Servidor Windows

```powershell
# Ejecutar como Administrador en PowerShell 7+
cd D:\TFM
pwsh -ExecutionPolicy Bypass -File scripts\install_windows_server.ps1

# Parámetros opcionales:
# -PgPassword "MiPassword" -NodeName "mi-servidor"
```

El script instala automáticamente:
- PostgreSQL 18 + extensión pgvector
- Redis (cola de tareas)
- Ollama con soporte CUDA (RTX 5080)
- Modelos LLM: `llama3.3:70b-instruct-q4_K_M` + `qwen2.5-coder:32b-q4_K_M`
- Modelo embeddings: `nomic-embed-text:v1.5`
- Python 3.12 + dependencias del backend
- Reglas de Windows Firewall (puertos 8000, 11434, 6379)

### Nodo 2: Kali Linux (VM VMware)

```bash
# En la VM Kali Linux
cd /opt/ForceVector
sudo bash scripts/install_kali_agent.sh --server-ip 192.168.x.x --node-name kali-vm-01
```

### Sincronización de Inteligencia (CVE + Exploit-DB)

```bash
# Primera sincronización completa (~1-2 horas con API Key NVD)
python scripts/cve_sync.py --source all

# Sincronización incremental (programar en Task Scheduler — diaria)
python scripts/cve_sync.py --days 1
```

---

## Inicio del Sistema

### Servidor Windows

```powershell
pwsh start_server.ps1
```

```
  ╔═══════════════════════════════════════════════════╗
  ║     ForceVector v2.0 — Servidor Windows           ║
  ╠═══════════════════════════════════════════════════╣
  ║  API:     http://localhost:8000/api/docs           ║
  ║  UI:      http://localhost:3000                    ║
  ║  Ollama:  http://localhost:11434                   ║
  ╚═══════════════════════════════════════════════════╝
```

### Nodo Kali VMware

```bash
bash start_agent.sh
```

---

## Estructura del Proyecto

```
ForceVector/
├── backend/                      # Servidor Windows
│   ├── main.py                   # FastAPI v2.0 entry point
│   ├── requirements.txt          # PostgreSQL + pgvector + Redis + JWT
│   ├── .env.example              # Config servidor + agente
│   ├── core/
│   │   ├── config.py             # Config centralizada (node_mode, DB, Redis, JWT)
│   │   ├── database.py           # PostgreSQL + pgvector + pool conexiones
│   │   ├── models.py             # ORM: CVE catalog, Exploit-DB, AgentNode, grafo red
│   │   ├── llm_client.py         # Cliente Ollama (GPU RTX 5080)
│   │   ├── orchestrator.py       # Orquestador OODA central
│   │   └── websocket_manager.py  # Tiempo real
│   ├── agents/                   # Lógica de agentes (ejecución en Kali via API)
│   │   ├── recon_agent.py
│   │   ├── scan_agent.py
│   │   ├── exploit_agent.py
│   │   └── report_agent.py
│   ├── parsers/
│   │   └── nmap_parser.py
│   └── routers/
│       ├── sessions.py           # CRUD sesiones de pentest
│       ├── agents.py             # ⭐ Gestión de nodos Kali VMware (JWT)
│       └── intel.py              # ⭐ Búsqueda RAG CVE/Exploit-DB local
├── agent/                        # Nodo Kali VMware
│   └── agent_runner.py           # ⭐ Cliente agente: recibe órdenes, ejecuta tools
├── frontend/
│   └── index.html                # UI Web (autocontenida)
└── scripts/
    ├── install_windows_server.ps1 # ⭐ Instalador servidor Windows (PostgreSQL+Ollama)
    ├── install_kali_agent.sh      # ⭐ Instalador nodo Kali VMware
    └── cve_sync.py               # ⭐ Sincronizador CVE/Exploit-DB → PostgreSQL
```

---

## Modelos LLM (Ollama — GPU RTX 5080)

| Modelo | VRAM necesaria | Uso recomendado |
|---|---|---|
| `llama3.3:70b-instruct-q4_K_M` | ~42 GB (VRAM+RAM) | **Producción** — Máximo razonamiento |
| `qwen2.5-coder:32b-q4_K_M` | ~20 GB | **Desarrollo** — Iteraciones rápidas |
| `nomic-embed-text:v1.5` | ~300 MB | **Embeddings** — Siempre activo |

```ini
# backend/.env — cambiar modelo activo
OLLAMA_MODEL=llama3.3:70b-instruct-q4_K_M
```

---

## API Endpoints Principales

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/sessions/` | Crear sesión de pentest |
| `POST` | `/api/sessions/{id}/start` | Iniciar engagement |
| `GET`  | `/api/sessions/{id}/state` | Estado del orquestador |
| `POST` | `/api/sessions/{id}/chat` | Chat con el LLM |
| `GET`  | `/api/sessions/{id}/approvals` | Aprobaciones MitL pendientes |
| `POST` | `/api/sessions/{id}/approvals/{tid}/decide` | Resolver aprobación MitL |
| `POST` | `/api/v1/agents/register` | ⭐ Registrar nodo Kali (devuelve JWT) |
| `POST` | `/api/v1/agents/{name}/heartbeat` | ⭐ Heartbeat del nodo Kali |
| `GET`  | `/api/v1/agents/` | ⭐ Listar nodos Kali conectados |
| `POST` | `/api/v1/intel/search` | ⭐ Búsqueda RAG CVE/Exploit-DB |
| `GET`  | `/api/v1/intel/cve/{id}` | ⭐ Detalle CVE local |
| `GET`  | `/api/v1/intel/stats` | ⭐ Estadísticas catálogo |
| `GET`  | `/api/health` | Estado completo del sistema |
| `WS`   | `/ws/{session_id}` | WebSocket sesión en tiempo real |
| `WS`   | `/ws/agent/{node_name}` | ⭐ Canal instrucciones → nodo Kali |

---

## Flujo Man-in-the-Loop (MitL)

```
[ExploitAgent en Kali]
        │ POST /api/v1/approvals
        ▼
[Servidor Windows — LLM valida coherencia]
        │ WebSocket → UI React
        ▼
┌─────────────────────────────────┐
│  Dashboard — Ticket de Aprobación│
│  Exploit: ms17_010_eternalblue  │
│  Target: 192.168.1.50 / :445    │
│  Riesgo: CRÍTICO | XAI: [LLM]   │
│  [✅ Aprobar] [❌ Denegar] [✏️ Edit]│
└─────────────────────────────────┘
        │ JWT firmado → agente Kali
        ▼
[ExploitAgent ejecuta Metasploit RPC]
        │
        ▼
[Resultado → BD PostgreSQL → Grafo de Red actualizado]
```

---

## ⚠️ Aviso Legal

Este software está desarrollado exclusivamente con fines académicos y de investigación en seguridad informática. El uso de este framework en sistemas sin autorización explícita por escrito del propietario es **ilegal** según la legislación vigente (Código Penal Español, Art. 197 bis). El usuario es el único responsable de cumplir con todas las leyes aplicables en su jurisdicción.
