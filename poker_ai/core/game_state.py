STREET_NEXT = {
    None:      'preflop',
    'preflop': 'flop',
    'flop':    'turn',
    'turn':    'river',
}


# This class represents a player at the poker table. It tracks their hole cards,
# chip stack, current bet amount, and whether they have folded this hand.
class Player:
    __slots__ = ('name', 'hand', 'stack', 'current_bet', 'folded')

    def __init__(self, name, stack):
        self.name        = name
        self.hand        = []
        self.stack       = stack
        self.current_bet = 0
        self.folded      = False

    def set_hand(self, cards):
        self.hand = cards

    def reset_hand(self):
        self.hand        = []
        self.current_bet = 0
        self.folded      = False

    def can_check(self, gamestate):
        return self.current_bet >= gamestate.current_bet

    # This method places a bet by deducting chips from the player's stack.
    # Parameters:
    #   - amount: intended number of chips to bet
    # Returns:
    #   - int: actual chips deducted (capped at remaining stack)
    def bet(self, amount):
        bet_amount = min(amount, self.stack)
        self.stack       -= bet_amount
        self.current_bet += bet_amount
        return bet_amount

    # This method raises the current bet by the given total amount. Enforces that
    # the raise is at least one big blind above the call amount.
    # Parameters:
    #   - amount: total additional chips to put in
    #   - gamestate: current Gamestate to read call amount and blind size
    # Returns:
    #   - int: actual chips deducted
    # Exceptions:
    #   - amount < call_amt + big_blind: raises ValueError if raise is too small
    def bet_raise(self, amount, gamestate):
        call_amt = gamestate.current_bet - self.current_bet
        if amount >= call_amt + gamestate.big_blind_amount:
            return self.bet(amount)
        raise ValueError("Raise too small — must be at least call + one big blind.")

    # This method calls the current bet by putting in the exact amount needed to match it.
    # Parameters:
    #   - gamestate: current Gamestate to read the required bet from
    # Returns:
    #   - int: chips deducted
    def call_bet(self, gamestate):
        return self.bet(gamestate.current_bet - self.current_bet)

    def fold(self):
        self.folded = True

    def __repr__(self):
        if self.folded:
            return f"{self.name} (folded)"
        if self.hand:
            return f"{self.name} [{self.hand[0]} {self.hand[1]}] ${self.stack}"
        return f"{self.name} ${self.stack}"


# This class tracks the complete state of a poker hand in progress. It holds all
# players, board cards, pot size, betting levels, dealer position, and a per-player
# action log keyed by street.
class Gamestate:
    def __init__(self, big_blind_amount, small_blind_amount=None):
        self.players          = []
        self.board            = []
        self.pot              = 0
        self.current_bet      = 0
        self.player_index     = 0
        self.big_blind_amount = big_blind_amount
        self.small_blind_amount = (
            small_blind_amount if small_blind_amount is not None
            else big_blind_amount >> 1
        )
        self.dealer_index    = 0
        self.current_street  = None
        # action_log[player_idx][street] = (action_code, bet_fraction)
        # action_code: 1=fold  2=check  3=call  4=raise
        # bet_fraction: chips_put_in / pot_before_action
        self.action_log: dict = {}

    def add_player(self, player):
        if len(self.players) < 9:
            self.players.append(player)

    def active_players(self):
        return [p for p in self.players if not p.folded]

    def players_who_can_act(self):
        return [p for p in self.players if not p.folded and p.stack > 0]

    def set_board(self, cards):
        self.board = cards

    # This method posts the small and big blinds from the players in those seats.
    def post_blinds(self):
        num       = len(self.players)
        sb_player = self.players[(self.dealer_index + 1) % num]
        bb_player = self.players[(self.dealer_index + 2) % num]

        sb = min(sb_player.stack, self.small_blind_amount)
        sb_player.stack       -= sb
        sb_player.current_bet  = sb

        bb = min(bb_player.stack, self.big_blind_amount)
        bb_player.stack       -= bb
        bb_player.current_bet  = bb

        self.pot         = sb + bb
        self.current_bet = bb

    # This method clears board, pot, bets, and action log then advances the dealer button.
    def reset_round(self):
        self.board          = []
        self.pot            = 0
        self.current_bet    = 0
        self.player_index   = 0
        self.current_street = None
        self.action_log     = {}
        self.dealer_index   = (self.dealer_index + 1) % len(self.players)
        for player in self.players:
            player.reset_hand()

    # This method deals two hole cards to every player from the given deck.
    # Parameters:
    #   - deck: Deck to deal from
    def deal_hands(self, deck):
        for player in self.players:
            player.set_hand(deck.deal(2))

    # This method burns one card and deals community cards for the given stage.
    # Parameters:
    #   - deck: Deck to deal from
    #   - stage: 'flop' deals 3 cards; 'turn' and 'river' deal 1
    def deal_board(self, deck, stage):
        deck.burn()
        if stage == 'flop':
            self.board.extend(deck.deal(3))
        else:
            self.board.append(deck.deal_one())

    # This method moves to the next street and resets per-street bet tracking.
    def advance_street(self):
        self.current_street = STREET_NEXT.get(self.current_street)
        self.current_bet    = 0
        for player in self.players:
            player.current_bet = 0

    # This method records a player's most recent action for the current street.
    # Parameters:
    #   - player_idx: index in self.players
    #   - action_code: 1=fold 2=check 3=call 4=raise
    #   - amount: chips put in this action
    #   - pot_before: pot size before the action (used to normalize bet size)
    def log_action(self, player_idx, action_code, amount, pot_before):
        frac = amount / pot_before if pot_before > 0 else 0.0
        self.action_log.setdefault(player_idx, {})[self.current_street] = (action_code, frac)

    def __repr__(self):
        street = self.current_street or 'waiting'
        board  = ' '.join(repr(c) for c in self.board) or '-'
        return f"[{street}] Board: {board} | Pot: ${self.pot}"
