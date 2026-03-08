from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from plsi_engine import PLSICalculator
from timeline_manager import ExposureTimelineManager
from models import EstimationRequest, EstimationResponse, TimelineResponse
import uvicorn

app = FastAPI(
    title="Respiratory Health Intelligence API",
    description="Backend service with ML-integrated 3-line trend forecasting.",
    version="2.0.0"
)

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
calculator = PLSICalculator()
timeline = ExposureTimelineManager()

@app.get("/")
async def root():
    return {"message": "LungGuard AI API is active with ML Trends"}

@app.post("/v1/estimate", response_model=EstimationResponse)
async def estimate_lung_impact(request: EstimationRequest):
    try:
        pollutants = request.environment.model_dump(exclude_none=True)
        physiology = request.physiology.model_dump(exclude_none=True)
        breathing_rate = request.physiology.breathing_rate_lpm
        profile = request.profile.model_dump()
        
        # Calculate PLSI + ML Trend Forecasts
        result = calculator.calculate(pollutants, breathing_rate, profile, physiology)
        
        # Log to Database
        timeline.log_exposure(
            plsi_score=result['plsi_score'],
            pollutants=pollutants,
            breathing_rate=breathing_rate,
            interpretation=result['interpretation']
        )
        
        return result
    except Exception as e:
        print(f"❌ API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/timeline", response_model=TimelineResponse)
async def get_exposure_timeline(hours: int = 24):
    try:
        history = timeline.get_timeline(hours)
        summary = timeline.calculate_cumulative_dose(hours)
        return {"history": history, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
