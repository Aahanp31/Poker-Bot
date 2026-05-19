from poker_ai.mc_cpp import monte_carlo as _run

def _to_int(card):
    return (card.rank - 2) * 4 + card.suit

class MonteCarlo:
    def __init__(self, hole_cards, board, num_opponents):
        self.hole_cards    = hole_cards
        self.board         = board
        self.num_opponents = num_opponents
        self._hole         = [_to_int(c) for c in hole_cards]
        self._board        = [_to_int(c) for c in board]

    def simulate(self, num_sims=10000):
        return _run(self._hole, self._board, self.num_opponents, num_sims)

    def __repr__(self):
        return (f"MonteCarlo(hand={self.hole_cards}, "
                f"board={self.board}, opponents={self.num_opponents})")
