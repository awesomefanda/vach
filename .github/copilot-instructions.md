<!-- Copilot / AI agent instructions for contributors and tools -->

# Vach — Quick AI contributor guide

Purpose: help an AI coding agent be productive quickly in this repository.

- **Big picture**: Local-only civic project tracker. Data flow: scrapers (src/scrapers/*) -> articles stored in `data/vach.db` -> LLM extraction (src/processors/llm_extractor.py) -> projects & updates in DB -> UI served from `ui/streamlit_app.py`.

- **Major components**:
  - `src/scrapers/` — concrete scrapers and `BaseScraper` (retry, rate limiting, validation). See `news_scraper.py` and `gov_scraper.py` for examples.
  - `src/processors/llm_extractor.py` — single canonical LLM workflow. The LLM must return strict JSON matching the prompt schema; the extractor cleans/parses that JSON.
  - `src/database/` — models and `DatabaseOperations` used everywhere for persistence (articles, projects, updates, scraper runs).
  - `ui/` — Streamlit app for visualization.
  - `scripts/` — orchestration scripts. Note: `scripts/run_scrapers.py` is currently empty; individual scrapers provide `main()` functions and can be executed directly.

- **Key files to inspect when changing behavior**:
  - `src/processors/llm_extractor.py` — prompt text and JSON schema (required fields, nulls). Keep changes backward-compatible.
  - `src/scrapers/base_scraper.py` — retry and rate-limit settings (uses `tenacity` and sleeps after requests).
  - `src/scrapers/news_scraper.py`, `src/scrapers/gov_scraper.py` — examples of collecting, validating and saving articles.
  - `src/database/operations.py` — DB API used by scripts and processors.
  - `config/settings.py` — environment-driven configuration (OLLAMA_MODEL, DATABASE_PATH, etc.). `.env` is loaded when present.

- **Developer workflows / commands** (run from repo root):
  - Setup: `python -m venv venv && venv\Scripts\activate` (Windows), `pip install -r requirements.txt`
  - Pull model: `ollama pull qwen2.5-coder:7b` and ensure `ollama serve` is running
  - Initialize DB: `python scripts/setup_database.py`
  - Run a single scraper (works even though orchestration script is empty): `python src/scrapers/news_scraper.py` or `python src/scrapers/gov_scraper.py`
  - Run processor (asks for confirmation): `python scripts/run_processor.py`
  - Health check: `python scripts/health_check.py`
  - UI: `streamlit run ui/streamlit_app.py`

- **Project-specific conventions / gotchas**:
  - LLM output must be strict JSON. `LLMExtractor.EXTRACTION_PROMPT` defines the exact expected keys and null semantics — do not add explanatory text around the JSON.
  - Duplicate/merge logic is intentionally conservative: `LLMExtractor` currently defers merging (adds updates to the first similar project). Avoid automated aggressive merging.
  - Scrapers rely on `BaseScraper.validate_article_data()` — keep title length and text thresholds in mind when modifying scraping logic.
  - Rate-limiting and retry behavior is centralized in `BaseScraper.fetch_url()` (uses `REQUEST_TIMEOUT`, `RETRY_ATTEMPTS`, `RATE_LIMIT_DELAY` in config).
  - Logs: `config/logging_config.py` + `logs/` directory. Use repository logger via `get_logger(__name__)`.

- **When modifying LLM prompts or model settings**:
  - Edit only `EXTRACTION_PROMPT` in `src/processors/llm_extractor.py` and update `config/settings.py` / `.env` (`OLLAMA_MODEL`, `LLM_MAX_TOKENS`, `LLM_TEMPERATURE`).
  - Keep the JSON schema unchanged unless you also update `src/database/operations.py` to persist new fields.

- **Tests & verification steps for changes**:
  - Run `python scripts/health_check.py` to validate environment (Ollama, DB, dependencies).
  - For scrapers: run the scraper module `python src/scrapers/news_scraper.py` and check `logs/scraper.log` and DB `data/vach.db` for new articles.
  - For LLM changes: run a small batch `python -c "from src.processors.llm_extractor import LLMExtractor; print(LLMExtractor().process_unprocessed_articles(limit=2))"` after ensuring Ollama is running.

If anything here is unclear or you want this file expanded with examples or a troubleshooting checklist, say what to add and I'll iterate.
