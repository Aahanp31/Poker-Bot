import random

from poker_ai.core.cards import Deck
from poker_ai.core.game_state import Gamestate
from poker_ai.core.hand_evaluator import evaluate
from poker_ai.equity.ev_calculator import get_preflop_odds, pot_odds, ev


class Simulator:
    def __init__(self, players, big_blind, small_blind=None):
        self.big_blind  = big_blind
        self.small_blind = small_blind if small_blind is not None else big_blind >> 1
        self.gamestate  = Gamestate(big_blind, self.small_blind)
        self.deck       = Deck()

        for player in players:
            self.gamestate.add_player(player)

    def simulate_hand(self):
        gs  = self.gamestate
        deck = self.deck
        num  = len(gs.players)

        gs.reset_round()
        deck.reset()
        gs.advance_street()   # preflop
        gs.post_blinds()
        gs.deal_hands(deck)

        gs.player_index = (gs.dealer_index + 3) % num
        self._betting_round()
        if self._hand_over():
            return self._award_pot()

        for stage in ('flop', 'turn', 'river'):
            gs.advance_street()
            gs.deal_board(deck, stage)
            gs.player_index = (gs.dealer_index + 1) % num
            self._betting_round()
            if self._hand_over():
                return self._award_pot()

        return self._showdown()

    def _betting_round(self):
        gs  = self.gamestate
        num = len(gs.players)

        players_to_act = {
            i for i, p in enumerate(gs.players)
            if not p.folded and p.stack > 0
        }

        while players_to_act:
            i = gs.player_index
            p = gs.players[i]

            if p.folded or p.stack <= 0:
                players_to_act.discard(i)
                gs.player_index = (i + 1) % num
                continue

            if i not in players_to_act:
                gs.player_index = (i + 1) % num
                continue

            action     = self._decide_action(p)
            pot_before = gs.pot

            if action == 'fold':
                p.fold()
                players_to_act.discard(i)
                gs.log_action(i, 1, 0, pot_before)

            elif action == 'call':
                amount  = p.call_bet(gs)
                gs.pot += amount
                players_to_act.discard(i)
                gs.log_action(i, 3, amount, pot_before)

            elif action == 'raise':
                call_amt  = gs.current_bet - p.current_bet
                raise_amt = call_amt + self.big_blind
                amount        = p.bet_raise(raise_amt, gs)
                gs.pot       += amount
                gs.current_bet = p.current_bet
                players_to_act = {
                    j for j, q in enumerate(gs.players)
                    if not q.folded and q.stack > 0 and j != i
                }
                gs.log_action(i, 4, amount, pot_before)

            else:  # check
                players_to_act.discard(i)
                gs.log_action(i, 2, 0, pot_before)

            if len(gs.active_players()) <= 1:
                return

            gs.player_index = (i + 1) % num

    def _decide_action(self, player):
        gs      = self.gamestate
        to_call = gs.current_bet - player.current_bet

        if to_call <= 0:
            return random.choice(['check', 'raise'])

        equity    = get_preflop_odds(player.hand[0], player.hand[1])
        call_ev   = ev(equity, gs.pot, to_call)
        pot_odd   = pot_odds(to_call, gs.pot)

        if call_ev > 0:
            return random.choice(['call', 'raise'])
        if equity > pot_odd:
            return 'call'
        return random.choice(['fold', 'call'])

    def _hand_over(self):
        return len(self.gamestate.active_players()) <= 1

    def _award_pot(self):
        gs     = self.gamestate
        active = gs.active_players()
        if len(active) == 1:
            active[0].stack += gs.pot
            result = {'winner': active[0].name, 'pot': gs.pot, 'method': 'fold'}
            gs.pot = 0
            return result
        return self._showdown()

    def _showdown(self):
        gs     = self.gamestate
        active = gs.active_players()

        winner    = min(active, key=lambda p: evaluate(p.hand, gs.board))
        winner.stack += gs.pot
        result = {'winner': winner.name, 'pot': gs.pot, 'method': 'showdown'}
        gs.pot = 0
        return result

    def run(self, num_hands):
        return [self.simulate_hand() for _ in range(num_hands)]
