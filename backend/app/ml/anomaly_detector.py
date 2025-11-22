import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime, timezone
import json

class AnomalyDetector:
    def __init__(self, models_dir='app/ml/models'):
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)
        self.models = {}
        self.scalers = {}
    
    def extract_features(self, device_data, current_behavior):
        features = []
        
        current_hour = datetime.now(timezone.utc).hour
        features.extend([
            np.sin(2 * np.pi * current_hour / 24),
            np.cos(2 * np.pi * current_hour / 24)
        ])
        
        current_area = hash(current_behavior.get('area', 'unknown')) % 100 / 100.0
        features.append(current_area)
        
        is_weekend = 1 if datetime.now(timezone.utc).weekday() >= 5 else 0
        features.append(is_weekend)
        
        connection_type = 1 if current_behavior.get('action') == 'connect' else 0
        features.append(connection_type)
        
        return np.array(features).reshape(1, -1)
    
    def train_model(self, device_id, normal_behavior_data):
        if len(normal_behavior_data) < 10:
            return False
        
        features = []
        for behavior in normal_behavior_data:
            feature_vector = self.extract_features({}, behavior)
            features.append(feature_vector.flatten())
        
        features = np.array(features)
        
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)
        
        model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        model.fit(scaled_features)
        
        model_path = os.path.join(self.models_dir, f'model_{device_id}.joblib')
        scaler_path = os.path.join(self.models_dir, f'scaler_{device_id}.joblib')
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        self.models[device_id] = model
        self.scalers[device_id] = scaler
        
        return True
    
    def detect_anomaly(self, device_id, current_behavior):
        model_path = os.path.join(self.models_dir, f'model_{device_id}.joblib')
        scaler_path = os.path.join(self.models_dir, f'scaler_{device_id}.joblib')
        
        if not os.path.exists(model_path):
            return True
        
        if device_id not in self.models:
            self.models[device_id] = joblib.load(model_path)
            self.scalers[device_id] = joblib.load(scaler_path)
        
        features = self.extract_features({}, current_behavior)
        scaled_features = self.scalers[device_id].transform(features)
        prediction = self.models[device_id].predict(scaled_features)
        
        return prediction[0] == -1

anomaly_detector = AnomalyDetector()