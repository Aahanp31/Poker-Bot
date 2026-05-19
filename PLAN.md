# Poker Bot Architecture — Implementation Plan

## Project Structure
```
poker_ai/
├── __init__.py
├── config.py
├── main.py                         (entry point)
├── core/
│   ├── __init__.py
│   ├── cards.py                    ✅ Card, Deck
│   ├── game_state.py               ✅ Player, Gamestate
│   └── hand_evaluator.py           ✅ evaluate, get_hand_rank, compare_hands
├── equity/
│   ├── __init__.py
│   ├── ev_calculator.py            ✅ get_preflop_odds, pot_odds, ev  (pure functions)
│   └── monte_carlo.py              ✅ MonteCarlo  (C++ backend via mc_cpp)
├── mc_cpp/
│   └── monte_carlo.cpp             ✅ C++ eval5/eval7 + MC loop (xoshiro256++)
├── ml/
│   ├── __init__.py
│   ├── features.py                 ✅ extract_features → float32[85]
│   ├── belief_model.py             ✅ BeliefModel — predicts opponent hand class
│   └── policy_model.py             ⬜ TODO
├── training/
│   ├── __init__.py
│   ├── data_generator.py           ✅ DataGenerator — records (state, action, reward)
│   ├── train_belief.py             ✅ trains BeliefModel on belief.npz
│   └── train_policy.py             ⬜ TODO
├── sim/
│   ├── __init__.py
│   └── simulator.py                ✅ Simulator — EV-based actions, full hand loop
├── db/
│   ├── __init__.py
│   ├── schema.py                   ⬜ TODO — SQLite schema (hands, actions, sessions)
│   └── repository.py               ⬜ TODO — read/write helpers for hand history
└── app/
    ├── __init__.py
    ├── server.py                   ⬜ TODO — FastAPI backend
    └── static/                     ⬜ TODO — frontend (React or plain HTML/JS)
```

## What To Build (in order)

### ✅ Step 1: Hand Evaluator — `core/hand_evaluator.py`
Wraps treys with a precomputed card lookup table. No ML.

- `evaluate(hole, board)` — returns treys score (lower = better)
- `get_hand_rank(hole, board)` — returns int 0–9 (High Card → Royal Flush)
- `get_hand_name(hole, board)` — human-readable string
- `compare_hands(hole_a, hole_b, board)` — returns 1, -1, or 0

### ✅ Step 2: Monte Carlo Engine — `equity/monte_carlo.py` + `mc_cpp/`
C++ backend (xoshiro256++ RNG, sorting network, precomputed C(7,5) table).
Python wrapper is a thin conversion layer.

- `MonteCarlo(hole, board, num_opponents).simulate(n)` — returns `{'win', 'tie', 'loss'}`
- ~9.5ms per 10k sims (12.6× faster than pure Python)

### ✅ Step 3: EV Calculator — `equity/ev_calculator.py`
Pure functions, no class wrapper.

- `get_preflop_odds(card1, card2)` — lookup table for all starting hands
- `pot_odds(call_amount, pot_size)` — call / (pot + call)
- `ev(equity, pot, call_amount)` — equity * pot - (1 - equity) * call

### ✅ Step 4: Game Simulator — `sim/simulator.py`
EV-based action selection. Full hand loop.

- `Simulator(players, big_blind).run(n)` — returns list of hand result dicts
- Actions driven by preflop EV: fold if EV < 0 and equity < pot odds, else call/raise
- Data generator (next step) wraps this to capture (state, action, reward) tuples

### ✅ Step 5: State Encoder — `ml/features.py`
Direct numpy array construction, no intermediate lists.

- `extract_features(player, gamestate, use_mc, mc_sims)` → `float32[21]`
- Features: hole ranks/suits, board ranks/suits (0-padded), street, pot, stack,
  call amount, position, opponents, equity (preflop table or MC)

### Step 6: Opponent Belief Model (ML) — `ml/belief_model.py`
Neural net that predicts opponent hand distributions.

- Input: encoded state + betting history
- Output: probability distribution over hand classes (has pair, has flush draw, has set, etc.)
- Train on self-play data where we know ground truth
- PyTorch small feedforward net to start

### Step 7: Decision Policy (ML/RL) — `ml/policy_model.py`
Action selection.

- Input: state encoding + EV + belief model output
- Output: action (fold/call/raise) + sizing
- Start rule-based (call if EV > 0), upgrade to RL later
- Training: PPO or DQN on self-play rewards

### Step 8: Entry Point — `main.py`
Wires together simulator, models, and data generation into a single runnable script.

### Step 9: Hand History Database — `db/`
SQLite database for storing hand histories and session stats.

- `schema.py` — creates tables: sessions, hands, actions, players
- `repository.py` — insert/query helpers (save a hand, fetch hands by session, player stats)
- Tracks: hand result, every action taken, chips won/lost per player per session
- Enables post-session review and opponent stat tracking (VPIP, aggression, etc.)

### Step 10: Frontend App — `app/`
Web interface for reviewing hands and session data stored in the database.

- `server.py` — FastAPI backend exposing hand history and stats as JSON endpoints
- Frontend — visualize session results, hand replayer, opponent tendencies
- Charts: win rate over time, hand class distribution, action breakdown by street

## File Dependencies
| File | Type | Depends On |
|------|------|------------|
| `core/cards.py` | Core | — |
| `core/game_state.py` | Core | core/cards.py |
| `core/hand_evaluator.py` | Deterministic | core/cards.py, treys |
| `mc_cpp/monte_carlo.cpp` | C++ | pybind11 |
| `equity/monte_carlo.py` | Probabilistic | mc_cpp |
| `equity/ev_calculator.py` | Math | — |
| `sim/simulator.py` | Game loop | core/*, equity/* |
| `ml/features.py` | ML prep | core/*, equity/*, numpy |
| `ml/belief_model.py` | ML | ml/features.py, PyTorch |
| `ml/policy_model.py` | ML/RL | ml/features.py, equity/*, PyTorch |

## Implementation Order
1.  ✅ `core/hand_evaluator.py`
2.  ✅ `mc_cpp/` + `equity/monte_carlo.py`
3.  ✅ `equity/ev_calculator.py`
4.  ✅ `sim/simulator.py`
5.  ✅ `ml/features.py`
6.  ✅ `training/data_generator.py`
7.  ✅ `ml/belief_model.py`
8.  ✅ `training/train_belief.py`
9.  ⬜ `ml/policy_model.py`
10. ⬜ `training/train_policy.py`
11. ⬜ `main.py`
12. ⬜ `db/schema.py` + `db/repository.py`
13. ⬜ `app/server.py` + frontend

## Key Architecture Principle
```
ML does NOT replace poker math. It sits on top of it.

[ Game State ]
      |
[ Hand Evaluator ]        <- deterministic (treys)
      |
[ Monte Carlo EV Engine ] <- C++ (9.5ms / 10k sims)
      |
[ State Encoder ]         <- float32[21] feature vector
      |
[ Opponent Belief Model ] <- PyTorch (TODO)
      |
[ Decision Policy ]       <- PyTorch / RL (TODO)
```

## Verification
- ✅ Hand evaluator: treys-backed, precomputed lookup table
- ✅ Monte Carlo: AA vs random ~85% equity (matches preflop table)
- ✅ Simulator: 200 hands, pot awarded correctly at showdown and fold
- ✅ Features: float32[85], equity wired to MC or preflop table
- ✅ Data generator: 8,787 hands/sec, 145k policy samples from 10k hands
- ⬜ Belief model: verify val_acc improves over epochs on real data
- ⬜ Full pipeline: state → encode → belief → policy → action
