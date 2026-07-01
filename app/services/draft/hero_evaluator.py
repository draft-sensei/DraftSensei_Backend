"""
Hero Evaluator
Scores individual heroes based on counter, synergy, composition, priority, and lane fit
"""

from typing import Dict, Any, List, Tuple
import logging

from ..config.draft_config import DraftConfig
from ..scoring.counter_scorer import CounterScorer
from ..scoring.synergy_scorer import SynergyScorer
from ..scoring.priority_scorer import PriorityScorer
from .team_analyzer import TeamAnalyzer
from ..scoring.weights import WeightCalculator

logger = logging.getLogger(__name__)


class HeroEvaluator:
    """Evaluates and scores individual heroes"""

    def __init__(self):
        self.config = DraftConfig()
        self.counter_scorer = CounterScorer()
        self.synergy_scorer = SynergyScorer()
        self.priority_scorer = PriorityScorer()
        self.team_analyzer = TeamAnalyzer()
        self.weight_calculator = WeightCalculator()

    def evaluate_hero(
        self,
        hero_name: str,
        hero: Dict[str, Any],
        banned_heroes: List[str],
        enemy_picks: List[str],
        ally_picks: List[str],
        current_role: str,
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> Tuple[float, List[str]]:
        """
        Calculate final score for a hero with dynamic weights.

        Args:
            hero_name: Name of hero
            hero: Hero data dictionary
            banned_heroes: Banned heroes
            enemy_picks: Enemy team picks
            ally_picks: Ally team picks
            current_role: Role being filled
            heroes_data: Dictionary of all heroes' data

        Returns:
            Tuple of (final_score, reasons_list)
        """
        reasons = []

        # Get missing roles for weight calculation
        missing_roles = self.team_analyzer.identify_missing_roles(
            ally_picks, heroes_data
        )

        # Get dynamic weights based on draft state
        weights = self.weight_calculator.calculate_dynamic_weights(
            banned_heroes, enemy_picks, ally_picks, current_role, missing_roles
        )

        # 1. Counter Score
        counter_score = self.counter_scorer.calculate_counter_score(
            hero, enemy_picks, heroes_data
        )
        if counter_score > self.config.COUNTER_THRESHOLD:
            reasons.append(
                f"Strong counter against enemy team ({counter_score:.0f}/100)"
            )

        # 2. Synergy Score
        synergy_score = self.synergy_scorer.calculate_synergy_score(
            hero, ally_picks, heroes_data
        )
        if synergy_score > self.config.SYNERGY_THRESHOLD:
            reasons.append(f"Excellent synergy with allies ({synergy_score:.0f}/100)")

        # 3. Team Composition Score
        comp_score = self.team_analyzer.analyze_composition_gap(
            hero, ally_picks, heroes_data
        )
        if comp_score > self.config.COMP_THRESHOLD:
            reasons.append("Fills critical team composition gap")

        # 4. Pick Priority Score
        priority_score = self.priority_scorer.calculate_pick_priority_score(hero)
        if priority_score > self.config.PRIORITY_THRESHOLD:
            reasons.append("High meta strength hero")

        # 5. Lane Fit Score
        lane_score = self._calculate_role_fit_score(hero, current_role)
        lane_name = self.config.ROLE_MAP.get(current_role, current_role)

        if lane_score >= 100:
            reasons.append(f"Primary lane: {lane_name}")
        elif lane_score >= 75:
            reasons.append(f"Viable for {lane_name}")
        elif lane_score >= 50:
            reasons.append(f"Situational pick for {lane_name}")
        elif lane_score < 30:
            reasons.append(f"Not suited for {lane_name}")

        # Calculate weighted final score using dynamic weights
        final_score = (
            counter_score * weights["counter"]
            + synergy_score * weights["synergy"]
            + comp_score * weights["team_composition"]
            + priority_score * weights["pick_priority"]
            + lane_score * weights["role_fit"]
        )

        # Add top tier indicator
        if final_score > 80:
            reasons.insert(0, f"Top tier pick (Score: {final_score:.1f})")

        return final_score, reasons[: self.config.REASONS_PER_HERO]

    def _calculate_role_fit_score(
        self, hero: Dict[str, Any], current_role: str
    ) -> float:
        """
        Calculate how well hero fits the requested lane (0-100).

        Based on lane_priority from meta data (most accurate indicator).

        Args:
            hero: Hero data dictionary
            current_role: Role code (exp, jungle, mid, gold, roam)

        Returns:
            Role fit score 0-100
        """
        hero_meta = hero.get("meta", {})
        roles = hero_meta.get("attributes", {}).get("roles", {})

        lane_priorities = roles.get("lane_priority", [])
        target_lane = self.config.ROLE_MAP.get(current_role, current_role)

        # Primary scoring: Lane priority is the most accurate indicator
        if target_lane in lane_priorities:
            lane_index = lane_priorities.index(target_lane)
            if lane_index == 0:
                return self.config.LANE_FIT_PRIMARY
            elif lane_index == 1:
                return self.config.LANE_FIT_SECONDARY
            elif lane_index == 2:
                return self.config.LANE_FIT_TERTIARY
            else:
                return self.config.LANE_FIT_LOWER

        return self.config.LANE_FIT_NO_MATCH
