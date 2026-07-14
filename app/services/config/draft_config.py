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

    # ===== LANE PRIORITY & IMPORTANCE =====
    # How important each lane is (higher = more impactful)
    # This determines priority when multiple lanes are missing
    LANE_IMPORTANCE: Dict[str, int] = {
        "jungle": 100,  # Highest impact - pick first
        "mid": 90,  # Second highest
        "exp": 80,  # Third
        "gold": 75,  # Fourth
        "roam": 70,  # Lowest impact
    }

    # ===== LANE-SPECIFIC WEIGHT CONFIGURATIONS =====
    # Different lanes need different scoring emphasis

    LANE_WEIGHTS: Dict[str, Dict[str, float]] = {
        # Jungle: High impact, needs team synergy and composition balance
        "jungle": {
            "counter": 0.15,  # Lower - jungle pick isn't about countering specific lane
            "synergy": 0.30,  # Medium - synergy with team matters
            "team_composition": 0.35,  # HIGH - filling gaps is critical
            "pick_priority": 0.15,  # Medium - meta strength
            "role_fit": 0.05,  # Very low (must play jungle)
        },
        # Mid Lane: Medium impact, needs counter play + team fit
        "mid": {
            "counter": 0.30,  # Medium - countering mid enemy matters
            "synergy": 0.25,  # Medium
            "team_composition": 0.25,  # Medium - balance team
            "pick_priority": 0.15,  # Medium
            "role_fit": 0.05,
        },
        # EXP Lane: Fighter/Tank heavy, needs tankiness and team coordination
        "exp": {
            "counter": 0.20,  # Low
            "synergy": 0.30,  # Medium
            "team_composition": 0.35,  # HIGH - need tankiness/durability
            "pick_priority": 0.10,  # Low
            "role_fit": 0.05,
        },
        # Gold Lane: Carry lane, needs late game power and farm potential
        "gold": {
            "counter": 0.15,  # Low
            "synergy": 0.25,  # Medium
            "team_composition": 0.30,  # Medium - need DPS
            "pick_priority": 0.25,  # Higher - meta marksmen/fighters
            "role_fit": 0.05,
        },
        # Roam: Support role, needs to cover team weaknesses
        "roam": {
            "counter": 0.10,  # Very low
            "synergy": 0.35,  # HIGH - must support team
            "team_composition": 0.30,  # High - fill gaps (heal, peel, engage)
            "pick_priority": 0.15,  # Low
            "role_fit": 0.10,
        },
    }

    # ===== BASE WEIGHTS (used if lane-specific not applicable) =====
    BASE_WEIGHTS: Dict[str, float] = {
        "counter": 0.35,
        "synergy": 0.25,
        "team_composition": 0.20,
        "pick_priority": 0.15,
        "role_fit": 0.05,
    }

    # ===== DRAFT PHASE DEFINITIONS =====
    EARLY_DRAFT_THRESHOLD = 4
    MID_DRAFT_THRESHOLD = 6
    LATE_DRAFT_THRESHOLD = 10

    # ===== THRESHOLD SCORES =====
    COUNTER_THRESHOLD = 70
    SYNERGY_THRESHOLD = 70
    COMP_THRESHOLD = 70
    PRIORITY_THRESHOLD = 75

    # ===== LANE FIT SCORES =====
    LANE_FIT_PRIMARY = 100
    LANE_FIT_SECONDARY = 75
    LANE_FIT_TERTIARY = 50
    LANE_FIT_LOWER = 30
    LANE_FIT_NO_MATCH = 5

    # ===== STAT THRESHOLDS =====
    HIGH_STAT_THRESHOLD = 4
    VERY_HIGH_STAT_THRESHOLD = 5

    # ===== TEAM COMPOSITION TARGETS =====
    TARGET_TANKINESS = 8
    TARGET_MAGIC_DAMAGE = 10
    TARGET_PHYSICAL_DAMAGE = 10
    TARGET_CROWD_CONTROL = 5
    TARGET_ENGAGE = 8
    TARGET_WAVECLEAR = 8

    # ===== PENALTY FACTORS =====
    ROLE_REDUNDANCY_PENALTY = 15
    PERFECT_STAT_PENALTY_2 = 0.90
    PERFECT_STAT_PENALTY_3 = 0.95
    PERFECT_STAT_PENALTY_5 = 0.85

    # ===== DIVERSITY TRACKING =====
    DIVERSITY_PENALTY_THRESHOLDS = {0: 0.00, 2: 0.05, 4: 0.10, float("inf"): 0.15}

    # ===== DYNAMIC WEIGHT ADJUSTMENTS =====
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
    COUNTER_SCORING = {
        "anti_squishy": {
            "threshold": 4,
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
    SYNERGY_SCORING = {
        "tank_dps": 20,
        "engage_aoe": 25,
        "cc_burst": 20,
        "peel_squishy": 18,
        "sustain_fighter": 22,
        "double_engage": 15,
        "dive_comp": 12,
    }

    # ===== PRIORITY MULTIPLIER =====
    PRIORITY_SCALE = 20

    # ===== MAX SUGGESTIONS =====
    TOP_SUGGESTIONS_COUNT = 5
    REASONS_PER_HERO = 5

    # ===== LOGGING =====
    LOG_SCORING_DETAILS = False
    LOG_WEIGHT_CALCULATIONS = False
