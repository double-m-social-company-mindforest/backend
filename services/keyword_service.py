from sqlalchemy.orm import Session
from database.models import Category, MainKeyword, SubKeyword
from schemas.keywords import CategoryKeywords, KeywordItem
from typing import List, Optional


class KeywordService:
    """키워드 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    # 카테고리별 영어 이름과 instruction 매핑
    CATEGORY_MAPPING = {
        1: {"english_name": "Mind", "instruction": "키워드를 우선순위에 맞게 순서대로 3개 선택해주세요."},
        2: {"english_name": "Daily Life", "instruction": "키워드를 우선순위에 맞게 순서대로 3개 선택해주세요."},
        3: {"english_name": "Leisure", "instruction": "키워드를 우선순위에 맞게 순서대로 3개 선택해주세요."}
    }

    @classmethod
    def get_category_by_id(cls, db: Session, category_id: int) -> Optional[Category]:
        """카테고리 ID로 카테고리 조회"""
        return db.query(Category).filter(Category.id == category_id).first()

    @classmethod
    def get_keywords_by_category_id(cls, db: Session, category_id: int) -> List[tuple]:
        """특정 카테고리의 모든 키워드 조회 (조인 쿼리)"""
        return db.query(
            SubKeyword.id,
            SubKeyword.name,
            MainKeyword.name.label('main_keyword_name'),
            Category.id.label('category_id'),
            Category.name.label('category_name'),
            Category.description
        ).join(
            MainKeyword, SubKeyword.main_keyword_id == MainKeyword.id
        ).join(
            Category, MainKeyword.category_id == Category.id
        ).filter(
            Category.id == category_id
        ).order_by(
            MainKeyword.display_order,
            SubKeyword.display_order
        ).all()

    @classmethod
    def get_all_category_ids(cls, db: Session) -> List[int]:
        """모든 카테고리 ID 조회 (display_order 순)"""
        return [id for (id,) in db.query(Category.id).order_by(Category.display_order).all()]

    @classmethod
    def build_category_keywords(cls, category_id: int, results: List[tuple]) -> Optional[CategoryKeywords]:
        """쿼리 결과를 CategoryKeywords 객체로 변환"""
        if not results:
            return None
            
        first_result = results[0]
        
        # 키워드 목록 생성
        keywords = [
            KeywordItem(
                id=result.id,
                name=result.name,
                main_keyword=result.main_keyword_name
            )
            for result in results
        ]
        
        # 카테고리 매핑 정보 가져오기
        mapping = cls.CATEGORY_MAPPING.get(category_id, {
            "english_name": "Unknown", 
            "instruction": "키워드를 우선순위에 맞게 순서대로 3개 선택해주세요."
        })
        
        return CategoryKeywords(
            id=first_result.category_id,
            name=first_result.category_name,
            english_name=mapping["english_name"],
            description=first_result.description or "",
            instruction=mapping["instruction"],
            keywords=keywords
        )

    @classmethod
    def get_category_keywords(cls, db: Session, category_id: int) -> Optional[CategoryKeywords]:
        """특정 카테고리의 키워드 데이터 조회"""
        # 카테고리 존재 확인
        if not cls.get_category_by_id(db, category_id):
            return None
            
        # 키워드 조회
        results = cls.get_keywords_by_category_id(db, category_id)
        
        return cls.build_category_keywords(category_id, results)

    @classmethod
    def get_all_categories_keywords(cls, db: Session) -> List[CategoryKeywords]:
        """모든 카테고리의 키워드 데이터 조회"""
        categories = []
        
        for category_id in cls.get_all_category_ids(db):
            category_data = cls.get_category_keywords(db, category_id)
            if category_data:
                categories.append(category_data)
        
        return categories