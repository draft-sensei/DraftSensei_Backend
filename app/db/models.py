"""
Database models for DraftSensei Mobile Legends Draft Assistant
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import json

Base = declarative_base()


class Hero(Base):
    """
    Hero model storing all hero information and metadata
    """
    __tablename__ = "heroes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    image = Column(String(500), nullable=True)  # Hero image URL
    stats_json = Column(Text, nullable=True)  # JSON string with hero stats
    meta_json = Column(Text, nullable=True)  # JSON string with hero meta
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    match_histories = relationship("MatchHistory", back_populates="hero")
    player_preferences = relationship("PlayerPreference", back_populates="hero")

    def get_stats(self):
        """Get hero stats as dictionary"""
        if self.stats_json:
            return json.loads(self.stats_json)
        return {}

    @property
    def stats(self):
        """Property to get stats as dict"""
        return self.get_stats()

    def set_stats(self, stats_dict):
        """Set hero stats from dictionary"""
        self.stats_json = json.dumps(stats_dict)

    def get_meta(self):
        """Get hero meta as dictionary"""
        if self.meta_json:
            return json.loads(self.meta_json)
        return {}

    @property
    def meta(self):
        """Property to get meta as dict"""
        return self.get_meta()

    def set_meta(self, meta_dict):
        """Set hero meta from dictionary"""
        self.meta_json = json.dumps(meta_dict)

    def __repr__(self):
        return f"<Hero(id={self.id}, name='{self.name}')>"


class MatchHistory(Base):
    """
    Match history model for tracking hero performance
    """
    __tablename__ = "match_history"

    id = Column(Integer, primary_key=True, index=True)
    hero_id = Column(Integer, ForeignKey("heroes.id"), nullable=False)
    performance_score = Column(Float, nullable=False)  # 0.0 to 100.0
    match_duration = Column(Integer, nullable=True)  # Duration in seconds
    ally_composition = Column(Text, nullable=True)  # JSON string of ally heroes
    enemy_composition = Column(Text, nullable=True)  # JSON string of enemy heroes
    game_mode = Column(String(50), default="ranked")  # ranked, classic, etc.
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    hero = relationship("Hero", back_populates="match_histories")

    def get_ally_composition(self):
        """Get ally composition as list"""
        if self.ally_composition:
            return json.loads(self.ally_composition)
        return []

    def get_enemy_composition(self):
        """Get enemy composition as list"""
        if self.enemy_composition:
            return json.loads(self.enemy_composition)
        return []

    def set_ally_composition(self, composition_list):
        """Set ally composition from list"""
        self.ally_composition = json.dumps(composition_list)

    def set_enemy_composition(self, composition_list):
        """Set enemy composition from list"""
        self.enemy_composition = json.dumps(composition_list)

    def __repr__(self):
        return f"<MatchHistory(id={self.id}, hero_id={self.hero_id}, score={self.performance_score})>"

class PlayerPreference(Base):
    """
    Player preference model for personalized recommendations
    """
    __tablename__ = "player_preferences"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(String(100), nullable=False, index=True)  # Player identifier
    hero_id = Column(Integer, ForeignKey("heroes.id"), nullable=False)
    weight = Column(Float, default=1.0)  # Preference weight (0.0 to 2.0)
    play_count = Column(Integer, default=0)  # Number of times played
    win_rate = Column(Float, default=0.0)  # Win rate percentage
    last_played = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    hero = relationship("Hero", back_populates="player_preferences")

    def update_performance(self, won: bool):
        """Update performance metrics after a match"""
        self.play_count += 1
        if won:
            # Update win rate using incremental formula
            self.win_rate = ((self.win_rate * (self.play_count - 1)) + 100) / self.play_count
        else:
            self.win_rate = (self.win_rate * (self.play_count - 1)) / self.play_count
        
        self.last_played = func.now()

    def __repr__(self):
        return f"<PlayerPreference(player_id='{self.player_id}', hero_id={self.hero_id}, weight={self.weight})>"
    