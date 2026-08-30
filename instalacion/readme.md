# 🏗️ Especificaciones de Arquitectura y Entorno: ForceVector

Este documento define la **topología de red, los requisitos de sistema y las dependencias de software** necesarias para replicar y desplegar correctamente el framework autónomo de pentesting **ForceVector**.

> **ForceVector** está diseñado bajo una arquitectura distribuida, desacoplando el **frontend táctico**, el **backend cognitivo** y la **capa de datos**, con el objetivo de aproximarse a un despliegue empresarial basado en una arquitectura **C2 (Command & Control)**.

---

## 📐 1. Topología del Laboratorio

ForceVector utiliza una arquitectura distribuida compuesta por tres tipos de nodos:

```text
                         ┌──────────────────────────────┐
                         │       NODO C2 / IA           │
                         │                              │
                         │  Windows Server / Linux      │
                         │                              │
                         │  ┌────────────────────────┐  │
                         │  │ Ollama                 │  │
                         │  │ Qwen3:14b              │  │
                         │  └────────────────────────┘  │
                         │                              │
                         │  ┌────────────────────────┐  │
                         │  │ PostgreSQL + pgvector   │  │
                         │  │ Base de conocimiento    │  │
                         │  └────────────────────────┘  │
                         │                              │
                         │       TCP 11434 / 5432       │
                         └──────────────┬───────────────┘
                                        │
                                        │ Red de laboratorio
                                        │
                         ┌──────────────▼───────────────┐
                         │     NODO ATACANTE            │
                         │                              │
                         │     Kali Linux / Debian      │
                         │                              │
                         │  ┌────────────────────────┐  │
                         │  │ ForceVector Agents     │  │
                         │  │ Nmap                   │  │
                         │  │ Metasploit / msfrpcd   │  │
                         │  └────────────────────────┘  │
                         │                              │
                         │       TCP 55552              │
                         └──────────────┬───────────────┘
                                        │
                                        │ Tráfico de ataque
                                        │
                         ┌──────────────▼───────────────┐
                         │        NODO OBJETIVO         │
                         │                              │
                         │  Metasploitable 2            │
                         │  Windows XP / 7 vulnerables  │
                         │  Windows Server vulnerable   │
                         └──────────────────────────────┘
```

### 1.1. Nodo Atacante — Frontend Táctico

| Parámetro             | Especificación                                         |
| --------------------- | ------------------------------------------------------ |
| **Sistema operativo** | Kali Linux o distribución Debian orientada a seguridad |
| **Rol**               | Frontend táctico y ejecución de agentes                |
| **Funciones**         | Escaneo, enumeración y explotación controlada          |
| **Herramientas**      | Nmap, Metasploit Framework                             |
| **Servicio RPC**      | `msfrpcd`                                              |
| **Puerto RPC**        | TCP `55552`                                            |

El Nodo Atacante ejecuta los agentes de **ForceVector** y constituye la capa responsable de la interacción directa con la infraestructura objetivo.

Entre sus funciones principales se encuentran:

* Ejecución de los agentes de ForceVector.
* Descubrimiento y reconocimiento de red mediante **Nmap**.
* Enumeración de servicios.
* Interacción con **Metasploit Framework**.
* Ejecución controlada de módulos de explotación.
* Comunicación con el backend cognitivo.
* Recuperación de contexto desde la base de conocimiento.

---

### 1.2. Nodo C2 / Inteligencia — Backend Cognitivo

| Parámetro               | Especificación                     |
| ----------------------- | ---------------------------------- |
| **Sistema operativo**   | Windows Server / Linux Server      |
| **Rol**                 | Backend cognitivo y almacenamiento |
| **Motor LLM**           | Ollama                             |
| **Modelo principal**    | `qwen3:14b`                        |
| **Base de datos**       | PostgreSQL                         |
| **Extensión vectorial** | pgvector                           |
| **API LLM**             | TCP `11434`                        |
| **PostgreSQL**          | TCP `5432`                         |

Este nodo concentra los recursos computacionales destinados a la **inteligencia artificial y gestión del conocimiento**.

Su separación respecto al Nodo Atacante permite:

* Dedicar recursos de **CPU/GPU** al procesamiento del LLM.
* Evitar que la inferencia afecte directamente al rendimiento de las herramientas ofensivas.
* Centralizar el conocimiento utilizado por el sistema RAG.
* Separar las funciones cognitivas de las funciones tácticas.
* Simular una arquitectura distribuida similar a un entorno empresarial.

---

### 1.3. Nodo Objetivo — Target

El Nodo Objetivo representa la infraestructura sobre la cual se realizan las pruebas de intrusión controladas.

| Sistema                       | Función                                      |
| ----------------------------- | -------------------------------------------- |
| **Metasploitable 2**          | Sistema Linux deliberadamente vulnerable     |
| **Windows XP**                | Sistema Windows vulnerable para laboratorio  |
| **Windows 7**                 | Sistema Windows vulnerable para laboratorio  |
| **Windows Server vulnerable** | Plataforma objetivo para pruebas controladas |

> ⚠️ **Importante:** todos los sistemas objetivo deben ejecutarse exclusivamente dentro de un entorno de laboratorio aislado y autorizado.

---

# ⚙️ 2. Motores y Servicios Base

La ejecución de ForceVector requiere una serie de servicios instalados y configurados a nivel de sistema operativo.

---

## 2.1. Base de Datos Vectorial — RAG

ForceVector utiliza **PostgreSQL** junto con la extensión **pgvector** para almacenar y consultar representaciones vectoriales utilizadas por el sistema **RAG (Retrieval-Augmented Generation)**.

### Requisitos

| Componente    | Requisito                                   |
| ------------- | ------------------------------------------- |
| **Motor**     | PostgreSQL `>= 13`                          |
| **Extensión** | `pgvector`                                  |
| **Puerto**    | TCP `5432`                                  |
| **Acceso**    | Desde el Nodo Atacante                      |
| **Uso**       | Almacenamiento y recuperación de embeddings |

La base de datos permite almacenar información contextual, incluyendo conocimiento relacionado con:

* CVEs.
* Vulnerabilidades.
* Técnicas de explotación.
* Información contextual para los agentes.
* Embeddings utilizados por el sistema RAG.

### Conectividad

El Nodo Atacante debe poder establecer conexión con PostgreSQL:

```text
Nodo Atacante
      │
      │ TCP/5432
      ▼
PostgreSQL + pgvector
```

---

## 2.2. Motor Cognitivo — Ollama

**Ollama** proporciona la infraestructura local necesaria para ejecutar el modelo de lenguaje utilizado por ForceVector.

### Requisitos

| Componente               | Especificación                  |
| ------------------------ | ------------------------------- |
| **Motor**                | Ollama                          |
| **Modelo principal**     | `qwen3:14b`                     |
| **Modelo de embeddings** | `nomic-embed-text` *(opcional)* |
| **Puerto API**           | TCP `11434`                     |
| **Host**                 | `0.0.0.0`                       |

El modelo utilizado puede modificarse mediante el archivo:

```text
config.json
```

Por defecto, el sistema contempla:

```text
qwen3:14b
```

Para la generación de embeddings destinados al sistema RAG puede utilizarse opcionalmente:

```text
nomic-embed-text
```

### Configuración de red

La API de Ollama debe estar disponible para el Nodo Atacante.

Por ejemplo:

```bash
OLLAMA_HOST=0.0.0.0
```

La arquitectura resultante es:

```text
ForceVector
     │
     │ HTTP
     │ TCP/11434
     ▼
Ollama
     │
     ▼
Qwen3:14b
```

---

## 2.3. Herramientas Ofensivas — Kali Linux

El Nodo Atacante requiere las herramientas necesarias para ejecutar las fases tácticas del pentesting.

### Metasploit Framework

| Parámetro    | Requisito                        |
| ------------ | -------------------------------- |
| **Versión**  | `>= 6.4`                         |
| **Servicio** | `msfrpcd`                        |
| **Puerto**   | TCP `55552`                      |
| **Bind**     | `127.0.0.1` o IP correspondiente |

El servicio RPC proporciona una interfaz programática para que ForceVector pueda interactuar con Metasploit.

```text
ForceVector Agent
       │
       │ MSF RPC
       │ TCP/55552
       ▼
   msfrpcd
       │
       ▼
Metasploit Framework
```

### Nmap

Nmap debe estar instalado globalmente y disponible mediante `$PATH`.

Comprobación:

```bash
which nmap
```

o:

```bash
nmap --version
```

Se recomienda disponer de privilegios `sudo` para permitir operaciones que requieran capacidades elevadas, especialmente:

* Escaneos UDP.
* OS fingerprinting.
* Service fingerprinting avanzado.
* Técnicas de descubrimiento que requieran raw sockets.

---

# 🐍 3. Dependencias de Software — Python

ForceVector requiere **Python 3.10 o superior**.

Comprobar la versión instalada:

```bash
python3 --version
```

Ejemplo esperado:

```text
Python 3.10.x
```

o superior.

---

## 3.1. Instalación de dependencias

Las dependencias Python se encuentran definidas en:

```text
requirements.txt
```

La instalación puede realizarse mediante:

```bash
pip install -r requirements.txt
```

Se recomienda utilizar un entorno virtual:

```bash
python3 -m venv .venv
```

Activación:

```bash
source .venv/bin/activate
```

Posteriormente:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3.2. Dependencias principales

| Categoría         | Dependencia       | Función                               |
| ----------------- | ----------------- | ------------------------------------- |
| **API / Red**     | `requests`        | Comunicación con la API de Ollama     |
| **Base de datos** | `psycopg2-binary` | Conexión con PostgreSQL               |
| **Vector DB**     | `pgvector`        | Interacción con vectores y embeddings |
| **C2 / Pivoting** | `pymetasploit3`   | Comunicación con Metasploit RPC       |
| **Reportes**      | `Jinja2`          | Generación de plantillas HTML         |
| **Reportes**      | `weasyprint`      | Conversión de HTML a PDF              |

---

# 🔌 4. Matriz de Conectividad

La siguiente matriz resume las comunicaciones necesarias entre los diferentes componentes.

| Origen        | Destino        | Protocolo |   Puerto | Propósito                    |
| ------------- | -------------- | --------- | -------: | ---------------------------- |
| Nodo Atacante | Ollama         | HTTP/TCP  |  `11434` | Inferencia LLM               |
| Nodo Atacante | PostgreSQL     | TCP       |   `5432` | RAG / vectores               |
| ForceVector   | Metasploit RPC | TCP       |  `55552` | Control de Metasploit        |
| Nodo Atacante | Target         | TCP/UDP   | Variable | Reconocimiento y explotación |
| Ollama        | —              | —         |        — | Ejecución local del LLM      |
| PostgreSQL    | —              | —         |   `5432` | Servicio de persistencia     |

> Los puertos utilizados pueden modificarse según la configuración del laboratorio, pero cualquier cambio debe reflejarse en `config.json` y en las reglas de firewall correspondientes.

---

# 🧩 5. Resumen de Componentes

```text
┌─────────────────────────────────────────────────────────────┐
│                        FORCEVECTOR                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐       ┌─────────────────────────┐  │
│  │   NODO ATACANTE     │       │       NODO C2 / IA      │  │
│  │                     │       │                         │  │
│  │  Kali Linux         │◄─────►│  Ollama                 │  │
│  │  ForceVector        │       │  Qwen3:14b              │  │
│  │  Nmap               │       │                         │  │
│  │  Metasploit         │       │  PostgreSQL             │  │
│  │  msfrpcd            │       │  pgvector               │  │
│  │                     │       │                         │  │
│  └──────────┬──────────┘       └─────────────────────────┘  │
│             │                                               │
│             │ Reconocimiento / Explotación                   │
│             ▼                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    NODO OBJETIVO                        │ │
│  │                                                         │ │
│  │  Metasploitable 2 / Windows XP / Windows 7 / Server    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
---

# 🏁 6. Arquitectura Final

La arquitectura de ForceVector puede resumirse en tres capas principales:

### 🔴 Capa Táctica

Responsable de la interacción con los objetivos:

```text
Kali Linux
├── ForceVector Agents
├── Nmap
└── Metasploit Framework
```

### 🧠 Capa Cognitiva

Responsable del razonamiento y toma de decisiones:

```text
Ollama
└── Qwen3:14b
```

### 🗄️ Capa de Conocimiento

Responsable de proporcionar contexto persistente al sistema:

```text
PostgreSQL
└── pgvector
    └── Embeddings / CVEs / Knowledge Base
```

Esta separación permite a **ForceVector** implementar un modelo distribuido en el que las capacidades de **reconocimiento y explotación**, **razonamiento mediante LLM** y **gestión del conocimiento** permanecen desacopladas, facilitando la escalabilidad, reproducibilidad y evolución del framework.
