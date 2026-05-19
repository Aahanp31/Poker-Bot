from treys import Evaluator as _TreysEvaluator
from treys import Card as _TreysCard

from .cards import RANKS, SUITS, RANK_NAMES

_evaluator = _TreysEvaluator()

_SUIT_MAP = {0: 'h', 1: 'd', 2: 'c', 3: 's'}

# Precomputed lookup: our card int (rank*4+suit, rank 0-based) -> treys int
# Avoids string formatting on every evaluation call
_TO_TREYS = {
    (r, s): _TreysCard.new(f'{RANK_NAMES[r]}{_SUIT_MAP[s]}')
    for r in RANKS
    for s in SUITS
}

HAND_NAMES = {
    0: 'High Card',     1: 'One Pair',      2: 'Two Pair',
    3: 'Three of a Kind', 4: 'Straight',    5: 'Flush',
    6: 'Full House',    7: 'Four of a Kind', 8: 'Straight Flush',
    9: 'Royal Flush',
}

_TREYS_TO_RANK = {0: 9, 1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1, 9: 0}


def evaluate(hole_cards, board):
    t_hand  = [_TO_TREYS[(c.rank, c.suit)] for c in hole_cards]
    t_board = [_TO_TREYS[(c.rank, c.suit)] for c in board]
    return _evaluator.evaluate(t_board, t_hand)


def get_hand_rank(hole_cards, board):
    return _TREYS_TO_RANK[_evaluator.get_rank_class(evaluate(hole_cards, board))]


def get_hand_name(hole_cards, board):
    return HAND_NAMES[get_hand_rank(hole_cards, board)]


def compare_hands(hole_a, hole_b, board):
    score_a = evaluate(hole_a, board)
    score_b = evaluate(hole_b, board)
    if score_a < score_b: return  1   # lower treys score = better
    if score_a > score_b: return -1
    return 0
