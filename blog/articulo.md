# De la Teoría a la Práctica: Diseño de un Framework de Pentesting Asistido por IA y Arquitecturas Multiagente

**Por Luis Yapura**
*Basado en el Trabajo Fin de Máster: "Diseño de un Sistema de Pentesting Basado en IA" (Máster en Ciberseguridad)*

La transición del análisis de vulnerabilidades manual hacia sistemas automatizados impulsados por Inteligencia Artificial (IA) representa uno de los debates más activos en la ciberseguridad ofensiva actual. La asimetría es evidente: las redes empresariales mutan a diario (microservicios, CI/CD), mientras que las auditorías manuales tradicionales (pentesting) ofrecen solo una "fotografía" estática (*Point-in-Time*) del riesgo corporativo.

Para mi Trabajo Fin de Máster (TFM), me propuse abordar este problema. El objetivo no era crear un simple chatbot que sugiriera comandos, sino diseñar, desarrollar y validar un framework modular multiagente basado en IA capaz de ejecutar pruebas de intrusión de forma semiautomática. En este artículo, detallo las decisiones arquitectónicas, los desafíos algorítmicos y las soluciones implementadas para llevar este sistema de la teoría a un entorno de laboratorio real.

---

## 1. El Problema del Estado del Arte: Por qué la IA falla en el Pentesting

Delegar el razonamiento táctico a un Modelo de Lenguaje de Gran Escala (LLM) presenta deficiencias estructurales graves que la industria aún intenta resolver. Durante mi investigación, identifiqué tres barreras fundamentales en los sistemas 100% autónomos:

### Amnesia Operativa y el efecto "Lost in the Middle"

Forzar a un LLM a procesar volcados de red crudos (como las salidas completas de Nmap o Nessus) satura rápidamente su ventana de contexto. El modelo comienza a "olvidar" puertos o credenciales descubiertas en etapas tempranas.

### Alucinaciones Lógicas

Los motores probabilísticos tienden a inventar exploits inexistentes o intentar ejecutar módulos de 64 bits en arquitecturas de 32 bits, lo que provoca el colapso de la cadena de ataque.

### Riesgos de OpSec (Denegación de Servicio accidental)

Un agente sin supervisión puede lanzar ataques masivos tan rápido que bloquee los servidores de la empresa o viole las reglas de enfrentamiento (RoE).

Para mitigar estos problemas, mi TFM propone una disociación de planos: separar el plano de razonamiento semántico (el LLM) del plano operativo de ejecución local (Nmap, Metasploit, etc.).

---

## 2. Arquitectura Modular: El Enjambre de Agentes

El núcleo del sistema abandona el enfoque de "agente monolítico" en favor de una **Arquitectura Multiagente**. Un Orquestador Central dirige a un equipo de agentes especializados, alineando su comportamiento con la metodología tradicional PTES (*Penetration Testing Execution Standard*):

* **Agente de Reconocimiento y Escaneo:** Ejecuta de forma determinista escaneos pasivos y activos, aislando el ruido de la red.

* **Agente de Autenticación:** Evalúa debilidades en protocolos de identidad (Kerberos, SMB) orquestando herramientas como Hydra o Hashcat.

* **Agente de Explotación:** Mapea vulnerabilidades (CVEs) e interactúa mediante APIs locales con el framework Metasploit.

* **Agente de Reporte:** Consolida las evidencias de forma autónoma.

---

## 3. Memoria Persistente: PostgreSQL y pgvector (State-Driven RAG)

El mayor hito técnico del proyecto fue solucionar la pérdida de contexto. En lugar de inyectar los logs de red directamente en el prompt de la IA, diseñé una arquitectura de memoria semántica basada en PostgreSQL con la extensión pgvector.

### ¿Cómo funciona?

Cuando el Agente de Escaneo descubre un puerto (por ejemplo, el puerto 53 DNS con ISC BIND 9.4.2), el sistema aplica expresiones regulares para parsear la salida de Nmap, la convierte a un objeto JSON estructurado y genera embeddings vectoriales para guardarlo en la base de datos.

Además, el sistema sincroniza asíncronamente las bases de datos de vulnerabilidades globales (NVD/CVE) y Exploit-DB. Así, cuando el Orquestador necesita saber cómo atacar, no lee un historial infinito; ejecuta un mecanismo de Generación Aumentada por Recuperación (RAG), consultando matemáticamente la base de datos vectorial para inyectar solo el contexto técnico necesario. Esto redujo el consumo de tokens drásticamente y erradicó la "amnesia operativa".

---

## 4. El "Guardarraíl" de Verificación Física

Para evitar que la IA alucinara comandos destructivos, desarrollé lo que denomino un **Guardarraíl de Verificación Física**.

Antes de que el Agente de Explotación interactúe con el demonio de Metasploit (`msfrpcd`), el framework extrae la ruta del exploit propuesta por el LLM. Luego, ejecuta una validación determinista a nivel de sistema operativo (`grep` en el directorio físico `/usr/share/metasploit-framework/modules/`). Si la IA inventó el módulo, el sistema bloquea la ejecución y retroalimenta al modelo (mediante un *Self-Reflection Loop*) forzándolo a corregir el error.

---

## 5. El Núcleo Operativo: Man-in-the-Loop (MitL)

En contraposición a los sistemas 100% autónomos, demostré empíricamente que la seguridad operativa requiere **Autonomía Progresiva**.

Para tareas de alta densidad informativa (reconocimiento, mapeo topológico, cruce de CVEs y reportes), el sistema es totalmente autónomo. Sin embargo, en el momento exacto de la explotación táctica, la ejecución se detiene en un **Gateway de Intervención Humana**. El sistema despliega un Sandbox Interactivo donde el operador humano (el auditor) revisa el script compilado.

Solo tras la aprobación del auditor, el ataque se lanza en segundo plano, confirmando matemáticamente el éxito mediante el recuento de sesiones inversas (Meterpreter) activas, garantizando velocidad de ejecución con control humano total.

---

## 6. Post-Explotación: El Bucle ReAct y Conciencia Situacional

El punto culminante de la evaluación empírica ocurrió en la Fase 6. Tras vulnerar con éxito un servidor de laboratorio (Linux/Windows) mediante un exploit en SMB, el sistema entró en un bucle autónomo **ReAct (Reasoning and Acting)**.

El sistema cargó dinámicamente "habilidades" (*skills*) y el LLM evaluó su entorno. De forma autónoma:

* Analizó los privilegios actuales (`uid=0`).

* Volcó los hashes locales leyendo el archivo `/etc/shadow`.

* Consultó la tabla de enrutamiento y caché ARP para evaluar la presencia de redes **Dual Homed** y calcular rutas óptimas de **Pivoting (movimiento lateral)**.

Finalmente, el Agente de Reporte limpió automáticamente las secuencias de escape ANSI de los logs capturados y utilizó Jinja2 y WeasyPrint para renderizar un documento técnico en PDF listo para ser entregado a gerencia.

---

## Conclusión

El desarrollo de este TFM demuestra que la integración de la IA en la ciberseguridad ofensiva no debe orientarse a reemplazar al auditor humano, sino a liberarlo de la saturación de datos y telemetría cruda. Una arquitectura híbrida, donde enjambres de agentes gestionan la base de conocimiento mediante memorias vectoriales y el analista humano retiene el control táctico (MitL), representa el equilibrio óptimo entre escalabilidad técnica, precisión algorítmica y seguridad operativa empresarial.
