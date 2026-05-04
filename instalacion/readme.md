# 📘 Guía de Implementación — Entorno Local

## 🧪 Proyecto de Tesis: Sistema de Pentesting Autónomo con LLMs (Ollama)

---

## 🎯 1. Objetivo

Implementar un entorno reproducible para ejecutar un sistema de pentesting autónomo basado en una arquitectura multi-modelo, optimizado para ejecutarse en tu estación de trabajo, este contara de un servidor local con 1 o mas clientes.

El sistema utiliza orquestación secuencial para maximizar la precisión analítica y de programación, respetando los límites de memoria gráfica y evitando el offloading a CPU.

---

## ⚙️ 2. Requisitos Previos

**Sistema Operativo:** Ubuntu 24.04 LTS./Kali Linux / Windows

**Hardware:** Ryzen 9 9950X3D, 64 GB RAM, NVIDIA RTX 5080 (16 GB VRAM).

**Software y Drivers:**

* Drivers NVIDIA 550+ o superior.
* CUDA Toolkit 12.4+ compatible.
* Python 3.11+.
* Git.
* PostgreSQL (para el almacenamiento de logs de auditoría).

**Verificación del entorno:**

```bash
nvidia-smi
python3 --version
git --version
psql --version
```

---

## 🧠 3. Instalación de Ollama

Instala la última versión de Ollama ejecutando el script oficial en la terminal:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verifica el correcto funcionamiento del servicio:

```bash
ollama --version
```

---

## 📦 4. Instalación y Dimensionamiento de Modelos

Para aprovechar la GPU sin exceder los 16 GB de VRAM, utilizaremos una estrategia de un solo modelo cargado a la vez, asegurando que cada nodo del pipeline tenga una latencia óptima y un ajuste de parámetros (quantization) adecuado.

### 🔹 4.1 Modelo Orquestador / Planner

**Modelo:** qwen3-coder:14b

**Comando de descarga:**

```bash
ollama pull qwen3-coder:14b
```

✔️ **Justificación técnica y hardware:**

* **Razonamiento:** El tamaño de 14B ofrece el nivel de abstracción y estructura (JSON Schema) necesario para diseñar árboles de ataque lógicos.
* **Memoria:** Ocupa aproximadamente 9.2 GB en VRAM (versión Q4_K_M), dejando espacio en memoria para el Executor.

---

### 🔹 4.2 Modelo Executor y Analista de Herramientas

**Modelo:** mistral-nemo:12b-instruct

**Comando de descarga:**

```bash
ollama pull mistral-nemo:12b-instruct
```

✔️ **Justificación técnica y hardware:**

* **Eficiencia:** Ocupa 7.8 GB en VRAM.
* **Propósito:** Excelente manejo de I/O de terminal, parsing de comandos y ejecución de herramientas de seguridad ofensiva (como Nmap, SQLMap, etc.) de manera directa.

---

### 🔹 4.3 Modelo Especializado en Código

**Modelo:** deepseek-coder:6.7b

**Comando de descarga:**

```bash
ollama pull deepseek-coder:6.7b
```

✔️ **Justificación técnica y hardware:**

* **Precisión:** Ocupa 4.1 GB en VRAM.
* **Propósito:** Generación, depuración e inserción de payloads y exploits sin contaminar el contexto del orquestador.

---

## 🧩 5. Configuración del Servidor y Gestión de Memoria

Para evitar la contención de memoria gráfica y garantizar que solo un modelo se cargue a la vez (evitando la saturación de los 16 GB), exporta estas variables de entorno en el sistema:

```bash
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_GPU=1
```

---

## 🧬 6. Diferenciación de Modelos Instruct vs. Base

Para tareas de automatización y orquestación de agentes, se deben utilizar únicamente variantes de tipo Instruct o Coder.

* **Modelos Base:** Predicción de texto no determinista. Generan respuestas conversacionales impredecibles y no parseables.
* **Modelos Instruct/Coder:** Optimizados para el seguimiento de esquemas (JSON, listas estructuradas, comandos de consola).

**Justificación formal:** La reducción de la entropía en las salidas es fundamental para que el flujo de agentes no se interrumpa debido a respuestas caóticas o no estructuradas.

---

## 🏗️ 7. Arquitectura del Sistema

El sistema procesa la información de forma secuencial, pasando el contexto paso a paso entre los agentes.

**Estructura de Directorios**

```plaintext
ForceVector/
├── config/
│   └── config.json # Configuración y parámetros del sistema
├── agents/
│   ├── __init__.py
│   └── ollama_client.py # Cliente de conexión reutilizable
└── main.py # Orquestador principal
```
