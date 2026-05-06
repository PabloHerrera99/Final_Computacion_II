from flask import Blueprint, request, jsonify
from app.api.database import get_db_connection

stats_bp = Blueprint('stats', __name__, url_prefix='/stats')

POINTS = {'win': 10, 'loss': 1, 'draw': 3}

@stats_bp.route('/update', methods=['POST'])
def update_stats():
    data = request.get_json()
    user_id = data.get('user_id')
    result = data.get('result')  # 'win', 'loss', 'draw'

    if not user_id or result not in ('win', 'loss', 'draw'):
        return jsonify({'error': 'user_id y result (win/loss/draw) requeridos'}), 400

    conn = get_db_connection()
    try:
        s = conn.execute('SELECT * FROM stats WHERE user_id = ?', (user_id,)).fetchone()
        if not s:
            return jsonify({'error': 'Stats no encontradas'}), 404

        wins   = s['wins']   + (1 if result == 'win'  else 0)
        losses = s['losses'] + (1 if result == 'loss' else 0)
        draws  = s['draws']  + (1 if result == 'draw' else 0)
        total  = s['total_matches'] + 1
        win_rate = wins / total
        current_streak = s['current_streak'] + 1 if result == 'win' else 0
        best_streak = max(s['best_streak'], current_streak)
        ranking_points = s['ranking_points'] + POINTS[result]

        conn.execute(
            '''UPDATE stats SET
               total_matches = ?, wins = ?, losses = ?, draws = ?,
               win_rate = ?, current_streak = ?, best_streak = ?,
               ranking_points = ?, updated_at = CURRENT_TIMESTAMP
               WHERE user_id = ?''',
            (total, wins, losses, draws, win_rate,
             current_streak, best_streak, ranking_points, user_id)
        )
        conn.commit()
        return jsonify({'ok': True}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@stats_bp.route('/ranking', methods=['GET'])
def get_ranking():
    conn = get_db_connection()
    try:
        rows = conn.execute(
            '''SELECT u.username, s.wins, s.losses, s.draws,
                      s.total_matches, s.win_rate, s.best_streak, s.ranking_points
               FROM stats s
               JOIN users u ON u.id = s.user_id
               ORDER BY s.ranking_points DESC
               LIMIT 10'''
        ).fetchall()
        ranking = [{'pos': i + 1, **dict(r)} for i, r in enumerate(rows)]
        return jsonify({'ranking': ranking}), 200
    finally:
        conn.close()

@stats_bp.route('/ranking/<username>', methods=['GET'])
def get_user_rank(username):
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        pos = conn.execute(
            '''SELECT COUNT(*) + 1 FROM stats
               WHERE ranking_points > (SELECT ranking_points FROM stats WHERE user_id = ?)''',
            (user['id'],)
        ).fetchone()[0]
        return jsonify({'username': username, 'position': pos}), 200
    finally:
        conn.close()

@stats_bp.route('/<username>', methods=['GET'])
def get_stats(username):
    conn = get_db_connection()
    try:
        row = conn.execute(
            '''SELECT s.* FROM stats s
               JOIN users u ON u.id = s.user_id
               WHERE u.username = ?''',
            (username,)
        ).fetchone()
        if not row:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        return jsonify(dict(row)), 200
    finally:
        conn.close()