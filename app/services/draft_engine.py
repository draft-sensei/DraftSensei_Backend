"""
AI Draft Engine for Mobile Legends Hero Recommendations
"""

from typing import List, Dict, Tuple, Optional, Any
import math
from sqlalchemy.orm import Session

from ..db.models import Hero, PlayerPreference, MatchHistory
from ..schemas.draft_schema import HeroPick, DraftRequest
from .synergy import synergy_system


class DraftEngine:
    """
    Core AI engine for draft recommendations
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.synergy_system = synergy_system
        
        # Load heroes and roles from database
        self.heroes_data = self._load_heroes_data()
        self.available_heroes = list(self.heroes_data.keys())
        
        # AI weights for different factors
        self.weights = {
            "synergy": 0.25,      # Team synergy
            "counter": 0.30,      # Counter enemy picks
            "role_balance": 0.20, # Role composition balance
            "meta": 0.15,         # Meta strength/tier
            "player_pref": 0.10   # Player preference/history
        }

    def _load_heroes_data(self) -> Dict[str, Dict[str, Any]]:
        """Load heroes data from database"""
        heroes_data = {}
        
        heroes = self.db.query(Hero).all()
        for hero in heroes:
            heroes_data[hero.name] = {
                "id": hero.id,
                "role": hero.role,
                "stats": hero.get_stats(),
                "counters": hero.get_counters(),
                "synergy": hero.get_synergy()
            }
        
        return heroes_data

    def suggest_picks(self, request: DraftRequest) -> List[HeroPick]:
        """
        Main method to suggest hero picks based on current draft state
        """
        # Get available heroes (not picked or banned)
        unavailable = set(request.ally_picks + request.enemy_picks + 
                         request.ally_bans + request.enemy_bans)
        available = [h for h in self.available_heroes if h not in unavailable]
        
        if not available:
            return []
        
        # Filter by role preference if specified
        if request.role_preference:
            available = [h for h in available 
                        if self.heroes_data.get(h, {}).get("role") == request.role_preference]
        
        # Calculate scores for each available hero
        scored_heroes = []
        for hero in available:
            score, reasons = self._calculate_hero_score(hero, request)
            scored_heroes.append((hero, score, reasons))
        
        # Sort by score (descending) and return top picks
        scored_heroes.sort(key=lambda x: x[1], reverse=True)
        
        # Convert to HeroPick objects
        picks = []
        for hero, score, reasons in scored_heroes[:10]:  # Top 10
            hero_data = self.heroes_data.get(hero, {})
            pick = HeroPick(
                hero=hero,
                score=round(score, 1),
                reasons=reasons,
                role=hero_data.get("role", "Unknown"),
                confidence=self._calculate_confidence(score, len(reasons))
            )
            picks.append(pick)
        
        return picks

    def _calculate_hero_score(self, hero: str, request: DraftRequest) -> Tuple[float, List[str]]:
        """
        Calculate overall score for a hero pick
        """
        scores = {}
        reasons = []
        
        # 1. Synergy Score
        synergy_score, synergy_reasons = self._calculate_synergy_score(hero, request.ally_picks)
        scores["synergy"] = synergy_score
        reasons.extend(synergy_reasons)
        
        # 2. Counter Score  
        counter_score, counter_reasons = self._calculate_counter_score(hero, request.enemy_picks)
        scores["counter"] = counter_score
        reasons.extend(counter_reasons)
        
        # 3. Role Balance Score
        role_score, role_reasons = self._calculate_role_balance_score(hero, request.ally_picks)
        scores["role_balance"] = role_score
        reasons.extend(role_reasons)
        
        # 4. Meta Score
        meta_score, meta_reasons = self._calculate_meta_score(hero)
        scores["meta"] = meta_score
        reasons.extend(meta_reasons)
        
        # 5. Player Preference Score
        pref_score, pref_reasons = self._calculate_player_preference_score(hero, request.player_id)
        scores["player_pref"] = pref_score
        reasons.extend(pref_reasons)
        
        # Calculate weighted final score
        final_score = sum(scores[factor] * self.weights[factor] for factor in scores)
        
        # Apply bonus/penalty modifiers
        final_score = self._apply_modifiers(final_score, hero, request)
        
        return min(final_score, 100.0), reasons[:5]  # Cap at 100, limit reasons

    def _calculate_synergy_score(self, hero: str, ally_picks: List[str]) -> Tuple[float, List[str]]:
        """Calculate team synergy score"""
        if not ally_picks:
            return 60.0, []
        
        total_synergy = 0.0
        reasons = []
        hero_role = self.heroes_data.get(hero, {}).get("role", "Fighter")
        
        for ally in ally_picks:
            synergy = self.synergy_system.get_synergy_score(hero, ally)
            total_synergy += synergy
            
            if synergy >= 85:
                reasons.append(f"Excellent synergy with {ally} ({synergy:.0f})")
            elif synergy >= 75:
                reasons.append(f"Good synergy with {ally} ({synergy:.0f})")
        
        avg_synergy = total_synergy / len(ally_picks)
        
        # Role-based synergy bonus
        roles = {ally: self.heroes_data.get(ally, {}).get("role", "Fighter") for ally in ally_picks}
        roles[hero] = hero_role
        team_synergy = self.synergy_system.get_team_synergy(ally_picks + [hero], roles)
        
        # Combine individual and team synergy
        final_score = (avg_synergy * 0.7) + (team_synergy * 0.3)
        
        if team_synergy >= 80:
            reasons.append(f"Creates strong team composition ({team_synergy:.0f})")
        
        return final_score, reasons

    def _calculate_counter_score(self, hero: str, enemy_picks: List[str]) -> Tuple[float, List[str]]:
        """Calculate counter advantage score"""
        if not enemy_picks:
            return 60.0, []
        
        total_counter = 0.0
        reasons = []
        
        for enemy in enemy_picks:
            counter_strength = self.synergy_system.get_counter_score(hero, enemy)
            total_counter += counter_strength
            
            if counter_strength >= 85:
                reasons.append(f"Hard counters {enemy} ({counter_strength:.0f})")
            elif counter_strength >= 70:
                reasons.append(f"Counters {enemy} ({counter_strength:.0f})")
            elif counter_strength <= 30:
                reasons.append(f"Countered by {enemy} ({counter_strength:.0f})")
        
        avg_counter = total_counter / len(enemy_picks)
        return avg_counter, reasons

    def _calculate_role_balance_score(self, hero: str, ally_picks: List[str]) -> Tuple[float, List[str]]:
        """Calculate role balance score"""
        hero_role = self.heroes_data.get(hero, {}).get("role", "Fighter")
        
        # Count current roles
        role_count = {}
        for ally in ally_picks:
            ally_role = self.heroes_data.get(ally, {}).get("role", "Fighter")
            role_count[ally_role] = role_count.get(ally_role, 0) + 1
        
        reasons = []
        
        # Check if hero fills needed role
        needed_roles = self._get_needed_roles(role_count, len(ally_picks))
        
        if hero_role in needed_roles:
            priority = needed_roles[hero_role]
            score = 70 + (priority * 10)  # 70-100 based on priority
            if priority >= 3:
                reasons.append(f"Critically needed {hero_role}")
            else:
                reasons.append(f"Fills needed {hero_role} role")
        else:
            # Check for role oversaturation
            current_role_count = role_count.get(hero_role, 0)
            if current_role_count >= 2:
                score = 30.0  # Heavy penalty for 3+ of same role
                reasons.append(f"Too many {hero_role}s already")
            elif current_role_count == 1:
                score = 50.0  # Mild penalty for duplicate role
                reasons.append(f"Duplicate {hero_role} role")
            else:
                score = 60.0  # Neutral for first of role
        
        return score, reasons

    def _get_needed_roles(self, role_count: Dict[str, int], team_size: int) -> Dict[str, int]:
        """Determine which roles are needed and their priority"""
        needed = {}
        
        # Essential roles based on team size
        if role_count.get("Tank", 0) == 0:
            needed["Tank"] = 3  # High priority
        
        if team_size >= 3 and role_count.get("Support", 0) == 0:
            needed["Support"] = 2  # Medium priority
            
        if role_count.get("Marksman", 0) == 0:
            needed["Marksman"] = 2  # Medium priority
        
        # Always need some damage
        damage_roles = role_count.get("Mage", 0) + role_count.get("Assassin", 0)
        if damage_roles == 0:
            needed["Mage"] = 2
            needed["Assassin"] = 2
        
        return needed

    def _calculate_meta_score(self, hero: str) -> Tuple[float, List[str]]:
        """Calculate meta strength score based on recent match performance"""
        hero_data = self.heroes_data.get(hero)
        if not hero_data:
            return 50.0, []
        
        # Get recent match history for this hero
        recent_matches = (self.db.query(MatchHistory)
                         .filter(MatchHistory.hero_id == hero_data["id"])
                         .order_by(MatchHistory.timestamp.desc())
                         .limit(50)
                         .all())
        
        if not recent_matches:
            return 60.0, ["Limited match data"]
        
        # Calculate average performance
        avg_performance = sum(match.performance_score for match in recent_matches) / len(recent_matches)
        
        reasons = []
        if avg_performance >= 80:
            reasons.append(f"Strong meta performance ({avg_performance:.0f})")
        elif avg_performance >= 70:
            reasons.append(f"Good meta performance ({avg_performance:.0f})")
        elif avg_performance <= 50:
            reasons.append(f"Weak in current meta ({avg_performance:.0f})")
        
        # Convert performance to 0-100 scale
        meta_score = min(max(avg_performance, 0), 100)
        
        return meta_score, reasons

    def _calculate_player_preference_score(self, hero: str, player_id: Optional[str]) -> Tuple[float, List[str]]:
        """Calculate player preference score"""
        if not player_id:
            return 60.0, []
        
        hero_data = self.heroes_data.get(hero)
        if not hero_data:
            return 50.0, []
        
        # Get player preference for this hero
        preference = (self.db.query(PlayerPreference)
                     .filter(PlayerPreference.player_id == player_id)
                     .filter(PlayerPreference.hero_id == hero_data["id"])
                     .first())
        
        if not preference:
            return 60.0, []  # Neutral for unknown heroes
        
        reasons = []
        base_score = 60.0
        
        # Weight-based scoring
        weight_bonus = (preference.weight - 1.0) * 30  # -30 to +30 points
        score = base_score + weight_bonus
        
        # Win rate bonus/penalty
        if preference.play_count >= 5:  # Minimum games for reliability
            if preference.win_rate >= 70:
                score += 15
                reasons.append(f"High win rate ({preference.win_rate:.0f}%)")
            elif preference.win_rate <= 40:
                score -= 15
                reasons.append(f"Low win rate ({preference.win_rate:.0f}%)")
        
        # Experience bonus
        if preference.play_count >= 20:
            score += 10
            reasons.append(f"Experienced with {hero} ({preference.play_count} games)")
        elif preference.play_count == 0:
            score -= 5
            reasons.append(f"No experience with {hero}")
        
        return min(max(score, 0), 100), reasons

    def _apply_modifiers(self, base_score: float, hero: str, request: DraftRequest) -> float:
        """Apply additional modifiers to the base score"""
        score = base_score
        
        # Penalty for risky picks in certain situations
        hero_role = self.heroes_data.get(hero, {}).get("role", "Fighter")
        
        # Late game penalty for assassins if team already has burst
        if (hero_role == "Assassin" and 
            any(self.heroes_data.get(ally, {}).get("role") == "Assassin" for ally in request.ally_picks)):
            score -= 10  # Penalty for double assassin
        
        # Bonus for versatile heroes
        versatile_heroes = ["Valentina", "Paquito", "Yu Zhong", "Jawhead", "Chou"]
        if hero in versatile_heroes:
            score += 5
        
        # Meta tier adjustments (placeholder - would be updated with patch data)
        s_tier_heroes = ["Yin", "Valentina", "Khufra", "Estes", "Fanny"]
        if hero in s_tier_heroes:
            score += 8
        
        return score

    def _calculate_confidence(self, score: float, reason_count: int) -> float:
        """Calculate confidence level for the recommendation"""
        # Base confidence from score
        score_confidence = min(score / 100.0, 1.0)
        
        # Confidence from number of supporting reasons
        reason_confidence = min(reason_count / 5.0, 1.0)
        
        # Combined confidence
        confidence = (score_confidence * 0.7) + (reason_confidence * 0.3)
        
        return round(confidence, 2)

    def suggest_bans(self, request: DraftRequest) -> List[HeroPick]:
        """Suggest hero bans based on enemy strategy and meta"""
        # Get heroes that would be good against our team
        ally_roles = {ally: self.heroes_data.get(ally, {}).get("role", "Fighter") 
                     for ally in request.ally_picks}
        
        banned_heroes = set(request.ally_bans + request.enemy_bans)
        available_to_ban = [h for h in self.available_heroes if h not in banned_heroes]
        
        ban_candidates = []
        
        for hero in available_to_ban:
            # Calculate how much this hero threatens our team
            threat_score = 0.0
            reasons = []
            
            # Counter threat
            for ally in request.ally_picks:
                counter_strength = self.synergy_system.get_counter_score(hero, ally)
                threat_score += max(0, counter_strength - 50) * 0.4  # Bonus for strong counters
                
                if counter_strength >= 85:
                    reasons.append(f"Hard counters {ally}")
            
            # Meta strength
            meta_score, _ = self._calculate_meta_score(hero)
            threat_score += (meta_score - 50) * 0.3  # Bonus for meta heroes
            
            # Priority picks (deny strong heroes)
            priority_heroes = ["Yin", "Valentina", "Khufra", "Fanny", "Estes"]
            if hero in priority_heroes:
                threat_score += 20
                reasons.append("High priority meta pick")
            
            if threat_score > 0:
                hero_data = self.heroes_data.get(hero, {})
                ban_pick = HeroPick(
                    hero=hero,
                    score=min(threat_score, 100),
                    reasons=reasons,
                    role=hero_data.get("role", "Unknown")
                )
                ban_candidates.append(ban_pick)
        
        # Sort by threat score and return top bans
        ban_candidates.sort(key=lambda x: x.score, reverse=True)
        return ban_candidates[:5]

    def analyze_draft_state(self, request: DraftRequest) -> Dict[str, Any]:
        """Analyze the current draft state and provide insights"""
        ally_roles = {ally: self.heroes_data.get(ally, {}).get("role", "Fighter") 
                     for ally in request.ally_picks}
        enemy_roles = {enemy: self.heroes_data.get(enemy, {}).get("role", "Fighter") 
                      for enemy in request.enemy_picks}
        
        # Analyze ally team
        ally_analysis = self.synergy_system.analyze_team_composition(request.ally_picks, ally_roles)
        
        # Counter analysis
        if request.enemy_picks:
            counter_advantage = self.synergy_system.get_counter_advantage(
                request.ally_picks, request.enemy_picks
            )
        else:
            counter_advantage = 50.0
        
        return {
            "ally_team": ally_analysis,
            "counter_advantage": counter_advantage,
            "draft_phase": self._determine_draft_phase(request),
            "recommendations": {
                "priority_roles": self._get_needed_roles(ally_analysis["role_distribution"], len(request.ally_picks)),
                "avoid_roles": self._get_oversaturated_roles(ally_analysis["role_distribution"])
            }
        }
    
    def _determine_draft_phase(self, request: DraftRequest) -> str:
        """Determine what phase of draft we're in"""
        total_picks = len(request.ally_picks) + len(request.enemy_picks)
        
        if total_picks <= 2:
            return "early"
        elif total_picks <= 6:
            return "mid" 
        else:
            return "late"
    
    def _get_oversaturated_roles(self, role_count: Dict[str, int]) -> List[str]:
        """Get roles that have too many heroes"""
        oversaturated = []
        for role, count in role_count.items():
            if count >= 2:
                oversaturated.append(role)
        return oversaturated