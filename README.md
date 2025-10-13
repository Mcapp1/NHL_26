# NHL 26 Club Analytics Pipeline

Automated stats scraping and analytics dashboard for EA Sports NHL 26 Pro Clubs.

## Features
- Scrapes game stats from ChelStats API
- Captures shot location heatmap data from EA's Pro Clubs API
- Calculates advanced metrics (WAR, Total Offense/Defense, Efficiency)
- Interactive Streamlit dashboard with visualizations

## Setup
1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Update `config/config.py` with your club info
4. Run pipeline: `python pipeline/orchestrator.py`
5. Launch dashboard: `streamlit run dashboard.py`

## Project Structure
- `scrapers/` - Data collection scripts
- `pipeline/` - Data processing and orchestration
- `utils/` - Helper functions
- `dashboard.py` - Streamlit analytics dashboard
- `config/` - Configuration settings