"""
Main Application Entry Point
Orchestrates all system components
"""

import cv2
import sys
import signal
import threading
import time
from pathlib import Path
from datetime import datetime
from loguru import logger
import uvicorn
from typing import Optional

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.utils import load_config, ensure_directories
from src.detection import AmbulanceDetector
from src.traffic_control import TrafficSignalController
from src.video_processing import VideoProcessor
from src.utils.database import Database
from src.api import app, set_system_manager


class LifelineSystem:
    """Main system manager"""
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        """
        Initialize the Lifeline system
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        logger.info("Loading configuration...")
        self.config = load_config(config_path)
        
        # Setup logging
        self._setup_logging()
        
        # Ensure required directories exist
        ensure_directories([
            'data',
            'data/logs',
            'data/test_videos',
            'models'
        ])
        
        # Initialize components
        logger.info("Initializing system components...")
        self.video_processor = VideoProcessor(self.config)
        self.detector = AmbulanceDetector(self.config)
        self.signal_controller = TrafficSignalController(self.config)
        self.db = Database(self.config['database']['path'])
        
        # System state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.detection_count = 0
        self.priority_count = 0
        self.current_detections = []
        self.display_frame = None
        
        # Threading
        self.processing_thread: Optional[threading.Thread] = None
        
        logger.info("✅ Lifeline system initialized successfully")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config['logging']
        
        # Remove default logger
        logger.remove()
        
        # Add console logger
        logger.add(
            sys.stdout,
            level=log_config['level'],
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
        )
        
        # Add file logger if enabled
        if log_config['log_to_file']:
            logger.add(
                log_config['log_file'],
                rotation=log_config['log_rotation'],
                retention=log_config['log_retention'],
                level=log_config['level']
            )
    
    def start(self):
        """Start the system"""
        if self.is_running:
            logger.warning("System is already running")
            return
        
        logger.info("🚀 Starting Lifeline system...")
        
        # Start video processor
        if not self.video_processor.start():
            logger.error("Failed to start video processor")
            return
        
        # Start processing thread
        self.is_running = True
        self.start_time = datetime.now()
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        # Log system start
        self.db.log_system_event('system_start', 'Lifeline system started')
        
        logger.info("✅ System started successfully")
    
    def stop(self):
        """Stop the system"""
        if not self.is_running:
            logger.warning("System is not running")
            return
        
        logger.info("Stopping Lifeline system...")
        
        self.is_running = False
        
        # Wait for processing thread to finish
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        
        # Stop video processor
        self.video_processor.stop()
        
        # Deactivate priority if active
        if self.signal_controller.in_priority_mode:
            self.signal_controller.deactivate_priority()
        
        # Log system stop
        self.db.log_system_event('system_stop', 'Lifeline system stopped')
        
        logger.info("✅ System stopped successfully")
    
    def _processing_loop(self):
        """Main processing loop (runs in separate thread)"""
        logger.info("Processing loop started")
        
        while self.is_running:
            try:
                # Get frame from video processor
                frame = self.video_processor.read()
                
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                # Run detection
                detections = self.detector.detect(frame)
                self.current_detections = detections
                
                # Process detections
                if detections:
                    self.detection_count += len(detections)
                    
                    # Log detections to database
                    for detection in detections:
                        self.db.log_detection({
                            'class_name': detection.class_name,
                            'confidence': detection.confidence,
                            'lane': detection.lane,
                            'bbox': detection.bbox,
                            'center': detection.center
                        })
                    
                    # Get priority lane
                    priority_lane = self.detector.get_priority_lane(detections)
                    
                    if priority_lane and not self.signal_controller.in_priority_mode:
                        logger.info(f"🚨 Ambulance detected in {priority_lane} lane!")
                        self.signal_controller.activate_priority(priority_lane)
                        self.priority_count += 1
                
                # Update signal controller
                self.signal_controller.update()
                
                # Draw detections on frame
                display_frame = self.detector.draw_detections(
                    frame,
                    detections,
                    show_lanes=self.config['dashboard']['show_lane_regions']
                )
                
                # Add system info overlay
                display_frame = self._add_overlay(display_frame)
                
                self.display_frame = display_frame
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(0.1)
        
        logger.info("Processing loop ended")
    
    def _add_overlay(self, frame):
        """Add system information overlay to frame"""
        # System status
        status_text = "PRIORITY MODE" if self.signal_controller.in_priority_mode else "NORMAL MODE"
        status_color = (0, 0, 255) if self.signal_controller.in_priority_mode else (0, 255, 0)
        
        cv2.putText(frame, status_text, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, frame.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def get_display_frame(self):
        """Get current display frame"""
        return self.display_frame
    
    def get_status(self) -> dict:
        """Get system status"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            'status': 'running' if self.is_running else 'stopped',
            'uptime': uptime,
            'detections_count': self.detection_count,
            'priority_activations': self.priority_count,
            'priority_mode': self.signal_controller.in_priority_mode,
            'priority_lane': self.signal_controller.priority_lane,
            'states': self.signal_controller.get_all_states(),
            'video_stats': self.video_processor.get_stats(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_statistics(self) -> dict:
        """Get system statistics"""
        return self.db.get_statistics(days=7)
    
    def get_recent_logs(self, limit: int = 50) -> list:
        """Get recent system logs"""
        # This would read from log file if needed
        return []


def signal_handler(signum, frame):
    """Handle system signals"""
    logger.info("Received shutdown signal")
    if 'system' in globals():
        system.stop()
    sys.exit(0)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Lifeline Traffic Management System')
    parser.add_argument('--config', default='config/config.yaml', help='Path to config file')
    parser.add_argument('--camera', help='Camera source (overrides config)')
    parser.add_argument('--mode', choices=['production', 'simulation', 'testing'], 
                       default='production', help='System mode')
    parser.add_argument('--video', help='Video file for simulation mode')
    parser.add_argument('--no-api', action='store_true', help='Disable API server')
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create system
    global system
    system = LifelineSystem(args.config)
    
    # Override config if command line args provided
    if args.camera:
        system.config['camera']['source'] = args.camera
    if args.video:
        system.config['camera']['source'] = args.video
    if args.mode:
        system.config['system']['mode'] = args.mode
    
    # Set system manager for API
    set_system_manager(system)
    
    # Start system
    system.start()
    
    logger.info("=" * 60)
    logger.info("🚑 LIFELINE - Intelligent Traffic Management System")
    logger.info("=" * 60)
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Camera: {system.config['camera']['source']}")
    logger.info(f"Dashboard: http://localhost:{system.config['api']['port']}")
    logger.info("=" * 60)
    
    if not args.no_api:
        # Run API server (this blocks)
        logger.info("Starting API server...")
        uvicorn.run(
            app,
            host=system.config['api']['host'],
            port=system.config['api']['port'],
            log_level="info"
        )
    else:
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    
    # Cleanup
    system.stop()
    logger.info("👋 Lifeline system shutdown complete")


if __name__ == "__main__":
    main()
