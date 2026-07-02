# Guía de Configuración de Red y Seguridad para PostgreSQL 18 (Windows ↔ Kali)

## Objetivo

Para el entorno del **TFM ForceVector**, la arquitectura requiere que **PostgreSQL 18**, alojado en **Windows**, acepte conexiones externas provenientes del agente orquestador ejecutado en **Kali Linux**.

Por defecto, PostgreSQL adopta una postura de **máxima seguridad**, escuchando únicamente en `localhost`. Como consecuencia, al intentar conectar desde una máquina virtual (por ejemplo, mediante VMware), suele aparecer el siguiente error:

```text
FATAL: no pg_hba.conf entry for host "<IP>", user "<usuario>", database "<base>", SSL encryption
```

Esta guía configura PostgreSQL siguiendo el principio de **Mínimo Privilegio (Least Privilege)** y una estrategia **Zero Trust interna**, evitando exponer el servicio a toda la red.

---

# Arquitectura

```text
┌────────────────────────────────────────────────────────────┐
│                    Host Windows 11                         │
│                                                            │
│ PostgreSQL 18                         Ollama              │
│ Puerto 5432                           Puerto 11434        │
│                                                            │
│ IP VMware (VMnet8): 192.168.159.1                         │
└────────────────────────────────────────────────────────────┘
                     ▲
                     │
          Red VMware NAT (VMnet8)
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                      Kali Linux                            │
│                                                            │
│ ForceVector                                                │
│ Orquestador (main.py)                                      │
│                                                            │
│ IP: 192.168.159.128                                        │
└────────────────────────────────────────────────────────────┘
```

---

# Paso 1 — Identificar las direcciones IP

Antes de modificar la configuración, identifica las direcciones IP del entorno VMware.

## En Kali Linux

Ejecuta:

```bash
ip a
```

Anota la dirección IP de la máquina virtual.

Ejemplo:

```text
192.168.159.128
```

---

## En Windows

Abre una consola (`cmd`) y ejecuta:

```cmd
ipconfig
```

Localiza el adaptador de VMware (normalmente **VMnet8**) y anota la IP.

Ejemplo:

```text
192.168.159.1
```

Ambas direcciones deben pertenecer a la misma subred.

---

# Paso 2 — Configurar la escucha de PostgreSQL

Ubicación habitual del directorio de datos:

```text
C:\Program Files\PostgreSQL\18\data\
```

Abre el archivo:

```text
postgresql.conf
```

Busca la directiva:

```ini
#listen_addresses = 'localhost'
```

y reemplázala por:

```ini
listen_addresses = 'localhost,192.168.159.1'
```

> Sustituye `192.168.159.1` por la IP de Windows correspondiente a tu red VMware.

Guardar los cambios.

---

# Paso 3 — Configurar `pg_hba.conf`

Abre el archivo:

```text
pg_hba.conf
```

Añade al final las siguientes reglas:

```ini
# TYPE  DATABASE         USER        ADDRESS                 METHOD

host    all              postgres    127.0.0.1/32            scram-sha-256
host    forcevector_db   postgres    192.168.159.128/32      scram-sha-256
host    postgres         postgres    192.168.159.128/32      scram-sha-256
```

## Explicación

La máscara:

```text
/32
```

indica que **únicamente esa dirección IP** podrá conectarse.

No se autoriza toda la red, sino exclusivamente la máquina Kali utilizada por ForceVector.

La autenticación utilizada es:

```text
scram-sha-256
```

que constituye el método recomendado por PostgreSQL 18.

---

# Paso 4 — Configurar el Firewall de Windows

Aunque PostgreSQL esté correctamente configurado, Windows Defender bloqueará por defecto las conexiones entrantes.

Debe crearse una excepción únicamente para la IP de Kali.

## Abrir

```
Firewall de Windows Defender con seguridad avanzada
```

Ir a:

```
Reglas de entrada
```

Seleccionar:

```
Nueva regla...
```

---

## Configuración

### Tipo

```
Puerto
```

### Protocolo

```
TCP
```

### Puertos

```
5432
11434
```

Donde:

| Puerto | Servicio |
|---------|----------|
| 5432 | PostgreSQL |
| 11434 | API de Ollama |

---

### Acción

```
Permitir la conexión
```

---

### Perfil

Seleccionar los perfiles correspondientes a la red VMware.

Generalmente:

- Dominio
- Privado

---

### Nombre

```
ForceVector - PostgreSQL y Ollama desde Kali
```

---

## Restricción de IP (muy importante)

Editar la regla recién creada.

Ir a:

```
Ámbito
```

En:

```
Dirección IP remota
```

Seleccionar:

```
Estas direcciones IP
```

Añadir únicamente:

```text
192.168.159.128
```

De esta forma únicamente Kali podrá acceder a PostgreSQL y Ollama.

---

# Paso 5 — Reiniciar PostgreSQL

Abrir:

```
services.msc
```

Buscar:

```
postgresql-x64-18
```

Seleccionar:

```
Reiniciar
```

Esto obliga al servicio a recargar:

- `postgresql.conf`
- `pg_hba.conf`

---

# Paso 6 — Verificar la conectividad

Desde Kali ejecutar:

```bash
psql -h 192.168.159.1 -U postgres -d postgres
```

Si aparece la solicitud de contraseña:

```text
Password for user postgres:
```

la configuración es correcta.

A partir de este momento, el orquestador de **ForceVector** podrá conectarse automáticamente al servidor PostgreSQL para crear e inicializar la infraestructura de bases de datos.

---

# Resumen de configuración

| Elemento | Configuración |
|-----------|---------------|
| PostgreSQL | Escucha únicamente en localhost + IP VMware |
| pg_hba.conf | Acceso exclusivo desde la IP de Kali (/32) |
| Firewall | Puerto 5432 y 11434 abiertos únicamente para Kali |
| Autenticación | SCRAM-SHA-256 |
| Arquitectura | Zero Trust interno |
| Principio aplicado | Least Privilege |

---

# Consideraciones de seguridad

Esta configuración evita errores comunes como:

- `no pg_hba.conf entry for host`
- `connection refused`
- bloqueo por Windows Defender

Además, reduce significativamente la superficie de ataque al:

- No utilizar `listen_addresses='*'`.
- No permitir acceso a toda la subred (`/24`).
- Restringir el firewall a una única dirección IP.
- Utilizar autenticación `SCRAM-SHA-256`.
- Mantener el principio de **Zero Trust** incluso dentro de la red virtual.

Esta estrategia constituye una configuración adecuada para un entorno de desarrollo e investigación como **ForceVector**, proporcionando conectividad entre Windows y Kali Linux sin exponer innecesariamente los servicios críticos de PostgreSQL y Ollama.
