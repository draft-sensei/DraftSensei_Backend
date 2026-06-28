"""
Database models for DraftSensei
Hero, MatchHistory, and PlayerPreference tables
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import json
import logging

from .database import Base

logger = logging.getLogger(__name__)


class Hero(Base):
    """Hero model storing hero information and meta attributes"""

    __tablename__ = "heroes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    image = Column(String(500), nullable=True)

    # Store stats and meta as JSON for flexibility
    stats_json = Column(JSON, nullable=True)  # Base stats, growth, etc.
    meta_json = Column(JSON, nullable=True)  # Attributes, reasoning, roles, etc.

    # Relationships
    match_histories = relationship(
        "MatchHistory", back_populates="hero", cascade="all, delete-orphan"
    )
    player_preferences = relationship(
        "PlayerPreference", back_populates="hero", cascade="all, delete-orphan"
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Hero(id={self.id}, name='{self.name}')>"

    def get_stats(self) -> dict:
        """Get hero stats as dictionary"""
        return self.stats_json or {}

    def set_stats(self, stats: dict):
        """Set hero stats"""
        self.stats_json = stats

    def get_meta(self) -> dict:
        """Get hero meta attributes as dictionary"""
        return self.meta_json or {}

    def set_meta(self, meta: dict):
        """Set hero meta attributes"""
        self.meta_json = meta

    def get_primary_role(self) -> str:
        """Get hero's primary role from meta"""
        meta = self.get_meta()
        if meta and isinstance(meta, dict):
            if "attributes" in meta and "roles" in meta["attributes"]:
                return meta["attributes"]["roles"].get("primary_role", "Unknown")
        return "Unknown"

    def get_lane_priority(self) -> list:
        """Get hero's lane priority list from meta"""
        meta = self.get_meta()
        if meta and isinstance(meta, dict):
            if "attributes" in meta and "roles" in meta["attributes"]:
                return meta["attributes"]["roles"].get("lane_priority", [])
        return []


class MatchHistory(Base):
    """Match history tracking hero performance"""

    __tablename__ = "match_histories"

    id = Column(Integer, primary_key=True, index=True)
    hero_id = Column(Integer, ForeignKey("heroes.id"), nullable=False, index=True)

    # Match result
    win = Column(Integer, default=0)  # 1 for win, 0 for loss
    performance_score = Column(Float, default=0.0)  # Custom performance metric (0-100)
    kda_score = Column(Float, nullable=True)  # K/D/A metric

    # Match details
    lane = Column(String(50), nullable=True)  # Lane played
    team_composition = Column(JSON, nullable=True)  # Other heroes picked
    enemy_composition = Column(JSON, nullable=True)  # Enemy heroes

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    hero = relationship("Hero", back_populates="match_histories")

    def __repr__(self):
        return f"<MatchHistory(hero_id={self.hero_id}, win={self.win}, score={self.performance_score})>"


class PlayerPreference(Base):
    """Player preference weights for hero recommendations"""

    __tablename__ = "player_preferences"

    id = Column(Integer, primary_key=True, index=True)
    hero_id = Column(
        Integer, ForeignKey("heroes.id"), nullable=False, unique=True, index=True
    )

    # Weight/preference value (0-100, higher = more preferred)
    weight = Column(Float, default=50.0)

    # Additional notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    hero = relationship("Hero", back_populates="player_preferences")

    def __repr__(self):
        return f"<PlayerPreference(hero_id={self.hero_id}, weight={self.weight})>"
