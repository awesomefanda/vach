# 🔍 Vach - San Jose Project Tracker

Automated civic accountability tracker that monitors government projects and promises in San Jose, California.

## Features

- 🤖 **Automated Collection**: Scrapes news and government websites
- 🧠 **AI-Powered Extraction**: Uses local LLM to extract structured project data
- 📊 **Project Tracking**: Monitors status changes over time
- 🔍 **Searchable Database**: Easy-to-use web interface
- 🏠 **100% Local**: Runs entirely on your machine, no cloud APIs needed

## Prerequisites

- **Python 3.8+**
- **16GB RAM** (for running local LLM)
- **Ollama** (for local LLM inference)
- **Windows/Mac/Linux**

## Installation

### 1. Clone or Download

```bash
# If using git
git clone https://github.com/yourusername/vach.git
cd vach

# Or download and extract the ZIP file
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ollama

Download and install Ollama from https://ollama.ai

Then pull the required model:

```bash
ollama pull qwen2.5-coder:7b
```

**Keep Ollama running in the background** (it should auto-start, or run `ollama serve`)

### 5. Configure Settings

Copy `.env.example` to `.env`:

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Edit `.env` if you want to customize settings (optional for basic usage).

### 6. Initialize Database

```bash
python scripts/setup_database.py
```

You should see: ✅ Database initialized successfully!

## Usage

### Step 1: Collect Data

Run the scrapers to collect articles:

```bash
python scripts/run_scrapers.py
```

This will:
- Scrape local news sources
- Scrape government websites
- Save articles to database

**Expected time**: 2-5 minutes
**Expected output**: 20-100 articles collected

### Step 2: Process Articles

Extract project data using AI:

```bash
python scripts/run_processor.py
```

This will:
- Use local LLM to extract project information
- Create structured project records
- Track project timelines

**Expected time**: 5-15 minutes (depending on article count)
**Expected output**: 10-50 projects extracted

### Step 3: View Results

Launch the web interface:

```bash
streamlit run ui/streamlit_app.py
```

This will open a browser window with the project tracker interface.

## Project Structure

```
vach/
├── config/             # Configuration and logging
├── data/              # Database and data files
├── logs/              # Application logs
├── scripts/           # Main execution scripts
├── src/
│   ├── database/      # Database models and operations
│   ├── processors/    # LLM extraction logic
│   ├── scrapers/      # Web scraping modules
│   └── utils/         # Utility functions
├── ui/                # Streamlit web interface
└── requirements.txt   # Python dependencies
```

## Troubleshooting

### Ollama Not Running

**Error**: `Failed to connect to Ollama`

**Solution**: 
```bash
# Start Ollama
ollama serve

# Then run your script again
```

### No Articles Collected

**Error**: Scrapers collect 0 articles

**Possible causes**:
1. Websites may have changed structure
2. Network issues
3. RSS feeds not responding

**Solution**:
- Check logs in `logs/scraper.log`
- Verify RSS feeds in `.env` are accessible
- Check your internet connection

### LLM Extraction Slow

If processing is taking too long:

1. Process in smaller batches (edit script to use limit=5)
2. Use smaller model: `ollama pull llama3.2:3b`
3. Update `.env`: `OLLAMA_MODEL=llama3.2:3b`

### Database Errors

**Error**: `Database locked` or `no such table`

**Solution**:
```bash
# Reinitialize database
python scripts/setup_database.py
```

## Data Sources

- **San Jose Mercury News** (RSS)
- **San Jose Spotlight** (RSS)
- **San Jose Official Press Releases**
- **San Jose Open Data Portal**

## Limitations

This is a prototype system:

- ⚠️ AI extraction may have errors
- ⚠️ Website structure changes can break scrapers
- ⚠️ Requires manual verification of important information
- ⚠️ Running locally only (no cloud sync)

## Maintenance

### Running Regularly

For best results, run collection weekly:

```bash
# Collect new data
python scripts/run_scrapers.py

# Process new articles
python scripts/run_processor.py
```

### Viewing Logs

Logs are stored in the `logs/` directory:

- `scraper.log` - Scraping activity
- `processor.log` - LLM processing
- `app.log` - General application logs

### Backing Up Data

Your database is stored in `data/vach.db`. To backup:

```bash
# Windows
copy data\vach.db data\vach_backup.db

# Mac/Linux
cp data/vach.db data/vach_backup.db
```

## Roadmap

Future enhancements:
- [ ] Email notifications for project updates
- [ ] Export to CSV/PDF
- [ ] Sentiment analysis
- [ ] Comparison with historical promises
- [ ] Multi-city support

## Contributing

This is a prototype. Contributions welcome!

## License

MIT License

## Disclaimer

This tool is for informational purposes only. Always verify important information with official government sources. The creators are not responsible for any decisions made based on this data.

## Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Review this README
3. Create an issue on GitHub

---

**Built with**: Python, Ollama, Streamlit, SQLAlchemy, BeautifulSoup

**Inspired by**: MIT Media Lab's Promise Tracker (2014-2017)