# User Guide

## Getting Started

### Quick Start

1. **Start the System**
   ```powershell
   python main.py
   ```

2. **Access the Dashboard**
   - Open your browser
   - Navigate to: `http://localhost:8000`

3. **Monitor the System**
   - View live video feed
   - Monitor traffic signals
   - Check detection statistics

### System Modes

#### Production Mode (Default)
- Real-time camera feed
- Active traffic control
- Full logging enabled

```powershell
python main.py --mode production
```

#### Simulation Mode
- Use pre-recorded videos
- Test system without real hardware

```powershell
python main.py --mode simulation --video data/test_videos/traffic_sample.mp4
```

#### Testing Mode
- Disable actual signal control
- Safe for development

```powershell
python main.py --mode testing
```

## Dashboard Features

### 1. Live Video Feed
- **Shows**: Real-time camera view with detection boxes
- **Controls**: 
  - Pause/Resume: Temporarily stop processing
  - Record: Save video with detections

### 2. Traffic Signals Display
- **Visual representation** of all four directions
- **Color coding**:
  - 🔴 Red: Stop
  - 🟡 Yellow: Caution
  - 🟢 Green: Go
- **Priority indicator** in center shows emergency mode status

### 3. Statistics Panel
- **Total Detections**: Number of ambulances detected
- **Priority Activations**: Times emergency mode triggered
- **Avg Response Time**: Average detection-to-signal time
- **System Uptime**: How long system has been running

### 4. Event Log
- Real-time system events
- Detection notifications
- Signal changes
- System alerts

## Control Features

### Manual Override
1. Click **"Manual Override"** button
2. Control panel appears below signals
3. Manually set any signal to Red/Yellow/Green
4. Click again to disable override

⚠️ **Warning**: Use manual override carefully. It bypasses safety checks.

### Emergency Stop
- **Purpose**: Immediately stop all automatic control
- **Action**: Sets all signals to RED
- **Use**: Only in emergencies or system malfunctions

### Start/Stop System
- **Start**: Begin detection and control
- **Stop**: Pause system (signals remain in last state)

## Configuration

### Camera Settings

Edit `config/config.yaml`:

```yaml
camera:
  source: 0  # 0 = webcam, or "rtsp://..." for IP camera
  width: 1280
  height: 720
  fps: 30
```

**Camera Sources**:
- Webcam: `0`, `1`, `2` (device index)
- IP Camera: `"rtsp://192.168.1.100:554/stream"`
- Video File: `"data/test_videos/traffic.mp4"`

### Detection Settings

```yaml
detection:
  confidence_threshold: 0.6  # 0.0 to 1.0, higher = more strict
  device: "cuda"  # "cuda" or "cpu"
```

**Confidence Threshold**:
- `0.5`: More detections, more false positives
- `0.7`: Balanced (recommended)
- `0.9`: Very strict, fewer detections

### Traffic Timing

```yaml
traffic_control:
  default_green_duration: 45  # Normal green light time (seconds)
  ambulance_green_duration: 60  # Emergency green time (seconds)
  yellow_duration: 3  # Yellow light time
```

### Lane Configuration

Define lane regions for your intersection:

```yaml
lanes:
  lane_regions:
    north: [0, 0, 640, 360]      # x1, y1, x2, y2
    south: [0, 360, 640, 720]
    east: [640, 0, 1280, 360]
    west: [640, 360, 1280, 720]
```

## API Usage

### REST API Endpoints

#### Get System Status
```bash
curl http://localhost:8000/api/status
```

#### Activate Priority
```bash
curl -X POST http://localhost:8000/api/priority/activate \
  -H "Content-Type: application/json" \
  -d '{"lane": "north"}'
```

#### Control Signal Manually
```bash
curl -X POST http://localhost:8000/api/signals/control \
  -H "Content-Type: application/json" \
  -d '{"direction": "north", "state": "green"}'
```

#### Get Statistics
```bash
curl http://localhost:8000/api/statistics
```

### WebSocket Connection

Real-time updates via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/updates');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('System update:', data);
};
```

## Common Tasks

### Change Camera

```powershell
python main.py --camera 1  # Use second camera
python main.py --camera "rtsp://camera-ip/stream"  # IP camera
```

### Record Session

In dashboard, click **"Record"** button. Video saved to `data/recordings/`.

### View Logs

```powershell
# View real-time logs
Get-Content data/logs/system.log -Wait -Tail 50
```

### Export Statistics

Statistics are automatically logged to database. To export:

```python
from src.utils.database import Database

db = Database('data/lifeline.db')
stats = db.get_statistics(days=30)
print(stats)
```

## Keyboard Shortcuts

- `Ctrl + E`: Emergency Stop
- `Ctrl + M`: Toggle Manual Override
- `Ctrl + C`: Exit application

## Troubleshooting

### No Detections

**Possible causes**:
1. Camera not working
2. Confidence threshold too high
3. Model not loaded

**Solutions**:
- Check video feed is visible
- Lower `confidence_threshold` to 0.5
- Ensure model file exists in `models/`

### False Detections

**Solutions**:
- Increase `confidence_threshold` to 0.8
- Train custom model on your specific environment
- Adjust lane regions to exclude irrelevant areas

### Signals Not Changing

**Check**:
1. System is in running state
2. Manual override is disabled
3. Check event log for errors
4. Verify `traffic_control` settings in config

### High CPU/Memory Usage

**Solutions**:
- Reduce camera resolution
- Use `device: "cuda"` if GPU available
- Increase `frame_skip` in config
- Close other applications

## Best Practices

### For Production Deployment

1. **Test thoroughly** in simulation mode first
2. **Use high-quality cameras** with good lighting
3. **Train custom model** on your local ambulances
4. **Set up monitoring** and alerts
5. **Have manual override** procedures in place
6. **Regular system health checks**
7. **Backup database** regularly

### For Development

1. Use simulation mode with test videos
2. Enable debug logging
3. Test edge cases (night, rain, occlusions)
4. Monitor false positive/negative rates
5. Validate signal timing is safe

## Safety Considerations

⚠️ **IMPORTANT**: This is a prototype system

- Always have human oversight
- Test extensively before real deployment
- Ensure fail-safe mechanisms
- Comply with local traffic regulations
- Regular maintenance and updates
- Emergency override always available

## Performance Optimization

### For Real-time Performance

1. **Use GPU**: Set `device: "cuda"`
2. **Reduce Resolution**: 720p is usually sufficient
3. **Optimize Threshold**: Find balance between accuracy and speed
4. **Frame Skipping**: Process every Nth frame if needed

### For Accuracy

1. **Train Custom Model**: Use local ambulance images
2. **Good Lighting**: Ensure cameras have clear view
3. **Multiple Cameras**: Cover all lanes
4. **Regular Updates**: Retrain model periodically

## Support & Feedback

For issues, improvements, or questions:
- Check documentation in `docs/`
- Review log files in `data/logs/`
- Run integration tests: `python scripts/integration_test.py`
