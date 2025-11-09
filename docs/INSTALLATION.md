# Installation Guide

## Prerequisites

### Required Software
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Optional (for better performance)
- CUDA-capable GPU with CUDA 11.0+
- cuDNN 8.0+

## Step-by-Step Installation

### 1. Clone or Download the Repository

```bash
cd c:\Users\Acer\Desktop\Bachelors\Hackathon\Lifeline
```

### 2. Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

**Note**: Installing PyTorch with CUDA support:
```powershell
# For CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# For CPU only
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### 4. Verify Installation

```powershell
python -c "import cv2; import torch; print('OpenCV:', cv2.__version__); print('PyTorch:', torch.__version__)"
```

### 5. Download Pre-trained Model (Optional)

The system will automatically download YOLOv8n on first run. To pre-download:

```powershell
python -c "from ultralytics import YOLO; model = YOLO('yolov8n.pt')"
```

### 6. Test the Installation

```powershell
python scripts/integration_test.py
```

## Troubleshooting

### Issue: Cannot import cv2
**Solution**: 
```powershell
pip uninstall opencv-python opencv-python-headless
pip install opencv-python==4.8.1.78
```

### Issue: CUDA out of memory
**Solution**: Reduce batch size in config or use CPU mode:
- Edit `config/config.yaml`
- Change `device: "cuda"` to `device: "cpu"`

### Issue: Camera not detected
**Solution**: 
- Check camera permissions
- Try different camera indices (0, 1, 2...)
- Use a test video: `python main.py --video path/to/video.mp4`

### Issue: Port 8000 already in use
**Solution**:
- Change port in `config/config.yaml` under `api: port:`
- Or kill the process using the port

### Issue: Module not found errors
**Solution**:
```powershell
# Ensure you're in the virtual environment
.\venv\Scripts\Activate.ps1

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

## Next Steps

After successful installation:

1. Configure the system: Edit `config/config.yaml`
2. Connect your camera or prepare test videos
3. Run the system: `python main.py`
4. Access dashboard: Open browser to `http://localhost:8000`

## Hardware Requirements

### Minimum
- CPU: Intel Core i5 or equivalent
- RAM: 8 GB
- Storage: 5 GB free space
- Camera: 720p webcam or IP camera

### Recommended
- CPU: Intel Core i7 or AMD Ryzen 7
- GPU: NVIDIA GTX 1060 or better (6GB VRAM)
- RAM: 16 GB
- Storage: 20 GB free space (SSD preferred)
- Camera: 1080p camera with good low-light performance

## Support

If you encounter issues not covered here:
1. Check the log files in `data/logs/`
2. Run with debug mode: Edit config.yaml and set `debug: true`
3. Open an issue on the repository
