"""
Lane Selector
Determines which lane should be picked based on current draft state
"""

from typing import Dict, Any, List
import logging

from ..config.draft_config import DraftConfig
from .team_analyzer import TeamAnalyzer

logger = logging.getLogger(__name__)


class LaneSelector:
    """Selects the best lane to pick next"""

    def __init__(self):
        self.config = DraftConfig()
        self.team_analyzer = TeamAnalyzer()

    def select_best_lane(
        self,
        banned_heroes: List[str],
        enemy_picks: List[str],
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> tuple:
        """
        Select the best lane to pick for the current draft phase.

        Returns the recommended lane and explanation.

        Args:
            banned_heroes: Banned heroes
            enemy_picks: Enemy team picks
            ally_picks: Ally team picks
            heroes_data: Dictionary of all heroes' data

        Returns:
            Tuple of (lane_code, lane_name, reasoning)
        """
        # Determine draft phase
        total_picks = len(enemy_picks) + len(ally_picks)
        is_early_draft = total_picks <= self.config.EARLY_DRAFT_THRESHOLD

        if is_early_draft and not ally_picks:
            # First pick: grab meta priority heroes
            recommended_lane = self._get_meta_priority_lane(
                enemy_picks, banned_heroes, heroes_data
            )
            reasoning = f"First pick: Secure high-impact {self.config.ROLE_MAP.get(recommended_lane)} hero to establish early advantage"
        else:
            # Mid/late draft: counter enemies and fill composition gaps
            open_lanes = self.team_analyzer.identify_open_lanes(ally_picks, heroes_data)
            recommended_lane = self._get_strategic_lane(
                enemy_picks, ally_picks, open_lanes, banned_heroes, heroes_data
            )
            reasoning = self._explain_lane_choice(
                recommended_lane, enemy_picks, ally_picks, open_lanes, heroes_data
            )

        lane_name = self.config.ROLE_MAP.get(recommended_lane, recommended_lane)
        return recommended_lane, lane_name, reasoning

    def _get_meta_priority_lane(
        self,
        enemy_picks: List[str],
        banned_heroes: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> str:
        """
        First pick strategy: get meta priority heroes.
        Priority order: Jungle > Mid > EXP > Gold > Roam

        Args:
            enemy_picks: Enemy team picks
            banned_heroes: Banned heroes
            heroes_data: Dictionary of all heroes' data

        Returns:
            Lane code for first pick
        """
        # If enemy already picked, counter their lane
        if enemy_picks:
            enemy_hero = enemy_picks[0]
            if enemy_hero in heroes_data:
                enemy = heroes_data[enemy_hero]
                enemy_meta = enemy.get("meta", {})
                enemy_lanes = (
                    enemy_meta.get("attributes", {})
                    .get("roles", {})
                    .get("lane_priority", [])
                )
                if enemy_lanes:
                    enemy_lane_code = self.team_analyzer._lane_to_code(enemy_lanes[0])
                    # Counter-pick same lane if it's high priority
                    if enemy_lane_code in ["jungle", "mid"]:
                        return enemy_lane_code

        # Default first pick priority
        return "jungle"  # Jungle has highest impact

    def _get_strategic_lane(
        self,
        enemy_picks: List[str],
        ally_picks: List[str],
        open_lanes: List[str],
        banned_heroes: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> str:
        """
        Strategic lane selection based on:
        1. Counter enemy threats
        2. Fill critical team composition gaps
        3. Secure remaining priority lanes

        Args:
            enemy_picks: Enemy team picks
            ally_picks: Ally team picks
            open_lanes: Available lanes
            banned_heroes: Banned heroes
            heroes_data: Dictionary of all heroes' data

        Returns:
            Recommended lane code
        """
        if not open_lanes:
            return "mid"

        # Score each open lane
        lane_scores = {}

        for lane in open_lanes:
            score = 0

            # 1. Counter priority
            enemy_lane_threat = self.team_analyzer.assess_enemy_lane_threat(
                lane, enemy_picks, heroes_data
            )
            score += enemy_lane_threat * 40

            # 2. Composition gap
            comp_need = self._assess_composition_need(lane, ally_picks, heroes_data)
            score += comp_need * 35

            # 3. Lane priority
            lane_importance = self.config.LANE_IMPORTANCE.get(lane, 50)
            score += (lane_importance / 100) * 25

            lane_scores[lane] = score

        best_lane = max(lane_scores, key=lane_scores.get)
        return best_lane

    def _assess_composition_need(
        self,
        lane: str,
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> float:
        """
        Assess how much team needs this lane (0-1).

        Args:
            lane: Lane code
            ally_picks: Ally team picks
            heroes_data: Dictionary of all heroes' data

        Returns:
            Need score 0-1.0
        """
        if not ally_picks:
            return 0.5

        # Analyze current team composition
        team_stats = {
            "tankiness": 0,
            "physical_damage": 0,
            "magic_damage": 0,
            "crowd_control": 0,
        }

        for ally_name in ally_picks:
            if ally_name in heroes_data:
                ally = heroes_data[ally_name]
                ally_meta = ally.get("meta", {})
                ally_combat = ally_meta.get("attributes", {}).get("combat", {})
                ally_surv = ally_meta.get("attributes", {}).get("survivability", {})
                ally_util = ally_meta.get("attributes", {}).get("utility", {})
                ally_roles = ally_meta.get("attributes", {}).get("roles", {})

                team_stats["tankiness"] += ally_surv.get("tankiness", 0)
                team_stats["crowd_control"] += ally_util.get("crowd_control", 0)

                role = ally_roles.get("primary_role", "")
                if role == "Mage":
                    team_stats["magic_damage"] += 5
                else:
                    team_stats["physical_damage"] += 5

        # Determine what this lane typically provides
        lane_contributions = {
            "exp": {"tankiness": 0.8, "physical_damage": 0.6, "crowd_control": 0.5},
            "jungle": {"physical_damage": 0.9, "mobility": 0.8},
            "mid": {"magic_damage": 0.9, "crowd_control": 0.4},
            "gold": {"physical_damage": 0.9, "late_game": 0.9},
            "roam": {"tankiness": 0.9, "crowd_control": 0.8},
        }

        contributions = lane_contributions.get(lane, {})
        need_score = 0

        # Check gaps
        if team_stats["tankiness"] < 8 and contributions.get("tankiness", 0) > 0.5:
            need_score += 0.4
        if (
            team_stats["magic_damage"] < 5
            and contributions.get("magic_damage", 0) > 0.5
        ):
            need_score += 0.3
        if (
            team_stats["physical_damage"] < 10
            and contributions.get("physical_damage", 0) > 0.5
        ):
            need_score += 0.3

        return min(need_score, 1.0)

    def _explain_lane_choice(
        self,
        lane: str,
        enemy_picks: List[str],
        ally_picks: List[str],
        open_lanes: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> str:
        """Generate explanation for lane choice"""
        lane_name = self.config.ROLE_MAP.get(lane, lane)
        reasons = []

        # Check enemy threats
        enemy_in_lane = []
        for enemy_name in enemy_picks:
            if enemy_name in heroes_data:
                enemy = heroes_data[enemy_name]
                enemy_meta = enemy.get("meta", {})
                enemy_lanes = (
                    enemy_meta.get("attributes", {})
                    .get("roles", {})
                    .get("lane_priority", [])
                )
                if lane_name in enemy_lanes:
                    enemy_in_lane.append(enemy_name)

        if enemy_in_lane:
            reasons.append(
                f"Counter enemy {', '.join(enemy_in_lane[:2])} in {lane_name}"
            )

        # Check team gaps
        if len(ally_picks) >= 2:
            reasons.append(f"Fill remaining {lane_name} position")

        if not reasons:
            reasons.append(
                f"Strategic pick for {lane_name} to strengthen team composition"
            )

        return " | ".join(reasons)
