"""
Hero Evaluator
Scores individual heroes using lane-specific weights.
Heroes that cannot play the target lane are filtered out entirely.
"""

from typing import Dict, Any, List, Tuple
import logging

from app.services.config.draft_config import DraftConfig
from app.services.scoring.counter_scorer import CounterScorer
from app.services.scoring.synergy_scorer import SynergyScorer
from app.services.scoring.priority_scorer import PriorityScorer
from .team_analyzer import TeamAnalyzer

logger = logging.getLogger(__name__)


class HeroEvaluator:
    """Evaluates and scores individual heroes"""

    def __init__(self):
        self.config = DraftConfig()
        self.counter_scorer = CounterScorer()
        self.synergy_scorer = SynergyScorer()
        self.priority_scorer = PriorityScorer()
        self.team_analyzer = TeamAnalyzer()

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
        Score a hero for a specific lane.

        HARD FILTER: Heroes who cannot play the target lane return score 0.
        This prevents suggesting Mid mages when Jungle is needed.

        Args:
            hero_name: Hero name
            hero: Hero data dict
            banned_heroes: Banned heroes
            enemy_picks: Enemy picks
            ally_picks: Ally picks
            current_role: Lane code (exp, jungle, mid, gold, roam)
            heroes_data: All heroes data

        Returns:
            Tuple of (score 0-100, list of reasons)
        """
        lane_name = self.config.ROLE_MAP.get(current_role, current_role)

        # ── STEP 1: Hard lane filter ─────────────────────────────────────────
        lane_score = self._calculate_lane_fit_score(hero, current_role)

        if lane_score == self.config.LANE_FIT_NO_MATCH:
            # Hero cannot play this lane - completely disqualify
            return 0.0, [f"Cannot play {lane_name}"]

        # ── STEP 2: Get lane-specific weights with dynamic adjustments ────────
        weights = self._get_weights(
            current_role, banned_heroes, enemy_picks, ally_picks
        )

        # ── STEP 3: Calculate individual component scores ─────────────────────
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

        # ── STEP 4: Build weighted final score ────────────────────────────────
        final_score = (
            counter_score * weights["counter"]
            + synergy_score * weights["synergy"]
            + comp_score * weights["team_composition"]
            + priority_score * weights["pick_priority"]
            + lane_score * weights["role_fit"]
        )

        # ── STEP 5: Critical gap boost ────────────────────────────────────────
        team_stats = self.team_analyzer._analyze_team_stats(ally_picks, heroes_data)
        if self._covers_critical_gap(hero, team_stats, current_role):
            final_score *= 1.15
            gap_reason = self._describe_gap_covered(hero, team_stats, current_role)
        else:
            gap_reason = None

        # ── STEP 6: Build reason list ─────────────────────────────────────────
        reasons = self._build_reasons(
            hero_name,
            hero,
            current_role,
            lane_name,
            lane_score,
            counter_score,
            synergy_score,
            comp_score,
            priority_score,
            final_score,
            gap_reason,
        )

        return final_score, reasons

    # ─────────────────────────────────────────────────────────────────────────
    # WEIGHTS
    # ─────────────────────────────────────────────────────────────────────────

    def _get_weights(
        self,
        lane: str,
        banned_heroes: List[str],
        enemy_picks: List[str],
        ally_picks: List[str],
    ) -> Dict[str, float]:
        """
        Get weights for this lane and adjust for draft state.

        Starts from lane-specific base weights from config,
        then applies dynamic adjustments on top.
        """
        weights = self.config.LANE_WEIGHTS.get(lane, self.config.BASE_WEIGHTS).copy()
        total_picks = len(enemy_picks) + len(ally_picks)

        # Late draft: team composition becomes more urgent
        if total_picks >= self.config.EARLY_DRAFT_THRESHOLD:
            adj = self.config.WEIGHT_ADJUSTMENTS["late_draft"]
            for key, delta in adj.items():
                weights[key] = weights.get(key, 0) + delta

        # Enemy pattern clear: boost counter for jungle/mid
        if len(enemy_picks) >= 3 and lane in ["jungle", "mid"]:
            adj = self.config.WEIGHT_ADJUSTMENTS["enemy_pattern_clear"]
            for key, delta in adj.items():
                weights[key] = weights.get(key, 0) + delta

        # Many bans: avoid niche picks
        if len(banned_heroes) >= 6:
            adj = self.config.WEIGHT_ADJUSTMENTS["many_bans"]
            for key, delta in adj.items():
                weights[key] = weights.get(key, 0) + delta

        # Normalize to sum to 1.0
        total = sum(weights.values())
        if total > 0:
            weights = {k: max(v, 0) / total for k, v in weights.items()}

        if self.config.LOG_WEIGHT_CALCULATIONS:
            logger.info(f"[{lane}] Final weights: {weights}")

        return weights

    # ─────────────────────────────────────────────────────────────────────────
    # LANE FIT
    # ─────────────────────────────────────────────────────────────────────────

    def _calculate_lane_fit_score(
        self, hero: Dict[str, Any], current_role: str
    ) -> float:
        """
        Score how well this hero fits the target lane.

        Returns LANE_FIT_NO_MATCH (0) if hero cannot play the lane at all.
        This is a hard disqualifier.
        """
        hero_meta = hero.get("meta", {})
        roles = hero_meta.get("attributes", {}).get("roles", {})
        lane_priorities = roles.get("lane_priority", [])
        target_lane = self.config.ROLE_MAP.get(current_role, current_role)

        if target_lane in lane_priorities:
            idx = lane_priorities.index(target_lane)
            if idx == 0:
                return self.config.LANE_FIT_PRIMARY  # 100
            elif idx == 1:
                return self.config.LANE_FIT_SECONDARY  # 75
            elif idx == 2:
                return self.config.LANE_FIT_TERTIARY  # 50
            else:
                return self.config.LANE_FIT_LOWER  # 25

        return self.config.LANE_FIT_NO_MATCH  # 0 - DISQUALIFIED

    # ─────────────────────────────────────────────────────────────────────────
    # CRITICAL GAP BOOST
    # ─────────────────────────────────────────────────────────────────────────

    def _covers_critical_gap(
        self,
        hero: Dict[str, Any],
        team_stats: Dict[str, float],
        lane: str,
    ) -> bool:
        """
        Check if this hero covers a gap the team critically needs.

        Examples:
        - Jungle: Team has no mobility → hero has high mobility → boost
        - EXP: Team has no tankiness → hero is tanky → boost
        - Roam: Team has no CC → hero has CC → boost
        """
        hero_meta = hero.get("meta", {})
        attrs = hero_meta.get("attributes", {})

        combat = attrs.get("combat", {})
        surv = attrs.get("survivability", {})
        util = attrs.get("utility", {})
        range_style = attrs.get("range_playstyle", {})
        power = attrs.get("power_curve", {})

        HIGH = self.config.HIGH_STAT_THRESHOLD  # 4

        if lane == "jungle":
            # Jungle needs mobility and burst
            return (
                surv.get("mobility", 0) >= HIGH or combat.get("burst_damage", 0) >= HIGH
            )

        elif lane == "mid":
            # Mid needs magic damage and CC
            role = attrs.get("roles", {}).get("primary_role", "")
            return role == "Mage" and (
                combat.get("dps", 0) >= HIGH or util.get("crowd_control", 0) >= HIGH
            )

        elif lane == "exp":
            # EXP needs tankiness and engage
            return (
                surv.get("tankiness", 0) >= HIGH or range_style.get("engage", 0) >= HIGH
            )

        elif lane == "gold":
            # Gold needs late game scaling and DPS
            return power.get("late_game", 0) >= HIGH and combat.get("dps", 0) >= HIGH

        elif lane == "roam":
            # Roam needs CC or team support
            return (
                util.get("crowd_control", 0) >= HIGH
                or util.get("team_heal", 0) >= 3
                or util.get("team_buff", 0) >= 3
            )

        return False

    def _describe_gap_covered(
        self,
        hero: Dict[str, Any],
        team_stats: Dict[str, float],
        lane: str,
    ) -> str:
        """Return a short description of which gap this hero covers"""
        gap_descriptions = {
            "jungle": "Provides burst damage & mobility for jungle",
            "mid": "Provides magic damage and CC from mid",
            "exp": "Provides frontline tankiness and engage",
            "gold": "Strong late-game scaling carry",
            "roam": "Provides CC and team support from roam",
        }
        return gap_descriptions.get(lane, "Fills critical team gap")

    # ─────────────────────────────────────────────────────────────────────────
    # REASON BUILDING
    # ─────────────────────────────────────────────────────────────────────────

    def _build_reasons(
        self,
        hero_name: str,
        hero: Dict[str, Any],
        current_role: str,
        lane_name: str,
        lane_score: float,
        counter_score: float,
        synergy_score: float,
        comp_score: float,
        priority_score: float,
        final_score: float,
        gap_reason: str,
    ) -> List[str]:
        """Build a clean, informative list of reasons for this suggestion"""
        reasons = []

        # Lane fit reason (always first)
        if lane_score >= self.config.LANE_FIT_PRIMARY:
            reasons.append(f"Primary {lane_name} hero")
        elif lane_score >= self.config.LANE_FIT_SECONDARY:
            reasons.append(f"Strong {lane_name} flex pick")
        elif lane_score >= self.config.LANE_FIT_TERTIARY:
            reasons.append(f"Situational {lane_name} pick")

        # Gap coverage reason
        if gap_reason:
            reasons.append(gap_reason)

        # Counter reason
        if counter_score >= self.config.COUNTER_THRESHOLD:
            reasons.append(f"Counters enemy team ({counter_score:.0f}/100)")

        # Synergy reason
        if synergy_score >= self.config.SYNERGY_THRESHOLD:
            reasons.append(f"Strong team synergy ({synergy_score:.0f}/100)")

        # Composition reason
        if comp_score >= self.config.COMP_THRESHOLD:
            reasons.append(f"Fills team composition gap ({comp_score:.0f}/100)")

        # Meta strength reason
        if priority_score >= self.config.PRIORITY_THRESHOLD:
            reasons.append("Strong meta pick")

        # Top tier indicator
        if final_score >= 80:
            reasons.insert(0, f"Top tier {lane_name} pick")

        return reasons[: self.config.REASONS_PER_HERO]
