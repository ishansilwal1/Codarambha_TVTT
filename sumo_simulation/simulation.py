"""
LifeLine AI - Smart Traffic Simulation System
AI-Powered Emergency Management with Dynamic Traffic Control

This script uses SUMO TraCI API to:
1. Detect ambulances in real-time
2. Identify traffic congestion
3. Activate green corridor for emergency vehicles
4. Log performance metrics
"""

import os
import sys
import csv
import time
from collections import defaultdict

# Check if SUMO_HOME is set
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci
from sumolib import checkBinary


class LifeLineTrafficController:
    """
    Main controller for LifeLine AI Traffic Management System
    Handles ambulance detection, congestion analysis, and green corridor activation
    """
    
    def __init__(self, sumo_cfg="simulation.sumocfg", use_gui=True):
        """
        Initialize the traffic controller
        
        Args:
            sumo_cfg (str): Path to SUMO configuration file
            use_gui (bool): Whether to use SUMO-GUI (True) or command-line SUMO (False)
        """
        self.sumo_cfg = sumo_cfg
        self.use_gui = use_gui
        
        # Ambulance tracking (7 ambulances)
        self.ambulance_ids = [f"ambulance_{i}" for i in range(1, 8)]
        self.ambulances_detected = set()
        self.ambulances_completed = set()
        self.ambulance_spawn_times = {}
        self.ambulance_arrival_times = {}
        
        # Green corridor state
        self.active_corridors = {}  # Dict: {tls_id: {'ambulance_id': str, 'lane': str, 'activated_at': int}}
        self.ambulance_priority_queue = []  # List of (detection_time, ambulance_id, tls_id) for priority handling
        self.original_tls_programs = {}  # Store original TLS programs for restoration
        self.corridor_activation_count = 0
        
        # Performance metrics
        self.metrics = {
            'ambulance_speeds': [],
            'normal_vehicle_speeds': [],
            'congestion_detections': 0,
            'corridor_activations': 0,
            'total_vehicles_cleared': 0
        }
        
        # Simulation state
        self.step = 0
        self.csv_file = None
        self.csv_writer = None
        
        # Congestion thresholds
        self.CONGESTION_SPEED_THRESHOLD = 2.0  # m/s
        self.CONGESTION_QUEUE_THRESHOLD = 5  # vehicles
        self.DETECTION_RANGE = 150  # meters ahead - increased for earlier detection
        
    def start_simulation(self):
        """Launch SUMO simulation with TraCI"""
        if self.use_gui:
            sumo_binary = checkBinary('sumo-gui')
            sumo_cmd = [sumo_binary, "-c", self.sumo_cfg, 
                        "--start", "--quit-on-end"]
        else:
            sumo_binary = checkBinary('sumo')
            sumo_cmd = [sumo_binary, "-c", self.sumo_cfg, 
                        "--quit-on-end"]
        
        print("=" * 80)
        print("🚑 LifeLine AI - Smart Traffic Simulation System")
        print("=" * 80)
        print(f"Starting SUMO {'GUI' if self.use_gui else 'command-line'}...")
        print(f"Configuration: {self.sumo_cfg}")
        print("-" * 80)
        
        traci.start(sumo_cmd)
        time.sleep(3 if self.use_gui else 1)  # Extra delay for GUI to fully initialize
        
        # Initialize CSV logging
        self._initialize_logging()
        
    def _initialize_logging(self):
        """Initialize CSV file for logging simulation metrics"""
        self.csv_file = open('results.csv', 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            'time_step', 'ambulance_id', 'ambulance_speed', 'ambulance_x', 'ambulance_y',
            'is_congested', 'corridor_active', 'nearest_tls', 'tls_state'
        ])
        print("📊 Logging initialized: results.csv")
        print(f"📍 Tracking {len(self.ambulance_ids)} ambulances")
        print("-" * 80)
        
    def check_congestion(self, ambulance_id):
        """
        Check if there is congestion ahead of the ambulance
        
        Args:
            ambulance_id (str): ID of the ambulance vehicle
            
        Returns:
            tuple: (is_congested, congestion_details)
        """
        try:
            # Get ambulance position and route
            amb_pos = traci.vehicle.getPosition(ambulance_id)
            amb_road = traci.vehicle.getRoadID(ambulance_id)
            amb_lane = traci.vehicle.getLaneID(ambulance_id)
            
            # Get vehicles on the same road ahead
            nearby_vehicles = []
            for veh_id in traci.vehicle.getIDList():
                if veh_id == ambulance_id:
                    continue
                    
                veh_road = traci.vehicle.getRoadID(veh_id)
                if veh_road == amb_road:
                    veh_pos = traci.vehicle.getPosition(veh_id)
                    distance = ((veh_pos[0] - amb_pos[0])**2 + (veh_pos[1] - amb_pos[1])**2)**0.5
                    
                    if distance < self.DETECTION_RANGE:
                        nearby_vehicles.append({
                            'id': veh_id,
                            'speed': traci.vehicle.getSpeed(veh_id),
                            'distance': distance
                        })
            
            # Check congestion based on speed and queue length
            if nearby_vehicles:
                avg_speed = sum(v['speed'] for v in nearby_vehicles) / len(nearby_vehicles)
                queue_length = len(nearby_vehicles)
                
                is_congested = (avg_speed < self.CONGESTION_SPEED_THRESHOLD or 
                              queue_length > self.CONGESTION_QUEUE_THRESHOLD)
                
                details = {
                    'avg_speed': avg_speed,
                    'queue_length': queue_length,
                    'nearby_vehicles': len(nearby_vehicles)
                }
                
                if is_congested:
                    self.metrics['congestion_detections'] += 1
                
                return is_congested, details
            
            return False, {'avg_speed': 0, 'queue_length': 0, 'nearby_vehicles': 0}
            
        except traci.exceptions.TraCIException:
            return False, {}
    
    def get_upcoming_traffic_lights(self, ambulance_id):
        """
        Get the list of upcoming traffic lights in ambulance's route
        
        Args:
            ambulance_id (str): ID of the ambulance vehicle
            
        Returns:
            list: List of traffic light IDs ahead
        """
        try:
            # Get next traffic lights
            next_tls = traci.vehicle.getNextTLS(ambulance_id)
            
            if next_tls:
                # Extract TLS IDs from the result
                # next_tls returns: [(tlsID, tlsIndex, distance, state), ...]
                tls_ahead = []
                for tls_info in next_tls:
                    tls_id = tls_info[0]
                    distance = tls_info[2]
                    if distance < 150:  # Within 150m range
                        tls_ahead.append(tls_id)
                return tls_ahead
            
        except traci.exceptions.TraCIException:
            pass
        
        return []
    
    def activate_green_corridor(self, traffic_light_id, ambulance_id, ambulance_lane):
        """
        Activate green corridor at specified traffic light
        ONLY turns ambulance's lane GREEN, keeps cross traffic RED
        
        Args:
            traffic_light_id (str): ID of the traffic light
            ambulance_id (str): ID of the ambulance
            ambulance_lane (str): Current lane of ambulance
        """
        try:
            # Check if another ambulance already has priority at this junction
            if traffic_light_id in self.active_corridors:
                existing = self.active_corridors[traffic_light_id]
                # If different ambulance, check which one was detected first
                if existing['ambulance_id'] != ambulance_id:
                    print(f"   ⏸️  Waiting: Another ambulance has priority at {traffic_light_id}")
                    return
            
            # Store original program if not already stored
            if traffic_light_id not in self.original_tls_programs:
                current_state = traci.trafficlight.getRedYellowGreenState(traffic_light_id)
                self.original_tls_programs[traffic_light_id] = {
                    'program': traci.trafficlight.getProgram(traffic_light_id),
                    'phase': traci.trafficlight.getPhase(traffic_light_id),
                    'state': current_state
                }
            
            # Get controlled links to map lanes to signal indices
            controlled_links = traci.trafficlight.getControlledLinks(traffic_light_id)
            
            # Extract ambulance edge from lane (format: "edge_laneIndex")
            amb_edge = ambulance_lane.rsplit('_', 1)[0] if '_' in ambulance_lane else ambulance_lane
            
            # Build signal state: GREEN only for ambulance lane, RED for all others
            new_state = []
            ambulance_signal_found = False
            
            for i, link in enumerate(controlled_links):
                if len(link) > 0:
                    incoming_lane = link[0][0]  # [0][0] is the incoming lane
                    incoming_edge = incoming_lane.rsplit('_', 1)[0] if '_' in incoming_lane else incoming_lane
                    
                    # Check if this signal controls the ambulance's lane
                    if incoming_edge == amb_edge or incoming_lane == ambulance_lane:
                        new_state.append('G')  # GREEN for ambulance lane ONLY
                        ambulance_signal_found = True
                    else:
                        new_state.append('r')  # RED for all cross-traffic (lowercase = definite red)
                else:
                    new_state.append('r')  # Default to red if no link info
            
            signal_state = ''.join(new_state)
            
            # Apply the signal state - GREEN for ambulance lane ONLY
            traci.trafficlight.setRedYellowGreenState(traffic_light_id, signal_state)
            
            # Mark as active corridor with priority info
            self.active_corridors[traffic_light_id] = {
                'ambulance_id': ambulance_id,
                'lane': ambulance_lane,
                'activated_at': self.step
            }
            self.corridor_activation_count += 1
            self.metrics['corridor_activations'] += 1
            
            print(f"🚨 {ambulance_id.upper()} - GREEN CORRIDOR ACTIVATED!")
            print(f"   📍 Traffic Light: {traffic_light_id}")
            print(f"   🟢 GREEN: Ambulance Lane ONLY ({amb_edge})")
            print(f"   🔴 RED: All Cross Traffic")
            print(f"   Signal State: {signal_state}")
            
        except traci.exceptions.TraCIException as e:
            print(f"⚠️  Error activating corridor at {traffic_light_id}: {e}")
    
    def clear_nearby_vehicles(self, ambulance_id, radius=50):
        """
        Simulate vehicles clearing the path by temporarily removing nearby vehicles
        
        Args:
            ambulance_id (str): ID of the ambulance
            radius (float): Radius around ambulance to clear (meters)
            
        Returns:
            int: Number of vehicles removed
        """
        try:
            amb_pos = traci.vehicle.getPosition(ambulance_id)
            removed_count = 0
            
            vehicles_to_remove = []
            for veh_id in traci.vehicle.getIDList():
                if veh_id in self.ambulance_ids:
                    continue
                
                veh_pos = traci.vehicle.getPosition(veh_id)
                distance = ((veh_pos[0] - amb_pos[0])**2 + (veh_pos[1] - amb_pos[1])**2)**0.5
                
                if distance < radius:
                    vehicles_to_remove.append(veh_id)
            
            # Remove vehicles
            for veh_id in vehicles_to_remove:
                traci.vehicle.remove(veh_id)
                removed_count += 1
            
            if removed_count > 0:
                self.metrics['total_vehicles_cleared'] += removed_count
                print(f"   🚗 Cleared {removed_count} vehicles from ambulance path")
            
            return removed_count
            
        except traci.exceptions.TraCIException:
            return 0
    
    def restore_signal(self, traffic_light_id):
        """
        Restore traffic light to its original program after ambulance passes
        
        Args:
            traffic_light_id (str): ID of the traffic light to restore
        """
        try:
            if traffic_light_id in self.original_tls_programs:
                original = self.original_tls_programs[traffic_light_id]
                
                # Restore original program
                traci.trafficlight.setProgram(traffic_light_id, original['program'])
                
                # Remove from active corridors
                if traffic_light_id in self.active_corridors:
                    del self.active_corridors[traffic_light_id]
                
                print(f"✅ AMBULANCE PASSED - RESTORING NORMAL TRAFFIC FLOW")
                print(f"   📍 Traffic Light: {traffic_light_id}")
                print(f"   🔄 Returning to Normal Signal Timing")
                print(f"   " + "-" * 50)
                
        except traci.exceptions.TraCIException as e:
            print(f"⚠️  Error restoring signal at {traffic_light_id}: {e}")
    
    def record_metrics(self, step):
        """
        Record metrics for current simulation step
        
        Args:
            step (int): Current simulation step
        """
        # Get ambulance data for all active ambulances
        active_ambulances = [amb_id for amb_id in self.ambulance_ids if amb_id in traci.vehicle.getIDList()]
        
        for amb_id in active_ambulances:
            ambulance_speed = traci.vehicle.getSpeed(amb_id)
            ambulance_x, ambulance_y = traci.vehicle.getPosition(amb_id)
            
            self.metrics['ambulance_speeds'].append(ambulance_speed)
            
            # Check congestion
            is_congested, _ = self.check_congestion(amb_id)
            
            # Get nearest TLS
            corridor_active = len(self.active_corridors) > 0
            tls_ahead = self.get_upcoming_traffic_lights(amb_id)
            nearest_tls = ""
            tls_state = ""
            
            if tls_ahead:
                nearest_tls = tls_ahead[0]
                try:
                    tls_state = traci.trafficlight.getRedYellowGreenState(nearest_tls)
                except:
                    tls_state = "unknown"
            
            # Write to CSV
            self.csv_writer.writerow([
                step, amb_id, ambulance_speed, ambulance_x, ambulance_y,
                is_congested, corridor_active, nearest_tls, tls_state
            ])
        
        # Record normal vehicle speeds for comparison
        for veh_id in traci.vehicle.getIDList():
            if veh_id not in self.ambulance_ids:
                speed = traci.vehicle.getSpeed(veh_id)
                self.metrics['normal_vehicle_speeds'].append(speed)
    
    def process_step(self):
        """
        Process a single simulation step
        Main logic for ambulance detection and traffic management
        """
        self.step += 1
        
        # Execute simulation step
        traci.simulationStep()
        
        # Check for all ambulances
        for amb_id in self.ambulance_ids:
            if amb_id in traci.vehicle.getIDList():
                # Track new detections
                if amb_id not in self.ambulances_detected:
                    self.ambulances_detected.add(amb_id)
                    self.ambulance_spawn_times[amb_id] = self.step
                    print(f"\n🚨 {amb_id.upper()} DETECTED at step {self.step}")
                    print("-" * 80)
                
                # Get ambulance info
                amb_speed = traci.vehicle.getSpeed(amb_id)
                amb_pos = traci.vehicle.getPosition(amb_id)
                
                # Check for congestion
                is_congested, congestion_details = self.check_congestion(amb_id)
                
                # Get upcoming traffic lights
                tls_ahead = self.get_upcoming_traffic_lights(amb_id)
                
                # Print status every 10 steps for first ambulance
                if self.step % 10 == 0 and amb_id == "ambulance_1":
                    active_ambs = len([a for a in self.ambulance_ids if a in traci.vehicle.getIDList()])
                    print(f"Step {self.step}: {active_ambs} ambulances active, "
                          f"{len(self.active_corridors)} green corridors, "
                          f"{self.metrics['corridor_activations']} total activations")
                
                # Activate green corridor if congested OR if ambulance is approaching junction
                # This ensures ambulance never stops at junctions
                if tls_ahead:
                    for tls_id in tls_ahead:
                        # Check if this TLS already has an active corridor
                        if tls_id in self.active_corridors:
                            existing_amb = self.active_corridors[tls_id]['ambulance_id']
                            if existing_amb != amb_id:
                                # Different ambulance - priority to first detected
                                continue
                        else:
                            # Activate green corridor for this ambulance
                            self.activate_green_corridor(tls_id, amb_id, traci.vehicle.getLaneID(amb_id))
                            
                            # Optionally clear nearby vehicles
                            if is_congested:
                                cleared = self.clear_nearby_vehicles(amb_id, radius=30)
                
                # Check if ambulance has passed any active corridors
                if self.active_corridors:
                    corridors_to_restore = []
                    for tls_id, corridor_info in list(self.active_corridors.items()):
                        # Only restore if THIS ambulance activated it
                        if corridor_info['ambulance_id'] == amb_id:
                            # Get TLS position
                            try:
                                tls_pos = traci.junction.getPosition(tls_id)
                                distance = ((amb_pos[0] - tls_pos[0])**2 + (amb_pos[1] - tls_pos[1])**2)**0.5
                                
                                # If ambulance is far past the TLS, restore it
                                if distance > 80:  # Reduced distance for quicker restoration
                                    corridors_to_restore.append(tls_id)
                            except:
                                pass
                    
                    # Restore signals
                    for tls_id in corridors_to_restore:
                        self.restore_signal(tls_id)
            
            else:
                # Ambulance completed route
                if amb_id in self.ambulances_detected and amb_id not in self.ambulances_completed:
                    self.ambulances_completed.add(amb_id)
                    self.ambulance_arrival_times[amb_id] = self.step
                    print(f"\n✅ {amb_id.upper()} COMPLETED ROUTE at step {self.step}")
                    print("-" * 80)
        
        # Record metrics
        self.record_metrics(self.step)
    
    def calculate_performance_metrics(self):
        """Calculate and display final performance metrics"""
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE METRICS SUMMARY")
        print("=" * 80)
        
        # Ambulance metrics
        if self.metrics['ambulance_speeds']:
            avg_amb_speed = sum(self.metrics['ambulance_speeds']) / len(self.metrics['ambulance_speeds'])
            print(f"Average Ambulance Speed: {avg_amb_speed:.2f} m/s")
        
        # Normal vehicle metrics
        if self.metrics['normal_vehicle_speeds']:
            avg_normal_speed = sum(self.metrics['normal_vehicle_speeds']) / len(self.metrics['normal_vehicle_speeds'])
            print(f"Average Normal Vehicle Speed: {avg_normal_speed:.2f} m/s")
            
            # Calculate speed advantage
            if avg_amb_speed > avg_normal_speed:
                speed_advantage = ((avg_amb_speed - avg_normal_speed) / avg_normal_speed) * 100
                print(f"Ambulance Speed Advantage: {speed_advantage:.1f}%")
        
        # Travel time for all ambulances
        if self.ambulance_spawn_times and self.ambulance_arrival_times:
            print(f"\n📊 Individual Ambulance Performance:")
            total_travel_time = 0
            for amb_id in self.ambulance_ids:
                if amb_id in self.ambulance_spawn_times and amb_id in self.ambulance_arrival_times:
                    travel_time = self.ambulance_arrival_times[amb_id] - self.ambulance_spawn_times[amb_id]
                    total_travel_time += travel_time
                    print(f"   {amb_id}: {travel_time}s (spawn: {self.ambulance_spawn_times[amb_id]}, "
                          f"arrival: {self.ambulance_arrival_times[amb_id]})")
            
            if len(self.ambulance_arrival_times) > 0:
                avg_travel_time = total_travel_time / len(self.ambulance_arrival_times)
                print(f"\n   Average Travel Time: {avg_travel_time:.1f} seconds")
                print(f"   Ambulances Completed: {len(self.ambulances_completed)}/{len(self.ambulance_ids)}")
        
        # Corridor metrics
        print(f"\nCongestion Detections: {self.metrics['congestion_detections']}")
        print(f"Green Corridor Activations: {self.metrics['corridor_activations']}")
        print(f"Total Vehicles Cleared: {self.metrics['total_vehicles_cleared']}")
        
        # Estimated time savings
        if self.metrics['corridor_activations'] > 0:
            # Rough estimate: each corridor saves ~10-15 seconds
            estimated_savings = self.metrics['corridor_activations'] * 12
            print(f"\n💡 Estimated Time Saved: ~{estimated_savings} seconds")
            
            if len(self.ambulance_arrival_times) > 0:
                avg_travel_time = sum(self.ambulance_arrival_times[amb] - self.ambulance_spawn_times[amb] 
                                     for amb in self.ambulance_arrival_times) / len(self.ambulance_arrival_times)
                delay_reduction = (estimated_savings / (avg_travel_time + estimated_savings)) * 100
                print(f"📉 Estimated Delay Reduction: ~{delay_reduction:.1f}%")
        
        print("=" * 80)
        print(f"📄 Detailed logs saved to: results.csv")
        print("=" * 80)
    
    def run_simulation(self):
        """Main simulation loop"""
        try:
            self.start_simulation()
            
            # Run until ambulance completes or max time
            max_steps = 1000
            ambulance_completed = False
            
            while self.step < max_steps:
                self.process_step()
                
                # Check if all ambulances have completed route
                if (len(self.ambulances_completed) == len(self.ambulance_ids) and
                    len(self.ambulances_detected) == len(self.ambulance_ids) and
                    not ambulance_completed):
                    ambulance_completed = True
                    print(f"\n🏁 All ambulances reached destination. Continuing for 50 more steps...")
                    max_steps = self.step + 50
            
            # Calculate and display metrics
            self.calculate_performance_metrics()
            
        except KeyboardInterrupt:
            print("\n⚠️  Simulation interrupted by user")
            
        finally:
            # Clean up
            if self.csv_file:
                self.csv_file.close()
            try:
                traci.close()
            except:
                pass  # Ignore errors during close if connection already lost
            print("\n✅ Simulation ended successfully")


def main():
    """Main entry point"""
    # Initialize controller
    controller = LifeLineTrafficController(
        sumo_cfg="simulation.sumocfg",
        use_gui=True  # Use SUMO-GUI for visualization
    )
    
    # Run simulation
    controller.run_simulation()


if __name__ == "__main__":
    main()
