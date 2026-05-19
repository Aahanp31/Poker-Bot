PREFLOP_ODDS = {
    # Pairs
    (14,14,False):0.85,(13,13,False):0.83,(12,12,False):0.80,(11,11,False):0.78,
    (10,10,False):0.75,(9,9,False):0.72,(8,8,False):0.69,(7,7,False):0.67,
    (6,6,False):0.64,(5,5,False):0.61,(4,4,False):0.58,(3,3,False):0.55,(2,2,False):0.51,
    # Ace high suited
    (14,13,True):0.68,(14,12,True):0.67,(14,11,True):0.66,(14,10,True):0.66,
    (14,9,True):0.64,(14,8,True):0.63,(14,7,True):0.63,(14,6,True):0.62,
    (14,5,True):0.62,(14,4,True):0.61,(14,3,True):0.60,(14,2,True):0.59,
    # Ace high offsuit
    (14,13,False):0.66,(14,12,False):0.65,(14,11,False):0.65,(14,10,False):0.64,
    (14,9,False):0.62,(14,8,False):0.61,(14,7,False):0.60,(14,6,False):0.59,
    (14,5,False):0.60,(14,4,False):0.59,(14,3,False):0.58,(14,2,False):0.57,
    # King high suited
    (13,12,True):0.64,(13,11,True):0.63,(13,10,True):0.63,(13,9,True):0.61,
    (13,8,True):0.60,(13,7,True):0.59,(13,6,True):0.59,(13,5,True):0.58,
    (13,4,True):0.57,(13,3,True):0.56,(13,2,True):0.55,
    # King high offsuit
    (13,12,False):0.62,(13,11,False):0.62,(13,10,False):0.61,(13,9,False):0.59,
    (13,8,False):0.58,(13,7,False):0.57,(13,6,False):0.56,(13,5,False):0.55,
    (13,4,False):0.54,(13,3,False):0.53,(13,2,False):0.53,
    # Queen high suited
    (12,11,True):0.61,(12,10,True):0.61,(12,9,True):0.59,(12,8,True):0.58,
    (12,7,True):0.57,(12,6,True):0.56,(12,5,True):0.55,(12,4,True):0.54,
    (12,3,True):0.53,(12,2,True):0.52,
    # Queen high offsuit
    (12,11,False):0.59,(12,10,False):0.59,(12,9,False):0.57,(12,8,False):0.56,
    (12,7,False):0.54,(12,6,False):0.53,(12,5,False):0.52,(12,4,False):0.51,
    (12,3,False):0.50,(12,2,False):0.49,
    # Jack high suited
    (11,10,True):0.59,(11,9,True):0.57,(11,8,True):0.56,(11,7,True):0.54,
    (11,6,True):0.53,(11,5,True):0.52,(11,4,True):0.51,(11,3,True):0.50,(11,2,True):0.50,
    # Jack high offsuit
    (11,10,False):0.57,(11,9,False):0.55,(11,8,False):0.53,(11,7,False):0.52,
    (11,6,False):0.50,(11,5,False):0.49,(11,4,False):0.48,(11,3,False):0.48,(11,2,False):0.47,
    # Ten high suited
    (10,9,True):0.56,(10,8,True):0.54,(10,7,True):0.53,(10,6,True):0.51,
    (10,5,True):0.49,(10,4,True):0.49,(10,3,True):0.48,(10,2,True):0.47,
    # Ten high offsuit
    (10,9,False):0.53,(10,8,False):0.52,(10,7,False):0.50,(10,6,False):0.48,
    (10,5,False):0.47,(10,4,False):0.46,(10,3,False):0.45,(10,2,False):0.43,
    # Nine high suited
    (9,8,True):0.53,(9,7,True):0.51,(9,6,True):0.50,(9,5,True):0.48,
    (9,4,True):0.46,(9,3,True):0.46,(9,2,True):0.45,
    # Nine high offsuit
    (9,8,False):0.50,(9,7,False):0.48,(9,6,False):0.47,(9,5,False):0.45,
    (9,4,False):0.43,(9,3,False):0.43,(9,2,False):0.42,
    # Eight high suited
    (8,7,True):0.50,(8,6,True):0.49,(8,5,True):0.47,(8,4,True):0.45,
    (8,3,True):0.45,(8,2,True):0.43,
    # Eight high offsuit
    (8,7,False):0.47,(8,6,False):0.46,(8,5,False):0.44,(8,4,False):0.42,
    (8,3,False):0.42,(8,2,False):0.40,
    # Seven high suited
    (7,6,True):0.48,(7,5,True):0.46,(7,4,True):0.45,(7,3,True):0.43,(7,2,True):0.42,
    # Seven high offsuit
    (7,6,False):0.45,(7,5,False):0.43,(7,4,False):0.42,(7,3,False):0.40,(7,2,False):0.39,
    # Six high suited
    (6,5,True):0.46,(6,4,True):0.44,(6,3,True):0.43,(6,2,True):0.42,
    # Six high offsuit
    (6,5,False):0.43,(6,4,False):0.41,(6,3,False):0.40,(6,2,False):0.39,
    # Five high suited
    (5,4,True):0.44,(5,3,True):0.43,(5,2,True):0.42,
    # Five high offsuit
    (5,4,False):0.41,(5,3,False):0.40,(5,2,False):0.39,
    # Four high suited
    (4,3,True):0.42,(4,2,True):0.40,
    # Four high offsuit
    (4,3,False):0.39,(4,2,False):0.37,
    # Three high
    (3,2,True):0.39,(3,2,False):0.37,
}


def get_preflop_odds(card1, card2):
    high   = max(card1.rank, card2.rank)
    low    = min(card1.rank, card2.rank)
    suited = (card1.suit == card2.suit) and (high != low)
    return PREFLOP_ODDS.get((high, low, suited), 0.0)


def pot_odds(call_amount, pot_size):
    return call_amount / (pot_size + call_amount)


def ev(equity, pot, call_amount):
    return equity * pot - (1 - equity) * call_amount
