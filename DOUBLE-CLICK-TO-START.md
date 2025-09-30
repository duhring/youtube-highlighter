# 🚀 Double-Click to Start YouTube Highlighter

## Quick Start - Just Double-Click!

### 🍎 macOS Users
**Double-click:** `launch.command`
- ✅ Opens Terminal automatically
- ✅ Runs setup if needed (first time only)
- ✅ Opens browser to http://localhost:5000
- ✅ Ready to use!

### 🪟 Windows Users  
**Double-click:** `launch.bat`
- ✅ Opens Command Prompt automatically
- ✅ Runs setup if needed (first time only)
- ✅ Opens browser to http://localhost:5000
- ✅ Ready to use!

### 🐧 Linux Users
**Double-click:** `launch.desktop` (or use `launch.sh`)
- ✅ Opens Terminal automatically  
- ✅ Runs setup if needed (first time only)
- ✅ Opens browser to http://localhost:5000
- ✅ Ready to use!

## What Happens When You Double-Click?

1. **🔍 System Check** - Verifies Python 3.8+ is installed
2. **⚙️ Auto Setup** - Runs full setup on first launch (takes ~2-3 minutes)
3. **🔧 Environment** - Activates virtual environment automatically  
4. **✅ Health Check** - Ensures all components are working
5. **🌐 Browser Launch** - Opens http://localhost:5000 automatically
6. **🎉 Ready!** - Start creating video highlights!

## First Time Setup

The very first time you double-click:
- ⏱️ Takes 2-3 minutes (downloads AI models and dependencies)
- 📦 Installs all required Python packages
- ✅ Creates virtual environment
- 🔧 Configures everything automatically

**After first setup:** Double-clicking starts instantly!

## Troubleshooting

**"Python not found"**
- Install Python 3.8+ from [python.org](https://python.org)
- ✅ Check "Add Python to PATH" during installation

**"Permission denied" (macOS/Linux)**
```bash
chmod +x launch.command launch.sh launch.desktop
```

**"Setup failed"**
- Check internet connection (downloads packages)
- Ensure you have write permissions in the folder
- Try running setup manually: `./setup.sh` (macOS/Linux) or `setup.bat` (Windows)

## Alternative Launch Methods

If double-click doesn't work, try:

```bash
# Universal (works everywhere)
./launch.sh

# macOS Terminal
./launch.command

# Windows Command Prompt  
launch.bat

# Manual method
./setup.sh          # First time only
source activate.sh  # Activate environment  
python app/web/server.py
```

## Need Help?

- 📋 Run validation: `./launch.sh validate`
- 🆘 Get help: `./launch.sh help`
- 🔧 Check status: `make status`
- 📖 Full docs: See `README.md`

---

**🎯 Goal: Make YouTube Highlighter as easy as double-clicking an app!** ✨