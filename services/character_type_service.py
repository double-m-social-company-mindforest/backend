from sqlalchemy.orm import Session
from database.models import FinalType
from schemas.types import CharacterType, StrengthWeakness
from typing import List, Optional


class CharacterTypeService:
    """캐릭터 타입 관련 비즈니스 로직을 처리하는 서비스 클래스"""

    @classmethod
    def get_character_by_id(cls, db: Session, type_id: int) -> Optional[FinalType]:
        """ID로 캐릭터 타입 조회"""
        return db.query(FinalType).filter(FinalType.id == type_id).first()

    @classmethod
    def get_all_characters(cls, db: Session) -> List[FinalType]:
        """모든 캐릭터 타입 조회 (ID 순)"""
        return db.query(FinalType).order_by(FinalType.id).all()

    @classmethod
    def convert_to_pydantic(cls, db_character: FinalType) -> CharacterType:
        """데이터베이스 모델을 Pydantic 모델로 변환"""
        # JSON 필드 파싱
        strengths = None
        if db_character.strengths:
            strengths = [
                StrengthWeakness(title=item["title"], description=item["description"])
                for item in db_character.strengths
                if isinstance(item, dict) and "title" in item and "description" in item
            ]

        weaknesses = None
        if db_character.weaknesses:
            weaknesses = [
                StrengthWeakness(title=item["title"], description=item["description"])
                for item in db_character.weaknesses
                if isinstance(item, dict) and "title" in item and "description" in item
            ]

        return CharacterType(
            id=db_character.id,
            name=db_character.name,
            animal=db_character.animal,
            group_name=db_character.group_name,
            one_liner=db_character.one_liner,
            overview=db_character.overview,
            greeting=db_character.greeting,
            hashtags=db_character.hashtags,
            strengths=strengths,
            weaknesses=weaknesses,
            relationship_style=db_character.relationship_style,
            behavior_pattern=db_character.behavior_pattern,
            image_filename=db_character.image_filename,
            image_filename_right=db_character.image_filename_right,
            strength_icons=db_character.strength_icons,
            weakness_icons=db_character.weakness_icons
        )

    @classmethod
    def get_character_type(cls, db: Session, type_id: int) -> Optional[CharacterType]:
        """특정 캐릭터 타입 조회 및 변환"""
        db_character = cls.get_character_by_id(db, type_id)
        if not db_character:
            return None
        return cls.convert_to_pydantic(db_character)

    @classmethod
    def get_all_character_types(cls, db: Session) -> List[CharacterType]:
        """모든 캐릭터 타입 조회 및 변환"""
        db_characters = cls.get_all_characters(db)
        return [cls.convert_to_pydantic(char) for char in db_characters]