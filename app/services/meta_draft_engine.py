"""
Meta-Based Draft Engine for Mobile Legends Hero Recommendations
Uses hero meta attributes for intelligent pick suggestions
"""

from typing import List, Dict, Optional, Tuple, Any
import json
from pathlib import Path
from sqlalchemy.orm import Session

from ..db.models import Hero
from ..schemas.draft_schema import HeroPick


class MetaDraftEngine:
    """
    Advanced draft engine using hero meta attributes for scoring
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.heroes_data = self._load_heroes_from_db()
        
        # Base weights (will be dynamically adjusted per draft state)
        self.base_weights = {
            "counter": 0.35,
            "synergy": 0.25,
            "team_composition": 0.20,
            "pick_priority": 0.15,
            "role_fit": 0.05
        }
        
        # Role mappings
        self.role_map = {
            "exp": "EXP Lane",
            "jungle": "Jungle",
            "mid": "Mid Lane",
            "gold": "Gold Lane",
            "roam": "Roam"
        }
        
        # Track hero suggestion frequency for diversity
        self.suggestion_count = {}

    def _load_heroes_from_db(self) -> Dict[str, Dict[str, Any]]:
        """Load heroes with meta attributes from database"""
        heroes_data = {}
        
        heroes = self.db.query(Hero).all()
        for hero in heroes:
            meta = hero.get_meta()
            if meta and 'attributes' in meta:
                heroes_data[hero.name] = {
                    "name": hero.name,
                    "meta": meta.get('attributes', {}),
                    "reasoning": meta.get('reasoning', {})
                }
        
        return heroes_data

    def suggest_best_role_and_heroes(
        self,
        banned_heroes: List[str],
        enemy_picks: List[str],
        ally_picks: List[str]
    ) -> Dict[str, Any]:
        """
        Intelligent draft suggestion: analyze draft state and suggest best lane + heroes
        
        Args:
            banned_heroes: List of banned hero names
            enemy_picks: List of enemy team picks
            ally_picks: List of ally team picks
            
        Returns:
            Dictionary with recommended_lane and suggestions for that lane
        """
        # Determine which lanes are still open for our team
        open_lanes = self._identify_open_lanes(ally_picks)
        
        # Determine draft phase and priority
        total_picks = len(enemy_picks) + len(ally_picks)
        is_early_draft = total_picks <= 4  # First 2 rounds
        
        if is_early_draft and not ally_picks:
            # First pick: grab meta priority heroes
            recommended_lane = self._get_meta_priority_lane(enemy_picks, banned_heroes)
        else:
            # Mid/late draft: counter enemies and fill composition gaps
            recommended_lane = self._get_strategic_lane(
                enemy_picks, ally_picks, open_lanes, banned_heroes
            )
        
        # Get hero suggestions for the recommended lane
        suggestions = self.get_pick_suggestions(
            banned_heroes,
            enemy_picks,
            ally_picks,
            recommended_lane
        )
        
        return {
            "recommended_lane": self.role_map.get(recommended_lane, recommended_lane),
            "lane_code": recommended_lane,
            "suggestions": suggestions,
            "reasoning": self._explain_lane_choice(
                recommended_lane, enemy_picks, ally_picks, open_lanes, is_early_draft
            )
        }

    def _identify_open_lanes(self, ally_picks: List[str]) -> List[str]:
        """Identify which lanes are still available for our team"""
        filled_lanes = set()
        
        for hero_name in ally_picks:
            if hero_name in self.heroes_data:
                hero = self.heroes_data[hero_name]
                lanes = hero["meta"].get("roles", {}).get("lane_priority", [])
                if lanes:
                    # Assume hero takes their primary lane
                    primary_lane = lanes[0]
                    lane_code = self._lane_to_code(primary_lane)
                    filled_lanes.add(lane_code)
        
        all_lanes = ["exp", "jungle", "mid", "gold", "roam"]
        open_lanes = [lane for lane in all_lanes if lane not in filled_lanes]
        
        return open_lanes

    def _lane_to_code(self, lane_name: str) -> str:
        """Convert lane name to code"""
        reverse_map = {v: k for k, v in self.role_map.items()}
        return reverse_map.get(lane_name, lane_name.lower())

    def _get_meta_priority_lane(
        self, 
        enemy_picks: List[str], 
        banned_heroes: List[str]
    ) -> str:
        """
        First pick strategy: get meta priority heroes
        Priority order: Jungle > Mid > EXP > Gold > Roam
        """
        # If enemy already picked, counter their lane
        if enemy_picks:
            enemy_hero = enemy_picks[0]
            if enemy_hero in self.heroes_data:
                enemy_lanes = self.heroes_data[enemy_hero]["meta"].get("roles", {}).get("lane_priority", [])
                if enemy_lanes:
                    enemy_lane_code = self._lane_to_code(enemy_lanes[0])
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
        banned_heroes: List[str]
    ) -> str:
        """
        Strategic lane selection based on:
        1. Counter enemy threats (if they have strong heroes)
        2. Fill critical team composition gaps
        3. Secure remaining priority lanes
        """
        if not open_lanes:
            return "mid"  # Fallback
        
        # Score each open lane
        lane_scores = {}
        
        for lane in open_lanes:
            score = 0
            
            # 1. Counter priority: Do enemies have strong heroes in this lane?
            enemy_lane_threat = self._assess_enemy_lane_threat(lane, enemy_picks)
            score += enemy_lane_threat * 40  # 40% weight
            
            # 2. Composition gap: Do we need this lane?
            comp_need = self._assess_composition_need(lane, ally_picks)
            score += comp_need * 35  # 35% weight
            
            # 3. Lane priority: Is this a high-impact lane?
            lane_importance = {"jungle": 100, "mid": 90, "exp": 80, "gold": 75, "roam": 70}
            score += (lane_importance.get(lane, 50) / 100) * 25  # 25% weight
            
            lane_scores[lane] = score
        
        # Return lane with highest score
        best_lane = max(lane_scores, key=lane_scores.get)
        return best_lane

    def _assess_enemy_lane_threat(self, lane: str, enemy_picks: List[str]) -> float:
        """
        Assess if enemies have strong heroes in this lane (0-1)
        Returns higher score if we need to counter this lane
        """
        lane_name = self.role_map.get(lane, lane)
        threat_score = 0
        enemy_count = 0
        
        for enemy_name in enemy_picks:
            if enemy_name in self.heroes_data:
                enemy = self.heroes_data[enemy_name]
                enemy_lanes = enemy["meta"].get("roles", {}).get("lane_priority", [])
                
                if lane_name in enemy_lanes:
                    # Enemy has this lane - check their strength
                    combat = enemy["meta"].get("combat", {})
                    power = enemy["meta"].get("power_curve", {})
                    
                    strength = (
                        combat.get("dps", 0) * 0.4 +
                        combat.get("burst_damage", 0) * 0.3 +
                        power.get("late_game", 0) * 0.3
                    ) / 5  # Normalize to 0-1
                    
                    threat_score += strength
                    enemy_count += 1
        
        if enemy_count == 0:
            return 0.3  # Slight preference to fill lanes not covered by enemy
        
        return threat_score / enemy_count

    def _assess_composition_need(self, lane: str, ally_picks: List[str]) -> float:
        """
        Assess how much team needs this lane (0-1)
        Returns higher score for critical missing roles
        """
        if not ally_picks:
            return 0.5  # Neutral
        
        # Analyze current team composition
        team_stats = {
            "tankiness": 0,
            "physical_damage": 0,
            "magic_damage": 0,
            "crowd_control": 0,
            "mobility": 0
        }
        
        for ally_name in ally_picks:
            if ally_name in self.heroes_data:
                ally = self.heroes_data[ally_name]
                ally_meta = ally["meta"]
                
                team_stats["tankiness"] += ally_meta.get("survivability", {}).get("tankiness", 0)
                team_stats["crowd_control"] += ally_meta.get("utility", {}).get("crowd_control", 0)
                team_stats["mobility"] += ally_meta.get("survivability", {}).get("mobility", 0)
                
                role = ally_meta.get("roles", {}).get("primary_role", "")
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
            "roam": {"tankiness": 0.9, "crowd_control": 0.8}
        }
        
        contributions = lane_contributions.get(lane, {})
        need_score = 0
        
        # Check gaps
        if team_stats["tankiness"] < 8 and contributions.get("tankiness", 0) > 0.5:
            need_score += 0.4
        if team_stats["magic_damage"] < 5 and contributions.get("magic_damage", 0) > 0.5:
            need_score += 0.3
        if team_stats["physical_damage"] < 10 and contributions.get("physical_damage", 0) > 0.5:
            need_score += 0.3
        
        return min(need_score, 1.0)

    def _explain_lane_choice(
        self,
        lane: str,
        enemy_picks: List[str],
        ally_picks: List[str],
        open_lanes: List[str],
        is_early_draft: bool
    ) -> str:
        """Generate human-readable explanation for lane choice"""
        lane_name = self.role_map.get(lane, lane)
        
        if is_early_draft and not ally_picks:
            return f"First pick: Secure high-impact {lane_name} hero to establish early advantage"
        
        reasons = []
        
        # Check enemy threats
        enemy_in_lane = []
        for enemy_name in enemy_picks:
            if enemy_name in self.heroes_data:
                enemy_lanes = self.heroes_data[enemy_name]["meta"].get("roles", {}).get("lane_priority", [])
                if lane_name in enemy_lanes:
                    enemy_in_lane.append(enemy_name)
        
        if enemy_in_lane:
            reasons.append(f"Counter enemy {', '.join(enemy_in_lane[:2])} in {lane_name}")
        
        # Check team gaps
        if len(ally_picks) >= 2:
            reasons.append(f"Fill remaining {lane_name} position")
        
        if not reasons:
            reasons.append(f"Strategic pick for {lane_name} to strengthen team composition")
        
        return " | ".join(reasons)

    def get_pick_suggestions(
        self,
        banned_heroes: List[str],
        enemy_picks: List[str],
        ally_picks: List[str],
        current_role: str
    ) -> List[Dict[str, Any]]:
        """
        Main function to get hero pick suggestions
        
        Args:
            banned_heroes: List of banned hero names
            enemy_picks: List of enemy team picks
            ally_picks: List of ally team picks
            current_role: Current role to fill (exp, jungle, mid, gold, roam)
            
        Returns:
            List of hero suggestions with scores and reasons
        """
        # Get available heroes
        unavailable = set(banned_heroes + enemy_picks + ally_picks)
        candidates = [
            name for name in self.heroes_data.keys()
            if name not in unavailable
        ]
        
        if not candidates:
            return []
        
        # Score each candidate
        scored_heroes = []
        for hero_name in candidates:
            score, reasons = self._calculate_hero_score(
                hero_name,
                enemy_picks,
                ally_picks,
                current_role,
                banned_heroes  # Pass banned heroes for dynamic weight calculation
            )
            
            # Apply diversity penalty for frequently suggested heroes
            diversity_penalty = self._calculate_diversity_penalty(hero_name)
            final_score = score * (1 - diversity_penalty)
            
            scored_heroes.append({
                "hero": hero_name,
                "score": round(final_score, 2),
                "reasons": reasons,
                "role": self.heroes_data[hero_name]["meta"].get("roles", {}).get("primary_role", "Unknown")
            })
        
        # Sort by score and return top 5
        scored_heroes.sort(key=lambda x: x["score"], reverse=True)
        top_5 = scored_heroes[:5]
        
        # Update suggestion counts for diversity tracking
        for suggestion in top_5:
            hero = suggestion["hero"]
            self.suggestion_count[hero] = self.suggestion_count.get(hero, 0) + 1
        
        return top_5

    def _calculate_dynamic_weights(
        self,
        banned_heroes: List[str],
        enemy_picks: List[str],
        ally_picks: List[str],
        current_role: str
    ) -> Dict[str, float]:
        """
        Dynamically adjust scoring weights based on draft state.
        
        Adaptive Rules:
        1. Late draft (4+ picks) → ↑ team_comp, ↑ synergy, ↓ pick_priority
        2. Enemy pattern clear (3+ picks) → ↑ counter, ↓ synergy
        3. Missing critical role → ↑ role_fit significantly
        4. Many bans (6+) → ↑ pick_priority (avoid niche heroes)
        5. Win condition secured → ↑ synergy, ↓ counter
        """
        weights = self.base_weights.copy()
        total_picks = len(enemy_picks) + len(ally_picks)
        
        # Rule 1: Late draft - focus on composition and synergy
        if total_picks >= 4:
            weights["team_composition"] += 0.10
            weights["synergy"] += 0.10
            weights["pick_priority"] -= 0.10
            reasons_debug = ["Late draft: +team_comp, +synergy"]
        
        # Rule 2: Enemy pattern clear - prioritize counters
        if len(enemy_picks) >= 3:
            weights["counter"] += 0.15
            weights["synergy"] -= 0.10
            reasons_debug = ["Enemy pattern clear: +counter"]
        
        # Rule 3: Check for missing critical roles
        missing_roles = self._identify_missing_roles(ally_picks)
        if current_role and self.role_map.get(current_role) in missing_roles:
            weights["role_fit"] += 0.15
            weights["pick_priority"] -= 0.05
            reasons_debug = [f"Missing {current_role}: +role_fit"]
        
        # Rule 4: Many bans - avoid weak niche picks
        if len(banned_heroes) >= 6:
            weights["pick_priority"] += 0.05
            reasons_debug = ["Many bans: +pick_priority"]
        
        # Rule 5: Win condition check (high DPS hero already picked)
        if self._has_win_condition(ally_picks):
            weights["synergy"] += 0.10
            weights["counter"] -= 0.05
            reasons_debug = ["Win condition secured: +synergy"]
        
        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights

    def _identify_missing_roles(self, ally_picks: List[str]) -> List[str]:
        """Identify which lanes/roles are missing from team"""
        filled_roles = set()
        
        for hero_name in ally_picks:
            if hero_name in self.heroes_data:
                hero = self.heroes_data[hero_name]
                lanes = hero["meta"].get("roles", {}).get("lane_priority", [])
                if lanes:
                    filled_roles.add(lanes[0])  # Primary lane
        
        all_lanes = ["EXP Lane", "Jungle", "Mid Lane", "Gold Lane", "Roam"]
        missing = [lane for lane in all_lanes if lane not in filled_roles]
        
        return missing

    def _has_win_condition(self, ally_picks: List[str]) -> bool:
        """Check if team has a strong carry/win condition hero"""
        for hero_name in ally_picks:
            if hero_name in self.heroes_data:
                hero = self.heroes_data[hero_name]
                combat = hero["meta"].get("combat", {})
                power = hero["meta"].get("power_curve", {})
                
                # High DPS + late game scaling = win condition
                dps = combat.get("dps", 0)
                late_game = power.get("late_game", 0)
                scaling = power.get("scaling", 0)
                
                if dps >= 4 and (late_game >= 4 or scaling >= 4):
                    return True
        
        return False

    def _calculate_hero_score(
        self,
        hero_name: str,
        enemy_picks: List[str],
        ally_picks: List[str],
        current_role: str,
        banned_heroes: List[str] = None
    ) -> Tuple[float, List[str]]:
        """Calculate final score for a hero with DYNAMIC weights"""
        hero = self.heroes_data[hero_name]
        reasons = []
        
        if banned_heroes is None:
            banned_heroes = []
        
        # Get dynamic weights based on current draft state
        weights = self._calculate_dynamic_weights(
            banned_heroes, enemy_picks, ally_picks, current_role
        )
        
        # 1. Counter Score
        counter_score = self._calculate_counter_score(hero, enemy_picks)
        if counter_score > 70:
            reasons.append(f"Strong counter against enemy team ({counter_score:.0f}/100)")
        
        # 2. Synergy Score
        synergy_score = self._calculate_synergy_score(hero, ally_picks)
        if synergy_score > 70:
            reasons.append(f"Excellent synergy with allies ({synergy_score:.0f}/100)")
        
        # 3. Team Composition Score
        comp_score = self._calculate_team_composition_score(hero, ally_picks)
        if comp_score > 70:
            reasons.append("Fills critical team composition gap")
        
        # 4. Pick Priority Score
        priority_score = self._calculate_pick_priority_score(hero)
        if priority_score > 75:
            reasons.append("High meta strength hero")
        
        # 5. Lane Fit Score - Based on lane_priority from meta
        lane_score = self._calculate_role_fit_score(hero, current_role)
        lane_name = self.role_map.get(current_role, current_role)
        if lane_score >= 100:
            reasons.append(f"Primary lane: {lane_name}")
        elif lane_score >= 75:
            reasons.append(f"Viable for {lane_name}")
        elif lane_score >= 50:
            reasons.append(f"Situational pick for {lane_name}")
        elif lane_score < 30:
            reasons.append(f"Not suited for {lane_name}")
        
        # Calculate weighted final score using DYNAMIC weights
        final_score = (
            counter_score * weights["counter"] +
            synergy_score * weights["synergy"] +
            comp_score * weights["team_composition"] +
            priority_score * weights["pick_priority"] +
            lane_score * weights["role_fit"]
        )
        
        # Add weight info to top picks for debugging
        if final_score > 75:
            weight_info = f"Weights: C={weights['counter']:.0%} S={weights['synergy']:.0%} T={weights['team_composition']:.0%}"
            # reasons.append(weight_info)  # Optional: show weights
        
        # Add detailed breakdown if score is high
        if final_score > 80:
            reasons.insert(0, f"Top tier pick (Score: {final_score:.1f})")
        
        return final_score, reasons[:5]  # Limit to 5 reasons

    def _calculate_diversity_penalty(self, hero_name: str) -> float:
        """
        Calculate diversity penalty for frequently suggested heroes
        Returns penalty factor (0.0 to 0.15)
        """
        count = self.suggestion_count.get(hero_name, 0)
        if count == 0:
            return 0.0
        elif count <= 2:
            return 0.05  # 5% penalty
        elif count <= 4:
            return 0.10  # 10% penalty
        else:
            return 0.15  # 15% penalty for excessive suggestions

    def _calculate_counter_score(self, hero: Dict, enemy_picks: List[str]) -> float:
        """
        Calculate how well hero counters enemy team (0-100)
        
        Logic:
        - High anti_squishy vs low tankiness enemies
        - High anti_tank vs high tankiness enemies
        - High mobility vs high crowd_control enemies
        - High poke vs short range enemies
        - High engage vs low mobility enemies
        """
        if not enemy_picks:
            return 60.0  # Neutral score
        
        hero_meta = hero["meta"]
        combat = hero_meta.get("combat", {})
        survivability = hero_meta.get("survivability", {})
        utility = hero_meta.get("utility", {})
        range_style = hero_meta.get("range_playstyle", {})
        
        total_counter_score = 0
        enemy_count = 0
        
        for enemy_name in enemy_picks:
            if enemy_name not in self.heroes_data:
                continue
            
            enemy = self.heroes_data[enemy_name]
            enemy_meta = enemy["meta"]
            enemy_combat = enemy_meta.get("combat", {})
            enemy_surv = enemy_meta.get("survivability", {})
            enemy_util = enemy_meta.get("utility", {})
            enemy_range = enemy_meta.get("range_playstyle", {})
            
            counter_points = 0
            
            # Anti-squishy vs squishy enemies (STRICTER: require high anti-squishy)
            enemy_tankiness = enemy_surv.get("tankiness", 3)
            hero_anti_squishy = combat.get("anti_squishy", 0)
            if enemy_tankiness <= 2 and hero_anti_squishy >= 4:
                counter_points += hero_anti_squishy * 5  # Max +25 (stronger bonus)
            elif enemy_tankiness <= 2 and hero_anti_squishy >= 3:
                counter_points += hero_anti_squishy * 3  # Max +15 (moderate)
            
            # Anti-tank vs tanky enemies (STRICTER: require actual anti-tank)
            hero_anti_tank = combat.get("anti_tank", 0)
            if enemy_tankiness >= 4 and hero_anti_tank >= 4:
                counter_points += hero_anti_tank * 5  # Max +25
            elif enemy_tankiness >= 4 and hero_anti_tank >= 3:
                counter_points += hero_anti_tank * 3  # Max +15
            
            # Mobility vs lockdown (STRICTER: must have high mobility to escape)
            enemy_cc = enemy_util.get("crowd_control", 0)
            hero_mobility = survivability.get("mobility", 0)
            hero_escape = survivability.get("escape", 0)
            if enemy_cc >= 4 and (hero_mobility >= 4 or hero_escape >= 4):
                counter_points += 20
            elif enemy_cc >= 3 and (hero_mobility >= 3 or hero_escape >= 3):
                counter_points += 10
            
            # Poke vs short range (require actual poke damage)
            enemy_range_val = enemy_range.get("range", 3)
            hero_poke = combat.get("poke", 0)
            if enemy_range_val <= 2 and hero_poke >= 4:
                counter_points += hero_poke * 4  # Max +20
            elif enemy_range_val <= 2 and hero_poke >= 3:
                counter_points += hero_poke * 2  # Max +10
            
            # Engage vs low mobility (need strong engage)
            enemy_mobility = enemy_surv.get("mobility", 3)
            hero_engage = range_style.get("engage", 0)
            if enemy_mobility <= 2 and hero_engage >= 4:
                counter_points += hero_engage * 4  # Max +20
            
            # Burst damage vs low defense (must have BOTH high burst AND enemy lacks defense)
            enemy_shields = enemy_surv.get("shields", 0)
            enemy_regen = enemy_surv.get("regen", 0)
            hero_burst = combat.get("burst_damage", 0)
            if (enemy_shields + enemy_regen <= 3) and hero_burst >= 4:
                counter_points += hero_burst * 4  # Max +20
            elif (enemy_shields + enemy_regen <= 3) and hero_burst >= 3:
                counter_points += hero_burst * 2  # Max +10
            
            total_counter_score += min(counter_points, 100)
            enemy_count += 1
        
        return total_counter_score / enemy_count if enemy_count > 0 else 60.0

    def _calculate_synergy_score(self, hero: Dict, ally_picks: List[str]) -> float:
        """
        Calculate synergy with ally team (0-100)
        
        Synergy examples:
        - Engage tank + AoE mage
        - Crowd control + burst assassin
        - Tank + hyper carry marksman
        - Peel support + squishy damage dealer
        """
        if not ally_picks:
            return 60.0
        
        hero_meta = hero["meta"]
        combat = hero_meta.get("combat", {})
        survivability = hero_meta.get("survivability", {})
        utility = hero_meta.get("utility", {})
        range_style = hero_meta.get("range_playstyle", {})
        
        total_synergy = 0
        ally_count = 0
        
        for ally_name in ally_picks:
            if ally_name not in self.heroes_data:
                continue
            
            ally = self.heroes_data[ally_name]
            ally_meta = ally["meta"]
            ally_combat = ally_meta.get("combat", {})
            ally_surv = ally_meta.get("survivability", {})
            ally_util = ally_meta.get("utility", {})
            ally_range = ally_meta.get("range_playstyle", {})
            
            synergy_points = 0
            
            # Tank + damage dealer synergy
            hero_tankiness = survivability.get("tankiness", 0)
            ally_dps = ally_combat.get("dps", 0)
            if hero_tankiness >= 4 and ally_dps >= 4:
                synergy_points += 20
            
            # Engage + AoE damage synergy
            hero_engage = range_style.get("engage", 0)
            ally_aoe = ally_combat.get("aoe_damage", 0)
            if hero_engage >= 4 and ally_aoe >= 4:
                synergy_points += 25
            
            # CC + burst damage synergy
            hero_cc = utility.get("crowd_control", 0)
            ally_burst = ally_combat.get("burst_damage", 0)
            if hero_cc >= 3 and ally_burst >= 4:
                synergy_points += 20
            
            # Peel + squishy carry synergy
            hero_peel = range_style.get("peel", 0)
            ally_tankiness = ally_surv.get("tankiness", 3)
            if hero_peel >= 3 and ally_tankiness <= 2:
                synergy_points += 18
            
            # Sustain support + fighter synergy
            hero_heal = utility.get("team_heal", 0)
            hero_buff = utility.get("team_buff", 0)
            ally_sustained = ally_combat.get("sustained_damage", 0)
            if (hero_heal >= 3 or hero_buff >= 3) and ally_sustained >= 4:
                synergy_points += 22
            
            # Double engage synergy
            ally_engage = ally_range.get("engage", 0)
            if hero_engage >= 4 and ally_engage >= 4:
                synergy_points += 15
            
            # Mobility synergy (dive comp)
            hero_mobility = survivability.get("mobility", 0)
            ally_mobility = ally_surv.get("mobility", 0)
            if hero_mobility >= 4 and ally_mobility >= 4:
                synergy_points += 12
            
            total_synergy += min(synergy_points, 100)
            ally_count += 1
        
        return total_synergy / ally_count if ally_count > 0 else 60.0

    def _calculate_team_composition_score(self, hero: Dict, ally_picks: List[str]) -> float:
        """
        Calculate how well hero fills team composition gaps (0-100)
        
        Checks for:
        - Missing tankiness
        - Missing magic damage
        - Missing physical damage
        - Missing crowd control
        - Missing engage
        - Missing waveclear
        """
        hero_meta = hero["meta"]
        combat = hero_meta.get("combat", {})
        survivability = hero_meta.get("survivability", {})
        utility = hero_meta.get("utility", {})
        range_style = hero_meta.get("range_playstyle", {})
        roles = hero_meta.get("roles", {})
        
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
            "sustained": 0
        }
        
        for ally_name in ally_picks:
            if ally_name not in self.heroes_data:
                continue
            
            ally = self.heroes_data[ally_name]
            ally_meta = ally["meta"]
            ally_combat = ally_meta.get("combat", {})
            ally_surv = ally_meta.get("survivability", {})
            ally_util = ally_meta.get("utility", {})
            ally_range = ally_meta.get("range_playstyle", {})
            ally_roles = ally_meta.get("roles", {})
            
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
        if len(ally_picks) >= 2 and team_stats["tankiness"] < 8:
            max_gaps += 15
            if survivability.get("tankiness", 0) >= 4:
                gaps_filled += 15
        
        # Magic damage gap
        if team_stats["magic_damage"] < 10:
            max_gaps += 15
            if roles.get("primary_role") == "Mage":
                gaps_filled += 15
        
        # Physical damage gap
        if team_stats["physical_damage"] < 10:
            max_gaps += 15
            if roles.get("primary_role") in ["Marksman", "Assassin", "Fighter"]:
                gaps_filled += 15
        
        # Crowd control gap
        if team_stats["crowd_control"] < 5:
            max_gaps += 10
            if utility.get("crowd_control", 0) >= 3:
                gaps_filled += 10
        
        # Engage gap
        if team_stats["engage"] < 8:
            max_gaps += 12
            if range_style.get("engage", 0) >= 4:
                gaps_filled += 12
        
        # Waveclear gap
        if team_stats["waveclear"] < 8:
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
        role_count = sum(1 for ally_name in ally_picks 
                        if ally_name in self.heroes_data and 
                        self.heroes_data[ally_name]["meta"].get("roles", {}).get("primary_role") == hero_role)
        
        if role_count >= 2:
            gaps_filled -= 15  # Penalty for role redundancy
        
        # Calculate final score
        if max_gaps == 0:
            return 60.0  # Neutral if no gaps
        
        score = (gaps_filled / max_gaps) * 100
        return max(min(score, 100), 0)

    def _calculate_pick_priority_score(self, hero: Dict) -> float:
        """
        Calculate pick priority based on overall hero strength (0-100)
        
        UPDATED: More balanced approach, penalize "perfect" stat heroes
        """
        hero_meta = hero["meta"]
        combat = hero_meta.get("combat", {})
        survivability = hero_meta.get("survivability", {})
        power_curve = hero_meta.get("power_curve", {})
        utility = hero_meta.get("utility", {})
        
        # Average combat effectiveness (capped to prevent inflation)
        combat_stats = [
            combat.get("burst_damage", 0),
            combat.get("sustained_damage", 0),
            combat.get("dps", 0),
            combat.get("aoe_damage", 0)
        ]
        combat_score = sum(combat_stats) / 4
        
        # Survivability score
        surv_stats = [
            survivability.get("tankiness", 0),
            survivability.get("mobility", 0),
            survivability.get("escape", 0)
        ]
        surv_score = sum(surv_stats) / 3
        
        # Power curve - balanced across game stages
        power_score = (
            power_curve.get("early_game", 0) * 0.2 +
            power_curve.get("mid_game", 0) * 0.35 +
            power_curve.get("late_game", 0) * 0.35 +
            power_curve.get("scaling", 0) * 0.1
        )
        
        # Utility score
        utility_score = utility.get("crowd_control", 0)
        
        # Combined score with balanced weights
        priority = (
            combat_score * 0.35 +
            surv_score * 0.25 +
            power_score * 0.30 +
            utility_score * 0.10
        ) * 20  # Scale to 100
        
        # PENALTY: Heroes with suspiciously perfect stats (likely overrated)
        perfect_stat_count = sum(1 for stat in combat_stats + surv_stats if stat >= 5)
        if perfect_stat_count >= 5:
            priority *= 0.85  # 15% penalty for 5+ perfect stats
        elif perfect_stat_count >= 4:
            priority *= 0.90  # 10% penalty for 4 perfect stats
        elif perfect_stat_count >= 3:
            priority *= 0.95  # 5% penalty for 3 perfect stats
        
        return min(priority, 100)

    def _calculate_role_fit_score(self, hero: Dict, current_role: str) -> float:
        """
        Calculate how well hero fits the requested lane (0-100)
        
        UPDATED: Focus on lane_priority from meta data (more accurate than role)
        Lane priority reflects actual gameplay: Mid (Mage), EXP (Fighter), 
        Gold (Marksman/Fighter), Jungle (Assassin/Tank), Roam (Tank/Support)
        """
        hero_meta = hero["meta"]
        roles = hero_meta.get("roles", {})
        
        lane_priorities = roles.get("lane_priority", [])
        target_lane = self.role_map.get(current_role, current_role)
        
        # Primary scoring: Lane priority is the most accurate indicator
        if target_lane in lane_priorities:
            lane_index = lane_priorities.index(target_lane)
            if lane_index == 0:
                return 100  # Primary lane - perfect fit
            elif lane_index == 1:
                return 75   # Secondary lane - viable option
            elif lane_index == 2:
                return 50   # Tertiary lane - situational pick
            else:
                return 30   # Lower priority lane - uncommon but possible
        
        # If hero has no lane priority data, severe penalty
        # (This means hero likely doesn't belong in this lane at all)
        return 5  # Very harsh penalty for no lane match


def get_pick_suggestions(
    db_session: Session,
    banned_heroes: List[str],
    enemy_picks: List[str],
    ally_picks: List[str],
    current_role: str
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Convenience function for getting pick suggestions
    
    Args:
        db_session: Database session
        banned_heroes: List of banned heroes
        enemy_picks: Enemy team picks
        ally_picks: Ally team picks
        current_role: Role to fill (exp, jungle, mid, gold, roam)
        
    Returns:
        Dictionary with suggestions list
    """
    engine = MetaDraftEngine(db_session)
    suggestions = engine.get_pick_suggestions(
        banned_heroes,
        enemy_picks,
        ally_picks,
        current_role
    )
    
    return {"suggestions": suggestions}
