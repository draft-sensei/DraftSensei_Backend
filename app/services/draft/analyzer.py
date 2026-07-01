"""
Draft Analyzer
Main orchestrator that coordinates lane selection and hero evaluation
"""

from typing import Dict, Any, List
import logging
from sqlalchemy.orm import Session

from app.db.models import Hero
from ..config.draft_config import DraftConfig
from .lane_selector import LaneSelector
from .hero_evaluator import HeroEvaluator

logger = logging.getLogger(__name__)


class DraftAnalyzer:
    """
    Main draft analysis service.
    Coordinates lane selection and hero evaluation.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.config = DraftConfig()
        self.lane_selector = LaneSelector()
        self.hero_evaluator = HeroEvaluator()

        # Load heroes data from database
        self.heroes_data = self._load_heroes_from_db()

        # Track suggestion frequency for diversity
        self.suggestion_count: Dict[str, int] = {}

    def suggest_best_lane_and_heroes(
        self,
        banned_heroes: List[str],
        enemy_picks: List[str],
        ally_picks: List[str],
    ) -> Dict[str, Any]:
        """
        Main function: suggest best lane and heroes for current draft state.

        Args:
            banned_heroes: List of banned hero names
            enemy_picks: List of enemy team picks
            ally_picks: List of ally team picks

        Returns:
            Dictionary with recommended_lane, lane_code, reasoning, and suggestions
        """
        try:
            # Step 1: Determine best lane to pick
            lane_code, lane_name, lane_reasoning = self.lane_selector.select_best_lane(
                banned_heroes, enemy_picks, ally_picks, self.heroes_data
            )

            # Step 2: Get hero suggestions for that lane
            suggestions = self._get_pick_suggestions(
                banned_heroes, enemy_picks, ally_picks, lane_code
            )

            return {
                "recommended_lane": lane_name,
                "lane_code": lane_code,
                "reasoning": lane_reasoning,
                "suggestions": suggestions,
            }

        except Exception as e:
            logger.error(f"Error in draft analysis: {e}")
            raise

    def _get_pick_suggestions(
        self,
        banned_heroes: List[str],
        enemy_picks: List[str],
        ally_picks: List[str],
        current_role: str,
    ) -> List[Dict[str, Any]]:
        """
        Get hero suggestions for a specific role.

        Args:
            banned_heroes: List of banned heroes
            enemy_picks: Enemy team picks
            ally_picks: Ally team picks
            current_role: Role to fill (exp, jungle, mid, gold, roam)

        Returns:
            List of suggested heroes with scores and reasons
        """
        # Get available heroes
        unavailable = set(banned_heroes + enemy_picks + ally_picks)
        candidates = [
            name for name in self.heroes_data.keys() if name not in unavailable
        ]

        if not candidates:
            logger.warning("No available heroes for suggestion")
            return []

        # Score each candidate
        scored_heroes = []
        for hero_name in candidates:
            try:
                hero = self.heroes_data[hero_name]
                score, reasons = self.hero_evaluator.evaluate_hero(
                    hero_name,
                    hero,
                    banned_heroes,
                    enemy_picks,
                    ally_picks,
                    current_role,
                    self.heroes_data,
                )

                # Apply diversity penalty
                diversity_penalty = self._calculate_diversity_penalty(hero_name)
                final_score = score * (1 - diversity_penalty)

                hero_role = (
                    hero.get("meta", {})
                    .get("attributes", {})
                    .get("roles", {})
                    .get("primary_role", "Unknown")
                )

                scored_heroes.append(
                    {
                        "hero": hero_name,
                        "score": round(final_score, 2),
                        "reasons": reasons,
                        "role": hero_role,
                    }
                )

            except Exception as e:
                logger.error(f"Error evaluating hero {hero_name}: {e}")
                continue

        # Sort by score and return top suggestions
        scored_heroes.sort(key=lambda x: x["score"], reverse=True)
        top_suggestions = scored_heroes[: self.config.TOP_SUGGESTIONS_COUNT]

        # Update suggestion counts for diversity tracking
        for suggestion in top_suggestions:
            hero = suggestion["hero"]
            self.suggestion_count[hero] = self.suggestion_count.get(hero, 0) + 1

        return top_suggestions

    def _calculate_diversity_penalty(self, hero_name: str) -> float:
        """
        Calculate diversity penalty for frequently suggested heroes.

        Args:
            hero_name: Name of hero

        Returns:
            Penalty factor (0.0 to 0.15)
        """
        count = self.suggestion_count.get(hero_name, 0)

        if count == 0:
            return 0.0
        elif count <= 2:
            return 0.05
        elif count <= 4:
            return 0.10
        else:
            return 0.15

    def _load_heroes_from_db(self) -> Dict[str, Dict[str, Any]]:
        """
        Load heroes with all their attributes from database.

        Returns:
            Dictionary with hero names as keys and hero data as values
        """
        try:
            heroes_data = {}
            heroes = self.db.query(Hero).all()

            for hero in heroes:
                meta = hero.get_meta()
                if meta and "attributes" in meta:
                    heroes_data[hero.name] = {
                        "name": hero.name,
                        "meta": meta,
                    }

            logger.info(f"Loaded {len(heroes_data)} heroes from database")
            return heroes_data

        except Exception as e:
            logger.error(f"Error loading heroes from database: {e}")
            return {}
