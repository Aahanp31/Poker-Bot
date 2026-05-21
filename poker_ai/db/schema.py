import sqlite3


# This module creates and manages the SQLite database schema. It defines four
# tables: sessions, hands, actions, and players. Call init_db() once at startup
# to create the tables if they don't already exist.

CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT    NOT NULL,
    num_players INTEGER NOT NULL,
    big_blind   INTEGER NOT NULL
);
"""

CREATE_HANDS = """
CREATE TABLE IF NOT EXISTS hands (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    hand_num   INTEGER NOT NULL,
    winner     TEXT    NOT NULL,
    pot        INTEGER NOT NULL,
    method     TEXT    NOT NULL,   -- 'fold' or 'showdown'
    street     TEXT    NOT NULL    -- street when hand ended
);
"""

CREATE_ACTIONS = """
CREATE TABLE IF NOT EXISTS actions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    hand_id    INTEGER NOT NULL REFERENCES hands(id),
    player     TEXT    NOT NULL,
    street     TEXT    NOT NULL,
    action     TEXT    NOT NULL,   -- 'fold', 'check', 'call', 'raise'
    amount     INTEGER NOT NULL
);
"""

CREATE_RESULTS = """
CREATE TABLE IF NOT EXISTS results (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    hand_id    INTEGER NOT NULL REFERENCES hands(id),
    player     TEXT    NOT NULL,
    stack_start INTEGER NOT NULL,
    stack_end   INTEGER NOT NULL,
    net         INTEGER NOT NULL   -- stack_end - stack_start
);
"""


# This function creates all tables in the database if they don't already exist.
# Parameters:
#   - db_path: path to the SQLite database file (created if missing)
def init_db(db_path='data/poker.db'):
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute(CREATE_SESSIONS)
    conn.execute(CREATE_HANDS)
    conn.execute(CREATE_ACTIONS)
    conn.execute(CREATE_RESULTS)
    conn.commit()
    conn.close()
