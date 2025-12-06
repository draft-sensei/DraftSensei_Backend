"""
Pydantic schemas for hero-related API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


# Meta attribute schemas
class CombatAttributes(BaseModel):
    """Combat-related attributes"""
    burst_damage: int = Field(ge=0, le=5)
    sustained_damage: int = Field(ge=0, le=5)
    poke: int = Field(ge=0, le=5)
    aoe_damage: int = Field(ge=0, le=5)
    single_target: int = Field(ge=0, le=5)
    anti_tank: int = Field(ge=0, le=5)
    anti_squishy: int = Field(ge=0, le=5)
    dps: int = Field(ge=0, le=5)


class SurvivabilityAttributes(BaseModel):
    """Survivability-related attributes"""
    tankiness: int = Field(ge=0, le=5)
    mobility: int = Field(ge=0, le=5)
    escape: int = Field(ge=0, le=5)
    regen: int = Field(ge=0, le=5)
    shields: int = Field(ge=0, le=5)


class UtilityAttributes(BaseModel):
    """Utility-related attributes"""
    crowd_control: int = Field(ge=0, le=5)
    displacement: int = Field(ge=0, le=5)
    silence: int = Field(ge=0, le=5)
    stun: int = Field(ge=0, le=5)
    slow: int = Field(ge=0, le=5)
    team_buff: int = Field(ge=0, le=5)
    team_heal: int = Field(ge=0, le=5)


class RangePlaystyleAttributes(BaseModel):
    """Range and playstyle attributes"""
    range: int = Field(ge=0, le=5)
    engage: int = Field(ge=0, le=5)
    peel: int = Field(ge=0, le=5)
    splitpush: int = Field(ge=0, le=5)
    waveclear: int = Field(ge=0, le=5)
    vision_or_traps: int = Field(ge=0, le=5)


class PowerCurveAttributes(BaseModel):
    """Power curve attributes"""
    early_game: int = Field(ge=0, le=5)
    mid_game: int = Field(ge=0, le=5)
    late_game: int = Field(ge=0, le=5)
    scaling: int = Field(ge=0, le=5)


class RolesAttributes(BaseModel):
    """Role-related attributes"""
    primary_role: str
    secondary_role: str
    lane_priority: List[str]


class MetaAttributes(BaseModel):
    """Complete meta attributes structure"""
    combat: CombatAttributes
    survivability: SurvivabilityAttributes
    utility: UtilityAttributes
    range_playstyle: RangePlaystyleAttributes
    power_curve: PowerCurveAttributes
    roles: RolesAttributes


class MetaReasoning(BaseModel):
    """Meta reasoning structure"""
    how_stats_influenced_scores: str
    how_skills_influenced_scores: str
    cooldown_impact: str
    special_passives_analysis: str
    final_role_justification: str


class HeroMeta(BaseModel):
    """Complete hero meta structure"""
    attributes: MetaAttributes
    reasoning: MetaReasoning


class HeroBase(BaseModel):
    """Base hero schema with common fields"""
    name: str = Field(description="Hero name", max_length=100)
    image: str = Field(description="URL to hero image", default="")


class HeroCreate(HeroBase):
    """Schema for creating a new hero"""
    stats: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Hero statistics and attributes"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Hero metadata and attributes"
    )


class HeroUpdate(BaseModel):
    """Schema for updating an existing hero"""
    name: Optional[str] = Field(None, max_length=100)
    image: Optional[str] = Field(None)
    stats: Optional[Dict[str, Any]] = Field(None)
    meta: Optional[Dict[str, Any]] = Field(None)


class Hero(HeroBase):
    """Schema for hero response"""
    id: int = Field(description="Hero ID")
    stats: Dict[str, Any] = Field(
        default={},
        description="Hero statistics and attributes"
    )
    meta: Dict[str, Any] = Field(
        default={},
        description="Hero metadata and attributes"
    )

    created_at: datetime = Field(description="Creation timestamp")
    updated_at: Optional[datetime] = Field(description="Last update timestamp")

    class Config:
        from_attributes = True


class HeroList(BaseModel):
    """Schema for hero list response"""
    heroes: List[Hero] = Field(description="List of heroes")
    total: int = Field(description="Total number of heroes")


class HeroStats(BaseModel):
    """Schema for detailed hero statistics"""
    hp: Optional[int] = Field(description="Hero health points")
    mana: Optional[int] = Field(description="Hero mana points") 
    attack_damage: Optional[int] = Field(description="Base attack damage")
    physical_defense: Optional[int] = Field(description="Physical defense")
    magic_defense: Optional[int] = Field(description="Magic defense")
    movement_speed: Optional[int] = Field(description="Movement speed")
    attack_speed: Optional[float] = Field(description="Attack speed")
    cooldown_reduction: Optional[float] = Field(description="Cooldown reduction")
    critical_chance: Optional[float] = Field(description="Critical chance")
    penetration: Optional[int] = Field(description="Penetration")
    spell_vamp: Optional[float] = Field(description="Spell vamp")
    physical_lifesteal: Optional[float] = Field(description="Physical lifesteal")


class HeroMetadata(BaseModel):
    """Schema for hero metadata and patch information"""
    patch_version: Optional[str] = Field(description="Game patch version")
    tier_ranking: Optional[str] = Field(
        description="Tier ranking (S, A, B, C, D)"
    )
    win_rate: Optional[float] = Field(
        description="Global win rate percentage",
        ge=0,
        le=100
    )
    pick_rate: Optional[float] = Field(
        description="Pick rate percentage",
        ge=0,
        le=100
    )
    ban_rate: Optional[float] = Field(
        description="Ban rate percentage", 
        ge=0,
        le=100
    )


class HeroSearchRequest(BaseModel):
    """Schema for hero search requests"""
    query: Optional[str] = Field(
        default=None,
        description="Search query for hero name"
    )
    role: Optional[str] = Field(
        default=None,
        description="Filter by role"
    )
    tier: Optional[str] = Field(
        default=None,
        description="Filter by tier ranking"
    )
    limit: Optional[int] = Field(
        default=50,
        description="Maximum number of results",
        gt=0,
        le=100
    )
    offset: Optional[int] = Field(
        default=0,
        description="Pagination offset",
        ge=0
    )

    @validator('role')
    def validate_role(cls, v):
        """Validate role filter"""
        if v is None:
            return None
        valid_roles = ["Tank", "Fighter", "Assassin", "Mage", "Marksman", "Support"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of {valid_roles}")
        return v

    @validator('tier')
    def validate_tier(cls, v):
        """Validate tier filter"""
        if v is None:
            return None
        valid_tiers = ["S", "A", "B", "C", "D"]
        if v not in valid_tiers:
            raise ValueError(f"Tier must be one of {valid_tiers}")
        return v


class BulkHeroUpdate(BaseModel):
    """Schema for bulk hero updates (patch data)"""
    heroes: List[HeroCreate] = Field(description="List of heroes to create/update")
    patch_version: Optional[str] = Field(description="Patch version")
    update_mode: str = Field(
        default="merge",
        description="Update mode: 'replace' or 'merge'"
    )

    @validator('update_mode')
    def validate_update_mode(cls, v):
        """Validate update mode"""
        if v not in ["replace", "merge"]:
            raise ValueError("Update mode must be 'replace' or 'merge'")
        return v