"""
Team Analyzer
Analyzes team composition and identifies critical gaps.
"""

from typing import Dict, Any, List
import logging

from app.services.config.draft_config import DraftConfig

logger = logging.getLogger(__name__)


class TeamAnalyzer:
    """Analyzes team composition and identifies gaps"""

    def __init__(self):
        self.config = DraftConfig()

    # ─────────────────────────────────────────────────────────────────────────
    # LANE IDENTIFICATION
    # ─────────────────────────────────────────────────────────────────────────

    def identify_filled_lanes(
        self,
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        """
        Identify which lanes are already filled by ally picks.

        Returns list of filled lane codes (exp, jungle, mid, gold, roam).
        """
        filled = set()

        for hero_name in ally_picks:
            if hero_name in heroes_data:
                hero = heroes_data[hero_name]
                meta = hero.get("meta", {})
                lanes = (
                    meta.get("attributes", {}).get("roles", {}).get("lane_priority", [])
                )

                if lanes:
                    primary = lanes[0]
                    code = self._lane_name_to_code(primary)
                    filled.add(code)
                    logger.debug(f"  {hero_name} → {primary} ({code})")

        return list(filled)

    def identify_open_lanes(
        self,
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        """Return lane codes that are NOT yet filled"""
        filled = self.identify_filled_lanes(ally_picks, heroes_data)
        return [lane for lane in self.config.ALL_LANES if lane not in filled]

    def identify_missing_roles(
        self,
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        """Return lane NAMES (not codes) that are missing from team"""
        open_lanes = self.identify_open_lanes(ally_picks, heroes_data)
        return [self.config.ROLE_MAP[lane] for lane in open_lanes]

    # ─────────────────────────────────────────────────────────────────────────
    # TEAM STATS ANALYSIS
    # ─────────────────────────────────────────────────────────────────────────

    def _analyze_team_stats(
        self,
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> Dict[str, float]:
        """
        Analyze current team's aggregate stats.

        Returns a dict with totals for:
        tankiness, physical_damage, magic_damage,
        crowd_control, mobility, engage, peel, burst, sustained
        """
        team_stats = {
            "tankiness": 0.0,
            "physical_damage": 0.0,
            "magic_damage": 0.0,
            "crowd_control": 0.0,
            "mobility": 0.0,
            "engage": 0.0,
            "peel": 0.0,
            "burst": 0.0,
            "sustained": 0.0,
            "waveclear": 0.0,
        }

        for ally_name in ally_picks:
            if ally_name not in heroes_data:
                continue

            ally = heroes_data[ally_name]
            meta = ally.get("meta", {})
            attrs = meta.get("attributes", {})

            combat = attrs.get("combat", {})
            surv = attrs.get("survivability", {})
            util = attrs.get("utility", {})
            range_style = attrs.get("range_playstyle", {})
            roles = attrs.get("roles", {})

            team_stats["tankiness"] += surv.get("tankiness", 0)
            team_stats["crowd_control"] += util.get("crowd_control", 0)
            team_stats["mobility"] += surv.get("mobility", 0)
            team_stats["engage"] += range_style.get("engage", 0)
            team_stats["peel"] += range_style.get("peel", 0)
            team_stats["burst"] += combat.get("burst_damage", 0)
            team_stats["sustained"] += combat.get("sustained_damage", 0)
            team_stats["waveclear"] += range_style.get("waveclear", 0)

            # Separate physical and magic damage
            role = roles.get("primary_role", "")
            if role == "Mage":
                team_stats["magic_damage"] += combat.get("dps", 0)
            else:
                team_stats["physical_damage"] += combat.get("dps", 0)

        return team_stats

    # ─────────────────────────────────────────────────────────────────────────
    # COMPOSITION GAP SCORING
    # ─────────────────────────────────────────────────────────────────────────

    def analyze_composition_gap(
        self,
        hero: Dict[str, Any],
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> float:
        """
        Score how well this hero fills team composition gaps (0-100).

        Checks: tankiness, magic damage, physical damage,
                CC, engage, waveclear, peel, role redundancy.
        """
        hero_meta = hero.get("meta", {})
        attrs = hero_meta.get("attributes", {})

        combat = attrs.get("combat", {})
        surv = attrs.get("survivability", {})
        util = attrs.get("utility", {})
        range_style = attrs.get("range_playstyle", {})
        roles = attrs.get("roles", {})

        team_stats = self._analyze_team_stats(ally_picks, heroes_data)

        gaps_filled = 0
        max_gaps = 0

        # Tankiness gap
        if (
            len(ally_picks) >= 2
            and team_stats["tankiness"] < self.config.TARGET_TANKINESS
        ):
            max_gaps += 15
            if surv.get("tankiness", 0) >= 4:
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

        # CC gap
        if team_stats["crowd_control"] < self.config.TARGET_CROWD_CONTROL:
            max_gaps += 10
            if util.get("crowd_control", 0) >= 3:
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

        # Peel gap (if team has carries that need protection)
        if team_stats["sustained"] >= 12 and team_stats["peel"] < 6:
            max_gaps += 10
            if range_style.get("peel", 0) >= 3:
                gaps_filled += 10

        # Role redundancy penalty
        hero_role = roles.get("primary_role", "")
        role_count = sum(
            1
            for a in ally_picks
            if a in heroes_data
            and heroes_data[a]
            .get("meta", {})
            .get("attributes", {})
            .get("roles", {})
            .get("primary_role")
            == hero_role
        )
        if role_count >= 2:
            gaps_filled -= self.config.ROLE_REDUNDANCY_PENALTY

        if max_gaps == 0:
            return 60.0

        score = (gaps_filled / max_gaps) * 100
        return max(min(score, 100), 0)

    # ─────────────────────────────────────────────────────────────────────────
    # ENEMY THREAT ASSESSMENT
    # ─────────────────────────────────────────────────────────────────────────

    def assess_enemy_lane_threat(
        self,
        lane: str,
        enemy_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> float:
        """
        Assess how strong the enemy threat is in a given lane (0-1).

        Higher score = more important to counter this lane.
        """
        lane_name = self.config.ROLE_MAP.get(lane, lane)
        threat_score = 0.0
        enemy_count = 0

        for enemy_name in enemy_picks:
            if enemy_name not in heroes_data:
                continue

            enemy = heroes_data[enemy_name]
            meta = enemy.get("meta", {})
            attrs = meta.get("attributes", {})
            lanes = attrs.get("roles", {}).get("lane_priority", [])

            if lane_name in lanes:
                combat = attrs.get("combat", {})
                power = attrs.get("power_curve", {})

                # Threat = DPS + burst + late game (normalized 0-1)
                strength = (
                    combat.get("dps", 0) * 0.4
                    + combat.get("burst_damage", 0) * 0.3
                    + power.get("late_game", 0) * 0.3
                ) / 5.0

                threat_score += strength
                enemy_count += 1

        if enemy_count == 0:
            return 0.3  # Slight default preference

        return threat_score / enemy_count

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _lane_name_to_code(self, lane_name: str) -> str:
        """Convert lane name (e.g. 'EXP Lane') to code (e.g. 'exp')"""
        return self.config.REVERSE_ROLE_MAP.get(lane_name, lane_name.lower())
