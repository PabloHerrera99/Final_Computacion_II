import sqlite3
from app.api.config import DATABASE_PATH, SCHEMA_PATH

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  
    return conn

def init_database():
    try:
        with open(SCHEMA_PATH, 'r') as f:
            schema_sql = f.read()

        conn = get_db_connection()
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        
        print("[OK] Base de datos inicializada correctamente")
        return True
    
    except Exception as e:
        print(f"[ERROR] Error al inicializar la base de datos: {e}")
        return False
    
def close_db_connection(conn):
    if conn:
        conn.close()