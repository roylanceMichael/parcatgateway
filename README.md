# Parc Gateway Community Board

This is the public website for the Parc at Gateway HOA.

## Setup Instructions

The scraping scripts are located in the `scraper` directory and use `uv` for dependency management. To set up the project on a new computer, follow these steps:

1. **Install uv:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Sync the project dependencies:**
   ```bash
   uv sync --project scraper
   ```

3. **Install Playwright Browsers:**
   Because this project uses Playwright to scrape content securely, you must install the required Chromium browser binaries.
   ```bash
   uv run --project scraper playwright install chromium
   ```

## Running the Scripts

To update all data (events, movies, and real estate) in the root directory, run the main script from the repository root:
```bash
uv run --project scraper scraper/scrape_all.py
```

