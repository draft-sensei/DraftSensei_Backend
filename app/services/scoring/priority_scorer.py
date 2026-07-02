"""
Priority Scorer
Evaluates overall hero strength and meta viability
"""

from typing import Dict, Any
import logging

from ..config.draft_config import DraftConfig

logger = logging.getLogger(__name__)


class PriorityScorer:
    """Scores hero's overall strength and pick priority"""

    def __init__(self):
        self.config = DraftConfig()

    def calculate_pick_priority_score(self, hero: Dict[str, Any]) -> float:
        """
        Calculate pick priority based on overall hero strength (0-100)

        Considers:
        - Combat effectiveness (burst, sustained damage, DPS, AoE)
        - Survivability (tankiness, mobility, escape)
        - Power curve (early, mid, late game scaling)
        - Utility (crowd control)

        With penalties for heroes with suspiciously perfect stats.

        Args:
            hero: Hero data dictionary

        Returns:
            Priority score 0-100
        """
        hero_meta = hero.get("meta", {})
        combat = hero_meta.get("attributes", {}).get("combat", {})
        survivability = hero_meta.get("attributes", {}).get("survivability", {})
        power_curve = hero_meta.get("attributes", {}).get("power_curve", {})
        utility = hero_meta.get("attributes", {}).get("utility", {})

        # Average combat effectiveness
        combat_stats = [
            combat.get("burst_damage", 0),
            combat.get("sustained_damage", 0),
            combat.get("dps", 0),
            combat.get("aoe_damage", 0),
        ]
        combat_score = sum(combat_stats) / 4

        # Survivability score
        surv_stats = [
            survivability.get("tankiness", 0),
            survivability.get("mobility", 0),
            survivability.get("escape", 0),
        ]
        surv_score = sum(surv_stats) / 3

        # Power curve - balanced across game stages
        power_score = (
            power_curve.get("early_game", 0) * 0.2
            + power_curve.get("mid_game", 0) * 0.35
            + power_curve.get("late_game", 0) * 0.35
            + power_curve.get("scaling", 0) * 0.1
        )

        # Utility score
        utility_score = utility.get("crowd_control", 0)

        # Combined score with balanced weights
        priority = (
            combat_score * 0.35
            + surv_score * 0.25
            + power_score * 0.30
            + utility_score * 0.10
        ) * self.config.PRIORITY_SCALE

        # PENALTY: Heroes with suspiciously perfect stats
        perfect_stat_count = sum(1 for stat in combat_stats + surv_stats if stat >= 5)

        if perfect_stat_count >= 5:
            priority *= self.config.PERFECT_STAT_PENALTY_5
        elif perfect_stat_count >= 4:
            priority *= self.config.PERFECT_STAT_PENALTY_2
        elif perfect_stat_count >= 3:
            priority *= self.config.PERFECT_STAT_PENALTY_3

        return min(priority, 100)
