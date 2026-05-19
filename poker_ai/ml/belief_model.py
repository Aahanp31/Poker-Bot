import torch
import torch.nn as nn

from poker_ai.ml.features import FEATURE_DIM

NUM_HAND_CLASSES = 10  # 0=High Card .. 9=Royal Flush


# This class is a feedforward neural net that predicts what hand class an opponent
# is holding. It takes in the encoded game state and outputs a probability
# distribution over the 10 hand classes.
class BeliefModel(nn.Module):

    def __init__(self, input_dim=FEATURE_DIM, hidden=256,
                 num_classes=NUM_HAND_CLASSES):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden, hidden // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden // 2, num_classes),
        )

    # This method runs a forward pass through the network and returns raw logits.
    # Parameters:
    #   - x: float32 tensor of shape (batch, FEATURE_DIM)
    # Returns:
    #   - Tensor: shape (batch, NUM_HAND_CLASSES), unnormalized logits
    def forward(self, x):
        return self.net(x)

    # This method returns a softmax probability distribution over hand classes.
    # Parameters:
    #   - x: float32 tensor of shape (batch, FEATURE_DIM)
    # Returns:
    #   - Tensor: shape (batch, NUM_HAND_CLASSES), probabilities summing to 1
    def predict_probs(self, x):
        with torch.no_grad():
            return torch.softmax(self.forward(x), dim=-1)

    # This method returns the most likely hand class for each sample in the batch.
    # Parameters:
    #   - x: float32 tensor of shape (batch, FEATURE_DIM)
    # Returns:
    #   - Tensor: shape (batch,), integer class indices 0-9
    def predict(self, x):
        with torch.no_grad():
            return self.forward(x).argmax(dim=-1)
