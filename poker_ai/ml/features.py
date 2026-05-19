import numpy as np

from poker_ai.equity.monte_carlo import MonteCarlo
from poker_ai.equity.ev_calculator import get_preflop_odds

_STREET_INT = {'preflop': 0, 'flop': 1, 'turn': 2, 'river': 3}
_STREETS    = ('preflop', 'flop', 'turn', 'river')

MAX_OPP_SLOTS = 8   # fixed opponent slots (padded with 0s if fewer players)

# 21 base features + 8 opponents × 4 streets × 2 values (action_code, bet_fraction)
FEATURE_DIM = 21 + MAX_OPP_SLOTS * 4 * 2   # = 85


def extract_features(player, gamestate, use_mc=False, mc_sims=500):
    """
    Encode game state + opponent action history into a float32 vector.

    Layout (85 values):
      [0-1]    hole card ranks       (rank-2)/12
      [2-3]    hole card suits       suit/3
      [4-8]    board ranks           (5 slots, 0-padded)
      [9-13]   board suits           (5 slots, 0-padded)
      [14]     street                preflop=0 .. river=1
      [15]     pot / total_chips
      [16]     stack / total_chips
      [17]     to_call / total_chips
      [18]     seat position from dealer / (num_players-1)
      [19]     active opponents / (num_players-1)
      [20]     equity                preflop table or Monte Carlo
      [21-84]  opponent history      8 slots × 4 streets × 2 values
                 each pair: (action_code/4, min(bet_fraction,3)/3)
                 action codes: 0=no action, 1=fold, 2=check, 3=call, 4=raise
    """
    gs  = gamestate
    out = np.zeros(FEATURE_DIM, dtype=np.float32)

    total_chips = sum(p.stack for p in gs.players) + gs.pot
    if total_chips == 0:
        total_chips = 1

    # ── Hole cards ────────────────────────────────────────────────────────────
    hole = player.hand
    out[0] = (hole[0].rank - 2) / 12.0
    out[1] = (hole[1].rank - 2) / 12.0
    out[2] = hole[0].suit / 3.0
    out[3] = hole[1].suit / 3.0

    # ── Board cards ───────────────────────────────────────────────────────────
    board = gs.board
    nb    = len(board)
    for i in range(nb):
        out[4 + i] = (board[i].rank - 2) / 12.0
        out[9 + i] =  board[i].suit      / 3.0

    # ── Game state scalars ────────────────────────────────────────────────────
    out[14] = _STREET_INT.get(gs.current_street, 0) / 3.0
    out[15] = gs.pot / total_chips
    out[16] = player.stack / total_chips
    out[17] = max(0, gs.current_bet - player.current_bet) / total_chips

    num_players = len(gs.players)
    denom       = max(num_players - 1, 1)
    hero_idx    = gs.players.index(player)
    out[18]     = ((hero_idx - gs.dealer_index) % num_players) / denom

    active  = gs.active_players()
    num_opp = len(active) - (0 if player.folded else 1)
    out[19] = num_opp / denom

    # ── Equity ────────────────────────────────────────────────────────────────
    if len(hole) == 2:
        if use_mc and nb > 0:
            r       = MonteCarlo(hole, board, max(num_opp, 1)).simulate(mc_sims)
            out[20] = r['win'] + r['tie'] * 0.5
        else:
            out[20] = get_preflop_odds(hole[0], hole[1])

    # ── Opponent action history ───────────────────────────────────────────────
    # Slots ordered clockwise from hero; unused slots stay 0
    for slot in range(MAX_OPP_SLOTS):
        base = 21 + slot * 8
        if slot >= num_players - 1:
            break
        opp_idx = (hero_idx + 1 + slot) % num_players
        opp_log = gs.action_log.get(opp_idx, {})
        for s, street in enumerate(_STREETS):
            entry = opp_log.get(street)
            if entry:
                action_code, bet_frac = entry
                out[base + s * 2]     = action_code / 4.0
                out[base + s * 2 + 1] = min(bet_frac, 3.0) / 3.0

    return out
