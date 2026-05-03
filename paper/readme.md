# ⚡ TFM – Diseño de un Sistema de Pentesting Basado en IA
---

## Autor
Luis Yapura  

## Máster en Ciberseguridad  
Módulo 11 – Trabajo Fin de Máster  

---

# 1. Introducción y Contexto 
## Análisis Estructural de las Limitaciones del Pentesting Tradicional en Entornos Empresariales

El estado actual de la ciberseguridad ofensiva empresarial presenta una divergencia crítica entre la velocidad de evolución de las infraestructuras tecnológicas y las metodologías de validación de seguridad. Aunque el penetration testing (pentesting) sigue siendo un control de cumplimiento y seguridad fundamental, su arquitectura operativa tradicional, basada en el esfuerzo manual, presenta fallos sistémicos.

A continuación, se desarrolla un análisis detallado de las tres limitaciones estructurales mencionadas, fundamentado en literatura técnica y reportes de la industria, con el rigor requerido para un marco de investigación de posgrado.

---

## 1.1.1. Dependencia de Capital Humano Altamente Cualificado (El Cuello de Botella Cognitivo)

El núcleo del pentesting tradicional es intrínsecamente dependiente del conocimiento heurístico del operador. A diferencia de un análisis de vulnerabilidades automatizado (vulnerability scanning), que es determinista y se basa en firmas, la explotación y el movimiento lateral requieren pensamiento lateral, encadenamiento de vulnerabilidades de severidad media y adaptación a controles evasivos.

- **La Brecha de Talento y la Carga Cognitiva:** Según el Cybersecurity Workforce Study de (ISC)² (2023), existe una brecha global de aproximadamente 4 millones de profesionales en ciberseguridad. En el dominio ofensivo, esta escasez es más aguda. La dependencia operativa recae en una élite técnica que está sujeta a fatiga cognitiva.

- **Heurística vs. Sistematización:** El éxito de un red team o de un pentesting avanzado depende de la "intuición" del atacante (por ejemplo, inferir la estructura de un Directorio Activo o predecir la reutilización de credenciales). Esta dependencia heurística significa que el proceso no puede ser parametrizado fácilmente a través de scripts estáticos. Como señalan investigaciones en automatización de la seguridad (ej. Automated Penetration Testing: A Systematic Review, IEEE), la toma de decisiones humana frente a un sistema complejo durante un ataque no estructurado es difícil de codificar mediante árboles de decisión convencionales.

---

## 1.1.2. Escalabilidad Limitada (Asimetría Temporal y Espacial)

La relación entre el tiempo requerido para auditar un sistema y el tamaño del sistema en sí mismo no es lineal; es exponencial. Esto genera una asimetría técnica entre la capacidad defensiva/despliegue y la capacidad ofensiva.

- **Superficies de Ataque Expansivas:** La adopción de arquitecturas basadas en microservicios, Infraestructura como Código (IaC), entornos híbridos y despliegues CI/CD (Integración y Despliegue Continuos) provoca que la topología de la red empresarial mute diariamente.

- **La Falacia del Point-in-Time:** Un pentesting manual es una "fotografía" del estado de seguridad en un momento específico. Gartner, en su formulación del marco de Continuous Threat Exposure Management (CTEM), advierte que las auditorías manuales anuales o semestrales son insuficientes. Un auditor humano requiere semanas para mapear, enumerar y explotar vectores en una red corporativa; para cuando se entrega el reporte final, la infraestructura subyacente ya ha cambiado, invalidando parcial o totalmente las conclusiones sobre la postura de riesgo actual.

---

## 1.1.3. Consistencia y Reproducibilidad (Varianza Metodológica)

En la investigación científica y en la auditoría técnica, la reproducibilidad es un pilar fundamental. Si dos auditores diferentes evalúan el mismo entorno con las mismas herramientas, deberían obtener resultados casi idénticos. En el pentesting manual, esto rara vez ocurre.

- **Subjetividad en la Ejecución:** Aunque existen marcos metodológicos estandarizados como PTES (Penetration Testing Execution Standard) o OSSTMM (Open Source Security Testing Methodology Manual), estos definen el "qué" se debe probar, pero dejan gran parte del "cómo" a discreción del operador. Un auditor especializado en aplicaciones web puede pasar por alto una vulnerabilidad de Active Directory (como un ataque Kerberoasting o un DCSync) simplemente debido a su sesgo de formación.

- **Evaluación y Contextualización del Riesgo:** La asignación de impacto a una vulnerabilidad varía significativamente entre operadores. Aunque métricas como CVSS (Common Vulnerability Scoring System) intentan objetivizar la gravedad técnica, el contexto de explotación en el pentesting manual depende del análisis humano. Esta varianza metodológica impide a las organizaciones establecer una línea base de seguridad (baseline) matemática y demostrable a lo largo del tiempo.

---

### Fuentes y Marcos de Referencia

Las referencias de estándares de la industria e investigación aplicada, para ello se eligieron los siguientes materiales:

- (ISC)² (2023). Cybersecurity Workforce Study. Documenta la escasez de talento y justifica la necesidad de automatización para suplir la falta de operadores humanos.

- Gartner (2022-presente). Implement a Continuous Threat Exposure Management (CTEM) Program. Define la obsolescencia de las pruebas point-in-time y la necesidad de una validación escalable y continua.

- The Penetration Testing Execution Standard (PTES). Documentación fundamental para criticar cómo los estándares actuales no resuelven la subjetividad de la fase de explotación.

- MITRE ATT&CK Framework. Útil para ilustrar cómo el comportamiento de un adversario requiere una matriz compleja de TTPs (Tácticas, Técnicas y Procedimientos) que, al ejecutarse manualmente, sufren de inconsistencia temporal.

- Literatura Académica (IEEE Xplore / ACM Digital Library): Búsquedas enfocadas en "Automated Penetration Testing with Reinforcement Learning" o "Autonomous Security Agents". Estos papers (frecuentes a partir de 2021) inician invariablemente sus introducciones citando la falta de escalabilidad y la dependencia humana del pentesting tradicional como justificación para el uso de Inteligencia Artificial en el modelo ofensivo.
---

## 1.2 Declaración del Problema

Existe una brecha operativa y semántica entre:

- La automatización de bajo nivel: Herramientas de escaneo que operan mediante firmas o enumeración de puertos.

- El razonamiento estratégico: Procesos de toma de decisiones de alto nivel que requieren contexto de negocio y correlación de vectores de ataque.

El uso directo de Modelos de Lenguaje (LLM) introduce el riesgo de alucinaciones. En pentesting, una alucinación (como la inferencia de un comando sintácticamente válido pero semánticamente destructivo o inexistente) compromete la integridad del entorno y la fiabilidad de la auditoría.

---

## 1.3 Oportunidad de Investigación

El uso de agentes de IA permite el razonamiento contextual, la planificación dinámica y la adaptación ante respuestas imprevistas del entorno, siempre y cuando se implemente un mecanismo de control estricto sobre las acciones.

---

# 2. Motivación Central y Limitaciones

## 2.1 Limitaciones del Pentesting Tradicional

- Falta de razonamiento dinámico: Los escáneres estáticos (como Nmap o Nessus) no pueden modificar su estrategia de enumeración basándose en el comportamiento de servicios no estándar.

- reproducibilidad: La captura del estado del entorno de red no es persistente ni estructurada.

---

## 2.2 Limitaciones de los Modelos de Lenguaje

- Alucinación de herramientas o parámetros: El modelo puede inventar parámetros de consola o exploits inexistentes.

- Sobreconfianza (Comprensión errónea): El modelo puede asumir que un servicio es vulnerable sin realizar una verificación empírica.

---

## 2.3 Motivación Central

Automatizar el proceso de toma de decisiones de forma fiable mediante la integración de agentes de IA, utilizando herramientas reales validadas de forma determinista antes de la ejecución.

---

# 3. Objetivo General

Diseñar e implementar un sistema de pentesting basado en agentes de IA, capaz de operar en modo Human-in-the-Loop (MitL) o autónomo, manteniendo el control sobre la generación de alucinaciones y el impacto sobre la red objetivo.

---

# 4. Objetivos Específicos

- O1: Desarrollar un módulo de reconocimiento de red tolerante a fallos.

- O2: Analizar protocolos y servicios mediante validación cruzada.

- O3: Evaluar mecanismos de autenticación evitando la saturación de servicios (fuerza bruta controlada).

- O4: Optimizar la fase de movimiento lateral mediante el modelado de grafos.

- O5: Implementar un mecanismo de control de alucinaciones basado en restricción de herramientas (tool grounding).

---

# 5. Marco de Hipótesis

## 5.1 Hipótesis Principal

Un sistema basado en agentes de IA, complementado con validación externa y restricción de herramientas, mejora la eficiencia operativa y la fiabilidad frente a los enfoques de escaneo tradicional.

---

## 5.2 Hipótesis Secundarias

- H1: El razonamiento semántico supera la automatización pura en el análisis de topologías de red complejas.

- H2: El modelo Man-in-the-Loop (MitL) reduce el riesgo de daño operativo sin afectar la velocidad de auditoría.

- H3: El modelado estructurado reduce las alucinaciones del modelo en la toma de decisiones.

- H4: La validación de acciones previene la ejecución de comandos inválidos o perjudiciales.

> **Nota:** INvestigar costo de Api y Tokens en la ejecucuion de tareas e implementacion local
---

# 6. Modelo de Estado y Pipeline de Ejecución

## 6.1 Definición Formal del Estado

El entorno de red se modela como un grafo de ataque G=(V,E), donde los nodos V representan activos o servicios y las aristas E representan relaciones de acceso o vulnerabilidad.

---

## 6.2 Pipeline de Ejecución

El ciclo de procesamiento del agente se formaliza en cinco fases secuenciales:

- Observación: Recopilación de datos del entorno mediante escaneo.

- Interpretación: El LLM genera una hipótesis de acción d.

- Validación Formal: Se verifica la existencia de la herramienta y la validez de los argumentos contra un esquema estricto.

- Ejecución Condicionada: Si la acción es aprobada por el validador, se ejecuta en el entorno real y se registra su salida.

- Persistencia: Actualización del grafo de ataque en la base de datos de grafos.

El principio fundamental de esta arquitectura es que el LLM actúa únicamente como generador de hipótesis, no como fuente de verdad.

---

# 7. Gestión de Alucinaciones y Diseño Defensivo

## 7.1 Estrategias de Mitigación

- Tool-grounding: El LLM no genera comandos libres, sino que selecciona funciones de una API o herramientas definidas.

- Restricción de prompts: Uso de plantillas que fuerzan justificación técnica.

- Validación externa: Capa determinista que analiza comandos antes de ejecución.

> **Nota:** Si se llega con el tiempo implementar sandboxig para evitar que la IA borre datos o comprometa el sistema como es de publico conocimiento

---

# 8. Metodología de Investigación

## 8.1 Entorno de Pruebas

Se implementará un entorno de red virtualizado que incluye:

- Un controlador de dominio Active Directory.

- Segmentación de red por VLANs.

- Servicios expuestos para auditoría.

---

## 8.2 Herramientas de Integración

- Nmap  
- CrackMapExec  
- BloodHound  

> **Nota:** Agregar tools a medida que se vayan creando los agentes y defina la arquitectura.

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
