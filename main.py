import random

SUITS = (0, 1, 2, 3)  # 0=Hearts, 1=Diamonds, 2=Clubs, 3=Spades
RANKS = tuple(range(2, 15))
STREET_NEXT = {None: 'preflop', 'preflop': 'flop', 'flop': 'turn', 'turn': 'river'}
SUIT_NAMES = ('H', 'D', 'C', 'S')
RANK_NAMES = {2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8',
              9: '9', 10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'}


class Card:
    __slots__ = ('rank', 'suit')

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"{RANK_NAMES[self.rank]}{SUIT_NAMES[self.suit]}"


# Pre-build a master deck as a tuple so reset just copies it
_MASTER_DECK = tuple(Card(r, s) for r in RANKS for s in SUITS)


class Deck:
    __slots__ = ('cards',)

    # Build shuffled 52-card deck from cached master copy
    def __init__(self):
        self.cards = list(_MASTER_DECK)
        random.shuffle(self.cards)

    # Pop and return a single card from the top
    def deal_one(self):
        return self.cards.pop()

    # Deal num cards from the top and return as list
    def deal(self, num):
        dealt = self.cards[-num:]
        del self.cards[-num:]
        return dealt

    # Discard top card (burn before community cards)
    def burn(self):
        self.cards.pop()

    # Rebuild and reshuffle the full 52-card deck
    def reset(self):
        self.cards = list(_MASTER_DECK)
        random.shuffle(self.cards)


class Player:
    __slots__ = ('name', 'hand', 'stack', 'current_bet', 'folded')

    def __init__(self, name, stack):
        self.name = name
        self.hand = []
        self.stack = stack
        self.current_bet = 0
        self.folded = False

    # Assign dealt cards as the player's hole cards
    def set_hand(self, cards):
        self.hand = cards

    # Clear hand and reset bet/fold state for a new round
    def reset_hand(self):
        self.hand = []
        self.current_bet = 0
        self.folded = False

    # Place a bet, capped at remaining stack (handles all-in)
    def bet(self, amount):
        bet_amount = min(amount, self.stack)
        self.stack -= bet_amount
        self.current_bet += bet_amount
        return bet_amount

    # Raise by amount; must be at least 2x the call amount
    def bet_raise(self, amount, gamestate):
        min_raise = gamestate.current_bet - self.current_bet
        if amount >= 2 * min_raise:
            return self.bet(amount)
        raise ValueError("Raise must be at least double the current bet to call.")

    # Match the current bet
    def call_bet(self, gamestate):
        return self.bet(gamestate.current_bet - self.current_bet)

    # Mark player as folded
    def fold(self):
        self.folded = True

    def __repr__(self):
        if self.folded:
            return f"{self.name} (folded)"
        if self.hand:
            return f"{self.name} [{self.hand[0]} {self.hand[1]}] ${self.stack}"
        return f"{self.name} ${self.stack}"


class Gamestate:
    def __init__(self, big_blind_amount, small_blind_amount=None):
        self.players = []
        self.board = []
        self.pot = 0
        self.current_bet = 0
        self.player_index = 0
        self.big_blind_amount = big_blind_amount
        self.small_blind_amount = small_blind_amount if small_blind_amount is not None else big_blind_amount >> 1
        self.dealer_index = 0
        self.current_street = None

    # Add a player to the table (max 8)
    def add_player(self, player):
        if len(self.players) < 8:
            self.players.append(player)

    # Manually set the community board cards
    def set_board(self, cards):
        self.board = cards

    # Deduct blinds from SB/BB players and seed the pot
    def post_blinds(self):
        num = len(self.players)
        sb_player = self.players[(self.dealer_index + 1) % num]
        bb_player = self.players[(self.dealer_index + 2) % num]

        sb = min(sb_player.stack, self.small_blind_amount)
        sb_player.stack -= sb
        sb_player.current_bet = sb

        bb = min(bb_player.stack, self.big_blind_amount)
        bb_player.stack -= bb
        bb_player.current_bet = bb

        self.pot = sb + bb
        self.current_bet = bb

    # Reset state for a new round and rotate dealer
    def reset_round(self):
        self.board = []
        self.pot = 0
        self.current_bet = 0
        for player in self.players:
            player.reset_hand()
        self.player_index = 0
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        self.current_street = None

    # Deal 2 hole cards to each player
    def deal_hands(self, deck):
        for player in self.players:
            player.set_hand(deck.deal(2))

    # Burn one card then deal community cards for the given stage
    def deal_board(self, deck, stage):
        deck.burn()
        if stage == 'flop':
            self.board.extend(deck.deal(3))
        else:
            self.board.append(deck.deal_one())

    # Move to the next street (preflop -> flop -> turn -> river)
    def advance_street(self):
        self.current_street = STREET_NEXT.get(self.current_street)

    def __repr__(self):
        street = self.current_street or 'waiting'
        board = ' '.join(repr(c) for c in self.board) or '-'
        return f"[{street}] Board: {board} | Pot: ${self.pot}"
