"""
Patch Updater Utility - Script to load new patch hero data
"""

import json
import os
import sys
import requests
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Hero
from app.schemas.hero_schema import HeroCreate, BulkHeroUpdate


class PatchUpdater:
    """
    Utility class for updating hero data from patch files or external sources
    """
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'db'):
            self.db.close()
    
    def load_patch_data_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load patch data from a JSON file
        
        Expected format:
        {
            "patch_version": "1.7.34",
            "heroes": [
                {
                    "name": "Hero Name",
                    "role": "Tank",
                    "stats": {...},
                    "counters": {...},
                    "synergy": {...}
                },
                ...
            ]
        }
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in file '{file_path}': {e}")
            return {}
    
    def update_heroes_from_file(self, file_path: str, update_mode: str = "merge") -> Dict[str, Any]:
        """
        Update heroes from a JSON file
        """
        patch_data = self.load_patch_data_from_file(file_path)
        
        if not patch_data:
            return {"error": "Failed to load patch data"}
        
        heroes_data = patch_data.get("heroes", [])
        patch_version = patch_data.get("patch_version", "unknown")
        
        if not heroes_data:
            return {"error": "No hero data found in file"}
        
        # Convert to HeroCreate objects
        heroes = []
        for hero_data in heroes_data:
            try:
                hero = HeroCreate(**hero_data)
                heroes.append(hero)
            except Exception as e:
                print(f"Error parsing hero data: {hero_data.get('name', 'unknown')}: {e}")
                continue
        
        if not heroes:
            return {"error": "No valid heroes found"}
        
        return self.bulk_update_heroes(heroes, patch_version, update_mode)
    
    def bulk_update_heroes(self, heroes: List[HeroCreate], patch_version: str, update_mode: str = "merge") -> Dict[str, Any]:
        """
        Bulk update heroes in database
        """
        updated_count = 0
        created_count = 0
        errors = []
        
        try:
            for hero_data in heroes:
                try:
                    # Check if hero exists
                    existing_hero = self.db.query(Hero).filter(Hero.name == hero_data.name).first()
                    
                    if existing_hero:
                        # Update existing hero
                        if update_mode == "replace" or hero_data.stats:
                            if hero_data.stats:
                                existing_hero.set_stats(hero_data.stats)
                        
                        if update_mode == "replace" or hero_data.counters:
                            if hero_data.counters:
                                existing_hero.set_counters(hero_data.counters)
                        
                        if update_mode == "replace" or hero_data.synergy:
                            if hero_data.synergy:
                                existing_hero.set_synergy(hero_data.synergy)
                        
                        if hero_data.role:
                            existing_hero.role = hero_data.role
                        
                        if hasattr(hero_data, 'image') and hero_data.image:
                            existing_hero.image = hero_data.image
                        
                        updated_count += 1
                        print(f"Updated hero: {hero_data.name}")
                    else:
                        # Create new hero
                        new_hero = Hero(
                            name=hero_data.name,
                            role=hero_data.role
                        )
                        
                        if hero_data.stats:
                            new_hero.set_stats(hero_data.stats)
                        if hero_data.counters:
                            new_hero.set_counters(hero_data.counters)
                        if hero_data.synergy:
                            new_hero.set_synergy(hero_data.synergy)
                        if hasattr(hero_data, 'image') and hero_data.image:
                            new_hero.image = hero_data.image
                        
                        self.db.add(new_hero)
                        created_count += 1
                        print(f"Created hero: {hero_data.name}")
                        
                except Exception as e:
                    error_msg = f"Error processing hero '{hero_data.name}': {str(e)}"
                    errors.append(error_msg)
                    print(error_msg)
                    continue
            
            # Commit all changes
            self.db.commit()
            
            result = {
                "success": True,
                "message": "Bulk update completed",
                "created": created_count,
                "updated": updated_count,
                "patch_version": patch_version
            }
            
            if errors:
                result["errors"] = errors
            
            print(f"Bulk update completed: {created_count} created, {updated_count} updated")
            return result
            
        except Exception as e:
            self.db.rollback()
            error_msg = f"Error in bulk update: {str(e)}"
            print(error_msg)
            return {"success": False, "error": error_msg}
    
    def load_sample_data(self) -> Dict[str, Any]:
        """
        Load sample hero data for development/testing
        """
        print("Loading sample hero data...")
        heroes = self.load_sample_heroes()
        return self.bulk_update_heroes(heroes, "sample_v1.0", "replace")
    
    def create_patch_template(self, output_file: str = "patch_template.json"):
        """
        Create a template JSON file for patch updates
        """
        template = {
            "patch_version": "1.7.34",
            "description": "Mobile Legends Patch Update",
            "heroes": [
                {
                    "name": "Hero Name",
                    "role": "Tank",  # Tank, Fighter, Assassin, Mage, Marksman, Support
                    "image": "https://kgapbcqtdpyhonznxwyu.supabase.co/storage/v1/object/public/hero-images/khufra.png",
                    "stats": {
                        "hp": 2500,
                        "mana": 400,
                        "attack_damage": 120,
                        "physical_defense": 20,
                        "magic_defense": 15,
                        "movement_speed": 240,
                        "attack_speed": 1.0,
                        "cooldown_reduction": 0,
                        "critical_chance": 0,
                        "penetration": 0,
                        "spell_vamp": 0,
                        "physical_lifesteal": 0
                    },
                    "counters": {
                        "Enemy Hero 1": 85.0,
                        "Enemy Hero 2": 70.0
                    },
                    "synergy": {
                        "Partner Hero 1": 90.0,
                        "Partner Hero 2": 75.0
                    }
                }
            ]
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=4, ensure_ascii=False)
            print(f"Patch template created: {output_file}")
            return {"success": True, "file": output_file}
        except Exception as e:
            print(f"Error creating template: {e}")
            return {"success": False, "error": str(e)}


def main():
    """
    Command line interface for patch updater
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="DraftSensei Patch Updater")
    parser.add_argument("action", choices=["load-sample", "update-from-file", "create-template"], 
                       help="Action to perform")
    parser.add_argument("--file", "-f", help="File path for patch data")
    parser.add_argument("--mode", "-m", choices=["merge", "replace"], default="merge",
                       help="Update mode: merge or replace")
    parser.add_argument("--output", "-o", default="patch_template.json",
                       help="Output file for template creation")
    
    args = parser.parse_args()
    
    updater = PatchUpdater()
    
    if args.action == "load-sample":
        result = updater.load_sample_data()
        print(f"Sample data loading result: {result}")
    
    elif args.action == "update-from-file":
        if not args.file:
            print("Error: --file argument required for update-from-file action")
            return
        result = updater.update_heroes_from_file(args.file, args.mode)
        print(f"File update result: {result}")
    
    elif args.action == "create-template":
        result = updater.create_patch_template(args.output)
        print(f"Template creation result: {result}")


if __name__ == "__main__":
    main()