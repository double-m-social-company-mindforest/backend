from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.keywords import CategoryResponse, AllCategoriesResponse
from services.keyword_service import KeywordService

router = APIRouter()

@router.get("/test/keywords/{category_id}", response_model=CategoryResponse)
def get_keywords_by_category(category_id: int, db: Session = Depends(get_db)):
    """특정 카테고리 키워드 조회 API"""
    try:
        category_data = KeywordService.get_category_keywords(db, category_id)
        
        if not category_data:
            raise HTTPException(status_code=404, detail="Category not found")
        
        return CategoryResponse(category=category_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/test/keywords", response_model=AllCategoriesResponse)
def get_all_keywords(db: Session = Depends(get_db)):
    """모든 카테고리 키워드 조회 API"""
    try:
        categories = KeywordService.get_all_categories_keywords(db)
        
        if not categories:
            raise HTTPException(status_code=404, detail="No categories found")
        
        return AllCategoriesResponse(categories=categories)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")