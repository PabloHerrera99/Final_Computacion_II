import json

  
  # Cliente → Servidor
AUTH_REQUEST     = "AUTH_REQUEST"
REGISTER_REQUEST = "REGISTER_REQUEST"
PLAY_REQUEST     = "PLAY_REQUEST"
MOVE             = "MOVE"
HISTORY_REQUEST  = "HISTORY_REQUEST"
RANKING_REQUEST  = "RANKING_REQUEST"

  # Servidor → Cliente
AUTH_RESPONSE    = "AUTH_RESPONSE"
BOARD_UPDATE     = "BOARD_UPDATE"
GAME_OVER        = "GAME_OVER"
HISTORY_RESPONSE = "HISTORY_RESPONSE"
RANKING_RESPONSE = "RANKING_RESPONSE"
ERROR            = "ERROR"
WAITING          = "WAITING"


# --- Funciones de serialización ---

# Construye un mensaje y lo devuelve como bytes listos para enviar por socket.
def encode_message(msg_type, payload=None):
   message = {
       "type": msg_type,
       "payload": payload or {}
   }
   return (json.dumps(message) + "\n").encode("utf-8")

# Recibe bytes o string, devuelve (msg_type, payload).
def decode_message(data):

   if isinstance(data, bytes):
       data = data.decode("utf-8")
   message = json.loads(data.strip())
   return message["type"], message["payload"]