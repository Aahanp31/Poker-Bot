import random

SUITS = (0, 1, 2, 3)  # 0=Hearts, 1=Diamonds, 2=Clubs, 3=Spades
RANKS = tuple(range(2, 15))

SUIT_NAMES = ('H', 'D', 'C', 'S')

RANK_NAMES = {
    2: '2', 3: '3', 4: '4', 5: '5',
    6: '6', 7: '7', 8: '8', 9: '9',
    10: 'T', 11: 'J', 12: 'Q', 13: 'K',
    14: 'A',
}


# This class represents a single playing card with a rank and suit.
class Card:
    __slots__ = ('rank', 'suit')

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"{RANK_NAMES[self.rank]}{SUIT_NAMES[self.suit]}"


# cached so reset() is just a list copy
_MASTER_DECK = tuple(Card(r, s) for r in RANKS for s in SUITS)


# This class manages a 52-card deck. It supports dealing, burning, and resetting
# for use across multiple hands without reallocating the full card set.
class Deck:
    __slots__ = ('cards',)

    def __init__(self):
        self.cards = list(_MASTER_DECK)
        random.shuffle(self.cards)

    # This method removes and returns the top card from the deck.
    # Returns:
    #   - Card: the next card from the top of the deck
    def deal_one(self):
        return self.cards.pop()

    # This method removes and returns num cards from the top of the deck.
    # Parameters:
    #   - num: number of cards to deal
    # Returns:
    #   - list[Card]: the dealt cards
    def deal(self, num):
        dealt = self.cards[-num:]
        del self.cards[-num:]
        return dealt

    # This method discards the top card. Called before dealing board cards per
    # standard poker rules.
    def burn(self):
        self.cards.pop()

    # This method refills the deck from the master set and reshuffles it.
    def reset(self):
        self.cards = list(_MASTER_DECK)
        random.shuffle(self.cards)
