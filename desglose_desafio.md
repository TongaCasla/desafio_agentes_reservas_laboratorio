# Desglose Técnico del Desafío: Sistema de Reservas con Agentes

## 1. Resumen Ejecutivo y Objetivo

El objetivo de la consigna **no** es construir una plataforma masiva ni implementar un sistema multiagente complejo. El desafío evalúa la **disciplina de ingeniería de software asistida por IA**:
- Cómo se especifica el problema.
- Cómo se prepara, acota y controla al agente de programación.
- Cómo se verifica humana y automáticamente el resultado.
- Cómo se documenta la trazabilidad de las decisiones y delegaciones.

> **Regla de oro de la rúbrica**: Lo que se califica es la **evidencia concreta en el repositorio** (código, pruebas automáticas reproducibles, configuración del agente y registro de decisiones), no afirmaciones vacías en el README ni complejidades innecesarias.

---

## 2. Dominio y Reglas del Negocio (Core del Sistema)

Se requiere desarrollar un sistema local para la gestión de reservas de equipos de laboratorio.

### 2.1. Inventario Precargado (Inmutable)
El inventario viene predefinido y no requiere interfaz de administración (CRUD de inventario fuera de alcance):
| ID Unidad | Equipo |
|---|---|
| `MIC-01` | Microscopio digital |
| `MIC-02` | Microscopio digital |
| `OSC-01` | Osciloscopio |
| `MUL-01` | Multímetro |
| `FUE-01` | Fuente de alimentación |

### 2.2. Reglas de Validación y Reserva
1. **Creación**:
   - Unidad debe existir en el inventario.
   - Solicitante ficticio no vacío (rechazar strings vacíos o compuestos únicamente de espacios en blanco).
   - Fechas y horas válidas con restricción estricta: `inicio < fin`.
   - Identificador único por reserva.
2. **Disponibilidad y Concurrencia de Horarios**:
   - **Misma unidad**: Rechazar cualquier solapamiento con reservas activas.
   - **Límites consecutivos**: Permitidos (e.g. Reserva A: 10:00 a 11:00; Reserva B: 11:00 a 12:00 sobre la misma unidad es válida).
   - **Unidades distintas**: Pueden reservarse simultáneamente en el mismo horario (e.g. `MIC-01` y `MIC-02` de 10:00 a 11:00).
   - La consulta de disponibilidad debe regirse exactamente por estas mismas reglas.
3. **Cancelación**:
   - Debe conservar el identificador y todos los datos históricos (soft-delete o estado `CANCELLED`).
   - Debe liberar inmediatamente el intervalo de tiempo para nuevas reservas.
4. **Persistencia**:
   - Las reservas (activas y canceladas) deben persistir en almacenamiento local (archivo JSON, SQLite, etc.).
   - Al reiniciar la aplicación, el estado debe recuperarse íntegramente.

---

## 3. Límites Técnicos y Alcance

### Dentro de Alcance:
- Lenguaje a elección con dependencias estándar y reproducibles.
- Interfaz mínima: Consola (CLI) o API local (FastAPI, Flask, Express, etc.).
- Pruebas automatizadas (unitarias y de integración) reproducibles sin configuración externa.
- Documentar zona horaria, formatos de fecha (e.g. ISO 8601) y supuestos adoptados.

### Fuera de Alcance Explícito:
- Autenticación, roles y usuarios reales.
- Notificaciones (emails, WhatsApp, webhooks).
- Pagos o facturación.
- Integraciones externas o despliegue en la nube.
- Frontend gráfico complejo.
- Concurrencia distribuida y escalabilidad productiva.

> **Atención crítica**: La aplicación y sus pruebas deben ejecutarse y pasar **sin requerir la cuenta de modelo ni API keys del autor**. El evaluador no usará LLMs para probar la aplicación.

---

## 4. Requisitos de Entrega y Estructura del README

El repositorio debe organizarse alrededor de un `README.md` estructurado en **cuatro secciones obligatorias**:

1. **Especificación breve**:
   - Problema, alcance, requisitos verificables, reglas de negocio, supuestos y criterios de aceptación.
   - Evolución de la especificación recuperable en el historial de Git.
2. **Solución**:
   - Arquitectura, estructura de directorios, decisiones técnicas, dependencias y versiones.
   - Instrucciones de instalación, carga inicial, comandos de ejecución y de pruebas.
   - Detalle de dónde y cómo persisten los datos, advertencia de si un reinicio borra datos, pendientes y limitaciones.
3. **Preparación del agente**:
   - Entorno utilizado (harness), modelo exacto y justificación de elección.
   - Instrucciones suministradas (system prompt, reglas de proyecto saneadas) y contexto excluido.
   - Herramientas y permisos concedidos, adaptaciones específicas comprobables (e.g. prompt para turnos consecutivos o persistencia).
4. **Registro de decisiones y delegación (Los 3 Episodios Reales)**:
   - Registro de decisiones de diseño con alternativas y consecuencias.
   - **Exactamente 3 episodios reales de delegación**, documentando para cada uno:
     - `Objetivo y requisito` →
     - `Contexto suministrado y extracto de instrucción` →
     - `Acción o resultado generado por el agente` →
     - `Decisión humana (aceptar, corregir o rechazar, con fundamentación)` →
     - `Enlace verificable (archivo, commit o prueba)`.

---

## 5. Rúbrica de Calificación

| Dimensión | Ponderación | Foco de Evaluación |
|---|:---:|---|
| **Funcionamiento y pruebas** | **30%** | Reglas de negocio operativas, suite de pruebas automatizadas y persistencia comprobada tras reinicio. |
| **Especificación** | **25%** | Requisitos claros, criterios de aceptación precisos y coherencia en supuestos. |
| **Preparación y uso del agente** | **25%** | Calidad del harness, control del contexto, instrucciones y adaptación comprobable. |
| **Trazabilidad y decisiones** | **20%** | Calidad de los 3 episodios de delegación conectando requisito, intervención humana y evidencia. |

---

## 6. Análisis Crítico: Estrategia de Arquitectura y Metodología

### 6.1. Adopción de ODD (Organic Driven Development)
La metodología ODD es ideal para este desafío:
- **Especificación viva**: Comienza con un contrato claro de tipos y comportamiento antes de codificar.
- **Ciclo guiado por pruebas (TDD/ODD)**: Cada regla (límites consecutivos, solapamiento, solapamiento entre unidades distintas, persistencia) se plasma en una prueba antes o en paralelo a la implementación.
- **Logbook y trazabilidad**: El registro de episodios y decisiones humanas exigido por la consigna coincide de forma natural con los hitos de ODD.

### 6.2. Evaluación del Stack de Agentes: Antigravity CLI vs. Harness Pi (con LLM Local)
La propuesta de utilizar **Antigravity CLI** y el **harness Pi** (ambos integrados con Gentle AI y con un LLM local en Pi):

| Aspecto | Enfoque con Antigravity CLI | Enfoque con Harness Pi + LLM Local | Combinación de Ambos |
|---|---|---|---|
| **Alineación con la Consigna** | **100% cubierto**: Cumple con el rol de harness existente que opera con herramientas reales sobre el repo. | **100% cubierto**: Es un harness existente con ejecución y herramientas locales. | Válido, pero la consigna aclara que *"un agente basta y la cantidad de agentes no da puntos por sí misma"*. |
| **Capacidad y Fiabilidad de Tool-Calling** | Modelos de frontera suelen respetar fielmente esquemas de herramientas y diffs precisos sin corromper código. | Un LLM local requiere verificar rigurosamente la calidad del tool-calling (edición atómica, comandos de shell y lectura sin alucinaciones). | Puede usarse Antigravity CLI para diseño/arquitectura y Pi para tareas acotadas de implementación. |
| **Documentación Requerida (Sección 3 del README)** | Registrar versión de CLI, modelo, prompts saneados, herramientas autorizadas y adaptación específica. | Registrar versión de Pi harness, modelo local exacto (cuantización, contexto), configuración saneada de Gentle AI y herramientas. | Obliga a documentar la configuración y permisos de **ambos** entornos y cómo se coordinan. |
| **Los 3 Episodios de Delegación** | Muy directo de registrar (instrucción → diff generado → revisión humana → commit). | Ideal si se busca demostrar cómo un LLM local resuelve o falla una tarea específica y requiere corrección humana. | Permite contrastar un episodio en un harness vs. otro, aportando variedad a la trazabilidad. |

**Recomendación de arquitectura**:
1. Asegurar primero que el pipeline de **ODD** y la suite de pruebas automáticas sean el árbitro de la verdad.
2. Si se utiliza el harness **Pi** con un LLM local, documentar con exactitud el modelo (nombre, pesos, contexto) y asegurarse de que sus acciones sobre los archivos sean verificadas mediante tests antes de aceptar los cambios (cumpliendo con la revisión humana exigida).
3. Recordar que el evaluador correrá el código y los tests **sin necesidad de levantar ningún LLM ni harness**.
