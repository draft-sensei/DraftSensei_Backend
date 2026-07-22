"""
Lane Selector
Determines which lane to fill based on what's missing.
Priority: Jungle > Mid > EXP > Gold > Roam (by game impact)
"""

from typing import Dict, Any, List, Tuple
import logging

from app.services.config.draft_config import DraftConfig
from .team_analyzer import TeamAnalyzer

logger = logging.getLogger(__name__)


class LaneSelector:
    """Selects the most important empty lane to fill next"""

    def __init__(self):
        self.config = DraftConfig()
        self.team_analyzer = TeamAnalyzer()

    def select_best_lane(
        self,
        banned_heroes: List[str],
        enemy_picks: List[str],
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> Tuple[str, str, str]:
        """
        Select which lane to fill next.

        Logic:
        1. Find all empty lanes
        2. Score each empty lane by:
           - Lane importance (Jungle=100, Mid=90, EXP=80, Gold=75, Roam=70)
           - Enemy threat in that lane
           - How much the team needs what that lane provides
        3. Return highest scoring empty lane

        Returns:
            Tuple of (lane_code, lane_name, reasoning)
        """
        # Step 1: Identify filled and empty lanes
        filled_lanes = self.team_analyzer.identify_filled_lanes(ally_picks, heroes_data)
        empty_lanes = [l for l in self.config.ALL_LANES if l not in filled_lanes]

        logger.info(
            f"Draft state: {len(ally_picks)} ally picks, {len(enemy_picks)} enemy picks"
        )
        logger.info(f"Filled lanes: {filled_lanes}")
        logger.info(f"Empty lanes:  {empty_lanes}")

        if not empty_lanes:
            # All lanes filled - shouldn't happen in normal draft
            logger.warning("All lanes are filled - defaulting to mid")
            return "mid", self.config.ROLE_MAP["mid"], "All lanes filled - flex pick"

        if len(empty_lanes) == 1:
            # Only one lane left - no decision needed
            lane = empty_lanes[0]
            lane_name = self.config.ROLE_MAP[lane]
            enemy_in_lane = self._get_enemy_in_lane(lane, enemy_picks, heroes_data)
            reasoning = self._build_reasoning(
                lane, filled_lanes, empty_lanes, enemy_in_lane, ally_picks, heroes_data
            )
            return lane, lane_name, reasoning

        # Step 2: Score each empty lane
        lane_scores = {}
        for lane in empty_lanes:
            score = self._score_lane(lane, enemy_picks, ally_picks, heroes_data)
            lane_scores[lane] = score
            logger.info(f"  Lane score [{lane}]: {score:.1f}")

        # Step 3: Pick highest scoring lane
        best_lane = max(lane_scores, key=lane_scores.get)
        best_lane_name = self.config.ROLE_MAP[best_lane]

        enemy_in_lane = self._get_enemy_in_lane(best_lane, enemy_picks, heroes_data)
        reasoning = self._build_reasoning(
            best_lane, filled_lanes, empty_lanes, enemy_in_lane, ally_picks, heroes_data
        )

        logger.info(f"Selected lane: {best_lane} ({best_lane_name})")
        return best_lane, best_lane_name, reasoning

    # ─────────────────────────────────────────────────────────────────────────
    # LANE SCORING
    # ─────────────────────────────────────────────────────────────────────────

    def _score_lane(
        self,
        lane: str,
        enemy_picks: List[str],
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> float:
        """
        Score an empty lane by three factors:

        1. Base importance   (50% weight) - Jungle always highest impact
        2. Enemy threat      (30% weight) - Dangerous enemy in this lane?
        3. Team need         (20% weight) - Does our team lack what this lane provides?
        """
        # Factor 1: Base lane importance (normalized to 0-1)
        base_importance = self.config.LANE_IMPORTANCE.get(lane, 50) / 100.0
        importance_score = base_importance * 50  # Scale to 0-50

        # Factor 2: Enemy threat in this lane
        enemy_threat = self.team_analyzer.assess_enemy_lane_threat(
            lane, enemy_picks, heroes_data
        )
        threat_score = enemy_threat * 30  # Scale to 0-30

        # Factor 3: Team composition need
        team_need = self._assess_team_need_for_lane(lane, ally_picks, heroes_data)
        need_score = team_need * 20  # Scale to 0-20

        total = importance_score + threat_score + need_score
        logger.debug(
            f"  [{lane}] importance={importance_score:.1f} threat={threat_score:.1f} need={need_score:.1f} total={total:.1f}"
        )

        return total

    def _assess_team_need_for_lane(
        self,
        lane: str,
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> float:
        """
        Assess how much the team needs what this lane typically provides (0-1).

        Each lane has a "contribution profile" - what it usually brings.
        If team is already strong in that area, need is lower.
        """
        if not ally_picks:
            return 0.5  # No picks yet - moderate need

        team_stats = self.team_analyzer._analyze_team_stats(ally_picks, heroes_data)

        # What each lane typically contributes to the team
        lane_contributions = {
            "exp": {
                "provides": "tankiness and engage",
                "check": lambda s: s["tankiness"] < self.config.TARGET_TANKINESS
                or s["engage"] < self.config.TARGET_ENGAGE,
            },
            "jungle": {
                "provides": "burst damage and mobility",
                "check": lambda s: s["burst"] < 8 or s["mobility"] < 6,
            },
            "mid": {
                "provides": "magic damage and CC",
                "check": lambda s: s["magic_damage"] < self.config.TARGET_MAGIC_DAMAGE
                or s["crowd_control"] < self.config.TARGET_CROWD_CONTROL,
            },
            "gold": {
                "provides": "physical damage and late game",
                "check": lambda s: s["physical_damage"]
                < self.config.TARGET_PHYSICAL_DAMAGE,
            },
            "roam": {
                "provides": "CC and team support",
                "check": lambda s: s["crowd_control"] < self.config.TARGET_CROWD_CONTROL
                or s["engage"] < self.config.TARGET_ENGAGE,
            },
        }

        contribution = lane_contributions.get(lane)
        if not contribution:
            return 0.5

        # If team is missing what this lane provides → high need
        if contribution["check"](team_stats):
            return 0.9
        else:
            return 0.3

    # ─────────────────────────────────────────────────────────────────────────
    # REASONING
    # ─────────────────────────────────────────────────────────────────────────

    def _get_enemy_in_lane(
        self,
        lane: str,
        enemy_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        """Find enemy heroes assigned to this lane"""
        lane_name = self.config.ROLE_MAP.get(lane, lane)
        result = []
        for enemy_name in enemy_picks:
            if enemy_name in heroes_data:
                meta = heroes_data[enemy_name].get("meta", {})
                lanes = (
                    meta.get("attributes", {}).get("roles", {}).get("lane_priority", [])
                )
                if lane_name in lanes:
                    result.append(enemy_name)
        return result

    def _build_reasoning(
        self,
        lane: str,
        filled_lanes: List[str],
        empty_lanes: List[str],
        enemy_in_lane: List[str],
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> str:
        """Build a clear explanation of why this lane was selected"""
        lane_name = self.config.ROLE_MAP.get(lane, lane)
        parts = []

        # Primary: why this lane is being picked
        if len(empty_lanes) == 1:
            parts.append(f"Last empty lane: {lane_name}")
        else:
            importance = self.config.LANE_IMPORTANCE.get(lane, 0)
            other_empty = [self.config.ROLE_MAP[l] for l in empty_lanes if l != lane]
            parts.append(f"Filling {lane_name} (highest priority empty lane)")
            if other_empty:
                parts.append(f"Also missing: {', '.join(other_empty)}")

        # Enemy threat
        if enemy_in_lane:
            parts.append(f"Counter enemy {', '.join(enemy_in_lane[:2])} in {lane_name}")

        # Team need
        team_stats = self.team_analyzer._analyze_team_stats(ally_picks, heroes_data)
        gaps = []
        if team_stats["tankiness"] < self.config.TARGET_TANKINESS:
            gaps.append("tankiness")
        if team_stats["magic_damage"] < 5:
            gaps.append("magic damage")
        if team_stats["burst"] < 8:
            gaps.append("burst damage")
        if team_stats["engage"] < self.config.TARGET_ENGAGE:
            gaps.append("engage")

        if gaps:
            parts.append(f"Team needs: {', '.join(gaps[:2])}")

        return " | ".join(parts)
