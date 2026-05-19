# Poker AI Bot

Texas Hold'em poker bot with ML-powered decision making, built for live online play.

## Status

### Core (Done)
- [x] Card/Deck system with `__slots__` and master deck optimization
- [x] Player/Gamestate management (blinds, betting, board dealing)
- [x] Hand evaluator (treys library, O(1) lookup-table evaluation)
- [x] Monte Carlo equity simulator (treys int optimization, 10k+ sims/sec)
- [x] EV calculator with preflop odds table (all 169 starting hands)
- [x] Self-play simulator (full hand loop, random action placeholder)

### ML (In Progress)
- [ ] Feature encoder — game state to numerical vector
- [ ] Belief model — predict opponent hand distributions (PyTorch)
- [ ] Policy model — action selection via RL (PPO/DQN)
- [ ] Player profiler — learn individual player tendencies over time

### Backend / Production
- [ ] REST API (Flask/FastAPI) — decision inference <150ms
- [ ] Redis caching — hand equity lookups
- [ ] PostgreSQL — persist game history for training data
- [ ] ONNX model serving — fast inference in production
- [ ] Experience replay with prioritization

### Analysis
- [ ] GTO comparison — KL divergence to optimal solutions
- [ ] Expected value benchmarks across 50k+ hand matchups
- [ ] Self-play convergence tracking (100k+ iterations)

### Demo
- [ ] Web UI (React) — play against bot or simulate hands
- [ ] Leaderboard / PokerStars simulation benchmark

## Decision Flow

This is how the bot makes a decision at each action point:

```
1. Cards are dealt
        |
2. features.py reads the full game state
        |  -> hole cards, board, pot, stack, position, street
        |  -> normalizes everything to 0-1 for the neural net
        |
3. player_profiler checks opponent history
        |  -> VPIP (how loose/tight they play)
        |  -> PFR (preflop raise %)
        |  -> aggression factor (bet+raise vs call ratio)
        |  -> fold to raise % (do they give up to pressure?)
        |  -> showdown frequency
        |  -> bluff frequency (bet big with weak hands)
        |  -> slow-play frequency (check/call with strong hands)
        |
4. belief_model predicts opponent hands
        |  -> "likely has a weak pair" based on their actions + profile
        |
5. monte carlo calculates equity
        |  -> simulates thousands of outcomes -> 72% to win
        |
6. policy_model takes ALL of the above
        |  -> equity + beliefs + opponent tendencies + pot odds
        |  -> outputs: fold / call / raise + sizing
        |
7. Decision: "raise — he folds 70% to aggression"
```

The key: the bot doesn't just play the math. It exploits individual players by learning their patterns over time.

## Architecture

```
[ Game State ]
      |
[ Hand Evaluator ]        <- deterministic, O(1) treys lookup
      |
[ Monte Carlo Engine ]    <- equity via simulation
      |
[ EV Calculator ]         <- expected value math
      |
[ Feature Encoder ]       <- state -> numerical vector
      |
[ Player Profiler ] -------> feeds opponent tendencies into features
      |
[ Belief Model (ML) ]    <- predict opponent hand distributions
      |
[ Policy Model (RL) ]    <- fold / call / raise decisions
      |
[ REST API ]              <- serve decisions <150ms
```

## Key Design Decisions

- **ML sits on top of math, doesn't replace it.** Hand evaluation and equity are deterministic. ML handles opponent modeling and action selection.
- **Treys library for hand eval.** O(1) lookup tables using bit manipulation and prime number hashing. ~100M+ evals/sec. We wrap it, not rewrite it.
- **Monte Carlo uses treys ints directly.** Cards are converted once in `__init__`, the hot loop is pure int operations and table lookups. No object creation per simulation.
- **`__slots__` on hot classes.** Card, Deck, Player use `__slots__` for memory/speed — no `__dict__` overhead.
- **Preflop odds table.** All 169 starting hand combinations pre-computed. Instant lookup instead of running Monte Carlo preflop.
- **Player profiler feeds into policy.** The bot doesn't play GTO — it exploits individual opponents. Fold more vs aggro players, bluff more vs tight players.

## How Each File Works

### core/cards.py
- `Card` — rank (2-14) and suit (0-3), `__slots__`
- `Deck` — built from `_MASTER_DECK` tuple, `reset()` copies and shuffles, `deal()` pops from end
- `_MASTER_DECK` — pre-built tuple of all 52 cards, avoids rebuilding on every reset

### core/game_state.py
- `Player` — name, hand, stack, current_bet, folded. Methods: `bet()`, `call_bet()`, `bet_raise()`, `fold()`
- `Gamestate` — players list, board, pot, current_bet, dealer_index, street. Methods: `post_blinds()`, `deal_hands()`, `deal_board()`, `advance_street()`, `reset_round()`
- `STREET_NEXT` — dict mapping None->preflop->flop->turn->river

### core/hand_evaluator.py
- Wraps treys library for hand evaluation
- `evaluate(hole_cards, board)` — returns treys score (lower = better)
- `get_hand_rank()` — maps treys score to our constants (HIGH_CARD=0 through ROYAL_FLUSH=9)
- `compare_hands(hole_a, hole_b, board)` — returns 1 (a wins), -1 (b wins), 0 (tie)
- `_to_treys(card)` — converts our Card to treys int format

### equity/monte_carlo.py
- `MonteCarlo(hole_cards, board, num_opponents)` — converts cards to treys ints once in constructor
- `simulate(num_sims=10000)` — returns `{'win': float, 'tie': float, 'loss': float}`
- `_ALL_TREYS` — pre-built list of all 52 treys ints at module import
- Hot loop caches `_evaluator.evaluate` as local `ev`, tracks `best_opp` directly instead of list comprehension

### equity/ev_calculator.py
- `PREFLOP_ODDS` — dict of all 169 starting hands -> win % (keyed by `(high_rank, low_rank, suited)`)
- `get_preflop_odds(card1, card2)` — lookup function
- `EVcalc.calculate_ev(equity, pot, call_amount)` — `EV = equity * pot - (1 - equity) * call`
- `EVcalc.calculate_pot_odds(call_amount, pot_size)` — `call / (pot + call)`

### sim/simulator.py
- `Simulator(players, big_blind)` — takes Player objects with custom stacks
- `Simulator.for_training(num_players, big_blind)` — static method, creates uniform 100BB stacks
- `simulate_hand()` — full hand: reset -> blinds -> deal -> 4 betting rounds -> showdown
- `run_betting_round()` — tracks `players_to_act` set, handles fold/call/raise/check
- `decide_action(player)` — **placeholder** (random). ML policy replaces this.
- `showdown()` — evaluates all active hands, awards pot to lowest treys score
- `run(num_hands)` — loop, collects results in `hand_history`

## Project Structure

```
poker_ai/
├── core/
│   ├── cards.py              Card, Deck (__slots__, master deck)
│   ├── game_state.py         Player, Gamestate
│   └── hand_evaluator.py     Treys wrapper (evaluate, compare)
├── equity/
│   ├── ev_calculator.py      EVcalc, preflop odds table (169 hands)
│   └── monte_carlo.py        Monte Carlo simulator (treys int optimized)
├── ml/
│   ├── features.py           State encoder (TODO)
│   ├── belief_model.py       Opponent hand prediction (TODO)
│   └── policy_model.py       Action selection (TODO)
├── sim/
│   └── simulator.py          Self-play game loop
├── training/
│   ├── data_generator.py     Generate training data (TODO)
│   ├── train_belief.py       Train belief model (TODO)
│   └── train_policy.py       Train policy model (TODO)
├── config.py
└── main.py
```

## Quick Start

```python
from poker_ai.core.cards import Card, Deck
from poker_ai.core.game_state import Player, Gamestate
from poker_ai.equity.monte_carlo import MonteCarlo
from poker_ai.equity.ev_calculator import EVcalc, get_preflop_odds
from poker_ai.sim.simulator import Simulator

# Monte Carlo equity
hole = [Card(14, 0), Card(14, 1)]  # Pocket Aces
mc = MonteCarlo(hole, [], 1)
print(mc.simulate())  # {'win': 0.85, 'tie': 0.005, 'loss': 0.145}

# EV calculation
ev = EVcalc()
ev.calculate_ev(equity=0.85, pot=100, call_amount=20)  # EV: 82.0

# Preflop odds lookup
odds = get_preflop_odds(Card(14, 0), Card(13, 0))  # AKs -> 0.68

# Run simulator (custom stacks)
players = [Player("Alice", 500), Player("Bob", 200), Player("Charlie", 1000)]
sim = Simulator(players, big_blind=10)
results = sim.run(100)

# Run simulator (training mode, uniform 100BB stacks)
sim = Simulator.for_training(6, 10)
results = sim.run(1000)
```

## Dependencies

- `treys` — O(1) hand evaluation via lookup tables
- `PyTorch` — belief and policy models (upcoming)
- `FastAPI` — REST API for inference (upcoming)
- `Redis` — equity caching (upcoming)
- `PostgreSQL` — game history persistence (upcoming)
