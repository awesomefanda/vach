# 🚀 Vach Quick Start Guide

Get Vach up and running in 15 minutes!

## Prerequisites Check

Before starting, make sure you have:
- [ ] Python 3.8 or higher installed
- [ ] 16GB RAM
- [ ] Internet connection
- [ ] Windows laptop 

## Step-by-Step Setup

### 1. Download Vach

Extract the Vach folder to your desired location, e.g., `C:\Users\YourName\vach`

### 2. Open Command Prompt

```cmd
cd C:\Users\YourName\vach
```

### 3. Create Virtual Environment

```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your command prompt.

### 4. Install Python Dependencies

```cmd
pip install -r requirements.txt
```

This will take 2-3 minutes. You'll see packages being installed.

### 5. Install Ollama

1. Download Ollama for Windows from: https://ollama.ai
2. Run the installer
3. Ollama will start automatically in the background

### 6. Download AI Model

```cmd
ollama pull qwen2.5-coder:7b
```

This will download ~4GB. Will take 5-10 minutes depending on your internet speed.

### 7. Setup Configuration

```cmd
copy .env.example .env
```

No need to edit `.env` for basic usage - defaults work fine!

### 8. Initialize Database

```cmd
python scripts\setup_database.py
```

You should see: ✅ Database initialized successfully!

### 9. Run Health Check (Optional but Recommended)

```cmd
python scripts\health_check.py
```

This verifies everything is working. All checks should pass ✓

## Running Vach

### First Run: Collect Data

```cmd
python scripts\run_scrapers.py
```

**What this does:**
- Visits San Jose news sites
- Collects relevant articles
- Saves to database

**Expected output:**
```
📰 News Scraper: 30 articles collected
🏛️  Government Scraper: 15 items collected
```

**Time:** 2-5 minutes

### Second Run: Extract Projects

```cmd
python scripts\run_processor.py
```

**What this does:**
- Uses AI to read articles
- Extracts project information
- Creates structured records

**Expected output:**
```
🤖 Starting LLM Processing
  Batch complete: 10 processed, 8 projects found
```

**Time:** 10-20 minutes (processing with AI is slow but thorough)

### Third Run: View Results

```cmd
streamlit run ui\streamlit_app.py
```

A browser window will open automatically showing your project tracker!

**What you'll see:**
- Dashboard with statistics
- List of tracked projects
- Project timelines
- Search and filter options

## What's Next?

### Regular Updates

Run weekly to collect new data:

```cmd
# Activate virtual environment
venv\Scripts\activate

# Collect new articles
python scripts\run_scrapers.py

# Process new articles
python scripts\run_processor.py

# View updated results
streamlit run ui\streamlit_app.py
```

### Troubleshooting

#### "Ollama not found"

Make sure Ollama is running:
```cmd
ollama serve
```

Keep this terminal open and open a new terminal for Vach commands.

#### "No articles collected"

1. Check your internet connection
2. Check logs: `type logs\scraper.log`
3. Some websites might be temporarily down - try again later

#### "Processing very slow"

This is normal! AI processing takes time:
- ~30-60 seconds per article
- 10 articles = 10 minutes
- Be patient, it's worth it!

#### "Database error"

Reinitialize:
```cmd
python scripts\setup_database.py
```

## Understanding the Output

### In the Streamlit UI:

- **Announced**: Project was just announced
- **Approved**: City council approved it
- **In Progress**: Construction/work has started
- **Delayed**: Behind schedule
- **Completed**: Project finished
- **Cancelled**: Project was cancelled

### Project Cards Show:

- **Project Name**: What it's called
- **Location**: Where in San Jose
- **Budget**: How much it costs (if disclosed)
- **Official**: Who announced it
- **Timeline**: History of updates

## Tips for Best Results

1. **Run scrapers weekly** - Catches new announcements
2. **Check different times** - Some sites update at specific times
3. **Verify important info** - AI can make mistakes, always check sources
4. **Read the logs** - Located in `logs/` folder if you want details

## Common Questions

**Q: Do I need to keep Ollama running?**  
A: Yes, but it runs in the background automatically after installation.

**Q: Does this use the internet constantly?**  
A: No, only when running scrapers. Processing is 100% local.

**Q: Can I track other cities?**  
A: Yes! Edit `.env` file and change `TARGET_CITY` and RSS feeds.

**Q: How much disk space needed?**  
A: ~5GB for Ollama + models, ~100MB for data

**Q: Is my data private?**  
A: Yes! Everything runs locally. No data sent to cloud.

## Need Help?

1. Run health check: `python scripts\health_check.py`
2. Check logs in `logs/` folder
3. Read the full README.md
4. Review error messages carefully

## Success Indicators

You'll know it's working when:
- ✅ Scrapers collect 20+ articles
- ✅ Processor finds 10+ projects
- ✅ UI shows project cards with timelines
- ✅ You can search and filter projects

Enjoy tracking San Jose's civic projects! 🎉