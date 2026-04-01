# Parc Gateway Scripts

Scripts for updating the Parc at Gateway community board.

## Setup Instructions

This project uses `uv` for dependency management. To set up the project on a new computer, follow these steps:

1. **Install uv:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Sync the project dependencies:**
   ```bash
   uv sync
   ```

3. **Install Playwright Browsers:**
   Because this project uses Playwright to scrape content securely, you must install the required Chromium browser binaries.
   ```bash
   uv run playwright install chromium
   ```

## Running the Scripts

To update all data (events, movies, and real estate), run the main script:
```bash
uv run scrape_all.py
```
