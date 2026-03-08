<div align="center">
  <img src="https://img.shields.io/badge/LungGuard-Health--Intelligence-4a8fe3?style=for-the-badge" alt="LungGuard Badge" />
  <img src="https://img.shields.io/badge/AI_Powered-Machine_Learning-success?style=for-the-badge" alt="AI Powered" />
  <img src="https://img.shields.io/badge/Status-Production_Ready-green?style=for-the-badge" alt="Production Ready" />
  
  <h1>🫁 LungGuard (AeroLung)</h1>
  <p><strong>AI-Powered Air Quality Monitoring & Respiratory Health Intelligence Platform</strong></p>
  
  <p>
    <a href="#-features">Features</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-architecture">Architecture</a> •
    <a href="#-api-documentation">API Docs</a> •
    <a href="#-tech-stack">Tech Stack</a>
  </p>
</div>

---

## 📖 Project Overview

**LungGuard (AeroLung)** is an enterprise-grade AI-powered health-tech platform that bridges environmental pollution data with individual health monitoring. By integrating real-time air quality metrics, wearable health signals, and advanced machine learning models, LungGuard provides:

- **Personalized Lung Health Scoring** (PLSI Engine)
- **Real-Time Respiratory Risk Prediction** 
- **Population Health Analytics**
- **Environmental Exposure Tracking**

This repository contains the complete **Full-Stack Application** including:
- 🔧 **FastAPI Backend** with JWT Authentication
- 🤖 **Machine Learning Pipeline** (3 trained RandomForest models)
- 🎨 **React Dashboard** with real-time data visualization
- 📊 **PLSI Engine** for health impact calculations

---

## 🎯 The Problem

Despite the availability of public Air Quality Index (AQI) data, individuals and healthcare providers lack actionable insights:

- ❌ **No Personalized Exposure Tracking** - AQI doesn't reflect individual impact
- ❌ **Missing Real-Time Health Correlation** - No connection between air quality and physiological data
- ❌ **Limited Predictive Capabilities** - Reactive rather than proactive health management
- ❌ **Fragmented Data Sources** - Environmental and health data exist in silos

## 💡 Our Solution

LungGuard solves these challenges through an integrated AI-powered platform:

### Core Components

1. **🌡️ Real-Time Air Quality Monitoring**
   - Live tracking of PM2.5, PM10, NO₂, O₃, SO₂, and CO
   - WHO standard compliance with proper µg/m³ units
   - Multi-city coverage with interactive maps

2. **❤️ Health Metrics Integration**
   - SpO₂ (Blood Oxygen Saturation)
   - Heart Rate & Respiratory Rate
   - Physiological stress indicators

3. **🤖 AI-Powered PLSI Engine**
   - Proprietary **Personal Lung Stress Index** calculation
   - 3 trained RandomForest ML models (42.3 MB total)
   - Real-time risk classification: LOW → MODERATE → HIGH → CRITICAL

4. **📊 Population Health Analytics**
   - Community health trends
   - Geographic risk heatmaps
   - Policy support data visualization

---

## ✨ Features

### User Features
- 🏥 **Personal Health Dashboard** - Real-time lung health scoring (0-100 PLSI)
- 📈 **Health Trend Analytics** - Historical data with predictive insights
- 🚨 **Smart Alerts** - Proactive warnings for high-risk exposure periods
- 🗺️ **Air Quality Map** - Interactive city-wise pollution visualization
- 💊 **Health Recommendations** - Personalized preventive suggestions

### Technical Features
- 🔐 **JWT Authentication** - OAuth2-compliant secure authentication
- 🔄 **Real-Time Updates** - Live data synchronization
- 📱 **Responsive Design** - Mobile-first UI with Tailwind CSS
- 🛡️ **Protected Routes** - Role-based access control
- ⚡ **Fast API** - High-performance async endpoints

---

## 🚀 Quick Start

### Prerequisites

```bash
# Required Software
- Python 3.9+ (tested on 3.14)
- Node.js 18+ 
- npm or yarn
- Git
```

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/AyushWadje/LungGuard.git
cd LungGuard
```

### 2️⃣ Backend Setup (FastAPI)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variables (optional)
# export PORT=5000
# export SECRET_KEY=your-secret-key

# Start the backend server (runs on port 5000)
python main.py
```

**Backend will be running at:** `http://localhost:5000`

### 3️⃣ Frontend Setup (React Dashboard)

```bash
# Navigate to dashboard directory
cd aerolung-dashboard

# Install Node dependencies
npm install

# Start the development server
npm run dev
```

**Frontend will be running at:** `http://localhost:5173`

### 4️⃣ Access the Application

1. Open your browser to `http://localhost:5173`
2. Login with demo credentials:
   - **Email:** `test@example.com`
   - **Password:** `1234`
3. Explore the dashboard and analytics!

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LungGuard Platform                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐ │
│  │   React UI   │ ───► │  FastAPI     │ ───► │  ML      │ │
│  │  (Port 5173) │ ◄─── │  Backend     │ ◄─── │  Models  │ │
│  │   Tailwind   │      │  (Port 5000) │      │  (42MB)  │ │
│  └──────────────┘      └──────────────┘      └──────────┘ │
│         │                       │                    │      │
│         │                       │                    │      │
│    ┌────▼────┐            ┌────▼────┐         ┌────▼────┐ │
│    │  Auth   │            │  PLSI   │         │  Risk   │ │
│    │ Context │            │ Engine  │         │  Pred.  │ │
│    └─────────┘            └─────────┘         └─────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

#### Backend
- **Framework:** FastAPI 0.133.0
- **Authentication:** JWT (python-jose, bcrypt, passlib)
- **ML Libraries:** scikit-learn 1.8.0, pandas, numpy
- **Data Processing:** joblib, pandas
- **API Standards:** OAuth2, REST

#### Frontend
- **Framework:** React 19.2.0
- **Build Tool:** Vite 7.3.1
- **Language:** TypeScript
- **Styling:** Tailwind CSS 3.5.0
- **Charts:** Recharts 3.7.0
- **Routing:** React Router 7.13.1

#### Machine Learning
- **Models:** 3x RandomForest Regressors
  - `env_model.joblib` (14.3 MB) - Environmental predictions
  - `phys_model.joblib` (13.8 MB) - Physiological predictions
  - `risk_model.joblib` (14.2 MB) - Risk classification
- **Training Data:** 10,000+ samples from synthetic EPA/NHANES data
- **Performance:** MAE < 2.0, R² > 0.75

---

## 🧠 Machine Learning Pipeline

### PLSI (Personal Lung Stress Index) Engine

The core innovation of LungGuard is the PLSI calculation:

```python
PLSI = weighted_sum(
    environmental_score,  # PM2.5, O3, NO2 exposure
    physiological_score,  # SpO2, HR, Breathing Rate
    risk_integration      # ML-predicted future risk
)
```

### Model Architecture

1. **Environmental Model** (`env_model.joblib`)
   - **Input Features:** PM2.5 lag (1,2,3), Ozone, NO2
   - **Output:** Predicted PM2.5 exposure
   - **Accuracy:** R² = 0.75, MAE = 23.86

2. **Physiological Model** (`phys_model.joblib`)
   - **Input Features:** Breathing rate lag (1,2), Heart rate, SpO2
   - **Output:** Predicted respiratory stress
   - **Accuracy:** MAE = 1.98

3. **Risk Integration Model** (`risk_model.joblib`)
   - **Input Features:** PM2.5, Breathing rate, Heart rate, Ozone
   - **Output:** Risk classification (0-100 scale)
   - **Accuracy:** MAE = 0.0026

### Training Pipeline

```bash
# Located in ML_model/ directory
python train_models.py          # Train all 3 models
python evaluate_classification.py  # Validate performance
python sync_data.py             # Update training data
```

---

## 📡 API Documentation

### Authentication Endpoints

#### POST `/api/auth/login`
Login with email and password (OAuth2 compliant)

**Request:**
```json
{
  "email": "test@example.com",
  "password": "1234"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "email": "test@example.com",
    "role": "admin",
    "name": "Demo User"
  }
}
```

#### POST `/api/auth/logout`
Invalidate current JWT token

---

### Health Prediction Endpoints

#### POST `/predict`
Get personalized health risk prediction

**Request:**
```json
{
  "aqi": 150,
  "spo2": 95.0,
  "age": 45,
  "smoker": false,
  "asthma": true,
  "heart_rate": 75,
  "pm25": 55.0,
  "pm10": 80.0,
  "o3": 40.0,
  "no2": 25.0
}
```

**Response:**
```json
{
  "risk_level": "MODERATE",
  "plsi_score": 67.8,
  "detailed_analysis": {
    "environmental_impact": 0.72,
    "physiological_stress": 0.65,
    "risk_factors": ["asthma", "high_pm25"],
    "recommendations": ["Limit outdoor activities", "Use air purifier"]
  }
}
```

---

### Dashboard Endpoints

#### GET `/api/dashboard/stats`
Get real-time dashboard statistics (public endpoint)

**Response:**
```json
{
  "total_users": 1234,
  "users_trend": "+12%",
  "avg_aqi": 87,
  "aqi_status": "Moderate",
  "high_risk_population": 234,
  "risk_trend": "+5%",
  "alerts_today": 12,
  "recommendations_sent": 567
}
```

#### GET `/api/dashboard/pollutants`
Get current pollutant levels with WHO compliance (public endpoint)

**Response:**
```json
[
  {
    "name": "PM2.5",
    "value": 35.2,
    "unit": "µg/m³",
    "percentage": 234.7,
    "trend": "+12%",
    "status": "Unhealthy",
    "who_limit": 15.0
  }
]
```

---

### Protected Endpoints

These endpoints require JWT authentication via `Authorization: Bearer {token}` header:

- `GET /api/users/profile` - Get current user profile
- `POST /api/team/invite` - Invite team members
- `GET /api/workspaces/list` - List user workspaces
- `POST /api/alerts/{id}/acknowledge` - Acknowledge alerts

---

## 📁 Project Structure

```
LungGuard/
├── main.py                      # FastAPI backend entry point
├── plsi_engine.py              # PLSI calculation engine
├── requirements.txt            # Python dependencies
├── requirements_ml.txt         # ML-specific dependencies
│
├── ML_model/                   # Trained ML models
│   ├── env_model.joblib       # Environmental model (14.3 MB)
│   ├── phys_model.joblib      # Physiological model (13.8 MB)
│   ├── risk_model.joblib      # Risk integration model (14.2 MB)
│   ├── train_models.py        # Training pipeline
│   └── *.csv                  # Training data
│
├── aerolung/                   # ML pipeline package
│   └── ml/
│       ├── models/            # Model classes
│       ├── training/          # Training scripts
│       └── data/              # Data preprocessors
│
├── aerolung-dashboard/        # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API services
│   │   └── context/          # Auth context
│   ├── package.json
│   └── vite.config.ts
│
├── Pipeline/                  # Data pipeline components
│   ├── timeline_manager.py
│   └── models.py
│
└── API_DOCS.md               # Full API documentation
```

---

## 🚢 Deployment

### Backend Deployment

#### Environment Variables

```bash
# .env file
PORT=5000
HOST=0.0.0.0
SECRET_KEY=your-super-secret-jwt-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Optional API Keys
OWM_API_KEY=your-openweathermap-key
OPENAQ_API_KEY=your-openaq-key
```

#### Docker Deployment (Optional)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "main.py"]
```

### Frontend Deployment

#### Build for Production

```bash
cd aerolung-dashboard
npm run build
# Output in dist/ folder ready for deployment
```

#### Deploy to Vercel/Netlify

```bash
# Update environment variables
VITE_API_URL=https://your-backend-api.com
```

---

## 🧪 Testing

### Backend Tests

```bash
# Run API tests
python -c "
import requests
BASE = 'http://localhost:5000'

# Test public endpoints
r = requests.get(f'{BASE}/api/dashboard/stats')
assert r.status_code == 200

# Test prediction
r = requests.post(f'{BASE}/predict', json={
    'aqi': 100, 'spo2': 95.0, 'age': 45
})
assert 'risk_level' in r.json()
print('✅ All tests passed!')
"
```

### ML Model Validation

```bash
cd ML_model
python evaluate_classification.py
# Shows MAE, R², and model metrics
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/AmazingFeature`
3. **Commit your changes:** `git commit -m 'Add some AmazingFeature'`
4. **Push to the branch:** `git push origin feature/AmazingFeature`
5. **Open a Pull Request**

### Code Style

- **Python:** Follow PEP 8 guidelines
- **JavaScript/TypeScript:** Use ESLint configuration
- **Commits:** Use conventional commit messages

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

**Team Syntax_Glitch**

- Project Lead & ML Engineer
- Full-Stack Developer
- UI/UX Designer
- Data Scientist

---

## 🙏 Acknowledgments

- WHO Air Quality Guidelines
- OpenAQ for air quality data
- EPA for environmental datasets
- scikit-learn community
- React and FastAPI teams

---

## 📞 Support

For issues, questions, or contributions:

- 📧 Email: support@lungguard.health
- 🐛 Issues: [GitHub Issues](https://github.com/AyushWadje/LungGuard/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/AyushWadje/LungGuard/discussions)

---

<div align="center">
  <h3>🫁 Stay Healthy, Stay Informed with LungGuard</h3>
  <p><i>Built with ❤️ using AI, Machine Learning, and Modern Web Technologies</i></p>
  
  <p>
    <a href="https://github.com/AyushWadje/LungGuard">⭐ Star us on GitHub</a>
  </p>
</div>

---

## 📊 Project Status

- ✅ **Backend API:** Production Ready
- ✅ **ML Models:** Trained & Validated
- ✅ **Frontend Dashboard:** Fully Functional
- ✅ **Authentication:** JWT Secured
- ✅ **Testing:** All Tests Passing
- 🚧 **Mobile App:** Coming Soon
- 🚧 **IoT Integration:** Planned

**Last Updated:** March 9, 2026

