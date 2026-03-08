import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

def prepare_features(df, target_col, lags=[1, 2, 3]):
    """
    Creates lag features for time-series prediction.
    Predicted value (t+1) based on (t, t-1, t-2).
    """
    df = df.copy()
    for lag in lags:
        df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
    
    # Drop rows with NaN from shifting
    return df.dropna()

def train_and_evaluate():
    print("🧠 Starting Model Training Phase...")
    
    # 1. Load Data
    data_path = os.path.join(os.path.dirname(__file__), "cleaned_training_data.csv")
    if not os.path.exists(data_path):
        print("❌ Error: Training data not found.")
        return
    
    df = pd.read_csv(data_path)
    
    # --- MODEL 1: ENVIRONMENTAL TREND (Predicting PM2.5) ---
    print("\n🌲 Training Line 1: Environmental Predictor...")
    df_env = prepare_features(df, 'pm2.5_ug_m3')
    X_env = df_env[['pm2.5_ug_m3_lag_1', 'pm2.5_ug_m3_lag_2', 'pm2.5_ug_m3_lag_3', 'ozone_ppb', 'no2_ppb']]
    y_env = df_env['pm2.5_ug_m3']
    
    X_train, X_test, y_train, y_test = train_test_split(X_env, y_env, test_size=0.2, random_state=42)
    model_env = RandomForestRegressor(n_estimators=100, random_state=42)
    model_env.fit(X_train, y_train)
    
    pred_env = model_env.predict(X_test)
    print(f"✅ Env Model MAE: {mean_absolute_error(y_test, pred_env):.2f}")
    print(f"✅ Env Model R2: {r2_score(y_test, pred_env):.2f}")
    
    # --- MODEL 2: PHYSIOLOGICAL TREND (Predicting Breathing Rate) ---
    print("\n🌲 Training Line 2: Physiological Predictor...")
    df_phys = prepare_features(df, 'breathing_rate_lpm')
    X_phys = df_phys[['breathing_rate_lpm_lag_1', 'breathing_rate_lpm_lag_2', 'heart_rate_bpm', 'spo2_percent']]
    y_phys = df_phys['breathing_rate_lpm']
    
    X_train, X_test, y_train, y_test = train_test_split(X_phys, y_phys, test_size=0.2, random_state=42)
    model_phys = RandomForestRegressor(n_estimators=100, random_state=42)
    model_phys.fit(X_train, y_train)
    
    pred_phys = model_phys.predict(X_test)
    print(f"✅ Phys Model MAE: {mean_absolute_error(y_test, pred_phys):.2f}")
    
    # --- MODEL 3: INTEGRATED RISK (Pattern Recognition) ---
    print("\n🌲 Training Line 3: Integrated Risk Predictor...")
    # Calculate a simple 'ground truth' risk for training (simplified PLSI)
    df['risk_score'] = (0.4 * df['pm2.5_ug_m3'] / 250) + (0.4 * df['breathing_rate_lpm'] / 100)
    df_risk = prepare_features(df, 'risk_score')
    
    X_risk = df_risk[['pm2.5_ug_m3', 'breathing_rate_lpm', 'heart_rate_bpm', 'ozone_ppb']]
    y_risk = df_risk['risk_score']
    
    X_train, X_test, y_train, y_test = train_test_split(X_risk, y_risk, test_size=0.2, random_state=42)
    model_risk = RandomForestRegressor(n_estimators=100, random_state=42)
    model_risk.fit(X_train, y_train)
    
    pred_risk = model_risk.predict(X_test)
    print(f"✅ Risk Model MAE: {mean_absolute_error(y_test, pred_risk):.4f}")
    
    # 💾 SAVE ALL MODELS
    model_dir = os.path.dirname(__file__)
    joblib.dump(model_env, os.path.join(model_dir, "env_model.joblib"))
    joblib.dump(model_phys, os.path.join(model_dir, "phys_model.joblib"))
    joblib.dump(model_risk, os.path.join(model_dir, "risk_model.joblib"))
    
    print("\n🎉 All models trained and saved successfully in ML_model/ folder!")

if __name__ == "__main__":
    train_and_evaluate()
