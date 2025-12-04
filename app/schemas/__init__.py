"""
Schemas module initialization
"""

from .draft_schema import (
    DraftRequest, DraftResponse, HeroPick, BanSuggestionRequest, BanResponse,
    TeamComposition, MatchResult, DraftAnalytics
)
from .hero_schema import (
    Hero, HeroCreate, HeroUpdate, HeroList, HeroStats, HeroCounters, 
    HeroSynergy, HeroMetadata, HeroSearchRequest, BulkHeroUpdate
)

__all__ = [
    # Draft schemas
    "DraftRequest",
    "DraftResponse", 
    "HeroPick",
    "BanSuggestionRequest",
    "BanResponse",
    "TeamComposition",
    "MatchResult",
    "DraftAnalytics",
    
    # Hero schemas
    "Hero",
    "HeroCreate",
    "HeroUpdate", 
    "HeroList",
    "HeroStats",
    "HeroCounters",
    "HeroSynergy",
    "HeroMetadata",
    "HeroSearchRequest",
    "BulkHeroUpdate"
]