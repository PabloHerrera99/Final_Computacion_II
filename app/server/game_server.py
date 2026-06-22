import asyncio
import logging
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.common.protocol import (
    encode_message, decode_message,
    AUTH_REQUEST, REGISTER_REQUEST, PLAY_REQUEST,
    MOVE, HISTORY_REQUEST, RANKING_REQUEST,
    AUTH_RESPONSE, BOARD_UPDATE, GAME_OVER,
    HISTORY_RESPONSE, RANKING_RESPONSE, ERROR, WAITING
)
from app.common.game_logic import Board

logging.basicConfig(level=logging.INFO, format='[Proceso1] %(message)s')
log = logging.getLogger(__name__)

waiting_queue = None
pipe_lock = None

class Player:
    def __init__(self, reader, writer, username, user_id):
        self.reader = reader
        self.writer = writer
        self.username = username
        self.user_id = user_id
        self.game_done = asyncio.Event()
        
async def send_msg(writer, msg_type, payload=None):
    writer.write(encode_message(msg_type, payload or {}))
    await writer.drain()


async def pipe_request(pipe, message):
      """Envía mensaje al Proceso 2 y espera respuesta. Usa lock para serializar."""
      loop = asyncio.get_event_loop()
      async with pipe_lock:
          await loop.run_in_executor(None, pipe.send, message)
          response = await loop.run_in_executor(None, pipe.recv)
      return response


async def start_game(p1, p2, pipe):
    board = Board()
    players = [p1, p2]
    start_time = time.time()
    current = 0  # índice del jugador al que le toca

    # Avisar inicio a ambos
    for i, p in enumerate(players):
        await send_msg(p.writer, BOARD_UPDATE, {
            'board': board.get_board_state(),
            'your_turn': i == current,
            'player_num': i + 1,
            'opponent': players[1 - i].username
        })

    read_tasks = [asyncio.create_task(p.reader.read(1024)) for p in players]
    try:
        while True:
            done, _ = await asyncio.wait(read_tasks, return_when=asyncio.FIRST_COMPLETED)

            task = next(iter(done))
            idx = read_tasks.index(task)
            try:
                data = task.result()
            except Exception:
                data = await task

            read_tasks[idx] = asyncio.create_task(players[idx].reader.readline())

            # CHECK: Si el jugador se desconectó, terminar la partida y declarar ganador al otro
            if not data:
                log.info(f"Jugador {players[idx].username} se desconecto durante la partida.")
                winner = players[1 - idx]
                try:
                    await send_msg(winner.writer, GAME_OVER, {
                        'winner': winner.username,
                        'reason': 'opponent_disconnected'
                    })
                except Exception:
                    pass
                await pipe_request(pipe, {
                    'action': 'save_match',
                    'player1_id': p1.user_id,
                    'player2_id': p2.user_id,
                    'winner_id': winner.user_id,
                    'duration_seconds': int(time.time() - start_time)
                })
                return
            
            # CHECK: Si NO es el turno del jugador activo, RECHAZAR
            if idx != current:
                try:
                    await send_msg(players[idx].writer, ERROR, {'message': 'No es tu turno'})
                except Exception:
                    pass
                continue
            
            # CHECK: Validacion del movimiento
            try:
                msg_type, payload = decode_message(data)
            except Exception:
                await send_msg(players[idx].writer, ERROR, {'message': 'Mensaje inválido'})
                continue

            if msg_type != MOVE:
                await send_msg(players[idx].writer, ERROR, {'message': 'Se esperaba un movimiento'})
                continue 

            col = payload.get('column')
            if not isinstance(col, int):
                await send_msg(players[idx].writer, ERROR, {'message': 'Columna inválida'})
                continue
            success, _ = board.drop_piece(col, current + 1)
            if not success:
                await send_msg(players[idx].writer, ERROR, {'message': 'Columna llena o inválida'})
                continue
            
            # CHECK: Ganador o empate
            winner = board.check_winner()
            is_draw = board.is_board_full()
            board_state = board.get_board_state()

            # Fin de partida
            if winner or is_draw:
                winner_id = None
                if winner:
                
                    winner_p = players[current]
                    loser_p = players[1 - current]
                    winner_id = winner_p.user_id
                    await send_msg(winner_p.writer, GAME_OVER, {'result': 'win', 'board': board_state})
                    await send_msg(loser_p.writer, GAME_OVER, {'result': 'lose', 'board': board_state})
                    log.info(f"Partida finalizada: {winner_p.username} ganó a {loser_p.username}")
                else:
                    for p in players:
                        await send_msg(p.writer, GAME_OVER, {'result': 'draw', 'board': board_state})
                    log.info(f"Partida finalizada: Empate entre {p1.username} y {p2.username}")
                
                await pipe_request(pipe, {
                    'action': 'save_match',
                    'player1_id': p1.user_id,
                    'player2_id': p2.user_id,
                    'winner_id': winner_id,
                    'duration_seconds': int(time.time() - start_time)
                })
                return
            
            # Cambio de turno
            current = 1 - current
            
            if read_tasks[current].done():
                try:
                    read_tasks[current].result()
                    log.info(f"Descarte de mensaje obsoletos de {players[current].username}")
                except Exception:
                    pass
                read_tasks[current] = asyncio.create_task(players[current].reader.readline())
            
            for i, p in enumerate(players):
                await send_msg(p.writer, BOARD_UPDATE, {
                    'board': board_state,
                    'your_turn': i == current,
                    'player_num': i + 1
                    })
    finally:
        for t in read_tasks:
            if not t.done():
                t.cancel()
        p1.game_done.set()
        p2.game_done.set()


async def handle_client(reader, writer, pipe):
    addr = writer.get_extra_info('peername')
    log.info(f"Nueva conexión: {addr}")
    playing = False

    try:
        # --- Autenticación ---
        data = await reader.readline()
        if not data:
            return

        msg_type, payload = decode_message(data)

        if msg_type == AUTH_REQUEST:
            action = 'login'
        elif msg_type == REGISTER_REQUEST:
            action = 'register'
        else:
            await send_msg(writer, ERROR, {'message': 'Se esperaba autenticación'})
            return

        response = await pipe_request(pipe, {
            'action': action,
            'username': payload.get('username'),
            'password': payload.get('password')
        })

        if not response['ok']:
            await send_msg(writer, AUTH_RESPONSE, {'ok': False, 'error': response.get('error')})
            return

        user_id  = response['user_id']
        username = payload.get('username')
        await send_msg(writer, AUTH_RESPONSE, {'ok': True, 'username': username})
        log.info(f"Autenticado: {username}")

        # --- Acción ---
        data = await reader.readline()
        if not data:
            return

        msg_type, payload = decode_message(data)

        if msg_type == PLAY_REQUEST:
            playing = True
            player = Player(reader, writer, username, user_id)
            await send_msg(writer, WAITING, {'message': 'Esperando oponente...'})
            await waiting_queue.put(player)
            await player.game_done.wait()   # se bloquea aquí hasta que termine la partida

        elif msg_type == HISTORY_REQUEST:
            resp = await pipe_request(pipe, {
                'action': 'history',
                'user_id': user_id,
                'page': payload.get('page', 1)
            })
            await send_msg(writer, HISTORY_RESPONSE, resp)
            
        elif msg_type == RANKING_REQUEST:
            resp = await pipe_request(pipe, {'action': 'ranking'})
            await send_msg(writer, RANKING_RESPONSE, resp)

        else:
            await send_msg(writer, ERROR, {'message': 'Acción desconocida'})

    except Exception as e:
        log.error(f"Error con {addr}: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        log.info(f"Conexión cerrada: {addr}")


async def matchmaker(pipe):
    log.info("Matchmaker activo")
    while True:
        p1 = await waiting_queue.get()
        p2 = await waiting_queue.get()
        log.info(f"Partida: {p1.username} vs {p2.username}")
        asyncio.create_task(start_game(p1, p2, pipe))


async def main(pipe):
    global waiting_queue, pipe_lock
    waiting_queue = asyncio.Queue()
    pipe_lock     = asyncio.Lock()

    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, pipe),
        '0.0.0.0', 8888
    )
    log.info("Servidor escuchando en :8888")

    async with server:
        await asyncio.gather(
            server.serve_forever(),
            matchmaker(pipe)
        )


def run(pipe):
    asyncio.run(main(pipe))