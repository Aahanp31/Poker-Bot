import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from poker_ai.core.game_state import Player
from poker_ai.db.schema import init_db
from poker_ai.db.repository import Repository
from poker_ai.sim.simulator import Simulator

DB_PATH     = os.environ.get('POKER_DB', 'data/poker.db')
ACTION_NAMES = {1: 'fold', 2: 'check', 3: 'call', 4: 'raise'}

app = FastAPI(title='Poker AI')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
def startup():
    os.makedirs('data', exist_ok=True)
    init_db(DB_PATH)


def repo():
    r = Repository(DB_PATH)
    try:
        yield r
    finally:
        r.close()


# This endpoint returns all sessions with hand counts.
# Returns:
#   - list of session objects: id, started_at, num_players, big_blind, hand_count
@app.get('/api/sessions')
def list_sessions():
    r = Repository(DB_PATH)
    rows = r.get_all_sessions()
    r.close()
    return [dict(row) for row in rows]


# This endpoint returns player stats for a session.
# Parameters:
#   - session_id: id of the session
# Returns:
#   - list of stat objects: player, wins, total_net
@app.get('/api/sessions/{session_id}/stats')
def session_stats(session_id: int):
    r = Repository(DB_PATH)
    rows = r.get_session_stats(session_id)
    r.close()
    if not rows:
        raise HTTPException(status_code=404, detail='Session not found')
    return [dict(row) for row in rows]


# This endpoint returns all hands in a session.
# Parameters:
#   - session_id: id of the session
# Returns:
#   - list of hand objects: id, hand_num, winner, pot, method, street
@app.get('/api/sessions/{session_id}/hands')
def session_hands(session_id: int):
    r = Repository(DB_PATH)
    rows = r.get_hands(session_id)
    r.close()
    return [dict(row) for row in rows]


# This endpoint returns all actions for a single hand.
# Parameters:
#   - hand_id: id of the hand
# Returns:
#   - list of action objects: player, street, action, amount
@app.get('/api/hands/{hand_id}/actions')
def hand_actions(hand_id: int):
    r = Repository(DB_PATH)
    rows = r.get_actions(hand_id)
    r.close()
    return [dict(row) for row in rows]


class RunConfig(BaseModel):
    num_players:    int = 3
    big_blind:      int = 20
    num_hands:      int = 50
    starting_stack: int = 1000


# This endpoint runs a session of num_hands hands, saves everything to the
# database, and returns the new session id.
# Parameters (body):
#   - num_players: number of players at the table
#   - big_blind: big blind chip amount
#   - num_hands: number of hands to simulate
#   - starting_stack: starting chips per player
# Returns:
#   - dict: { session_id, hands }
@app.post('/api/run')
def run_session(config: RunConfig):
    players = [Player(f'P{i}', config.starting_stack)
               for i in range(config.num_players)]
    sim = Simulator(players, config.big_blind)
    r   = Repository(DB_PATH)

    session_id = r.start_session(config.num_players, config.big_blind)

    for hand_num in range(1, config.num_hands + 1):
        gs           = sim.gamestate
        start_stacks = {p.name: p.stack for p in gs.players}

        # reset stacks so players never bust mid-session
        for p in gs.players:
            p.stack = config.starting_stack

        start_stacks = {p.name: p.stack for p in gs.players}
        result       = sim.simulate_hand()

        hand_id = r.save_hand(
            session_id, hand_num, result,
            gs.current_street or 'preflop',
        )

        actions = []
        for p_idx, street_log in gs.action_log.items():
            p_name = gs.players[p_idx].name
            for street, (code, _) in street_log.items():
                actions.append({
                    'player': p_name,
                    'street': street,
                    'action': ACTION_NAMES.get(code, 'unknown'),
                    'amount': 0,
                })
        r.save_actions(hand_id, actions)

        results = [{
            'player':      p.name,
            'stack_start': start_stacks[p.name],
            'stack_end':   p.stack,
        } for p in gs.players]
        r.save_results(hand_id, results)

    r.close()
    return {'session_id': session_id, 'hands': config.num_hands}
