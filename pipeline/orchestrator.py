"""
Main pipeline orchestrator
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent))

from scrapers.api_scraper import APIBasicStatsScraper
from scrapers.ui_scraper import UIAdvancedStatsScraper
from scrapers.ea_proclubs_scraper import capture_proclubs_api_data
from scrapers.heatmap_scraper import scrape_career_shot_data
from pipeline.merge import merge_stats
from pipeline.validate import validate_data
from utils.helpers import setup_logging, get_existing_match_ids

logger = setup_logging(__name__)


async def run_pipeline():
    """Main pipeline execution"""
    logger.info("="*70)
    logger.info("NHL 26 Stats Pipeline - Starting")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70)
    
    new_games_processed = False
    
    try:
        # Step 1: Check for new games via API
        logger.info("\n[Step 1] Checking for new games...")
        api_scraper = APIBasicStatsScraper()
        club_data = api_scraper.fetch_club_data()
        
        if not club_data:
            logger.error("Failed to fetch club data.")
        else:
            match_ids = api_scraper.get_match_ids(club_data)
            existing_match_ids = get_existing_match_ids()
            new_match_ids = [mid for mid in match_ids if mid not in existing_match_ids]
            
            if not new_match_ids:
                logger.info("No new games found.")
            else:
                new_games_processed = True
                logger.info(f"Found {len(new_match_ids)} new games to scrape")
                
                # Step 2: Scrape basic stats
                logger.info("\n[Step 2] Scraping basic stats...")
                basic_data = api_scraper.scrape()
                basic_count = api_scraper.save(basic_data)
                logger.info(f"Saved {basic_count} basic stat records")
                
                # Step 3: Scrape advanced stats
                logger.info("\n[Step 3] Scraping advanced stats...")
                ui_scraper = UIAdvancedStatsScraper()
                advanced_data = await ui_scraper.scrape(new_match_ids)
                advanced_count = ui_scraper.save(advanced_data)
                logger.info(f"Saved {advanced_count} advanced stat records")
                
                # Step 4: Merge data
                logger.info("\n[Step 4] Merging datasets...")
                merge_success = merge_stats()
                
                if not merge_success:
                    logger.error("Merge failed")
                
                # Step 5: Validate
                logger.info("\n[Step 5] Validating data...")
                validation_success = validate_data()
                
                if not validation_success:
                    logger.warning("Validation found issues (see above)")
        
        # Step 6: Always capture Pro Clubs shot location data (independent of new games)
        logger.info("\n[Step 6] Capturing Pro Clubs shot location data...")
        capture_success = await capture_proclubs_api_data()
        
        if capture_success:
            # Step 7: Process shot location data
            logger.info("\n[Step 7] Processing shot location data...")
            shot_data = scrape_career_shot_data()
            logger.info(f"Collected shot location data for {len(shot_data)} players")
        else:
            logger.warning("Failed to capture Pro Clubs data - skipping shot location processing")

        logger.info("\n" + "="*70)
        logger.info("Pipeline completed successfully")
        if new_games_processed:
            logger.info(f"Processed {len(new_match_ids)} new games")
        else:
            logger.info("No new games processed, but shot location data updated")
        logger.info("="*70)
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(run_pipeline())