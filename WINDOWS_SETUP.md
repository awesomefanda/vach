# 🪟 Vach - Windows Setup Guide

Complete setup guide for Windows 10/11 with 16GB RAM.

## Prerequisites Installation

### 1. Install Python

1. Go to https://www.python.org/downloads/
2. Download Python 3.11 (or latest 3.x)
3. **IMPORTANT**: Check "Add Python to PATH" during installation
4. Click "Install Now"

Verify installation:
```cmd
python --version
```

Should show: `Python 3.11.x` or similar

### 2. Install Ollama

1. Go to https://ollama.ai/download/windows
2. Download OllamaSetup.exe
3. Run the installer
4. Ollama will start automatically

Verify installation:
```cmd
ollama --version
```

### 3. Install Git (Optional)

Only needed if you want to clone from GitHub.

1. Go to https://git-scm.com/download/win
2. Download and install
3. Use default settings

## Vach Installation

### Method 1: Download ZIP (Easiest)

1. Download Vach project as ZIP
2. Extract to `C:\Users\YourName\Documents\vach`
3. Remember this location!

### Method 2: Git Clone

```cmd
cd C:\Users\YourName\Documents
git clone https://github.com/yourusername/vach.git
cd vach
```

## Setup Process

### Step 1: Open Command Prompt as Administrator

1. Press `Win + X`
2. Click "Command Prompt (Admin)" or "PowerShell (Admin)"
3. Navigate to vach folder:

```cmd
cd C:\Users\YourName\Documents\vach
```

### Step 2: Create Virtual Environment

```cmd
python -m venv venv
```

Wait for it to complete (30 seconds).

### Step 3: Activate Virtual Environment

```cmd
venv\Scripts\activate
```

Your prompt should now show `(venv)`.

**Important**: You'll need to run this every time you open a new Command Prompt!

### Step 4: Upgrade pip

```cmd
python -m pip install --upgrade pip
```

### Step 5: Install Dependencies

```cmd
pip install -r requirements.txt
```

This takes 3-5 minutes. You'll see many packages installing.


### Step 6: Download AI Model

```cmd
ollama pull qwen2.5-coder:7b
```

This downloads ~4.2GB. Takes 5-15 minutes depending on internet speed.

**Progress bar will show**:
```
pulling manifest
pulling 8934d96d3f08... 100%
```

### Step 7: Setup Configuration

```cmd
copy .env.example .env
```

Open `.env` in Notepad if you want to customize (optional):
```cmd
notepad .env
```

### Step 8: Initialize Database

```cmd
python scripts\setup_database.py
```

You should see:
```
✅ Database initialized successfully!
```

### Step 9: Health Check

```cmd
python scripts\health_check.py
```

All checks should pass ✓. If any fail, follow the error messages.

## Running Vach

### Start Ollama (if not running)

Ollama should start automatically on boot. If it's not running:

```cmd
ollama serve
```

Keep this terminal open and open a new one for Vach commands.

### Activate Virtual Environment

Every time you open a new terminal:

```cmd
cd C:\Users\YourName\Documents\vach
venv\Scripts\activate
```

### Run Scrapers

```cmd
python scripts\run_scrapers.py
```

Expected output:
```
📰 Running News Scraper...
✓ News Scraper: 30 articles collected
```

### Run Processor

```cmd
python scripts\run_processor.py
```

You'll be asked to confirm. Press `y` and Enter.

**This is slow** - about 30-60 seconds per article. Be patient!

### View Results

```cmd
streamlit run ui\streamlit_app.py
```

Browser opens automatically at http://localhost:8501

## Creating Desktop Shortcuts (Optional)

### Shortcut 1: Activate Environment

1. Right-click Desktop > New > Shortcut
2. Location: `cmd.exe /k "cd C:\Users\YourName\Documents\vach && venv\Scripts\activate"`
3. Name: "Vach Terminal"

### Shortcut 2: Run Vach UI

1. Create file `run_vach.bat` in vach folder:
```batch
@echo off
cd /d %~dp0
call venv\Scripts\activate
streamlit run ui\streamlit_app.py
pause
```

2. Right-click > Send to > Desktop (create shortcut)

## Troubleshooting

### Python not found

**Error**: `'python' is not recognized`

**Solution**:
1. Reinstall Python with "Add to PATH" checked
2. Or add manually:
   - Search "Environment Variables" in Windows
   - Add `C:\Users\YourName\AppData\Local\Programs\Python\Python311` to PATH

### Virtual environment activation fails

**Error**: `cannot be loaded because running scripts is disabled`

**Solution** (PowerShell only):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again.

### Ollama connection failed

**Solution**:
1. Check if Ollama is running:
   - Look for Ollama icon in system tray (bottom right)
   - Or run `ollama serve` in a terminal

2. Restart Ollama:
   - Close from system tray
   - Search "Ollama" in Start menu
   - Run it again

### Port 8501 already in use

**Error when running Streamlit**

**Solution**:
```cmd
streamlit run ui\streamlit_app.py --server.port 8502
```

### Out of memory errors


1. Close other applications
2. Use smaller model:
```cmd
ollama pull llama3.2:3b
```

3. Edit `.env`:
```
OLLAMA_MODEL=llama3.2:3b
```

### Scrapers collect 0 articles

**Possible causes**:
1. Internet connection issue
2. Websites temporarily down
3. RSS feeds changed

**Solution**:
1. Check internet: `ping google.com`
2. Try again later
3. Check logs: `type logs\scraper.log`

## Performance Tips

### Speed Up Processing

1. **Process fewer articles**:
   Edit `scripts\run_processor.py`, change:
   ```python
   limit=10  # Instead of 20
   ```

2. **Use smaller model**:
   ```cmd
   ollama pull llama3.2:3b
   ```
   Update `.env`: `OLLAMA_MODEL=llama3.2:3b`

### Reduce RAM Usage

1. Close browser tabs
2. Close unnecessary applications
3. Use Task Manager to monitor RAM usage

## Scheduled Runs (Advanced)

### Using Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Vach Weekly Scraper"
4. Trigger: Weekly, Monday 8:00 AM
5. Action: Start a program
6. Program: `C:\Users\YourName\Documents\vach\venv\Scripts\python.exe`
7. Arguments: `scripts\run_scrapers.py`
8. Start in: `C:\Users\YourName\Documents\vach`

Repeat for processor with 1-hour delay.

## Maintenance

### Update Vach

```cmd
cd C:\Users\YourName\Documents\vach
venv\Scripts\activate
git pull  # If using git
pip install -r requirements.txt --upgrade
```

### Backup Data

```cmd
xcopy data\vach.db data\backup\vach_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db*
```

### Clear Old Logs

```cmd
del /F logs\*.log
```

### Reset Everything

```cmd
rmdir /S /Q venv
rmdir /S /Q data
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scripts\setup_database.py
```

## Uninstallation

1. Delete vach folder: `rmdir /S /Q C:\Users\YourName\Documents\vach`
2. Uninstall Ollama from Control Panel
3. Delete Ollama data: `rmdir /S /Q %USERPROFILE%\.ollama`

## Getting Help

1. Run health check: `python scripts\health_check.py`
2. Check logs in `logs\` folder
3. Review error messages carefully
4. Check README.md for detailed documentation

## Quick Command Reference

```cmd
# Start everything
cd C:\Users\YourName\Documents\vach
venv\Scripts\activate

# Collect data
python scripts\run_scrapers.py

# Process data
python scripts\run_processor.py

# View results
streamlit run ui\streamlit_app.py

# Check health
python scripts\health_check.py
```

---

**Need more help?** Check the main README.md or QUICKSTART.md files!