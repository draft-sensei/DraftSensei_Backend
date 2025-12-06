"""
Heroes API Router - Endpoints for hero management and data
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional

from ..db.database import get_db
from ..db.models import Hero
from ..schemas.hero_schema import (
    Hero as HeroSchema, HeroCreate, HeroUpdate, HeroList, 
    HeroSearchRequest, BulkHeroUpdate
)

router = APIRouter(prefix="/heroes", tags=["heroes"])


@router.get("/list", response_model=HeroList, summary="Get list of all heroes")
async def get_heroes_list(
    skip: int = Query(0, ge=0, description="Number of heroes to skip"),
    limit: int = Query(150, ge=1, le=100, description="Number of heroes to return"),
    role: Optional[str] = Query(None, description="Filter by role"),
    search: Optional[str] = Query(None, description="Search by hero name"),
    db: Session = Depends(get_db)
) -> HeroList:
    """
    Get a paginated list of all heroes with optional filtering.
    
    - **skip**: Number of heroes to skip for pagination
    - **limit**: Maximum number of heroes to return (1-100)
    - **role**: Filter heroes by role (Tank, Fighter, Assassin, Mage, Marksman, Support)
    - **search**: Search heroes by name (case-insensitive partial match)
    
    Returns a list of heroes with their basic information and metadata.
    """
    try:
        query = db.query(Hero)
        
        # Apply search filter
        if search:
            query = query.filter(Hero.name.ilike(f"%{search}%"))
        
        # Get heroes (we'll filter by role in Python since it's in JSON)
        all_heroes = query.all()
        
        # Filter by role if specified (role is in meta JSON)
        if role:
            filtered_heroes = []
            for hero in all_heroes:
                meta = hero.get_meta()
                if meta and isinstance(meta, dict):
                    if 'attributes' in meta and 'roles' in meta['attributes']:
                        primary_role = meta['attributes']['roles'].get('primary_role', '')
                        if primary_role.lower() == role.lower():
                            filtered_heroes.append(hero)
            all_heroes = filtered_heroes
        
        # Get total count after filtering
        total = len(all_heroes)
        
        # Apply pagination
        heroes = all_heroes[skip:skip + limit]
        
        # Convert to response schema
        hero_list = []
        for hero in heroes:
            metadata = hero.get_meta()
            # Extract primary role from nested meta structure
            primary_role = "Unknown"
            if metadata and isinstance(metadata, dict):
                if 'attributes' in metadata and 'roles' in metadata['attributes']:
                    primary_role = metadata['attributes']['roles'].get('primary_role', 'Unknown')
            
            hero_data = HeroSchema(
                id=hero.id,
                name=hero.name,
                image=hero.image or "",
                stats=hero.get_stats(),
                meta=metadata,
                created_at=hero.created_at,
                updated_at=hero.updated_at
            )
            hero_list.append(hero_data)
        
        return HeroList(heroes=hero_list, total=total)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching heroes: {str(e)}"
        )


@router.get("/id/{hero_id}", response_model=HeroSchema, summary="Get hero by ID")
async def get_hero_by_id(
    hero_id: int,
    db: Session = Depends(get_db)
) -> HeroSchema:
    """
    Get detailed information for a specific hero by ID.
    
    - **hero_id**: Unique identifier of the hero
    
    Returns complete hero information including stats, counters, and synergies.
    """
    try:
        hero = db.query(Hero).filter(Hero.id == hero_id).first()
        
        if not hero:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hero with ID {hero_id} not found"
            )
        
        return HeroSchema(
            id=hero.id,
            name=hero.name,
            image=hero.image or "",
            stats=hero.get_stats(),
            meta=hero.get_meta(),
            created_at=hero.created_at,
            updated_at=hero.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching hero: {str(e)}"
        )


@router.get("/{hero_name}", response_model=HeroSchema, summary="Get hero by name")
async def get_hero_by_name(
    hero_name: str,
    db: Session = Depends(get_db)
) -> HeroSchema:
    """
    Get detailed information for a specific hero by name.
    
    - **hero_name**: Name of the hero (case-sensitive)
    
    Returns complete hero information including stats and metadata.
    """
    try:
        hero = db.query(Hero).filter(Hero.name == hero_name).first()
        
        if not hero:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hero '{hero_name}' not found"
            )
        
        return HeroSchema(
            id=hero.id,
            name=hero.name,
            image=hero.image or "",
            stats=hero.get_stats(),
            meta=hero.get_meta(),
            created_at=hero.created_at,
            updated_at=hero.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching hero: {str(e)}"
        )

@router.post("/create", response_model=HeroSchema, summary="Create a new hero")
async def create_hero(
    hero_data: HeroCreate,
    db: Session = Depends(get_db)
) -> HeroSchema:
    """
    Create a new hero in the database.
    
    - **name**: Hero name (must be unique)
    - **role**: Hero role
    - **stats**: Hero statistics (optional)
    - **meta**: Hero metadata (optional)
    
    Returns the created hero with generated ID and timestamps.
    """
    try:
        # Check if hero already exists
        existing_hero = db.query(Hero).filter(Hero.name == hero_data.name).first()
        if existing_hero:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Hero '{hero_data.name}' already exists"
            )
        
        # Create new hero
        new_hero = Hero(
            name=hero_data.name,
            image=hero_data.image
        )
        
        # Set optional data
        if hero_data.stats:
            new_hero.set_stats(hero_data.stats)
        if hero_data.meta:
            new_hero.set_meta(hero_data.meta)
        
        db.add(new_hero)
        db.commit()
        db.refresh(new_hero)
        
        return HeroSchema(
            id=new_hero.id,
            name=new_hero.name,
            image=new_hero.image or "",
            stats=new_hero.get_stats(),
            meta=new_hero.get_meta(),
            created_at=new_hero.created_at,
            updated_at=new_hero.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating hero: {str(e)}"
        )


@router.put("/{hero_name}", response_model=HeroSchema, summary="Update hero")
async def update_hero(
    hero_name: str,
    hero_update: HeroUpdate,
    db: Session = Depends(get_db)
) -> HeroSchema:
    """
    Update an existing hero's information.
    
    - **hero_name**: Name of the hero to update
    - All fields in request body are optional - only provided fields will be updated
    
    Returns the updated hero information.
    """
    try:
        hero = db.query(Hero).filter(Hero.name == hero_name).first()
        
        if not hero:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hero '{hero_name}' not found"
            )
        
        # Update fields if provided
        if hero_update.name is not None:
            # Check if new name conflicts
            if hero_update.name != hero.name:
                existing = db.query(Hero).filter(Hero.name == hero_update.name).first()
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Hero name '{hero_update.name}' already exists"
                    )
            hero.name = hero_update.name
        
        if hero_update.image is not None:
            hero.image = hero_update.image
        
        if hero_update.stats is not None:
            hero.set_stats(hero_update.stats)
        
        if hero_update.meta is not None:
            hero.set_meta(hero_update.meta)

        db.commit()
        db.refresh(hero)
        
        return HeroSchema(
            id=hero.id,
            name=hero.name,
            image=hero.image or "",
            stats=hero.get_stats(),
            meta=hero.get_meta(),
            created_at=hero.created_at,
            updated_at=hero.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating hero: {str(e)}"
        )


@router.post("/update-bulk", summary="Bulk update heroes from patch data")
async def bulk_update_heroes(
    bulk_update: BulkHeroUpdate,
    db: Session = Depends(get_db)
):
    """
    Bulk update or create heroes from patch data.
    
    - **heroes**: List of heroes to create or update
    - **patch_version**: Patch version identifier (optional)
    - **update_mode**: 'replace' to overwrite existing, 'merge' to update only (default: 'merge')
    
    Used for importing new patch data or updating hero statistics in bulk.
    """
    try:
        updated_count = 0
        created_count = 0
        errors = []
        
        for hero_data in bulk_update.heroes:
            try:
                # Check if hero exists
                existing_hero = db.query(Hero).filter(Hero.name == hero_data.name).first()
                
                if existing_hero:
                    # Update existing hero
                    if bulk_update.update_mode == "replace" or hero_data.stats:
                        if hero_data.stats:
                            existing_hero.set_stats(hero_data.stats)                   
                    
                    if bulk_update.update_mode == "replace" or hero_data.meta:
                        if hero_data.meta:
                            existing_hero.set_meta(hero_data.meta)
                    
                    if hero_data.image:
                        existing_hero.image = hero_data.image
                    
                    updated_count += 1
                else:
                    # Create new hero
                    new_hero = Hero(
                        name=hero_data.name,
                        image=hero_data.image or ""
                    )
                    
                    if hero_data.stats:
                        new_hero.set_stats(hero_data.stats)
                    if hero_data.meta:
                        new_hero.set_meta(hero_data.meta)
                    
                    db.add(new_hero)
                    created_count += 1
                    
            except Exception as e:
                errors.append(f"Error processing hero '{hero_data.name}': {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
        result = {
            "message": "Bulk update completed",
            "created": created_count,
            "updated": updated_count,
            "patch_version": bulk_update.patch_version
        }
        
        if errors:
            result["errors"] = errors
        
        return result
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in bulk update: {str(e)}"
        )


@router.delete("/{hero_name}", summary="Delete hero")
async def delete_hero(
    hero_name: str,
    db: Session = Depends(get_db)
):
    """
    Delete a hero from the database.
    
    - **hero_name**: Name of the hero to delete
    
    Warning: This will also delete all associated match history and preferences.
    """
    try:
        hero = db.query(Hero).filter(Hero.name == hero_name).first()
        
        if not hero:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hero '{hero_name}' not found"
            )
        
        db.delete(hero)
        db.commit()
        
        return {"message": f"Hero '{hero_name}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting hero: {str(e)}"
        )


@router.get("/roles/distribution", summary="Get role distribution stats")
async def get_role_distribution(db: Session = Depends(get_db)):
    """
    Get statistics about role distribution in the hero pool.
    
    Returns count of heroes per role and percentage distribution.
    """
    try:
        # Get all heroes and extract roles from meta
        heroes = db.query(Hero).all()
        role_counts = {}
        
        for hero in heroes:
            meta = hero.get_meta()
            if meta and isinstance(meta, dict):
                if 'attributes' in meta and 'roles' in meta['attributes']:
                    primary_role = meta['attributes']['roles'].get('primary_role', 'Unknown')
                    role_counts[primary_role] = role_counts.get(primary_role, 0) + 1
        
        total_heroes = len(heroes)
        
        distribution = {}
        for role, count in role_counts.items():
            distribution[role] = {
                "count": count,
                "percentage": round((count / total_heroes) * 100, 1) if total_heroes > 0 else 0
            }
        
        return {
            "total_heroes": total_heroes,
            "distribution": distribution
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching role distribution: {str(e)}"
        )
    