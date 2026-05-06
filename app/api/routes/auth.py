import hashlib
from flask import Blueprint, request, jsonify
from app.api.database import get_db_connection

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username y password requeridos'}), 400

    conn = get_db_connection()
    try:
        existing = conn.execute('SELECT id FROM users WHERE username = ?',
(username,)).fetchone()
        if existing:
            return jsonify({'error': 'El usuario ya existe'}), 409

        cursor = conn.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, hash_password(password))
        )
        user_id = cursor.lastrowid
        conn.execute('INSERT INTO stats (user_id) VALUES (?)', (user_id,))
        conn.commit()
        return jsonify({'user_id': user_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username y password requeridos'}), 400

    conn = get_db_connection()
    try:
        user = conn.execute(
            'SELECT id, password_hash FROM users WHERE username = ?', (username,)
        ).fetchone()

        if not user or user['password_hash'] != hash_password(password):
            return jsonify({'error': 'Credenciales inválidas'}), 401

        return jsonify({'user_id': user['id']}), 200
    finally:
        conn.close()
          