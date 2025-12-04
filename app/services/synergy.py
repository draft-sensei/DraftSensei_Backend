"""
Hero synergy and counter relationship system for Mobile Legends
"""

from typing import Dict, List, Set
import json


class SynergySystem:
    """
    Manages hero synergy and counter relationships
    """

    def __init__(self):
        self.synergy_data = self._load_synergy_data()
        self.counter_data = self._load_counter_data()
        self.role_synergies = self._load_role_synergies()

    def _load_synergy_data(self) -> Dict[str, Dict[str, float]]:
        """
        Load hero-to-hero synergy data
        Returns: {hero_name: {partner_hero: synergy_score}}
        """
        return {
            # Tank synergies
            "Lolita": {
                "Yin": 85.0, "Paquito": 80.0, "Hanabi": 75.0, "Chang'e": 82.0,
                "Floryn": 88.0, "Cecilion": 79.0, "Granger": 77.0
            },
            "Khufra": {
                "Yin": 90.0, "Franco": 85.0, "Gusion": 87.0, "Fanny": 89.0,
                "Hanabi": 82.0, "Pharsa": 84.0, "Valentina": 86.0
            },
            "Franco": {
                "Khufra": 85.0, "Yin": 88.0, "Paquito": 83.0, "Clint": 80.0,
                "Chang'e": 85.0, "Pharsa": 87.0, "Moskov": 81.0
            },
            "Johnson": {
                "Odette": 95.0, "Aurora": 92.0, "Vale": 88.0, "Cecilion": 87.0,
                "Chang'e": 90.0, "Pharsa": 89.0, "Zhask": 85.0
            },

            # Fighter synergies  
            "Yin": {
                "Lolita": 85.0, "Khufra": 90.0, "Franco": 88.0, "Floryn": 82.0,
                "Estes": 80.0, "Mathilda": 84.0, "Rafaela": 79.0
            },
            "Paquito": {
                "Lolita": 80.0, "Franco": 83.0, "Floryn": 85.0, "Estes": 87.0,
                "Mathilda": 82.0, "Angela": 84.0, "Diggie": 81.0
            },
            "Yu Zhong": {
                "Angela": 88.0, "Estes": 85.0, "Floryn": 87.0, "Mathilda": 83.0,
                "Rafaela": 80.0, "Diggie": 82.0, "Faramis": 79.0
            },

            # Assassin synergies
            "Gusion": {
                "Khufra": 87.0, "Johnson": 85.0, "Diggie": 88.0, "Mathilda": 90.0,
                "Angela": 86.0, "Kaja": 89.0, "Franco": 84.0
            },
            "Fanny": {
                "Khufra": 89.0, "Angela": 92.0, "Diggie": 87.0, "Mathilda": 88.0,
                "Kaja": 86.0, "Johnson": 85.0, "Franco": 83.0
            },
            "Ling": {
                "Angela": 90.0, "Mathilda": 88.0, "Diggie": 85.0, "Kaja": 87.0,
                "Johnson": 84.0, "Khufra": 86.0, "Franco": 82.0
            },

            # Mage synergies
            "Chang'e": {
                "Lolita": 82.0, "Franco": 85.0, "Johnson": 90.0, "Atlas": 87.0,
                "Tigreal": 84.0, "Hylos": 83.0, "Grock": 81.0
            },
            "Pharsa": {
                "Khufra": 84.0, "Franco": 87.0, "Johnson": 89.0, "Atlas": 86.0,
                "Tigreal": 85.0, "Grock": 83.0, "Hylos": 82.0
            },
            "Valentina": {
                "Khufra": 86.0, "Johnson": 88.0, "Atlas": 90.0, "Franco": 84.0,
                "Tigreal": 87.0, "Grock": 85.0, "Hylos": 86.0
            },
            "Cecilion": {
                "Lolita": 79.0, "Johnson": 87.0, "Atlas": 85.0, "Franco": 82.0,
                "Tigreal": 84.0, "Grock": 83.0, "Hylos": 81.0
            },

            # Marksman synergies
            "Hanabi": {
                "Lolita": 75.0, "Khufra": 82.0, "Franco": 78.0, "Johnson": 80.0,
                "Atlas": 84.0, "Tigreal": 81.0, "Grock": 79.0
            },
            "Granger": {
                "Lolita": 77.0, "Khufra": 83.0, "Franco": 80.0, "Johnson": 82.0,
                "Atlas": 85.0, "Tigreal": 83.0, "Grock": 81.0
            },
            "Clint": {
                "Franco": 80.0, "Johnson": 84.0, "Atlas": 87.0, "Tigreal": 85.0,
                "Grock": 83.0, "Khufra": 82.0, "Lolita": 79.0
            },
            "Moskov": {
                "Franco": 81.0, "Johnson": 83.0, "Atlas": 86.0, "Tigreal": 84.0,
                "Grock": 82.0, "Khufra": 85.0, "Lolita": 80.0
            },

            # Support synergies
            "Floryn": {
                "Lolita": 88.0, "Yin": 82.0, "Paquito": 85.0, "Yu Zhong": 87.0,
                "Aulus": 83.0, "Lapu-Lapu": 84.0, "Silvanna": 86.0
            },
            "Estes": {
                "Yin": 80.0, "Paquito": 87.0, "Yu Zhong": 85.0, "Aulus": 88.0,
                "Lapu-Lapu": 86.0, "Silvanna": 84.0, "Martis": 83.0
            },
            "Mathilda": {
                "Yin": 84.0, "Gusion": 90.0, "Fanny": 88.0, "Ling": 88.0,
                "Lancelot": 87.0, "Hayabusa": 85.0, "Harley": 86.0
            },
            "Angela": {
                "Paquito": 84.0, "Yu Zhong": 88.0, "Fanny": 92.0, "Ling": 90.0,
                "Gusion": 86.0, "Lancelot": 89.0, "Hayabusa": 87.0
            }
        }

    def _load_counter_data(self) -> Dict[str, Dict[str, float]]:
        """
        Load hero counter relationships
        Returns: {hero_name: {countered_hero: counter_strength}}
        """
        return {
            # Tank counters
            "Khufra": {
                "Fanny": 95.0, "Gusion": 88.0, "Ling": 90.0, "Lancelot": 85.0,
                "Hayabusa": 82.0, "Harley": 80.0, "Kagura": 83.0
            },
            "Franco": {
                "Chang'e": 88.0, "Pharsa": 90.0, "Cecilion": 85.0, "Zhask": 87.0,
                "Valentina": 82.0, "Lylia": 84.0, "Lunox": 83.0
            },
            "Johnson": {
                "Hanabi": 87.0, "Granger": 85.0, "Clint": 88.0, "Moskov": 86.0,
                "Wanwan": 90.0, "Brody": 84.0, "Beatrix": 83.0
            },

            # Fighter counters
            "Yin": {
                "Valentina": 92.0, "Chang'e": 88.0, "Pharsa": 85.0, "Cecilion": 87.0,
                "Zhask": 84.0, "Lylia": 86.0, "Lunox": 83.0
            },
            "Paquito": {
                "Hanabi": 89.0, "Granger": 87.0, "Clint": 85.0, "Moskov": 88.0,
                "Wanwan": 86.0, "Brody": 90.0, "Beatrix": 84.0
            },
            "Yu Zhong": {
                "Lancelot": 88.0, "Gusion": 85.0, "Fanny": 82.0, "Ling": 84.0,
                "Hayabusa": 87.0, "Harley": 89.0, "Kagura": 86.0
            },

            # Assassin counters  
            "Gusion": {
                "Chang'e": 90.0, "Pharsa": 88.0, "Cecilion": 92.0, "Zhask": 87.0,
                "Valentina": 85.0, "Lylia": 89.0, "Lunox": 86.0
            },
            "Fanny": {
                "Hanabi": 85.0, "Granger": 88.0, "Clint": 90.0, "Moskov": 87.0,
                "Wanwan": 84.0, "Brody": 89.0, "Beatrix": 86.0
            },
            "Ling": {
                "Cecilion": 88.0, "Chang'e": 86.0, "Pharsa": 90.0, "Zhask": 85.0,
                "Valentina": 87.0, "Lylia": 84.0, "Lunox": 89.0
            },

            # Mage counters
            "Valentina": {
                "Estes": 95.0, "Angela": 90.0, "Floryn": 88.0, "Mathilda": 85.0,
                "Rafaela": 87.0, "Diggie": 82.0, "Kaja": 84.0
            },
            "Chang'e": {
                "Lolita": 85.0, "Franco": 82.0, "Johnson": 80.0, "Atlas": 88.0,
                "Tigreal": 86.0, "Grock": 84.0, "Hylos": 83.0
            },
            "Esmeralda": {
                "Chang'e": 92.0, "Pharsa": 90.0, "Cecilion": 88.0, "Valentina": 85.0,
                "Zhask": 87.0, "Lylia": 89.0, "Lunox": 86.0
            },

            # Support counters
            "Diggie": {
                "Khufra": 88.0, "Franco": 85.0, "Atlas": 90.0, "Tigreal": 87.0,
                "Johnson": 84.0, "Grock": 86.0, "Hylos": 83.0
            },
            "Mathilda": {
                "Yu Zhong": 85.0, "Paquito": 82.0, "Aulus": 88.0, "Lapu-Lapu": 86.0,
                "Silvanna": 84.0, "Martis": 87.0, "Jawhead": 83.0
            }
        }

    def _load_role_synergies(self) -> Dict[str, Dict[str, float]]:
        """
        Load role-based synergy modifiers
        """
        return {
            "Tank": {
                "Fighter": 80.0, "Assassin": 75.0, "Mage": 85.0, 
                "Marksman": 90.0, "Support": 70.0
            },
            "Fighter": {
                "Tank": 80.0, "Assassin": 70.0, "Mage": 75.0,
                "Marksman": 65.0, "Support": 85.0
            },
            "Assassin": {
                "Tank": 75.0, "Fighter": 70.0, "Mage": 60.0,
                "Marksman": 65.0, "Support": 90.0
            },
            "Mage": {
                "Tank": 85.0, "Fighter": 75.0, "Assassin": 60.0,
                "Marksman": 70.0, "Support": 80.0
            },
            "Marksman": {
                "Tank": 90.0, "Fighter": 65.0, "Assassin": 65.0,
                "Mage": 70.0, "Support": 85.0
            },
            "Support": {
                "Tank": 70.0, "Fighter": 85.0, "Assassin": 90.0,
                "Mage": 80.0, "Marksman": 85.0
            }
        }

    def get_synergy_score(self, hero1: str, hero2: str) -> float:
        """
        Get synergy score between two heroes
        """
        # Check direct synergy data
        if hero1 in self.synergy_data and hero2 in self.synergy_data[hero1]:
            return self.synergy_data[hero1][hero2]
        
        if hero2 in self.synergy_data and hero1 in self.synergy_data[hero2]:
            return self.synergy_data[hero2][hero1]
        
        # Default to moderate synergy
        return 60.0

    def get_counter_score(self, countering_hero: str, target_hero: str) -> float:
        """
        Get how well countering_hero counters target_hero
        """
        if countering_hero in self.counter_data and target_hero in self.counter_data[countering_hero]:
            return self.counter_data[countering_hero][target_hero]
        
        return 50.0  # Neutral counter score

    def get_team_synergy(self, heroes: List[str], roles: Dict[str, str]) -> float:
        """
        Calculate overall team synergy score
        """
        if len(heroes) < 2:
            return 100.0
        
        total_score = 0.0
        pair_count = 0
        
        # Calculate pairwise synergies
        for i in range(len(heroes)):
            for j in range(i + 1, len(heroes)):
                hero1, hero2 = heroes[i], heroes[j]
                score = self.get_synergy_score(hero1, hero2)
                
                # Apply role synergy modifier
                role1 = roles.get(hero1, "Fighter")
                role2 = roles.get(hero2, "Fighter")
                
                if role1 in self.role_synergies and role2 in self.role_synergies[role1]:
                    role_modifier = self.role_synergies[role1][role2] / 100.0
                    score *= role_modifier
                
                total_score += score
                pair_count += 1
        
        return total_score / pair_count if pair_count > 0 else 60.0

    def get_counter_advantage(self, our_heroes: List[str], enemy_heroes: List[str]) -> float:
        """
        Calculate counter advantage against enemy team
        """
        if not enemy_heroes:
            return 50.0
        
        total_counter = 0.0
        counter_count = 0
        
        for our_hero in our_heroes:
            for enemy_hero in enemy_heroes:
                counter_score = self.get_counter_score(our_hero, enemy_hero)
                total_counter += counter_score
                counter_count += 1
        
        return total_counter / counter_count if counter_count > 0 else 50.0

    def get_best_synergy_partners(self, hero: str, available_heroes: List[str], top_n: int = 5) -> List[tuple]:
        """
        Get best synergy partners for a hero from available options
        Returns: List of (hero_name, synergy_score) tuples
        """
        partners = []
        
        for available_hero in available_heroes:
            if available_hero != hero:
                synergy = self.get_synergy_score(hero, available_hero)
                partners.append((available_hero, synergy))
        
        # Sort by synergy score and return top N
        partners.sort(key=lambda x: x[1], reverse=True)
        return partners[:top_n]

    def get_best_counters(self, target_heroes: List[str], available_heroes: List[str], top_n: int = 5) -> List[tuple]:
        """
        Get best counter picks from available heroes
        Returns: List of (hero_name, average_counter_score) tuples
        """
        counters = []
        
        for available_hero in available_heroes:
            total_counter = 0.0
            for target_hero in target_heroes:
                total_counter += self.get_counter_score(available_hero, target_hero)
            
            avg_counter = total_counter / len(target_heroes) if target_heroes else 50.0
            counters.append((available_hero, avg_counter))
        
        # Sort by counter score and return top N
        counters.sort(key=lambda x: x[1], reverse=True)
        return counters[:top_n]

    def analyze_team_composition(self, heroes: List[str], roles: Dict[str, str]) -> Dict[str, any]:
        """
        Analyze team composition strengths and weaknesses
        """
        role_count = {}
        for hero in heroes:
            role = roles.get(hero, "Fighter")
            role_count[role] = role_count.get(role, 0) + 1
        
        synergy_score = self.get_team_synergy(heroes, roles)
        
        # Identify composition type
        strengths = []
        weaknesses = []
        
        # Check role balance
        if role_count.get("Tank", 0) >= 1:
            strengths.append("Good frontline presence")
        else:
            weaknesses.append("Lacks tank protection")
        
        if role_count.get("Support", 0) >= 1:
            strengths.append("Good team sustain")
        else:
            weaknesses.append("Limited team support")
        
        if role_count.get("Marksman", 0) >= 1:
            strengths.append("Strong late game damage")
        
        if role_count.get("Assassin", 0) >= 2:
            strengths.append("High burst potential")
            weaknesses.append("May lack sustained damage")
        
        # Check for excessive role stacking
        for role, count in role_count.items():
            if count >= 3:
                weaknesses.append(f"Too many {role}s - lacks role diversity")
        
        return {
            "synergy_score": synergy_score,
            "role_distribution": role_count,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "composition_type": self._determine_comp_type(role_count)
        }
    
    def _determine_comp_type(self, role_count: Dict[str, int]) -> str:
        """Determine team composition type"""
        if role_count.get("Assassin", 0) >= 2:
            return "Burst/Dive Composition"
        elif role_count.get("Mage", 0) >= 2:
            return "Poke/Magic Composition"
        elif role_count.get("Tank", 0) >= 2:
            return "Tank/Sustain Composition"
        elif role_count.get("Fighter", 0) >= 2:
            return "Bruiser Composition"
        else:
            return "Balanced Composition"


# Global instance
synergy_system = SynergySystem()