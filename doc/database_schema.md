# Esquema de Base de Datos

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
            |                          |                           |
            v                          v                           v
+-----------------------+   +------------------------+   +------------------------+
|      matches          |   |      matches           |   |        stats           |
|   (como player1)      |   |   (como player2)       |   |                        |
+-----------------------+   +------------------------+   +------------------------+
| - id (PK)             |   | - id (PK)              |   | - user_id (PK, FK)     |
| - player1_id (FK) ----+-->| - player2_id (FK) -----+-->| - total_matches        |
| - player2_id (FK)     |   | - winner_id (FK, NULL) |   | - wins                 |
| - winner_id (FK)      |   | - played_at            |   | - losses               |
| - played_at           |   | - duration_seconds     |   | - draws                |
| - duration_seconds    |   +------------------------+   | - win_rate             |
+-----------------------+                                | - current_streak       |
                                                         | - best_streak          |
                                                         | - ranking_points       |
                                                         | - updated_at           |
                                                         +------------------------+
```

## Descripción de Tablas

### 1. users
Almacena la información de los usuarios registrados.

| Campo          | Tipo      | Descripción                              |
|----------------|-----------|------------------------------------------|
| id             | INTEGER   | Clave primaria autoincremental           |
| username       | TEXT      | Nombre de usuario único                  |
| password_hash  | TEXT      | Hash de la contraseña                    |
| created_at     | TIMESTAMP | Fecha de registro (automática)           |

### 2. matches
Registra todas las partidas jugadas.

| Campo            | Tipo      | Descripción                                    |
|------------------|-----------|------------------------------------------------|
| id               | INTEGER   | Clave primaria autoincremental                 |
| player1_id       | INTEGER   | FK a users - Primer jugador                    |
| player2_id       | INTEGER   | FK a users - Segundo jugador                   |
| winner_id        | INTEGER   | FK a users - Ganador (NULL si empate)          |
| played_at        | TIMESTAMP | Fecha y hora de la partida (automática)        |
| duration_seconds | INTEGER   | Duración de la partida en segundos             |

### 3. stats
Mantiene estadísticas acumuladas de cada jugador.

| Campo           | Tipo      | Descripción                                      |
|-----------------|-----------|--------------------------------------------------|
| user_id         | INTEGER   | Clave primaria, FK a users                       |
| total_matches   | INTEGER   | Total de partidas jugadas                        |
| wins            | INTEGER   | Partidas ganadas                                 |
| losses          | INTEGER   | Partidas perdidas                                |
| draws           | INTEGER   | Partidas empatadas                               |
| win_rate        | REAL      | Porcentaje de victoria (0.0 - 1.0)               |
| current_streak  | INTEGER   | Racha actual de victorias consecutivas           |
| best_streak     | INTEGER   | Mejor racha de victorias en la historia          |
| ranking_points  | INTEGER   | Puntos para el ranking global                    |
| updated_at      | TIMESTAMP | Última actualización de estadísticas             |
