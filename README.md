<p align="center">
  <img src="/img/portada.png" width="1200" height="400" alt="portada">
</p>
# ⚡ ForceVector
### IA para Pentesting Ético

> “Que la fuerza del conocimiento te guíe.”

---

## 🧠 Descripción

**ForceVector** es un sistema autónomo basado en inteligencia artificial diseñado para asistir en procesos de **pentesting ético**, mediante la correlación de información, análisis de vulnerabilidades y priorización de vectores de ataque.

El objetivo del proyecto es emular el razonamiento de un pentester humano, permitiendo:
- Interpretar resultados de reconocimiento
- Identificar vulnerabilidades relevantes
- Priorizar objetivos de forma inteligente
- Recomendar acciones concretas

---

## 🎯 Objetivos del proyecto

- Desarrollar un sistema de apoyo al pentesting basado en IA local
- Automatizar la toma de decisiones en fases de reconocimiento y explotación
- Integrar fuentes de inteligencia (CVE, exploits, etc.)
- Reducir la dependencia de análisis manual
- Mantener un enfoque **ético y controlado**

---

## ⚙️ Arquitectura (visión inicial)
[Escaneo / Entrada de datos]
↓
[Parser]
↓
[Base de conocimiento]
↓
[Motor IA (LLM)]
↓
[Motor de decisión]
↓
[Recomendaciones]

---

## 🔍 Funcionalidades previstas

- 🔎 Reconocimiento y enumeración (integración con herramientas como Nmap)
- 🧠 Análisis mediante modelos LLM locales
- 📊 Correlación de vulnerabilidades (CVE, exploits)
- 🎯 Priorización de vectores de ataque
- 📋 Generación de recomendaciones para pentesting
- 📑 (Futuro) generación automática de informes

---

## 🧪 Tecnologías utilizadas

- Python
- LLM local (Ollama + modelos como Mistral)
- Nmap (fase posterior)
- Base de datos de vulnerabilidades (NVD, ExploitDB)
- SQLite / futuras alternativas
- (Futuro) integración con frameworks de explotación

---

## 🚧 Estado del proyecto

> 🔧 En desarrollo (fase inicial)

Actualmente enfocado en:
- Configuración del entorno IA local
- Diseño de prompts y validación del modelo
- Definición de arquitectura base

---

## 📚 Contexto académico

Este proyecto forma parte de una **Tesis de Máster en Ciberseguridad**, centrada en:

> El uso de inteligencia artificial para la automatización y optimización de procesos de pentesting.

---

## ⚠️ Uso ético

Este proyecto está diseñado exclusivamente para:

- Entornos controlados
- Laboratorios de pruebas
- Pentesting autorizado

**El uso indebido de esta herramienta es responsabilidad del usuario.**

---

## 📌 Roadmap (simplificado)

- [x] Definición del concepto
- [x] Selección del modelo LLM
- [ ] Integración con entrada de datos (simulada)
- [ ] Base de conocimiento (CVE + exploits)
- [ ] Motor de priorización
- [ ] Integración con herramientas reales
- [ ] Automatización completa del ciclo de pentesting

---

## 👨‍💻 Autor

Proyecto desarrollado como parte de una Tesis en Ciberseguridad.

---

## 📄 Licencia

Actualmente no se ha definido una licencia pública.  
El proyecto se mantiene en desarrollo privado.

---
