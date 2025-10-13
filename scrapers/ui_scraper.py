"""
UI-based scraper for advanced NHL 26 stats
"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.config import (
    PLAYER_NAMES, CLUB_ID, DB_ADVANCED_STATS,
    SCRAPER_TIMEOUT, WAIT_AFTER_CLICK, HEADLESS_MODE,
    get_game_url
)
from utils.helpers import setup_logging

logger = setup_logging(__name__)


class UIAdvancedStatsScraper:
    """Scrapes advanced stats from ChelStats UI"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        
    async def initialize(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=HEADLESS_MODE)
        logger.info("Browser initialized")
        
    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")
    
    def parse_advanced_stats(self, html):
        """Parse advanced stats from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        stats = {}
        
        # Find all label tags
        labels = soup.find_all('p', class_='css-9y6e4h')
        
        for label in labels:
            label_text = label.get_text(strip=True)
            value_tag = label.find_next_sibling('p')
            
            if value_tag:
                value_text = value_tag.get_text(strip=True)
                
                if label_text == 'WAR':
                    stats['war'] = self._to_float(value_text)
                elif label_text == 'TO':
                    stats['total_offense'] = self._to_float(value_text)
                elif label_text == 'TD':
                    stats['total_defense'] = self._to_float(value_text)
                elif label_text == 'Eff':
                    stats['efficiency'] = self._to_float(value_text)
                elif label_text == 'xG':
                    stats['expected_goals'] = self._to_float(value_text)
                elif label_text == 'GAE':
                    stats['goals_above_expected'] = self._to_float(value_text)
                elif label_text == 'GAR':
                    stats['goals_above_replacement'] = self._to_float(value_text)
        
        return stats
    
    def _to_float(self, value):
        try:
            return float(str(value).replace('%', '').replace(',', '').strip())
        except:
            return None
    
    async def scrape_game(self, match_id):
        """Scrape advanced stats for one game"""
        page = await self.browser.new_page()
        url = get_game_url(match_id)
        
        all_player_stats = []
        
        try:
            logger.info(f"Scraping game {match_id}")
            await page.goto(url, wait_until="networkidle", timeout=SCRAPER_TIMEOUT)
            await page.wait_for_timeout(5000)
            
            # Close any modals
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
            
            # Click ADVANCED STATS tab
            await page.click('text=ADVANCED STATS')
            await page.wait_for_timeout(3000)
            
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
            
            # Iterate through players
            for player_name in PLAYER_NAMES:
                try:
                    # Click dropdown
                    await page.locator('#player-select').click(force=True, timeout=5000)
                    await page.wait_for_timeout(1500)
                    
                    # Select player
                    try:
                        await page.locator(f'[role="option"]:has-text("{player_name}")').click(timeout=5000)
                    except Exception as e:
                        logger.warning(f"  {player_name} not found in dropdown (likely didn't play)")
                        # Close the dropdown before continuing
                        await page.keyboard.press('Escape')
                        await page.wait_for_timeout(500)
                        continue
                    
                    await page.wait_for_timeout(WAIT_AFTER_CLICK)
                    
                    # Extract stats
                    html = await page.content()
                    stats = self.parse_advanced_stats(html)
                    
                    stats['player_name'] = player_name
                    stats['match_id'] = match_id
                    stats['scraped_at'] = datetime.now().isoformat()
                    
                    all_player_stats.append(stats)
                    
                    logger.info(f"  {player_name}: WAR={stats.get('war', 'N/A')}%")
                    
                except Exception as e:
                    logger.error(f"  Error scraping {player_name}: {e}")
            
            return all_player_stats
            
        except Exception as e:
            logger.error(f"Error scraping game {match_id}: {e}")
            return []
        finally:
            await page.close()
    
    async def scrape(self, match_ids):
        """Scrape multiple games"""
        logger.info(f"Starting advanced stats scraper for {len(match_ids)} games...")
        
        await self.initialize()
        
        all_stats = []
        for match_id in match_ids:
            stats = await self.scrape_game(match_id)
            all_stats.extend(stats)
        
        await self.close()
        
        return all_stats
    
    def save(self, data):
        """Save to database with duplicate checking"""
        if not data:
            logger.warning("No data to save")
            return 0
        
        df_new = pd.DataFrame(data)
        
        if DB_ADVANCED_STATS.exists():
            df_existing = pd.read_csv(DB_ADVANCED_STATS)
            
            df_existing['key'] = df_existing['match_id'].astype(str) + '_' + df_existing['player_name']
            df_new['key'] = df_new['match_id'].astype(str) + '_' + df_new['player_name']
            
            df_new_only = df_new[~df_new['key'].isin(df_existing['key'])].drop('key', axis=1)
            df_existing = df_existing.drop('key', axis=1)
            
            if len(df_new_only) > 0:
                df_combined = pd.concat([df_existing, df_new_only], ignore_index=True)
            else:
                logger.info("No new records (all duplicates)")
                return 0
        else:
            df_combined = df_new
        
        df_combined.to_csv(DB_ADVANCED_STATS, index=False)
        logger.info(f"Saved {len(df_new)} new records to {DB_ADVANCED_STATS}")
        
        return len(df_new)