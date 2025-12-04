"""
DraftSensei - AI-Powered Mobile Legends Draft Assistant Backend
Main FastAPI application setup and configuration
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import logging

from app.db.database import init_db, test_connection
from app.routers import draft_router, heroes_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting DraftSensei Backend...")
    
    # Test database connection
    if test_connection():
        logger.info("Database connection successful")
        # Initialize database tables
        init_db()
        logger.info("Database initialized")
    else:
        logger.error("Database connection failed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DraftSensei Backend...")


# Create FastAPI application
app = FastAPI(
    title="DraftSensei API",
    description="""
    🎮 **DraftSensei** - AI-Powered Mobile Legends Draft Assistant Backend
    
    ## Features
    
    * **AI Draft Suggestions** - Get intelligent hero pick recommendations based on team compositions, synergies, and counter strategies
    * **Hero Management** - Complete hero database with stats, roles, and relationships
    * **Team Analysis** - Analyze team compositions for strengths, weaknesses, and synergy scores
    * **Ban Suggestions** - Strategic ban recommendations to deny enemy strong picks
    * **Match Tracking** - Record match results to improve future recommendations
    * **Meta Analytics** - Current meta trends and hero performance statistics
    
    ## API Endpoints
    
    ### Draft Endpoints
    * `POST /draft/suggest` - Get hero pick suggestions
    * `POST /draft/ban-suggest` - Get hero ban suggestions  
    * `POST /draft/analyze` - Analyze team composition
    * `POST /draft/record-match` - Record match results
    * `GET /draft/meta-stats` - Get meta statistics
    
    ### Heroes Endpoints
    * `GET /heroes/list` - List all heroes with pagination and filtering
    * `GET /heroes/{hero_name}` - Get detailed hero information
    * `GET /heroes/{hero_name}/counters` - Get hero counter relationships
    * `GET /heroes/{hero_name}/synergy` - Get hero synergy relationships
    * `POST /heroes/create` - Create new hero
    * `PUT /heroes/{hero_name}` - Update hero information
    * `POST /heroes/update-bulk` - Bulk update heroes from patch data
    
    ## Usage Example
    
    ```python
    import requests
    
    # Get draft suggestions
    response = requests.post("http://localhost:8000/draft/suggest", json={
        "ally_picks": ["Lolita", "Yin"],
        "enemy_picks": ["Valentina", "Esmeralda"],
        "role_preference": "Tank"
    })
    
    suggestions = response.json()["best_picks"]
    print(f"Recommended: {suggestions[0]['hero']} (Score: {suggestions[0]['score']})")
    ```
    """,
    version="1.0.0",
    contact={
        "name": "DraftSensei Team",
        "email": "support@draftsensei.com"
    },
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(draft_router)
app.include_router(heroes_router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information"""
    return {
        "message": "🎮 Welcome to DraftSensei - AI-Powered Mobile Legends Draft Assistant",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
        "redoc": "/redoc",
        "api_endpoints": {
            "draft_suggestions": "/draft/suggest",
            "hero_list": "/heroes/list",
            "hero_details": "/heroes/{hero_name}",
            "team_analysis": "/draft/analyze",
            "ban_suggestions": "/draft/ban-suggest"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db_status = "healthy" if test_connection() else "unhealthy"
        
        return {
            "status": "healthy",
            "service": "draftsensei-backend",
            "version": "1.0.0",
            "database": db_status,
            "environment": os.getenv("ENV", "development")
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )


@app.get("/info", tags=["Info"])
async def app_info():
    """Application information and statistics"""
    try:
        from app.db.database import SessionLocal
        from app.db.models import Hero, MatchHistory
        
        db = SessionLocal()
        try:
            hero_count = db.query(Hero).count()
            match_count = db.query(MatchHistory).count()
            
            return {
                "application": "DraftSensei Backend",
                "version": "1.0.0",
                "description": "AI-Powered Mobile Legends Draft Assistant",
                "statistics": {
                    "total_heroes": hero_count,
                    "total_matches": match_count,
                    "database_status": "connected"
                },
                "features": [
                    "AI Draft Recommendations",
                    "Hero Counter Analysis", 
                    "Team Synergy Calculation",
                    "Meta Performance Tracking",
                    "Ban Strategy Suggestions"
                ],
                "supported_roles": [
                    "Tank", "Fighter", "Assassin", 
                    "Mage", "Marksman", "Support"
                ]
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Info endpoint failed: {e}")
        return {
            "application": "DraftSensei Backend",
            "version": "1.0.0",
            "status": "partial",
            "error": "Could not fetch statistics"
        }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error occurred",
            "error_type": type(exc).__name__
        }
    )


# Custom 404 handler
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": f"Endpoint '{request.url.path}' not found",
            "available_endpoints": {
                "docs": "/docs",
                "draft": "/draft/suggest", 
                "heroes": "/heroes/list",
                "health": "/health"
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting DraftSensei on {host}:{port} (debug={debug})")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )