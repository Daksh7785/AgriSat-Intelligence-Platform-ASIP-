import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestClassifier
from typing import Dict, List, Tuple

# Try imports for gradient boosting libraries
try:
    import xgboost as xgb
except ImportError:
    xgb = None

try:
    import lightgbm as lgb
except ImportError:
    lgb = None

try:
    import catboost as cb
except ImportError:
    cb = None

# Set random seed
torch.manual_seed(42)
np.random.seed(42)

# --- DEEP LEARNING ARCHITECTURES IN PYTORCH ---

class TemporalCNN(nn.Module):
    def __init__(self, input_dim: int, num_classes: int, seq_len: int):
        super(TemporalCNN, self).__init__()
        self.conv1 = nn.Conv1d(in_channels=input_dim, out_channels=32, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.fc = nn.Linear(64, num_classes)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Input shape: (batch_size, seq_len, input_dim) -> transpose to (batch_size, input_dim, seq_len)
        x = x.transpose(1, 2)
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.pool(x).squeeze(-1)
        x = self.fc(x)
        return x

class LSTMClassifier(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, num_classes: int, num_layers: int = 1):
        super(LSTMClassifier, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_classes)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Input shape: (batch_size, seq_len, input_dim)
        out, (hn, cn) = self.lstm(x)
        # Take the output of the last time step
        out = self.fc(out[:, -1, :])
        return out

class TransformerTimeSeriesClassifier(nn.Module):
    def __init__(self, input_dim: int, num_classes: int, d_model: int = 32, nhead: int = 4, num_layers: int = 1):
        super(TransformerTimeSeriesClassifier, self).__init__()
        self.input_projection = nn.Linear(input_dim, d_model)
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, dim_feedforward=64, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc = nn.Linear(d_model, num_classes)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Project features to d_model
        x = self.input_projection(x)
        x = self.transformer(x)
        # Global average pooling over time dimension
        x = torch.mean(x, dim=1)
        x = self.fc(x)
        return x

# --- AUTOML ENSEMBLE SERVICE ---

class AutoMLCropClassifier:
    def __init__(self, seq_len: int = 12, input_dim: int = 6):
        self.seq_len = seq_len
        self.input_dim = input_dim
        self.classes = ['wheat', 'rice', 'cotton', 'sugarcane', 'fallow']
        self.num_classes = len(self.classes)
        
        # Instantiate classical models
        self.rf = RandomForestClassifier(n_estimators=100, random_state=42)
        
        self.xgb_model = None
        if xgb:
            self.xgb_model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42)
            
        self.lgb_model = None
        if lgb:
            self.lgb_model = lgb.LGBMClassifier(random_state=42, verbose=-1)
            
        self.cb_model = None
        if cb:
            self.cb_model = cb.CatBoostClassifier(verbose=0, random_state=42)
            
        # Instantiate deep models
        self.tcnn = TemporalCNN(input_dim, self.num_classes, seq_len)
        self.lstm = LSTMClassifier(input_dim, hidden_dim=32, num_classes=self.num_classes)
        self.transformer = TransformerTimeSeriesClassifier(input_dim, self.num_classes)
        
        self.is_trained = False

    def train(self, X: np.ndarray, y: np.ndarray):
        """
        Trains all models on historical dataset.
        X shape: (num_samples, seq_len, input_dim)
        y shape: (num_samples,) -> integer class labels
        """
        # Flatten temporal dimension for tabular classifiers
        num_samples = X.shape[0]
        X_flat = X.reshape(num_samples, -1)
        
        # 1. Train Random Forest
        self.rf.fit(X_flat, y)
        
        # 2. Train XGBoost
        if self.xgb_model:
            self.xgb_model.fit(X_flat, y)
            
        # 3. Train LightGBM
        if self.lgb_model:
            self.lgb_model.fit(X_flat, y)
            
        # 4. Train CatBoost
        if self.cb_model:
            self.cb_model.fit(X_flat, y)
            
        # 5. Train Deep Learning models (simplified fast training)
        X_tensor = torch.tensor(X, dtype=torch.float32)
        y_tensor = torch.tensor(y, dtype=torch.long)
        
        # Set up loss and optimizers
        criterion = nn.CrossEntropyLoss()
        optimizers = [
            torch.optim.Adam(self.tcnn.parameters(), lr=0.01),
            torch.optim.Adam(self.lstm.parameters(), lr=0.01),
            torch.optim.Adam(self.transformer.parameters(), lr=0.01)
        ]
        
        models_list = [self.tcnn, self.lstm, self.transformer]
        
        # Fast 10 epochs training for demonstration
        for model, opt in zip(models_list, optimizers):
            model.train()
            for epoch in range(15):
                opt.zero_grad()
                outputs = model(X_tensor)
                loss = criterion(outputs, y_tensor)
                loss.backward()
                opt.step()
                
        self.is_trained = True

    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Combines all model probabilities via soft voting.
        Calculates predicted class index, probability vector, and entropy uncertainty.
        X shape: (num_samples, seq_len, input_dim)
        """
        num_samples = X.shape[0]
        X_flat = X.reshape(num_samples, -1)
        
        # Dynamic weights (can be tuned or set based on validation accuracy)
        # Target accuracy > 85% is achievable through ensembling
        probabilities = []
        
        # 1. RF
        probabilities.append(self.rf.predict_proba(X_flat))
        
        # 2. XGBoost
        if self.xgb_model:
            probabilities.append(self.xgb_model.predict_proba(X_flat))
        else:
            probabilities.append(self.rf.predict_proba(X_flat)) # Fallback duplicate
            
        # 3. LightGBM
        if self.lgb_model:
            probabilities.append(self.lgb_model.predict_proba(X_flat))
        else:
            probabilities.append(self.rf.predict_proba(X_flat))
            
        # 4. CatBoost
        if self.cb_model:
            probabilities.append(self.cb_model.predict_proba(X_flat))
        else:
            probabilities.append(self.rf.predict_proba(X_flat))
            
        # 5. Deep Models Inference
        X_tensor = torch.tensor(X, dtype=torch.float32)
        self.tcnn.eval()
        self.lstm.eval()
        self.transformer.eval()
        
        with torch.no_grad():
            tcnn_probs = torch.softmax(self.tcnn(X_tensor), dim=1).numpy()
            lstm_probs = torch.softmax(self.lstm(X_tensor), dim=1).numpy()
            trans_probs = torch.softmax(self.transformer(X_tensor), dim=1).numpy()
            
        probabilities.extend([tcnn_probs, lstm_probs, trans_probs])
        
        # Average probability across 7 models
        avg_probs = np.mean(probabilities, axis=0)  # Shape: (num_samples, num_classes)
        
        # Crop class predictions
        pred_classes = np.argmax(avg_probs, axis=1)
        
        # Calculate uncertainty: Shannon Entropy H(x) = -sum(p * log(p))
        eps = 1e-9
        uncertainty = -np.sum(avg_probs * np.log2(avg_probs + eps), axis=1)
        # Normalize uncertainty to [0, 1] using log2(num_classes)
        normalized_uncertainty = uncertainty / np.log2(self.num_classes)
        
        return pred_classes, avg_probs, normalized_uncertainty

    def get_crop_name(self, class_idx: int) -> str:
        return self.classes[class_idx]
