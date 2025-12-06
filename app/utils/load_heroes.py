"""
Script to load hero data from final_heroes.json into the database
"""

import json
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.db.database import SessionLocal, init_db
from app.db.models import Hero


def load_heroes_from_json(json_file: str = "final_heroes.json"):
    """Load heroes from JSON file into database"""
    
    # Initialize database
    print("Initializing database...")
    init_db()
    
    # Load JSON data
    print(f"Loading heroes from {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    heroes_data = data.get('heroes', [])
    print(f"Found {len(heroes_data)} heroes in file")
    
    # Create database session
    db = SessionLocal()
    
    try:
        added_count = 0
        updated_count = 0
        error_count = 0
        
        for hero_data in heroes_data:
            try:
                name = hero_data.get('name')
                if not name:
                    print(f"  ⚠ Skipping hero without name")
                    error_count += 1
                    continue
                
                # Check if hero already exists
                existing_hero = db.query(Hero).filter(Hero.name == name).first()
                
                if existing_hero:
                    # Update existing hero
                    existing_hero.image = hero_data.get('image', '')
                    
                    if 'stats' in hero_data:
                        existing_hero.set_stats(hero_data['stats'])
                    
                    if 'meta' in hero_data:
                        existing_hero.set_meta(hero_data['meta'])
                    
                    updated_count += 1
                    print(f"  ✓ Updated: {name}")
                else:
                    # Create new hero
                    new_hero = Hero(
                        name=name,
                        image=hero_data.get('image', '')
                    )
                    
                    if 'stats' in hero_data:
                        new_hero.set_stats(hero_data['stats'])
                    
                    if 'meta' in hero_data:
                        new_hero.set_meta(hero_data['meta'])
                    
                    db.add(new_hero)
                    added_count += 1
                    print(f"  ✓ Added: {name}")
                    
            except Exception as e:
                print(f"  ✗ Error processing {hero_data.get('name', 'Unknown')}: {str(e)}")
                error_count += 1
                continue
        
        # Commit all changes
        db.commit()
        
        print(f"\n{'='*50}")
        print(f"Summary:")
        print(f"  Added: {added_count} heroes")
        print(f"  Updated: {updated_count} heroes")
        print(f"  Errors: {error_count}")
        print(f"  Total: {added_count + updated_count} heroes in database")
        print(f"{'='*50}")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error during database operation: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Load heroes from JSON into database')
    parser.add_argument('--file', type=str, default='final_heroes.json',
                        help='Path to JSON file (default: final_heroes.json)')
    
    args = parser.parse_args()
    
    try:
        load_heroes_from_json(args.file)
    except Exception as e:
        print(f"\n✗ Failed to load heroes: {str(e)}")
        sys.exit(1)
