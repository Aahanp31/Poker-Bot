import argparse
import os

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split

from poker_ai.ml.belief_model import BeliefModel


def load_data(path):
    data   = np.load(os.path.join(path, 'belief.npz'))
    states = torch.from_numpy(data['states'])
    labels = torch.from_numpy(data['labels'])
    return TensorDataset(states, labels)


# This function trains the BeliefModel on belief.npz data and saves the weights.
# Parameters:
#   - data_path: directory containing belief.npz
#   - save_path: file path to write the trained model weights
#   - epochs: number of full passes over the training set
#   - batch_size: samples per gradient update
#   - lr: learning rate for Adam optimizer
#   - val_split: fraction of data held out for validation
def train(data_path='data', save_path='data/belief_model.pt',
          epochs=20, batch_size=256, lr=1e-3, val_split=0.1):

    dataset = load_data(data_path)
    n_val   = max(1, int(len(dataset) * val_split))
    n_train = len(dataset) - n_val
    train_ds, val_ds = random_split(dataset, [n_train, n_val])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader   = DataLoader(val_ds,   batch_size=batch_size)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model  = BeliefModel().to(device)
    opt    = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            total_loss += loss.item() * len(x)

        model.eval()
        correct = 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                correct += (model(x).argmax(dim=-1) == y).sum().item()

        acc = correct / n_val
        print(f"Epoch {epoch:3d}/{epochs}  "
              f"loss={total_loss/n_train:.4f}  val_acc={acc:.3f}")

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save(model.state_dict(), save_path)
    print(f"Saved → {save_path}")
    return model


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data',   default='data')
    parser.add_argument('--save',   default='data/belief_model.pt')
    parser.add_argument('--epochs', type=int,   default=20)
    parser.add_argument('--batch',  type=int,   default=256)
    parser.add_argument('--lr',     type=float, default=1e-3)
    args = parser.parse_args()

    train(data_path=args.data, save_path=args.save,
          epochs=args.epochs, batch_size=args.batch, lr=args.lr)
