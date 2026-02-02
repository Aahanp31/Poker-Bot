import random

from treys import Evaluator as _TreysEvaluator
from treys import Card as _TreysCard

from poker_ai.core.cards import SUITS, RANKS, RANK_NAMES

# Singleton evaluator + suit map (same as hand_evaluator)
_evaluator = _TreysEvaluator()

_SUIT_MAP = {
    0: 'h',
    1: 'd',
    2: 'c',
    3: 's',
}

# Pre-build full 52-card deck as treys ints (built once at import)
_ALL_TREYS = [
    _TreysCard.new(f'{RANK_NAMES[r]}{_SUIT_MAP[s]}')
    for r in RANKS
    for s in SUITS
]


def _to_treys(card):
    # Convert our Card to treys int
    return _TreysCard.new(f'{RANK_NAMES[card.rank]}{_SUIT_MAP[card.suit]}')


class MonteCarlo:
    def __init__(self, hole_cards, board, num_opponents):
        self.hole_cards = hole_cards
        self.board = board
        self.num_opponents = num_opponents

        # Convert known cards to treys ints once
        self.t_hole = [_to_treys(c) for c in hole_cards]
        self.t_board = [_to_treys(c) for c in board]

        # Build remaining deck as treys ints (exclude known cards)
        known = set(self.t_hole + self.t_board)
        self.t_remaining = [c for c in _ALL_TREYS if c not in known]

    # Run num_sims simulations, return win/tie/loss rates
    def simulate(self, num_sims):
        wins = 0
        ties = 0
        losses = 0

        board_len = len(self.t_board)
        board_need = 5 - board_len
        cards_needed = board_need + (self.num_opponents * 2)

        # Cache references for speed in hot loop
        t_hole = self.t_hole
        t_board = self.t_board
        t_remaining = self.t_remaining
        ev = _evaluator.evaluate

        for _ in range(num_sims):
            sampled = random.sample(t_remaining, cards_needed)

            # Complete the board
            sim_board = t_board + sampled[:board_need]

            # Evaluate our hand
            my_score = ev(sim_board, t_hole)

            # Evaluate each opponent, track best score
            best_opp = 7463  # worst possible treys score
            i = board_need
            for _ in range(self.num_opponents):
                opp_hole = sampled[i:i + 2]
                opp_score = ev(sim_board, opp_hole)
                if opp_score < best_opp:
                    best_opp = opp_score
                i += 2

            # Compare (lower = better in treys)
            if my_score < best_opp:
                wins += 1
            elif my_score == best_opp:
                ties += 1
            else:
                losses += 1

        return {
            'win': wins / num_sims,
            'tie': ties / num_sims,
            'loss': losses / num_sims,
        }

    def __repr__(self):
        return (
            f"MonteCarlo(hand={self.hole_cards}, "
            f"board={self.board}, opponents={self.num_opponents})"
        )
