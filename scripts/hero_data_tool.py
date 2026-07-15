"""
Hero JSON Validation and Update Tool
Helps validate hero data and batch update heroes for patches
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import shutil


class HeroDataValidator:
    """Validates hero JSON structure and values"""

    def __init__(self, filepath: str = "final_heroes.json"):
        self.filepath = filepath
        self.heroes = self._load_json()
        self.errors = []
        self.warnings = []

    def _load_json(self) -> List[Dict]:
        """Load JSON file"""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"✗ File not found: {self.filepath}")
            return []
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON: {e}")
            return []

    def validate_all(self) -> bool:
        """Run all validations"""
        print("\n" + "=" * 60)
        print("HERO DATA VALIDATION")
        print("=" * 60)

        for idx, hero in enumerate(self.heroes, 1):
            self._validate_hero(hero, idx)

        # Summary
        print("\n" + "=" * 60)
        print(f"VALIDATION COMPLETE - {len(self.heroes)} heroes checked")
        print("=" * 60)
        print(f"✓ Valid: {len(self.heroes) - len(self.errors)}")
        print(f"✗ Errors: {len(self.errors)}")
        print(f"⚠ Warnings: {len(self.warnings)}")

        if self.errors:
            print("\nERRORS:")
            for error in self.errors[:10]:  # Show first 10
                print(f"  ✗ {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")

        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings[:10]:
                print(f"  ⚠ {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")

        return len(self.errors) == 0

    def _validate_hero(self, hero: Dict, idx: int):
        """Validate a single hero"""
        hero_name = hero.get("name", f"Hero#{idx}")

        # Check required fields
        required_fields = ["name", "image", "stats", "meta"]
        for field in required_fields:
            if field not in hero:
                self.errors.append(f"{hero_name}: Missing '{field}'")
                return

        # Check stats
        self._validate_stats(hero, hero_name)

        # Check meta
        self._validate_meta(hero, hero_name)

    def _validate_stats(self, hero: Dict, hero_name: str):
        """Validate stats section"""
        stats = hero.get("stats", {})

        # Check key stats exist
        expected_stats = [
            "hp",
            "physical_attack",
            "physical_defense(physical_damage_reduced)",
        ]
        for stat in expected_stats:
            if stat not in stats:
                self.warnings.append(f"{hero_name}: Missing stat '{stat}'")

    def _validate_meta(self, hero: Dict, hero_name: str):
        """Validate meta attributes"""
        meta = hero.get("meta", {})

        if "attributes" not in meta:
            self.errors.append(f"{hero_name}: Missing meta.attributes")
            return

        attrs = meta["attributes"]

        # Check all attribute categories
        categories = {
            "combat": [
                "burst_damage",
                "sustained_damage",
                "dps",
                "aoe_damage",
                "poke",
                "single_target",
                "anti_tank",
                "anti_squishy",
            ],
            "survivability": ["tankiness", "mobility", "escape", "regen", "shields"],
            "utility": [
                "crowd_control",
                "displacement",
                "silence",
                "stun",
                "slow",
                "team_buff",
                "team_heal",
            ],
            "range_playstyle": ["range", "engage", "peel", "splitpush", "waveclear"],
            "power_curve": ["early_game", "mid_game", "late_game", "scaling"],
            "roles": ["primary_role", "secondary_role", "lane_priority"],
        }

        for category, expected_fields in categories.items():
            if category not in attrs:
                self.errors.append(f"{hero_name}: Missing attributes.{category}")
                continue

            cat_data = attrs[category]

            # Validate numeric fields (should be 0-5)
            if category != "roles":
                for field in expected_fields:
                    if field not in cat_data:
                        self.warnings.append(f"{hero_name}: Missing {category}.{field}")
                    else:
                        value = cat_data[field]
                        if not isinstance(value, (int, float)):
                            self.errors.append(
                                f"{hero_name}: {category}.{field} = {value} (expected number)"
                            )
                        elif not (0 <= value <= 5):
                            self.errors.append(
                                f"{hero_name}: {category}.{field} = {value} (should be 0-5)"
                            )

    def get_hero(self, hero_name: str) -> Dict:
        """Get hero by name"""
        for hero in self.heroes:
            if hero.get("name") == hero_name:
                return hero
        return None

    def save_json(self, filepath: str = None):
        """Save heroes back to JSON"""
        filepath = filepath or self.filepath
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.heroes, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved {len(self.heroes)} heroes to {filepath}")


class HeroDataUpdater:
    """Update hero data for patches"""

    def __init__(self, filepath: str = "final_heroes.json"):
        self.validator = HeroDataValidator(filepath)
        self.filepath = filepath

    def batch_update_heroes(self, updates: Dict[str, Dict]):
        """
        Batch update multiple heroes at once

        Example:
            updates = {
                "Sora": {
                    "combat.burst_damage": 5,
                    "power_curve.early_game": 5,
                    "reasoning.how_skills_influenced_scores": "New description..."
                },
                "Claude": {
                    "power_curve.mid_game": 4,
                }
            }
            updater.batch_update_heroes(updates)
        """
        print("\n" + "=" * 60)
        print("BATCH UPDATE HEROES")
        print("=" * 60)

        successful = 0
        failed = 0

        for hero_name, changes in updates.items():
            hero = self.validator.get_hero(hero_name)
            if not hero:
                print(f"✗ Hero not found: {hero_name}")
                failed += 1
                continue

            try:
                self._update_hero_fields(hero, changes)
                print(f"✓ Updated {hero_name}: {len(changes)} fields")
                successful += 1
            except Exception as e:
                print(f"✗ Failed to update {hero_name}: {e}")
                failed += 1

        print("=" * 60)
        print(f"Complete: {successful} successful, {failed} failed")

        return successful, failed

    def _update_hero_fields(self, hero: Dict, changes: Dict[str, any]):
        """
        Update nested fields in hero dict

        Supports dot notation:
        "combat.burst_damage" → hero["meta"]["attributes"]["combat"]["burst_damage"]
        """
        for path, value in changes.items():
            parts = path.split(".")
            current = hero

            # Navigate to parent
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Set final value
            final_key = parts[-1]
            old_value = current.get(final_key)
            current[final_key] = value

            print(f"    {path}: {old_value} → {value}")

    def backup_json(self) -> str:
        """Create backup of current JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"final_heroes_backup_{timestamp}.json"
        shutil.copy(self.filepath, backup_path)
        print(f"✓ Backup created: {backup_path}")
        return backup_path

    def save_and_validate(self) -> bool:
        """Save updates and validate"""
        print("\nValidating before save...")
        if self.validator.validate_all():
            print("\n✓ Validation passed!")
            self.validator.save_json()
            return True
        else:
            print("\n✗ Validation failed - not saving")
            return False


# CLI Tool
def main():
    """Example usage"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        # Validate JSON
        validator = HeroDataValidator()
        validator.validate_all()

    elif len(sys.argv) > 1 and sys.argv[1] == "example":
        # Example: Update heroes for a patch
        print("\n" + "=" * 60)
        print("EXAMPLE: Update for Patch 1.8.32")
        print("=" * 60)

        updater = HeroDataUpdater()

        # Backup first
        updater.backup_json()

        # Define updates from patch notes
        patch_updates = {
            "Sora": {
                "combat.burst_damage": 5,
                "combat.dps": 5,
                "power_curve.early_game": 5,
            },
            "Claude": {
                "survivability.mobility": 5,
                "power_curve.mid_game": 5,
            },
            "Karina": {
                "combat.burst_damage": 4,  # Nerfed
                "power_curve.late_game": 4,
            },
        }

        # Apply updates
        successful, failed = updater.batch_update_heroes(patch_updates)

        # Save and validate
        updater.save_and_validate()

    else:
        # Usage guide
        print("\n" + "=" * 60)
        print("Hero Data Tool - Usage")
        print("=" * 60)
        print("\nCommands:")
        print("  python hero_data_tool.py validate  - Validate hero JSON")
        print("  python hero_data_tool.py example   - Example patch update")
        print("\nOr use programmatically:")
        print("""
        from hero_data_tool import HeroDataValidator, HeroDataUpdater
        
        # Validate
        validator = HeroDataValidator()
        validator.validate_all()
        
        # Update
        updater = HeroDataUpdater()
        updater.batch_update_heroes({
            "HeroName": {"field.path": value}
        })
        updater.save_and_validate()
        """)


if __name__ == "__main__":
    main()
