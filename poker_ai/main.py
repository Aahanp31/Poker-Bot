import argparse
import os

import torch

from poker_ai.training.data_generator import generate
from poker_ai.training.train_belief import train as train_belief
from poker_ai.training.train_policy import train as train_policy


# This function runs the full training pipeline in order:
# generate data → train belief model → train policy model.
# Parameters:
#   - num_players: number of players at the table
#   - big_blind: big blind chip amount
#   - hands: number of hands to generate for training data
#   - data_path: directory to store .npz training data
#   - belief_epochs: epochs to train the belief model
#   - policy_iterations: PPO iterations to train the policy model
def run_pipeline(num_players=3, big_blind=20, hands=10000, data_path='data',
                 belief_epochs=20, policy_iterations=100):

    print(f"\n{'='*50}")
    print(f"  Step 1/3 — Generating {hands:,} hands of training data")
    print(f"{'='*50}")
    generate(
        num_hands=hands,
        num_players=num_players,
        big_blind=big_blind,
        save_path=data_path,
    )

    print(f"\n{'='*50}")
    print(f"  Step 2/3 — Training belief model")
    print(f"{'='*50}")
    train_belief(
        data_path=data_path,
        save_path=os.path.join(data_path, 'belief_model.pt'),
        epochs=belief_epochs,
    )

    print(f"\n{'='*50}")
    print(f"  Step 3/3 — Training policy model (PPO)")
    print(f"{'='*50}")
    train_policy(
        belief_path=os.path.join(data_path, 'belief_model.pt'),
        save_path=os.path.join(data_path, 'policy_model.pt'),
        num_players=num_players,
        big_blind=big_blind,
        iterations=policy_iterations,
    )

    print(f"\nDone. Models saved to {data_path}/")


# This function runs N hands with the trained policy model and prints the results.
# Parameters:
#   - num_players: number of players at the table
#   - big_blind: big blind chip amount
#   - hands: number of hands to play
#   - data_path: directory containing belief_model.pt and policy_model.pt
def run_bot(num_players=3, big_blind=20, hands=20, data_path='data'):
    from poker_ai.core.game_state import Player
    from poker_ai.ml.belief_model import BeliefModel
    from poker_ai.ml.policy_model import PolicyModel, make_policy_input
    from poker_ai.ml.features import extract_features
    from poker_ai.training.train_policy import RolloutCollector

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    belief = BeliefModel().to(device)
    belief.load_state_dict(torch.load(
        os.path.join(data_path, 'belief_model.pt'), map_location=device))
    belief.eval()

    policy = PolicyModel().to(device)
    policy.load_state_dict(torch.load(
        os.path.join(data_path, 'policy_model.pt'), map_location=device))
    policy.eval()

    players   = [Player(f'P{i}', 1000) for i in range(num_players)]
    collector = RolloutCollector(policy, belief, players, big_blind)

    print(f"\nRunning {hands} hands with trained policy...\n")
    wins = {}
    for i in range(hands):
        for p in collector.gamestate.players:
            p.stack = 1000
        result = collector.simulate_hand()
        winner = result['winner']
        wins[winner] = wins.get(winner, 0) + 1
        print(f"  Hand {i+1:3d}: {winner} wins ${result['pot']} ({result['method']})")

    print(f"\nWin counts over {hands} hands:")
    for name, count in sorted(wins.items(), key=lambda x: -x[1]):
        print(f"  {name}: {count} ({count/hands*100:.1f}%)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Poker AI')
    sub    = parser.add_subparsers(dest='command')

    # train command
    t = sub.add_parser('train', help='run the full training pipeline')
    t.add_argument('--players',    type=int,   default=3)
    t.add_argument('--big-blind',  type=int,   default=20)
    t.add_argument('--hands',      type=int,   default=10000)
    t.add_argument('--data',       default='data')
    t.add_argument('--belief-epochs',     type=int, default=20)
    t.add_argument('--policy-iterations', type=int, default=100)

    # run command
    r = sub.add_parser('run', help='play hands with the trained bot')
    r.add_argument('--players',   type=int, default=3)
    r.add_argument('--big-blind', type=int, default=20)
    r.add_argument('--hands',     type=int, default=20)
    r.add_argument('--data',      default='data')

    args = parser.parse_args()

    if args.command == 'train':
        run_pipeline(
            num_players=args.players,
            big_blind=args.big_blind,
            hands=args.hands,
            data_path=args.data,
            belief_epochs=args.belief_epochs,
            policy_iterations=args.policy_iterations,
        )
    elif args.command == 'run':
        run_bot(
            num_players=args.players,
            big_blind=args.big_blind,
            hands=args.hands,
            data_path=args.data,
        )
    else:
        parser.print_help()
