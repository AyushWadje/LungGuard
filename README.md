<div align="center">
  <img src="https://img.shields.io/badge/AeroLung-Health--Tech-4a8fe3?style=for-the-badge" alt="AeroLung Badge" />
  <img src="https://img.shields.io/badge/Status-Hackathon_Ready-success?style=for-the-badge" alt="Hackathon Ready" />
  <h1>🌬️ AeroLung</h1>
  <p><strong>Real-Time Air Quality Monitoring & Respiratory Impact Prediction System</strong></p>
</div>

---

## 📖 Project Overview

**AeroLung** is an AI-powered health-tech platform designed to bridge the gap between environmental pollution data and individual health monitoring. By integrating real-time air quality metrics, wearable health signals, and advanced machine learning models, AeroLung estimates personalized lung impact and predicts respiratory disease risks.

This repository contains the **Backend API Engine** and the **Analytics Dashboard** for the AeroLung platform.

---

## 🎯 The Problem

Despite the availability of public Air Quality Index (AQI) data, individuals and public health officials lack actionable insights because they are missing:
- **Personalized Exposure Tracking:** AQI doesn't equal personal impact.
- **Real-Time Lung Stress Estimation:** Understanding the immediate physical toll.
- **AI-Driven Disease Risk Prediction:** Forecasting exacerbations for asthma and COPD.

## 💡 Our Solution

AeroLung solves these challenges through three core components:

1. **Air Quality Monitoring Module:** Live tracking of PM2.5, PM10, NO₂, SO₂, CO, and O₃.
2. **Wearable Health Integration:** Correlates environmental data with Heart Rate, SpO₂, and Respiratory Rate.
3. **AI Lung Impact Model (PLSI Engine):** A proprietary algorithmic engine that scores personal exposure, predicts time-series lung stress, and classifies respiratory risk.

---

## ⚙️ Key Features

- 🏥 **Personal Lung Health Dashboard:** Live AQI display, Risk Percentage Scores, and Health Trend Graphs.
- 🕒 **Pollution Exposure Timeline:** Cumulative exposure scoring and high-risk period detection.
- 🚨 **Risk Alerts & Preventive Suggestions:** Smart outdoor activity warnings and mask recommendations.
- 📊 **Public Health Analytics Panel:** City-wise AQI analysis, Risk Heatmaps, and policy-support analytics.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### 1. Running the Backend (PLSI Engine)

The backend is a FastAPI application that serves the ML models, calculations, and data aggregations.

```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI Server (runs on port 8000 by default)
python main.py
```

### 2. Running the Analytics Dashboard

The dashboard is built with React, Vite, and Tailwind CSS.

```bash
cd aerolung-dashboard

# Install dependencies
npm install

# Start the development server
npm run dev
```

---

## 🧠 Machine Learning Architecture

The AI engine utilizes several models located in the `ML_model/` directory:
- **Environment Model (`env_model.joblib`)**: Forecasts PM2.5 based on chemical lag drivers.
- **Physiology Model (`phys_model.joblib`)**: Predicts breathing rates under varied environmental stress.
- **Risk Integration Model (`risk_model.joblib`)**: Unified classification algorithm mapping exposure to exact risk severity (Low, Moderate, High, Critical).

---

## 🏆 Hackathon Judges Note

We have streamlined this repository specifically for evaluation during this hackathon. The architecture has been verified for code quality, the APIs are secured via localized environment variable loading, and the Dashboard is rigorously integrated with our real-time Python model engine. 

*(AeroLung Mobile Application source code is maintained in a separate repository for deployment modularity).*

---

<div align="center">
  <i>Built with ❤️ by Team Syntax_Glitch</i>
</div>

