# QUICKSTART.md

## 🚀 Get Started in 5 Minutes

### Option 1: Quick Start (Recommended)

1. **Run the startup script**:
   ```powershell
   .\start.ps1
   ```

2. **Access the dashboard**:
   - Open browser: `http://localhost:8000`

That's it! The system will:
- Create virtual environment
- Install dependencies
- Start the system
- Open video feed from your webcam

### Option 2: Manual Setup

1. **Create virtual environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Run the system**:
   ```powershell
   python main.py
   ```

4. **Open dashboard**:
   - Browser: `http://localhost:8000`

## 🎯 First-Time Setup

### Prerequisites
- ✅ Python 3.8+ installed
- ✅ Webcam or video file
- ✅ 8GB RAM minimum

### Verify Installation
```powershell
python --version  # Should be 3.8+
pip --version     # Should show pip version
```

## 📹 Test with Video File

Don't have a camera? Test with a video:

```powershell
python main.py --mode simulation --video path\to\video.mp4
```

**Download sample videos**:
- Traffic videos from YouTube (search "traffic camera footage")
- Place in `data/test_videos/` folder

## 🎮 Dashboard Controls

| Feature | Action |
|---------|--------|
| View Live Feed | Automatically shown |
| Start System | Click "▶️ Start System" |
| Stop System | Click "⏸️ Stop System" |
| Manual Control | Click "Manual Override" |
| Emergency Stop | Click "🛑 EMERGENCY STOP" |

## 🔧 Common Issues

### "Camera not found"
**Solution**: 
```powershell
# Try different camera index
python main.py --camera 1

# Or use a video file
python main.py --video data\test_videos\sample.mp4
```

### "Module not found"
**Solution**:
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Reinstall
pip install -r requirements.txt
```

### "Port already in use"
**Solution**: Edit `config/config.yaml` and change port to 8080

### Slow performance
**Solution**: Use GPU acceleration
```powershell
# Install CUDA version
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## 📚 Next Steps

1. **Read the User Guide**: `docs/USER_GUIDE.md`
2. **Configure Settings**: Edit `config/config.yaml`
3. **Train Custom Model**: See `docs/TRAINING.md`
4. **API Integration**: Check `docs/API_DOCUMENTATION.md`

## 🎓 How It Works

```
Camera → Detection (YOLOv8) → Lane Analysis → Signal Control → Dashboard
   ↓                                                              ↑
   └──────────────── Database Logging ─────────────────────────┘
```

1. **Camera captures** traffic video
2. **AI detects** ambulances in real-time
3. **System determines** which lane
4. **Traffic lights** automatically adjust
5. **Dashboard shows** everything live

## 💡 Quick Demo

Want to see it work immediately?

1. Start system: `python main.py`
2. Open dashboard: `http://localhost:8000`
3. The system will detect vehicles (uses general YOLO model)
4. Click "Manual Override" to test signal controls

## 🔥 Tips

- **GPU**: 10x faster detection with NVIDIA GPU
- **Resolution**: 720p is sweet spot (speed vs accuracy)
- **Confidence**: Adjust in config (0.6 = balanced)
- **Recording**: Click "Record" to save sessions

## 📞 Need Help?

- **Logs**: Check `data/logs/system.log`
- **Test**: Run `python scripts/integration_test.py`
- **Issues**: See `docs/INSTALLATION.md` for detailed troubleshooting

## 🎯 Project Goals

This system demonstrates:
- ✅ Real-time computer vision
- ✅ Automated traffic control
- ✅ Web-based monitoring
- ✅ Database logging
- ✅ API integration

Perfect for:
- 🏆 Hackathons
- 📚 Academic projects  
- 🚀 Smart city prototypes
- 🔬 Research demonstrations

---

**Ready to save lives with AI? Let's go! 🚑**

```powershell
.\start.ps1
```
