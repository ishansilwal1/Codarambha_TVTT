"""
Ambulance Detection Module
Uses YOLOv8 for real-time ambulance detection and lane identification
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class Detection:
    """Data class for ambulance detection"""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    class_name: str
    lane: Optional[str] = None
    center: Optional[Tuple[int, int]] = None
    track_id: Optional[int] = None


class AmbulanceDetector:
    """Real-time ambulance detection and tracking system"""
    
    def __init__(self, config: dict):
        """
        Initialize the ambulance detector
        
        Args:
            config: Configuration dictionary containing model settings
        """
        self.config = config
        self.model_path = config['detection']['model_path']
        self.confidence_threshold = config['detection']['confidence_threshold']
        self.device = config['detection']['device']
        self.classes_to_detect = config['detection']['classes_to_detect']
        
        # Lane configuration
        self.lane_regions = config['lanes']['lane_regions']
        self.directions = config['lanes']['directions']
        
        # Load YOLO model
        logger.info(f"Loading YOLOv8 model from {self.model_path}")
        try:
            self.model = YOLO(self.model_path)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load custom model: {e}. Using default YOLOv8n")
            self.model = YOLO('yolov8n.pt')  # Fallback to pretrained model
        
        # Detection history for tracking
        self.detection_history: Dict[int, List[Detection]] = {}
        self.track_counter = 0
        
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect ambulances in a frame
        
        Args:
            frame: Input image frame (BGR format)
            
        Returns:
            List of Detection objects
        """
        detections = []
        
        # Run YOLO inference
        results = self.model(frame, conf=self.confidence_threshold, device=self.device)
        
        # Process detections
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                # Extract bounding box coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                class_name = self.model.names[class_id]
                
                # Your trained model detects ambulances
                # Accept any detection from your custom trained model
                # Calculate center point
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                center = (center_x, center_y)
                
                # Determine which lane the ambulance is in
                lane = self._identify_lane(center)
                
                detection = Detection(
                    bbox=(x1, y1, x2, y2),
                    confidence=confidence,
                    class_name=class_name,
                    center=center,
                    lane=lane,
                    track_id=self.track_counter
                )
                
                detections.append(detection)
                self.track_counter += 1
                
                logger.debug(f"Detected {class_name} in {lane} lane with confidence {confidence:.2f}")
        
        return detections
    
    def _identify_lane(self, center: Tuple[int, int]) -> str:
        """
        Identify which lane the vehicle is in based on its center point
        
        Args:
            center: (x, y) coordinates of vehicle center
            
        Returns:
            Lane direction (north, south, east, west)
        """
        x, y = center
        
        for direction, region in self.lane_regions.items():
            x1, y1, x2, y2 = region
            if x1 <= x <= x2 and y1 <= y <= y2:
                return direction
        
        return "unknown"
    
    def draw_detections(self, frame: np.ndarray, detections: List[Detection], 
                       show_lanes: bool = True) -> np.ndarray:
        """
        Draw detection boxes and lane regions on frame
        
        Args:
            frame: Input image frame
            detections: List of detections to draw
            show_lanes: Whether to show lane regions
            
        Returns:
            Frame with drawings
        """
        output_frame = frame.copy()
        
        # Draw lane regions
        if show_lanes:
            for direction, region in self.lane_regions.items():
                x1, y1, x2, y2 = region
                color = self._get_lane_color(direction)
                cv2.rectangle(output_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(output_frame, direction.upper(), (x1 + 10, y1 + 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Draw detections
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            
            # Determine color based on confidence
            color = (0, 255, 0) if detection.confidence > 0.7 else (0, 255, 255)
            
            # Draw bounding box
            cv2.rectangle(output_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{detection.class_name}: {detection.confidence:.2f}"
            if detection.lane:
                label += f" - {detection.lane}"
            
            # Background for text
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(output_frame, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1)
            cv2.putText(output_frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Draw center point
            if detection.center:
                cv2.circle(output_frame, detection.center, 5, (0, 0, 255), -1)
        
        # Add detection count
        cv2.putText(output_frame, f"Detections: {len(detections)}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return output_frame
    
    def _get_lane_color(self, direction: str) -> Tuple[int, int, int]:
        """Get color for lane direction"""
        colors = {
            'north': (255, 0, 0),    # Blue
            'south': (0, 255, 0),    # Green
            'east': (0, 0, 255),     # Red
            'west': (255, 255, 0)    # Cyan
        }
        return colors.get(direction, (128, 128, 128))
    
    def is_ambulance_detected(self, detections: List[Detection]) -> bool:
        """
        Check if any ambulance is detected
        
        Args:
            detections: List of detections
            
        Returns:
            True if ambulance detected
        """
        return len(detections) > 0
    
    def get_priority_lane(self, detections: List[Detection]) -> Optional[str]:
        """
        Get the lane that should be prioritized
        
        Args:
            detections: List of detections
            
        Returns:
            Lane direction or None
        """
        if not detections:
            return None
        
        # Return lane of highest confidence detection
        highest_conf_detection = max(detections, key=lambda d: d.confidence)
        return highest_conf_detection.lane
