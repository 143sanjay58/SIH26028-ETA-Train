import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
import joblib
import os
from datetime import datetime, timezone
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class ETAPredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.model_version = "1.0"
        self.is_loaded = False
        self.model_path = Path("ml/models/eta_predictor.joblib")
        self.scaler_path = Path("ml/models/scaler.joblib")

    async def load_model(self):
        if self.model_path.exists() and self.scaler_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_loaded = True
                logger.info("ML model loaded successfully")
            except Exception as e:
                logger.error("Failed to load ML model", error=str(e))
                self.is_loaded = False
        else:
            logger.warning("ML model files not found, using fallback")
            self.is_loaded = False

    async def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_loaded:
            return self._fallback_prediction(features)

        try:
            X = self._prepare_features(features)
            X_scaled = self.scaler.transform(X)
            delay_prediction = self.model.predict(X_scaled)[0]

            if hasattr(self.model, "predict_proba"):
                confidence = 0.8
            else:
                confidence = 0.75

            return {
                "delay_minutes": max(0, float(delay_prediction)),
                "confidence": confidence,
                "model_version": self.model_version,
            }
        except Exception as e:
            logger.error("ML prediction error", error=str(e))
            return self._fallback_prediction(features)

    def _prepare_features(self, features: Dict[str, Any]) -> np.ndarray:
        X = np.array([[features.get(name, 0) for name in self.feature_names]])
        return X

    def _fallback_prediction(self, features: Dict[str, Any]) -> Dict[str, Any]:
        current_delay = features.get("current_delay", 0)
        section_avg = features.get("section_historical_avg", 60)
        scheduled = features.get("section_scheduled_time", 60)

        predicted_delay = current_delay * 1.1
        if features.get("congestion_level", 0) > 1:
            predicted_delay += 5
        if features.get("weather_severity", 0) > 0:
            predicted_delay += 3

        return {
            "delay_minutes": predicted_delay,
            "confidence": 0.6,
            "model_version": "fallback",
        }

    async def train(self, X_train: np.ndarray, y_train: np.ndarray, feature_names: List[str]):
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

        self.feature_names = feature_names

        X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42)

        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        self.model = HistGradientBoostingRegressor(
            max_iter=200,
            learning_rate=0.1,
            max_depth=6,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
        )
        self.model.fit(X_train_scaled, y_train)

        y_pred = self.model.predict(X_val_scaled)
        mae = mean_absolute_error(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        r2 = r2_score(y_val, y_pred)

        logger.info("Model trained", mae=mae, rmse=rmse, r2=r2)

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)

        self.is_loaded = True
        self.model_version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        return {
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "model_version": self.model_version,
        }

    def get_feature_importance(self) -> Dict[str, float]:
        if not self.is_loaded or not hasattr(self.model, "feature_importances_"):
            return {}

        importances = self.model.feature_importances_
        return dict(zip(self.feature_names, importances.tolist()))