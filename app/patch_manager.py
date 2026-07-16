"""
Patch Update Management System
Helps track and manage hero data updates across game patches
"""

from datetime import datetime
from typing import Dict, List, Any
import json
from pathlib import Path


class PatchManager:
    """Manages patch versions and hero data updates"""

    def __init__(self):
        self.patches_file = "patch_history.json"
        self.heroes_file = "final_heroes.json"
        self.load_patch_history()

    def load_patch_history(self):
        """Load patch history or create if doesn't exist"""
        if Path(self.patches_file).exists():
            with open(self.patches_file, "r") as f:
                self.patch_history = json.load(f)
        else:
            self.patch_history = {
                "current_patch": None,
                "last_update": None,
                "patches": [],
            }

    def create_new_patch(
        self,
        patch_version: str,
        release_date: str,
        changes: Dict[str, Any],
        notes_url: str = "",
    ):
        """
        Create a new patch entry

        Example:
            patch_manager.create_new_patch(
                patch_version="1.8.32",
                release_date="2024-01-15",
                changes={
                    "buffed_heroes": ["Sora", "Claude"],
                    "nerfed_heroes": ["Karina"],
                    "revamped_heroes": ["Yin"],
                },
                notes_url="https://mobilelegends.fandom.com/wiki/Patch_1.8.32"
            )
        """
        patch_entry = {
            "patch_version": patch_version,
            "release_date": release_date,
            "update_date": datetime.now().isoformat(),
            "changes": changes,
            "notes_url": notes_url,
            "hero_updates": {},  # Will fill as we update heroes
        }

        self.patch_history["patches"].append(patch_entry)
        self.patch_history["current_patch"] = patch_version
        self.patch_history["last_update"] = datetime.now().isoformat()

        self.save_patch_history()
        print(f"✓ Created patch {patch_version}")

    def record_hero_update(
        self, patch_version: str, hero_name: str, changes: Dict[str, Any]
    ):
        """
        Record what changed for a hero in a patch

        Example:
            patch_manager.record_hero_update(
                patch_version="1.8.32",
                hero_name="Sora",
                changes={
                    "type": "buff",
                    "changes": [
                        "Skill 1 damage increased by 10%",
                        "Passive HP conversion increased from 30% to 35%"
                    ],
                    "reason": "Sora was underperforming in meta"
                }
            )
        """
        for patch in self.patch_history["patches"]:
            if patch["patch_version"] == patch_version:
                patch["hero_updates"][hero_name] = {
                    "updated_at": datetime.now().isoformat(),
                    "changes": changes,
                }
                self.save_patch_history()
                print(f"✓ Recorded update for {hero_name} in {patch_version}")
                return

        print(f"✗ Patch {patch_version} not found")

    def save_patch_history(self):
        """Save patch history to file"""
        with open(self.patches_file, "w") as f:
            json.dump(self.patch_history, f, indent=2)

    def get_hero_changelog(self, hero_name: str) -> List[Dict]:
        """Get all changes for a specific hero across patches"""
        changelog = []
        for patch in self.patch_history["patches"]:
            if hero_name in patch["hero_updates"]:
                changelog.append(
                    {
                        "patch": patch["patch_version"],
                        "date": patch["release_date"],
                        **patch["hero_updates"][hero_name],
                    }
                )
        return changelog

    def get_patch_summary(self, patch_version: str) -> Dict:
        """Get summary of all changes in a patch"""
        for patch in self.patch_history["patches"]:
            if patch["patch_version"] == patch_version:
                return patch
        return None

    def print_update_guide(self, patch_version: str):
        """Print a guide for updating heroes for a patch"""
        patch = self.get_patch_summary(patch_version)
        if not patch:
            print(f"Patch {patch_version} not found")
            return

        print("\n" + "=" * 60)
        print(f"PATCH {patch['patch_version']} - Update Guide")
        print("=" * 60)
        print(f"Release Date: {patch['release_date']}")
        if patch["notes_url"]:
            print(f"Full Notes: {patch['notes_url']}")

        if patch["changes"]:
            print("\nChanges Summary:")
            changes = patch["changes"]
            for change_type, heroes in changes.items():
                if heroes:
                    print(f"  {change_type}: {', '.join(heroes)}")

        print("\nHeroes to Update:")
        if patch["hero_updates"]:
            for hero, update in patch["hero_updates"].items():
                print(
                    f"  ✓ {hero} - {update.get('changes', {}).get('type', 'updated')}"
                )
        else:
            if patch["changes"]:
                all_changed = []
                for heroes_list in patch["changes"].values():
                    all_changed.extend(heroes_list)
                for hero in all_changed:
                    print(f"  ☐ {hero} - needs update")

        print("=" * 60)


# Workflow Example
if __name__ == "__main__":
    pm = PatchManager()

    # When new patch comes out
    pm.create_new_patch(
        patch_version="1.8.32",
        release_date="2024-01-15",
        changes={
            "buffed_heroes": ["Sora", "Claude", "Yin"],
            "nerfed_heroes": ["Karina", "Valentina"],
            "revamped_heroes": [],
        },
        notes_url="https://mobilelegends.fandom.com/wiki/Patch_1.8.32",
    )

    # As you update each hero
    pm.record_hero_update(
        patch_version="1.8.32",
        hero_name="Sora",
        changes={
            "type": "buff",
            "areas": ["Skill 1 damage", "Passive scaling"],
            "details": "Skill 1 increased by 10%, Passive conversion 30%→35%",
        },
    )

    # Get update guide
    pm.print_update_guide("1.8.32")

    # Track changes
    print("\nSora Changelog:")
    print(pm.get_hero_changelog("Sora"))
