# API Documentation

## Overview

The Lifeline API provides RESTful endpoints and WebSocket connections for controlling and monitoring the traffic management system.

**Base URL**: `http://localhost:8000`

## Authentication

Currently, the API does not require authentication. In production, implement proper authentication mechanisms.

## REST API Endpoints

### System Management

#### `GET /`
Root endpoint

**Response**:
```json
{
  "message": "Lifeline Traffic Management System API",
  "version": "1.0.0",
  "status": "running"
}
```

#### `GET /api/status`
Get complete system status

**Response**:
```json
{
  "status": "running",
  "uptime": 3600.5,
  "detections_count": 45,
  "priority_activations": 12,
  "priority_mode": false,
  "priority_lane": null,
  "states": {
    "north": "red",
    "south": "green",
    "east": "red",
    "west": "red"
  },
  "video_stats": {
    "frame_count": 54000,
    "actual_fps": 30,
    "dropped_frames": 12
  },
  "timestamp": "2025-11-09T10:30:00"
}
```

#### `POST /api/system/start`
Start the detection and control system

**Response**:
```json
{
  "status": "success",
  "message": "System started"
}
```

#### `POST /api/system/stop`
Stop the system

**Response**:
```json
{
  "status": "success",
  "message": "System stopped"
}
```

### Traffic Signals

#### `GET /api/signals`
Get all traffic signal states

**Response**:
```json
{
  "north": "red",
  "south": "green",
  "east": "red",
  "west": "red"
}
```

#### `POST /api/signals/control`
Manually control a traffic signal (requires manual override enabled)

**Request Body**:
```json
{
  "direction": "north",
  "state": "green"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Signal north set to green"
}
```

**Error Response** (400):
```json
{
  "detail": "Invalid signal state"
}
```

### Priority Control

#### `POST /api/priority/activate`
Activate priority mode for a specific lane

**Request Body**:
```json
{
  "lane": "north",
  "duration": 60  // optional, seconds
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Priority activated for north"
}
```

#### `POST /api/priority/deactivate`
Deactivate priority mode and return to normal operation

**Response**:
```json
{
  "status": "success",
  "message": "Priority mode deactivated"
}
```

### Manual Override

#### `POST /api/override/enable`
Enable manual override mode

**Response**:
```json
{
  "status": "success",
  "message": "Manual override enabled"
}
```

#### `POST /api/override/disable`
Disable manual override mode

**Response**:
```json
{
  "status": "success",
  "message": "Manual override disabled"
}
```

### Detection & Logging

#### `GET /api/detections/latest`
Get latest detection events

**Query Parameters**:
- `limit` (optional): Number of records (default: 10)

**Response**:
```json
{
  "detections": [
    {
      "id": 123,
      "timestamp": "2025-11-09T10:30:00",
      "class_name": "ambulance",
      "confidence": 0.95,
      "lane": "north",
      "bbox_x1": 100,
      "bbox_y1": 150,
      "bbox_x2": 300,
      "bbox_y2": 400
    }
  ]
}
```

#### `GET /api/statistics`
Get system statistics

**Response**:
```json
{
  "total_detections": 450,
  "priority_activations": 120,
  "detections_by_lane": {
    "north": 120,
    "south": 110,
    "east": 115,
    "west": 105
  },
  "detections_by_hour": {
    "08": 45,
    "09": 52,
    "10": 38
  },
  "period_days": 7
}
```

#### `GET /api/logs/recent`
Get recent system logs

**Response**:
```json
{
  "logs": [
    {
      "timestamp": "2025-11-09T10:30:00",
      "level": "INFO",
      "message": "Ambulance detected in north lane"
    }
  ]
}
```

### Video Stream

#### `GET /api/video/feed`
Get live video stream with detections

**Response**: MJPEG stream (multipart/x-mixed-replace)

**Usage in HTML**:
```html
<img src="http://localhost:8000/api/video/feed" />
```

### Health Check

#### `GET /health`
Health check endpoint for monitoring

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-09T10:30:00"
}
```

## WebSocket API

### Connection

**URL**: `ws://localhost:8000/ws/updates`

### Real-time Updates

Connect to receive real-time system updates every second.

**JavaScript Example**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/updates');

ws.onopen = () => {
  console.log('Connected to Lifeline');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
  // data contains same structure as /api/status
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

**Python Example**:
```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print(f"Update: {data}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

def on_open(ws):
    print("Connected")

ws = websocket.WebSocketApp(
    "ws://localhost:8000/ws/updates",
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()
```

## Error Responses

### 400 Bad Request
Invalid request parameters

```json
{
  "detail": "Invalid signal state"
}
```

### 503 Service Unavailable
System not initialized

```json
{
  "detail": "System not initialized"
}
```

### 500 Internal Server Error
Server error

```json
{
  "detail": "Error message here"
}
```

## Rate Limiting

Currently no rate limiting is implemented. In production:
- Implement rate limiting (e.g., 100 requests/minute)
- Use API keys for authentication
- Log all API access

## CORS

CORS is enabled for all origins (`*`) by default. For production:
- Restrict to specific domains
- Update CORS settings in `src/api/api_server.py`

## Integration Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000"

# Get status
response = requests.get(f"{BASE_URL}/api/status")
status = response.json()
print(f"System status: {status['status']}")

# Activate priority
response = requests.post(
    f"{BASE_URL}/api/priority/activate",
    json={"lane": "north"}
)
result = response.json()
print(result['message'])

# Get statistics
response = requests.get(f"{BASE_URL}/api/statistics")
stats = response.json()
print(f"Total detections: {stats['total_detections']}")
```

### cURL Examples

```bash
# Get status
curl http://localhost:8000/api/status

# Start system
curl -X POST http://localhost:8000/api/system/start

# Activate priority
curl -X POST http://localhost:8000/api/priority/activate \
  -H "Content-Type: application/json" \
  -d '{"lane": "north"}'

# Control signal
curl -X POST http://localhost:8000/api/signals/control \
  -H "Content-Type: application/json" \
  -d '{"direction": "north", "state": "green"}'

# Get statistics
curl http://localhost:8000/api/statistics
```

### JavaScript/Fetch

```javascript
// Get status
fetch('http://localhost:8000/api/status')
  .then(response => response.json())
  .then(data => console.log('Status:', data))
  .catch(error => console.error('Error:', error));

// Activate priority
fetch('http://localhost:8000/api/priority/activate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ lane: 'north' }),
})
  .then(response => response.json())
  .then(data => console.log('Result:', data))
  .catch(error => console.error('Error:', error));
```

## Extending the API

To add new endpoints, edit `src/api/api_server.py`:

```python
@app.get("/api/custom/endpoint")
async def custom_endpoint():
    """Your custom endpoint"""
    return {"message": "Custom data"}
```

## Production Considerations

For production deployment:

1. **Security**:
   - Implement authentication (JWT, OAuth)
   - Use HTTPS/WSS
   - Validate all inputs
   - Rate limiting

2. **Performance**:
   - Use load balancer
   - Cache frequently accessed data
   - Optimize database queries

3. **Monitoring**:
   - Log all API calls
   - Monitor response times
   - Alert on errors

4. **Documentation**:
   - Use OpenAPI/Swagger for auto-docs
   - Keep API versioned
   - Document breaking changes
