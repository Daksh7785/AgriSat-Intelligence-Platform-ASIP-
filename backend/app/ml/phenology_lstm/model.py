import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from loguru import logger

PHENOLOGY_STAGES = {
    0: "Pre-Season/Fallow",
    1: "Sowing/Germination",
    2: "Vegetative Growth",
    3: "Reproductive/Flowering",
    4: "Grain Fill/Fruiting",
    5: "Maturity/Harvest",
}

class PhenologyLSTM(nn.Module):
    """
    Bidirectional LSTM mapping temporal signatures to crop growth stages.
    Sequence-to-sequence structure outputs predictions for each time step.
    """
    def __init__(
        self,
        input_dim: int = 5,
        hidden_dim: int = 64,
        num_classes: int = 6,
        num_layers: int = 2,
        dropout: float = 0.2
    ):
        super(PhenologyLSTM, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        # Bidirectional outputs doubled feature size to hidden_dim * 2
        self.fc = nn.Linear(hidden_dim * 2, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, input_dim)
        lstm_out, _ = self.lstm(x) # shape: (batch_size, seq_len, hidden_dim * 2)
        logits = self.fc(lstm_out)   # shape: (batch_size, seq_len, num_classes)
        return logits

class PhenologyPredictor:
    """Wrapper class managing training configurations and inference for PhenologyLSTM."""
    def __init__(self, input_dim: int = 5, num_classes: int = 6):
        self.model = PhenologyLSTM(input_dim=input_dim, num_classes=num_classes)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.is_trained = False

    def train_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 20,
        batch_size: int = 32,
        lr: float = 0.001
    ) -> Dict:
        """Trains the LSTM model using CrossEntropyLoss."""
        self.model.train()
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

        X_train_t = torch.tensor(X_train, dtype=torch.float32).to(self.device)
        y_train_t = torch.tensor(y_train, dtype=torch.long).to(self.device)

        dataset = torch.utils.data.TensorDataset(X_train_t, y_train_t)
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

        logger.info(f"Training Phenology LSTM on {X_train.shape[0]} sequences...")

        for epoch in range(epochs):
            total_loss = 0.0
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                outputs = self.model(batch_x)
                # Reshape for sequence loss
                loss = criterion(outputs.view(-1, 6), batch_y.view(-1))
                loss.backward()
                optimizer.step()
                total_loss += loss.item() * batch_x.size(0)
            
            epoch_loss = total_loss / X_train.shape[0]
            if (epoch + 1) % 5 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs} | Loss: {epoch_loss:.4f}")

        self.is_trained = True
        return {"status": "success", "final_loss": epoch_loss}

    def predict_sequence(self, x_seq: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Runs inference on sequence shape (seq_len, input_dim) or (batch, seq_len, input_dim).
        Returns (stage_labels, confidence).
        """
        self.model.eval()
        with torch.no_grad():
            if len(x_seq.shape) == 2:
                # Add batch dimension
                x_tensor = torch.tensor(x_seq, dtype=torch.float32).unsqueeze(0).to(self.device)
            else:
                x_tensor = torch.tensor(x_seq, dtype=torch.float32).to(self.device)

            logits = self.model(x_tensor)
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
            
            pred_classes = np.argmax(probs, axis=-1)
            confidence = np.max(probs, axis=-1)

            if len(x_seq.shape) == 2:
                return pred_classes[0], confidence[0]
            return pred_classes, confidence

    def save(self, path: Path, filename: str = "phenology_lstm.pt"):
        """Saves model weights to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        torch.save(self.model.state_dict(), path / filename)
        logger.info(f"Phenology LSTM weights saved to {path / filename}")

    def load(self, path: Path, filename: str = "phenology_lstm.pt"):
        """Loads model weights from disk."""
        path = Path(path)
        self.model.load_state_dict(torch.load(path / filename, map_location=self.device))
        self.model.eval()
        self.is_trained = True
        logger.info(f"Phenology LSTM weights loaded from {path / filename}")
