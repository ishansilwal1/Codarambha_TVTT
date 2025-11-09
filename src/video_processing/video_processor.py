"""
Video Processing Module
Handles video stream capture and frame processing
"""

import cv2
import numpy as np
from typing import Optional, Callable
from threading import Thread, Lock
from queue import Queue
import time
from loguru import logger


class VideoProcessor:
    """Real-time video stream processor with threading"""
    
    def __init__(self, config: dict):
        """
        Initialize video processor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.source = config['camera']['source']
        self.width = config['camera']['width']
        self.height = config['camera']['height']
        self.fps = config['camera']['fps']
        self.buffer_size = config['camera']['buffer_size']
        
        # Video capture
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.is_paused = False
        
        # Threading
        self.capture_thread: Optional[Thread] = None
        self.frame_queue = Queue(maxsize=self.buffer_size)
        self.lock = Lock()
        
        # Current frame
        self.current_frame: Optional[np.ndarray] = None
        self.frame_count = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.actual_fps = 0
        
        # Statistics
        self.dropped_frames = 0
        
    def start(self) -> bool:
        """
        Start video capture
        
        Returns:
            True if started successfully
        """
        try:
            logger.info(f"Starting video capture from source: {self.source}")
            self.cap = cv2.VideoCapture(self.source)
            
            if not self.cap.isOpened():
                logger.error("Failed to open video source")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
            
            # Get actual properties
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            logger.info(f"Video capture started: {actual_width}x{actual_height} @ {actual_fps} FPS")
            
            self.is_running = True
            self.capture_thread = Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting video capture: {e}")
            return False
    
    def stop(self):
        """Stop video capture"""
        logger.info("Stopping video capture")
        self.is_running = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=5)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        logger.info("Video capture stopped")
    
    def _capture_loop(self):
        """Internal capture loop (runs in separate thread)"""
        while self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue
            
            try:
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.warning("Failed to read frame")
                    if self._is_video_file():
                        # Loop video if it's a file
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                # Update current frame
                with self.lock:
                    self.current_frame = frame
                    self.frame_count += 1
                
                # Try to add to queue (non-blocking)
                if not self.frame_queue.full():
                    self.frame_queue.put(frame)
                else:
                    self.dropped_frames += 1
                
                # Calculate FPS
                self.fps_counter += 1
                if time.time() - self.fps_start_time >= 1.0:
                    self.actual_fps = self.fps_counter
                    self.fps_counter = 0
                    self.fps_start_time = time.time()
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(0.1)
    
    def read(self) -> Optional[np.ndarray]:
        """
        Read the next frame from the queue
        
        Returns:
            Frame or None if no frame available
        """
        if not self.frame_queue.empty():
            return self.frame_queue.get()
        return None
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        Get the most recent frame (non-blocking)
        
        Returns:
            Current frame or None
        """
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None
    
    def pause(self):
        """Pause video capture"""
        self.is_paused = True
        logger.info("Video capture paused")
    
    def resume(self):
        """Resume video capture"""
        self.is_paused = False
        logger.info("Video capture resumed")
    
    def is_opened(self) -> bool:
        """
        Check if video source is opened
        
        Returns:
            True if opened
        """
        return self.cap is not None and self.cap.isOpened()
    
    def _is_video_file(self) -> bool:
        """Check if source is a video file"""
        return isinstance(self.source, str) and not self.source.startswith('rtsp')
    
    def get_stats(self) -> dict:
        """
        Get video processing statistics
        
        Returns:
            Statistics dictionary
        """
        return {
            'frame_count': self.frame_count,
            'actual_fps': self.actual_fps,
            'dropped_frames': self.dropped_frames,
            'queue_size': self.frame_queue.qsize(),
            'is_running': self.is_running,
            'is_paused': self.is_paused
        }
    
    def apply_preprocessing(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply preprocessing to frame
        
        Args:
            frame: Input frame
            
        Returns:
            Preprocessed frame
        """
        # Add any preprocessing here (e.g., denoising, contrast adjustment)
        # For now, just return the frame as-is
        return frame
    
    def resize_frame(self, frame: np.ndarray, width: int, height: int) -> np.ndarray:
        """
        Resize frame to specified dimensions
        
        Args:
            frame: Input frame
            width: Target width
            height: Target height
            
        Returns:
            Resized frame
        """
        return cv2.resize(frame, (width, height))


class VideoWriter:
    """Video writer for recording processed streams"""
    
    def __init__(self, output_path: str, fps: int, width: int, height: int):
        """
        Initialize video writer
        
        Args:
            output_path: Output video file path
            fps: Frames per second
            width: Frame width
            height: Frame height
        """
        self.output_path = output_path
        self.fps = fps
        self.width = width
        self.height = height
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        logger.info(f"Video writer initialized: {output_path}")
    
    def write(self, frame: np.ndarray):
        """
        Write frame to video
        
        Args:
            frame: Frame to write
        """
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))
        
        self.writer.write(frame)
    
    def release(self):
        """Release video writer"""
        self.writer.release()
        logger.info(f"Video saved to: {self.output_path}")
