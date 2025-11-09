# LifeLine AI - SUMO Traffic Simulation

## 🚑 Smart Emergency Vehicle Management System

An AI-powered traffic simulation system that detects ambulances and dynamically controls traffic signals to create green corridors, reducing emergency response times.

---

## 📋 Prerequisites

1. **SUMO Installation**
   - Download and install SUMO from: https://eclipse.dev/sumo/
   - Windows: Install to `C:\Program Files (x86)\Eclipse\Sumo`
   - Linux: `sudo apt-get install sumo sumo-tools sumo-doc`
   - macOS: `brew install sumo`

2. **Set SUMO_HOME Environment Variable**
   - Windows: `setx SUMO_HOME "C:\Program Files (x86)\Eclipse\Sumo"`
   - Linux/Mac: `export SUMO_HOME=/usr/share/sumo` (add to `.bashrc`)

3. **Python Requirements**
   - Python 3.7+
   - TraCI (comes with SUMO)

---

## 🚀 Quick Start

### Step 1: Generate Network

```bash
cd sumo_simulation
python setup_simulation.py
```

This will:
- Verify SUMO installation
- Generate `city.net.xml` from node and edge files
- Validate all configuration files

### Step 2: Run Simulation

```bash
python simulation.py
```

This will:
- Launch SUMO-GUI
- Load the 4×4 urban grid network
- Spawn normal vehicles and create congestion
- Spawn ambulance at t=100s
- Detect congestion and activate green corridors
- Log all metrics to `results.csv`

---

## 📁 Project Structure

```
sumo_simulation/
├── city.nod.xml           # Network nodes (intersections)
├── city.edg.xml           # Network edges (roads)
├── city.net.xml           # Generated network file
├── routes.rou.xml         # Vehicle routes and flows
├── simulation.sumocfg     # SUMO configuration
├── gui-settings.xml       # GUI visualization settings
├── simulation.py          # Main Python control script
├── setup_simulation.py    # Network generation script
├── results.csv            # Output metrics (generated)
└── README.md             # This file
```

---

## 🎯 Features

### 1. **Network Setup**
- 4×4 urban grid (16 intersections)
- All intersections have traffic lights
- Two-lane bidirectional roads
- Speed limit: 13.9 m/s (~50 km/h)

### 2. **Traffic Generation**
- **Cars:** 80% of traffic (multiple flows)
- **Buses:** 10% of traffic
- **Bikes:** 10% of traffic
- High density to simulate congestion
- Random departure times and speeds

### 3. **Ambulance**
- Spawns at t=100s
- Red color, higher max speed (25 m/s)
- Crosses 4+ intersections
- Route: n00 → n01 → n11 → n21 → n31

### 4. **AI-Powered Control**

#### Congestion Detection
- Monitors average speed of vehicles ahead
- Checks queue length at intersections
- Threshold: speed < 2 m/s OR queue > 5 vehicles
- Detection range: 100 meters ahead

#### Green Corridor Activation
- Identifies upcoming traffic lights
- Sets lights to GREEN for ambulance
- Sets cross-traffic to RED
- Optionally clears nearby vehicles (simulates drivers yielding)
- Prints: "🚑 Ambulance detected in congestion — activating green corridor"

#### Signal Restoration
- Monitors ambulance position
- Restores normal traffic signals after ambulance passes
- Ensures safe transitions

### 5. **Real-time Logging**
Logs to `results.csv` every step:
- `time_step`: Simulation time
- `ambulance_speed`: Current speed (m/s)
- `ambulance_x`, `ambulance_y`: Position
- `is_congested`: Congestion detected (True/False)
- `corridor_active`: Green corridor active (True/False)
- `nearest_tls`: Nearest traffic light ID
- `tls_state`: Traffic light state (G/r/y)

### 6. **Performance Metrics**

At simulation end, displays:
- Average ambulance speed vs normal vehicles
- Speed advantage percentage
- Travel time (spawn to arrival)
- Number of congestion detections
- Green corridor activations
- Vehicles cleared from path
- Estimated time savings
- Estimated delay reduction percentage

---

## 🔧 Configuration

### Adjust Congestion Thresholds

Edit in `simulation.py`:

```python
self.CONGESTION_SPEED_THRESHOLD = 2.0  # m/s
self.CONGESTION_QUEUE_THRESHOLD = 5    # vehicles
self.DETECTION_RANGE = 100             # meters
```

### Change Ambulance Spawn Time

Edit in `routes.rou.xml`:

```xml
<vehicle id="ambulance_1" type="ambulance" route="ambulance_route" depart="100" .../>
```

### Adjust Traffic Density

Edit flow probabilities in `routes.rou.xml`:

```xml
<flow id="flow_cars_WE" type="car" route="route_WE_1" begin="0" end="1000" probability="0.15"/>
```

Higher probability = more vehicles

### Use Command-line SUMO (faster)

Edit in `simulation.py`:

```python
controller = LifeLineTrafficController(
    sumo_cfg="simulation.sumocfg",
    use_gui=False  # Set to False for faster simulation
)
```

---

## 📊 Understanding the Output

### Console Output Example:

```
================================================================================
🚑 LifeLine AI - Smart Traffic Simulation System
================================================================================
Starting SUMO GUI...
Configuration: simulation.sumocfg
--------------------------------------------------------------------------------
📊 Logging initialized: results.csv
--------------------------------------------------------------------------------

🚨 AMBULANCE DETECTED at step 100
--------------------------------------------------------------------------------
Step 100: Ambulance position (23.4, 5.2), speed=12.3 m/s, congestion=False, TLS ahead=1
Step 110: Ambulance position (145.7, 8.1), speed=8.5 m/s, congestion=True, TLS ahead=2
🚑 Ambulance detected in congestion — activating green corridor at TLS n01
   🚗 Cleared 3 vehicles from ambulance path
Step 120: Ambulance position (198.2, 152.3), speed=15.2 m/s, congestion=False, TLS ahead=1
✅ Restoring normal traffic at TLS n01

🏁 Ambulance reached destination. Continuing for 50 more steps...

================================================================================
📊 PERFORMANCE METRICS SUMMARY
================================================================================
Average Ambulance Speed: 14.52 m/s
Average Normal Vehicle Speed: 8.73 m/s
Ambulance Speed Advantage: 66.3%

Ambulance Travel Time: 245 seconds
Spawn Time: Step 100
Arrival Time: Step 345

Congestion Detections: 12
Green Corridor Activations: 4
Total Vehicles Cleared: 15

💡 Estimated Time Saved: ~48 seconds
📉 Estimated Delay Reduction: ~16.4%
================================================================================
📄 Detailed logs saved to: results.csv
================================================================================
```

### CSV Output (`results.csv`):

```csv
time_step,ambulance_speed,ambulance_x,ambulance_y,is_congested,corridor_active,nearest_tls,tls_state
100,12.34,23.5,5.2,False,False,n01,rrrGGG
101,11.89,35.7,5.3,False,False,n01,rrrGGG
110,8.45,145.2,8.1,True,True,n01,GGGGGG
...
```

---

## 🎨 Visualization

In SUMO-GUI you'll see:
- **Red vehicle** = Ambulance (highlighted)
- **Yellow vehicles** = Cars
- **Cyan vehicles** = Buses
- **Blue vehicles** = Bikes
- **Green traffic lights** = Active green corridor
- **Route lines** = Vehicle paths

---

## 🐛 Troubleshooting

### Error: "SUMO_HOME environment variable not set"

**Solution:**
```bash
# Windows
setx SUMO_HOME "C:\Program Files (x86)\Eclipse\Sumo"

# Linux/Mac
export SUMO_HOME=/usr/share/sumo
```

### Error: "netconvert not found"

**Solution:** Make sure SUMO is installed and SUMO_HOME is set correctly.

### Network generation fails

**Solution:**
```bash
# Manually generate network
cd sumo_simulation
netconvert --node-files=city.nod.xml --edge-files=city.edg.xml --output-file=city.net.xml
```

### TraCI connection error

**Solution:** Make sure no other SUMO instance is running. Close all SUMO windows and try again.

### Ambulance doesn't spawn

**Solution:** Check `routes.rou.xml` - make sure route edges exist in network.

---

## 📈 Extending the System

### Add More Vehicle Types

Edit `routes.rou.xml`:

```xml
<vType id="truck" vClass="truck" speedFactor="0.7" length="10" color="0.5,0.5,0.5"/>
<flow id="flow_trucks" type="truck" route="route_WE_1" begin="0" end="1000" probability="0.05"/>
```

### Add More Intersections

1. Edit `city.nod.xml` - add more nodes
2. Edit `city.edg.xml` - add connecting edges
3. Run `python setup_simulation.py`

### Implement Advanced Algorithms

Edit `simulation.py`:

```python
def activate_green_corridor(self, traffic_light_id, ambulance_lane):
    # Add your custom logic here
    # - Predictive traffic control
    # - Multi-intersection coordination
    # - Learning-based optimization
    pass
```

### Add Audio/Visual Alerts

```python
# In process_step()
if is_congested:
    import winsound
    winsound.Beep(1000, 200)  # 1000 Hz, 200ms
```

---

## 🤝 Integration with LifeLine Main System

This SUMO simulation can be integrated with the main LifeLine AI system:

1. **Replace camera input** with SUMO vehicle positions
2. **Use TraCI** for detection instead of YOLOv8
3. **Test algorithms** in simulation before real deployment
4. **Validate performance** with controlled scenarios

Example integration:

```python
# In main LifeLine system
from sumo_simulation.simulation import LifeLineTrafficController

# Run simulation
controller = LifeLineTrafficController()
controller.run_simulation()

# Use metrics for validation
metrics = controller.metrics
```

---

## 📚 Resources

- **SUMO Documentation:** https://sumo.dlr.de/docs/
- **TraCI Tutorial:** https://sumo.dlr.de/docs/TraCI.html
- **SUMO Examples:** https://github.com/eclipse/sumo/tree/main/tests
- **LifeLine Main Project:** ../README.md

---

## 📝 License

This simulation is part of the LifeLine AI project.
See main project LICENSE for details.

---

## 👥 Authors

LifeLine AI Team
- Smart Traffic Management
- Emergency Vehicle Prioritization
- Real-time AI Control

---

**🚑 Saving Lives Through Intelligent Traffic Management**
