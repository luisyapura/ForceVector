# `ForceVector` — Framework Pentesting Basado en IA

<p align="center">
  <img src="/img/portada.png" width="1200" height="500" alt="ForceVector Banner">
</p>

<h1 align="center">⚡ ForceVector</h1>

<h3 align="center">
Framework Multiagente de Pentesting Ético Basado en Inteligencia Artificial
</h3>

<p align="center">
  <em>
    “Que la fuerza del conocimiento ofensivo te guíe.”
  </em>
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge\&logo=python)
![Status](https://img.shields.io/badge/Status-In%20Research-orange?style=for-the-badge)
![AI](https://img.shields.io/badge/LLM-Local%20AI-green?style=for-the-badge)
![Database](https://img.shields.io/badge/PostgreSQL-pgvector-blue?style=for-the-badge\&logo=postgresql)
![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-critical?style=for-the-badge)
![Security](https://img.shields.io/badge/Cybersecurity-Offensive%20Security-darkred?style=for-the-badge)
![License](https://img.shields.io/badge/License-Private-lightgrey?style=for-the-badge)

</p>

---
# ForceVector — Framework Pentesting Basado en IA

## 🧠 Descripción General

ForceVector es un framework experimental de pentesting ético asistido por Inteligencia Artificial diseñado para automatizar parcialmente auditorías ofensivas sobre infraestructuras empresariales modernas.

El proyecto nace como parte de una investigación académica enfocada en las limitaciones estructurales del pentesting tradicional y en la necesidad de desarrollar arquitecturas híbridas capaces de combinar:

* razonamiento semántico mediante LLMs,
* correlación contextual de vulnerabilidades,
* memoria persistente vectorial,
* y automatización ofensiva supervisada.

A diferencia de los escáneres convencionales basados únicamente en firmas estáticas, ForceVector busca aproximarse al razonamiento táctico de un operador Red Team humano, permitiendo:

* correlacionar CVEs,
* inferir rutas de ataque,
* priorizar vectores críticos,
* y reducir la carga cognitiva asociada al análisis ofensivo manual.

## ⚡ Objetivos del Proyecto

### Objetivo General

Diseñar y validar una arquitectura multiagente basada en IA capaz de ejecutar pruebas de intrusión semiautónomas sobre redes empresariales bajo un enfoque controlado y éticamente supervisado.

### Objetivos Específicos

* Automatizar tareas de reconocimiento y enumeración.
* Implementar memoria semántica persistente mediante pgvector.
* Correlacionar vulnerabilidades utilizando la base de datos local de CVEs.
* Reducir alucinaciones operativas mediante grounding técnico.
* Integrar agentes especializados por dominio funcional.
* Incorporar esquemas de supervisión Man-in-the-Loop (MitL).
* Permitir planificación táctica basada en contexto.
* Mantener cumplimiento operativo y control de alcance.

## 🏗️ Arquitectura Conceptual

La arquitectura de ForceVector se basa en un modelo jerárquico híbrido dividido en:

* plano semántico de planificación,
* plano táctico de ejecución,
* y memoria contextual compartida.

```text
                           +----------------------------------+
                           |      Agente Orquestador IA       |
                           |       (LLM + Planificador)       |
                           +----------------+-----------------+
                                            |
                +---------------------------+---------------------------+
                |                           |                           |
    +-----------v-----------+   +-----------v-----------+   +-----------v-----------+
    | Reconocimiento        |   | Enumeración / Scan    |   | Autenticación         |
    | Scapy / Nmap          |   | Nessus / OpenVAS      |   | SMB / Kerberos / LDAP |
    +-----------+-----------+   +-----------+-----------+   +-----------+-----------+
                |                           |                           |
                +---------------------------+---------------------------+
                                            |
                               +------------v------------+
                               |     Memoria Vectorial   |
                               | PostgreSQL + pgvector   |
                               +------------+------------+
                                            |
                     +----------------------+----------------------+
                     |                                             |
          +----------v----------+                     +-----------v-----------+
          | Explotación         |                     | Generación de Reporte |
          | Metasploit/sqlmap   |                     | Evidencias y Riesgo   |
          +---------------------+                     +-----------------------+
```

## 🧩 Filosofía Arquitectónica

El proyecto se fundamenta en una separación explícita entre:

| Capa                | Responsabilidad                                   |
| ------------------- | ------------------------------------------------- |
| Plano Semántico     | Razonamiento, correlación y planificación táctica |
| Plano Táctico       | Ejecución controlada de acciones ofensivas        |
| Memoria Persistente | Compartición contextual entre agentes             |
| MitL                | Supervisión humana de acciones críticas           |

Esta aproximación busca mitigar:

* saturación de contexto,
* explosión de tokens,
* pérdida de persistencia lógica,
* y alucinaciones ofensivas.

## 🔍 Capacidades Principales

### Reconocimiento Inteligente

* Descubrimiento de hosts.
* Fingerprinting activo y pasivo.
* Enumeración de servicios.
* Detección contextual de superficie de ataque.

### Correlación Semántica de Vulnerabilidades

Integración directa con base de datos CVE local.

Priorización ofensiva basada en:

* criticidad,
* exposición,
* transitividad,
* y contexto topológico.

### Memoria Vectorial Persistente

Uso de PostgreSQL + pgvector para:

* almacenar telemetría ofensiva,
* preservar estado entre agentes,
* evitar re-procesamiento contextual,
* compartir conocimiento táctico.

### Arquitectura Multiagente

Agentes especializados para:

* reconocimiento,
* escaneo,
* explotación,
* autenticación,
* y generación de reportes.

### Supervisión Humana (MitL)

Las acciones de alto impacto requieren aprobación explícita:

* explotación,
* movimiento lateral,
* post-explotación,
* ejecución de payloads.

## 🧪 Tecnologías

### Inteligencia Artificial

* Ollama
* Qwen3
* Arquitecturas RAG
* Chain-of-Thought Planning

### Seguridad Ofensiva

* Nmap
* Scapy
* Metasploit Framework (MSF RPC)
* sqlmap
* Hashcat
* Nessus
* OpenVAS

### Backend y Datos

* Python
* PostgreSQL
* pgvector
* SQLAlchemy
* FastAPI (planificado)

### Infraestructura

* Linux (Kali Linux para ejecución táctica)
* Windows Server (Para bases de datos de conocimiento y LLM)
* Virtualización de laboratorios
* Entornos aislados
* GPUs locales para inferencia

## 🗄️ Memoria Semántica y RAG

Uno de los pilares fundamentales de ForceVector es la eliminación del intercambio lineal de contexto entre agentes.

En lugar de transmitir grandes volúmenes de texto entre modelos, el sistema:

* transforma resultados ofensivos en embeddings,
* almacena información estructurada en pgvector,
* y recupera únicamente el contexto relevante en tiempo real.

Esto permite:

* reducir costos de inferencia,
* minimizar amnesia contextual,
* estabilizar razonamiento multiagente,
* y mantener persistencia táctica.

## 🧠 Motivación Técnica

El proyecto surge como respuesta a múltiples limitaciones observadas en el estado del arte actual:

* dependencia heurística del operador humano,
* escalabilidad limitada del pentesting tradicional,
* crecimiento exponencial de CVEs,
* altos costos operativos de modelos SaaS,
* pérdida de contexto en arquitecturas ReAct,
* y baja trazabilidad de decisiones ofensivas.

ForceVector propone una arquitectura híbrida local orientada a:

* eficiencia,
* persistencia,
* trazabilidad,
* escalabilidad,
* y control operacional.

## ⚙️ Flujo Operativo

| Fase                 | Automatización |
| -------------------- | -------------- |
| Reconocimiento       | Autónoma       |
| Modelado de amenazas | Autónoma       |
| Enumeración          | Autónoma       |
| Correlación de CVEs  | Autónoma       |
| Explotación          | Supervisada    |
| Post-explotación     | Supervisada    |
| Reporte              | Autónoma       |

## 📊 Objetivos de Validación

El framework será validado mediante:

* laboratorios virtuales,
* entornos vulnerables controlados,
* benchmarking ofensivo,
* y comparación frente a enfoques tradicionales.

### Benchmarks Objetivo

* AutoPenBench
* AI-Pentest-Benchmark
* Metasploitable
* VulnNetLabs

## 🚧 Estado Actual

* * Investigación arquitectónica completada

* * Diseño conceptual multiagente

* * Definición del modelo de memoria vectorial

* * Evaluación del estado del arte

* * Selección de stack tecnológico

* ! Implementación modular en progreso

* ! Integración de agentes especializados

* ! Desarrollo del motor RAG

* * Pipeline ofensivo completo

* * Benchmarks automatizados

* * Sistema MitL operativo

## 🛡️ Seguridad y Uso Ético

Este proyecto está orientado exclusivamente a:

* investigación académica,
* laboratorios controlados,
* auditorías autorizadas,
* y desarrollo defensivo.

### Restricciones

No está diseñado para uso malicioso.

No debe utilizarse sobre infraestructuras sin autorización explícita.

El usuario final es responsable del cumplimiento legal y ético.

## 📚 Contexto Académico

Proyecto desarrollado como parte de una:

**Tesis de Máster en Ciberseguridad**

enfocada en automatización ofensiva inteligente, arquitecturas multiagente y memoria vectorial aplicada al pentesting.

## 📌 Roadmap

### Fase 1 — Investigación

* [x] Estado del arte
* [x] Diseño conceptual
* [x] Arquitectura inicial
* [x] Selección de modelos IA

### Fase 2 — Núcleo Operativo

* [x] Integración PostgreSQL + pgvector
* [x] Motor RAG
* [x] Sistema de memoria contextual
* [x] APIs internas de agentes

### Fase 3 — Agentes Especializados

* [x] Agente Recon
* [x] Agente Scan
* [x] Agente Auth
* [x] Agente Exploit
* [x] Agente Report

### Fase 4 — Validación

* [ ] Benchmarking
* [ ] Comparativa contra pentesting tradicional
* [x] Validación MitL
* [x] Métricas de falsos positivos

## 👨‍💻 Autor

**Luis Yapura**

Investigación y desarrollo en:

* Inteligencia Artificial aplicada a ciberseguridad
* Automatización ofensiva
* Arquitecturas multiagente
* Memoria vectorial y RAG

## 📄 Licencia

Actualmente el proyecto permanece bajo una licencia privada y en fase de investigación académica.

No se autoriza:

* redistribución,
* explotación comercial,
* ni despliegue operativo sin autorización explícita.
