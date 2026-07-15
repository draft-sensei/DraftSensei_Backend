"""
Lane Selector
Determines which lane should be picked based on current draft state
Prioritizes completely empty lanes over partial composition
"""

from typing import Dict, Any, List, Tuple
import logging

from app.services.config.draft_config import DraftConfig
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

        PRIORITY: Fill completely empty lanes first (by impact)

        Example:
          If team has: Gold Lane, Roam, Exp Lane
          Missing: Jungle, Mid Lane
          → Pick Jungle (highest impact among missing)

        Returns the recommended lane and explanation.

        Args:
            banned_heroes: Banned heroes
            enemy_picks: Enemy team picks
            ally_picks: Ally team picks
            heroes_data: Dictionary of all heroes' data

        Returns:
            Tuple of (lane_code, lane_name, reasoning)
        """
        # Step 1: Identify which lanes are filled vs empty
        filled_lanes = self._identify_filled_lanes(ally_picks, heroes_data)
        empty_lanes = [
            lane for lane in self.config.ALL_LANES if lane not in filled_lanes
        ]

        logger.info(f"Filled lanes: {filled_lanes}")
        logger.info(f"Empty lanes: {empty_lanes}")

        # Step 2: Prioritize empty lanes by importance
        if empty_lanes:
            # Pick the most important empty lane
            recommended_lane = self._get_highest_priority_empty_lane(empty_lanes)
            reasoning = self._explain_lane_selection(
                recommended_lane,
                filled_lanes,
                empty_lanes,
                enemy_picks,
                ally_picks,
                heroes_data,
            )
        else:
            # All lanes filled (shouldn't happen in normal draft)
            # Fall back to strategic lane replacement
            recommended_lane = self._get_strategic_lane_replacement(
                enemy_picks, ally_picks, heroes_data
            )
            reasoning = f"All lanes filled - strategic {self.config.ROLE_MAP.get(recommended_lane)} replacement"

        lane_name = self.config.ROLE_MAP.get(recommended_lane, recommended_lane)
        return recommended_lane, lane_name, reasoning

    def _identify_filled_lanes(
        self, ally_picks: List[str], heroes_data: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """
        Identify which lanes are already filled by ally picks.

        A lane is "filled" if at least one ally hero can/should play there.

        Args:
            ally_picks: Current ally team picks
            heroes_data: Dictionary of all heroes' data

        Returns:
            List of filled lane codes
        """
        filled_lanes = set()

        for hero_name in ally_picks:
            if hero_name in heroes_data:
                hero = heroes_data[hero_name]
                meta = hero.get("meta", {})
                lane_priority = (
                    meta.get("attributes", {}).get("roles", {}).get("lane_priority", [])
                )

                if lane_priority:
                    # Assume primary lane (first in priority list)
                    primary_lane = lane_priority[0]
                    lane_code = self._lane_name_to_code(primary_lane)
                    filled_lanes.add(lane_code)
                    logger.debug(f"{hero_name} fills {primary_lane} ({lane_code})")

        return list(filled_lanes)

    def _get_highest_priority_empty_lane(self, empty_lanes: List[str]) -> str:
        """
        Get the most important empty lane based on impact.

        Priority: Jungle > Mid > Exp > Gold > Roam

        Args:
            empty_lanes: List of empty lane codes

        Returns:
            Lane code with highest importance
        """
        # Sort by importance (descending)
        sorted_lanes = sorted(
            empty_lanes,
            key=lambda lane: self.config.LANE_IMPORTANCE.get(lane, 0),
            reverse=True,
        )

        best_lane = sorted_lanes[0]
        importance = self.config.LANE_IMPORTANCE.get(best_lane, 0)

        logger.info(f"Selected priority lane: {best_lane} (importance: {importance})")
        return best_lane

    def _explain_lane_selection(
        self,
        lane: str,
        filled_lanes: List[str],
        empty_lanes: List[str],
        enemy_picks: List[str],
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> str:
        """Generate detailed explanation for lane choice"""
        lane_name = self.config.ROLE_MAP.get(lane, lane)
        reasons = []

        # Primary reason: lane was empty and has high priority
        lane_importance = self.config.LANE_IMPORTANCE.get(lane, 0)
        empty_lane_count = len(empty_lanes)

        if empty_lane_count == 1:
            reasons.append(f"Only empty lane remaining: {lane_name}")
        else:
            reasons.append(
                f"Highest priority empty lane: {lane_name} (importance: {lane_importance})"
            )

        # Secondary: what enemies are in this lane?
        enemy_in_lane = self._find_enemy_in_lane(lane, enemy_picks, heroes_data)
        if enemy_in_lane:
            reasons.append(
                f"Enemy threat: {', '.join(enemy_in_lane[:2])} in {lane_name}"
            )

        # Tertiary: what does team need?
        team_need = self._describe_team_need_for_lane(lane, ally_picks, heroes_data)
        if team_need:
            reasons.append(team_need)

        return " | ".join(reasons)

    def _find_enemy_in_lane(
        self,
        lane: str,
        enemy_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        """Find which enemy heroes can/should play in this lane"""
        lane_name = self.config.ROLE_MAP.get(lane, lane)
        enemy_in_lane = []

        for enemy_name in enemy_picks:
            if enemy_name in heroes_data:
                enemy = heroes_data[enemy_name]
                meta = enemy.get("meta", {})
                lane_priority = (
                    meta.get("attributes", {}).get("roles", {}).get("lane_priority", [])
                )

                if lane_name in lane_priority:
                    enemy_in_lane.append(enemy_name)

        return enemy_in_lane

    def _describe_team_need_for_lane(
        self,
        lane: str,
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> str:
        """Describe what team needs for this lane"""
        # Analyze current team composition
        team_stats = self._analyze_team_stats(ally_picks, heroes_data)

        lane_needs = {
            "exp": "Tank/durability",
            "jungle": "Mobility & gap close",
            "mid": "Magic damage or CC",
            "gold": "Physical damage & scaling",
            "roam": "Support abilities & vision",
        }

        lane_name = self.config.ROLE_MAP.get(lane, lane)
        need = lane_needs.get(lane, "")

        # Check if team is missing this
        critical_gaps = self._identify_critical_team_gaps(team_stats)

        if critical_gaps:
            return f"Team needs: {', '.join(critical_gaps)}"

        return ""

    def _analyze_team_stats(
        self,
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> Dict[str, float]:
        """Analyze team composition stats"""
        team_stats = {
            "tankiness": 0,
            "physical_damage": 0,
            "magic_damage": 0,
            "crowd_control": 0,
            "mobility": 0,
            "engage": 0,
        }

        for ally_name in ally_picks:
            if ally_name in heroes_data:
                ally = heroes_data[ally_name]
                meta = ally.get("meta", {})
                attrs = meta.get("attributes", {})

                combat = attrs.get("combat", {})
                surv = attrs.get("survivability", {})
                util = attrs.get("utility", {})
                range_style = attrs.get("range_playstyle", {})

                team_stats["tankiness"] += surv.get("tankiness", 0)
                team_stats["crowd_control"] += util.get("crowd_control", 0)
                team_stats["mobility"] += surv.get("mobility", 0)
                team_stats["engage"] += range_style.get("engage", 0)

                # Damage type
                role = attrs.get("roles", {}).get("primary_role", "")
                if role == "Mage":
                    team_stats["magic_damage"] += combat.get("dps", 0)
                else:
                    team_stats["physical_damage"] += combat.get("dps", 0)

        return team_stats

    def _identify_critical_team_gaps(self, team_stats: Dict[str, float]) -> List[str]:
        """Identify critical gaps in team composition"""
        gaps = []

        if team_stats["tankiness"] < self.config.TARGET_TANKINESS:
            gaps.append("Tank/durability")
        if team_stats["magic_damage"] < 5:
            gaps.append("Magic damage")
        if team_stats["physical_damage"] < 5:
            gaps.append("Physical damage")
        if team_stats["crowd_control"] < 3:
            gaps.append("CC/Disable")
        if team_stats["mobility"] < 5:
            gaps.append("Mobility/Chase")

        return gaps

    def _get_strategic_lane_replacement(
        self,
        enemy_picks: List[str],
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> str:
        """
        Get a strategic lane when all are already filled.
        (Shouldn't happen in normal draft, but fallback just in case)
        """
        # Check which lane has weakest counter coverage
        return "mid"  # Default fallback

    def _lane_name_to_code(self, lane_name: str) -> str:
        """Convert lane name to code"""
        reverse_map = self.config.REVERSE_ROLE_MAP
        return reverse_map.get(lane_name, lane_name.lower())
