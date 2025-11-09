"""
Integration test script
Tests the complete system workflow
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from main import LifelineSystem
from loguru import logger


def test_system_initialization():
    """Test 1: System initialization"""
    logger.info("TEST 1: System Initialization")
    try:
        system = LifelineSystem('config/config.yaml')
        assert system.video_processor is not None
        assert system.detector is not None
        assert system.signal_controller is not None
        assert system.db is not None
        logger.info("✅ System initialization: PASSED")
        return system
    except Exception as e:
        logger.error(f"❌ System initialization: FAILED - {e}")
        return None


def test_video_processing(system):
    """Test 2: Video processing"""
    logger.info("\nTEST 2: Video Processing")
    try:
        success = system.video_processor.start()
        assert success, "Failed to start video processor"
        
        time.sleep(2)  # Wait for frames
        
        frame = system.video_processor.get_current_frame()
        assert frame is not None, "No frame received"
        
        stats = system.video_processor.get_stats()
        logger.info(f"Video stats: {stats}")
        
        system.video_processor.stop()
        logger.info("✅ Video processing: PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Video processing: FAILED - {e}")
        return False


def test_detection(system):
    """Test 3: Ambulance detection"""
    logger.info("\nTEST 3: Ambulance Detection")
    try:
        import numpy as np
        
        # Create a dummy frame
        test_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        
        detections = system.detector.detect(test_frame)
        logger.info(f"Detections: {len(detections)}")
        
        # Test drawing
        output_frame = system.detector.draw_detections(test_frame, detections)
        assert output_frame is not None
        
        logger.info("✅ Ambulance detection: PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Ambulance detection: FAILED - {e}")
        return False


def test_traffic_control(system):
    """Test 4: Traffic signal control"""
    logger.info("\nTEST 4: Traffic Signal Control")
    try:
        # Test priority activation
        success = system.signal_controller.activate_priority('north')
        assert success, "Failed to activate priority"
        
        # Check state
        state = system.signal_controller.get_state('north')
        logger.info(f"North signal state: {state}")
        
        time.sleep(2)
        
        # Deactivate priority
        system.signal_controller.deactivate_priority()
        
        logger.info("✅ Traffic signal control: PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Traffic signal control: FAILED - {e}")
        return False


def test_database(system):
    """Test 5: Database operations"""
    logger.info("\nTEST 5: Database Operations")
    try:
        # Log a test detection
        system.db.log_detection({
            'class_name': 'ambulance',
            'confidence': 0.95,
            'lane': 'north',
            'bbox': (100, 100, 200, 200),
            'center': (150, 150)
        })
        
        # Log a signal change
        system.db.log_signal_change('north', 'red', 'green', 'test', True)
        
        # Get recent detections
        detections = system.db.get_recent_detections(limit=5)
        logger.info(f"Recent detections: {len(detections)}")
        
        # Get statistics
        stats = system.db.get_statistics(days=1)
        logger.info(f"Statistics: {stats}")
        
        logger.info("✅ Database operations: PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Database operations: FAILED - {e}")
        return False


def test_full_integration(system):
    """Test 6: Full system integration"""
    logger.info("\nTEST 6: Full System Integration")
    try:
        # Start the system
        system.start()
        
        logger.info("System running... (5 seconds)")
        time.sleep(5)
        
        # Get status
        status = system.get_status()
        logger.info(f"System status: {status}")
        
        # Stop the system
        system.stop()
        
        logger.info("✅ Full integration: PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Full integration: FAILED - {e}")
        return False


def run_all_tests():
    """Run all integration tests"""
    logger.info("=" * 60)
    logger.info("LIFELINE INTEGRATION TEST SUITE")
    logger.info("=" * 60)
    
    results = []
    
    # Test 1: Initialization
    system = test_system_initialization()
    results.append(system is not None)
    
    if system is None:
        logger.error("Cannot continue tests - initialization failed")
        return
    
    # Test 2: Video Processing
    results.append(test_video_processing(system))
    
    # Test 3: Detection
    results.append(test_detection(system))
    
    # Test 4: Traffic Control
    results.append(test_traffic_control(system))
    
    # Test 5: Database
    results.append(test_database(system))
    
    # Test 6: Full Integration
    results.append(test_full_integration(system))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    passed = sum(results)
    total = len(results)
    logger.info(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED!")
    else:
        logger.warning(f"⚠️  {total - passed} test(s) failed")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    run_all_tests()
