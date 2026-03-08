# Respiratory Health Intelligence API (LungGuard AI) 🫁

A real-time machine learning system that predicts respiratory health risks by correlating environmental pollutants with user physiological data.

## 🌟 Key Features
- **Personalized Lung Stress Index (PLSI):** Real-time calculation of lung stress.
- **3-Line Trend Forecasting:** ML-powered forecasts for the next 3 hours:
  - **Line 1 (Environmental):** PM2.5 concentration trends based on Delhi historical data.
  - **Line 2 (Physiological):** Breathing Rate predictions based on heart rate patterns.
  - **Line 3 (Integrated):** Combined Health Risk projection.
- **Exposure Timeline:** SQLite-backed logging of cumulative pollutant doses.

## 🛠️ Installation & Setup
1. **Dependencies:**
   ```bash
   pip install fastapi uvicorn scikit-learn joblib pandas requests
   ```
2. **Start the API:**
   ```bash
   python main.py
   ```
   The API will be available at `http://127.0.0.1:8000`.

## 🛰️ API Endpoints

### 1. Estimate Lung Impact
- **Endpoint:** `POST /v1/estimate`
- **Payload:** Includes `environment` (PM2.5, O3), `physiology` (Heart Rate, Breathing), and `profile`.
- **Response:**
  - `plsi_score`: Current risk score (0-100).
  - `forecasts`: **Continuous numerical arrays** for the next 3 hours (Environment, Physiology, Risk). Use these to draw trend lines on your frontend.

### 2. Exposure History
- **Endpoint:** `GET /v1/timeline?hours=24`
- **Response:** Historical exposure logs and cumulative dose analysis.

## 🧠 Machine Learning Structure
The models are located in the `ML_model/` folder:
- `env_model.joblib`: Random Forest for air quality forecasting.
- `phys_model.joblib`: Regressor for physiological demand patterns.
- `risk_model.joblib`: Integrated pattern recognition brain.

---
*Ready for integration with React, Mobile, or Web dashboards.*
