"""
Data Loader Script - Loads final_heroes.json into Neon database
Usage: python load_heroes.py
"""

import json
import logging
import sys
from pathlib import Path
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

from app.db.database import SessionLocal, init_db, test_connection
from app.db.models import Hero


def load_heroes_from_json(file_path: str = "final_heroes.json") -> list:
    """
    Load heroes from JSON file

    Args:
        file_path: Path to final_heroes.json

    Returns:
        List of hero dictionaries
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            heroes_data = json.load(f)

        # Handle both list and dict formats
        if isinstance(heroes_data, dict):
            heroes_list = heroes_data.get("heroes", [])
        else:
            heroes_list = heroes_data

        logger.info(f"✓ Loaded {len(heroes_list)} heroes from {file_path}")
        return heroes_list

    except FileNotFoundError:
        logger.error(f"✗ File not found: {file_path}")
        return []
    except json.JSONDecodeError:
        logger.error(f"✗ Invalid JSON in {file_path}")
        return []
    except Exception as e:
        logger.error(f"✗ Error loading file: {e}")
        return []


def populate_heroes_to_db(heroes_list: list, clear_existing: bool = False) -> tuple:
    """
    Populate heroes to database

    Args:
        heroes_list: List of hero dictionaries from JSON
        clear_existing: If True, drop all existing heroes first

    Returns:
        Tuple of (successful_count, failed_count)
    """
    db = SessionLocal()
    successful = 0
    failed = 0
    errors = []

    try:
        # Optionally clear existing data
        if clear_existing:
            logger.warning("⚠️  Clearing existing heroes...")
            db.query(Hero).delete()
            db.commit()
            logger.info("✓ Existing heroes cleared")

        logger.info(f"Starting to insert {len(heroes_list)} heroes...")

        for idx, hero_data in enumerate(heroes_list, 1):
            try:
                # Check if hero already exists
                hero_name = hero_data.get("name")
                if not hero_name:
                    logger.warning(f"  ⚠️  Skipping hero #{idx}: Missing name")
                    failed += 1
                    continue

                existing = db.query(Hero).filter(Hero.name == hero_name).first()

                if existing:
                    # Update existing hero
                    if "stats" in hero_data:
                        existing.set_stats(hero_data.get("stats", {}))
                    if "meta" in hero_data:
                        existing.set_meta(hero_data.get("meta", {}))
                    if "image" in hero_data:
                        existing.image = hero_data.get("image")

                    db.commit()
                    successful += 1

                    if idx % 50 == 0:
                        logger.info(f"  ✓ Processed {successful + failed} heroes...")
                else:
                    # Create new hero
                    new_hero = Hero(
                        name=hero_name,
                        image=hero_data.get("image", ""),
                    )

                    # Set stats and meta
                    if "stats" in hero_data:
                        new_hero.set_stats(hero_data.get("stats", {}))
                    if "meta" in hero_data:
                        new_hero.set_meta(hero_data.get("meta", {}))

                    db.add(new_hero)
                    db.commit()
                    successful += 1

                    if idx % 50 == 0:
                        logger.info(f"  ✓ Processed {successful + failed} heroes...")

            except Exception as e:
                db.rollback()
                failed += 1
                error_msg = (
                    f"Hero #{idx} ({hero_data.get('name', 'Unknown')}): {str(e)}"
                )
                errors.append(error_msg)
                logger.error(f"  ✗ {error_msg}")
                continue

        logger.info(f"✓ Completed: {successful} successful, {failed} failed")

        if errors and len(errors) <= 10:
            logger.info("First few errors:")
            for error in errors[:10]:
                logger.info(f"  - {error}")

        return successful, failed

    except Exception as e:
        logger.error(f"✗ Database error: {e}")
        db.rollback()
        return 0, len(heroes_list)

    finally:
        db.close()


def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("DraftSensei - Hero Data Loader")
    logger.info("=" * 60)

    # Step 1: Test database connection
    logger.info("\n[1/4] Testing database connection...")
    if not test_connection():
        logger.error("✗ Cannot connect to database. Check your .env file.")
        logger.error("  Make sure DATABASE_URL is set correctly in .env")
        return False

    # Step 2: Initialize database tables
    logger.info("\n[2/4] Initializing database tables...")
    if not init_db():
        logger.error("✗ Failed to initialize database tables.")
        return False

    # Step 3: Load heroes from JSON
    logger.info("\n[3/4] Loading heroes from final_heroes.json...")
    heroes_list = load_heroes_from_json("final_heroes.json")

    if not heroes_list:
        logger.error("✗ No heroes loaded from JSON file.")
        logger.error("  Make sure final_heroes.json exists in the current directory")
        return False

    # Step 4: Populate database
    logger.info("\n[4/4] Populating database...")
    successful, failed = populate_heroes_to_db(heroes_list, clear_existing=False)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("LOAD COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total processed: {successful + failed}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")

    if successful > 0:
        logger.info("\n✓ Hero data loaded successfully!")
        return True
    else:
        logger.error("\n✗ No heroes were loaded.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
