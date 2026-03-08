import os
import re
import time
import numpy as np
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
import bcrypt as _bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel
import requests as http_client
import uvicorn

from plsi_engine import PLSICalculator, AeroLungMLOrchestrator

# ================================
# Load Environment Variables
# ================================
load_dotenv()

OWM_API_KEY = os.getenv("OWM_API_KEY", "")
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY", "")
PORT = int(os.getenv("PORT", 5000))
HOST = os.getenv("HOST", "0.0.0.0")
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")

# FIX 1.1 — JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "changeme_please_use_a_real_256bit_secret_in_production")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))
ALGORITHM = "HS256"

# WHO 24-hour guideline limits µg/m³  (FIX 2.1)
WHO_LIMITS = {"pm25": 15.0, "pm10": 45.0, "o3": 100.0, "no2": 25.0}

# ================================
# Create App
# ================================
app = FastAPI(
    title="AeroLung API",
    description="Real-Time Air Quality Monitoring & Respiratory Impact Prediction API",
    version="2.0.0",
)

# FIX 1.2 — Tightened CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


# ================================
# Global Exception Handler
# ================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# ================================
# Initialize AI Engines
# ================================
print("Loading ML Models...")
calculator   = PLSICalculator()
orchestrator = AeroLungMLOrchestrator()
print("ML Models loaded successfully!")

# ================================
# AQI Cache (reduces latency)
# ================================
cache = {"data": None, "timestamp": 0}

# ================================
# Thread-safe acknowledged alerts  (FIX 2.7)
# ================================
acknowledged_alert_ids: set = set()
alerts_lock = Lock()

# FIX 1.1 — Token blacklist for logout invalidation
blacklisted_tokens: set = set()

# ================================
# Auth Utilities  (FIX 1.1)
# ================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Demo password hash for "1234" — generated once at startup
DEMO_PASSWORD_HASH: bytes = _bcrypt.hashpw(b"1234", _bcrypt.gensalt())


def _verify_password(plain: str, hashed: bytes) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed)


def create_access_token(data: dict) -> str:
    """Create a signed JWT with an expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Decode and validate a JWT; raise HTTP 401 on any failure."""
    if token in blacklisted_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("sub") is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token invalid or expired: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency — extracts and verifies the bearer token."""
    return verify_token(token)


# ================================
# Pydantic Models
# ================================

class LoginRequest(BaseModel):
    email: str
    password: str


class UserProfileData(BaseModel):
    name: str = "Dr. Jane Doe"
    role: str = "Pulmonologist"
    email: str = "jane.doe@example.com"
    avatar: str = ""
    avatar_url: str = "https://i.pravatar.cc/150?img=5"


class WorkspaceSettings(BaseModel):
    name: str = "Central Hospital Region 1"
    timezone: str = "America/New_York"
    primary_region: str = "New York City"


class InviteRequest(BaseModel):
    email: str
    role: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class PredictRequest(BaseModel):
    aqi: int
    spo2: float
    age: int
    smoker: bool = False
    asthma: bool = False
    heart_rate: int = 75
    # FIX 2.3 — optional individual pollutant overrides
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    o3: Optional[float] = None
    no2: Optional[float] = None


# ================================
# In-memory state stores (demo)
# ================================
profile_db = UserProfileData()
workspace_db = WorkspaceSettings()

ALL_ALERTS = [
    {
        "id": "a1",
        "severity": "CRITICAL",
        "title": "Industrial Smog Alert",
        "location": "Sector 7 — Industrial Zone",
        "population": 45000,
        "color": "red",
        "status": "active",
    },
    {
        "id": "a2",
        "severity": "HIGH",
        "title": "Ozone Levels Peaking",
        "location": "Downtown Core",
        "population": 120000,
        "color": "orange",
        "status": "active",
    },
    {
        "id": "a3",
        "severity": "HIGH",
        "title": "PM2.5 Spike Detected",
        "location": "Harbor District",
        "population": 32000,
        "color": "orange",
        "status": "active",
    },
]

team_members = [
    {"id": "t1", "name": "Dr. Smith", "email": "smith@example.com", "role": "Admin"},
    {"id": "t2", "name": "Nurse Joy", "email": "joy@example.com", "role": "Viewer"},
    {"id": "t3", "name": "Dr. Patel", "email": "patel@example.com", "role": "Analyst"},
]


# ================================
# Helper Functions
# ================================

def make_json_compatible(obj):
    """Convert numpy types to standard Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: make_json_compatible(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_compatible(v) for v in obj]
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    return obj


def get_cached_avg_aqi() -> int:
    """Return average AQI from cache if < 300 s old, else 128.  (FIX 2.2)"""
    age = time.time() - cache["timestamp"]
    if cache["data"] and age < 300:
        aqis = [c.get("aqi", 0) for c in cache["data"] if isinstance(c, dict)]
        if aqis:
            return round(sum(aqis) / len(aqis))
    return 128


def get_aqi_status_label(aqi: int) -> str:
    """Return a human-readable WHO/EPA AQI category label.  (FIX 2.2)"""
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"


def pm25_to_aqi(pm25: float) -> int:
    """Convert PM2.5 µg/m³ to standard EPA AQI integer.  (FIX 2.4)"""
    if pm25 <= 12.0:
        return int((50 / 12.0) * pm25)
    elif pm25 <= 35.4:
        return int(50 + ((100 - 50) / (35.4 - 12.1)) * (pm25 - 12.1))
    elif pm25 <= 55.4:
        return int(100 + ((150 - 100) / (55.4 - 35.5)) * (pm25 - 35.5))
    elif pm25 <= 150.4:
        return int(150 + ((200 - 150) / (150.4 - 55.5)) * (pm25 - 55.5))
    elif pm25 <= 250.4:
        return int(200 + ((300 - 200) / (250.4 - 150.5)) * (pm25 - 150.5))
    else:
        return min(500, int(300 + (pm25 - 250.5) * 0.99))


# ================================
# API Routes
# ================================

@app.get("/")
def home():
    return {"message": "AeroLung API Running!", "version": "2.0.0"}


# ================================
# Predict  (FIX 2.3)
# ================================

@app.post("/predict")
def predict(data: PredictRequest):
    """Predict respiratory risk using the PLSI ML engine."""
    pm25 = max(0.0, data.pm25 if data.pm25 is not None else float(data.aqi))
    pm10 = max(0.0, data.pm10 if data.pm10 is not None else data.aqi * 1.5)
    o3   = max(0.0, data.o3   if data.o3   is not None else data.aqi * 0.4)
    no2  = max(0.0, data.no2  if data.no2  is not None else data.aqi * 0.3)

    pollutants = {"pm25": pm25, "pm10": pm10, "o3": o3, "no2": no2}

    physiology = {
        "heart_rate": data.heart_rate,
        "spo2": data.spo2,
        "breathing_rate_lpm": 16,
        "systolic_bp": 120,
        "diastolic_bp": 80,
    }

    profile = {
        "age": data.age,
        "pre_existing_conditions": ["asthma"] if data.asthma else [],
        "smoking_history": "active" if data.smoker else "none",
    }

    try:
        result = calculator.calculate(pollutants, physiology["breathing_rate_lpm"], profile, physiology)
        safe_result = make_json_compatible(result)

        interpretation = safe_result.get("interpretation", "Low")
        mapping = {
            "Low": "LOW",
            "Mild": "LOW",
            "Medium": "MODERATE",
            "High": "HIGH",
            "Extreme": "CRITICAL",
        }
        final_risk = mapping.get(interpretation, "MODERATE")

        # ML pipeline augmentation — non-blocking
        ml_insights: dict = {}
        try:
            recent_pm25 = [pm25]  # extend from cache/history if available
            ml_profile  = {"age": data.age, "conditions": profile["pre_existing_conditions"],
                           "name": "Patient"}
            ml_insights = orchestrator.predict(
                pollutants=pollutants,
                physiology=physiology,
                profile=ml_profile,
                recent_pm25_history=recent_pm25,
            )
            ml_insights = make_json_compatible(ml_insights)
        except Exception as ml_exc:
            print(f"ML orchestrator warning (non-fatal): {ml_exc}")

        return {
            "risk_level":      final_risk,
            "detailed_analysis": safe_result,
            "ml_insights":     ml_insights,
        }
    except Exception as e:
        print(f"Error in predict: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict")
def predict_get(
    aqi: int = 100,
    spo2: float = 98.0,
    age: int = 30,
    smoker: bool = False,
    asthma: bool = False,
    heart_rate: int = 75,
    pm25: Optional[float] = None,
    pm10: Optional[float] = None,
    o3: Optional[float] = None,
    no2: Optional[float] = None,
):
    """GET version of predict for backward compatibility."""
    return predict(
        PredictRequest(
            aqi=aqi, spo2=spo2, age=age, smoker=smoker, asthma=asthma,
            heart_rate=heart_rate, pm25=pm25, pm10=pm10, o3=o3, no2=no2,
        )
    )


# ================================
# Auth Routes  (FIX 1.1)
# ================================

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Authenticate user and return a signed JWT token."""
    if request.email == "test@example.com" and _verify_password(request.password, DEMO_PASSWORD_HASH):
        token = create_access_token({"sub": request.email, "role": "doctor"})
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "email": request.email,
                "role": "doctor",
                "name": "Dr. Demo User"
            }
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/api/auth/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Invalidate the current JWT by adding it to the blacklist."""
    blacklisted_tokens.add(token)
    return {"message": "Logged out"}


@app.post("/api/auth/password/change")
async def change_password(
    req_body: ChangePasswordRequest,
    _: dict = Depends(get_current_user),
):
    if not req_body.old_password or not req_body.new_password:
        raise HTTPException(status_code=400, detail="Both old and new passwords are required")
    if len(req_body.new_password) < 4:
        raise HTTPException(status_code=400, detail="New password must be at least 4 characters")
    return {"message": "Password changed successfully"}


# ================================
# Dashboard Data
# ================================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    avg = get_cached_avg_aqi()
    with alerts_lock:
        active_count = len([a for a in ALL_ALERTS if a["id"] not in acknowledged_alert_ids])
    return {
        "total_users": 15420,
        "users_trend": "+12% this week",
        "avg_aqi": avg,
        "aqi_status": get_aqi_status_label(avg),
        "active_alerts": active_count,
        "hospital_admissions": 412,
        "admissions_trend": "trending_down",
    }


@app.get("/api/dashboard/health-trends")
async def get_health_trends():
    return [
        {"name": "Week 1", "health": 85, "pollution": 40},
        {"name": "Week 2", "health": 82, "pollution": 55},
        {"name": "Week 3", "health": 88, "pollution": 30},
        {"name": "Week 4", "health": 79, "pollution": 80},
    ]


@app.get("/api/dashboard/pollutants")
async def get_pollutants():
    """Return raw µg/m3 values with a WHO-limit-based percentage field.  (FIX 2.1)"""
    url = (
        f"https://api.openweathermap.org/data/2.5/air_pollution"
        f"?lat=19.0144&lon=72.8479&appid={OWM_API_KEY}"
    )
    try:
        response = http_client.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        comps = data["list"][0]["components"]
        raw_pm25 = max(0.0, comps.get("pm2_5", 45.0))
        raw_pm10 = max(0.0, comps.get("pm10",  25.0))
        raw_o3   = max(0.0, comps.get("o3",    15.0))
        raw_no2  = max(0.0, comps.get("no2",   15.0))
    except Exception as e:
        print(f"Pollutant fetch error: {e}")
        raw_pm25, raw_pm10, raw_o3, raw_no2 = 45.0, 25.0, 15.0, 15.0

    def _pct(value: float, limit: float) -> float:
        return min(round((value / limit) * 100, 1), 999.0)

    return [
        {"name": "PM2.5", "value": round(raw_pm25, 2), "unit": "µg/m³", "percentage": _pct(raw_pm25, WHO_LIMITS["pm25"]), "fill": "#3b82f6"},
        {"name": "PM10",  "value": round(raw_pm10, 2), "unit": "µg/m³", "percentage": _pct(raw_pm10, WHO_LIMITS["pm10"]), "fill": "#22c55e"},
        {"name": "O3",    "value": round(raw_o3,   2), "unit": "µg/m³", "percentage": _pct(raw_o3,   WHO_LIMITS["o3"]),   "fill": "#a855f7"},
        {"name": "NO2",   "value": round(raw_no2,  2), "unit": "µg/m³", "percentage": _pct(raw_no2,  WHO_LIMITS["no2"]),  "fill": "#f59e0b"},
    ]


# ================================
# Population Health  (FIX 2.5)
# ================================

@app.get("/api/health/demographics")
async def get_health_demographics(condition: Optional[str] = None, age: Optional[str] = None):
    base = [
        {"name": "North", "age0_17": 120, "age18_64": 300, "age65_plus": 80},
        {"name": "South", "age0_17": 90,  "age18_64": 250, "age65_plus": 110},
        {"name": "East",  "age0_17": 150, "age18_64": 400, "age65_plus": 90},
        {"name": "West",  "age0_17": 80,  "age18_64": 200, "age65_plus": 150},
    ]
    if condition == "Asthma":
        base = [{"name": d["name"], "age0_17": int(d["age0_17"] * 0.36), "age18_64": int(d["age18_64"] * 0.36), "age65_plus": int(d["age65_plus"] * 0.36)} for d in base]
    elif condition == "COPD":
        base = [{"name": d["name"], "age0_17": int(d["age0_17"] * 0.17), "age18_64": int(d["age18_64"] * 0.17), "age65_plus": int(d["age65_plus"] * 0.17)} for d in base]

    if age == "0-17":
        return [{"name": d["name"], "value": d["age0_17"]} for d in base]
    elif age == "18-64":
        return [{"name": d["name"], "value": d["age18_64"]} for d in base]
    elif age == "65+":
        return [{"name": d["name"], "value": d["age65_plus"]} for d in base]
    return base


@app.get("/api/health/correlation")
async def get_health_correlation():
    return [
        {"name": "Low AQI",  "aqi": 30,  "score": 95},
        {"name": "Med AQI",  "aqi": 80,  "score": 85},
        {"name": "High AQI", "aqi": 150, "score": 60},
        {"name": "Crit AQI", "aqi": 300, "score": 25},
    ]


# ================================
# Alerts  (FIX 2.7 — thread-safe; FIX 1.1 — auth on write)
# ================================

@app.get("/api/alerts/active")
async def get_active_alerts():
    with alerts_lock:
        return [a for a in ALL_ALERTS if a["id"] not in acknowledged_alert_ids]


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, _: dict = Depends(get_current_user)):
    with alerts_lock:
        acknowledged_alert_ids.add(alert_id)
    return {"message": f"Alert {alert_id} acknowledged successfully"}


@app.post("/api/alerts/{alert_id}/advisory")
async def issue_alert_advisory(alert_id: str, _: dict = Depends(get_current_user)):
    alert = next((a for a in ALL_ALERTS if a["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return {"message": f"Public advisory issued for: {alert['title']} in {alert['location']}"}


# ================================
# Analytics
# ================================

@app.get("/api/analytics/historical")
async def get_historical_analytics(range: str = "12m"):
    base = [
        {"month": "Jan", "pm25": 40,  "o3": 20, "no2": 15, "respiratory": 100},
        {"month": "Feb", "pm25": 45,  "o3": 25, "no2": 18, "respiratory": 110},
        {"month": "Mar", "pm25": 60,  "o3": 35, "no2": 25, "respiratory": 150},
        {"month": "Apr", "pm25": 80,  "o3": 50, "no2": 40, "respiratory": 200},
        {"month": "May", "pm25": 55,  "o3": 30, "no2": 20, "respiratory": 130},
        {"month": "Jun", "pm25": 70,  "o3": 45, "no2": 35, "respiratory": 175},
        {"month": "Jul", "pm25": 90,  "o3": 60, "no2": 50, "respiratory": 220},
        {"month": "Aug", "pm25": 85,  "o3": 55, "no2": 45, "respiratory": 210},
        {"month": "Sep", "pm25": 65,  "o3": 40, "no2": 30, "respiratory": 160},
        {"month": "Oct", "pm25": 50,  "o3": 28, "no2": 22, "respiratory": 120},
        {"month": "Nov", "pm25": 42,  "o3": 22, "no2": 16, "respiratory": 105},
        {"month": "Dec", "pm25": 38,  "o3": 18, "no2": 12, "respiratory": 95},
    ]
    if range == "ytd":
        current_month = time.localtime().tm_mon
        return base[:current_month]
    return base


@app.get("/api/analytics/yoy")
async def get_yoy_analytics():
    return [
        {"aqi": 30,  "admissions": 8},
        {"aqi": 50,  "admissions": 15},
        {"aqi": 80,  "admissions": 42},
        {"aqi": 100, "admissions": 78},
        {"aqi": 130, "admissions": 145},
        {"aqi": 150, "admissions": 190},
        {"aqi": 180, "admissions": 280},
        {"aqi": 200, "admissions": 350},
        {"aqi": 250, "admissions": 480},
        {"aqi": 300, "admissions": 620},
    ]


@app.get("/api/analytics/export")
async def export_analytics_report(format: str = "pdf", _: dict = Depends(get_current_user)):
    return {
        "status": "success",
        "format": format,
        "message": "Report generation is handled client-side via html2canvas + jsPDF.",
        "data": {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "report_type": "historical_analytics",
        },
    }


# ================================
# User Profile & Workspace  (FIX 1.1 — auth-protected)
# ================================

@app.get("/api/users/profile")
async def get_profile(_: dict = Depends(get_current_user)):
    return profile_db.model_dump()


@app.put("/api/users/profile")
async def update_profile(profile: UserProfileData, _: dict = Depends(get_current_user)):
    global profile_db
    profile_db = profile
    return {"message": "Profile updated", "data": profile_db.model_dump()}


@app.get("/api/workspaces/current")
async def get_workspace(_: dict = Depends(get_current_user)):
    return workspace_db.model_dump()


@app.put("/api/workspaces/current")
async def update_workspace(workspace: WorkspaceSettings, _: dict = Depends(get_current_user)):
    global workspace_db
    workspace_db = workspace
    return {"message": "Workspace updated", "data": workspace_db.model_dump()}


@app.put("/api/users/notifications")
async def update_notifications(settings: dict, _: dict = Depends(get_current_user)):
    return {"message": "Notifications updated", "data": settings}


# ================================
# Team Management  (FIX 1.1 + FIX 1.3)
# ================================

@app.get("/api/team/members")
async def get_team_members(_: dict = Depends(get_current_user)):
    return team_members


@app.post("/api/team/invite")
async def invite_member(invite: InviteRequest, _: dict = Depends(get_current_user)):
    # FIX 1.3 — validate email format
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, invite.email):
        raise HTTPException(status_code=422, detail="Invalid email format")
    new_member = {
        "id": f"t{len(team_members) + 1}",
        "name": invite.email.split("@")[0].replace(".", " ").title(),
        "email": invite.email,
        "role": invite.role,
    }
    team_members.append(new_member)
    return {"message": f"Invited {invite.email} as {invite.role}", "member": new_member}


# ================================
# Map & Sensors  (FIX 2.4)
# ================================

@app.get("/api/map/sensors/live")
async def get_live_sensors():
    headers = {"X-API-Key": OPENAQ_API_KEY}
    try:
        response = http_client.get(
            "https://api.openaq.org/v3/locations/2178/latest",
            headers=headers,
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()

        pm25_readings = []
        lat, lng = 35.1353, -106.5847

        for res in data.get("results", []):
            coords = res.get("coordinates", {})
            if coords:
                lat = coords.get("latitude", lat)
                lng = coords.get("longitude", lng)
            param_name = res.get("parameter", {}).get("name", "").lower()
            if param_name == "pm25":
                pm25_readings.append(res.get("value", 0))

        pm25_val = (
            round(sum(pm25_readings) / len(pm25_readings), 2) if pm25_readings else 12.0
        )

        return [
            {
                "id": "openaq-2178",
                "lat": lat,
                "lng": lng,
                "aqi": pm25_to_aqi(pm25_val),
                "pm25": pm25_val,
            }
        ]
    except Exception as e:
        print(f"OpenAQ error: {e}")
        return [
            {"id": "s1", "lat": 40.7128, "lng": -74.0060, "aqi": pm25_to_aqi(12.0), "pm25": 12.0},
            {"id": "s2", "lat": 40.7580, "lng": -73.9855, "aqi": pm25_to_aqi(45.0), "pm25": 45.0},
        ]


@app.get("/api/map/zones")
async def get_zones():
    return [
        {
            "id": "z1",
            "name": "Industrial Sector",
            "severity": "HIGH",
            "polygon": [[40.7, -74.0], [40.75, -73.9], [40.6, -73.8]],
        }
    ]


# ================================
# Cities AQI  (FIX 2.6)
# ================================

_OWM_AQI_MAPPING = {
    1: {"aqi": 25,  "label": "Good"},
    2: {"aqi": 75,  "label": "Fair"},
    3: {"aqi": 125, "label": "Moderate"},
    4: {"aqi": 175, "label": "Poor"},
    5: {"aqi": 250, "label": "Very Poor"},
}

CITIES = {
    "mumbai":    (19.0760, 72.8777),
    "delhi":     (28.7041, 77.1025),
    "pune":      (18.5204, 73.8567),
    "bangalore": (12.9716, 77.5946),
    "chennai":   (13.0827, 80.2707),
    "kolkata":   (22.5726, 88.3639),
}


@app.get("/cities-aqi")
async def get_cities_aqi():
    current_time = time.time()
    if cache["data"] and (current_time - cache["timestamp"]) < 300:
        return cache["data"]

    results = []
    for city, coord in CITIES.items():
        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/air_pollution"
                f"?lat={coord[0]}&lon={coord[1]}&appid={OWM_API_KEY}"
            )
            response = http_client.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            raw_aqi = data["list"][0]["main"]["aqi"]
            mapped = _OWM_AQI_MAPPING.get(raw_aqi, {"aqi": 100, "label": "Moderate"})
            results.append({"city": city.capitalize(), "aqi": mapped["aqi"], "label": mapped["label"]})
        except Exception as e:
            print(f"Error fetching city AQI for {city}: {e}")
            results.append({"city": city.capitalize(), "aqi": 80, "label": "Fair"})

    cache["data"] = results
    cache["timestamp"] = current_time
    return cache["data"]


# ================================
# ML Pipeline Health
# ================================
@app.get("/ml/health")
def ml_health():
    """Health check for the AeroLung ML pipeline (orchestrator + all 5 models)."""
    try:
        status = orchestrator.health_check()
        status["plsi_engine"] = calculator.health_check()
        return status
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


# ================================
# Start Server
# ================================
if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
