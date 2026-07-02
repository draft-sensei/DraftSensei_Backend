"""
Synergy Scorer
Evaluates how well a hero synergizes with the ally team
"""

from typing import Dict, Any, List
import logging

from ..config.draft_config import DraftConfig

logger = logging.getLogger(__name__)


class SynergyScorer:
    """Scores hero's synergy with ally team"""

    def __init__(self):
        self.config = DraftConfig()

    def calculate_synergy_score(
        self,
        hero: Dict[str, Any],
        ally_picks: List[str],
        heroes_data: Dict[str, Dict[str, Any]],
    ) -> float:
        """
        Calculate synergy with ally team (0-100)

        Synergy examples:
        - Engage tank + AoE mage
        - Crowd control + burst assassin
        - Tank + hyper carry marksman
        - Peel support + squishy damage dealer

        Args:
            hero: Hero data dictionary
            ally_picks: List of ally hero names
            heroes_data: Dictionary of all heroes' data

        Returns:
            Synergy score 0-100
        """
        if not ally_picks:
            return 60.0

        hero_meta = hero.get("meta", {})
        combat = hero_meta.get("attributes", {}).get("combat", {})
        survivability = hero_meta.get("attributes", {}).get("survivability", {})
        utility = hero_meta.get("attributes", {}).get("utility", {})
        range_style = hero_meta.get("attributes", {}).get("range_playstyle", {})

        total_synergy = 0
        ally_count = 0

        for ally_name in ally_picks:
            if ally_name not in heroes_data:
                continue

            ally = heroes_data[ally_name]
            ally_meta = ally.get("meta", {})
            ally_combat = ally_meta.get("attributes", {}).get("combat", {})
            ally_surv = ally_meta.get("attributes", {}).get("survivability", {})
            ally_util = ally_meta.get("attributes", {}).get("utility", {})
            ally_range = ally_meta.get("attributes", {}).get("range_playstyle", {})

            synergy_points = 0

            # Tank + damage dealer synergy
            hero_tankiness = survivability.get("tankiness", 0)
            ally_dps = ally_combat.get("dps", 0)
            if hero_tankiness >= 4 and ally_dps >= 4:
                synergy_points += self.config.SYNERGY_SCORING["tank_dps"]

            # Engage + AoE damage synergy
            hero_engage = range_style.get("engage", 0)
            ally_aoe = ally_combat.get("aoe_damage", 0)
            if hero_engage >= 4 and ally_aoe >= 4:
                synergy_points += self.config.SYNERGY_SCORING["engage_aoe"]

            # CC + burst damage synergy
            hero_cc = utility.get("crowd_control", 0)
            ally_burst = ally_combat.get("burst_damage", 0)
            if hero_cc >= 3 and ally_burst >= 4:
                synergy_points += self.config.SYNERGY_SCORING["cc_burst"]

            # Peel + squishy carry synergy
            hero_peel = range_style.get("peel", 0)
            ally_tankiness = ally_surv.get("tankiness", 3)
            if hero_peel >= 3 and ally_tankiness <= 2:
                synergy_points += self.config.SYNERGY_SCORING["peel_squishy"]

            # Sustain support + fighter synergy
            hero_heal = utility.get("team_heal", 0)
            hero_buff = utility.get("team_buff", 0)
            ally_sustained = ally_combat.get("sustained_damage", 0)
            if (hero_heal >= 3 or hero_buff >= 3) and ally_sustained >= 4:
                synergy_points += self.config.SYNERGY_SCORING["sustain_fighter"]

            # Double engage synergy
            ally_engage = ally_range.get("engage", 0)
            if hero_engage >= 4 and ally_engage >= 4:
                synergy_points += self.config.SYNERGY_SCORING["double_engage"]

            # Mobility synergy (dive comp)
            hero_mobility = survivability.get("mobility", 0)
            ally_mobility = ally_surv.get("mobility", 0)
            if hero_mobility >= 4 and ally_mobility >= 4:
                synergy_points += self.config.SYNERGY_SCORING["dive_comp"]

            total_synergy += min(synergy_points, 100)
            ally_count += 1

        return total_synergy / ally_count if ally_count > 0 else 60.0
