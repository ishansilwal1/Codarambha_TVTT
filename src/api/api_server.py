"""
FastAPI Backend API
Provides REST endpoints for system control and monitoring
"""

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Any
import cv2
import asyncio
import json
from datetime import datetime
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger


# Pydantic models for request/response
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
    title="Lifeline Traffic Management API",
    description="API for Intelligent Traffic Management System",
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

# Global state (will be initialized by main app)
system_manager = None


def set_system_manager(manager):
    """Set the system manager instance"""
    global system_manager
    system_manager = manager


# Mount static files
frontend_path = Path(__file__).parent.parent.parent / "frontend"
app.mount("/css", StaticFiles(directory=str(frontend_path / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(frontend_path / "js")), name="js")


@app.get("/")
async def root():
    """Serve the frontend dashboard"""
    html_path = frontend_path / "index.html"
    return FileResponse(html_path)


@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "Lifeline Traffic Management System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/status")
async def get_status():
    """Get system status"""
    if system_manager is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return system_manager.get_status()


@app.get("/api/signals")
async def get_signals():
    """Get all traffic signal states"""
    if system_manager is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return system_manager.signal_controller.get_all_states()


@app.post("/api/signals/control")
async def control_signal(control: SignalControl):
    """Manually control a traffic signal"""
    if system_manager is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        from traffic_control import SignalState
        state = SignalState(control.state.lower())
        system_manager.signal_controller.set_signal_state(control.direction, state)
        return {"status": "success", "message": f"Signal {control.direction} set to {control.state}"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signal state")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/priority/activate")
async def activate_priority(request: PriorityRequest):
    """Activate priority mode for a lane"""
    if system_manager is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    success = system_manager.signal_controller.activate_priority(request.lane)
    
    if success:
        return {"status": "success", "message": f"Priority activated for {request.lane}"}
    else:
        raise HTTPException(status_code=400, detail="Failed to activate priority")


@app.post("/api/priority/deactivate")
async def deactivate_priority():
    """Deactivate priority mode"""
    if system_manager is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    system_manager.signal_controller.deactivate_priority()
    return {"status": "success", "message": "Priority mode deactivated"}


@app.post("/api/override/enable")
async def enable_override():
    """Enable manual override"""
    if system_manager is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    system_manager.signal_controller.set_manual_override(True)
    return {"status": "success", "message": "Manual override enabled"}


@app.post("/api/override/disable")
async def disable_override():
    """Disable manual override"""
    if system_manager is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    system_manager.signal_controller.set_manual_override(False)
    return {"status": "success", "message": "Manual override disabled"}


@app.get("/api/detections/latest")
async def get_latest_detections():
    """Get latest detection events"""
    if system_manager is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Return latest detections from database
    detections = system_manager.db.get_recent_detections(limit=10)
    return {"detections": detections}


@app.get("/api/statistics")
async def get_statistics():
    """Get system statistics"""
    if system_manager is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    stats = system_manager.get_statistics()
    return stats


@app.get("/api/video/feed")
async def video_feed():
    """Stream video feed with detections"""
    if system_manager is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    def generate():
        import time
        while True:
            try:
                frame = system_manager.get_display_frame()
                if frame is not None:
                    # Encode frame as JPEG
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n'
                               b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n'
                               b'\r\n' + frame_bytes + b'\r\n')
                
                # Small delay to control frame rate (~30 FPS)
                time.sleep(0.033)
            except Exception as e:
                logger.error(f"Error generating video frame: {e}")
                time.sleep(0.1)
    
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    
    try:
        while True:
            if system_manager:
                # Send status update
                status = system_manager.get_status()
                await websocket.send_json(status)
            
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass  # Already closed


@app.post("/api/system/start")
async def start_system():
    """Start the detection system"""
    if system_manager is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    system_manager.start()
    return {"status": "success", "message": "System started"}


@app.post("/api/system/stop")
async def stop_system():
    """Stop the detection system"""
    if system_manager is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    system_manager.stop()
    return {"status": "success", "message": "System stopped"}


@app.get("/api/logs/recent")
async def get_recent_logs():
    """Get recent system logs"""
    if system_manager is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    logs = system_manager.get_recent_logs(limit=50)
    return {"logs": logs}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
