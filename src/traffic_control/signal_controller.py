"""
Traffic Signal Controller Module
Manages traffic light states and priority control
"""

from enum import Enum
from typing import Dict, Optional
from datetime import datetime, timedelta
from loguru import logger
import time


class SignalState(Enum):
    """Traffic signal states"""
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    OFF = "off"


class TrafficSignalController:
    """Controls traffic signals for an intersection"""
    
    def __init__(self, config: dict):
        """
        Initialize traffic signal controller
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.directions = config['lanes']['directions']
        
        # Timing configuration
        self.default_green_duration = config['traffic_control']['default_green_duration']
        self.ambulance_green_duration = config['traffic_control']['ambulance_green_duration']
        self.yellow_duration = config['traffic_control']['yellow_duration']
        self.all_red_duration = config['traffic_control']['all_red_duration']
        self.priority_timeout = config['traffic_control']['priority_timeout']
        
        # Safety settings
        self.conflict_detection = config['safety']['conflict_detection']
        self.manual_override_enabled = config['traffic_control']['manual_override_enabled']
        
        # Current state
        self.current_states: Dict[str, SignalState] = {
            direction: SignalState.RED for direction in self.directions
        }
        
        # Priority management
        self.priority_lane: Optional[str] = None
        self.priority_start_time: Optional[datetime] = None
        self.in_priority_mode = False
        self.manual_override = False
        
        # Normal cycle tracking
        self.current_cycle_direction = 0
        self.cycle_start_time = datetime.now()
        
        logger.info("Traffic Signal Controller initialized")
    
    def activate_priority(self, lane: str) -> bool:
        """
        Activate priority mode for a specific lane (ambulance detected)
        
        Args:
            lane: Lane direction to prioritize
            
        Returns:
            True if priority activated successfully
        """
        if self.manual_override:
            logger.warning("Cannot activate priority - manual override is active")
            return False
        
        if lane not in self.directions:
            logger.error(f"Invalid lane direction: {lane}")
            return False
        
        logger.info(f"🚨 PRIORITY MODE ACTIVATED for {lane.upper()} lane")
        
        # Immediately set priority lane to green (FAST RESPONSE - no delay)
        self.current_states[lane] = SignalState.GREEN
        
        # Set conflicting directions to red
        conflicting = self._get_conflicting_directions(lane)
        for direction in conflicting:
            self.current_states[direction] = SignalState.RED
        
        self.priority_lane = lane
        self.priority_start_time = datetime.now()
        self.in_priority_mode = True
        
        logger.info(f"✅ GREEN signal IMMEDIATELY activated for {lane} lane - Duration: {self.ambulance_green_duration}s")
        return True
    
    def deactivate_priority(self):
        """Deactivate priority mode and return to normal cycle"""
        if not self.in_priority_mode:
            return
        
        logger.info("Priority mode deactivated - returning to normal operation")
        
        # Immediately return to normal cycle (FAST TRANSITION)
        self._set_all_red()
        
        self.priority_lane = None
        self.priority_start_time = None
        self.in_priority_mode = False
        self.cycle_start_time = datetime.now()
    
    def update(self):
        """
        Update traffic signal states (call this in main loop)
        """
        # Check if manual override is active
        if self.manual_override:
            return
        
        # NOTE: Priority timeout disabled - priority now deactivates only when ambulance is no longer detected
        # This allows immediate response when ambulance appears and disappears
        # if self.in_priority_mode and self.priority_start_time:
        #     elapsed = (datetime.now() - self.priority_start_time).total_seconds()
        #     if elapsed >= self.ambulance_green_duration:
        #         logger.info("Priority duration expired")
        #         self.deactivate_priority()
        
        # Normal cycle management (if not in priority mode)
        if not self.in_priority_mode:
            self._manage_normal_cycle()
    
    def _manage_normal_cycle(self):
        """Manage normal traffic signal cycle"""
        elapsed = (datetime.now() - self.cycle_start_time).total_seconds()
        
        if elapsed >= self.default_green_duration:
            # Change to next direction
            current_dir = self.directions[self.current_cycle_direction]
            
            # Immediately change to red
            self.current_states[current_dir] = SignalState.RED
            
            # Move to next direction
            self.current_cycle_direction = (self.current_cycle_direction + 1) % len(self.directions)
            next_dir = self.directions[self.current_cycle_direction]
            
            # Green phase for next direction (IMMEDIATE SWITCH)
            self.current_states[next_dir] = SignalState.GREEN
            
            # Ensure conflicting directions are red
            conflicting = self._get_conflicting_directions(next_dir)
            for direction in conflicting:
                self.current_states[direction] = SignalState.RED
            
            self.cycle_start_time = datetime.now()
            logger.debug(f"Normal cycle: {next_dir} now GREEN")
    
    def _set_all_red(self):
        """Set all signals to red (safety measure)"""
        for direction in self.directions:
            self.current_states[direction] = SignalState.RED
        logger.debug("All signals set to RED")
    
    def _get_conflicting_directions(self, direction: str) -> list:
        """
        Get directions that conflict with the given direction
        
        Args:
            direction: Current direction
            
        Returns:
            List of conflicting directions
        """
        conflicts = {
            'north': ['south'],
            'south': ['north'],
            'east': ['west'],
            'west': ['east']
        }
        return conflicts.get(direction, [])
    
    def set_manual_override(self, enabled: bool):
        """
        Enable/disable manual override mode
        
        Args:
            enabled: True to enable manual control
        """
        if not self.manual_override_enabled:
            logger.warning("Manual override is disabled in configuration")
            return
        
        self.manual_override = enabled
        logger.info(f"Manual override: {'ENABLED' if enabled else 'DISABLED'}")
    
    def set_signal_state(self, direction: str, state: SignalState):
        """
        Manually set signal state (requires manual override)
        
        Args:
            direction: Lane direction
            state: Signal state to set
        """
        if not self.manual_override:
            logger.warning("Manual override must be enabled to set signals manually")
            return
        
        if direction not in self.directions:
            logger.error(f"Invalid direction: {direction}")
            return
        
        self.current_states[direction] = state
        logger.info(f"Manual control: {direction} set to {state.value}")
    
    def get_state(self, direction: str) -> SignalState:
        """
        Get current state of a signal
        
        Args:
            direction: Lane direction
            
        Returns:
            Current signal state
        """
        return self.current_states.get(direction, SignalState.OFF)
    
    def get_all_states(self) -> Dict[str, str]:
        """
        Get all signal states
        
        Returns:
            Dictionary of direction: state
        """
        return {direction: state.value for direction, state in self.current_states.items()}
    
    def get_status(self) -> dict:
        """
        Get complete controller status
        
        Returns:
            Status dictionary
        """
        return {
            'states': self.get_all_states(),
            'priority_mode': self.in_priority_mode,
            'priority_lane': self.priority_lane,
            'manual_override': self.manual_override,
            'timestamp': datetime.now().isoformat()
        }
