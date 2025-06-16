from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from schemas.types import CharacterType


class KeywordSelectionRequest(BaseModel):
    """키워드 선택 요청 스키마"""
    selected_keywords: Dict[str, List[str]] = Field(
        ...,
        description="카테고리별 선택된 키워드들",
        example={
            "마음": ["긴장", "불확실성"],
            "일상": ["워라밸"],
            "여유": ["에너지", "경험", "상상"]
        }
    )


class TypeScore(BaseModel):
    """유형별 점수"""
    type_name: str
    score: float


class IntermediateTypeInfo(BaseModel):
    """중간 유형 정보"""
    id: int
    name: str
    description: Optional[str] = None
    characteristics: Optional[str] = None


class TypeCalculationResult(BaseModel):
    """유형 계산 결과"""
    first_type: str
    first_type_score: float
    first_type_id: int
    first_type_info: Optional[IntermediateTypeInfo] = None
    second_type: str
    second_type_score: float
    second_type_id: int
    second_type_info: Optional[IntermediateTypeInfo] = None
    final_type_id: int
    type_scores: Dict[str, float]
    calculation_details: Dict


class TypeMatchingResponse(BaseModel):
    """유형 매칭 응답"""
    character: CharacterType
    calculation_result: TypeCalculationResult
    message: str = "성공적으로 유형이 계산되었습니다."


class TypeCalculationOnlyResponse(BaseModel):
    """유형 계산만 하는 응답 (캐릭터 정보 없이)"""
    calculation_result: TypeCalculationResult
    message: str = "유형 계산이 완료되었습니다."