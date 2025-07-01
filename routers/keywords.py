from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.keywords import CategoryResponse, AllCategoriesResponse
from services.keyword_service import KeywordService

router = APIRouter(
    prefix="/api/v1/keywords",
    tags=["keywords"]
)


@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_keywords_by_category(
    category_id: int, 
    db: Session = Depends(get_db)
):
    """
    특정 카테고리의 키워드 조회
    
    - **category_id**: 조회할 카테고리 ID
    
    해당 카테고리에 속한 모든 주요 키워드와 세부 키워드를 반환합니다.
    성격 유형 테스트에서 사용자가 선택할 수 있는 키워드 목록을 제공합니다.
    """
    try:
        category_data = KeywordService.get_category_keywords(db, category_id)
        
        if not category_data:
            raise HTTPException(
                status_code=404, 
                detail=f"카테고리 ID {category_id}를 찾을 수 없습니다"
            )
        
        return CategoryResponse(category=category_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"키워드 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/categories", response_model=AllCategoriesResponse)
def get_all_keywords(db: Session = Depends(get_db)):
    """
    모든 카테고리의 키워드 조회
    
    성격 유형 테스트에 사용되는 모든 카테고리와 
    각 카테고리별 키워드 목록을 반환합니다.
    
    **반환 정보:**
    - 카테고리별 주요 키워드 목록
    - 각 주요 키워드별 세부 키워드 목록  
    - 키워드 표시 순서 정보
    """
    try:
        categories = KeywordService.get_all_categories_keywords(db)
        
        if not categories:
            raise HTTPException(
                status_code=404, 
                detail="등록된 카테고리가 없습니다"
            )
        
        return AllCategoriesResponse(categories=categories)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"키워드 조회 중 오류가 발생했습니다: {str(e)}"
        )