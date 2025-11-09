"""
Database Module
SQLite database for logging detections and system events
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from contextlib import contextmanager
from loguru import logger
import json


class Database:
    """SQLite database manager"""
    
    def __init__(self, db_path: str):
        """
        Initialize database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._create_tables()
        logger.info(f"Database initialized: {db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Detections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    class_name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    lane TEXT,
                    bbox_x1 INTEGER,
                    bbox_y1 INTEGER,
                    bbox_x2 INTEGER,
                    bbox_y2 INTEGER,
                    center_x INTEGER,
                    center_y INTEGER
                )
            """)
            
            # Signal changes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signal_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    direction TEXT NOT NULL,
                    old_state TEXT,
                    new_state TEXT NOT NULL,
                    reason TEXT,
                    priority_mode BOOLEAN DEFAULT 0
                )
            """)
            
            # System events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    description TEXT,
                    metadata TEXT
                )
            """)
            
            # Statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    total_detections INTEGER DEFAULT 0,
                    priority_activations INTEGER DEFAULT 0,
                    avg_response_time REAL DEFAULT 0,
                    uptime_minutes INTEGER DEFAULT 0,
                    UNIQUE(date)
                )
            """)
            
            conn.commit()
            logger.info("Database tables created/verified")
    
    def log_detection(self, detection: dict):
        """
        Log an ambulance detection
        
        Args:
            detection: Detection dictionary
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO detections 
                (class_name, confidence, lane, bbox_x1, bbox_y1, bbox_x2, bbox_y2, center_x, center_y)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                detection.get('class_name'),
                detection.get('confidence'),
                detection.get('lane'),
                detection.get('bbox', [None]*4)[0],
                detection.get('bbox', [None]*4)[1],
                detection.get('bbox', [None]*4)[2],
                detection.get('bbox', [None]*4)[3],
                detection.get('center', [None, None])[0],
                detection.get('center', [None, None])[1]
            ))
            detection_id = cursor.lastrowid
            logger.debug(f"💾 Database: Detection saved (ID: {detection_id}, Lane: {detection.get('lane')})")
    
    def log_signal_change(self, direction: str, old_state: str, new_state: str, 
                         reason: str = None, priority_mode: bool = False):
        """
        Log a traffic signal state change
        
        Args:
            direction: Lane direction
            old_state: Previous signal state
            new_state: New signal state
            reason: Reason for change
            priority_mode: Whether change was due to priority mode
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO signal_changes 
                (direction, old_state, new_state, reason, priority_mode)
                VALUES (?, ?, ?, ?, ?)
            """, (direction, old_state, new_state, reason, priority_mode))
    
    def log_system_event(self, event_type: str, description: str, metadata: dict = None):
        """
        Log a system event
        
        Args:
            event_type: Type of event
            description: Event description
            metadata: Additional metadata
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            metadata_json = json.dumps(metadata) if metadata else None
            cursor.execute("""
                INSERT INTO system_events (event_type, description, metadata)
                VALUES (?, ?, ?)
            """, (event_type, description, metadata_json))
    
    def get_recent_detections(self, limit: int = 10) -> List[Dict]:
        """
        Get recent detections
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of detection dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM detections 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_recent_signal_changes(self, limit: int = 10) -> List[Dict]:
        """
        Get recent signal changes
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of signal change dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM signal_changes 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_statistics(self, days: int = 7) -> Dict:
        """
        Get statistics for the last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            Statistics dictionary
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate timestamp threshold (e.g., 24 hours ago)
            since_timestamp = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Total detections
            cursor.execute("""
                SELECT COUNT(*) as count FROM detections 
                WHERE timestamp >= ?
            """, (since_timestamp,))
            total_detections = cursor.fetchone()['count']
            
            # Priority activations
            cursor.execute("""
                SELECT COUNT(*) as count FROM signal_changes 
                WHERE priority_mode = 1 AND timestamp >= ?
            """, (since_timestamp,))
            priority_activations = cursor.fetchone()['count']
            
            # Detections by lane
            cursor.execute("""
                SELECT lane, COUNT(*) as count FROM detections 
                WHERE timestamp >= ?
                GROUP BY lane
            """, (since_timestamp,))
            by_lane = {row['lane']: row['count'] for row in cursor.fetchall()}
            
            # Detections by hour
            cursor.execute("""
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count 
                FROM detections 
                WHERE timestamp >= ?
                GROUP BY hour
                ORDER BY hour
            """, (since_timestamp,))
            by_hour = {row['hour']: row['count'] for row in cursor.fetchall()}
            
            result = {
                'total_detections': total_detections,
                'priority_activations': priority_activations,
                'detections_by_lane': by_lane,
                'detections_by_hour': by_hour,
                'period_days': days
            }
            
            logger.debug(f"📊 Database stats: {total_detections} detections, {priority_activations} priority activations (last {days} days)")
            
            return result
    
    def cleanup_old_records(self, days: int = 90):
        """
        Delete records older than specified days
        
        Args:
            days: Records older than this will be deleted
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            cursor.execute("DELETE FROM detections WHERE DATE(timestamp) < ?", (cutoff_date,))
            deleted_detections = cursor.rowcount
            
            cursor.execute("DELETE FROM signal_changes WHERE DATE(timestamp) < ?", (cutoff_date,))
            deleted_changes = cursor.rowcount
            
            cursor.execute("DELETE FROM system_events WHERE DATE(timestamp) < ?", (cutoff_date,))
            deleted_events = cursor.rowcount
            
            logger.info(f"Cleaned up old records: {deleted_detections} detections, "
                       f"{deleted_changes} signal changes, {deleted_events} events")
