<p align="center">
  <img src="/img/portada.png" width="1200" height="500" alt="portada">
</p>

<h1 align="center">⚡ForceVector</h1>
<h3 align="center">IA para Pentesting Ético</h3>

<p align="center">
  <em>“Que la fuerza del conocimiento te guíe.”</em>
</p>

---

## 🧠 Descripción

**ForceVector** es un sistema autónomo basado en inteligencia artificial diseñado para asistir en procesos de **pentesting ético**, mediante el análisis, correlación y priorización de vectores de ataque.

El sistema busca emular el razonamiento de un pentester humano, permitiendo tomar decisiones informadas en tiempo real.

---

## 🚀 Badges

<p align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge\&logo=python)
![Status](https://img.shields.io/badge/Status-En%20Desarrollo-orange?style=for-the-badge)
![AI](https://img.shields.io/badge/LLM-Local-green?style=for-the-badge)
![Database](https://img.shields.io/badge/Database-PostgreSQL-blue?style=for-the-badge\&logo=postgresql)
![Security](https://img.shields.io/badge/Cybersecurity-Pentesting-critical?style=for-the-badge)
![License](https://img.shields.io/badge/License-Private-lightgrey?style=for-the-badge)

</p>

---

## 🎯 Objetivos

* Automatizar el análisis de superficies de ataque
* Priorizar vulnerabilidades según impacto real
* Asistir en la toma de decisiones en pentesting
* Integrar inteligencia de amenazas en tiempo real
* Mantener un enfoque ético y controlado

---

## ⚙️ Arquitectura (visión inicial)

```
                  +-----------------------------------+
                  |         Agente Orquestador        |
                  |         (Qwen2.5-Coder-7B)        |
                  +-----------------+-----------------+
                                    |
            +-----------------------+-----------------------+
            |                       |                       |
  +---------v---------+   +---------v---------+   +---------v---------+
  | Reconocimiento    |   |   Protocolos      |   |    Evaluación de  |
  | (Scapy / nmap)    |   | (ARP/DNS/SMB)     |   |   Autenticación   |
  +---------+---------+   +---------+---------+   +---------+---------+
            |                       |                       |
            +-----------------------+-----------------------+
                                    |
                          +---------v---------+
                          |   Base de datos   |
                          | (Vectorial / Logs)|
                          +-------------------+
```

---

## 🔍 Funcionalidades

* 🔎 Reconocimiento y enumeración
* 🧠 Análisis con LLM local
* 📊 Correlación de CVEs y exploits
* 🎯 Priorización de vectores de ataque
* 📋 Recomendaciones técnicas

---

## 🧪 Tecnologías

* Python
* Ollama (LLM local)
* Mistral 7B Instruct (modelo de prueba)
* PostgreSQL
* SQLAlchemy (ORM)
* Nmap *(fase posterior)*
* Hashcat

---

## 🗄️ Base de Datos

El sistema utiliza **PostgreSQL** como motor de base de datos desde las fases iniciales, permitiendo:

* Modelado relacional robusto
* Consultas complejas y eficientes
* Escalabilidad para futuras integraciones
* Soporte para correlación avanzada de vulnerabilidades

---

## 🚧 Estado del Proyecto

> 🔧 Fase inicial — diseño de arquitectura, validación del modelo y pruebas de primeros agentes.

---

## 📚 Contexto Académico

Proyecto desarrollado como parte de una **Tesis de Máster en Ciberseguridad**, enfocado en la automatización del pentesting mediante inteligencia artificial.

---

## ⚠️ Uso Ético

Este proyecto está destinado exclusivamente a:

* Laboratorios controlados
* Entornos autorizados
* Investigación en ciberseguridad

El uso indebido es responsabilidad del usuario.

---

## 📌 Roadmap

* [x] Definición del concepto
* [x] Selección del LLM
* [ ] Integración de entradas reales
* [ ] Diseño e implementación del modelo de datos
* [ ] Motor de priorización
* [ ] Automatización completa

---

## 👨‍💻 Autor

Desarrollado como parte de una Tesis en Ciberseguridad.

---

## 📄 Licencia

Proyecto actualmente en desarrollo privado.
