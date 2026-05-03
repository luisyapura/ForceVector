# ⚡ TFM – Diseño de un Sistema de Pentesting Basado en IA

## Autor
Luis Yapura  

## Máster en Ciberseguridad  
Módulo 11 – Trabajo Fin de Máster  

---

# 1. Introducción

## 1.1 Contexto

El pentesting en entornos empresariales es una actividad crítica dentro de la ciberseguridad ofensiva. Sin embargo, presenta limitaciones importantes:

- Alta dependencia de expertos cualificados.
- Procesos manuales y poco escalables.
- Dificultad para mantener consistencia en auditorías complejas.

Las herramientas actuales automatizan tareas, pero no la toma de decisiones.

---

## 1.2 Problema

Existe una brecha entre:

- Automatización técnica (herramientas)
- Razonamiento estratégico (pentester humano)

Además, los LLM introducen el problema de alucinación.

---

## 1.3 Oportunidad

Los sistemas basados en agentes de IA permiten:

- Razonamiento contextual
- Planificación
- Adaptación dinámica

---

# 2. Motivación

## 2.1 Limitaciones del pentesting tradicional

- No escalable
- Dependiente del experto
- Baja reproducibilidad

---

## 2.2 Limitaciones de los LLM

- Alucinaciones
- Inferencias incorrectas
- Sobreconfianza

---

## 2.3 Motivación central

> Automatizar decisiones de pentesting de forma fiable mediante IA + validación.

---

# 3. Objetivo General

Diseñar un sistema de pentesting basado en agentes de IA capaz de operar de forma autónoma o semi-autónoma.

---

# 4. Objetivos Específicos

- Reconocimiento de red
- Análisis de protocolos
- Evaluación de autenticación
- Movimiento lateral
- Control de alucinaciones

---

# 5. Hipótesis

## 5.1 Hipótesis principal

> Un sistema basado en IA con control de alucinaciones mejora eficiencia y fiabilidad.

---

## 5.2 Hipótesis secundarias

- H1: El razonamiento supera la automatización pura
- H2: MitL es más robusto que autonomía total
- H3: El modelado estructurado mejora decisiones
- H4: Mejora del movimiento lateral
- H5: Mejora del análisis de protocolos
- H6: Reducción de errores mediante validación

---

### 6. Modelo de Estado
- Base de datos / grafo
- Persistencia del entorno

---

## 6.3 Pipeline

1. Observación (datos reales)
2. Interpretación (LLM)
3. Validación
4. Ejecución
5. Persistencia

---

## 6.4 Principio clave

> El LLM no es una fuente de verdad, sino un generador de hipótesis.

---

# 7. Gestión de Alucinaciones

## 7.1 Estrategias

- Tool-grounding
- Validación externa
- Restricción de prompts
- Control de acciones
- Supervisión humana

---

## 7.2 Diseño defensivo

- No ejecutar directamente decisiones del LLM
- Requerir confirmación o validación
- Uso de contexto estructurado

---

# 8. Metodología

## 8.1 Entorno de pruebas

- Red empresarial simulada
- Active Directory
- Segmentación de red

---

## 8.2 Implementación

- Agente basado en LLM local
- Integración con herramientas reales

---

## 8.3 Comparativa

- Pentesting tradicional
- Sistema propuesto

---

# 9. Métricas de Evaluación

- Tiempo de ejecución
- Cobertura de activos
- Vulnerabilidades detectadas
- Falsos positivos
- Falsos negativos
- Acciones inválidas del LLM

---

# 10. Resultados Esperados

- Reducción de tiempo
- Mejora en detección
- Mayor consistencia
- Reducción de errores por alucinación

---

# 11. Conclusiones

El uso de IA en pentesting es viable si:

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
- Agentes de prueba que por el momento trabajan de forma individual
---

# 16. Bibliografía (placeholder)

- OWASP
- MITRE ATT&CK
- Papers LLM Agents
- Estudios sobre alucinación

---
