# ⚙️ Guía de Implementación — Entorno Local (Windows)

## Proyecto de Tesis: Sistema de Pentesting Autónomo con LLMs (Ollama)

---

## 🧠 1. Objetivo

Implementar un entorno reproducible para ejecutar un sistema de pentesting autónomo basado en **arquitectura multi-modelo**, optimizado para hardware local:

* GPU: RTX 5080
* CPU: Ryzen 9 9950X3D
* RAM: 64 GB

El sistema utiliza **orquestación secuencial de modelos LLM** para maximizar capacidad sin requerir paralelismo en VRAM.

---

## 🖥️ 2. Requisitos Previos

* Windows 10/11
* Drivers NVIDIA actualizados
* CUDA Toolkit compatible
* Python 3.11+
* Git

Verificación:

```bash
nvidia-smi
python --version
git --version
```

---

## 🤖 3. Instalación de Ollama

Descargar:
https://ollama.com/download

Verificar:

```bash
ollama --version
```

---

# 📦 4. Instalación de Modelos (Versionada y Reproducible)

## 🔹 4.1 Modelo Ejecutor (Base del sistema)

```bash
ollama pull mistral:7b-instruct-q4_K_M
```

### ✔️ Justificación técnica

* Baja latencia → ideal para loops iterativos
* Buen instruction-following
* Consumo reducido de VRAM
* Estable para parsing de outputs

👉 Rol:

* ejecución de tareas
* interpretación de resultados
* control del flujo operativo

---

## 🔹 4.2 Modelo de Razonamiento

```bash
wget https://huggingface.co/TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF/resolve/main/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf?download=true -O mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf
```

### ✔️ Justificación técnica

* Arquitectura MoE (Mixture of Experts)
* Mejor rendimiento en razonamiento multi-step
* Capacidad de planificación compleja

👉 Rol:

* diseño de vectores de ataque
* toma de decisiones
* priorización

---

## 🔹 4.3 Modelo Especializado en Código

```bash
ollama pull deepseek-coder:6.7b-instruct-q4_K_M
```

### ✔️ Justificación técnica

* Optimizado para generación de código
* Mejor desempeño en scripting técnico
* Alta precisión en sintaxis

👉 Rol:

* generación de exploits
* creación de payloads
* automatización técnica

---

## 🔍 Verificación

```bash
ollama list
```

---

# ⚙️ 5. Configuración Crítica

```bash
set OLLAMA_MAX_LOADED_MODELS=1
set OLLAMA_NUM_GPU=1
```

### ✔️ Objetivo

* Evitar múltiples modelos en VRAM
* Prevenir crashes por memoria
* Forzar ejecución secuencial

---

# 🧠 6. ¿Por qué usar versiones *Instruct*?

## 🔹 Diferencia clave

### Modelo base

* Predicción de texto sin control
* Salidas inconsistentes
* Difícil de automatizar

### Modelo Instruct

* Fine-tuned para seguir instrucciones
* Salidas estructuradas
* Mayor consistencia

---

## ⚠️ Impacto en el sistema

Tu arquitectura depende de:

* prompts estructurados
* outputs parseables
* decisiones encadenadas

👉 Sin *Instruct*:

* respuestas caóticas
* formato impredecible
* fallos en automatización

---

## ✅ Ventajas en esta tesis

* Mejor adherencia a formatos (JSON, listas, etc.)
* Menor necesidad de prompt engineering complejo
* Mayor estabilidad operativa

---

## 🧩 Justificación formal (defensa)

> Se seleccionaron variantes *Instruct* debido a su alineación con tareas dirigidas, reducción de entropía en las salidas y mejor integración con sistemas automatizados de orquestación.

---

# 🏗️ 7. Arquitectura del Sistema

```text
Input
  ↓
Planner (Mixtral)
  ↓
Executor (Mistral)
  ↓
Coder (DeepSeek, opcional)
  ↓
Resultado
```
```
├── ForceVector/
│   ├── config/
│   │   └── config.json       # Archivo de configuración
│   ├── agents/
│   │   ├── __init__.py
│   │   └── ollama_client.py   # Módulo reutilizable de conexión
│   └── main.py                # Script principal de ejecución
```
---

## 🔄 Ejecución real (Single Model Strategy)

* Un solo modelo activo a la vez
* Carga bajo demanda
* Descarga implícita al cambiar

---

# ⚙️ 8. Orquestador (Base del sistema)

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
        return run_model("mixtral:8x7b-instruct-q4_K_M", task["input"])

    elif task["type"] == "code":
        return run_model("deepseek-coder:6.7b-instruct-q4_K_M", task["input"])

    else:
        return run_model("mistral:7b-instruct-q4_K_M", task["input"])
```

---

# 💾 9. Persistencia de Estado

Ejemplo:

```python
import json

def save_log(data):
    with open("log.json", "a") as f:
        f.write(json.dumps(data) + "\n")
```

---

# 🚀 10. Prueba Inicial

```bash
python main.py
```

---

# ⚠️ 11. Problemas Comunes

### Modelo no carga

* Verificar VRAM
* Reiniciar Ollama

### Lentitud

* Normal en modelos grandes
* Reducir cambios de modelo

### CUDA no detectado

* Revisar drivers

---

# 📌 12. Buenas Prácticas

* Evitar tags genéricos (usar versiones exactas)
* Minimizar swaps de modelo
* Loggear todas las decisiones
* Separar roles claramente

---

# 🧭 13. Conclusión

El sistema implementado:

* Utiliza múltiples LLMs especializados
* Opera en hardware local limitado
* Evita paralelismo mediante orquestación
* Garantiza reproducibilidad

👉 Esto lo posiciona como una arquitectura sólida, defendible y alineada con sistemas reales de IA aplicada.

---
