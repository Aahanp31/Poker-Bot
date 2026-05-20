import argparse
import os

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from poker_ai.core.game_state import Player
from poker_ai.ml.features import extract_features
from poker_ai.ml.belief_model import BeliefModel
from poker_ai.ml.policy_model import PolicyModel, make_policy_input
from poker_ai.sim.simulator import Simulator


# This class extends Simulator so the policy model drives decisions instead of
# the EV heuristic. It records (state, action, log_prob, value) at every decision
# and attaches the net chip reward after each hand completes.
class RolloutCollector(Simulator):

    def __init__(self, policy, belief, players, big_blind, small_blind=None):
        super().__init__(players, big_blind, small_blind)
        self.policy  = policy
        self.belief  = belief
        self._device = next(policy.parameters()).device
        self._buffer = []

    def _decide_action(self, player):
        gs      = self.gamestate
        to_call = gs.current_bet - player.current_bet

        state   = extract_features(player, gs, use_mc=False)
        state_t = torch.tensor(state, dtype=torch.float32, device=self._device).unsqueeze(0)

        with torch.no_grad():
            belief_probs = self.belief.predict_probs(state_t)

        policy_input        = make_policy_input(state_t, belief_probs)
        action, lp, val, _ = self.policy.act(policy_input)
        action_idx          = action.item()

        # map policy output to simulator action string
        if action_idx == 2:
            # only raise if stack covers call + one big blind
            if player.stack >= to_call + self.big_blind:
                action_str = 'raise'
            else:
                action_str = 'check' if to_call <= 0 else 'call'
        elif action_idx == 1:
            action_str = 'check' if to_call <= 0 else 'call'
        else:
            action_str = 'fold'

        self._buffer.append({
            'state':      state,
            'action':     action_idx,
            'log_prob':   lp.item(),
            'value':      val.item(),
            'player_idx': gs.players.index(player),
        })
        return action_str

    # This method runs num_hands hands with the policy model deciding and returns
    # the collected rollout entries with rewards filled in.
    # Parameters:
    #   - num_hands: number of hands to simulate
    #   - starting_stack: chips to reset each player to before every hand
    # Returns:
    #   - list[dict]: one entry per decision with state/action/log_prob/value/reward
    def collect(self, num_hands, starting_stack=1000):
        entries = []
        for _ in range(num_hands):
            for p in self.gamestate.players:
                p.stack = starting_stack

            start_stacks = [p.stack for p in self.gamestate.players]
            self._buffer = []
            self.simulate_hand()

            for entry in self._buffer:
                idx             = entry['player_idx']
                entry['reward'] = self.gamestate.players[idx].stack - start_stacks[idx]
                entries.append(entry)

        return entries


# This function runs one PPO update on a batch of rollout entries.
# Parameters:
#   - policy: PolicyModel to update
#   - optimizer: torch optimizer
#   - entries: rollout data from RolloutCollector.collect
#   - clip_eps: PPO clipping range (default 0.2)
#   - value_coef: weight on value loss (default 0.5)
#   - entropy_coef: weight on entropy bonus — higher means more exploration (default 0.01)
#   - epochs: number of passes over the batch per update (default 4)
#   - batch_size: minibatch size (default 256)
#   - device: torch device string
def _ppo_update(policy, optimizer, entries, clip_eps=0.2, value_coef=0.5,
                entropy_coef=0.01, epochs=4, batch_size=256, device='cpu'):

    states   = torch.tensor([e['state']    for e in entries], dtype=torch.float32, device=device)
    actions  = torch.tensor([e['action']   for e in entries], dtype=torch.int64,   device=device)
    old_lp   = torch.tensor([e['log_prob'] for e in entries], dtype=torch.float32, device=device)
    returns  = torch.tensor([e['reward']   for e in entries], dtype=torch.float32, device=device)
    old_vals = torch.tensor([e['value']    for e in entries], dtype=torch.float32, device=device)

    advantages = returns - old_vals
    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

    dataset = TensorDataset(states, actions, old_lp, returns, advantages)
    loader  = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    for _ in range(epochs):
        for s, a, olp, ret, adv in loader:
            log_prob, entropy, value = policy.evaluate(s, a)
            ratio = torch.exp(log_prob - olp)

            policy_loss  = -torch.min(
                ratio * adv,
                torch.clamp(ratio, 1 - clip_eps, 1 + clip_eps) * adv,
            ).mean()
            value_loss   = F.mse_loss(value.squeeze(-1), ret)
            entropy_loss = -entropy.mean()

            loss = policy_loss + value_coef * value_loss + entropy_coef * entropy_loss

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(policy.parameters(), 0.5)
            optimizer.step()


# This function trains the PolicyModel using PPO on self-play rollouts with a
# frozen BeliefModel providing opponent hand estimates.
# Parameters:
#   - belief_path: path to saved BeliefModel weights
#   - save_path: file path to write trained PolicyModel weights
#   - num_players: number of players at the table
#   - big_blind: big blind chip amount
#   - iterations: number of PPO iterations
#   - hands_per_iter: hands to simulate per iteration before each update
#   - lr: Adam learning rate
def train(belief_path='data/belief_model.pt', save_path='data/policy_model.pt',
          num_players=3, big_blind=20, iterations=100, hands_per_iter=200, lr=3e-4):

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    belief = BeliefModel().to(device)
    belief.load_state_dict(torch.load(belief_path, map_location=device))
    belief.eval()

    policy    = PolicyModel().to(device)
    optimizer = torch.optim.Adam(policy.parameters(), lr=lr)

    players   = [Player(f'P{i}', 1000) for i in range(num_players)]
    collector = RolloutCollector(policy, belief, players, big_blind)

    for it in range(1, iterations + 1):
        policy.eval()
        entries = collector.collect(hands_per_iter)

        policy.train()
        _ppo_update(policy, optimizer, entries, device=str(device))

        avg_reward = sum(e['reward'] for e in entries) / len(entries)
        print(f"Iter {it:4d}/{iterations}  "
              f"steps={len(entries):5d}  avg_reward={avg_reward:+.1f}")

    save_dir = os.path.dirname(save_path)
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
    torch.save(policy.state_dict(), save_path)
    print(f"Saved → {save_path}")
    return policy


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--belief',     default='data/belief_model.pt')
    parser.add_argument('--save',       default='data/policy_model.pt')
    parser.add_argument('--players',    type=int,   default=3)
    parser.add_argument('--iterations', type=int,   default=100)
    parser.add_argument('--hands',      type=int,   default=200)
    parser.add_argument('--lr',         type=float, default=3e-4)
    args = parser.parse_args()

    train(
        belief_path=args.belief,
        save_path=args.save,
        num_players=args.players,
        iterations=args.iterations,
        hands_per_iter=args.hands,
        lr=args.lr,
    )
