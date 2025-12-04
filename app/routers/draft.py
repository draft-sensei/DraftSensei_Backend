"""
Draft API Router - Main endpoint for hero draft suggestions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..db.database import get_db
from ..schemas.draft_schema import (
    DraftRequest, DraftResponse, HeroPick, BanSuggestionRequest, 
    BanResponse, TeamComposition, MatchResult
)
from ..services.draft_engine import DraftEngine

router = APIRouter(prefix="/draft", tags=["draft"])


@router.post("/suggest", response_model=DraftResponse, summary="Get hero pick suggestions")
async def suggest_picks(
    request: DraftRequest,
    db: Session = Depends(get_db)
) -> DraftResponse:
    """
    Get AI-powered hero pick suggestions based on current draft state.
    
    - **ally_picks**: Heroes already picked by your team
    - **enemy_picks**: Heroes picked by the enemy team
    - **ally_bans**: Heroes banned by your team (optional)
    - **enemy_bans**: Heroes banned by enemy team (optional)
    - **player_id**: Player ID for personalized recommendations (optional)
    - **role_preference**: Preferred role to fill (optional)
    
    Returns the top hero recommendations with scores and reasoning.
    """
    try:
        # Initialize draft engine
        draft_engine = DraftEngine(db)
        
        # Get hero suggestions
        best_picks = draft_engine.suggest_picks(request)
        
        # Analyze current draft state
        team_analysis = draft_engine.analyze_draft_state(request)
        
        # Prepare response
        response = DraftResponse(
            best_picks=best_picks,
            team_analysis=team_analysis,
            meta_info={
                "version": "1.0",
                "algorithm": "weighted_multi_factor",
                "total_candidates": len(best_picks)
            }
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating suggestions: {str(e)}"
        )


@router.post("/ban-suggest", response_model=BanResponse, summary="Get hero ban suggestions")
async def suggest_bans(
    request: BanSuggestionRequest,
    db: Session = Depends(get_db)
) -> BanResponse:
    """
    Get AI-powered hero ban suggestions to deny enemy team strong picks.
    
    - **ally_picks**: Heroes already picked by your team
    - **enemy_picks**: Heroes picked by the enemy team  
    - **ally_bans**: Heroes already banned by your team
    - **enemy_bans**: Heroes already banned by enemy team
    - **ban_phase**: Current ban phase ('first' or 'second')
    
    Returns priority ban targets that threaten your team composition.
    """
    try:
        draft_engine = DraftEngine(db)
        
        # Convert ban request to draft request format
        draft_request = DraftRequest(
            ally_picks=request.ally_picks,
            enemy_picks=request.enemy_picks,
            ally_bans=request.ally_bans,
            enemy_bans=request.enemy_bans
        )
        
        # Get ban suggestions
        ban_suggestions = draft_engine.suggest_bans(draft_request)
        
        return BanResponse(best_bans=ban_suggestions)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating ban suggestions: {str(e)}"
        )


@router.post("/analyze", summary="Analyze team composition")
async def analyze_composition(
    ally_picks: List[str],
    db: Session = Depends(get_db)
) -> TeamComposition:
    """
    Analyze a team composition for strengths, weaknesses, and synergy.
    
    - **ally_picks**: List of hero names in the team composition
    
    Returns detailed analysis of the team composition including synergy score,
    role distribution, strengths, and weaknesses.
    """
    try:
        if not ally_picks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team composition cannot be empty"
            )
        
        draft_engine = DraftEngine(db)
        
        # Get hero roles
        roles = {}
        for hero in ally_picks:
            if hero in draft_engine.heroes_data:
                roles[hero] = draft_engine.heroes_data[hero]["role"]
            else:
                roles[hero] = "Unknown"
        
        # Analyze composition
        analysis = draft_engine.synergy_system.analyze_team_composition(ally_picks, roles)
        
        return TeamComposition(
            heroes=ally_picks,
            roles_filled=analysis["role_distribution"],
            synergy_score=analysis["synergy_score"],
            strengths=analysis["strengths"],
            weaknesses=analysis["weaknesses"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing composition: {str(e)}"
        )


@router.post("/record-match", summary="Record match result for learning")
async def record_match_result(
    match_result: MatchResult,
    db: Session = Depends(get_db)
):
    """
    Record a match result to improve future recommendations.
    
    - **hero_name**: Name of the hero played
    - **ally_team**: Complete allied team composition
    - **enemy_team**: Complete enemy team composition  
    - **performance_score**: Performance score (0-100)
    - **match_duration**: Match duration in seconds (optional)
    - **game_mode**: Game mode (ranked, classic, etc.)
    - **won**: Whether the match was won
    
    This data is used to improve the AI recommendation engine.
    """
    try:
        from ..db.models import Hero, MatchHistory
        
        # Find hero in database
        hero = db.query(Hero).filter(Hero.name == match_result.hero_name).first()
        if not hero:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hero '{match_result.hero_name}' not found"
            )
        
        # Create match history entry
        match_history = MatchHistory(
            hero_id=hero.id,
            performance_score=match_result.performance_score,
            match_duration=match_result.match_duration,
            game_mode=match_result.game_mode
        )
        
        # Set team compositions
        match_history.set_ally_composition(match_result.ally_team)
        match_history.set_enemy_composition(match_result.enemy_team)
        
        db.add(match_history)
        db.commit()
        
        return {"message": "Match result recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording match result: {str(e)}"
        )


@router.get("/meta-stats", summary="Get current meta statistics")
async def get_meta_stats(db: Session = Depends(get_db)):
    """
    Get current meta statistics and trends.
    
    Returns statistics about hero performance, pick rates, and meta trends
    based on recent match data.
    """
    try:
        from ..db.models import Hero, MatchHistory
        from sqlalchemy import func, desc
        
        # Get hero performance stats
        hero_stats = (
            db.query(
                Hero.name,
                Hero.role,
                func.avg(MatchHistory.performance_score).label('avg_score'),
                func.count(MatchHistory.id).label('match_count')
            )
            .join(MatchHistory)
            .group_by(Hero.id, Hero.name, Hero.role)
            .having(func.count(MatchHistory.id) >= 5)  # Minimum matches for stats
            .order_by(desc('avg_score'))
            .all()
        )
        
        meta_data = {
            "top_performers": [
                {
                    "hero": stat.name,
                    "role": stat.role,
                    "avg_performance": round(stat.avg_score, 1),
                    "matches": stat.match_count
                }
                for stat in hero_stats[:10]
            ],
            "role_distribution": {},
            "last_updated": "2024-12-04"  # Would be dynamic in production
        }
        
        # Calculate role distribution
        for stat in hero_stats:
            role = stat.role
            if role not in meta_data["role_distribution"]:
                meta_data["role_distribution"][role] = []
            meta_data["role_distribution"][role].append({
                "hero": stat.name,
                "performance": round(stat.avg_score, 1)
            })
        
        return meta_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching meta stats: {str(e)}"
        )