"""
Training script for custom ambulance detection model
"""

from ultralytics import YOLO
import yaml
from pathlib import Path
from loguru import logger


def train_ambulance_detector(
    data_yaml: str = 'data/ambulance_dataset.yaml',
    epochs: int = 100,
    img_size: int = 640,
    batch_size: int = 16,
    model: str = 'yolov8n.pt'
):
    """
    Train YOLOv8 model for ambulance detection
    
    Args:
        data_yaml: Path to dataset configuration
        epochs: Number of training epochs
        img_size: Image size for training
        batch_size: Batch size
        model: Base model to start from
    """
    logger.info("Starting ambulance detector training")
    logger.info(f"Base model: {model}")
    logger.info(f"Epochs: {epochs}, Batch size: {batch_size}")
    
    # Load YOLO model
    model = YOLO(model)
    
    # Train the model
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=img_size,
        batch=batch_size,
        name='ambulance_detector',
        patience=50,
        save=True,
        device='0',  # Use GPU 0, or 'cpu' for CPU training
        workers=8,
        verbose=True
    )
    
    logger.info("Training completed!")
    logger.info(f"Best model saved to: runs/detect/ambulance_detector/weights/best.pt")
    
    # Validate the model
    metrics = model.val()
    logger.info(f"Validation metrics: {metrics}")
    
    return results


def create_dataset_config():
    """Create a template dataset configuration file"""
    config = {
        'path': '../data/ambulance_dataset',
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        'names': {
            0: 'ambulance',
            1: 'emergency_vehicle'
        },
        'nc': 2  # number of classes
    }
    
    output_path = Path('data/ambulance_dataset.yaml')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    logger.info(f"Dataset config template created at: {output_path}")
    logger.info("Please organize your dataset according to this structure:")
    logger.info("  data/ambulance_dataset/")
    logger.info("    ├── images/")
    logger.info("    │   ├── train/")
    logger.info("    │   ├── val/")
    logger.info("    │   └── test/")
    logger.info("    └── labels/")
    logger.info("        ├── train/")
    logger.info("        ├── val/")
    logger.info("        └── test/")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train ambulance detection model')
    parser.add_argument('--data', default='data/ambulance_dataset.yaml', help='Dataset config')
    parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    parser.add_argument('--batch', type=int, default=16, help='Batch size')
    parser.add_argument('--img-size', type=int, default=640, help='Image size')
    parser.add_argument('--create-config', action='store_true', help='Create dataset config template')
    
    args = parser.parse_args()
    
    if args.create_config:
        create_dataset_config()
    else:
        train_ambulance_detector(
            data_yaml=args.data,
            epochs=args.epochs,
            img_size=args.img_size,
            batch_size=args.batch
        )
