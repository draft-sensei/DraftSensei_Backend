"""
Draft Configuration - Centralized configuration for all draft-related constants
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

    # ===== BASE WEIGHTS =====
    # These are the default weights used in scoring
    # Dynamically adjusted based on draft state in weights.py
    BASE_WEIGHTS: Dict[str, float] = {
        "counter": 0.35,
        "synergy": 0.25,
        "team_composition": 0.20,
        "pick_priority": 0.15,
        "role_fit": 0.05,
    }

    # ===== LANE IMPORTANCE SCORES =====
    # How important each lane is (higher = more impactful pick)
    LANE_IMPORTANCE: Dict[str, int] = {
        "jungle": 100,
        "mid": 90,
        "exp": 80,
        "gold": 75,
        "roam": 70,
    }

    # ===== DRAFT PHASE DEFINITIONS =====
    # When is early/mid/late draft?
    EARLY_DRAFT_THRESHOLD = 4  # Total picks <= 4 = early draft
    MID_DRAFT_THRESHOLD = 6  # Total picks <= 6 = mid draft
    LATE_DRAFT_THRESHOLD = 10  # Total picks > 6 = late draft

    # ===== THRESHOLD SCORES =====
    # Score thresholds for adding reasons to suggestions
    COUNTER_THRESHOLD = 70  # Counter score >= 70 to mention it
    SYNERGY_THRESHOLD = 70  # Synergy score >= 70 to mention it
    COMP_THRESHOLD = 70  # Comp score >= 70 to mention it
    PRIORITY_THRESHOLD = 75  # Priority score >= 75 to mention it

    # ===== LANE FIT SCORES =====
    # Scoring for how well hero fits a lane
    LANE_FIT_PRIMARY = 100  # Hero's primary lane
    LANE_FIT_SECONDARY = 75  # Hero's secondary lane
    LANE_FIT_TERTIARY = 50  # Hero's tertiary lane
    LANE_FIT_LOWER = 30  # Lower priority lanes
    LANE_FIT_NO_MATCH = 5  # No lane priority match

    # ===== STAT THRESHOLDS =====
    # What counts as "high" for different attributes
    HIGH_STAT_THRESHOLD = 4  # Stats >= 4 out of 5 are "high"
    VERY_HIGH_STAT_THRESHOLD = 5  # Stats == 5 are "very high"

    # ===== TEAM COMPOSITION TARGETS =====
    # Target stats for a balanced team composition
    TARGET_TANKINESS = 8  # Minimum total team tankiness
    TARGET_MAGIC_DAMAGE = 10  # Minimum total magic damage output
    TARGET_PHYSICAL_DAMAGE = 10  # Minimum total physical damage output
    TARGET_CROWD_CONTROL = 5  # Minimum total CC
    TARGET_ENGAGE = 8  # Minimum total engage
    TARGET_WAVECLEAR = 8  # Minimum total waveclear

    # ===== PENALTY FACTORS =====
    ROLE_REDUNDANCY_PENALTY = 15  # Penalty for picking same role twice
    PERFECT_STAT_PENALTY_2 = 0.90  # 10% penalty for 4 perfect stats
    PERFECT_STAT_PENALTY_3 = 0.95  # 5% penalty for 3 perfect stats
    PERFECT_STAT_PENALTY_5 = 0.85  # 15% penalty for 5+ perfect stats

    # ===== DIVERSITY TRACKING =====
    # Penalty for frequently suggested heroes
    DIVERSITY_PENALTY_THRESHOLDS = {
        0: 0.00,  # First suggestion: no penalty
        2: 0.05,  # 1-2 suggestions: 5% penalty
        4: 0.10,  # 3-4 suggestions: 10% penalty
        float("inf"): 0.15,  # 5+ suggestions: 15% penalty
    }

    # ===== DYNAMIC WEIGHT ADJUSTMENTS =====
    # How much to adjust weights based on draft state
    WEIGHT_ADJUSTMENTS = {
        "late_draft": {
            "team_composition": +0.10,
            "synergy": +0.10,
            "pick_priority": -0.10,
        },
        "enemy_pattern_clear": {
            "counter": +0.15,
            "synergy": -0.10,
        },
        "missing_critical_role": {
            "role_fit": +0.15,
            "pick_priority": -0.05,
        },
        "many_bans": {
            "pick_priority": +0.05,
        },
        "win_condition_secured": {
            "synergy": +0.10,
            "counter": -0.05,
        },
    }

    # ===== COUNTER SCORING MECHANICS =====
    # How much each type of counter adds to score
    COUNTER_SCORING = {
        "anti_squishy": {
            "threshold": 4,  # Need anti_squishy >= 4
            "vs_tankiness": {"threshold": 2, "bonus": 25},
            "vs_tankiness_mod": {"threshold": 3, "bonus": 15},
        },
        "anti_tank": {
            "threshold": 4,
            "vs_tankiness": {"threshold": 4, "bonus": 25},
            "vs_tankiness_mod": {"threshold": 5, "bonus": 15},
        },
        "mobility": {
            "bonus_escape": 20,
            "bonus_mobility": 20,
        },
        "poke": {
            "threshold": 4,
            "vs_range": {"threshold": 2, "bonus": 20},
            "vs_range_mod": {"threshold": 3, "bonus": 10},
        },
        "engage": {
            "threshold": 4,
            "vs_mobility": {"threshold": 2, "bonus": 20},
        },
        "burst": {
            "threshold": 4,
            "vs_defense": {"threshold": 3, "bonus": 20},
            "vs_defense_mod": {"threshold": 4, "bonus": 10},
        },
    }

    # ===== SYNERGY SCORING MECHANICS =====
    # How much each type of synergy adds to score
    SYNERGY_SCORING = {
        "tank_dps": 20,  # Tank + DPS dealer
        "engage_aoe": 25,  # Engage + AoE damage
        "cc_burst": 20,  # CC + burst damage
        "peel_squishy": 18,  # Peel + squishy carry
        "sustain_fighter": 22,  # Sustain support + fighter
        "double_engage": 15,  # Two engage heroes
        "dive_comp": 12,  # Multiple mobile heroes
    }

    # ===== PICK PRIORITY MULTIPLIER =====
    # Scale for pick priority score calculation
    PRIORITY_SCALE = 20  # Multiply final priority by 20 to get 0-100 score

    # ===== MAX SUGGESTIONS =====
    TOP_SUGGESTIONS_COUNT = 5  # Return top 5 hero suggestions
    REASONS_PER_HERO = 5  # Max reasons to show per hero

    # ===== LOGGING =====
    LOG_SCORING_DETAILS = False  # Set to True to log detailed scoring for each hero
    LOG_WEIGHT_CALCULATIONS = False  # Set to True to log weight calculation details
