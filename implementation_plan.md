# Plan de Implementacion - ForceVector
## Arquitectura del Sistema (basada en el codigo existente)

---

## Estructura de archivos existente

```
forcevector/
+-- main.py                    (610 lineas)
+-- agents/
|   +-- agent_utils.py         (78 lineas)
|   +-- recon_agent.py         (75 lineas)
|   +-- scan_agent.py          (97 lineas)
|   +-- exploit_agent.py       (300 lineas)
|   +-- auth_agent.py          (20 lineas)
|   +-- web_agent.py           (21 lineas)
|   +-- ad_agent.py            (18 lineas)
|   +-- db_agent.py            (19 lineas)
|   +-- privesc_agent.py       (18 lineas)
|   +-- report_agent.py        (98 lineas)
+-- config/
|   +-- conifg.json
+-- logs/
|   +-- recon_results.json
|   +-- tfm_hallucination_metrics.json
|   +-- tfm_llm_debug.log
+-- templates/
|   +-- report_template.html
+-- img/
    +-- logo_forcevector.png
```

---

## Flujo Operativo del Sistema

El flujo esta controlado por el REPL de main.py:

```
main()
  |
  +-- check_directory_structure()    # Crea carpetas si no existen
  +-- generate_config() / load JSON  # Lee config/conifg.json o genera interactivo
  +-- check_ollama_connection()      # GET /api/tags a Ollama
  +-- verify_and_configure_models()  # Valida modelos instalados
  +-- print_banner()                 # Banner ANSI
  +-- setup_vector_database()        # PostgreSQL: extension vector + tabla agent_memory
  |
  +-- while True (REPL):
        "flow"        -> print_operational_flow()
        "recon <CIDR>"-> execute_autonomous_flow(skip_recon=False)
        "scan <IP>"   -> execute_autonomous_flow(skip_recon=True)
        "exploit <IP>"-> execute_exploitation_phase()
        <otro texto>  -> ask_ollama() [Orquestador LLM]
```

### Fases automaticas: execute_autonomous_flow()

```
FASE 1 - Reconocimiento (recon_agent.run_recon)
  |   Nmap ping sweep sobre CIDR
  |   Retorna lista de hosts activos [{ip, mac}]
  |
FASE 2 - Escaneo (scan_agent.run_scan por cada host)
  |   Nmap TCP: -sV -O -F -T4
  |   Nmap UDP: -sU -sV -F -T4
  |   Parseo regex -> {ip, os, ports:[{portid,protocol,state,service,version}]}
  |   Guarda scan_<IP>.json en logs/<target>/<ip>/
  |   INSERT INTO agent_memory (task_id='recon_port_vector', content=JSON) por cada puerto
  |
FASE 3 - Modelado de Amenazas (LLM iterativo)
    SELECT content FROM agent_memory WHERE task_id='recon_port_vector'
    Por cada vector:
      |  direct_ollama_query() -> modelo "analyzer" -> prompt simple sin ejemplos
      |  Parseo regex JSON de la respuesta
      |  Acumula en objetivos_analizados[]
    DELETE + INSERT agent_memory (task_id='threat_model_results', content=JSON[])
    Guarda threat_model_<IP>.json en logs/<target>/<ip>/
```

### Fases supervisadas: execute_exploitation_phase()

```
FASE 4/5 - Explotacion HITL (exploit_agent.run_exploitation_plan)
  |   Carga threat_model_<IP>.json del disco
  |   Por cada vector en el threat_model:
  |     Determina categoria: web/auth/ad/database/rce
  |     |
  |     +-- web      -> web_agent.run(vector, config_data)
  |     +-- auth     -> auth_agent.run(vector, config_data)
  |     +-- ad       -> ad_agent.run(vector, config_data)
  |     +-- database -> db_agent.run(vector, config_data)
  |     +-- rce/*    -> _execute_rce_metasploit(vector, config_data)
  |
  +-- _execute_rce_metasploit():
        1. _get_dynamic_lhost()          # Resolucion de IP atacante via socket
        2. _find_real_msf_module_by_cve()# RAG offline: grep CVE en /usr/share/metasploit-framework
        3. Configura system_prompt segun si encontro modulo real o no
        4. ask_ollama_exploit()          # Genera script .rc con LLM
        5. _verify_msf_module()          # Comprueba existencia fisica del modulo .rb
        6. _log_llm_debug()             # Guarda traza en logs/tfm_llm_debug.log
        7. Si modulo invalido:
             _log_hallucination()        # Guarda en logs/tfm_hallucination_metrics.json
             Aborta ejecucion
        8. Si modulo valido:
             Inyecta cabecera spool/setg al script rc
             interact_hitl()            # HITL: [E]jecutar | [M]odificar | [A]bortar
             msfconsole -q -r <archivo.rc>
```

### Chat libre: ask_ollama()

```
ask_ollama(prompt, config_data, db_conn)
  |
  Modelo: config_data["models"]["orchestrator"]
  System prompt: Orquestador ForceVector en espanol, puede emitir bloques ```sql```
  |
  Streaming POST /api/generate con num_ctx=8192, num_predict=4096
  |
  Intercepcion de SQL:
    Si respuesta contiene ```sql ... ```:
      Filtro blocklist: drop|delete|truncate|alter|grant|revoke -> deniega
      Si pasa el filtro: cur.execute(sql_query)
      Segunda llamada LLM con resultados BD como contexto
      Modelo segunda llamada: "Analista de ForceVector"
```

---

## Modulos y Funciones por Archivo

### main.py

| Funcion | Descripcion |
|---------|-------------|
| `print_banner()` | Imprime banner ASCII ANSI, limpia pantalla |
| `print_operational_flow()` | Tabla de fases y nivel de automatizacion |
| `check_directory_structure(base_path)` | Crea config/, agents/, logs/, projects/ si no existen |
| `generate_config(config_path)` | Wizard interactivo -> guarda conifg.json |
| `check_ollama_connection(config_data, silent)` | GET /api/tags con timeout 5s |
| `verify_and_configure_models(config_data, config_path)` | Comprueba orchestrator y analyzer estan en Ollama instalados |
| `check_postgres_connection(config_data, silent)` | psycopg2.connect con timeout 5s |
| `setup_vector_database(config_data)` | CREATE EXTENSION vector + CREATE TABLE agent_memory, retorna conn |
| `direct_ollama_query(prompt, config_data)` | Llamada streaming al modelo "analyzer", retorna texto completo |
| `execute_autonomous_flow(target, config_data, db_conn, logs_path, skip_recon)` | Coordina Fases 1, 2, 3 |
| `execute_exploitation_phase(target_ip, config_data, logs_path)` | Carga threat model y delega a exploit_agent |
| `ask_ollama(prompt, config_data, db_conn, follow_up_task)` | Chat libre con orquestador, intercepta SQL |
| `main()` | Entry point: config, verificaciones, REPL |

### agents/agent_utils.py

| Funcion | Descripcion |
|---------|-------------|
| `ask_ollama_exploit(prompt, system_prompt, config_data)` | POST /api/generate no-streaming, temperatura 0.0, timeout 120s. Usado por todos los agentes de explotacion |
| `interact_hitl(command_text, is_msf_resource)` | Muestra codigo al operador. Opciones: [E] ejecutar, [M] modificar en nano/EDITOR, [A] abortar. Si es .rc -> msfconsole -q -r |

### agents/recon_agent.py

- `run_recon(target, logs_path)` — Nmap ping sweep (`-sn`) sobre CIDR. Parsea hosts activos. Guarda `recon_results.json`. Retorna lista `[{ip, mac}]`.

### agents/scan_agent.py

- `run_scan(target_ip, host_dir)` — Dos rondas de Nmap: TCP (`-sV -O -F -T4`) y UDP (`-sU -sV -F -T4`). Parseo regex linea a linea. Guarda `scan_<IP>.json`. Retorna dict `{ip, os, ports:[...]}`.
- `_parse_nmap_output(output, host_data, is_udp)` — Extrae OS y puertos abiertos/open|filtered con regex.

### agents/exploit_agent.py

| Funcion | Descripcion |
|---------|-------------|
| `run_exploitation_plan(threat_model_path, config_data)` | Dispatcher: carga JSON, itera vectores, enruta por categoria |
| `_determinar_categoria(servicio)` | Clasifica por nombre de servicio: web/auth/ad/database/rce |
| `_get_dynamic_lhost(rhost_ip)` | Resuelve LHOST via UDP socket hacia RHOST |
| `_find_real_msf_module_by_cve(cves, os_target, service)` | RAG offline: grep CVE en /usr/share/metasploit-framework/modules/exploits. Dos intentos: con filtro de servicio, luego sin el |
| `_verify_msf_module(rc_content)` | Extrae "use <modulo>" del script .rc y verifica si el .rb existe en disco |
| `_log_hallucination(vector, fake_module)` | Append a logs/tfm_hallucination_metrics.json |
| `_log_llm_debug(vector, sys_prompt, prompt, response, fake_module)` | Append a logs/tfm_llm_debug.log |
| `_execute_rce_metasploit(vector, config_data)` | Flujo completo RCE: RAG -> LLM -> verificacion -> guardarrail -> HITL |

### agents/auth_agent.py / web_agent.py / ad_agent.py / db_agent.py / privesc_agent.py

Todos siguen el mismo patron de 18-21 lineas:
```
run(vector, config_data):
  1. Construye system_prompt especializado (texto fijo)
  2. prompt = "Vector: " + json.dumps(vector)
  3. comando = ask_ollama_exploit(prompt, sys_prompt, config_data)
  4. Si comando: interact_hitl(comando, is_msf_resource=False)
```

Cada uno con su especializacion:
- `auth_agent`: genera comando hydra/medusa/ncrack
- `web_agent`: genera comando sqlmap/nikto/dirb/curl
- `ad_agent`: genera comandos Impacket/CrackMapExec para AD
- `db_agent`: genera consultas de enumeracion de base de datos
- `privesc_agent`: genera script para escalada de privilegios local

### agents/report_agent.py

- `clean_ansi_escape_sequences(text)` — Limpia codigos de escape ANSI del texto de logs.
- `generate_pdf_report(base_dir, threat_model_path)` — Carga threat model JSON + logs de sesiones de logs/sessions/*.txt, renderiza Jinja2 con templates/report_template.html, exporta PDF con WeasyPrint.

---

## Base de Datos

**PostgreSQL** con extension `pgvector`.

Tabla actual:
```sql
CREATE TABLE IF NOT EXISTS agent_memory (
    id        bigserial PRIMARY KEY,
    task_id   varchar(255),
    content   text,
    embedding vector(4096)
);
```

Uso real de `task_id` como discriminador de tipo:
- `'recon_port_vector'` — un registro por puerto detectado en Fase 2. `content` = JSON del vector de puerto.
- `'threat_model_results'` — un registro con array JSON completo del analisis de Fase 3.

---

## Configuracion

El sistema lee `config/conifg.json` (o genera un wizard interactivo la primera vez):

```json
{
  "server": {
    "host": "<IP Ollama>",
    "port": 11434,
    "keep_alive_seconds": 0
  },
  "models": {
    "orchestrator": "<modelo>",
    "analyzer": "<modelo>",
    "temperature_orch": 0.1,
    "temperature_exploit": 0.0
  },
  "database": {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "postgres",
    "password": "<password>",
    "dbname": "forcevector_db"
  }
}
```

El path de la config se construye como: `Path.home() / "forcevector" / "config" / "config.json"`

---

## Sistema de Metricas TFM

### logs/tfm_hallucination_metrics.json

Generado por `_log_hallucination()` en exploit_agent.py. Se escribe cuando el guardarrail detecta que el LLM genero un modulo de Metasploit que no existe en el filesystem de Kali.

Formato de cada entrada:
```json
{
  "timestamp": "2025-01-01 12:00:00",
  "ip": "192.168.139.128",
  "puerto": "21",
  "servicio": "ftp",
  "version": "vsftpd 2.3.4",
  "fake_module_generated": "exploit/unix/ftp/vsftpd_backdoor_2023"
}
```

### logs/tfm_llm_debug.log

Generado por `_log_llm_debug()` en exploit_agent.py. Registro cualitativo de cada interaccion LLM durante Fases 4/5. Incluye system prompt completo, user prompt, respuesta raw del LLM y estado (ALUCINACION / VALIDO).

---

## Comunicacion con Ollama

Dos clientes HTTP en el sistema:

| Funcion | Endpoint | Stream | Timeout | Modelo usado |
|---------|----------|--------|---------|--------------|
| `ask_ollama()` (orquestador) | POST /api/generate | Si | 300s | `config["models"]["orchestrator"]` |
| `direct_ollama_query()` (Fase 3) | POST /api/generate | Si | 180s | `config["models"]["analyzer"]` |
| `ask_ollama_exploit()` (agentes) | POST /api/generate | No | 120s | `config["models"]["orchestrator"]` |
| `check_ollama_connection()` | GET /api/tags | No | 5s | — |
| `verify_and_configure_models()` | GET /api/tags | No | 5s | — |

---

## Guardarrail Anti-Alucinacion (Fase 4/5)

El flujo de verificacion en `_execute_rce_metasploit()`:

```
1. RAG offline: grep CVE en /usr/share/metasploit-framework/modules/exploits
   Si encuentra modulo real -> system_prompt fuerza "use <modulo_real>" al LLM
   Si no encuentra -> system_prompt libre (LLM puede elegir modulo)

2. LLM genera script .rc

3. _verify_msf_module():
   Extrae linea "use <modulo>" del script
   Construye ruta: /usr/share/metasploit-framework/modules/<modulo>.rb
   os.path.exists() -> True/False

4. Si modulo no existe en disco:
   - Imprime "[!] GUARDARRAIL ACTIVADO"
   - _log_hallucination() -> tfm_hallucination_metrics.json
   - _log_llm_debug() -> tfm_llm_debug.log
   - Retorna sin ejecutar

5. Si modulo existe:
   - Inyecta cabecera spool/setg al script
   - interact_hitl() -> operador decide [E/M/A]
   - Si E: msfconsole -q -r <archivo.rc>
```

---

## Dependencias del Sistema

Librerias Python (declaradas en el codigo con import):
- `psycopg2` — conexion PostgreSQL
- `requests` — llamadas HTTP a Ollama
- `jinja2` — renderizado de plantilla HTML para PDF
- `weasyprint` — exportacion PDF
- Standard library: `os, sys, json, re, traceback, pathlib, subprocess, socket, time, tempfile`

Herramientas externas en Kali (invocadas por subprocess):
- `nmap` — Fases 1 y 2
- `msfconsole` — Fase 4/5 (script .rc)
- `nano` (o $EDITOR) — edicion HITL del script
- `hydra / medusa / ncrack` — auth_agent (generado por LLM)
- `sqlmap / nikto / dirb` — web_agent (generado por LLM)
