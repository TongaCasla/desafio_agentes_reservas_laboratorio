# Sistema de Reservas de Equipos de Laboratorio

Sistema local y desacoplado para la gestión de reservas de equipos de laboratorio, desarrollado con arquitectura limpia (Clean Architecture), pruebas automatizadas integrales y persistencia en SQLite, ejecutado y verificado mediante ingeniería de software asistida por IA.

---

## 1. Especificación Breve

### 1.1. Problema y Alcance
El sistema resuelve la gestión de reservas compartidas de equipos de laboratorio para evitar colisiones horarias y garantizar disponibilidad en un entorno de inventario predefinido.

- **Dentro de alcance**:
  - Inventario inmutable de 5 unidades de laboratorio (`MIC-01`, `MIC-02`, `OSC-01`, `MUL-01`, `FUE-01`).
  - Validación de reservas (unidad existente, solicitante no vacío, intervalo estrictamente válido `inicio < fin`).
  - Prevención de solapamiento en la misma unidad con soporte explícito para turnos consecutivos (límites coincidentes).
  - Concurrencia válida para distintas unidades en el mismo horario.
  - Cancelación de reservas con conservación de trazabilidad histórica e inmediata liberación del horario.
  - Persistencia local en SQLite que sobrevive íntegramente al reinicio.
  - API REST local en FastAPI y suite de pruebas automatizadas con Pytest.
  - Empaquetado en contenedor Docker reproducible.
- **Fuera de alcance**:
  - Autenticación, roles y usuarios reales.
  - Notificaciones por correo/webhooks.
  - Facturación o pagos.
  - Concurrencia distribuida en clúster.

### 1.2. Inventario Precargado (Inmutable)
| ID Unidad | Equipo |
|---|---|
| `MIC-01` | Microscopio digital |
| `MIC-02` | Microscopio digital |
| `OSC-01` | Osciloscopio |
| `MUL-01` | Multímetro |
| `FUE-01` | Fuente de alimentación |

### 1.3. Reglas de Negocio y Criterios de Aceptación
1. **Identificación única**: Toda reserva genera un UUID4 persistente.
2. **Validación de solicitante**: Strings vacíos o compuestos únicamente de espacios en blanco (`"   "`) son rechazados con HTTP 400 (`EMPTY_REQUESTER`).
3. **Validación temporal**: Requiere `start_time < end_time` en formato ISO 8601 (normalizado a UTC). Si `start_time >= end_time`, se rechaza con HTTP 400 (`INVALID_TIME_RANGE`).
4. **Semántica de intervalos y no solapamiento**: Dos reservas sobre la misma unidad colisionan si y solo si:
   $$\max(inicio_1, inicio_2) < \min(fin_1, fin_2)$$
   - Intervalos consecutivos como `[10:00, 11:00)` y `[11:00, 12:00)` en la misma unidad **son válidos** y no colisionan.
   - Si colisiona, se rechaza con HTTP 409 (`RESERVATION_OVERLAP`).
5. **Independencia de unidades**: Unidades distintas (ej. `MIC-01` y `MIC-02`) pueden reservarse simultáneamente en el mismo intervalo sin conflicto.
6. **Cancelación**: Cambia el estado a `CANCELLED`, preserva el ID y los metadatos históricos, y libera el horario inmediatamente. Una segunda cancelación sobre la misma reserva arroja HTTP 409 (`ALREADY_CANCELLED`).
7. **Evolución en Git**: El historial de commits refleja la especificación inicial (`6cb6043`), el dominio (`0f08636`), la persistencia (`776590e`), la API (`6efc4a5`) y la contenerización (`df1d338`).

---

## 2. Solución

### 2.1. Arquitectura y Estructura de Directorios
Se adoptó **Clean / Hexagonal Architecture** para desacoplar las reglas de negocio puras de cualquier framework web o motor de almacenamiento:

```text
desafio_agentes_reservas_laboratorio/
├── src/
│   └── lab_reservations/
│       ├── domain/                  # Núcleo puro (sin dependencias externas)
│       │   ├── exceptions.py        # Excepciones de dominio tipadas
│       │   ├── models.py            # Entidad Reservation, inventario inmutable y lógica de solapamiento
│       │   ├── repository.py        # Contrato abstracto (ABC) de persistencia
│       │   └── service.py           # Casos de uso del sistema de reservas
│       ├── infrastructure/          # Adaptadores secundarios
│       │   ├── database.py          # Conexión SQLite y creación de tablas/índices
│       │   └── sqlite_repository.py # Implementación concreta del repositorio
│       └── api/                     # Adaptadores primarios (FastAPI)
│           ├── app.py               # Factory de la aplicación y manejadores de error HTTP
│           ├── dependencies.py      # Inyección de dependencias desacoplada
│           ├── routes.py            # Endpoints REST
│           └── schemas.py           # Contratos de entrada/salida Pydantic
├── tests/
│   ├── unit/                        # Tests unitarios del dominio (en memoria)
│   │   ├── test_models.py           # Validación de reglas temporales, solicitante e inventario
│   │   └── test_service.py          # Concurrencia, límites consecutivos y cancelaciones
│   └── integration/                 # Tests de integración
│       ├── test_sqlite_repository.py# Verificación de persistencia tras reinicio
│       └── test_api.py              # Suite completa contra endpoints HTTP
├── Dockerfile                       # Contenedor autocontenido
├── docker-compose.yml               # Orquestación local con volumen persistente
├── pyproject.toml                   # Configuración del paquete y pytest
├── requirements.txt                 # Dependencias productivas
└── requirements-dev.txt             # Dependencias de desarrollo y test
```

### 2.2. Tecnologías y Versiones
- **Python**: 3.11+ (desarrollado y probado sobre 3.12 / 3.14)
- **FastAPI**: >= 0.115.0
- **Uvicorn**: >= 0.30.0
- **Pydantic**: >= 2.8.0
- **Pytest**: >= 8.0.0
- **HTTPX**: >= 0.27.0
- **SQLite3**: Incluido en la biblioteca estándar de Python
- **Docker**: 20+

### 2.3. Instrucciones de Instalación y Ejecución

#### Opción A: Entorno Local (Python)
1. **Crear y activar entorno virtual**:
   ```bash
   python -m venv .venv
   # En Windows:
   .\.venv\Scripts\activate
   # En Linux/macOS:
   source .venv/bin/activate
   ```
2. **Instalar dependencias**:
   ```bash
   pip install -r requirements-dev.txt
   ```
3. **Ejecutar la suite de pruebas**:
   ```bash
   pytest -v
   ```
4. **Iniciar el servidor API**:
   ```bash
   uvicorn lab_reservations.api.app:app --host 0.0.0.0 --port 8000 --reload
   ```
   La documentación interactiva Swagger estará disponible en: `http://localhost:8000/docs`.

#### Opción B: Ejecución en Docker
1. **Levantar el servicio con docker-compose**:
   ```bash
   docker compose up --build -d
   ```
2. **Ejecutar los tests dentro del contenedor**:
   ```bash
   docker compose exec api pytest -v
   ```
3. **Detener el servicio**:
   ```bash
   docker compose down
   ```

### 2.4. Persistencia y Recuperación tras Reinicio
- Los datos se almacenan en un archivo SQLite ubicado por defecto en `data/reservations.db` (en Docker montado en el volumen persistente `lab_data` mapeado a `/app/data`).
- **Garantía de persistencia**: El archivo almacena todas las reservas y cancelaciones con sus marcas de tiempo ISO 8601. Al reiniciar el servidor o el contenedor, el repositorio reconecta a la base existente y recupera el 100% del estado histórico.
- La prueba `tests/integration/test_sqlite_repository.py::test_sqlite_persistence_survives_restart` valida explícitamente que tras cerrar y volver a instanciar el repositorio, las reservas activas y canceladas se mantienen intactas.

### 2.5. Limitaciones Conocidas y Trabajo Futuro
- Al no requerirse autenticación por la consigna, cualquier solicitante puede registrar reservas indicando su nombre.
- El almacenamiento SQLite usa transacciones locales; en un entorno distribuido multi-nodo se requeriría una base de datos relacional cliente-servidor (PostgreSQL) o bloqueos distribuidos.

---

## 3. Preparación del Agente

### 3.1. Entorno y Harness Utilizado
- **Harness**: **Antigravity CLI** operando dentro de **Mission Control** con el protocolo de ingeniería asistida **Gentle AI**.
- **Modelo de Lenguaje**: Gemini 2.5 / 3.8 Flash.
- **Justificación de elección**: Modelos con alta velocidad de inferencia, excelente seguimiento de contratos de esquemas, tool-calling determinista y capacidad de emitir diffs atómicos sin romper código preexistente ni alucinar dependencias.

### 3.2. Instrucciones Suministradas y Contexto Excluido
- **Instrucciones activas (System Prompt)**:
  - Protocolo de persona Senior Architect con foco en fundamentos de arquitectura limpia antes de codificar.
  - Regla estricta de verificación: no asumir afirmaciones sin prueba ejecutable.
  - Protocolo de memoria episódica persistente (Engram MCP) para registrar decisiones técnicas y lecciones aprendidas entre sesiones.
  - Política de commits convencionales sin atribuciones artificiales.
- **Contexto excluido deliberadamente**:
  - Se excluyeron deliberadamente frameworks pesados, ORMs complejos (como SQLAlchemy o Django ORM) y librerías de interfaz gráfica para evitar sobreingeniería innecesaria que distrajera de la evaluación de las reglas de negocio puras.

### 3.3. Herramientas y Permisos Concedidos
- **Herramientas de shell**: Ejecución controlada de PowerShell para inicialización de Git, creación de entornos virtuales y ejecución de Pytest.
- **Herramientas de sistema de archivos**: `read_file`, `write_file`, `edit_file` con lecturas limitadas por ventana y ediciones atómicas.
- **Memoria persistente**: `mem_save`, `mem_context` (Engram MCP) para persistir decisiones de arquitectura entre turnos.

### 3.4. Adaptaciones Específicas Comprobables
- **Control de límites temporales estrictos**: Se instruyó al agente para tratar las reservas como intervalos semi-abiertos $[inicio, fin)$, permitiendo que una reserva termine a las `11:00` y otra comience a las `11:00` en la misma unidad sin generar falsos positivos de solapamiento.
- **Aislamiento de dominio primero (TDD/ODD)**: Se obligó a construir el núcleo de dominio y verificarlo con 20 tests unitarios aislados antes de escribir una sola línea de código HTTP o SQLite.

---

## 4. Registro de Decisiones y Delegación (Los 3 Episodios Reales)

### 4.1. Registro de Decisiones de Diseño

| ID Decisión | Alternativas Evaluadas | Decisión Adoptada | Fundamentación y Consecuencias |
|---|---|---|---|
| **ADR-01: Stack Técnico** | Node.js (TypeScript) vs. Go vs. Python | **Python con Pytest y SQLite** | Maximiza la legibilidad, reduce el boilerplate y cuenta con soporte nativo de SQLite sin requerir servicios externos para el evaluador. |
| **ADR-02: Patrón Arquitectónico** | Arquitectura en capas tradicional vs. Clean/Hexagonal | **Clean/Hexagonal Architecture** | Aísla el cálculo de solapamiento y las entidades de cualquier dependencia de red o persistencia; habilita tests unitarios inmediatos en milisegundos. |
| **ADR-03: Interfaz de Usuario** | CLI interactiva vs. API REST | **API REST con FastAPI** | Proporciona contratos HTTP fuertemente tipados con OpenAPI/Swagger automático, códigos de estado canónicos (400, 404, 409) y facilidad de prueba automatizada con TestClient. |

---

### 4.2. Los 3 Episodios Reales de Delegación

#### Episodio 1: Diagnóstico de Estado y Decisión del Stack Técnico
- **Objetivo y requisito**: Establecer las bases técnicas del proyecto asegurando la trazabilidad exigida por la rúbrica desde el primer commit.
- **Contexto suministrado y extracto de instrucción**:
  - *Humano*: `"vamos a trabajar sobre desglose_desafio.md"` (luego renombrado a `planificacion_desafio.md`)
  - *Agente*: Inspeccionó el espacio de trabajo, verificó que no existía repositorio Git inicializado y propuso comenzar inicializando Git y acordando el stack tecnológico para asegurar evidencia auditable.
- **Acción o resultado generado por el agente**:
  - Lectura completa del archivo de requisitos [planificacion_desafio.md](planificacion_desafio.md).
  - Alerta sobre la ausencia de control de versiones y solicitud de definición de stack.
- **Decisión humana (aceptar, corregir o rechazar, con fundamentación)**:
  - *Aceptada y acotada*: El humano aprobó inicializar el repositorio y definió el stack: `"me parece bien inicializar el repo, respecto al stack tecnico vamos con python, pytest, como es un proyecto chico usamos sqlite y docker"`.
- **Enlace verificable**:
  - Commit inicial de Git: `6cb6043` (`docs: add challenge specification and initial project structure`).
  - Archivo de exclusión: [.gitignore](.gitignore).

---

#### Episodio 2: Diseño del Dominio Puro y Validación de Solapamiento Temporal
- **Objetivo y requisito**: Implementar las entidades de negocio, el inventario inmutable y la regla matemática de solapamiento que admita reservas consecutivas en la misma unidad.
- **Contexto suministrado y extracto de instrucción**:
  - *Agente*: Propuso estructurar el dominio puro antes de tocar infraestructura y consultó si exponer vía CLI o API.
  - *Humano*: `"Aislar el dominio de 10, y sobre la interfaz vamos con fastapi"`.
- **Acción o resultado generado por el agente**:
  - Creó la entidad [`Reservation`](src/lab_reservations/domain/models.py) con normalización UTC y validación de solicitante no vacío.
  - Implementó la lógica matemática de intervalos semi-abiertos:
    `max(start1, start2) < min(end1, end2)`
  - Desarrolló [`ReservationService`](src/lab_reservations/domain/service.py) y el inventario inmutable.
  - Diseñó una suite de 20 tests unitarios en [`test_models.py`](tests/unit/test_models.py) y [`test_service.py`](tests/unit/test_service.py) cubriendo turnos consecutivos, unidades distintas simultáneas y cancelaciones.
- **Decisión humana (aceptar, corregir o rechazar, con fundamentación)**:
  - *Aceptada*: La suite de 20 tests unitarios pasó de forma determinista en 0.10s, validando todas las reglas del negocio de manera aislada antes de conectar la base de datos.
- **Enlace verificable**:
  - Commit: `0f08636` (`feat(domain): implement core entities, validation rules, and service with unit tests`).
  - Pruebas unitarias: [`tests/unit/test_models.py`](tests/unit/test_models.py) y [`tests/unit/test_service.py`](tests/unit/test_service.py).

---

#### Episodio 3: Persistencia en SQLite, API REST con FastAPI y Contenerización Docker
- **Objetivo y requisito**: Persistir el estado garantizando recuperación íntegra tras reinicio, exponer los endpoints HTTP canónicos y encapsular la solución para su ejecución reproducible sin dependencias locales.
- **Contexto suministrado y extracto de instrucción**:
  - Instrucción derivada de los requisitos acordados: persistencia local sin ORMs pesados y API con FastAPI.
- **Acción o resultado generado por el agente**:
  - Construyó [`SQLiteReservationRepository`](src/lab_reservations/infrastructure/sqlite_repository.py) con esquema SQL optimizado e índices por unidad y estado.
  - Creó la prueba de integración [`test_sqlite_persistence_survives_restart`](tests/integration/test_sqlite_repository.py) que simula el apagado y reencendido de la aplicación comprobando que las reservas activas y canceladas persisten.
  - Implementó los endpoints en [`routes.py`](src/lab_reservations/api/routes.py) y manejadores globales de error en [`app.py`](src/lab_reservations/api/app.py) mapeando excepciones de dominio a códigos HTTP (400, 404, 409).
  - Diseñó el [`Dockerfile`](Dockerfile) y [`docker-compose.yml`](docker-compose.yml) configurando el volumen persistente de datos.
  - Escribió la suite de pruebas de integración [`tests/integration/test_api.py`](tests/integration/test_api.py) alcanzando un total de 30 pruebas automatizadas exitosas.
- **Decisión humana (aceptar, corregir o rechazar, con fundamentación)**:
  - *Aceptada*: Verificación de la suite completa de 30 tests pasando al 100% en menos de 1 segundo (`pytest -v`), confirmando persistencia de datos y manejo de colisiones.
- **Enlace verificable**:
  - Commits:
    - `776590e` (`feat(infrastructure): implement SQLite repository and restart persistence verification`).
    - `6efc4a5` (`feat(api): implement FastAPI REST endpoints with dependency injection and error handling`).
    - `df1d338` (`feat(docker): add Dockerfile, docker-compose.yml and .dockerignore for containerized execution`).
