# Funcionalidades por Entidad

## Cliente (CLI)

### Parseo de Argumentos
- **Argumentos de línea de comandos:** Utiliza `argparse` para procesar:
  - `-u, --username`: Nombre de usuario
  - `-p, --password`: Contraseña del usuario
  - `-a, --action`: Acción a realizar (jugar / historial / ranking)
  - `-i, --ip`: Dirección IP del servidor (IPv4 o IPv6)
  - `--port`: Puerto del servidor (opcional, con valor por defecto)

### Conexión y Comunicación
- **Conexión al Servidor:** Se conecta al servidor mediante sockets TCP utilizando la IP y puerto especificados
- **Envío de Credenciales:** Envía nombre de usuario y contraseña al servidor para autenticación o registro
- **Comunicación Asíncrona:** Envía y recibe mensajes del servidor de forma no bloqueante

### Funcionalidades de Juego
- **Envío de Jugadas:** Permite al usuario ingresar la columna donde desea colocar su ficha (1-7)
- **Recepción del Estado del Tablero:** Muestra el tablero actualizado después de cada movimiento
- **Notificaciones de Juego:**
  - Avisa cuando es el turno del jugador
  - Informa si una jugada es inválida (columna llena, fuera de rango)
  - Notifica el resultado final (victoria, derrota, empate)

### Consultas de Información
- **Ver Historial Personal:** Solicita y muestra el historial de partidas del usuario
  - Lista de partidas jugadas con fecha, rival y resultado
  - Estadísticas personales (ganadas, perdidas, empatadas)
- **Ver Ranking:** Solicita y muestra el ranking global de jugadores
  - Top jugadores ordenados por puntuación
  - Posición del usuario en el ranking
  - Estadísticas resumidas de cada jugador en el top

### Interfaz de Usuario
- **Visualización del Tablero:** Renderiza el tablero de juego en formato ASCII
- **Mensajes Informativos:** Muestra mensajes claros sobre el estado del juego y acciones del oponente
- **Manejo de Errores:** Informa al usuario sobre errores de conexión, credenciales inválidas, etc.

---

## Servidor - Proceso 1 (Lógica del Juego)

### Gestión de Conexiones
- **Aceptar Conexiones:** Escucha en un puerto TCP y acepta múltiples conexiones de clientes de forma asíncrona
- **Manejo Concurrente:** Utiliza `asyncio` para gestionar múltiples clientes simultáneamente sin bloqueo
- **Identificación de Clientes:** Mantiene registro de cada cliente conectado con su información de sesión

### Cola de Espera y Emparejamiento
- **Cola de Jugadores:** Mantiene una cola de jugadores autenticados esperando para jugar
- **Emparejamiento Automático:** Cuando hay al menos dos jugadores en la cola, los empareja para iniciar una partida
- **Gestión de Múltiples Partidas:** Puede gestionar varias partidas en paralelo de forma concurrente

### Lógica del Juego
- **Validación de Jugadas:**
  - Verifica que la columna seleccionada sea válida (1-7)
  - Comprueba que la columna no esté llena
  - Valida que sea el turno del jugador
- **Actualización del Estado:**
  - Coloca la ficha en la posición correcta del tablero
  - Actualiza el tablero de la partida
  - Alterna el turno entre jugadores
- **Detección de Fin de Juego:**
  - Verifica si hay cuatro fichas consecutivas (horizontal, vertical, diagonal)
  - Detecta empates (tablero lleno sin ganador)
  - Determina el ganador de la partida

### Comunicación con Clientes
- **Envío de Actualizaciones:** Notifica a ambos jugadores sobre:
  - Estado actualizado del tablero
  - Turno actual
  - Jugadas del oponente
  - Resultado de la partida
- **Manejo de Desconexiones:** Detecta y maneja desconexiones de clientes durante la partida

### Comunicación con Proceso 2 (IPC)
- **Solicitudes de Autenticación:**
  - Envía credenciales al Proceso 2 mediante pipe para validación
  - Recibe confirmación de autenticación o error
- **Registro de Resultados:**
  - Al finalizar una partida, envía el resultado (ganador, perdedor, empate) al Proceso 2
  - Incluye información de ambos jugadores y detalles de la partida
- **Solicitudes de Datos:**
  - Solicita historial de partidas de un usuario
  - Solicita datos del ranking global
  - Recibe respuestas del Proceso 2 con los datos solicitados

---

## Servidor - Proceso 2 (Consultas y Estadísticas)

### Comunicación por IPC
- **Recepción de Solicitudes:** Escucha continuamente el pipe para recibir solicitudes del Proceso 1
- **Envío de Respuestas:** Envía resultados de las consultas de vuelta al Proceso 1 mediante pipe
- **Gestión de Cola de Solicitudes:** Procesa solicitudes en orden manteniendo la integridad de los datos

### Interacción con la API
- **Autenticación de Usuarios:**
  - Envía solicitudes HTTP a la API para validar credenciales
  - Solicita registro de nuevos usuarios
  - Recibe tokens de sesión o confirmaciones
- **Registro de Partidas:**
  - Envía resultados de partidas finalizadas a la API
  - Incluye información de jugadores, ganador, fecha y duración
- **Consulta de Datos:**
  - Solicita historial de partidas de un usuario específico
  - Obtiene estadísticas actualizadas de jugadores
  - Consulta el ranking global

### Procesamiento de Estadísticas
- **Actualización de Stats:** Después de cada partida:
  - Incrementa contadores de partidas jugadas
  - Actualiza victorias, derrotas o empates
  - Calcula porcentaje de victoria
  - Actualiza racha actual (victorias consecutivas)
  - Registra mejor racha si corresponde
- **Cálculo de Puntuación:** Calcula puntos para el ranking basándose en:
  - Número de victorias
  - Ratio de victoria
  - Racha actual
  - Otros factores de ponderación

### Sincronización de Datos
- **Garantía de Consistencia:** Asegura que las actualizaciones a la base de datos se procesen correctamente
- **Manejo de Errores:** Gestiona errores de comunicación con la API y reintentos si es necesario

---

## API REST (Flask)

### Endpoints de Autenticación
- **POST /auth/register**
  - Registra un nuevo usuario
  - Valida que el username no exista
  - Hashea la contraseña antes de almacenarla
  - Retorna confirmación o error
- **POST /auth/login**
  - Valida credenciales de usuario
  - Verifica password hash
  - Retorna token de sesión o error

### Endpoints de Partidas
- **POST /matches**
  - Registra una nueva partida finalizada
  - Almacena jugadores, resultado, fecha y hora
  - Retorna ID de la partida creada
- **GET /matches/user/<username>**
  - Obtiene el historial de partidas de un usuario
  - Retorna lista de partidas con detalles
  - Ordenadas por fecha (más recientes primero)

### Endpoints de Estadísticas
- **GET /stats/<username>**
  - Obtiene estadísticas completas de un jugador
  - Retorna: partidas jugadas, ganadas, perdidas, empatadas, ratio de victoria, rachas
- **POST /stats/update**
  - Actualiza estadísticas después de una partida
  - Recalcula todos los valores estadísticos
  - Actualiza puntuación para el ranking

### Endpoints de Ranking
- **GET /ranking**
  - Obtiene el ranking global de jugadores
  - Retorna lista ordenada por puntuación
  - Incluye posición, username, puntos y estadísticas clave
- **GET /ranking/<username>**
  - Obtiene la posición específica de un usuario en el ranking
  - Retorna posición y estadísticas

### Gestión de Base de Datos
- **Conexión a SQLite:** Maneja conexión con la base de datos
- **Queries Optimizadas:** Ejecuta consultas SQL eficientes
- **Manejo de Transacciones:** Garantiza integridad de los datos con transacciones
- **Migraciones:** Gestiona el esquema de la base de datos

---

## Base de Datos (SQLite)

### Tabla: users
- **Campos:**
  - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
  - `username`: TEXT UNIQUE NOT NULL
  - `password_hash`: TEXT NOT NULL
  - `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

### Tabla: matches
- **Campos:**
  - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
  - `player1_id`: INTEGER (FK a users)
  - `player2_id`: INTEGER (FK a users)
  - `winner_id`: INTEGER (FK a users, NULL si empate)
  - `played_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  - `duration_seconds`: INTEGER

### Tabla: stats
- **Campos:**
  - `user_id`: INTEGER PRIMARY KEY (FK a users)
  - `total_matches`: INTEGER DEFAULT 0
  - `wins`: INTEGER DEFAULT 0
  - `losses`: INTEGER DEFAULT 0
  - `draws`: INTEGER DEFAULT 0
  - `win_rate`: REAL DEFAULT 0.0
  - `current_streak`: INTEGER DEFAULT 0
  - `best_streak`: INTEGER DEFAULT 0
  - `ranking_points`: INTEGER DEFAULT 0
  - `updated_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

### Funcionalidades
- **Persistencia:** Almacena todos los datos de forma permanente
- **Integridad Referencial:** Mantiene relaciones entre tablas con foreign keys
- **Índices:** Optimiza consultas frecuentes (búsqueda por username, ranking)
- **Respaldos:** Permite backups del archivo de base de datos

---

## Resumen de Interacciones Entre Entidades

1. **Cliente → Servidor (Proceso 1):** Sockets TCP (jugadas, solicitudes)
2. **Servidor Proceso 1 → Servidor Proceso 2:** Pipes IPC (autenticación, resultados, consultas)
3. **Servidor Proceso 2 → API:** HTTP REST (CRUD de usuarios, partidas, estadísticas)
4. **API → Base de Datos:** SQL queries (lectura/escritura de datos)
5. **Base de Datos → API:** Resultados de queries
6. **API → Servidor Proceso 2:** Respuestas HTTP
7. **Servidor Proceso 2 → Servidor Proceso 1:** Pipes IPC (respuestas)
8. **Servidor (Proceso 1) → Cliente:** Sockets TCP (actualizaciones, resultados)
