"""
Simple Backend API Test Script
Tests the FastAPI server without video processing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Any
import uvicorn

# Pydantic models
class SignalControl(BaseModel):
    direction: str
    state: str

class PriorityRequest(BaseModel):
    lane: str
    duration: Optional[int] = None

class SystemStatus(BaseModel):
    status: str
    uptime: float
    detections_count: int
    priority_mode: bool
    timestamp: str

class ConfigUpdate(BaseModel):
    key: str
    value: Any

# Create FastAPI app
app = FastAPI(
    title="Lifeline API Test",
    description="Test Backend API for Traffic Management System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test data
test_signals = {
    "north": {"state": "red", "timer": 0},
    "south": {"state": "red", "timer": 0},
    "east": {"state": "green", "timer": 30},
    "west": {"state": "red", "timer": 0},
}

test_stats = {
    "detections_today": 0,
    "priority_activations": 0,
    "avg_response_time": 0,
    "system_uptime": 0
}

# Mount static files
try:
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
except Exception as e:
    print(f"Warning: Could not mount frontend: {e}")

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Lifeline API Test Server Running", "status": "ok"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "lifeline-backend-test"}

@app.get("/api/status")
async def get_status():
    from datetime import datetime
    return SystemStatus(
        status="running",
        uptime=123.45,
        detections_count=0,
        priority_mode=False,
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/signals")
async def get_signals():
    return test_signals

@app.post("/api/signals/control")
async def control_signal(control: SignalControl):
    if control.direction not in test_signals:
        return {"success": False, "error": "Invalid direction"}
    
    test_signals[control.direction]["state"] = control.state
    return {"success": True, "message": f"Signal {control.direction} set to {control.state}"}

@app.get("/api/statistics")
async def get_statistics():
    return test_stats

@app.post("/api/priority/activate")
async def activate_priority(request: PriorityRequest):
    print(f"Priority activated for lane: {request.lane}")
    return {
        "success": True,
        "message": f"Priority activated for {request.lane}",
        "duration": request.duration or 60
    }

@app.post("/api/priority/deactivate")
async def deactivate_priority():
    print("Priority mode deactivated")
    return {"success": True, "message": "Priority mode deactivated"}

@app.get("/api/config")
async def get_config():
    return {
        "camera": {"source": 0, "fps": 30, "width": 1280, "height": 720},
        "detection": {"confidence_threshold": 0.6, "device": "cpu"},
        "traffic_control": {"default_green_duration": 45}
    }

@app.post("/api/config/update")
async def update_config(update: ConfigUpdate):
    print(f"Config update: {update.key} = {update.value}")
    return {"success": True, "message": f"Configuration updated: {update.key}"}

@app.get("/api/detections")
async def get_recent_detections():
    return {
        "recent_detections": [],
        "total_count": 0
    }

@app.post("/api/system/restart")
async def restart_system():
    return {"success": True, "message": "System restart initiated (test mode)"}

@app.post("/api/system/shutdown")
async def shutdown_system():
    return {"success": True, "message": "System shutdown initiated (test mode)"}

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Lifeline Backend API Test Server...")
    print("=" * 60)
    print("📡 API will be available at: http://localhost:8000")
    print("📊 API Docs: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/api/health")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
