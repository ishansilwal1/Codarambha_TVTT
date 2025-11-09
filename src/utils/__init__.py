"""
Utility functions and helpers
"""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def ensure_directories(paths: list):
    """
    Ensure directories exist, create if they don't
    
    Args:
        paths: List of directory paths
    """
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)
