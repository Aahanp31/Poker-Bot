import os
import numpy as np

from poker_ai.core.game_state import Player
from poker_ai.core.hand_evaluator import get_hand_rank
from poker_ai.ml.features import extract_features, FEATURE_DIM
from poker_ai.sim.simulator import Simulator

# Simplified 3-action space used by both data gen and policy model
# check and call both map to 1 — model learns from context which applies
ACTION_MAP = {'fold': 0, 'check': 1, 'call': 1, 'raise': 2}
NUM_ACTIONS = 3


class DataGenerator(Simulator):
    """
    Extends Simulator to record (state, action, reward) at every decision
    and opponent hand class labels at showdown for the belief model.

    Policy data  : (state[85], action, reward)
    Belief data  : (state[85], opp_hand_class)  — showdown hands only
    """

    def __init__(self, num_players, big_blind, starting_stack=1000,
                 small_blind=None):
        players = [Player(f'P{i}', starting_stack) for i in range(num_players)]
        super().__init__(players, big_blind, small_blind)
        self._starting_stack = starting_stack
        self._hand_buffer    = []

        self._policy_states  = []
        self._policy_actions = []
        self._policy_rewards = []
        self._belief_states  = []
        self._belief_labels  = []

    # ── Override to intercept every decision ──────────────────────────────────

    def _decide_action(self, player):
        state      = extract_features(player, self.gamestate, use_mc=False)
        action_str = super()._decide_action(player)
        self._hand_buffer.append({
            'state':      state,
            'action':     ACTION_MAP[action_str],
            'player_idx': self.gamestate.players.index(player),
        })
        return action_str

    def simulate_hand(self):
        gs           = self.gamestate
        start_stacks = [p.stack for p in gs.players]
        self._hand_buffer = []

        result = super().simulate_hand()

        # Fill reward: net chips this hand (includes blind cost)
        for entry in self._hand_buffer:
            idx             = entry['player_idx']
            entry['reward'] = gs.players[idx].stack - start_stacks[idx]

        # Belief labels: only when hand reaches showdown with a board
        board = gs.board
        if result['method'] == 'showdown' and board:
            active     = [i for i, p in enumerate(gs.players) if not p.folded]
            hand_ranks = {i: get_hand_rank(gs.players[i].hand, board)
                          for i in active}
            for entry in self._hand_buffer:
                hero   = entry['player_idx']
                others = {i: r for i, r in hand_ranks.items() if i != hero}
                if len(others) == 1:
                    # Clean 1-vs-1 label: what did the single opponent hold?
                    entry['opp_hand_class'] = next(iter(others.values()))

        # Flush buffer into accumulators
        for entry in self._hand_buffer:
            self._policy_states.append(entry['state'])
            self._policy_actions.append(entry['action'])
            self._policy_rewards.append(entry['reward'])
            if 'opp_hand_class' in entry:
                self._belief_states.append(entry['state'])
                self._belief_labels.append(entry['opp_hand_class'])

        return result

    # ── Data access ───────────────────────────────────────────────────────────

    @property
    def num_policy_samples(self):
        return len(self._policy_states)

    @property
    def num_belief_samples(self):
        return len(self._belief_states)

    def get_policy_arrays(self):
        """Returns (states, actions, rewards) as numpy arrays."""
        return (
            np.array(self._policy_states,  dtype=np.float32),
            np.array(self._policy_actions, dtype=np.int64),
            np.array(self._policy_rewards, dtype=np.float32),
        )

    def get_belief_arrays(self):
        """Returns (states, labels) as numpy arrays."""
        return (
            np.array(self._belief_states, dtype=np.float32),
            np.array(self._belief_labels, dtype=np.int64),
        )

    def save(self, path='data'):
        """Save accumulated data to compressed .npz files."""
        os.makedirs(path, exist_ok=True)

        if self._policy_states:
            states, actions, rewards = self.get_policy_arrays()
            np.savez_compressed(
                os.path.join(path, 'policy.npz'),
                states=states, actions=actions, rewards=rewards,
            )

        if self._belief_states:
            states, labels = self.get_belief_arrays()
            np.savez_compressed(
                os.path.join(path, 'belief.npz'),
                states=states, labels=labels,
            )

        print(f"Saved {self.num_policy_samples:,} policy samples "
              f"and {self.num_belief_samples:,} belief samples → {path}/")

    def clear(self):
        """Reset accumulators (keeps simulator state intact)."""
        self._policy_states.clear()
        self._policy_actions.clear()
        self._policy_rewards.clear()
        self._belief_states.clear()
        self._belief_labels.clear()


def generate(num_hands, num_players=3, big_blind=20,
             starting_stack=1000, save_path='data'):
    """Convenience function: run N hands and save training data."""
    gen = DataGenerator(num_players, big_blind,
                        starting_stack=starting_stack)
    gen.run(num_hands)
    gen.save(save_path)
    return gen
