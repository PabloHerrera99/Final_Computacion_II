import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from multiprocessing import Process, Pipe
from app.server import game_server, process_api


def main():
    # Un Pipe duplex es bidireccional: ambos extremos pueden enviar y recibir
    conn1, conn2 = Pipe()

    p1 = Process(target=game_server.run,  args=(conn1,), name='Proceso1-GameServer')
    p2 = Process(target=process_api.run,  args=(conn2,), name='Proceso2-APIBridge')

    p1.start()
    p2.start()

    print("[main] Servidor iniciado. Ctrl+C para detener.")

    try:
        p1.join()
        p2.join()
    except KeyboardInterrupt:
        print("\n[main] Deteniendo procesos...")
        p1.terminate()
        p2.terminate()
        p1.join()
        p2.join()
        print("[main] Listo.")


if __name__ == '__main__':
    main()