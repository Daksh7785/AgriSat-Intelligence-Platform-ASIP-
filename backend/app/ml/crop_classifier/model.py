import numpy as np
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, cohen_kappa_score, f1_score,
    classification_report, confusion_matrix
)
import xgboost as xgb
from loguru import logger

# ── Crop Class Definitions ─────────────────────────────────────────────────
CROP_CLASSES = {
    0: "Wheat",
    1: "Rice/Paddy",
    2: "Cotton",
    3: "Sugarcane",
    4: "Maize",
    5: "Soybean",
    6: "Groundnut",
    7: "Mustard/Rapeseed",
    8: "Vegetables",
    9: "Fallow/Barren",
}

CROP_CLASS_COLORS = {
    0: "#F5E642",   # Wheat — golden yellow
    1: "#2ECC71",   # Rice — bright green
    2: "#E74C3C",   # Cotton — red
    3: "#8E44AD",   # Sugarcane — purple
    4: "#E67E22",   # Maize — orange
    5: "#27AE60",   # Soybean — dark green
    6: "#F39C12",   # Groundnut — amber
    7: "#D4AC0D",   # Mustard — mustard yellow
    8: "#1ABC9C",   # Vegetables — teal
    9: "#95A5A6",   # Fallow — grey
}

class CropClassifierModel:
    """
    Ensemble crop classifier combining Random Forest and XGBoost.
    Uses 70-dimensional multi-temporal feature vectors per pixel.
    """

    def __init__(
        self,
        n_estimators_rf: int = 200,
        n_estimators_xgb: int = 500,
        max_depth_rf: int = 20,
        n_jobs: int = -1,
        random_state: int = 42,
    ):
        self.n_estimators_rf = n_estimators_rf
        self.n_estimators_xgb = n_estimators_xgb
        self.random_state = random_state
        self.n_jobs = n_jobs
        self.is_trained = False
        self.feature_names: List[str] = []
        self.model: Optional[Pipeline] = None
        self._build_model(max_depth_rf)

    def _build_model(self, max_depth_rf: int):
        """Build the ensemble pipeline."""
        rf = RandomForestClassifier(
            n_estimators=self.n_estimators_rf,
            max_depth=max_depth_rf,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features="sqrt",
            n_jobs=self.n_jobs,
            random_state=self.random_state,
            class_weight="balanced",
            oob_score=True,
        )

        xgb_clf = xgb.XGBClassifier(
            n_estimators=self.n_estimators_xgb,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=self.random_state,
            n_jobs=self.n_jobs,
            tree_method="hist",
        )

        ensemble = VotingClassifier(
            estimators=[("rf", rf), ("xgb", xgb_clf)],
            voting="soft",
            weights=[0.45, 0.55],
            n_jobs=self.n_jobs,
        )

        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", ensemble),
        ])

    def build_feature_names(self, n_temporal_steps: int = 16) -> List[str]:
        """Generate feature names for the 70-dimensional feature vector."""
        features = []
        # Temporal optical features (16 timesteps × 4 indices = 64)
        for t in range(n_temporal_steps):
            for idx in ["NDVI", "EVI", "NDWI", "LSWI"]:
                features.append(f"{idx}_t{t:02d}")
        # SAR features (8 timesteps × 3 = 24)
        for t in range(0, n_temporal_steps, 2):
            for pol in ["VV_dB", "VH_dB", "VHVV_ratio"]:
                features.append(f"{pol}_t{t:02d}")
        # Texture features (3)
        for tex in ["GLCM_contrast", "GLCM_entropy", "GLCM_homogeneity"]:
            features.append(tex)
        # Static features (3)
        features.extend(["elevation_m", "slope_deg", "soil_type_enc"])
        # Phenological summary (4)
        features.extend(["NDVI_max", "NDVI_integral", "SOS_doy", "EOS_doy"])

        self.feature_names = features
        return features

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
    ) -> Dict:
        """
        Train the ensemble model.
        Returns training metrics dict.
        """
        logger.info(
            f"Training crop classifier on {X_train.shape[0]} samples, "
            f"{X_train.shape[1]} features, {len(np.unique(y_train))} classes"
        )

        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Training accuracy
        y_pred_train = self.model.predict(X_train)
        train_oa = accuracy_score(y_train, y_pred_train)
        train_kappa = cohen_kappa_score(y_train, y_pred_train)

        metrics = {
            "train_overall_accuracy": float(train_oa),
            "train_kappa": float(train_kappa),
        }

        if X_val is not None and y_val is not None:
            y_pred_val = self.model.predict(X_val)
            val_oa = accuracy_score(y_val, y_pred_val)
            val_kappa = cohen_kappa_score(y_val, y_pred_val)
            val_f1_per_class = f1_score(
                y_val, y_pred_val, average=None,
                labels=list(CROP_CLASSES.keys())
            )
            metrics.update({
                "val_overall_accuracy": float(val_oa),
                "val_kappa": float(val_kappa),
                "val_f1_per_class": {
                    CROP_CLASSES[i]: float(f1)
                    for i, f1 in enumerate(val_f1_per_class)
                    if i < len(val_f1_per_class)
                },
                "val_classification_report": classification_report(
                    y_val, y_pred_val,
                    target_names=list(CROP_CLASSES.values()),
                    output_dict=True,
                ),
            })
            logger.info(
                f"Validation OA: {val_oa:.4f} | Kappa: {val_kappa:.4f}"
            )

        return metrics

    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict crop types.
        Returns (class_labels, confidence_scores).
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() or load() first.")

        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)
        confidence = np.max(probabilities, axis=1)
        return predictions, confidence

    def predict_map(
        self,
        feature_array: np.ndarray,
        height: int,
        width: int,
        batch_size: int = 10000,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict on a 2D raster array (H×W×Features) in batches.
        Returns (class_map H×W, confidence_map H×W).
        """
        n_pixels = height * width
        X_flat = feature_array.reshape(n_pixels, -1)

        # Remove NaN pixels
        valid_mask = ~np.any(np.isnan(X_flat), axis=1)
        X_valid = X_flat[valid_mask]

        predictions_flat = np.full(n_pixels, -1, dtype=np.int8)
        confidence_flat = np.zeros(n_pixels, dtype=np.float32)

        # Batch inference
        for start in range(0, len(X_valid), batch_size):
            end = min(start + batch_size, len(X_valid))
            batch = X_valid[start:end]
            preds, confs = self.predict(batch)
            valid_indices = np.where(valid_mask)[0][start:end]
            predictions_flat[valid_indices] = preds
            confidence_flat[valid_indices] = confs

        class_map = predictions_flat.reshape(height, width)
        confidence_map = confidence_flat.reshape(height, width)
        return class_map, confidence_map

    def get_feature_importance(self) -> Dict[str, float]:
        """Return feature importance from the RF component."""
        rf_model = self.model.named_steps["classifier"].estimators_[0]
        importances = rf_model.feature_importances_
        return {
            name: float(imp)
            for name, imp in zip(self.feature_names, importances)
        }

    def save(self, path: Path):
        """Save model to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        with open(path / "crop_classifier.pkl", "wb") as f:
            pickle.dump(self, f)
        logger.info(f"Model saved to {path}/crop_classifier.pkl")

    @classmethod
    def load(cls, path: Path) -> "CropClassifierModel":
        """Load model from disk."""
        path = Path(path)
        with open(path / "crop_classifier.pkl", "rb") as f:
            model = pickle.load(f)
        model.is_trained = True
        logger.info(f"Model loaded from {path}/crop_classifier.pkl")
        return model
