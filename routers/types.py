from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.types import CharacterTypeResponse, AllCharacterTypesResponse
from services.character_type_service import CharacterTypeService

router = APIRouter()


@router.get("/types/{type_id}", response_model=CharacterTypeResponse)
def get_character_type(type_id: int, db: Session = Depends(get_db)):
    """특정 캐릭터 타입 조회 API"""
    try:
        character = CharacterTypeService.get_character_type(db, type_id)
        
        if not character:
            raise HTTPException(status_code=404, detail="Character type not found")
        
        return CharacterTypeResponse(character=character)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/types", response_model=AllCharacterTypesResponse)
def get_all_character_types(db: Session = Depends(get_db)):
    """모든 캐릭터 타입 조회 API"""
    try:
        characters = CharacterTypeService.get_all_character_types(db)
        
        if not characters:
            raise HTTPException(status_code=404, detail="No character types found")
        
        return AllCharacterTypesResponse(
            characters=characters,
            total=len(characters)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")