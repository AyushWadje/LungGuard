# System Architecture & AI Requirements (SystemAI)

This document formalizes the system layout, architecture flow, and necessary requirements for the **AeroLung** platform. It provides the definitive technical blueprint utilized by Team Syntax_Glitch.

---

## 1. System Overview

AeroLung operates on a highly decoupled client-server architecture. The system relies on heavy computations done server-side using pre-trained Machine Learning (ML) Models, served through high-performance asynchronous API endpoints. 

### Architecture Diagram

```mermaid
graph TD
    A[Sensors / OpenAQ API / OpenWeatherMap] -->|Live Pollutants| B(FastAPI Backend)
    C[Wearable Devices / User Data] -->|Heart Rate, SpO2| B
    
    subgraph PLSI Engine (AI Core)
        B --> D{TrendPredictor}
        D -->|pm2.5, lags| E(Environment Model)
        D -->|breathing rate, HR| F(Physiology Model)
        D -->|features| G(Risk Model)
        E --> H[Alert Engine]
        F --> H
        G --> H
    end
    
    H -->|Risk Score & Forecasts| B
    B -->|REST JSON| I[AeroLung React Dashboard]
    B -->|REST JSON| J[Mobile End-Users]
```

---

## 2. Artificial Intelligence Requirements

The core of the system is the **Personal Lung Stress Index (PLSI) Engine**, which uses Scikit-Learn RandomForest Classifiers/Regressors to provide real-time inference.

### Data Requirements
- **Inputs Required:**
  - `pm25`, `pm10`, `o3`, `no2` (from environmental APIs).
  - `heart_rate`, `spo2`, `breathing_rate`, `systolic_bp`, `diastolic_bp` (from health data).
  - `age`, `smoking_history`, `pre_existing_conditions`.
- **Latency Requirement:** Predictions must resolve in `<200ms` for real-time mobile application tracking telemetry.

### Model Manifest
The `TrendPredictor` module dynamically loads the following serialized `.joblib` models into memory:

| Model ID | File Name | Purpose | Output |
|----------|-----------|---------|--------|
| `M-ENV` | `env_model.joblib` | Forecasting immediate chemical pollution trends | PM2.5 trajectory |
| `M-PHY` | `phys_model.joblib` | Predicting breathing rate distress | Breathing Rate LPM |
| `M-RSK` | `risk_model.joblib` | Synthesizing environmental and physical strain | Numerical Risk |

---

## 3. APIs & External Dependency Integration

To function securely, the backend relies on environment variables mapped to external services.

### API Keys (`.env` Configuration)
Must be deployed defensively in the environment runtime:
- `OWM_API_KEY`: OpenWeatherMap token (Live Air Pollution endpoint).
- `OPENAQ_API_KEY`: OpenAQ API Key (Sector by sector sensor polling).

### Backend Framework
- **FastAPI / Uvicorn:** Chosen for native asynchronous (`asyncio`) handling. The `aiohttp` library is mandated for polling external sensory networks (OpenWeatherMap) without blocking the main React Dashboard event loop.

---

## 4. Dashboard Requirements

- **Framework:** React 19 + Vite.
- **Styling:** TailwindCSS 3.4 (Strictly adhered to `bg-background-light`, `dark:bg-background-dark` schema).
- **Communication:** Must consume the backend API via the base configured URL, injectable through `import.meta.env.VITE_API_URL` to ensure the dashboard works immediately upon Vercel/Netlify hackathon deployment without demanding a localhost bypass.
- **Routing:** Handles complex analytics interfaces (Historical Analytics, Alerts, Demographics) via `react-router-dom`.
