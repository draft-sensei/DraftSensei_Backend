"""
Pydantic schemas for hero-related API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class HeroBase(BaseModel):
    """Base hero schema with common fields"""
    name: str = Field(description="Hero name", max_length=100)
    role: str = Field(description="Hero role")
    image: str = Field(description="URL to hero image", default="")

    @validator('role')
    def validate_role(cls, v):
        """Validate hero role"""
        valid_roles = ["Tank", "Fighter", "Assassin", "Mage", "Marksman", "Support"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of {valid_roles}")
        return v


class HeroCreate(HeroBase):
    """Schema for creating a new hero"""
    stats: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Hero statistics and attributes"
    )
    counters: Optional[Dict[str, float]] = Field(
        default=None,
        description="Hero counter relationships (hero_name: counter_score)"
    )
    synergy: Optional[Dict[str, float]] = Field(
        default=None,
        description="Hero synergy relationships (hero_name: synergy_score)"
    )


class HeroUpdate(BaseModel):
    """Schema for updating an existing hero"""
    name: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None)
    image: Optional[str] = Field(None)
    stats: Optional[Dict[str, Any]] = Field(None)
    counters: Optional[Dict[str, float]] = Field(None)
    synergy: Optional[Dict[str, float]] = Field(None)

    @validator('role')
    def validate_role(cls, v):
        """Validate hero role"""
        if v is None:
            return None
        valid_roles = ["Tank", "Fighter", "Assassin", "Mage", "Marksman", "Support"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of {valid_roles}")
        return v


class Hero(HeroBase):
    """Schema for hero response"""
    id: int = Field(description="Hero ID")
    stats: Dict[str, Any] = Field(
        default={},
        description="Hero statistics and attributes"
    )
    counters: Dict[str, float] = Field(
        default={},
        description="Hero counter relationships"
    )
    synergy: Dict[str, float] = Field(
        default={},
        description="Hero synergy relationships" 
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


class HeroCounters(BaseModel):
    """Schema for hero counter relationships"""
    hero_name: str = Field(description="Hero name")
    countered_by: List[str] = Field(
        description="Heroes that counter this hero",
        default=[]
    )
    counters: List[str] = Field(
        description="Heroes that this hero counters",
        default=[]
    )
    counter_scores: Dict[str, float] = Field(
        description="Counter strength scores (0-100)",
        default={}
    )


class HeroSynergy(BaseModel):
    """Schema for hero synergy relationships"""
    hero_name: str = Field(description="Hero name")
    synergies: Dict[str, float] = Field(
        description="Synergy scores with other heroes (0-100)",
        default={}
    )
    best_partners: List[str] = Field(
        description="Best hero partners",
        default=[]
    )


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