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
        self.alive = True
        self.matched = asyncio.Event()
        self.game_done = asyncio.Event()
        self.ready_for_game = asyncio.Event()
        
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

    while True:
        active  = players[current]
        waiting = players[1 - current]

        try:
            data = await active.reader.readline()
        except Exception:
            data = None

        if not data:
            log.info(f"{active.username} se desconectó durante la partida")
            try:
                await send_msg(waiting.writer, GAME_OVER, {
                    'result': 'win',
                    'reason': f'{active.username} se desconectó'
                })
            except Exception:
                pass
            await pipe_request(pipe, {
                'action': 'save_match',
                'player1_id': p1.user_id,
                'player2_id': p2.user_id,
                'winner_id': waiting.user_id,
                'duration_seconds': int(time.time() - start_time)
            })
            break

        try:
            msg_type, payload = decode_message(data)
        except Exception:
            await send_msg(active.writer, ERROR, {'message': 'Mensaje inválido'})
            continue

        if msg_type != MOVE:
            await send_msg(active.writer, ERROR, {'message': 'Se esperaba un movimiento'})
            continue

        col = payload.get('column')
        if not isinstance(col, int):
            await send_msg(active.writer, ERROR, {'message': 'Columna inválida'})
            continue

        success, _ = board.drop_piece(col, current + 1)
        if not success:
            await send_msg(active.writer, ERROR, {'message': 'Columna inválida o llena'})
            continue

        winner_num = board.check_winner()
        is_draw    = board.is_board_full()
        board_state = board.get_board_state()

        if winner_num or is_draw:
            winner_id = None
            if winner_num:
                winner_p = players[current]
                loser_p  = players[1 - current]
                winner_id = winner_p.user_id
                await send_msg(winner_p.writer, GAME_OVER, {'result': 'win',  'board': board_state})
                await send_msg(loser_p.writer,  GAME_OVER, {'result': 'loss', 'board': board_state})
                log.info(f"Ganador: {winner_p.username}")
            else:
                for p in players:
                    await send_msg(p.writer, GAME_OVER, {'result': 'draw', 'board': board_state})
                log.info("Empate")

            await pipe_request(pipe, {
                'action': 'save_match',
                'player1_id': p1.user_id,
                'player2_id': p2.user_id,
                'winner_id': winner_id,
                'duration_seconds': int(time.time() - start_time)
            })
            break

        # Cambiar turno y notificar a ambos
        current = 1 - current
        for i, p in enumerate(players):
            await send_msg(p.writer, BOARD_UPDATE, {
                'board': board_state,
                'your_turn': i == current,
                'player_num': i + 1
            })

    # Señalar a handle_client que la partida terminó
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

            # empareja el matchmaker o el cliente se desconecta
            disconnect_task = asyncio.create_task(reader.readline())
            match_task = asyncio.create_task(player.matched.wait())
            done, _ = await asyncio.wait(
                [disconnect_task, match_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            if match_task in done:
                # Cancelar la lectura para liberar el reader.
                disconnect_task.cancel()
                try:
                    await disconnect_task
                except (asyncio.CancelledError, Exception):
                    pass
                player.ready_for_game.set()       # avisar al matchmaker
                await player.game_done.wait()     # esperar fin de partida
            else:
                # Desconexión antes del emparejamiento
                match_task.cancel()
                player.alive = False
                player.ready_for_game.set()       # liberar al matchmaker si está esperando
                log.info(f"{username} se desconectó de la cola")
                
     
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

async def get_waiting_players():
    while True:
        p = await waiting_queue.get()
        if p.alive:
            return p
        log.info(f"{p.username} estaba desconectado, buscando otro jugador...")
        p.game_done.set()  # liberar al matchmaker si estaba esperando
        
async def matchmaker(pipe):
    log.info("Matchmaker activo")
    while True:
        p1 = await get_waiting_players()
        p2 = await get_waiting_players()
        
        p1.matched.set()
        p2.matched.set()
        
        await p1.ready_for_game.wait()
        await p2.ready_for_game.wait()
        
        if not p1.alive or not p2.alive:
            log.info("Un jugador se desconectó antes de iniciar la partida, buscando reemplazo...")
            for p in [p1, p2]:
                if p.alive:
                    p.matched.clear()
                    p.ready_for_game.clear()
                    await waiting_queue.put(p)
                else:
                    p.game_done.set()  # liberar al matchmaker si estaba esperando
            continue
        
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