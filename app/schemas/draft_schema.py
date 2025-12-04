"""
Pydantic schemas for draft-related API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class DraftRequest(BaseModel):
    """Request schema for draft suggestions"""
    ally_picks: List[str] = Field(
        default=[],
        description="List of already picked ally heroes",
        example=["Lolita", "Yin"]
    )
    enemy_picks: List[str] = Field(
        default=[],
        description="List of already picked enemy heroes", 
        example=["Valentina", "Esmeralda"]
    )
    ally_bans: Optional[List[str]] = Field(
        default=[],
        description="List of banned heroes by ally team"
    )
    enemy_bans: Optional[List[str]] = Field(
        default=[],
        description="List of banned heroes by enemy team"
    )
    player_id: Optional[str] = Field(
        default=None,
        description="Optional player ID for personalized recommendations"
    )
    role_preference: Optional[str] = Field(
        default=None,
        description="Preferred role to fill (Tank, Fighter, Assassin, Mage, Marksman, Support)"
    )

    @validator('ally_picks', 'enemy_picks', 'ally_bans', 'enemy_bans')
    def validate_hero_lists(cls, v):
        """Validate that hero names are not empty strings"""
        if v is None:
            return []
        return [hero.strip() for hero in v if hero and hero.strip()]

    @validator('role_preference')
    def validate_role(cls, v):
        """Validate role preference"""
        if v is None:
            return None
        valid_roles = ["Tank", "Fighter", "Assassin", "Mage", "Marksman", "Support"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of {valid_roles}")
        return v


class HeroPick(BaseModel):
    """Schema for a single hero pick recommendation"""
    hero: str = Field(description="Hero name")
    score: float = Field(
        description="Recommendation score (0-100)",
        ge=0,
        le=100
    )
    reasons: List[str] = Field(
        description="List of reasons for this recommendation",
        default=[]
    )
    role: Optional[str] = Field(description="Hero role")
    confidence: Optional[float] = Field(
        description="Confidence level of recommendation (0-1)",
        ge=0,
        le=1,
        default=1.0
    )


class DraftResponse(BaseModel):
    """Response schema for draft suggestions"""
    best_picks: List[HeroPick] = Field(
        description="List of recommended hero picks (sorted by score)",
        max_items=10
    )
    team_analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Analysis of current team composition"
    )
    meta_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata about the recommendation"
    )


class BanSuggestionRequest(BaseModel):
    """Request schema for ban phase suggestions"""
    ally_picks: List[str] = Field(default=[])
    enemy_picks: List[str] = Field(default=[])
    ally_bans: List[str] = Field(default=[])
    enemy_bans: List[str] = Field(default=[])
    ban_phase: str = Field(
        default="first",
        description="Ban phase: 'first' or 'second'"
    )

    @validator('ban_phase')
    def validate_ban_phase(cls, v):
        """Validate ban phase"""
        if v not in ["first", "second"]:
            raise ValueError("Ban phase must be 'first' or 'second'")
        return v


class BanResponse(BaseModel):
    """Response schema for ban suggestions"""
    best_bans: List[HeroPick] = Field(
        description="List of recommended hero bans (sorted by priority)",
        max_items=5
    )


class TeamComposition(BaseModel):
    """Schema for team composition analysis"""
    heroes: List[str] = Field(description="List of hero names in the team")
    roles_filled: Dict[str, int] = Field(
        description="Count of heroes per role"
    )
    synergy_score: float = Field(
        description="Overall team synergy score",
        ge=0,
        le=100
    )
    weaknesses: List[str] = Field(
        description="Identified team weaknesses",
        default=[]
    )
    strengths: List[str] = Field(
        description="Identified team strengths", 
        default=[]
    )


class MatchResult(BaseModel):
    """Schema for recording match results"""
    hero_name: str = Field(description="Name of the hero played")
    ally_team: List[str] = Field(description="Allied team composition")
    enemy_team: List[str] = Field(description="Enemy team composition")
    performance_score: float = Field(
        description="Performance score (0-100)",
        ge=0,
        le=100
    )
    match_duration: Optional[int] = Field(
        description="Match duration in seconds",
        gt=0
    )
    game_mode: Optional[str] = Field(
        default="ranked",
        description="Game mode (ranked, classic, etc.)"
    )
    won: bool = Field(description="Whether the match was won")


class DraftAnalytics(BaseModel):
    """Schema for draft analytics and insights"""
    total_matches: int = Field(description="Total matches analyzed")
    win_rate: float = Field(
        description="Overall win rate",
        ge=0,
        le=100
    )
    popular_picks: List[Dict[str, Any]] = Field(
        description="Most popular hero picks with statistics"
    )
    meta_trends: Dict[str, Any] = Field(
        description="Current meta trends and statistics"
    )
    last_updated: datetime = Field(description="Last update timestamp")