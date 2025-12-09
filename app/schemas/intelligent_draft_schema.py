"""
Pydantic schemas for intelligent draft suggestions
"""

from pydantic import BaseModel, Field, validator
from typing import List


class IntelligentDraftRequest(BaseModel):
    """Request for intelligent draft suggestions (auto-determines best lane)"""
    banned_heroes: List[str] = Field(default_factory=list, description="List of banned hero names")
    enemy_picks: List[str] = Field(default_factory=list, description="Enemy team's picked heroes")
    ally_picks: List[str] = Field(default_factory=list, description="Your team's picked heroes")

    @validator('banned_heroes', 'enemy_picks', 'ally_picks')
    def validate_hero_lists(cls, v):
        """Ensure hero lists don't have duplicates"""
        if len(v) != len(set(v)):
            raise ValueError("Hero lists must not contain duplicates")
        return v


class HeroSuggestion(BaseModel):
    """Individual hero suggestion with score and reasoning"""
    hero: str = Field(description="Hero name")
    score: float = Field(description="Recommendation score (0-100)")
    reasons: List[str] = Field(description="List of reasons why this hero is recommended")
    role: str = Field(description="Hero's primary role")


class IntelligentDraftResponse(BaseModel):
    """Response with recommended lane and hero suggestions"""
    recommended_lane: str = Field(description="Recommended lane to fill")
    lane_code: str = Field(description="Lane code for API")
    reasoning: str = Field(description="Explanation for why this lane was chosen")
    suggestions: List[HeroSuggestion] = Field(description="Top 5 hero suggestions for this lane")
