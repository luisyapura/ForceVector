# ⚙️ Guía de Implementación — Entorno Local (Windows)

## Proyecto de Tesis: Sistema de Pentesting Autónomo con LLMs (Ollama)

---

## 🧠 1. Objetivo

Esta guía describe la instalación y configuración de un entorno local en Windows para ejecutar un sistema de pentesting asistido por múltiples modelos LLM utilizando **Ollama**, optimizado para hardware de alto rendimiento:

* GPU: RTX 5080
* CPU: Ryzen 9 9950X3D
* RAM: 64 GB

---

## 🖥️ 2. Requisitos Previos

### ✔️ Software necesario

* Windows 10/11 (preferentemente Pro)
* WSL2 habilitado (opcional pero recomendado)
* Drivers NVIDIA actualizados
* CUDA Toolkit (compatible con tu driver)
* Git
* Python 3.11+

---

## 🔧 3. Instalación de Dependencias

### 3.1 Instalar drivers NVIDIA + CUDA

1. Instalar los últimos drivers desde NVIDIA
2. Verificar instalación:

```bash
nvidia-smi
```

Debe mostrar la GPU correctamente.

---

### 3.2 Instalar Python

Descargar desde:
https://www.python.org/downloads/

Verificar:

```bash
python --version
pip --version
```

---

### 3.3 Instalar Git

```bash
git --version
```

---

## 🤖 4. Instalación de Ollama

### 4.1 Descargar Ollama

https://ollama.com/download

Instalar normalmente en Windows.

---

### 4.2 Verificar instalación

```bash
ollama --version
```

---

### 4.3 Probar ejecución básica

```bash
ollama run mistral
```

---

## 📦 5. Descarga de Modelos

### 🔹 Modelo base (ejecutor)

```bash
ollama pull mistral
```

---

### 🔹 Modelo de razonamiento

```bash
ollama pull mixtral
```

---

### 🔹 Modelo especializado en código

```bash
ollama pull deepseek-coder
```

---

## ⚙️ 6. Configuración Optimizada (IMPORTANTE)

Dado tu hardware, se recomienda:

### 🔹 Cuantización

Ollama gestiona automáticamente, pero puedes ajustar:

* Preferir variantes Q4_K_M o similares
* Evitar modelos full precision (innecesario)

---

### 🔹 Variables de entorno (opcional)

```bash
set OLLAMA_NUM_GPU=1
set OLLAMA_MAX_LOADED_MODELS=1
```

👉 Esto fuerza el modelo único en VRAM (clave para tu arquitectura)

---

## 🧩 7. Arquitectura del Proyecto

```
project/
│
├── core/
│   ├── orchestrator.py
│   ├── scheduler.py
│
├── agents/
│   ├── executor.py
│   ├── planner.py
│   ├── coder.py
│
├── memory/
│   ├── store.py
│
├── tools/
│   ├── nmap_wrapper.py
│
└── main.py
```

---

## 🧠 8. Orquestador (Base del Sistema)

### Ejemplo simplificado:

```python
import subprocess

def run_model(model, prompt):
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        capture_output=True
    )
    return result.stdout


def route_task(task):
    if task["type"] == "planning":
        return run_model("mixtral", task["input"])

    elif task["type"] == "code":
        return run_model("deepseek-coder", task["input"])

    else:
        return run_model("mistral", task["input"])
```

---

## 🔄 9. Estrategia de Ejecución

### ✔️ Modelo único en memoria

* Nunca cargar más de un modelo simultáneamente
* Cada llamada a `ollama run` hace load/unload automático

---

### ✔️ Flujo operativo

```
Input → Planner (Mixtral)
      → Executor (Mistral)
      → Coder (DeepSeek, opcional)
      → Resultado
```

---

## 💾 10. Persistencia de Estado

NO depender del contexto del modelo.

Opciones:

* JSON (simple)
* SQLite (recomendado)
* Redis (avanzado)

Ejemplo básico:

```python
import json

def save_log(data):
    with open("log.json", "a") as f:
        f.write(json.dumps(data) + "\n")
```

---

## 🚀 11. Prueba Inicial

```bash
python main.py
```

Ejemplo de input:

```json
{
  "type": "planning",
  "input": "Analiza este objetivo y propone vectores de ataque"
}
```

---

## ⚠️ 12. Problemas Comunes

### ❌ Modelo no carga

* Verificar VRAM disponible
* Reiniciar Ollama

---

### ❌ Lentitud

* Normal en carga de modelos grandes
* Solución: reducir swaps (batching)

---

### ❌ CUDA no detectado

* Verificar drivers
* Reinstalar CUDA

---

## 📌 13. Mejores Prácticas

* Mantener Mistral como modelo residente (si optimizas más adelante)
* Minimizar cambios de modelo
* Loggear TODO (clave para tesis)
* Separar claramente roles de agentes

---

## 🧭 14. Siguientes Pasos

1. Implementar scheduler avanzado
2. Añadir herramientas reales (nmap, ffuf, etc.)
3. Integrar sistema de memoria
4. Evaluación de resultados (métricas)

---

## 🧠 Conclusión

Este enfoque permite ejecutar un sistema multi-modelo en hardware local sin necesidad de paralelismo real, utilizando:

* Orquestación inteligente
* Carga secuencial de modelos
* Persistencia externa de contexto

👉 Base sólida para una tesis de nivel profesional.

---
