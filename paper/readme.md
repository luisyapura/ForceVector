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

---

# 10. Resultados Esperados

- Reducción de tiempo
- Mejora en detección
- Mayor consistencia
- Reducción de errores por alucinación

---

# 11. Conclusiones

El pentesting basado en IA es viable y seguro únicamente si se desacopla el razonamiento de la ejecución.

- Se controla el comportamiento del modelo
- Se valida la información generada
- Se combina con herramientas reales

---

# 12. Trabajo Futuro

- Multi-agente colaborativo
- Integración con SIEM
- Aprendizaje continuo
- Automatización avanzada de explotación

---

# 13. Sección Académica Formal (Estado del Arte, Motivación, Hipótesis y Tesis)

## 13.1 Estado del arte

El pentesting automatizado ha evolucionado significativamente en las últimas décadas, pasando de herramientas manuales a frameworks integrados como:

- Escáneres de red (Nmap)
- Frameworks de explotación (Metasploit)
- Herramientas de enumeración (BloodHound, CrackMapExec)

Sin embargo, estos sistemas presentan limitaciones claras:

- Dependencia de firmas o heurísticas predefinidas
- Falta de razonamiento contextual
- Incapacidad de adaptación dinámica

En paralelo, los modelos de lenguaje (LLMs) han demostrado capacidades avanzadas en:

- Comprensión de lenguaje técnico
- Generación de estrategias
- Razonamiento aproximado

Recientemente, han surgido enfoques de **agentes autónomos**, donde los LLM:

- Planifican acciones
- Interactúan con herramientas
- Iteran sobre resultados

No obstante, estos sistemas presentan un problema crítico:

> La alucinación, que limita su uso en entornos donde la precisión es esencial, como la ciberseguridad.

---

## 13.2 Motivación (formal)

La creciente complejidad de las infraestructuras empresariales exige soluciones que:

- Sean escalables
- Reduzcan la dependencia del experto humano
- Mantengan precisión operativa

Si bien los LLM ofrecen capacidades de razonamiento, su falta de fiabilidad limita su adopción directa.

Por tanto, surge la necesidad de:

> Diseñar sistemas híbridos que combinen razonamiento basado en IA con mecanismos de validación estrictos.

---

## 13.3 Hipótesis (formal)

### Hipótesis principal

Un sistema de pentesting basado en agentes de IA, complementado con mecanismos de control de alucinaciones y validación externa, puede mejorar tanto la eficiencia como la fiabilidad frente a enfoques tradicionales.

---

### Hipótesis secundarias

- La integración de LLM con herramientas reales permite superar limitaciones de los escáneres tradicionales.
- La validación estructurada reduce significativamente errores derivados de alucinaciones.
- El uso de modelos de estado mejora la coherencia del sistema.
- La supervisión humana (MitL) incrementa la seguridad operativa.

---

## 13.4 Tesis

> Es posible diseñar un sistema de pentesting basado en agentes de IA que no solo automatice tareas, sino que tome decisiones informadas y verificadas, aproximándose al comportamiento de un pentester humano, siempre que se incorporen mecanismos robustos de control de alucinaciones y validación.

---

# 14. Frases clave

- “Automatizar decisiones, no herramientas”
- “El LLM es un generador de hipótesis, no una fuente de verdad”
- “La IA sin validación no es fiable en ciberseguridad”

---

# 15. Repositorio y Demo

- Código
- Scripts
- Video

---

# 16. Bibliografía (placeholder)

- OWASP
- MITRE ATT&CK
- Papers LLM Agents
- Estudios sobre hallucination

---
