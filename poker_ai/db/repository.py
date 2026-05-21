import sqlite3
from datetime import datetime


# This class handles all reads and writes to the poker SQLite database. It wraps
# a single connection and provides methods for recording sessions, hands, actions,
# and player results, plus queries for the frontend to display stats and history.
class Repository:

    def __init__(self, db_path='data/poker.db'):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys = ON')

    def close(self):
        self.conn.close()

    # This method creates a new session record and returns its id.
    # Parameters:
    #   - num_players: number of players at the table
    #   - big_blind: big blind chip amount
    # Returns:
    #   - int: the new session id
    def start_session(self, num_players, big_blind):
        cur = self.conn.execute(
            'INSERT INTO sessions (started_at, num_players, big_blind) VALUES (?, ?, ?)',
            (datetime.utcnow().isoformat(), num_players, big_blind),
        )
        self.conn.commit()
        return cur.lastrowid

    # This method records one completed hand and returns its id.
    # Parameters:
    #   - session_id: id of the current session
    #   - hand_num: sequential hand number within the session
    #   - result: dict with keys 'winner', 'pot', 'method'
    #   - street: street the hand ended on
    # Returns:
    #   - int: the new hand id
    def save_hand(self, session_id, hand_num, result, street):
        cur = self.conn.execute(
            'INSERT INTO hands (session_id, hand_num, winner, pot, method, street) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (session_id, hand_num, result['winner'],
             result['pot'], result['method'], street),
        )
        self.conn.commit()
        return cur.lastrowid

    # This method records every action taken in a hand.
    # Parameters:
    #   - hand_id: id of the hand these actions belong to
    #   - actions: list of dicts with keys 'player', 'street', 'action', 'amount'
    def save_actions(self, hand_id, actions):
        self.conn.executemany(
            'INSERT INTO actions (hand_id, player, street, action, amount) '
            'VALUES (?, ?, ?, ?, ?)',
            [(hand_id, a['player'], a['street'], a['action'], a['amount'])
             for a in actions],
        )
        self.conn.commit()

    # This method records each player's chip change for a hand.
    # Parameters:
    #   - hand_id: id of the hand
    #   - results: list of dicts with keys 'player', 'stack_start', 'stack_end'
    def save_results(self, hand_id, results):
        self.conn.executemany(
            'INSERT INTO results (hand_id, player, stack_start, stack_end, net) '
            'VALUES (?, ?, ?, ?, ?)',
            [(hand_id, r['player'], r['stack_start'], r['stack_end'],
              r['stack_end'] - r['stack_start']) for r in results],
        )
        self.conn.commit()

    # This method returns all hands for a session, newest first.
    # Parameters:
    #   - session_id: id of the session to query
    # Returns:
    #   - list[sqlite3.Row]: hand rows with id, hand_num, winner, pot, method, street
    def get_hands(self, session_id):
        return self.conn.execute(
            'SELECT * FROM hands WHERE session_id = ? ORDER BY hand_num DESC',
            (session_id,),
        ).fetchall()

    # This method returns all actions for a single hand.
    # Parameters:
    #   - hand_id: id of the hand to query
    # Returns:
    #   - list[sqlite3.Row]: action rows ordered by id (chronological)
    def get_actions(self, hand_id):
        return self.conn.execute(
            'SELECT * FROM actions WHERE hand_id = ? ORDER BY id',
            (hand_id,),
        ).fetchall()

    # This method returns win counts and net chips per player across a session.
    # Parameters:
    #   - session_id: id of the session to query
    # Returns:
    #   - list[sqlite3.Row]: rows with player, wins, total_net
    def get_session_stats(self, session_id):
        return self.conn.execute(
            '''
            SELECT
                r.player,
                COUNT(CASE WHEN h.winner = r.player THEN 1 END) AS wins,
                SUM(r.net) AS total_net
            FROM results r
            JOIN hands h ON h.id = r.hand_id
            WHERE h.session_id = ?
            GROUP BY r.player
            ORDER BY total_net DESC
            ''',
            (session_id,),
        ).fetchall()

    # This method returns a summary of all sessions.
    # Returns:
    #   - list[sqlite3.Row]: rows with id, started_at, num_players, big_blind, hand_count
    def get_all_sessions(self):
        return self.conn.execute(
            '''
            SELECT s.*, COUNT(h.id) AS hand_count
            FROM sessions s
            LEFT JOIN hands h ON h.session_id = s.id
            GROUP BY s.id
            ORDER BY s.id DESC
            '''
        ).fetchall()
