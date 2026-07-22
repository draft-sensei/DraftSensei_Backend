"""
Draft Configuration - Centralized configuration for all draft-related constants
Weights based on MLBB game knowledge and role responsibilities
"""

from typing import Dict, List


class DraftConfig:
    """Configuration for draft suggestion system"""

    # ===== ROLE MAPPINGS =====
    ROLE_MAP: Dict[str, str] = {
        "exp": "EXP Lane",
        "jungle": "Jungle",
        "mid": "Mid Lane",
        "gold": "Gold Lane",
        "roam": "Roam",
    }

    REVERSE_ROLE_MAP: Dict[str, str] = {v: k for k, v in ROLE_MAP.items()}

    ALL_LANES: List[str] = ["exp", "jungle", "mid", "gold", "roam"]

    # ===== LANE PRIORITY & IMPORTANCE =====
    # Determines which empty lane to fill first
    LANE_IMPORTANCE: Dict[str, int] = {
        "jungle": 100,  # Highest impact - controls map tempo
        "mid": 90,  # Second - provides magic damage and roaming
        "exp": 80,  # Third - provides frontline and engage
        "gold": 75,  # Fourth - scaling carry damage
        "roam": 70,  # Last - support/enabler role
    }

    # ===== LANE-SPECIFIC WEIGHT CONFIGURATIONS =====
    # Based on MLBB game knowledge of each role's responsibilities
    LANE_WEIGHTS: Dict[str, Dict[str, float]] = {
        # ── JUNGLE ──────────────────────────────────────────────────────────
        # Jungler contests enemy jungler directly → counter is important
        # Rotates to all lanes → synergy with whole team matters
        # Usually provides burst/assassin role → composition matters
        # Non-jungler in jungle = disaster → role_fit raised
        "jungle": {
            "counter": 0.30,  # Counter enemy jungler directly
            "synergy": 0.25,  # Rotates to all lanes - synergy matters
            "team_composition": 0.20,  # Fill burst/assassin gap
            "pick_priority": 0.15,  # Meta junglers matter (Fanny, Lancelot)
            "role_fit": 0.10,  # Must actually be a jungler
        },
        # ── MID LANE ────────────────────────────────────────────────────────
        # Counters enemy mid (Kagura, Harith, Valentina mirror etc)
        # Mage needs team setup to land spells → synergy matters
        # Usually fills magic damage gap → composition matters
        # Must be able to play mid efficiently
        "mid": {
            "counter": 0.25,  # Counter enemy mid laner
            "synergy": 0.25,  # Needs team setup for spells
            "team_composition": 0.25,  # Fills magic damage gap
            "pick_priority": 0.15,  # Meta mid laners matter
            "role_fit": 0.10,  # Must be a mid hero
        },
        # ── EXP LANE ────────────────────────────────────────────────────────
        # Provides team's FRONTLINE → composition is most critical
        # 1v1 duels happen → counter matters somewhat
        # EXP lane is isolated early → synergy less critical
        # Without frontline: team has no engage/peel → composition #1
        "exp": {
            "counter": 0.20,  # 1v1 duels matter in EXP lane
            "synergy": 0.20,  # Isolated early - synergy less critical
            "team_composition": 0.35,  # CRITICAL: must provide tankiness/engage
            "pick_priority": 0.15,  # Meta exp laners matter
            "role_fit": 0.10,  # Must survive lane phase
        },
        # ── GOLD LANE ───────────────────────────────────────────────────────
        # Protected by roamer → direct counters less important
        # Pick strong meta marksman → pick_priority is HIGHEST here
        # Provides scaling damage → composition matters
        # Strong gold laners (Beatrix, Melissa, Brody) outperform situational picks
        "gold": {
            "counter": 0.15,  # Protected - counters less impactful
            "synergy": 0.20,  # Needs roamer peel/support
            "team_composition": 0.25,  # Provides physical/late game damage
            "pick_priority": 0.30,  # META MATTERS MOST: pick strong gold laner
            "role_fit": 0.10,  # Must scale well in gold lane
        },
        # ── ROAM ────────────────────────────────────────────────────────────
        # Exists purely to ENABLE team → synergy is everything
        # Fills engage/peel/heal gap → composition is second
        # Does not counter enemy directly → counter is lowest
        # Meta matters less than team fit
        # e.g. Team has Franco (engage) → pick Angela (peel/heal)
        #      Team has no engage → pick Khufra/Tigreal
        "roam": {
            "counter": 0.10,  # Roamer doesn't counter directly
            "synergy": 0.40,  # SYNERGY IS EVERYTHING for roamer
            "team_composition": 0.30,  # Fill engage/peel/heal gap
            "pick_priority": 0.10,  # Meta matters less for roam
            "role_fit": 0.10,  # Must be able to roam
        },
    }

    # ===== BASE WEIGHTS (fallback if lane not found) =====
    BASE_WEIGHTS: Dict[str, float] = {
        "counter": 0.25,
        "synergy": 0.25,
        "team_composition": 0.25,
        "pick_priority": 0.15,
        "role_fit": 0.10,
    }

    HIGH_STAT_THRESHOLD = 4

    # ===== DRAFT PHASE DEFINITIONS =====
    EARLY_DRAFT_THRESHOLD = 4  # Total picks <= 4 = early draft
    MID_DRAFT_THRESHOLD = 6
    LATE_DRAFT_THRESHOLD = 10

    # ===== SCORE THRESHOLDS (when to add a reason) =====
    COUNTER_THRESHOLD = 65
    SYNERGY_THRESHOLD = 65
    COMP_THRESHOLD = 60
    PRIORITY_THRESHOLD = 70

    # ===== LANE FIT SCORES =====
    LANE_FIT_PRIMARY = 100  # Hero's primary lane
    LANE_FIT_SECONDARY = 75  # Hero's secondary lane
    LANE_FIT_TERTIARY = 50  # Hero's tertiary lane
    LANE_FIT_LOWER = 25  # Lower priority lanes
    LANE_FIT_NO_MATCH = 0  # Hero cannot play this lane - DISQUALIFIED

    # ===== TEAM COMPOSITION TARGETS =====
    TARGET_TANKINESS = 8
    TARGET_MAGIC_DAMAGE = 10
    TARGET_PHYSICAL_DAMAGE = 10
    TARGET_CROWD_CONTROL = 5
    TARGET_ENGAGE = 8
    TARGET_WAVECLEAR = 8

    # ===== ROLE REDUNDANCY PENALTY =====
    # Picking the same primary role twice (e.g., two Roamers)
    ROLE_REDUNDANCY_PENALTY = 20

    # ===== PERFECT STAT PENALTIES =====
    # Heroes with suspiciously perfect stats get penalized
    PERFECT_STAT_PENALTY_3 = 0.95  # 5% penalty for 3 perfect stats
    PERFECT_STAT_PENALTY_4 = 0.90  # 10% penalty for 4 perfect stats
    PERFECT_STAT_PENALTY_5 = 0.85  # 15% penalty for 5+ perfect stats

    # ===== DIVERSITY TRACKING =====
    # Prevent same hero being suggested repeatedly
    DIVERSITY_PENALTY_LOW = 0.05  # 1-2 suggestions: 5% penalty
    DIVERSITY_PENALTY_MID = 0.10  # 3-4 suggestions: 10% penalty
    DIVERSITY_PENALTY_HIGH = 0.15  # 5+ suggestions: 15% penalty

    # ===== DYNAMIC WEIGHT ADJUSTMENTS =====
    # Applied ON TOP of lane-specific weights based on draft state
    WEIGHT_ADJUSTMENTS = {
        # Late draft: team composition becomes more urgent
        "late_draft": {
            "team_composition": +0.05,
            "pick_priority": -0.05,
        },
        # Enemy pattern clear (3+ picks): boost counter for jungle/mid
        "enemy_pattern_clear": {
            "counter": +0.10,
            "synergy": -0.05,
            "pick_priority": -0.05,
        },
        # Many bans (6+): avoid niche picks
        "many_bans": {
            "pick_priority": +0.05,
            "team_composition": -0.05,
        },
        # Win condition secured (strong carry already picked)
        "win_condition_secured": {
            "synergy": +0.10,
            "counter": -0.05,
            "pick_priority": -0.05,
        },
    }

    # ===== SYNERGY SCORING BONUSES =====
    SYNERGY_SCORING = {
        "tank_dps": 20,  # Tank + DPS dealer
        "engage_aoe": 25,  # Engage + AoE damage (e.g., Tigreal + Odette)
        "cc_burst": 20,  # CC + burst assassin (e.g., Franco + Gusion)
        "peel_squishy": 18,  # Peel support + squishy carry (e.g., Angela + Layla)
        "sustain_fighter": 22,  # Sustain support + fighter
        "double_engage": 15,  # Two engage heroes (dive comp)
        "dive_comp": 12,  # Multiple mobile heroes
    }

    # ===== PRIORITY SCALE =====
    PRIORITY_SCALE = 20  # Multiplier to bring score to 0-100

    # ===== SUGGESTIONS CONFIG =====
    TOP_SUGGESTIONS_COUNT = 5  # Return top 5 heroes
    REASONS_PER_HERO = 5  # Max reasons shown per hero

    # ===== LOGGING =====
    LOG_SCORING_DETAILS = False
    LOG_WEIGHT_CALCULATIONS = False
