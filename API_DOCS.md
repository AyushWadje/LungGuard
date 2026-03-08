# AeroLung Backend API Documentation 🫁

## Base URL
```
http://localhost:8000
```

---

## Authentication

### POST `/api/auth/login`
Login with email and password.

**Request Body:**
```json
{
  "email": "test@example.com",
  "password": "1234"
}
```

**Success Response (200):**
```json
{
  "token": "demo_secure_token_99x",
  "message": "Login successful"
}
```

**Error Response (401):**
```json
{
  "detail": "Invalid credentials"
}
```

### POST `/api/auth/logout`
Logout the current user.

**Response:**
```json
{ "message": "Logged out" }
```

### POST `/api/auth/password/change`
Change user password.

**Request Body:**
```json
{
  "old_password": "1234",
  "new_password": "newpass"
}
```

---

## Health Check

### GET `/`
Check if the API is running.

**Response:**
```json
{ "message": "✅ AeroLung API Running!" }
```

---

## Risk Prediction

### GET `/predict`
Predict respiratory risk level based on patient metrics.

**Query Parameters:**

| Name       | Type    | Example | Description                |
|------------|---------|---------|----------------------------|
| aqi        | int     | 250     | Air Quality Index value    |
| spo2       | float   | 94.0    | Blood oxygen saturation    |
| age        | int     | 45      | Patient age                |
| smoker     | bool    | true    | Is the patient a smoker?   |
| asthma     | bool    | true    | Does patient have asthma?  |
| heart_rate | int     | 88      | Heart rate in BPM          |

**Example URL:**
```
/predict?aqi=250&spo2=94&age=45&smoker=true&asthma=true&heart_rate=88
```

**Response:**
```json
{
  "risk_level": "CRITICAL",
  "detailed_analysis": {
    "plsi_score": 72.5,
    "interpretation": "High",
    "alerts": { ... },
    "forecasts": { ... },
    "breakdown": { ... }
  }
}
```

**Risk Levels:** `LOW`, `MODERATE`, `HIGH`, `CRITICAL`

---

## Cities AQI

### GET `/cities-aqi`
Fetch real-time AQI data for major Indian cities (cached for 5 minutes).

**Response:**
```json
[
  { "city": "Mumbai", "aqi": 71 },
  { "city": "Delhi", "aqi": 107 },
  { "city": "Pune", "aqi": 232 },
  { "city": "Bangalore", "aqi": 68 },
  { "city": "Chennai", "aqi": 30 },
  { "city": "Kolkata", "aqi": 165 }
]
```

---

## Dashboard

### GET `/api/dashboard/stats`
Fetch dashboard summary statistics.

**Response:**
```json
{
  "total_users": 15420,
  "users_trend": "+12% this week",
  "avg_aqi": 128,
  "aqi_status": "Moderate",
  "active_alerts": 3,
  "hospital_admissions": 412,
  "admissions_trend": "trending_down"
}
```

### GET `/api/dashboard/health-trends`
Fetch weekly health vs pollution trends.

**Response:**
```json
[
  { "name": "Week 1", "health": 85, "pollution": 40 },
  { "name": "Week 2", "health": 82, "pollution": 55 }
]
```

### GET `/api/dashboard/pollutants`
Fetch current pollutant levels (live from OpenWeatherMap).

**Response:**
```json
[
  { "name": "PM2.5", "value": 45.2, "unit": "µg/m³", "fill": "#3b82f6" },
  { "name": "PM10", "value": 25.1, "unit": "µg/m³", "fill": "#22c55e" },
  { "name": "O3", "value": 15.3, "unit": "µg/m³", "fill": "#a855f7" },
  { "name": "NO2", "value": 15.0, "unit": "µg/m³", "fill": "#f59e0b" }
]
```

---

## Population Health

### GET `/api/health/demographics`
Fetch health demographics by region.

**Query Parameters:**
| Name      | Type   | Description              |
|-----------|--------|--------------------------|
| condition | string | Filter by condition type |

### GET `/api/health/correlation`
Fetch AQI vs health score correlation data.

---

## Map & Sensors

### GET `/api/map/sensors/live`
Fetch live sensor data (from OpenAQ).

**Response:**
```json
[
  { "id": "openaq-2178", "lat": 35.13, "lng": -106.58, "aqi": 36, "pm25": 12 }
]
```

### GET `/api/map/zones`
Fetch risk zones for map overlay.

---

## Alerts

### GET `/api/alerts/active`
Fetch all active alerts.

### POST `/api/alerts/{alert_id}/acknowledge`
Acknowledge a specific alert.

### POST `/api/alerts/{alert_id}/advisory`
Issue a public advisory for a specific alert.

---

## Analytics

### GET `/api/analytics/historical`
Fetch historical pollution and health analytics.

**Query Parameters:**
| Name  | Type   | Default | Description        |
|-------|--------|---------|--------------------|
| range | string | "12m"   | Time range filter  |

### GET `/api/analytics/yoy`
Fetch year-over-year AQI vs hospital admissions correlation.

### GET `/api/analytics/export`
Export analytics report metadata.

**Query Parameters:**
| Name   | Type   | Default | Description     |
|--------|--------|---------|-----------------|
| format | string | "pdf"   | Export format   |

---

## User Profile & Workspace

### GET `/api/users/profile`
Fetch current user profile.

### PUT `/api/users/profile`
Update user profile.

### GET `/api/workspaces/current`
Fetch current workspace settings.

### PUT `/api/workspaces/current`
Update workspace settings.

### PUT `/api/users/notifications`
Update notification preferences.

---

## Team Management

### GET `/api/team/members`
Fetch all team members.

### POST `/api/team/invite`
Invite a new team member.

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "role": "Viewer"
}
```

---

## React Frontend Integration

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Fetch Cities AQI
const getCitiesAQI = async () => {
  const res = await fetch(`${API_BASE_URL}/cities-aqi`);
  return await res.json();
};

// Predict Risk
const predictRisk = async (params: Record<string, string>) => {
  const query = new URLSearchParams(params);
  const res = await fetch(`${API_BASE_URL}/predict?${query}`);
  return await res.json();
};
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
OWM_API_KEY=your_openweathermap_key
OPENAQ_API_KEY=your_openaq_key
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

<div align="center">
  <i>Built with ❤️ by Team Syntax_Glitch</i>
</div>
