import json
import joblib
import os
import numpy as np
from typing import Dict, List, Optional

class TrendPredictor:
    """Loads trained ML models and provides continuous numerical forecasts."""
    def __init__(self, model_dir: str = "ML_model"):
        self.model_dir = model_dir
        self.env_model = self._load_model("env_model.joblib")
        self.phys_model = self._load_model("phys_model.joblib")
        self.risk_model = self._load_model("risk_model.joblib")

    def _load_model(self, name):
        path = os.path.join(self.model_dir, name)
        if os.path.exists(path):
            return joblib.load(path)
        return None

    def predict_trends(self, pollutants: Dict, physiology: Dict) -> Dict:
        """Generates 3-hour numerical forecasts for all 3 lines."""
        forecasts = {
            "environment_pm25": [],
            "physiology_breathing": [],
            "integrated_risk": []
        }
        
        # Start with current values
        curr_pm25 = pollutants.get('pm25', 50)
        curr_br = physiology.get('breathing_rate_lpm', 15)
        curr_hr = physiology.get('heart_rate', 75)
        curr_spo2 = physiology.get('spo2', 97)
        curr_o3 = pollutants.get('o3', 30)

        # Simple iterative prediction for the next 3 hours
        for i in range(1, 4):
            # 1. Environment Prediction (Line 1)
            if self.env_model:
                # Predicting PM2.5 based on lags and chemical drivers
                # We simulate shifting lags manually for this demo
                pred_pm25 = self.env_model.predict([[curr_pm25, curr_pm25*0.9, curr_pm25*0.8, curr_o3, 40]])[0]
                curr_pm25 = pred_pm25
            else:
                curr_pm25 += np.random.normal(2, 5) # Fallback with slight rise
            forecasts["environment_pm25"].append(round(curr_pm25, 2))

            # 2. Physiology Prediction (Line 2)
            if self.phys_model:
                pred_br = self.phys_model.predict([[curr_br, curr_br*0.9, curr_hr, curr_spo2]])[0]
                curr_br = pred_br
            else:
                curr_br += np.random.normal(0.5, 1) # Fallback
            forecasts["physiology_breathing"].append(round(curr_br, 2))

            # 3. Integrated Risk (Line 3)
            if self.risk_model:
                pred_risk = self.risk_model.predict([[curr_pm25, curr_br, curr_hr, curr_o3]])[0]
            else:
                # Basic calculation if model is missing
                pred_risk = (0.4 * curr_pm25 / 250) + (0.4 * curr_br / 100)
            forecasts["integrated_risk"].append(round(float(pred_risk), 4))

        return forecasts

class AlertEngine:
    @staticmethod
    def _get_level(score: float) -> str:
        if score < 20: return "Low"
        if score < 40: return "Mild"
        if score < 60: return "Medium"
        if score < 80: return "High"
        return "Extreme"

    @classmethod
    def generate_alerts(cls, plsi: float, risks: Dict, pollutants: Dict, profile: Dict) -> Dict:
        alerts = {
            "plsi": {"level": cls._get_level(plsi), "score": plsi},
            "environmental": []
        }
        if pollutants.get('pm25', 0) > 100:
            alerts["environmental"].append({"parameter": "PM2.5", "level": "High", "action": "Use an N95 mask."})
        return alerts

class PLSICalculator:
    def __init__(self, w1=0.4, w2=0.35, w3=0.25):
        self.w1, self.w2, self.w3 = w1, w2, w3
        self.predictor = TrendPredictor()

    def calculate(self, pollutants: Dict, breathing_rate: float, profile: Dict, physiology: Dict) -> Dict:
        # 1. Base Score (Simplified)
        e_norm = min(1.0, pollutants.get('pm25', 0) / 250)
        p_norm = min(1.0, (breathing_rate - 5) / 115)
        age = profile.get('age', 30)
        b_risk = 0.1 if (18 < age < 45) else 0.5
        
        plsi_score = (self.w1 * e_norm + self.w2 * p_norm + self.w3 * b_risk) * 100
        
        # 2. Generate Forecasts (Phase 3 Models)
        forecasts = self.predictor.predict_trends(pollutants, physiology)
        
        return {
            "plsi_score": round(plsi_score, 2),
            "interpretation": AlertEngine._get_level(plsi_score),
            "alerts": AlertEngine.generate_alerts(plsi_score, {}, pollutants, profile),
            "impact_explanations": [
                f"Environment accounts for {round(e_norm*100)}% of stress.",
                f"Physical activity accounts for {round(p_norm*100)}% of impact."
            ],
            "disease_risks": {"asthma_exacerbation": 0.1, "copd_flare_up": 0.05, "general_inflammation": round(plsi_score/100, 2)},
            "risk_drivers": ["PM2.5 levels are the primary driver."],
            "breakdown": {
                "environmental_stress": round(e_norm, 4),
                "physical_demand": round(p_norm, 4),
                "biological_vulnerability": round(b_risk, 4)
            },
            "forecasts": forecasts
        }
