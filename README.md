# Final_Computacion_II

## Cuatro en Línea — multijugador en red
 
Aplicación cliente–servidor del clásico **Cuatro en Línea**, escrita en Python. Varios jugadores se conectan desde distintas máquinas por la red, se emparejan automáticamente y juegan partidas por turnos. El sistema mantiene un historial de partidas y un ranking con estadísticas por jugador.
 
- **Instalación y despliegue:** ver [`INSTALL.md`](INSTALL.md).
- **Decisiones de diseño y justificación:** ver [`INFO.md`](INFO.md).
- **Mejoras y características futuras:** ver [`TODO.md`](TODO.md).

## Características
 
- Juego de Cuatro en Línea por turnos entre dos jugadores en red.
- Emparejamiento automático (matchmaking) por orden de llegada.
- Registro e inicio de sesión de usuarios.
- Historial de partidas paginado.
- Ranking global con puntos, victorias, derrotas, empates y win rate.
- Cliente de línea de comandos (CLI).
- Múltiples partidas en simultáneo gracias a la concurrencia con `asyncio`.

## Uso básico del cliente
 
Una vez levantados la API y el servidor (ver `INSTALL.md`), cada jugador usa el cliente desde su propia terminal:
 
```bash
python3 app/client/client.py -u <usuario> -p <contraseña> -a <acción> -i <ip_servidor> [--port 8888]
```
### Argumentos
 
| Argumento        | Descripción                                            | Obligatorio |
|------------------|--------------------------------------------------------|-------------|
| `-u`, `--username` | Nombre de usuario.                                   | Sí          |
| `-p`, `--password` | Contraseña.                                          | Sí          |
| `-a`, `--action`   | Acción a realizar: `jugar`, `historial` o `ranking`. | Sí          |
| `-i`, `--ip`       | IP del servidor (`127.0.0.1` si es local).           | Sí          |
| `--port`           | Puerto del servidor (por defecto `8888`).            | No          |

### Iniciar sesión y registrarse
 
No hay un comando aparte para iniciar sesión: el cliente intenta loguearse solo, con el usuario y la contraseña que le pasás. 
 
- Si las credenciales son correctas, te saluda y sigue con la acción pedida.
- Si el usuario **no existe** o la contraseña es incorrecta, te pregunta en consola `¿Registrarse? (s/n)`. Con `s` crea la cuenta con ese usuario y contraseña y quedás logueado.
Es decir, **la primera vez que usás un usuario nuevo, ese mismo paso lo registra.**

### Jugar una partida
 
El emparejamiento necesita **dos jugadores**, así que para una partida real abrí **dos clientes** (dos terminales) con usuarios distintos:
 
```bash
# Terminal A — jugador 1
python3 app/client/client.py -u pablo -p 1234 -a jugar -i 127.0.0.1
 
# Terminal B — jugador 2
python3 app/client/client.py -u ana -p 5678 -a jugar -i 127.0.0.1
```

Cuando hay dos en espera, el servidor los empareja y arranca la partida. El primero que entró a la cola juega primero.
