# scrapers/ea_proclubs_scraper.py
import asyncio
from playwright.async_api import async_playwright
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.helpers import setup_logging
from config.config import CLUB_ID, CONSOLE

logger = setup_logging(__name__)

USER_DATA_DIR = "ea_profile"

async def capture_proclubs_api_data():
    """Navigate directly to API URL and extract JSON"""
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()

        # Go directly to the API endpoint
        api_url = f"https://proclubs.ea.com/api/nhl/members/stats?platform={CONSOLE}&clubId={CLUB_ID}"
        logger.info(f"Navigating directly to API: {api_url}")
        
        try:
            response = await page.goto(api_url, timeout=30000)
            
            if response.status == 200:
                logger.info("API returned 200 OK")
                
                # Wait for content to load
                await page.wait_for_load_state("domcontentloaded")
                
                # Try to get JSON from <pre> tag (how browsers display JSON)
                try:
                    json_text = await page.locator('body').inner_text()
                    data = json.loads(json_text)
                except:
                    # If that fails, try getting it from the response directly
                    json_text = await response.text()
                    data = json.loads(json_text)
                
                # Save to file
                Path("data/raw").mkdir(parents=True, exist_ok=True)
                with open("data/raw/proclubs_members_stats.json", "w") as f:
                    json.dump(data, f, indent=2)
                
                logger.info("✅ Data saved to data/raw/proclubs_members_stats.json")
                logger.info(f"Found {len(data.get('members', []))} members")
                
                await browser.close()
                return True
            else:
                logger.error(f"API returned status {response.status}")
                logger.error(await response.text())
                await browser.close()
                return False
                
        except Exception as e:
            logger.error(f"Failed to fetch API data: {e}", exc_info=True)
            await browser.close()
            return False

if __name__ == "__main__":
    logger.info("Starting Pro Clubs data capture...")
    success = asyncio.run(capture_proclubs_api_data())
    if success:
        logger.info("✅ Successfully captured Pro Clubs data")
    else:
        logger.error("❌ Failed to capture Pro Clubs data")