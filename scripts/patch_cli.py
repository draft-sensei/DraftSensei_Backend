"""
DraftSensei - Patch Manager CLI
Interactive tool for managing hero data across patches.

Usage: python patch_cli.py
"""

import json
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# ─────────────────────────────────────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────────────────────────────────────

sys.path.insert(0, str(Path(__file__).parent.absolute()))

from dotenv import load_dotenv

load_dotenv()

HEROES_FILE = "final_heroes.json"
PATCH_HISTORY_FILE = "patch_history.json"

# Valid attribute categories and their fields
ATTRIBUTE_SCHEMA = {
    "combat": [
        "burst_damage",
        "sustained_damage",
        "poke",
        "aoe_damage",
        "single_target",
        "anti_tank",
        "anti_squishy",
        "dps",
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
    "range_playstyle": [
        "range",
        "engage",
        "peel",
        "splitpush",
        "waveclear",
        "vision_or_traps",
    ],
    "power_curve": ["early_game", "mid_game", "late_game", "scaling"],
}

VALID_ROLES = ["Tank", "Fighter", "Assassin", "Mage", "Marksman", "Support"]
VALID_LANES = ["EXP Lane", "Jungle", "Mid Lane", "Gold Lane", "Roam"]


# ─────────────────────────────────────────────────────────────────────────────
# FILE I/O
# ─────────────────────────────────────────────────────────────────────────────


def load_heroes() -> List[Dict]:
    """Load heroes from JSON file"""
    try:
        with open(HEROES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data.get("heroes", [])
        return data
    except FileNotFoundError:
        print(f"  ✗ {HEROES_FILE} not found")
        return []
    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON: {e}")
        return []


def save_heroes(heroes: List[Dict]) -> bool:
    """Save heroes back to JSON file"""
    try:
        with open(HEROES_FILE, "w", encoding="utf-8") as f:
            json.dump(heroes, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"  ✗ Save failed: {e}")
        return False


def load_patch_history() -> Dict:
    """Load patch history or create empty structure"""
    if Path(PATCH_HISTORY_FILE).exists():
        with open(PATCH_HISTORY_FILE, "r") as f:
            return json.load(f)
    return {"current_patch": None, "last_update": None, "patches": []}


def save_patch_history(history: Dict) -> bool:
    """Save patch history"""
    try:
        with open(PATCH_HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
        return True
    except Exception as e:
        print(f"  ✗ Failed to save patch history: {e}")
        return False


def backup_heroes() -> str:
    """Create a timestamped backup of heroes file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"final_heroes_backup_{timestamp}.json"
    shutil.copy(HEROES_FILE, backup_path)
    return backup_path


def find_hero(heroes: List[Dict], name: str) -> Optional[Dict]:
    """Find hero by name (case-insensitive)"""
    name_lower = name.lower()
    for hero in heroes:
        if hero.get("name", "").lower() == name_lower:
            return hero
    return None


# ─────────────────────────────────────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def subheader(title: str):
    print(f"\n── {title} {'─' * (54 - len(title))}")


def prompt(msg: str, default: str = "") -> str:
    """Get input with optional default"""
    if default:
        result = input(f"  {msg} [{default}]: ").strip()
        return result if result else default
    return input(f"  {msg}: ").strip()


def prompt_int(msg: str, min_val: int = 0, max_val: int = 5) -> Optional[int]:
    """Get integer input within range"""
    while True:
        raw = input(f"  {msg} ({min_val}-{max_val}): ").strip()
        if raw == "":
            return None  # Skip/keep existing
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            print(f"    ✗ Must be between {min_val} and {max_val}")
        except ValueError:
            print("    ✗ Please enter a number")


def confirm(msg: str) -> bool:
    """Y/N confirmation"""
    answer = input(f"  {msg} (y/n): ").strip().lower()
    return answer in ("y", "yes")


def show_patch_status(history: Dict):
    """Show current patch info"""
    current = history.get("current_patch")
    last_update = history.get("last_update")
    patch_count = len(history.get("patches", []))

    if current:
        print(f"  Current patch: {current}")
        print(f"  Last updated:  {last_update[:10] if last_update else 'Unknown'}")
        print(f"  Total patches: {patch_count}")
    else:
        print("  No patch set yet")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────────────────────────────────────


def main_menu():
    """Main CLI entry point"""
    while True:
        clear()
        heroes = load_heroes()
        history = load_patch_history()

        header("DraftSensei - Patch Manager CLI")
        print(f"  Heroes loaded: {len(heroes)}")
        show_patch_status(history)

        print("\n  What would you like to do?\n")
        print("  [1] New Patch - Start a new patch update")
        print("  [2] Update Hero - Edit an existing hero's attributes")
        print("  [3] Add Hero - Add a brand new hero")
        print("  [4] View Hero - View a hero's current data")
        print("  [5] Patch History - View and manage past patches")
        print("  [6] Validate JSON - Check for errors in hero data")
        print("  [7] Push to DB - Load updated heroes into Neon database")
        print("  [8] Backup - Create a backup of heroes file")
        print("  [0] Exit")

        choice = prompt("\n  Choice").strip()

        if choice == "1":
            new_patch_flow(heroes, history)
        elif choice == "2":
            update_hero_flow(heroes, history)
        elif choice == "3":
            add_hero_flow(heroes, history)
        elif choice == "4":
            view_hero_flow(heroes)
        elif choice == "5":
            patch_history_flow(history)
        elif choice == "6":
            validate_flow(heroes)
        elif choice == "7":
            push_to_db_flow()
        elif choice == "8":
            backup_flow()
        elif choice == "0":
            print("\n  Goodbye!\n")
            break
        else:
            print("  ✗ Invalid choice")
            input("  Press Enter to continue...")


# ─────────────────────────────────────────────────────────────────────────────
# 1. NEW PATCH FLOW
# ─────────────────────────────────────────────────────────────────────────────


def new_patch_flow(heroes: List[Dict], history: Dict):
    """Start a new patch - record what changed"""
    clear()
    header("New Patch")

    print("  Enter the new patch details from the official patch notes.\n")

    version = prompt("Patch version (e.g. 1.8.94)")
    if not version:
        return

    release_date = prompt(
        "Release date (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d")
    )
    notes_url = prompt("Patch notes URL (optional)", "")

    print("\n  Enter changed heroes (comma-separated, or leave blank):")
    buffed = [h.strip() for h in prompt("Buffed heroes").split(",") if h.strip()]
    nerfed = [h.strip() for h in prompt("Nerfed heroes").split(",") if h.strip()]
    revamped = [h.strip() for h in prompt("Revamped heroes").split(",") if h.strip()]
    new_heroes = [h.strip() for h in prompt("New heroes").split(",") if h.strip()]

    # Validate hero names exist
    all_changed = buffed + nerfed + revamped
    unknown = [h for h in all_changed if not find_hero(heroes, h)]
    if unknown:
        print(f"\n  ⚠ These heroes not found in DB: {', '.join(unknown)}")
        print("  (New heroes will be added separately)")

    # Build patch entry
    patch_entry = {
        "patch_version": version,
        "release_date": release_date,
        "created_at": datetime.now().isoformat(),
        "notes_url": notes_url,
        "changes": {
            "buffed": buffed,
            "nerfed": nerfed,
            "revamped": revamped,
            "new_heroes": new_heroes,
        },
        "hero_updates": {},
        "status": "in_progress",
    }

    history["patches"].append(patch_entry)
    history["current_patch"] = version
    history["last_update"] = datetime.now().isoformat()
    save_patch_history(history)

    print(f"\n  ✓ Patch {version} created!")

    # Show update checklist
    subheader("Update Checklist")
    all_to_update = buffed + nerfed + revamped + new_heroes
    if all_to_update:
        print("  Heroes that need updating:\n")
        for hero in all_to_update:
            status = "NEW" if hero in new_heroes else "UPDATE"
            print(f"    ☐ {hero} ({status})")
    else:
        print("  No heroes to update listed")

    print("\n  Tip: Go to [2] Update Hero or [3] Add Hero to apply changes")
    input("\n  Press Enter to continue...")


# ─────────────────────────────────────────────────────────────────────────────
# 2. UPDATE HERO FLOW
# ─────────────────────────────────────────────────────────────────────────────


def update_hero_flow(heroes: List[Dict], history: Dict):
    """Update an existing hero's attributes"""
    clear()
    header("Update Hero")

    name = prompt("Hero name")
    hero = find_hero(heroes, name)

    if not hero:
        print(f"\n  ✗ Hero '{name}' not found")
        print("  Tip: Use [3] Add Hero for new heroes")
        input("\n  Press Enter to continue...")
        return

    print(f"\n  Found: {hero['name']}")

    # Show current meta
    meta = hero.get("meta", {})
    attrs = meta.get("attributes", {})
    roles = attrs.get("roles", {})
    print(
        f"  Role: {roles.get('primary_role', '?')} / {roles.get('secondary_role', '?')}"
    )
    print(f"  Lanes: {', '.join(roles.get('lane_priority', []))}")

    print("\n  What would you like to update?\n")
    print("  [1] Combat attributes")
    print("  [2] Survivability attributes")
    print("  [3] Utility attributes")
    print("  [4] Range & Playstyle attributes")
    print("  [5] Power Curve attributes")
    print("  [6] Role & Lane priority")
    print("  [7] Reasoning / Description text")
    print("  [8] Update all attribute categories")
    print("  [0] Back")

    choice = prompt("\n  Choice")

    changed = False

    if choice == "1":
        changed = update_attribute_category(hero, "combat")
    elif choice == "2":
        changed = update_attribute_category(hero, "survivability")
    elif choice == "3":
        changed = update_attribute_category(hero, "utility")
    elif choice == "4":
        changed = update_attribute_category(hero, "range_playstyle")
    elif choice == "5":
        changed = update_attribute_category(hero, "power_curve")
    elif choice == "6":
        changed = update_role_and_lanes(hero)
    elif choice == "7":
        changed = update_reasoning(hero)
    elif choice == "8":
        for category in ATTRIBUTE_SCHEMA.keys():
            update_attribute_category(hero, category)
        changed = True
    elif choice == "0":
        return

    if changed:
        # Record the update in patch history
        current_patch = history.get("current_patch")
        if current_patch:
            for patch in history["patches"]:
                if patch["patch_version"] == current_patch:
                    patch["hero_updates"][hero["name"]] = {
                        "updated_at": datetime.now().isoformat(),
                        "status": "done",
                    }
                    break
            save_patch_history(history)

        # Save to file
        if save_heroes(heroes):
            print(f"\n  ✓ {hero['name']} saved successfully!")
        else:
            print(f"\n  ✗ Failed to save")

    input("\n  Press Enter to continue...")


def update_attribute_category(hero: Dict, category: str) -> bool:
    """Update all fields in a single attribute category"""
    subheader(f"Editing: {category.replace('_', ' ').title()}")

    meta = hero.setdefault("meta", {})
    attrs = meta.setdefault("attributes", {})
    cat_data = attrs.setdefault(category, {})

    fields = ATTRIBUTE_SCHEMA.get(category, [])
    changed = False

    print("  Press Enter to keep current value. Enter 0-5 to update.\n")

    for field in fields:
        current = cat_data.get(field, "?")
        new_val = prompt_int(f"{field:<25} (current: {current})")
        if new_val is not None:
            cat_data[field] = new_val
            changed = True
            print(f"    ✓ {field}: {current} → {new_val}")

    return changed


def update_role_and_lanes(hero: Dict) -> bool:
    """Update hero's role and lane priority"""
    subheader("Role & Lane Priority")

    meta = hero.setdefault("meta", {})
    attrs = meta.setdefault("attributes", {})
    roles = attrs.setdefault("roles", {})

    print(f"  Current primary role:   {roles.get('primary_role', '?')}")
    print(f"  Current secondary role: {roles.get('secondary_role', '?')}")
    print(f"  Current lane priority:  {roles.get('lane_priority', [])}")

    print(f"\n  Valid roles: {', '.join(VALID_ROLES)}")
    print(f"  Valid lanes: {', '.join(VALID_LANES)}")

    changed = False

    primary = prompt("\n  New primary role (Enter to keep)")
    if primary:
        if primary not in VALID_ROLES:
            print(f"  ✗ Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
        else:
            roles["primary_role"] = primary
            changed = True

    secondary = prompt("  New secondary role (Enter to keep)")
    if secondary:
        if secondary not in VALID_ROLES:
            print(f"  ✗ Invalid role.")
        else:
            roles["secondary_role"] = secondary
            changed = True

    print("\n  Enter lane priority in order (e.g. EXP Lane, Jungle)")
    print("  Comma-separated. Enter to keep current.")
    lanes_input = prompt("  Lane priority")
    if lanes_input:
        lanes = [l.strip() for l in lanes_input.split(",")]
        invalid = [l for l in lanes if l not in VALID_LANES]
        if invalid:
            print(f"  ✗ Invalid lanes: {invalid}")
            print(f"  Valid: {VALID_LANES}")
        else:
            roles["lane_priority"] = lanes
            changed = True

    return changed


def update_reasoning(hero: Dict) -> bool:
    """Update hero's reasoning text"""
    subheader("Reasoning / Description")

    meta = hero.setdefault("meta", {})
    reasoning = meta.setdefault("reasoning", {})

    fields = [
        "how_stats_influenced_scores",
        "how_skills_influenced_scores",
        "cooldown_impact",
        "special_passives_analysis",
        "final_role_justification",
    ]

    changed = False
    print("  Press Enter to skip a field.\n")

    for field in fields:
        current = reasoning.get(field, "")
        print(f"\n  {field}:")
        if current:
            # Show truncated current value
            preview = current[:100] + "..." if len(current) > 100 else current
            print(f"  Current: {preview}")

        new_val = input("  New text (Enter to skip): ").strip()
        if new_val:
            reasoning[field] = new_val
            changed = True
            print(f"  ✓ Updated")

    return changed


# ─────────────────────────────────────────────────────────────────────────────
# 3. ADD HERO FLOW
# ─────────────────────────────────────────────────────────────────────────────


def add_hero_flow(heroes: List[Dict], history: Dict):
    """Add a brand new hero to the JSON"""
    clear()
    header("Add New Hero")

    name = prompt("Hero name")
    if not name:
        return

    # Check if already exists
    if find_hero(heroes, name):
        print(f"\n  ✗ Hero '{name}' already exists. Use [2] Update Hero instead.")
        input("\n  Press Enter to continue...")
        return

    image_url = prompt("Image URL (optional)", "")

    print(f"\n  Valid roles: {', '.join(VALID_ROLES)}")
    primary_role = prompt("Primary role")
    if primary_role not in VALID_ROLES:
        print(f"  ✗ Invalid role")
        input("\n  Press Enter to continue...")
        return

    secondary_role = prompt("Secondary role (optional)", "")

    print(f"\n  Valid lanes: {', '.join(VALID_LANES)}")
    print("  Enter in priority order, comma-separated")
    lanes_input = prompt("Lane priority")
    lanes = [l.strip() for l in lanes_input.split(",") if l.strip()]
    invalid_lanes = [l for l in lanes if l not in VALID_LANES]
    if invalid_lanes:
        print(f"  ✗ Invalid lanes: {invalid_lanes}")
        input("\n  Press Enter to continue...")
        return

    # Build new hero structure
    new_hero = {
        "name": name,
        "image": image_url,
        "stats": {},
        "meta": {
            "attributes": {
                "combat": {f: 0 for f in ATTRIBUTE_SCHEMA["combat"]},
                "survivability": {f: 0 for f in ATTRIBUTE_SCHEMA["survivability"]},
                "utility": {f: 0 for f in ATTRIBUTE_SCHEMA["utility"]},
                "range_playstyle": {f: 0 for f in ATTRIBUTE_SCHEMA["range_playstyle"]},
                "power_curve": {f: 0 for f in ATTRIBUTE_SCHEMA["power_curve"]},
                "roles": {
                    "primary_role": primary_role,
                    "secondary_role": secondary_role,
                    "lane_priority": lanes,
                },
            },
            "reasoning": {
                "how_stats_influenced_scores": "",
                "how_skills_influenced_scores": "",
                "cooldown_impact": "",
                "special_passives_analysis": "",
                "final_role_justification": "",
            },
        },
    }

    print(f"\n  ✓ Hero template created for {name}")
    print("  Now fill in the attribute scores (0-5).\n")

    # Fill in each category
    for category in ATTRIBUTE_SCHEMA.keys():
        if confirm(f"  Fill in {category.replace('_', ' ')} now?"):
            update_attribute_category(new_hero, category)

    heroes.append(new_hero)

    if save_heroes(heroes):
        print(f"\n  ✓ {name} added successfully! ({len(heroes)} total heroes)")

        # Record in patch history
        current_patch = history.get("current_patch")
        if current_patch:
            for patch in history["patches"]:
                if patch["patch_version"] == current_patch:
                    patch["hero_updates"][name] = {
                        "updated_at": datetime.now().isoformat(),
                        "status": "new_hero",
                    }
                    break
            save_patch_history(history)
    else:
        print(f"\n  ✗ Failed to save")

    input("\n  Press Enter to continue...")


# ─────────────────────────────────────────────────────────────────────────────
# 4. VIEW HERO FLOW
# ─────────────────────────────────────────────────────────────────────────────


def view_hero_flow(heroes: List[Dict]):
    """View a hero's full current data"""
    clear()
    header("View Hero")

    name = prompt("Hero name")
    hero = find_hero(heroes, name)

    if not hero:
        print(f"\n  ✗ Hero '{name}' not found")
        input("\n  Press Enter to continue...")
        return

    meta = hero.get("meta", {})
    attrs = meta.get("attributes", {})
    roles = attrs.get("roles", {})

    print(f"\n  ┌─ {hero['name']} {'─' * (50 - len(hero['name']))}")
    print(f"  │  Role:   {roles.get('primary_role')} / {roles.get('secondary_role')}")
    print(f"  │  Lanes:  {', '.join(roles.get('lane_priority', []))}")
    print(f"  │  Image:  {hero.get('image', 'None')[:50]}")
    print(f"  └{'─' * 55}")

    for category, fields in ATTRIBUTE_SCHEMA.items():
        cat_data = attrs.get(category, {})
        print(f"\n  {category.replace('_', ' ').title()}:")
        for field in fields:
            val = cat_data.get(field, 0)
            bar = "█" * val + "░" * (5 - val)
            print(f"    {field:<25} {bar}  {val}/5")

    reasoning = meta.get("reasoning", {})
    if reasoning.get("final_role_justification"):
        subheader("Role Justification")
        print(f"  {reasoning['final_role_justification'][:200]}")

    input("\n  Press Enter to continue...")


# ─────────────────────────────────────────────────────────────────────────────
# 5. PATCH HISTORY FLOW
# ─────────────────────────────────────────────────────────────────────────────


def patch_history_flow(history: Dict):
    """View and manage patch history"""
    clear()
    header("Patch History")

    patches = history.get("patches", [])
    if not patches:
        print("  No patches recorded yet")
        print("  Use [1] New Patch to start tracking")
        input("\n  Press Enter to continue...")
        return

    print(f"  {'Patch':<12} {'Date':<14} {'Changed':<10} {'Status'}")
    print(f"  {'─'*12} {'─'*14} {'─'*10} {'─'*12}")

    for patch in reversed(patches[-10:]):  # Show last 10
        version = patch["patch_version"]
        date = patch.get("release_date", "?")
        changes = patch.get("changes", {})
        total_changed = sum(len(v) for v in changes.values() if isinstance(v, list))
        status = patch.get("status", "?")
        current = " ← current" if version == history.get("current_patch") else ""
        print(f"  {version:<12} {date:<14} {total_changed:<10} {status}{current}")

    print("\n  [1] View patch details")
    print("  [2] Mark current patch as complete")
    print("  [0] Back")

    choice = prompt("\n  Choice")

    if choice == "1":
        version = prompt("Patch version to view")
        for patch in patches:
            if patch["patch_version"] == version:
                _show_patch_details(patch)
                break
        else:
            print(f"  ✗ Patch {version} not found")

    elif choice == "2":
        current = history.get("current_patch")
        if current:
            for patch in history["patches"]:
                if patch["patch_version"] == current:
                    patch["status"] = "complete"
                    break
            save_patch_history(history)
            print(f"  ✓ Patch {current} marked complete")

    input("\n  Press Enter to continue...")


def _show_patch_details(patch: Dict):
    """Show detailed view of a single patch"""
    subheader(f"Patch {patch['patch_version']}")
    print(f"  Release date: {patch.get('release_date')}")
    print(f"  Status: {patch.get('status')}")

    if patch.get("notes_url"):
        print(f"  Notes: {patch['notes_url']}")

    changes = patch.get("changes", {})
    for change_type, heroes_list in changes.items():
        if heroes_list:
            print(f"\n  {change_type.title()}: {', '.join(heroes_list)}")

    updates = patch.get("hero_updates", {})
    if updates:
        print(f"\n  Updated ({len(updates)}):")
        for hero_name, info in updates.items():
            status = info.get("status", "done")
            date = info.get("updated_at", "")[:10]
            print(f"    ✓ {hero_name} ({status}) - {date}")

    # Find not yet updated
    all_changes = []
    for heroes_list in changes.values():
        if isinstance(heroes_list, list):
            all_changes.extend(heroes_list)

    pending = [h for h in all_changes if h not in updates]
    if pending:
        print(f"\n  Still pending ({len(pending)}):")
        for hero in pending:
            print(f"    ☐ {hero}")


# ─────────────────────────────────────────────────────────────────────────────
# 6. VALIDATE FLOW
# ─────────────────────────────────────────────────────────────────────────────


def validate_flow(heroes: List[Dict]):
    """Validate all heroes for structural and value errors"""
    clear()
    header("Validate Hero JSON")

    print(f"  Checking {len(heroes)} heroes...\n")

    errors = []
    warnings = []

    for hero in heroes:
        name = hero.get("name", "UNNAMED")
        meta = hero.get("meta", {})
        attrs = meta.get("attributes", {})

        # Check required top-level fields
        for field in ["name", "meta"]:
            if field not in hero:
                errors.append(f"{name}: Missing '{field}'")

        # Check all attribute categories
        for category, fields in ATTRIBUTE_SCHEMA.items():
            if category not in attrs:
                errors.append(f"{name}: Missing attributes.{category}")
                continue

            cat_data = attrs[category]
            for field in fields:
                if field not in cat_data:
                    warnings.append(f"{name}: Missing {category}.{field}")
                else:
                    val = cat_data[field]
                    if not isinstance(val, (int, float)):
                        errors.append(
                            f"{name}: {category}.{field} = '{val}' (not a number)"
                        )
                    elif not (0 <= val <= 5):
                        errors.append(
                            f"{name}: {category}.{field} = {val} (must be 0-5)"
                        )

        # Check roles
        roles = attrs.get("roles", {})
        if "primary_role" not in roles:
            errors.append(f"{name}: Missing roles.primary_role")
        elif roles["primary_role"] not in VALID_ROLES:
            errors.append(f"{name}: Invalid primary_role '{roles['primary_role']}'")

        if "lane_priority" not in roles:
            errors.append(f"{name}: Missing roles.lane_priority")
        else:
            for lane in roles["lane_priority"]:
                if lane not in VALID_LANES:
                    errors.append(f"{name}: Invalid lane '{lane}'")

    # Print results
    if not errors and not warnings:
        print(f"  ✓ All {len(heroes)} heroes are valid!")
    else:
        print(f"  ✗ Errors:   {len(errors)}")
        print(f"  ⚠ Warnings: {len(warnings)}")

        if errors:
            print("\n  ERRORS (must fix):")
            for e in errors[:20]:
                print(f"    ✗ {e}")
            if len(errors) > 20:
                print(f"    ... and {len(errors) - 20} more")

        if warnings:
            print("\n  WARNINGS (should fix):")
            for w in warnings[:10]:
                print(f"    ⚠ {w}")
            if len(warnings) > 10:
                print(f"    ... and {len(warnings) - 10} more")

    input("\n  Press Enter to continue...")


# ─────────────────────────────────────────────────────────────────────────────
# 7. PUSH TO DB FLOW
# ─────────────────────────────────────────────────────────────────────────────


def push_to_db_flow():
    """Load updated heroes into Neon database"""
    clear()
    header("Push to Database")

    print("  This will load final_heroes.json into your Neon database.")
    print("  Existing heroes will be updated, new ones will be created.\n")

    if not confirm("  Continue?"):
        return

    print("\n  Running load_heroes.py...\n")
    exit_code = os.system("python load_heroes.py")

    if exit_code == 0:
        print("\n  ✓ Database updated successfully!")
    else:
        print("\n  ✗ Database update failed. Check errors above.")

    input("\n  Press Enter to continue...")


# ─────────────────────────────────────────────────────────────────────────────
# 8. BACKUP FLOW
# ─────────────────────────────────────────────────────────────────────────────


def backup_flow():
    """Create a backup of the heroes file"""
    clear()
    header("Backup")

    try:
        backup_path = backup_heroes()
        print(f"\n  ✓ Backup created: {backup_path}")
    except Exception as e:
        print(f"\n  ✗ Backup failed: {e}")

    # Show existing backups
    backups = sorted(Path(".").glob("final_heroes_backup_*.json"), reverse=True)
    if backups:
        print(f"\n  Existing backups ({len(backups)}):")
        for b in backups[:5]:
            size = b.stat().st_size // 1024
            print(f"    {b.name} ({size} KB)")

    input("\n  Press Enter to continue...")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main_menu()
