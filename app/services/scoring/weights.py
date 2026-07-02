"""
Dynamic Weight Calculation
Adjusts scoring weights based on current draft state
"""

from typing import Dict, List
import logging

from ..config.draft_config import DraftConfig

logger = logging.getLogger(__name__)


class WeightCalculator:
    """Calculates dynamic weights based on draft state"""

    def __init__(self):
        self.config = DraftConfig()
        self.base_weights = self.config.BASE_WEIGHTS.copy()

    def calculate_dynamic_weights(
        self,
        banned_heroes: List[str],
        enemy_picks: List[str],
        ally_picks: List[str],
        current_role: str,
        missing_roles: List[str] = None,
    ) -> Dict[str, float]:
        """
        Dynamically adjust scoring weights based on draft state.

        Adaptive Rules:
        1. Late draft (4+ picks) → ↑ team_comp, ↑ synergy, ↓ pick_priority
        2. Enemy pattern clear (3+ picks) → ↑ counter, ↓ synergy
        3. Missing critical role → ↑ role_fit significantly
        4. Many bans (6+) → ↑ pick_priority (avoid niche heroes)
        5. Win condition secured → ↑ synergy, ↓ counter

        Args:
            banned_heroes: List of banned heroes
            enemy_picks: Enemy team's picks
            ally_picks: Your team's picks
            current_role: The role being filled
            missing_roles: List of missing roles in team

        Returns:
            Dictionary of adjusted weights summing to 1.0
        """
        weights = self.base_weights.copy()
        total_picks = len(enemy_picks) + len(ally_picks)
        adjustments_applied = []

        # Rule 1: Late draft - focus on composition and synergy
        if total_picks >= self.config.EARLY_DRAFT_THRESHOLD:
            adj = self.config.WEIGHT_ADJUSTMENTS["late_draft"]
            weights["team_composition"] += adj["team_composition"]
            weights["synergy"] += adj["synergy"]
            weights["pick_priority"] += adj["pick_priority"]
            adjustments_applied.append("late_draft")

        # Rule 2: Enemy pattern clear - prioritize counters
        if len(enemy_picks) >= 3:
            adj = self.config.WEIGHT_ADJUSTMENTS["enemy_pattern_clear"]
            weights["counter"] += adj["counter"]
            weights["synergy"] += adj["synergy"]
            adjustments_applied.append("enemy_pattern_clear")

        # Rule 3: Check for missing critical roles
        if missing_roles and current_role:
            role_name = self.config.ROLE_MAP.get(current_role, current_role)
            if role_name in missing_roles:
                adj = self.config.WEIGHT_ADJUSTMENTS["missing_critical_role"]
                weights["role_fit"] += adj["role_fit"]
                weights["pick_priority"] += adj["pick_priority"]
                adjustments_applied.append("missing_critical_role")

        # Rule 4: Many bans - avoid weak niche picks
        if len(banned_heroes) >= 6:
            adj = self.config.WEIGHT_ADJUSTMENTS["many_bans"]
            weights["pick_priority"] += adj["pick_priority"]
            adjustments_applied.append("many_bans")

        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        if self.config.LOG_WEIGHT_CALCULATIONS:
            logger.info(f"Weight adjustments: {adjustments_applied}")
            logger.info(f"Final weights: {weights}")

        return weights
