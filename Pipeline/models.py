from pydantic import BaseModel, Field
from typing import Dict, Optional, List

class EnvironmentalData(BaseModel):
    pm25: float = Field(..., description="PM2.5 concentration in µg/m³")
    pm10: Optional[float] = Field(None, description="PM10 concentration in µg/m³")
    o3: Optional[float] = Field(None, description="Ozone concentration in ppb")
    no2: Optional[float] = Field(None, description="NO2 concentration in ppb")
    so2: Optional[float] = Field(None, description="SO2 concentration in ppb")
    co: Optional[float] = Field(None, description="CO concentration in ppm")

class PhysiologicalData(BaseModel):
    breathing_rate_lpm: float = Field(..., description="Estimated breathing rate in Liters Per Minute", ge=5.0, le=120.0)
    spo2: Optional[float] = Field(None, description="Blood oxygen saturation percentage", ge=70.0, le=100.0)
    heart_rate: Optional[int] = Field(None, description="Heart rate in bpm")

class UserProfile(BaseModel):
    age: int = Field(..., ge=0, le=120)
    is_smoker: bool = False
    has_respiratory_disease: bool = False
    has_cardiovascular_disease: bool = False
    fev1_percent: float = Field(100.0, ge=0.0, le=100.0)

class EstimationRequest(BaseModel):
    environment: EnvironmentalData
    physiology: PhysiologicalData
    profile: UserProfile

class Breakdown(BaseModel):
    environmental_stress: float
    physical_demand: float
    biological_vulnerability: float

class DiseaseRisks(BaseModel):
    asthma_exacerbation: float
    copd_flare_up: float
    general_inflammation: float

class ForecastData(BaseModel):
    environment_pm25: List[float] = Field(..., description="3-hour PM2.5 forecast (Line 1)")
    physiology_breathing: List[float] = Field(..., description="3-hour Breathing Rate forecast (Line 2)")
    integrated_risk: List[float] = Field(..., description="3-hour Integrated Risk forecast (Line 3)")

class EstimationResponse(BaseModel):
    plsi_score: float
    interpretation: str
    alerts: dict
    impact_explanations: List[str]
    disease_risks: DiseaseRisks
    risk_drivers: List[str]
    breakdown: Breakdown
    forecasts: ForecastData

class TimelineEntry(BaseModel):
    timestamp: str
    plsi_score: float
    pm25: float
    interpretation: str

class TimelineResponse(BaseModel):
    history: List[TimelineEntry]
    summary: dict
