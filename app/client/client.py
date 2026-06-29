import sys
import os
import socket
import argparse
import select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.common.protocol import (
    encode_message, decode_message,
    AUTH_REQUEST, REGISTER_REQUEST, PLAY_REQUEST,
    MOVE, HISTORY_REQUEST, RANKING_REQUEST,
    AUTH_RESPONSE, BOARD_UPDATE, GAME_OVER,
    HISTORY_RESPONSE, RANKING_RESPONSE, ERROR, WAITING
)


def send_msg(sock, msg_type, payload=None):
    sock.sendall(encode_message(msg_type, payload or {}))


def recv_msg(sock_file):
    line = sock_file.readline()
    if not line:
        raise ConnectionError("Servidor desconectado")
    return decode_message(line)


# Descarta input acumulado en stdin mientras se esperaba turno.
def drain_stdin():
    while select.select([sys.stdin], [], [], 0)[0]:
        sys.stdin.readline()


def render_board(board_state, player_num):
    symbols = {0: '·', 1: '●', 2: '○'}
    my_sym  = symbols[player_num]
    opp_sym = symbols[2 if player_num == 1 else 1]
    lines = [
        f"\n  Vos: {my_sym}   Oponente: {opp_sym}\n",
        "   1 2 3 4 5 6 7",
        " ┌───────────────┐",
    ]
    for row in board_state:
        lines.append(" │ " + " ".join(symbols[cell] for cell in row) + " │")
    lines.append(" └───────────────┘")
    return "\n".join(lines)


def ask_column():
    while True:
        try:
            col = int(input("  Tu columna (1-7): "))
            if 1 <= col <= 7:
                return col - 1  # el protocolo usa índice 0
            print("  Ingresa un número entre 1 y 7.")
        except ValueError:
            print("  Ingresa un número.")


def play_game(sock, sock_file):
    send_msg(sock, PLAY_REQUEST)
    player_num = None
    your_turn  = False

    while True:
        msg_type, payload = recv_msg(sock_file)

        if msg_type == WAITING:
            print(f"\n[...] {payload.get('message', 'Esperando oponente...')}")

        elif msg_type == BOARD_UPDATE:
            if player_num is None:
                player_num = payload.get('player_num', 1)
                opponent   = payload.get('opponent', '?')
                print(f"\n--- Partida iniciada contra {opponent} ---")

            board     = payload.get('board')
            your_turn = payload.get('your_turn', False)
            print(render_board(board, player_num))

            if your_turn:
                drain_stdin()
                print("  *** Tu turno ***")
                send_msg(sock, MOVE, {'column': ask_column()})
            else:
                print("  Esperando jugada del oponente...")

        elif msg_type == ERROR:
            print(f"  [!] {payload.get('message')}")
            if your_turn:
                drain_stdin()
                send_msg(sock, MOVE, {'column': ask_column()})

        elif msg_type == GAME_OVER:
            result = payload.get('result')
            board  = payload.get('board')
            reason = payload.get('reason', '')

            if board and player_num:
                print(render_board(board, player_num))

            msgs = {'win': 'Ganaste!', 'loss': 'Perdiste.', 'draw': 'Empate.'}
            print(f"\n=== {msgs.get(result, 'Fin de partida')} ===")
            if reason:
                print(f"    ({reason})")
            break

        else:
            print(f"[?] Mensaje inesperado: {msg_type}")
            break


def show_history(sock, sock_file):
    send_msg(sock, HISTORY_REQUEST, {'page': 1})
    msg_type, payload = recv_msg(sock_file)

    if msg_type != HISTORY_RESPONSE or not payload.get('ok'):
        print(f"[!] {payload.get('error', 'Error al obtener historial')}")
        return

    matches = payload.get('matches', [])
    if not matches:
        print("\nSin partidas registradas.")
        return

    print(f"\n{'#':<5} {'Jugador 1':<15} {'Jugador 2':<15} {'Ganador':<15} {'Seg':<6} Fecha")
    print("─" * 72)
    for i, m in enumerate(matches, 1):
        winner   = m.get('winner') or 'Empate'
        duration = f"{m.get('duration_seconds') or 0}s"
        date     = (m.get('played_at') or '')[:16]
        print(f"{i:<5} {m['player1']:<15} {m['player2']:<15} {winner:<15} {duration:<6} {date}")

    print(f"\nTotal: {payload.get('total', 0)} partida(s)")


def show_ranking(sock, sock_file):
    send_msg(sock, RANKING_REQUEST)
    msg_type, payload = recv_msg(sock_file)

    if msg_type != RANKING_RESPONSE or not payload.get('ok'):
        print(f"[!] {payload.get('error', 'Error al obtener ranking')}")
        return

    ranking = payload.get('ranking', [])
    if not ranking:
        print("\nRanking vacío.")
        return

    print(f"\n{'Pos':<5} {'Jugador':<15} {'Puntos':<9} {'V':<5} {'D':<5} {'E':<5} Win%")
    print("─" * 52)
    for r in ranking:
        win_pct = f"{r.get('win_rate', 0) * 100:.0f}%"
        print(f"{r['pos']:<5} {r['username']:<15} {r['ranking_points']:<9} "
              f"{r['wins']:<5} {r['losses']:<5} {r['draws']:<5} {win_pct}")


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='Cliente Cuatro en Linea')
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-a', '--action', required=True, choices=['jugar', 'historial', 'ranking'])
    parser.add_argument('-i', '--ip', required=True)
    parser.add_argument('--port', type=int, default=8888)
    return parser.parse_args()


def connect(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    return sock, sock.makefile('rb')


def authenticate(args):
    sock, sock_file = connect(args.ip, args.port)
    send_msg(sock, AUTH_REQUEST, {'username': args.username, 'password': args.password})
    _, payload = recv_msg(sock_file)

    if payload.get('ok'):
        print(f"[OK] Bienvenido, {args.username}!")
        return sock, sock_file

    print(f"[!] Login fallido: {payload.get('error', '')}")
    sock.close()

    resp = input("El usuario no existe o la contrasena es incorrecta. Registrarse? (s/n): ").strip().lower()
    if resp != 's':
        return None, None

    sock, sock_file = connect(args.ip, args.port)
    send_msg(sock, REGISTER_REQUEST, {'username': args.username, 'password': args.password})
    _, payload = recv_msg(sock_file)

    if payload.get('ok'):
        print(f"[OK] Registro exitoso. Bienvenido, {args.username}!")
        return sock, sock_file

    print(f"[!] Error al registrarse: {payload.get('error', '')}")
    sock.close()
    return None, None


def main():
    args = parse_args()

    try:
        sock, sock_file = authenticate(args)
    except ConnectionRefusedError:
        print(f"[!] No se pudo conectar a {args.ip}:{args.port}. El servidor esta corriendo?")
        sys.exit(1)

    if not sock:
        sys.exit(1)

    try:
        if args.action == 'jugar':
            play_game(sock, sock_file)
        elif args.action == 'historial':
            show_history(sock, sock_file)
        elif args.action == 'ranking':
            show_ranking(sock, sock_file)
    except ConnectionError as e:
        print(f"\n[!] Conexion perdida: {e}")
    except KeyboardInterrupt:
        print("\n[!] Saliendo...")
    finally:
        sock.close()


if __name__ == '__main__':
    main()