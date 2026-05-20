import os
import numpy as np

from poker_ai.core.game_state import Player
from poker_ai.core.hand_evaluator import get_hand_rank
from poker_ai.ml.features import extract_features
from poker_ai.sim.simulator import Simulator

# check and call both map to 1 — model learns from context which applies
ACTION_MAP  = {'fold': 0, 'check': 1, 'call': 1, 'raise': 2}
NUM_ACTIONS = 3


# This class extends Simulator to record training data at every decision point.
# Policy data pairs each game state with the action taken and the net chip reward at hand end.
# Belief data pairs game states with the opponent's showdown hand class (head-to-head only).
class DataGenerator(Simulator):

    def __init__(self, num_players, big_blind, starting_stack=1000, small_blind=None):
        players = [Player(f'P{i}', starting_stack) for i in range(num_players)]
        super().__init__(players, big_blind, small_blind)
        self._starting_stack = starting_stack
        self._hand_buffer    = []
        self._policy_states  = []
        self._policy_actions = []
        self._policy_rewards = []
        self._belief_states  = []
        self._belief_labels  = []

    def _decide_action(self, player):
        state      = extract_features(player, self.gamestate, use_mc=False)
        action_str = super()._decide_action(player)
        self._hand_buffer.append({
            'state':      state,
            'action':     ACTION_MAP[action_str],
            'player_idx': self.gamestate.players.index(player),
        })
        return action_str

    # This method runs one hand, collects (state, action, reward) samples for the policy,
    # and (state, opp_hand_class) samples for the belief model at showdown.
    # Returns:
    #   - dict: same result dict as Simulator.simulate_hand
    def simulate_hand(self):
        gs           = self.gamestate
        start_stacks = [p.stack for p in gs.players]
        self._hand_buffer = []

        result = super().simulate_hand()

        for entry in self._hand_buffer:
            idx             = entry['player_idx']
            entry['reward'] = gs.players[idx].stack - start_stacks[idx]

        board = gs.board
        if result['method'] == 'showdown' and board:
            active     = [i for i, p in enumerate(gs.players) if not p.folded]
            hand_ranks = {i: get_hand_rank(gs.players[i].hand, board) for i in active}
            for entry in self._hand_buffer:
                hero   = entry['player_idx']
                others = {i: r for i, r in hand_ranks.items() if i != hero}
                if len(others) == 1:
                    entry['opp_hand_class'] = next(iter(others.values()))

        for entry in self._hand_buffer:
            self._policy_states.append(entry['state'])
            self._policy_actions.append(entry['action'])
            self._policy_rewards.append(entry['reward'])
            if 'opp_hand_class' in entry:
                self._belief_states.append(entry['state'])
                self._belief_labels.append(entry['opp_hand_class'])

        return result

    @property
    def num_policy_samples(self):
        return len(self._policy_states)

    @property
    def num_belief_samples(self):
        return len(self._belief_states)

    # This method returns the accumulated policy training data as numpy arrays.
    # Returns:
    #   - tuple: (states float32 [N,85], actions int64 [N], rewards float32 [N])
    def get_policy_arrays(self):
        return (
            np.array(self._policy_states,  dtype=np.float32),
            np.array(self._policy_actions, dtype=np.int64),
            np.array(self._policy_rewards, dtype=np.float32),
        )

    # This method returns the accumulated belief training data as numpy arrays.
    # Returns:
    #   - tuple: (states float32 [N,85], labels int64 [N])
    def get_belief_arrays(self):
        return (
            np.array(self._belief_states, dtype=np.float32),
            np.array(self._belief_labels, dtype=np.int64),
        )

    # This method saves accumulated samples to compressed .npz files in the given directory.
    # Parameters:
    #   - path: directory to write policy.npz and belief.npz (created if missing)
    def save(self, path='data'):
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

    # This method clears all accumulated training data without resetting the simulator state.
    def clear(self):
        self._policy_states.clear()
        self._policy_actions.clear()
        self._policy_rewards.clear()
        self._belief_states.clear()
        self._belief_labels.clear()


# This function runs num_hands complete hands, saves training data to save_path, and returns
# the DataGenerator with all accumulated samples.
# Parameters:
#   - num_hands: number of hands to simulate
#   - num_players: number of players at the table
#   - big_blind: big blind chip amount
#   - starting_stack: starting chip count per player
#   - save_path: directory to write .npz files
# Returns:
#   - DataGenerator: with accumulated policy and belief data
def generate(num_hands, num_players=3, big_blind=20,
             starting_stack=1000, save_path='data'):
    gen = DataGenerator(num_players, big_blind, starting_stack=starting_stack)
    gen.run(num_hands)
    gen.save(save_path)
    return gen
