"""
Draft API Router - Intelligent hero draft suggestions
Uses refactored modular services
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.intelligent_draft_schema import (
    IntelligentDraftRequest,
    IntelligentDraftResponse,
    HeroSuggestion,
)
from app.services.draft.analyzer import DraftAnalyzer

router = APIRouter(prefix="/draft", tags=["draft"])


@router.post(
    "/suggest",
    response_model=IntelligentDraftResponse,
    summary="Get intelligent draft suggestions with adaptive weighting",
)
async def intelligent_suggest_picks(
    request: IntelligentDraftRequest, db: Session = Depends(get_db)
) -> IntelligentDraftResponse:
    """
    Advanced adaptive draft suggestion system that intelligently determines the best lane/role
    and recommends heroes using dynamic weight adjustment based on game state.

    **Adaptive Behavior:**
    - **Early draft (few picks)**: Prioritizes meta strength and pick priority
    - **Late draft (many picks)**: Increases weight on team composition and synergy
    - **Clear enemy patterns**: Boosts counter weight when enemy threats are identified
    - **Missing roles**: Strongly increases role_fit weight for critical gaps
    - **Many bans**: Adjusts to avoid weak niche picks

    **How it works:**
    - Analyzes draft pick order (1-2-2-2-2-1 pattern in MLBB)
    - For **first pick**: Secures high-priority meta heroes (Jungle/Mid priority)
    - For **later picks**:
      - Counters enemy threats in their lanes
      - Fills critical team composition gaps
      - Prioritizes remaining high-impact lane

    **Parameters:**
    - `banned_heroes`: List of banned hero names
    - `enemy_picks`: Enemy team's hero picks (in order)
    - `ally_picks`: Your team's hero picks (in order)

    **Returns:**
    - `recommended_lane`: The lane you should fill (e.g., "Jungle", "Mid Lane")
    - `lane_code`: Lane code for API usage ("jungle", "mid", "exp", "gold", "roam")
    - `reasoning`: Explanation for why this lane was chosen
    - `suggestions`: Top 5 hero picks with adaptive scoring and detailed reasoning

    **Example scenarios:**
    1. **First pick** → Suggests Jungle (highest impact) with meta heroes
    2. **Enemy picks strong mage** → Suggests Mid Lane to counter, increases counter weight
    3. **Team has no tank** → Suggests Roam/EXP with tanky heroes, boosts role_fit weight
    4. **Late draft with 4 picks** → Focuses on synergy and composition completion
    """
    try:
        # Initialize analyzer with database session
        analyzer = DraftAnalyzer(db)

        # Get suggestions
        result = analyzer.suggest_best_lane_and_heroes(
            banned_heroes=request.banned_heroes,
            enemy_picks=request.enemy_picks,
            ally_picks=request.ally_picks,
        )

        # Convert to response format
        suggestions = [
            HeroSuggestion(
                hero=s["hero"], score=s["score"], reasons=s["reasons"], role=s["role"]
            )
            for s in result["suggestions"]
        ]

        return IntelligentDraftResponse(
            recommended_lane=result["recommended_lane"],
            lane_code=result["lane_code"],
            reasoning=result["reasoning"],
            suggestions=suggestions,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating draft suggestions: {str(e)}",
        )
