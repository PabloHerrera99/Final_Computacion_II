from flask import Blueprint, request, jsonify
from app.api.database import get_db_connection

matches_bp = Blueprint('matches', __name__, url_prefix='/matches')

@matches_bp.route('', methods=['POST'])
def create_match():
    data = request.get_json()
    player1_id = data.get('player1_id')
    player2_id = data.get('player2_id')
    winner_id = data.get('winner_id')       # None si empate
    duration_seconds = data.get('duration_seconds')

    if not player1_id or not player2_id:
        return jsonify({'error': 'player1_id y player2_id requeridos'}), 400

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            'INSERT INTO matches (player1_id, player2_id, winner_id, duration_seconds) VALUES (?,?, ?, ?)',
        (player1_id, player2_id, winner_id, duration_seconds)
        )
        
        conn.commit()
        return jsonify({'match_id': cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@matches_bp.route('', methods=['GET'])
def get_matches():
    user_id = request.args.get('user_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    if not user_id:
        return jsonify({'error': 'user_id requerido'}), 400

    conn = get_db_connection()
    try:
        total = conn.execute(
            'SELECT COUNT(*) FROM matches WHERE player1_id = ? OR player2_id = ?',
            (user_id, user_id)
        ).fetchone()[0]

        rows = conn.execute(
            '''SELECT m.id, m.played_at, m.duration_seconds,
                      u1.username AS player1, u2.username AS player2,
                      uw.username AS winner
               FROM matches m
               JOIN users u1 ON u1.id = m.player1_id
               JOIN users u2 ON u2.id = m.player2_id
               LEFT JOIN users uw ON uw.id = m.winner_id
               WHERE m.player1_id = ? OR m.player2_id = ?
               ORDER BY m.played_at DESC
               LIMIT ? OFFSET ?''',
            (user_id, user_id, per_page, offset)
        ).fetchall()

        return jsonify({
            'matches': [dict(r) for r in rows],
            'total': total,
            'page': page,
            'pages': (total + per_page - 1) // per_page
        }), 200
    finally:
        conn.close()