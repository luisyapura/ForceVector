# Marco CTEM

Estructura Detallada del Marco CTEMEl ciclo de CTEM se divide en cinco etapas interconectadas que deben ejecutarse de manera cíclica y no lineal:

- **Scoping (Definición del Alcance):** A diferencia del inventario tradicional de activos, aquí se define el "radio de explosión" crítico para el negocio. Se identifican los activos externos, nubes, aplicaciones SaaS y procesos cuya interrupción sería catastrófica.

- **Discovery (Descubrimiento): ** Se identifican no solo vulnerabilidades (CVEs), sino también configuraciones erróneas, identidades expuestas y activos "en la sombra" (Shadow IT). El objetivo es mapear la superficie de ataque completa, incluyendo la cadena de suministro.

- **Prioritization (Priorización):** Se aleja del puntaje CVSS estándar. CTEM evalúa la explotabilidad real y la importancia del activo para el negocio. Un activo con 100 vulnerabilidades teóricas puede ser menos prioritario que uno con una sola vulnerabilidad que sea activamente explotada por atacantes.

- **Validation (Validación):** Aquí es donde se confirma si una exposición es realmente explotable. Se utilizan técnicas de simulación de ataques para verificar si los controles de seguridad actuales (como firewalls o EDR) son efectivos contra esa amenaza específica.

- **Mobilization (Movilización):** Se enfoca en la remediación operativa. En lugar de enviar reportes interminables a TI, se definen flujos de trabajo claros para mitigar el riesgo, lo que puede incluir cambios de configuración o controles compensatorios si el parche no es posible.

## Postura frente al Pentesting Tradicional
Gartner sostiene que el pentesting tradicional (basado en proyectos anuales o semestrales) tiene problemas críticos en el panorama actual:

- Obsolescencia Inmediata: Un pentest es una "fotografía" en el tiempo. Minutos después de terminar la prueba, un cambio en la configuración de la nube o una nueva vulnerabilidad de día cero pueden invalidar los resultados.
- Falta de Escala: Las pruebas manuales son costosas y lentas, lo que impide cubrir la creciente infraestructura híbrida y dinámica de las empresas modernas.
- Visión Siloada: El pentesting a menudo se enfoca en sistemas aislados, perdiendo de vista los vectores de ataque que atraviesan diferentes capas (desde el correo hasta la infraestructura de red).

## Problemas Actuales que CTEM Intenta Resolver
- Fatiga por Vulnerabilidades: Con más de 25,000 nuevos CVEs al año, es imposible parchearlo todo. CTEM reduce el ruido enfocándose en el riesgo real.
- Exposiciones más allá del Software: Los ataques modernos suelen explotar errores humanos, identidades mal gestionadas o servicios en la nube mal configurados, elementos que el escaneo de vulnerabilidades tradicional suele omitir.
- Velocidad del Atacante: Mientras las empresas operan con ciclos de auditoría trimestrales, los atacantes profesionalizados actúan en horas.

[Fuente](https://ctem.org/docs/what-is-continuous-threat-exposure-management)
