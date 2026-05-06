import requests
import logging

logging.basicConfig(level=logging.INFO, format='[Proceso2] %(message)s')
log = logging.getLogger(__name__)

API_BASE = 'http://localhost:5000'


def handle_login(data):
    try:
        r = requests.post(f'{API_BASE}/auth/login', json={
            'username': data['username'],
            'password': data['password']
        }, timeout=5)
        body = r.json()
        if r.status_code == 200:
            return {'ok': True, 'user_id': body['user_id']}
        return {'ok': False, 'error': body.get('error', 'Error de login')}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def handle_register(data):
    try:
        r = requests.post(f'{API_BASE}/auth/register', json={
            'username': data['username'],
            'password': data['password']
        }, timeout=5)
        body = r.json()
        if r.status_code == 201:
            return {'ok': True, 'user_id': body['user_id']}
        return {'ok': False, 'error': body.get('error', 'Error de registro')}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def handle_save_match(data):
    try:
        player1_id     = data['player1_id']
        player2_id     = data['player2_id']
        winner_id      = data.get('winner_id')       # None si empate
        duration_secs  = data.get('duration_seconds')

        r = requests.post(f'{API_BASE}/matches', json={
            'player1_id': player1_id,
            'player2_id': player2_id,
            'winner_id': winner_id,
            'duration_seconds': duration_secs
        }, timeout=5)

        if r.status_code != 201:
            return {'ok': False, 'error': 'Error al guardar partida'}
        
        match_id = r.json()['match_id']

        # Actualizar stats de ambos jugadores
        if winner_id is None:
            for uid in [player1_id, player2_id]:
                requests.post(f'{API_BASE}/stats/update',
                              json={'user_id': uid, 'result': 'draw'}, timeout=5)
        else:
            loser_id = player2_id if winner_id == player1_id else player1_id
            requests.post(f'{API_BASE}/stats/update',
                          json={'user_id': winner_id, 'result': 'win'}, timeout=5)
            requests.post(f'{API_BASE}/stats/update',
                          json={'user_id': loser_id, 'result': 'loss'}, timeout=5)

        return {'ok': True, 'match_id': match_id}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def handle_history(data):
    try:
        r = requests.get(f'{API_BASE}/matches', params={
            'user_id': data['user_id'],
            'page': data.get('page', 1)
        }, timeout=5)
        if r.status_code == 200:
            return {'ok': True, **r.json()}
        return {'ok': False, 'error': 'Error al obtener historial'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def handle_ranking(_data):
    try:
        r = requests.get(f'{API_BASE}/stats/ranking', timeout=5)
        if r.status_code == 200:
            return {'ok': True, **r.json()}
        return {'ok': False, 'error': 'Error al obtener ranking'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}




HANDLERS = {
    'login':      handle_login,
    'register':   handle_register,
    'save_match': handle_save_match,
    'history':    handle_history,
    'ranking':    handle_ranking,
}

def run(pipe):
    log.info("Iniciado, esperando mensajes...")
    while True:
        try:
            message = pipe.recv()
            action = message.get('action')
            log.info(f"Acción recibida: {action}")

            handler = HANDLERS.get(action)
            if handler:
                response = handler(message)
            else:
                response = {'ok': False, 'error': f'Acción desconocida: {action}'}
                
            pipe.send(response)

        except EOFError:
            log.info("Pipe cerrado, terminando.")
            break
        except Exception as e:
            log.error(f"Error inesperado: {e}")
            try:
                pipe.send({'ok': False, 'error': str(e)})
            except Exception:
                break