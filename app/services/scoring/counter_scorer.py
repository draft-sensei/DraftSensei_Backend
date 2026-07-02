"""
Counter Scorer
Evaluates how well a hero counters the enemy team composition
"""

from typing import Dict, Any, List
import logging

from ..config.draft_config import DraftConfig

logger = logging.getLogger(__name__)


class CounterScorer:
    """Scores hero's effectiveness against enemy team"""

    def __init__(self):
        self.config = DraftConfig()

    def calculate_counter_score(
        self,
        hero: Dict[str, Any],
        enemy_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> float:
        """
        Calculate how well hero counters enemy team (0-100)

        Logic:
        - High anti_squishy vs low tankiness enemies
        - High anti_tank vs high tankiness enemies
        - High mobility vs high crowd_control enemies
        - High poke vs short range enemies
        - High engage vs low mobility enemies
        - High burst vs low defense enemies

        Args:
            hero: Hero data dictionary
            enemy_picks: List of enemy hero names
            heroes_data: Dictionary of all heroes' data

        Returns:
            Counter score 0-100
        """
        if not enemy_picks:
            return 60.0  # Neutral score

        hero_meta = hero.get("meta", {})
        combat = hero_meta.get("attributes", {}).get("combat", {})
        survivability = hero_meta.get("attributes", {}).get("survivability", {})
        utility = hero_meta.get("attributes", {}).get("utility", {})
        range_style = hero_meta.get("attributes", {}).get("range_playstyle", {})

        total_counter_score = 0
        enemy_count = 0

        for enemy_name in enemy_picks:
            if enemy_name not in heroes_data:
                continue

            enemy = heroes_data[enemy_name]
            enemy_meta = enemy.get("meta", {})
            enemy_combat = enemy_meta.get("attributes", {}).get("combat", {})
            enemy_surv = enemy_meta.get("attributes", {}).get("survivability", {})
            enemy_util = enemy_meta.get("attributes", {}).get("utility", {})
            enemy_range = enemy_meta.get("attributes", {}).get("range_playstyle", {})

            counter_points = 0

            # Anti-squishy vs squishy enemies
            enemy_tankiness = enemy_surv.get("tankiness", 3)
            hero_anti_squishy = combat.get("anti_squishy", 0)
            if enemy_tankiness <= 2 and hero_anti_squishy >= 4:
                counter_points += hero_anti_squishy * 5
            elif enemy_tankiness <= 2 and hero_anti_squishy >= 3:
                counter_points += hero_anti_squishy * 3

            # Anti-tank vs tanky enemies
            hero_anti_tank = combat.get("anti_tank", 0)
            if enemy_tankiness >= 4 and hero_anti_tank >= 4:
                counter_points += hero_anti_tank * 5
            elif enemy_tankiness >= 4 and hero_anti_tank >= 3:
                counter_points += hero_anti_tank * 3

            # Mobility vs lockdown
            enemy_cc = enemy_util.get("crowd_control", 0)
            hero_mobility = survivability.get("mobility", 0)
            hero_escape = survivability.get("escape", 0)
            if enemy_cc >= 4 and (hero_mobility >= 4 or hero_escape >= 4):
                counter_points += 20
            elif enemy_cc >= 3 and (hero_mobility >= 3 or hero_escape >= 3):
                counter_points += 10

            # Poke vs short range
            enemy_range_val = enemy_range.get("range", 3)
            hero_poke = combat.get("poke", 0)
            if enemy_range_val <= 2 and hero_poke >= 4:
                counter_points += hero_poke * 4
            elif enemy_range_val <= 2 and hero_poke >= 3:
                counter_points += hero_poke * 2

            # Engage vs low mobility
            enemy_mobility = enemy_surv.get("mobility", 3)
            hero_engage = range_style.get("engage", 0)
            if enemy_mobility <= 2 and hero_engage >= 4:
                counter_points += hero_engage * 4

            # Burst damage vs low defense
            enemy_shields = enemy_surv.get("shields", 0)
            enemy_regen = enemy_surv.get("regen", 0)
            hero_burst = combat.get("burst_damage", 0)
            if (enemy_shields + enemy_regen <= 3) and hero_burst >= 4:
                counter_points += hero_burst * 4
            elif (enemy_shields + enemy_regen <= 3) and hero_burst >= 3:
                counter_points += hero_burst * 2

            total_counter_score += min(counter_points, 100)
            enemy_count += 1

        return total_counter_score / enemy_count if enemy_count > 0 else 60.0
