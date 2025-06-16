from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import IntermediateType
from schemas.intermediate_types import IntermediateTypesResponse

router = APIRouter()


@router.get("/intermediate-types", response_model=IntermediateTypesResponse)
def get_all_intermediate_types(db: Session = Depends(get_db)):
    """모든 중간 유형 조회 API"""
    try:
        types = db.query(IntermediateType).order_by(IntermediateType.display_order).all()
        
        if not types:
            raise HTTPException(status_code=404, detail="No intermediate types found")
        
        return IntermediateTypesResponse(
            intermediate_types=types,
            total=len(types)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/intermediate-types/{type_id}")
def get_intermediate_type(type_id: int, db: Session = Depends(get_db)):
    """특정 중간 유형 조회 API"""
    try:
        intermediate_type = db.query(IntermediateType).filter(IntermediateType.id == type_id).first()
        
        if not intermediate_type:
            raise HTTPException(status_code=404, detail="Intermediate type not found")
        
        return {
            "id": intermediate_type.id,
            "name": intermediate_type.name,
            "description": intermediate_type.description,
            "characteristics": intermediate_type.characteristics,
            "display_order": intermediate_type.display_order
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")