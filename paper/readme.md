# ⚡ TFM – Diseño de un Sistema de Pentesting Basado en IA

---

# 1. Introducción y Contexto Problemático

## 1.1 Contexto de la Ciberseguridad Ofensiva

El pentesting empresarial es una actividad crítica para la validación de la postura de seguridad. Sin embargo, su ejecución adolece de limitaciones estructurales:

- Dependencia de capital humano altamente cualificado: El proceso descansa sobre la heurística y la intuición del pentester.

- Escalabilidad limitada: La ejecución de pruebas sobre infraestructuras de red complejas requiere un tiempo de procesamiento humano no lineal.

- Consistencia y reproducibilidad: Las auditorías manuales varían en función del auditor, dificultando la estandarización de resultados.

> **Nota:** Podrías reforzar este punto incluyendo métricas reales (ej. tiempo medio de auditoría o variabilidad entre analistas) para aumentar el peso empírico.

---

## 1.2 Declaración del Problema

Existe una brecha operativa y semántica entre:

- La automatización de bajo nivel: Herramientas de escaneo que operan mediante firmas o enumeración de puertos.

- El razonamiento estratégico: Procesos de toma de decisiones de alto nivel que requieren contexto de negocio y correlación de vectores de ataque.

El uso directo de Modelos de Lenguaje (LLM) introduce el riesgo de alucinaciones. En pentesting, una alucinación (como la inferencia de un comando sintácticamente válido pero semánticamente destructivo o inexistente) compromete la integridad del entorno y la fiabilidad de la auditoría.

> **Nota:** Aquí podrías añadir un ejemplo real de comando mal generado para reforzar la comprensión del tribunal.

---

## 1.3 Oportunidad de Investigación

El uso de agentes de IA permite el razonamiento contextual, la planificación dinámica y la adaptación ante respuestas imprevistas del entorno, siempre y cuando se implemente un mecanismo de control estricto sobre las acciones.

> **Nota:** Puedes mencionar explícitamente el paradigma “LLM as planner + tools executor” para alinearlo con literatura reciente.

---

# 2. Motivación Central y Limitaciones

## 2.1 Limitaciones del Pentesting Tradicional

- Falta de razonamiento dinámico: Los escáneres estáticos (como Nmap o Nessus) no pueden modificar su estrategia de enumeración basándose en el comportamiento de servicios no estándar.

- reproducibilidad: La captura del estado del entorno de red no es persistente ni estructurada.

> **Nota:** Corrige capitalización de “Reproducibilidad” y considera añadir “trazabilidad” como limitación adicional.

---

## 2.2 Limitaciones de los Modelos de Lenguaje

- Alucinación de herramientas o parámetros: El modelo puede inventar parámetros de consola o exploits inexistentes.

- Sobreconfianza (Comprensión errónea): El modelo puede asumir que un servicio es vulnerable sin realizar una verificación empírica.

> **Nota:** Podrías añadir el concepto de “lack of grounding” para mayor precisión académica.

---

## 2.3 Motivación Central

Automatizar el proceso de toma de decisiones de forma fiable mediante la integración de agentes de IA, utilizando herramientas reales validadas de forma determinista antes de la ejecución.

> **Nota:** Muy buen punto. Puedes reforzarlo indicando que el sistema desacopla “decision-making” y “execution”.

---

# 3. Objetivo General

Diseñar e implementar un sistema de pentesting basado en agentes de IA, capaz de operar en modo Human-in-the-Loop (MitL) o autónomo, manteniendo el control sobre la generación de alucinaciones y el impacto sobre la red objetivo.

> **Nota:** Considera añadir “en entornos controlados” para evitar interpretaciones éticas o legales.

---

# 4. Objetivos Específicos

- O1: Desarrollar un módulo de reconocimiento de red tolerante a fallos.

- O2: Analizar protocolos y servicios mediante validación cruzada.

- O3: Evaluar mecanismos de autenticación evitando la saturación de servicios (fuerza bruta controlada).

- O4: Optimizar la fase de movimiento lateral mediante el modelado de grafos.

- O5: Implementar un mecanismo de control de alucinaciones basado en restricción de herramientas (tool grounding).

> **Nota:** Podrías añadir un O6 relacionado con métricas o evaluación experimental.

---

# 5. Marco de Hipótesis

## 5.1 Hipótesis Principal

Un sistema basado en agentes de IA, complementado con validación externa y restricción de herramientas, mejora la eficiencia operativa y la fiabilidad frente a los enfoques de escaneo tradicional.

> **Nota:** Puedes formalizarla matemáticamente como en la sección 13 para mayor coherencia.

---

## 5.2 Hipótesis Secundarias

- H1: El razonamiento semántico supera la automatización pura en el análisis de topologías de red complejas.

- H2: El modelo Man-in-the-Loop (MitL) reduce el riesgo de daño operativo sin afectar la velocidad de auditoría.

- H3: El modelado estructurado reduce las alucinaciones del modelo en la toma de decisiones.

- H4: La validación de acciones previene la ejecución de comandos inválidos o perjudiciales.

> **Nota:** Podrías añadir una hipótesis explícita sobre rendimiento computacional o coste.

---

# 6. Modelo de Estado y Pipeline de Ejecución

## 6.1 Definición Formal del Estado

El entorno de red se modela como un grafo de ataque G=(V,E), donde los nodos V representan activos o servicios y las aristas E representan relaciones de acceso o vulnerabilidad.

> **Nota:** Considera especificar tipo de grafo (dirigido, ponderado) para mayor precisión.

---

## 6.2 Pipeline de Ejecución

El ciclo de procesamiento del agente se formaliza en cinco fases secuenciales:

- Observación: Recopilación de datos del entorno mediante escaneo.

- Interpretación: El LLM genera una hipótesis de acción d.

- Validación Formal: Se verifica la existencia de la herramienta y la validez de los argumentos contra un esquema estricto.

- Ejecución Condicionada: Si la acción es aprobada por el validador, se ejecuta en el entorno real y se registra su salida.

- Persistencia: Actualización del grafo de ataque en la base de datos de grafos.

El principio fundamental de esta arquitectura es que el LLM actúa únicamente como generador de hipótesis, no como fuente de verdad.

> **Nota:** Excelente diseño. Puedes añadir logging estructurado para auditoría.

---

# 7. Gestión de Alucinaciones y Diseño Defensivo

## 7.1 Estrategias de Mitigación

- Tool-grounding: El LLM no genera comandos libres, sino que selecciona funciones de una API o herramientas definidas.

- Restricción de prompts: Uso de plantillas que fuerzan justificación técnica.

- Validación externa: Capa determinista que analiza comandos antes de ejecución.

> **Nota:** Podrías añadir “sandboxing” como capa adicional de seguridad.

---

# 8. Metodología de Investigación

## 8.1 Entorno de Pruebas

Se implementará un entorno de red virtualizado que incluye:

- Un controlador de dominio Active Directory.

- Segmentación de red por VLANs.

- Servicios expuestos para auditoría.

> **Nota:** Especificar herramientas de virtualización (ej. Proxmox, VMware) puede sumar puntos.

---

## 8.2 Herramientas de Integración

- Nmap  
- CrackMapExec  
- BloodHound  

> **Nota:** Considera añadir Wireshark o Responder para enriquecer escenarios.

---

# 9. Métricas de Evaluación

| Métrica | Definición | Dimensión |
|--------|----------|----------|
| Texec | Tiempo total de ejecución | Eficiencia |
| FPR | Falsos positivos | Fiabilidad |
| FNR | Falsos negativos | Cobertura |
| Ainv | Acciones inválidas rechazadas | Estabilidad |

> **Nota:** Podrías añadir “precision/recall” para formalidad académica.

---

# 10. Resultados Esperados

- Reducción del tiempo en un 25%.

- Eliminación de comandos destructivos no deseados.

- Consistencia en informes.

> **Nota:** Justifica el 25% con hipótesis o baseline.

---

# 11. Conclusiones

El pentesting basado en IA es viable y seguro únicamente si se desacopla el razonamiento de la ejecución.

> **Nota:** Muy buen cierre conceptual.

---

# 12. Trabajo Futuro

- Sistemas multi-agente  
- Integración con SIEM  
- Optimización hardware  

> **Nota:** Podrías añadir RL (reinforcement learning) como evolución.

---

# 13. Sección Académica Formal

## 13.1 Estado del Arte

Automatización → frameworks → LLM → problema de alucinación.

> **Nota:** Añadir citas reales es clave aquí.

---

## 13.2 Motivación Formal

Diseño de modelos híbridos IA + ejecución determinista.

> **Nota:** Correcto, bien alineado con literatura actual.

---

## 13.3 Hipótesis (Formalización)

H0: E[EficienciaHíbrido] > E[EficienciaTradicional]

> **Nota:** Muy buen toque matemático, poco común en TFMs.

---

## 13.4 Tesis Doctoral

Sistema MitL + control de alucinaciones ≈ comportamiento experto.

> **Nota:** Puedes eliminar “Doctoral” si no quieres sobredimensionar.

---

# 14. Frases Clave

- Automatizar decisiones  
- LLM ≠ fuente de verdad  
- IA sin validación = riesgo  

---

# 15. Repositorio y Demostración

- Código  
- Demo  

---

# 16. Bibliografía

- OWASP  
- MITRE ATT&CK  
- Papers LLM  

> **Nota:** Aquí debes añadir citas reales obligatoriamente.

---
