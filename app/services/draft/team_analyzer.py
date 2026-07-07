"""
Team Analyzer
Analyzes team composition and identifies critical gaps
"""

from typing import Dict, Any, List
import logging

from ..config.draft_config import DraftConfig

logger = logging.getLogger(__name__)


class TeamAnalyzer:
    """Analyzes team composition and identifies gaps"""

    def __init__(self):
        self.config = DraftConfig()

    def identify_open_lanes(
        self, ally_picks: List[str], heroes_data: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """
        Identify which lanes are still available for our team.

        Args:
            ally_picks: Current ally team picks
            heroes_data: Dictionary of all heroes' data

        Returns:
            List of open lane codes (exp, jungle, mid, gold, roam)
        """
        filled_lanes = set()

        for hero_name in ally_picks:
            if hero_name in heroes_data:
                hero = heroes_data[hero_name]
                meta = hero.get("meta", {})
                lanes = (
                    meta.get("attributes", {}).get("roles", {}).get("lane_priority", [])
                )
                if lanes:
                    # Assume hero takes their primary lane
                    primary_lane = lanes[0]
                    lane_code = self._lane_to_code(primary_lane)
                    filled_lanes.add(lane_code)

        open_lanes = [
            lane for lane in self.config.ALL_LANES if lane not in filled_lanes
        ]
        return open_lanes

    def identify_missing_roles(
        self, ally_picks: List[str], heroes_data: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """
        Identify which lanes/roles are missing from team.

        Args:
            ally_picks: Current ally team picks
            heroes_data: Dictionary of all heroes' data

        Returns:
            List of missing lane names (e.g., "EXP Lane", "Jungle")
        """
        filled_roles = set()

        for hero_name in ally_picks:
            if hero_name in heroes_data:
                hero = heroes_data[hero_name]
                meta = hero.get("meta", {})
                lanes = (
                    meta.get("attributes", {}).get("roles", {}).get("lane_priority", [])
                )
                if lanes:
                    filled_roles.add(lanes[0])  # Primary lane

        all_lanes = list(self.config.ROLE_MAP.values())
        missing = [lane for lane in all_lanes if lane not in filled_roles]

        return missing

    def analyze_composition_gap(
        self,
        hero: Dict[str, Any],
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> float:
        """
        Calculate how well hero fills team composition gaps (0-100).

        Checks for:
        - Missing tankiness
        - Missing magic damage
        - Missing physical damage
        - Missing crowd control
        - Missing engage
        - Missing waveclear
        - Role redundancy penalty

        Args:
            hero: Hero data dictionary
            ally_picks: Current ally team picks
            heroes_data: Dictionary of all heroes' data

        Returns:
            Composition gap score 0-100
        """
        hero_meta = hero.get("meta", {})
        combat = hero_meta.get("attributes", {}).get("combat", {})
        survivability = hero_meta.get("attributes", {}).get("survivability", {})
        utility = hero_meta.get("attributes", {}).get("utility", {})
        range_style = hero_meta.get("attributes", {}).get("range_playstyle", {})
        roles = hero_meta.get("attributes", {}).get("roles", {})

        # Analyze current team composition
        team_stats = {
            "tankiness": 0,
            "magic_damage": 0,
            "physical_damage": 0,
            "crowd_control": 0,
            "engage": 0,
            "waveclear": 0,
            "peel": 0,
            "burst": 0,
            "sustained": 0,
        }

        for ally_name in ally_picks:
            if ally_name not in heroes_data:
                continue

            ally = heroes_data[ally_name]
            ally_meta = ally.get("meta", {})
            ally_combat = ally_meta.get("attributes", {}).get("combat", {})
            ally_surv = ally_meta.get("attributes", {}).get("survivability", {})
            ally_util = ally_meta.get("attributes", {}).get("utility", {})
            ally_range = ally_meta.get("attributes", {}).get("range_playstyle", {})
            ally_roles = ally_meta.get("attributes", {}).get("roles", {})

            team_stats["tankiness"] += ally_surv.get("tankiness", 0)
            team_stats["crowd_control"] += ally_util.get("crowd_control", 0)
            team_stats["engage"] += ally_range.get("engage", 0)
            team_stats["waveclear"] += ally_range.get("waveclear", 0)
            team_stats["peel"] += ally_range.get("peel", 0)
            team_stats["burst"] += ally_combat.get("burst_damage", 0)
            team_stats["sustained"] += ally_combat.get("sustained_damage", 0)

            # Determine if physical or magic damage
            primary_role = ally_roles.get("primary_role", "")
            if primary_role in ["Mage"]:
                team_stats["magic_damage"] += ally_combat.get("dps", 0)
            else:
                team_stats["physical_damage"] += ally_combat.get("dps", 0)

        # Calculate gaps
        gaps_filled = 0
        max_gaps = 0

        # Tankiness gap (critical if < 8 for team of 2+)
        if (
            len(ally_picks) >= 2
            and team_stats["tankiness"] < self.config.TARGET_TANKINESS
        ):
            max_gaps += 15
            if survivability.get("tankiness", 0) >= 4:
                gaps_filled += 15

        # Magic damage gap
        if team_stats["magic_damage"] < self.config.TARGET_MAGIC_DAMAGE:
            max_gaps += 15
            if roles.get("primary_role") == "Mage":
                gaps_filled += 15

        # Physical damage gap
        if team_stats["physical_damage"] < self.config.TARGET_PHYSICAL_DAMAGE:
            max_gaps += 15
            if roles.get("primary_role") in ["Marksman", "Assassin", "Fighter"]:
                gaps_filled += 15

        # Crowd control gap
        if team_stats["crowd_control"] < self.config.TARGET_CROWD_CONTROL:
            max_gaps += 10
            if utility.get("crowd_control", 0) >= 3:
                gaps_filled += 10

        # Engage gap
        if team_stats["engage"] < self.config.TARGET_ENGAGE:
            max_gaps += 12
            if range_style.get("engage", 0) >= 4:
                gaps_filled += 12

        # Waveclear gap
        if team_stats["waveclear"] < self.config.TARGET_WAVECLEAR:
            max_gaps += 8
            if range_style.get("waveclear", 0) >= 4:
                gaps_filled += 8

        # Peel gap (if team has carries)
        if team_stats["sustained"] >= 12 and team_stats["peel"] < 6:
            max_gaps += 10
            if range_style.get("peel", 0) >= 3:
                gaps_filled += 10

        # Balance check - avoid redundancy
        hero_role = roles.get("primary_role", "")
        role_count = sum(
            1
            for ally_name in ally_picks
            if ally_name in heroes_data
            and heroes_data[ally_name]
            .get("meta", {})
            .get("attributes", {})
            .get("roles", {})
            .get("primary_role")
            == hero_role
        )

        if role_count >= 2:
            gaps_filled -= self.config.ROLE_REDUNDANCY_PENALTY

        # Calculate final score
        if max_gaps == 0:
            return 60.0

        score = (gaps_filled / max_gaps) * 100
        return max(min(score, 100), 0)

    def assess_enemy_lane_threat(
        self,
        lane: str,
        enemy_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> float:
        """
        Assess if enemies have strong heroes in this lane.

        Returns higher score if we need to counter this lane.

        Args:
            lane: Lane code (exp, jungle, mid, gold, roam)
            enemy_picks: Enemy team picks
            heroes_data: Dictionary of all heroes' data

        Returns:
            Threat score 0-1.0?.
        """
        lane_name = self.config.ROLE_MAP.get(lane, lane)
        threat_score = 0
        enemy_count = 0

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
                    # Enemy has this lane - check their strength
                    combat = enemy_meta.get("attributes", {}).get("combat", {})
                    power = enemy_meta.get("attributes", {}).get("power_curve", {})

                    strength = (
                        combat.get("dps", 0) * 0.4
                        + combat.get("burst_damage", 0) * 0.3
                        + power.get("late_game", 0) * 0.3
                    ) / 5

                    threat_score += strength
                    enemy_count += 1

        if enemy_count == 0:
            return 0.3

        return threat_score / enemy_count

    def _lane_to_code(self, lane_name: str) -> str:
        """Convert lane name to code"""
        reverse_map = self.config.REVERSE_ROLE_MAP
        return reverse_map.get(lane_name, lane_name.lower())
