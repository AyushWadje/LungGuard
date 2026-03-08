import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report

def get_level(val):
    """Maps PM2.5 to our 5 standard levels (Simplified version of plsi_engine logic)"""
    if val < 50: return "Low"
    if val < 100: return "Mild"
    if val < 150: return "Medium"
    if val < 250: return "High"
    return "Extreme"

def generate_confusion_matrix():
    print("📋 Generating Confusion Matrix for Environmental Model...")
    
    # Load Model and Data
    model_path = os.path.join(os.path.dirname(__file__), "env_model.joblib")
    data_path = os.path.join(os.path.dirname(__file__), "cleaned_training_data.csv")
    
    if not os.path.exists(model_path) or not os.path.exists(data_path):
        print("❌ Error: Model or data not found.")
        return

    model = joblib.load(model_path)
    df = pd.read_csv(data_path)
    
    # Re-prepare the same features used in training
    target_col = 'pm2.5_ug_m3'
    lags = [1, 2, 3]
    df_env = df.copy()
    for lag in lags:
        df_env[f'{target_col}_lag_{lag}'] = df_env[target_col].shift(lag)
    df_env = df_env.dropna()
    
    X = df_env[['pm2.5_ug_m3_lag_1', 'pm2.5_ug_m3_lag_2', 'pm2.5_ug_m3_lag_3', 'ozone_ppb', 'no2_ppb']]
    y_actual = df_env[target_col]
    
    # Get predictions
    _, X_test, _, y_test = train_test_split(X, y_actual, test_size=0.2, random_state=42)
    y_pred = model.predict(X_test)
    
    # BINNING: Convert continuous values to 5 Categories
    levels = ["Low", "Mild", "Medium", "High", "Extreme"]
    y_test_cat = [get_level(v) for v in y_test]
    y_pred_cat = [get_level(v) for v in y_pred]
    
    # Generate Matrix
    cm = confusion_matrix(y_test_cat, y_pred_cat, labels=levels)
    cm_df = pd.DataFrame(cm, index=levels, columns=levels)
    
    print("\n--- CONFUSION MATRIX (Pollutant Severity Levels) ---")
    print(cm_df)
    print("\n--- CLASSIFICATION REPORT ---")
    print(classification_report(y_test_cat, y_pred_cat, labels=levels, zero_division=0))

if __name__ == "__main__":
    generate_confusion_matrix()
