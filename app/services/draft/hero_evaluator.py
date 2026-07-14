"""
Hero Evaluator
Scores individual heroes based on counter, synergy, composition, priority, and lane fit
Uses lane-specific weights for more accurate recommendations
"""

from typing import Dict, Any, List, Tuple
import logging

from app.services.config.draft_config import DraftConfig
from app.services.scoring.counter_scorer import CounterScorer
from app.services.scoring.synergy_scorer import SynergyScorer
from app.services.scoring.priority_scorer import PriorityScorer
from .team_analyzer import TeamAnalyzer
from app.services.scoring.weights import WeightCalculator

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
        Calculate final score for a hero with lane-specific weights.

        Args:
            hero_name: Name of hero
            hero: Hero data dictionary
            banned_heroes: Banned heroes
            enemy_picks: Enemy team picks
            ally_picks: Ally team picks
            current_role: Lane code being filled (exp, jungle, mid, gold, roam)
            heroes_data: Dictionary of all heroes' data

        Returns:
            Tuple of (final_score, reasons_list)
        """
        reasons = []

        # Get missing roles for weight calculation
        missing_roles = self.team_analyzer.identify_missing_roles(
            ally_picks, heroes_data
        )

        # Get lane-specific weights (not just base weights)
        weights = self._get_lane_specific_weights(
            current_role, banned_heroes, enemy_picks, ally_picks, missing_roles
        )

        # Calculate individual scores
        counter_score = self.counter_scorer.calculate_counter_score(
            hero, enemy_picks, heroes_data
        )
        synergy_score = self.synergy_scorer.calculate_synergy_score(
            hero, ally_picks, heroes_data
        )
        comp_score = self.team_analyzer.analyze_composition_gap(
            hero, ally_picks, heroes_data
        )
        priority_score = self.priority_scorer.calculate_pick_priority_score(hero)
        lane_score = self._calculate_role_fit_score(hero, current_role)

        # Add reasons based on scores and lane
        lane_name = self.config.ROLE_MAP.get(current_role, current_role)

        # Always add lane fit reason
        if lane_score >= 100:
            reasons.append(f"Primary {lane_name} hero")
        elif lane_score >= 75:
            reasons.append(f"Good fit for {lane_name}")
        elif lane_score < 30:
            reasons.append(f"❌ Not suited for {lane_name}")
            # Don't suggest heroes who can't play the lane
            return 0, [f"Cannot play {lane_name}"]

        # Add other reasons based on lane context
        if counter_score > self.config.COUNTER_THRESHOLD:
            reasons.append(f"Counters enemies ({counter_score:.0f}/100)")

        if synergy_score > self.config.SYNERGY_THRESHOLD:
            reasons.append(f"Great team synergy ({synergy_score:.0f}/100)")

        if comp_score > self.config.COMP_THRESHOLD:
            reasons.append(f"Fills team gaps ({comp_score:.0f}/100)")

        if priority_score > self.config.PRIORITY_THRESHOLD:
            reasons.append(f"Strong meta pick")

        # Calculate weighted final score using LANE-SPECIFIC weights
        final_score = (
            counter_score * weights["counter"]
            + synergy_score * weights["synergy"]
            + comp_score * weights["team_composition"]
            + priority_score * weights["pick_priority"]
            + lane_score * weights["role_fit"]
        )

        # Boost score if hero fills critical team gap for this lane
        team_stats = self.team_analyzer._analyze_team_stats(ally_picks, heroes_data)
        if self._hero_covers_critical_gap(hero, team_stats, current_role):
            final_score *= 1.15  # 15% boost for filling critical gap
            if not reasons[0].startswith("Top tier"):
                reasons.insert(0, "✓ Covers critical team gap")

        # Add top tier indicator
        if final_score > 80:
            reasons.insert(0, f"Top tier pick for {lane_name}")

        return final_score, reasons[: self.config.REASONS_PER_HERO]

    def _get_lane_specific_weights(
        self,
        lane: str,
        banned_heroes: List[str],
        enemy_picks: List[str],
        ally_picks: List[str],
        missing_roles: List[str],
    ) -> Dict[str, float]:
        """
        Get weights specific to the lane being filled.

        Different lanes have different priorities:
        - Jungle: Team composition > Synergy > Priority > Counter
        - Mid: Counter > Synergy > Composition > Priority
        - EXP: Composition > Synergy > Counter > Priority
        - Gold: Composition > Counter > Synergy > Priority
        - Roam: Synergy > Composition > Priority > Counter

        Args:
            lane: Lane code
            banned_heroes: Banned heroes
            enemy_picks: Enemy team picks
            ally_picks: Ally team picks
            missing_roles: Missing roles in team

        Returns:
            Dictionary of adjusted weights summing to 1.0
        """
        # Get base lane-specific weights
        if lane in self.config.LANE_WEIGHTS:
            weights = self.config.LANE_WEIGHTS[lane].copy()
        else:
            weights = self.config.BASE_WEIGHTS.copy()

        logger.debug(f"Base weights for {lane}: {weights}")

        # Apply dynamic adjustments (late game, enemy pattern, etc)
        total_picks = len(enemy_picks) + len(ally_picks)

        # Late draft: increase team composition weight
        if total_picks >= self.config.EARLY_DRAFT_THRESHOLD:
            weights["team_composition"] += 0.05
            weights["pick_priority"] -= 0.05

        # Enemy pattern clear: boost counter for mid/gold lanes
        if len(enemy_picks) >= 3 and lane in ["mid", "gold"]:
            weights["counter"] += 0.10
            weights["synergy"] -= 0.05

        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        logger.debug(f"Final weights for {lane}: {weights}")
        return weights

    def _hero_covers_critical_gap(
        self,
        hero: Dict[str, Any],
        team_stats: Dict[str, float],
        lane: str,
    ) -> bool:
        """
        Check if this hero covers a critical gap for the lane being filled.

        Examples:
        - Jungle: Team needs mobility? Check hero has high mobility
        - EXP: Team needs tankiness? Check hero has high tankiness
        - Roam: Team needs CC? Check hero has CC
        """
        hero_meta = hero.get("meta", {})
        attrs = hero_meta.get("attributes", {})

        combat = attrs.get("combat", {})
        surv = attrs.get("survivability", {})
        util = attrs.get("utility", {})
        range_style = attrs.get("range_playstyle", {})

        # Define what each lane "solves"
        lane_solutions = {
            "jungle": {"mobility": 4, "damage": 4},  # Need mobile, high damage
            "mid": {"damage": 4, "cc": 3},  # Need damage and CC
            "exp": {"tankiness": 4, "engage": 3},  # Need tank and engage
            "gold": {"damage": 4, "late_game": 4},  # Need DPS and scaling
            "roam": {"cc": 3, "support": 3},  # Need CC and support
        }

        solutions = lane_solutions.get(lane, {})

        # Check if hero provides needed attributes
        for attr, threshold in solutions.items():
            if attr == "mobility":
                if surv.get("mobility", 0) >= threshold:
                    return True
            elif attr == "damage":
                dps = combat.get("dps", 0)
                if dps >= threshold:
                    return True
            elif attr == "cc":
                if util.get("crowd_control", 0) >= threshold:
                    return True
            elif attr == "tankiness":
                if surv.get("tankiness", 0) >= threshold:
                    return True
            elif attr == "engage":
                if range_style.get("engage", 0) >= threshold:
                    return True
            elif attr == "support":
                heal = util.get("team_heal", 0)
                buff = util.get("team_buff", 0)
                if heal >= 3 or buff >= 3:
                    return True
            elif attr == "late_game":
                power = attrs.get("power_curve", {})
                if power.get("late_game", 0) >= threshold:
                    return True

        return False

    def _calculate_role_fit_score(
        self, hero: Dict[str, Any], current_role: str
    ) -> float:
        """
        Calculate how well hero fits the requested lane (0-100).

        Based on lane_priority from meta data.
        Only heroes who can actually play the lane should score high.

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

        # Check if hero can actually play this lane
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

        # Hero can't play this lane
        return self.config.LANE_FIT_NO_MATCH
