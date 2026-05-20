import torch
import torch.nn as nn
from torch.distributions import Categorical

from poker_ai.ml.features import FEATURE_DIM
from poker_ai.ml.belief_model import NUM_HAND_CLASSES

# state vector + belief model output probabilities
INPUT_DIM  = FEATURE_DIM + NUM_HAND_CLASSES  # 85 + 10 = 95
NUM_ACTIONS = 3  # 0=fold  1=check/call  2=raise


# This class is an actor-critic policy network for poker decision making. It takes
# in the game state and opponent belief probabilities, then outputs both an action
# distribution and a state value estimate used during PPO training.
class PolicyModel(nn.Module):

    def __init__(self, input_dim=INPUT_DIM, hidden=256, num_actions=NUM_ACTIONS):
        super().__init__()

        # shared feature extractor
        self.trunk = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden // 2),
            nn.ReLU(),
        )

        self.policy_head = nn.Linear(hidden // 2, num_actions)  # action logits
        self.value_head  = nn.Linear(hidden // 2, 1)            # state value

    # This method runs a forward pass and returns action logits and the state value.
    # Parameters:
    #   - x: float32 tensor of shape (batch, INPUT_DIM)
    # Returns:
    #   - logits: shape (batch, NUM_ACTIONS), unnormalized action scores
    #   - value:  shape (batch, 1), estimated cumulative reward from this state
    def forward(self, x):
        features = self.trunk(x)
        return self.policy_head(features), self.value_head(features)

    # This method samples an action from the policy distribution and returns it
    # along with its log probability and the state value — all needed for PPO.
    # Parameters:
    #   - x: float32 tensor of shape (batch, INPUT_DIM)
    # Returns:
    #   - action:    shape (batch,), sampled action indices 0-2
    #   - log_prob:  shape (batch,), log probability of the sampled action
    #   - value:     shape (batch, 1), estimated state value
    #   - entropy:   shape (batch,), distribution entropy (used as PPO bonus)
    def act(self, x):
        logits, value = self.forward(x)
        dist     = Categorical(logits=logits)
        action   = dist.sample()
        return action, dist.log_prob(action), value, dist.entropy()

    # This method returns the log probability and entropy for given state-action pairs.
    # Used during PPO updates to evaluate old actions under the updated policy.
    # Parameters:
    #   - x:      float32 tensor of shape (batch, INPUT_DIM)
    #   - action: int64 tensor of shape (batch,)
    # Returns:
    #   - log_prob: shape (batch,)
    #   - entropy:  shape (batch,)
    #   - value:    shape (batch, 1)
    def evaluate(self, x, action):
        logits, value = self.forward(x)
        dist = Categorical(logits=logits)
        return dist.log_prob(action), dist.entropy(), value

    # This method greedily picks the best action. Used at inference time, not training.
    # Parameters:
    #   - x: float32 tensor of shape (batch, INPUT_DIM)
    # Returns:
    #   - Tensor: shape (batch,), action indices 0-2
    def predict(self, x):
        with torch.no_grad():
            logits, _ = self.forward(x)
            return logits.argmax(dim=-1)


# This function builds the combined input vector for the policy model by
# concatenating the game state features with the belief model's output.
# Parameters:
#   - state:        float32 tensor of shape (batch, FEATURE_DIM)
#   - belief_probs: float32 tensor of shape (batch, NUM_HAND_CLASSES)
# Returns:
#   - Tensor: shape (batch, INPUT_DIM), ready to feed into PolicyModel
def make_policy_input(state, belief_probs):
    return torch.cat([state, belief_probs], dim=-1)
