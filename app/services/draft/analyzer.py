"""
Draft Analyzer
Main orchestrator - coordinates lane selection and hero evaluation.
"""

from typing import Dict, Any, List
import logging
from sqlalchemy.orm import Session

from app.db.models import Hero
from app.services.config.draft_config import DraftConfig
from .lane_selector import LaneSelector
from .hero_evaluator import HeroEvaluator

logger = logging.getLogger(__name__)


class DraftAnalyzer:
    """
    Main draft analysis service.
    Flow:
      1. Load all heroes from DB
      2. Identify best lane to fill (LaneSelector)
      3. Score all valid heroes for that lane (HeroEvaluator)
      4. Return top 5 suggestions with reasons
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.config = DraftConfig()
        self.lane_selector = LaneSelector()
        self.hero_evaluator = HeroEvaluator()

        # Load heroes once on init
        self.heroes_data = self._load_heroes_from_db()

        # Diversity tracking (prevents same hero being suggested repeatedly)
        self.suggestion_count: Dict[str, int] = {}

    def suggest_best_lane_and_heroes(
        self,
        banned_heroes: List[str],
        enemy_picks: List[str],
        ally_picks: List[str],
    ) -> Dict[str, Any]:
        """
        Main entry point for draft suggestions.

        Args:
            banned_heroes: Banned hero names
            enemy_picks: Enemy team's picks
            ally_picks: Your team's picks

        Returns:
            {
                "recommended_lane": "Jungle",
                "lane_code": "jungle",
                "reasoning": "...",
                "suggestions": [ {hero, score, reasons, role}, ... ]
            }
        """
        if not self.heroes_data:
            logger.error("No heroes loaded from database")
            return {
                "recommended_lane": "Unknown",
                "lane_code": "unknown",
                "reasoning": "No hero data available",
                "suggestions": [],
            }

        logger.info(
            f"Draft request: {len(ally_picks)} ally picks, {len(enemy_picks)} enemy picks, {len(banned_heroes)} bans"
        )

        # Step 1: Pick the best lane to fill
        lane_code, lane_name, lane_reasoning = self.lane_selector.select_best_lane(
            banned_heroes, enemy_picks, ally_picks, self.heroes_data
        )

        logger.info(f"Recommended lane: {lane_name}")

        # Step 2: Get hero suggestions for that lane
        suggestions = self._get_suggestions(
            banned_heroes, enemy_picks, ally_picks, lane_code
        )

        return {
            "recommended_lane": lane_name,
            "lane_code": lane_code,
            "reasoning": lane_reasoning,
            "suggestions": suggestions,
        }

    def _get_suggestions(
        self,
        banned_heroes: List[str],
        enemy_picks: List[str],
        ally_picks: List[str],
        lane_code: str,
    ) -> List[Dict[str, Any]]:
        """
        Score all available heroes for the target lane and return top 5.

        Heroes who cannot play the lane are filtered out automatically
        by the HeroEvaluator (score = 0).
        """
        # Build set of unavailable heroes
        unavailable = set(h.lower() for h in banned_heroes + enemy_picks + ally_picks)

        # Get candidates (available heroes only)
        candidates = [
            name for name in self.heroes_data if name.lower() not in unavailable
        ]

        logger.info(f"Evaluating {len(candidates)} candidates for {lane_code}")

        # Score each candidate
        scored = []
        for hero_name in candidates:
            try:
                hero = self.heroes_data[hero_name]
                score, reasons = self.hero_evaluator.evaluate_hero(
                    hero_name,
                    hero,
                    banned_heroes,
                    enemy_picks,
                    ally_picks,
                    lane_code,
                    self.heroes_data,
                )

                # Skip heroes who can't play the lane (score = 0)
                if score <= 0:
                    continue

                # Apply diversity penalty
                penalty = self._get_diversity_penalty(hero_name)
                final_score = score * (1 - penalty)

                # Get hero role
                role = (
                    hero.get("meta", {})
                    .get("attributes", {})
                    .get("roles", {})
                    .get("primary_role", "Unknown")
                )

                scored.append(
                    {
                        "hero": hero_name,
                        "score": round(final_score, 2),
                        "reasons": reasons,
                        "role": role,
                    }
                )

            except Exception as e:
                logger.error(f"Error evaluating {hero_name}: {e}")
                continue

        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[: self.config.TOP_SUGGESTIONS_COUNT]

        logger.info(f"Top {len(top)} suggestions for {lane_code}:")
        for s in top:
            logger.info(f"  {s['hero']}: {s['score']:.2f}")

        # Track suggestions for diversity
        for s in top:
            hero = s["hero"]
            self.suggestion_count[hero] = self.suggestion_count.get(hero, 0) + 1

        return top

    def _get_diversity_penalty(self, hero_name: str) -> float:
        """Penalty for frequently suggested heroes to ensure variety"""
        count = self.suggestion_count.get(hero_name, 0)
        if count == 0:
            return 0.0
        elif count <= 2:
            return self.config.DIVERSITY_PENALTY_LOW
        elif count <= 4:
            return self.config.DIVERSITY_PENALTY_MID
        else:
            return self.config.DIVERSITY_PENALTY_HIGH

    def _load_heroes_from_db(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all heroes from database into memory.

        Only loads heroes that have valid meta attributes.
        """
        try:
            heroes_data = {}
            heroes = self.db.query(Hero).all()

            skipped = 0
            for hero in heroes:
                meta = hero.get_meta()
                if meta and "attributes" in meta:
                    heroes_data[hero.name] = {
                        "name": hero.name,
                        "meta": meta,
                    }
                else:
                    skipped += 1

            logger.info(
                f"Loaded {len(heroes_data)} heroes ({skipped} skipped - missing meta)"
            )
            return heroes_data

        except Exception as e:
            logger.error(f"Failed to load heroes from DB: {e}")
            return {}
