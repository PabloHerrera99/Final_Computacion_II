# Descripción de la Aplicación

El proyecto consiste en una aplicación cliente-servidor para el juego **Cuatro en Línea**, implementado en Python. La aplicación permite a múltiples usuarios conectarse desde diferentes dispositivos para jugar en línea de manera concurrente. El sistema utiliza un servidor central que gestiona las partidas y mantiene un sistema de ranking y estadísticas de los jugadores, mientras que los clientes se encargan de enviar los movimientos realizados por los jugadores y recibir actualizaciones sobre el estado del juego.

## Funcionamiento del Cliente

Cada cliente actúa como una interfaz de línea de comandos (CLI) que permite al usuario jugar **Cuatro en Línea**. Los clientes se conectan al servidor mediante sockets TCP y envían las jugadas (la columna donde desean colocar su ficha) al servidor. Los clientes reciben actualizaciones en tiempo real sobre el estado del tablero de juego, incluyendo mensajes que indican cuándo un jugador ha ganado, empatado o cometido una jugada inválida. Además, los usuarios pueden consultar su historial de partidas y ver el ranking general de jugadores.

El cliente parsea argumentos por línea de comandos para configurar la conexión, credenciales y acción a realizar (jugar, ver historial, ver ranking).

## Funcionamiento del Servidor

El servidor central gestiona múltiples partidas de **Cuatro en Línea** de manera concurrente. Cada vez que un cliente envía una jugada, el servidor valida el movimiento, actualiza el tablero y verifica si ha habido un ganador o si el juego ha terminado en empate. Al finalizar cada partida, el servidor actualiza las estadísticas de los jugadores y recalcula el ranking.

El servidor se basa en **dos procesos paralelos**:
1. **Proceso principal**: Encargado de la **lógica del juego** y el manejo de conexiones de clientes mediante sockets TCP de forma asíncrona (asyncio).
2. **Proceso secundario**: Gestiona las **consultas** a la base de datos a través de la API REST y el procesamiento de estadísticas.

Estos procesos se comunican entre sí mediante **pipes** (IPC) para intercambiar información de manera eficiente, como resultados de partidas, solicitudes de autenticación y consultas de estadísticas.

Para manejar las conexiones de múltiples clientes simultáneamente, el servidor utiliza **concurrencia** implementada con el módulo `asyncio`. Esto permite que cada cliente pueda interactuar con el servidor sin bloquear a otros jugadores. Los clientes y el servidor se comunican de manera asíncrona, intercambiando mensajes a través de sockets.

## Gestión de Usuarios, Estadísticas y API

La aplicación incluye una **API REST** que gestiona la **base de datos de usuarios** y el **sistema de ranking**. Esta API es responsable de:
- Registrar y autenticar usuarios
- Almacenar el historial completo de partidas
- Calcular y mantener estadísticas de cada jugador (partidas ganadas, perdidas, empatadas, racha actual)
- Generar y mantener actualizado el ranking global de jugadores
- Proporcionar consultas de datos históricos y estadísticos

La API utiliza **Flask** como framework para manejar las solicitudes HTTP y se conecta a una base de datos SQLite (puede escalarse a PostgreSQL) para almacenar toda la información.

## Sistema de Ranking y Estadísticas

El sistema mantiene las siguientes estadísticas por jugador:
- Total de partidas jugadas
- Partidas ganadas, perdidas y empatadas
- Porcentaje de victoria
- Racha actual (victorias consecutivas)
- Mejor racha histórica
- Puntuación para el ranking (basada en victorias, ratio de victoria, etc.)

El ranking se actualiza automáticamente después de cada partida finalizada y puede ser consultado por cualquier usuario.

## Tecnología Utilizada

- **Concurrencia:** Implementada en el servidor mediante `asyncio` para manejar múltiples conexiones simultáneas de clientes de forma asíncrona.
- **Paralelismo:** El servidor está dividido en dos procesos: uno encargado de manejar la lógica del juego y las conexiones, y otro encargado de gestionar las consultas a la base de datos, estadísticas y la API.
- **IPC (Inter-Process Communication):** Los dos procesos se comunican a través de `pipes` para intercambiar información de manera eficiente.
- **Comunicación Asíncrona:** El servidor y los clientes se comunican utilizando sockets TCP de manera no bloqueante mediante asyncio.
- **Flask y API REST:** Se utiliza Flask para la gestión de la API REST que maneja usuarios, partidas y estadísticas.
- **Parseo de Argumentos:** El cliente utiliza `argparse` para procesar argumentos de línea de comandos.
- **Persistencia de Datos:** Base de datos SQLite para almacenar usuarios, partidas, estadísticas y ranking.
- **Manejo de Estado del Juego:** El servidor mantiene el estado de múltiples partidas simultáneas y envía actualizaciones a los clientes correspondientes.

## Diagrama Entidad-Relación

```
                         +---------------------------+
                         |         users             |
                         +---------------------------+
                         | - id (PK)                 |
                         | - username (UNIQUE)       |
                         | - password_hash           |
                         | - created_at              |
                         +-------------+-------------+
                                       |
                                       | 1:N
                                       |
            +--------------------------+---------------------------+
            |                                                      |
            v                                                      v
+-----------------------+                                +------------------------+
|      matches          |                                |        stats           |
|   (como player1)      |                                |                        |
+-----------------------+                                +------------------------+
| - id (PK)             |                                | - user_id (PK, FK)     |
| - player1_id (FK)     |                                | - total_matches        |
| - player2_id (FK)     |                                | - wins                 |
| - winner_id (FK)      |                                | - losses               |
| - played_at           |                                | - draws                |
| - duration_seconds    |                                | - win_rate             |
+-----------------------+                                | - current_streak       |
                                                         | - best_streak          |
                                                         | - ranking_points       |
                                                         | - updated_at           |
                                                         +------------------------+
```

# Gráfico de la Arquitectura

```
+----------------+         +-------------------------------------------------------------------+
|    Cliente     |         |                            Servidor                               |
|     (CLI)      |         |                                                                   |
|                |         |        Proceso 1                           Proceso 2              |
|  +----------+  |   TCP   |   +------------------------+   Pipe   +-------------------------+ |
|  | Jugador  |  +-------->|   | Lógica de Juego        +--------->| Consultas a API         | |
|  | argparse |  |         |   | Gestión de Clientes    |<---------+ Procesamiento de Stats  | |
|  +----------+  |         |   | AsyncIO (Sockets)      |   Pipe   +------------+------------+ |
|                |         |   +------------------------+                       |              |
+----------------+         +----------------------------------------------------|--------------|
                                                                                |
                                                                                | HTTP
                                                                                v
                                                                  +---------------------------+
                                                                  |        API REST           |
                                                                  | +----------------------+  |
                                                                  | | Gestión de Usuarios  |  |
                                                                  | | Historial de Partidas|  |
                                                                  | | Sistema de Ranking   |  |
                                                                  | | Estadísticas         |  |
                                                                  | +----------+-----------+  |
                                                                  +------------|-------------+
                                                                               |
                                                                               v
                                                                  +---------------------------+
                                                                  |    Base de Datos SQLite   |
                                                                  | - Usuarios                |
                                                                  | - Partidas                |
                                                                  | - Estadísticas            |
                                                                  | - Ranking                 |
                                                                  +---------------------------+
```

## Nodos Principales

1. **Cliente (CLI)**:
   - Interfaz de línea de comandos que parsea argumentos (usuario, contraseña, acción, IP del servidor)
   - Se conecta al servidor mediante sockets TCP
   - Envía jugadas (movimientos) y recibe actualizaciones sobre el estado del tablero
   - Puede solicitar historial de partidas y consultar ranking

2. **Servidor - Proceso 1 (Lógica del Juego)**:
   - Gestiona múltiples partidas concurrentes utilizando asyncio
   - Acepta y maneja conexiones de clientes mediante sockets TCP asíncronos
   - Valida jugadas de los jugadores y actualiza el estado del juego
   - Mantiene cola de jugadores esperando partida
   - Envía solicitudes al Proceso 2 mediante pipes para autenticación y registro de resultados

3. **Servidor - Proceso 2 (Consultas y Estadísticas)**:
   - Recibe solicitudes del Proceso 1 a través de pipes
   - Se comunica con la API REST mediante HTTP para consultas a la base de datos
   - Procesa y actualiza estadísticas de jugadores
   - Recalcula el ranking después de cada partida
   - Responde al Proceso 1 con los resultados mediante pipes

4. **API REST (Flask)**:
   - Endpoints para registro y autenticación de usuarios
   - Gestión del historial de partidas
   - Cálculo y consulta de estadísticas por jugador
   - Generación y consulta del ranking global
   - Interfaz con la base de datos

5. **Base de Datos (SQLite)**:
   - Almacena usuarios (username, password hash)
   - Registra todas las partidas jugadas (jugadores, resultado, fecha)
   - Mantiene estadísticas por jugador
   - Almacena el ranking actualizado

## Conectividad y Mecanismos de Comunicación

- **Sockets TCP:** Comunicación entre cliente y servidor (Proceso 1). El servidor escucha en un puerto determinado para recibir conexiones entrantes de múltiples clientes.
- **Pipes (IPC):** Comunicación bidireccional entre el Proceso 1 y Proceso 2 del servidor para intercambiar información (autenticación, resultados de partidas, consultas de estadísticas).
- **API REST (HTTP):** El Proceso 2 se comunica con la API mediante solicitudes HTTP para acceder a la base de datos.
- **AsyncIO:** Flujos de comunicación asíncrona entre cliente y servidor, permitiendo múltiples conexiones concurrentes sin bloqueo.

## Flujos de Comunicación

1. **Conexión Cliente-Servidor:**
   - El cliente parsea los argumentos de línea de comandos (username, password, acción, IP)
   - El cliente se conecta al servidor mediante socket TCP
   - El servidor (Proceso 1) acepta la conexión de forma asíncrona

2. **Autenticación/Registro:**
   - El cliente envía credenciales (username, password) al servidor
   - El Proceso 1 envía solicitud de autenticación al Proceso 2 mediante pipe
   - El Proceso 2 consulta la API para validar o registrar al usuario
   - La API verifica en la base de datos y responde
   - El Proceso 2 envía resultado al Proceso 1 mediante pipe
   - El servidor confirma al cliente si puede acceder

3. **Jugar Partida:**
   - El cliente solicita jugar y es agregado a la cola de espera
   - Cuando hay dos jugadores disponibles, el Proceso 1 inicia la partida
   - Los clientes envían movimientos (número de columna)
   - El servidor valida cada jugada, actualiza el estado y notifica a ambos jugadores
   - Al finalizar la partida (victoria/empate):
     - El Proceso 1 envía el resultado al Proceso 2 mediante pipe
     - El Proceso 2 actualiza estadísticas y ranking vía API
     - Los clientes reciben notificación del resultado final

4. **Consultar Historial:**
   - El cliente solicita su historial
   - El Proceso 1 envía solicitud al Proceso 2 mediante pipe
   - El Proceso 2 consulta la API que obtiene datos de la base de datos
   - El resultado se envía de vuelta al cliente

5. **Consultar Ranking:**
   - El cliente solicita ver el ranking
   - El Proceso 1 solicita datos al Proceso 2 mediante pipe
   - El Proceso 2 obtiene el ranking actualizado de la API
   - El ranking se envía al cliente para visualización

## Uso de Herramientas de Sincronismo y Concurrencia

- **AsyncIO:** Para manejar múltiples clientes conectados simultáneamente de forma no bloqueante
- **Multiprocessing:** Para ejecutar dos procesos en paralelo (juego + consultas/estadísticas)
- **Pipes:** Para sincronizar la comunicación entre los dos procesos del servidor
- **Locks/Semáforos (si necesario):** Para proteger recursos compartidos en la gestión de partidas concurrentes

## Justificaciones Técnicas

1. **¿Por qué AsyncIO?** 

Al ser un sistema simple en donde la comunicacion se realiza con comandos simples me parecio mejor usar AsynIO permite manejar muchas conexiones de clientes simultáneamente sin crear un proceso o thread por cada uno, optimizando recursos.

2. **¿Por qué Multiprocessing + Pipes?** 

Separar la lógica del juego del procesamiento de datos permite que ambos trabajen en paralelo sin bloquearse mutuamente.

3. **¿Por qué SQLite?** 
Base de datos ligera, sin necesidad de servidor adicional, suficiente para el alcance del proyecto.

(Creo que podria usarse una base de datos no relacional pero para facilitar el desarrollo decidí usar una base de datos que me resulte mas comoda al desarrollar)

