from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SessionStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# Session 1 schemas
class FutureVision(BaseModel):
    answer1: str = Field(..., min_length=1, max_length=500, description="5년 후 모습 1")
    answer2: str = Field(..., min_length=1, max_length=500, description="5년 후 모습 2")


class Goal(BaseModel):
    goal: str = Field(..., min_length=1, max_length=200, description="목표")
    first_step: str = Field(..., min_length=1, max_length=200, description="첫 걸음")


class Session1Request(BaseModel):
    future_vision: FutureVision
    goals: List[Goal] = Field(..., min_items=3, max_items=3, description="3개의 목표")

    class Config:
        json_schema_extra = {
            "example": {
                "future_vision": {
                    "answer1": "유명한 사람이 되고 싶다",
                    "answer2": "새로운 도전을 하고 싶다"
                },
                "goals": [
                    {
                        "goal": "자기계발 전문가 되기",
                        "first_step": "매일 책 한 권 읽기"
                    },
                    {
                        "goal": "유튜브 채널 운영",
                        "first_step": "첫 영상 기획하기"
                    },
                    {
                        "goal": "건강한 몸 만들기",
                        "first_step": "매일 30분 운동하기"
                    }
                ]
            }
        }


# Generic session schemas
class SessionDataResponse(BaseModel):
    id: int
    user_id: int
    session_number: int
    session_data: Dict[str, Any]
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SessionSaveResponse(BaseModel):
    status: str = "success"
    message: str
    data: dict

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "세션 1 데이터가 저장되었습니다",
                "data": {
                    "session_number": 1,
                    "status": "completed",
                    "updated_at": "2025-01-01T10:00:00Z"
                }
            }
        }


class SessionProgressItem(BaseModel):
    session_number: int
    title: str
    status: SessionStatus
    completed_at: Optional[datetime]


class UserProgressResponse(BaseModel):
    status: str = "success"
    data: dict

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "total_sessions": 8,
                    "completed_sessions": 2,
                    "progress_percentage": 25.0,
                    "sessions": [
                        {
                            "session_number": 1,
                            "title": "삶의 목표 설정",
                            "status": "completed",
                            "completed_at": "2025-01-01T10:00:00Z"
                        }
                    ]
                }
            }
        }


# Session 2 schemas
class HelpingExperience(BaseModel):
    experience: str = Field(..., min_length=1, max_length=1000, description="도움을 준 경험")
    meaning: str = Field(..., min_length=1, max_length=1000, description="그 일의 의미")


class ReluctantHelp(BaseModel):
    experience: str = Field(..., min_length=1, max_length=1000, description="내키지 않았지만 도운 경험")
    change: str = Field(..., min_length=1, max_length=1000, description="그로 인한 변화")


class ReceivedHelp(BaseModel):
    experience: str = Field(..., min_length=1, max_length=1000, description="도움받은 경험")
    impact: str = Field(..., min_length=1, max_length=1000, description="그 위로가 나의 삶에 미친 영향")


class KindnessWhenLacking(BaseModel):
    experience: str = Field(..., min_length=1, max_length=1000, description="부족함을 느낄 때 받은 친절")
    inspiration: str = Field(..., min_length=1, max_length=1000, description="그 친절이 준 영감")


class Session2Request(BaseModel):
    helping_experience: HelpingExperience
    reluctant_help: ReluctantHelp
    received_help: ReceivedHelp
    kindness_when_lacking: KindnessWhenLacking

    class Config:
        json_schema_extra = {
            "example": {
                "helping_experience": {
                    "experience": "아이들에게 책을 읽어주는 봉사활동을 했습니다",
                    "meaning": "아이들이 즐거워하는 모습을 보며 마음이 충만해졌습니다"
                },
                "reluctant_help": {
                    "experience": "친구의 이사를 도와준 적이 있습니다",
                    "change": "다른 사람에게 도움이 필요할 때 더 적극적으로 돕고 싶다는 생각이 들었습니다"
                },
                "received_help": {
                    "experience": "취업 실패로 힘들어할 때 선배가 자신의 경험을 나누며 위로해주었습니다",
                    "impact": "실패를 겪어도 다시 일어설 수 있다는 용기를 얻었습니다"
                },
                "kindness_when_lacking": {
                    "experience": "발표 준비가 부족했을 때 동료가 자료를 함께 준비해주었습니다",
                    "inspiration": "나도 누군가에게 그런 따뜻한 도움을 주고 싶다는 마음이 생겼습니다"
                }
            }
        }


# Session 3 schemas
class Session3Request(BaseModel):
    answer1: str = Field(..., min_length=1, max_length=2000, description="나의 삶에서 가장 큰 영향을 준 사람과 배운 가치")
    answer2: str = Field(..., min_length=1, max_length=2000, description="가장 가깝게 느낀 사람과 그 이유")
    answer3: List[str] = Field(..., min_items=2, max_items=2, description="관계의 지속성과 이어가게 한 이유 (2개 답변)")
    answer4: str = Field(..., min_length=1, max_length=2000, description="관계의 지속성이 삶의 의미에 미치는 영향")

    class Config:
        json_schema_extra = {
            "example": {
                "answer1": "어머니가 가장 큰 영향을 주었습니다. 어떤 상황에서도 포기하지 않는 인내심을 배웠습니다.",
                "answer2": "형이 가장 가깝게 느껴집니다. 힘들 때마다 조언과 응원을 아끼지 않았기 때문입니다.",
                "answer3": [
                    "네, 지금도 좋은 관계를 유지하고 있습니다.",
                    "서로에 대한 신뢰와 이해, 그리고 진심어린 관심이 관계를 이어가게 합니다."
                ],
                "answer4": "이런 지속적인 관계들이 제게는 삶의 든든한 버팀목이 되어주고, 어려움을 극복할 수 있는 힘을 줍니다."
            }
        }


# Session 4 schemas
class Session4Request(BaseModel):
    # 35.png - 감정 표현 활동 (2개)
    answer1: List[str] = Field(..., min_items=2, max_items=2, description="감정 표현 활동 (2개 답변)")

    # 38.png - 창조적 가치 찾기: 단어 (1개)
    answer2: str = Field(..., min_length=1, max_length=2000, description="내 삶의 의미를 가장 잘 표현하는 단어")

    # 39.png - 창조적 가치 찾기: 연결 (1개)
    answer3: str = Field(..., min_length=1, max_length=2000, description="답변한 단어에 내재하고 있다고 생각하는 가치")

    # 40.png - 창조적 가치 찾기: 활동 (1개)
    answer4: str = Field(..., min_length=1, max_length=2000, description="이 가치를 실현하기 위해 할 수 있는 활동")

    # 41.png - 자아정체감: 나를 표현하는 문장 (3개)
    answer5: List[str] = Field(..., min_items=3, max_items=3, description="나를 가장 잘 표현하는 문장 (3개 답변)")

    # 42.png - 자아정체감: 되고 싶은 나 (3개)
    answer6: List[str] = Field(..., min_items=3, max_items=3, description="진실으로 되었으면 하고 바라는 나 자신 (3개 답변)")

    # 43.png - 자아정체감: 바라는 것 (3개)
    answer7: List[str] = Field(..., min_items=3, max_items=3, description="내가 바라는 나 자신이 되기를 바라는 것 (3개 답변)")

    class Config:
        json_schema_extra = {
            "example": {
                "answer1": [
                    "오늘은 친구와 대화로 마음이 따뜻해졌습니다",
                    "이 감정이 나에게 소중한 연결감과 따뜻함을 의미합니다"
                ],
                "answer2": "희망",
                "answer3": "희망은 나에게 삶의 동력이 되는 의미입니다",
                "answer4": "매일 감사 일기를 쓰며 긍정적인 마음 유지하기",
                "answer5": [
                    "나는 도전을 두려워하지 않는 사람입니다",
                    "나는 타인의 아픔을 공감할 수 있는 사람입니다",
                    "나는 끊임없이 성장하려는 사람입니다"
                ],
                "answer6": [
                    "더 용기 있는 사람",
                    "더 지혜로운 사람",
                    "더 따뜻한 사람"
                ],
                "answer7": [
                    "많은 사람에게 영감을 주는 사람",
                    "자신의 분야에서 전문가",
                    "행복한 가정을 이룬 사람"
                ]
            }
        }


# Session 5 schemas
class Session5Request(BaseModel):
    # 47.png - 바꿀 수 없는 상황 대응
    unchangeable_situation: str = Field(..., min_length=1, max_length=2000, description="바꿀 수 없는 상황 설명")
    response_to_situation: str = Field(..., min_length=1, max_length=2000, description="상황 대응 방식")

    # 49.png - 타인의 극복 사례
    person_or_media: str = Field(..., min_length=1, max_length=2000, description="사람 또는 매체 소개")
    overcoming_method: str = Field(..., min_length=1, max_length=2000, description="극복 방법 설명")

    # 58.png - 나의 나무 (텍스트 입력)
    my_tree_thought: str = Field(..., min_length=1, max_length=2000, description="나의 나무에 대한 생각")

    class Config:
        json_schema_extra = {
            "example": {
                "unchangeable_situation": "직장에서 갑작스럽게 프로젝트가 취소되어 몇 달간의 노력이 물거품이 되었습니다.",
                "response_to_situation": "처음에는 실망했지만, 이 경험을 통해 배운 점들을 정리하고 다음 프로젝트에 활용할 수 있는 기회로 삼았습니다.",
                "person_or_media": "스티브 잡스가 애플에서 해고된 후 다시 돌아와 성공한 이야기",
                "overcoming_method": "실패를 인생의 전환점으로 받아들이고, 그 시간을 자기 성찰과 새로운 도전의 기회로 활용했습니다.",
                "my_tree_thought": "저 강렬한 뿌리처럼, 나는 내 삶을 단단히 세울 수 있어."
            }
        }


# Session 6 schemas
class Session6Request(BaseModel):
    # 70.png - 유일성 질문 1
    unique_situation: str = Field(..., min_length=1, max_length=2000, description="당신은 어떤 가정에서 태어났나요? 관련 답변")

    # 71.png - 유일성 질문 2
    unique_life_path: str = Field(..., min_length=1, max_length=2000, description="지금까지의 삶의 목적/의미 관련 답변")

    # 74.png - 괄호 채우기 (5개)
    fill_blank_1: str = Field(..., min_length=1, max_length=500, description="첫 번째 괄호 답")
    fill_blank_2: str = Field(..., min_length=1, max_length=500, description="두 번째 괄호 답")
    fill_blank_3: str = Field(..., min_length=1, max_length=500, description="세 번째 괄호 답")
    fill_blank_4: str = Field(..., min_length=1, max_length=500, description="네 번째 괄호 답")
    fill_blank_5: str = Field(..., min_length=1, max_length=500, description="다섯 번째 괄호 답")

    # 74.png - 추가 질문
    life_meaning: str = Field(..., min_length=1, max_length=2000, description="이 문장이 보여주는 가치")

    class Config:
        json_schema_extra = {
            "example": {
                "unique_situation": "평범한 가정에서 태어났지만, 부모님의 노력과 사랑으로 꿈을 키울 수 있었습니다.",
                "unique_life_path": "지금까지 삶은 도전과 성장의 연속이었고, 이를 통해 더 나은 사람이 되고자 했습니다.",
                "fill_blank_1": "존재",
                "fill_blank_2": "나 자신",
                "fill_blank_3": "빛",
                "fill_blank_4": "사랑",
                "fill_blank_5": "영혼",
                "life_meaning": "이 문장은 제가 추구하는 진정성과 내면의 가치를 보여줍니다."
            }
        }


# Session info
SESSION_TITLES = {
    1: "삶의 목표 설정",
    2: "자기초월",
    3: "가치관 탐색",
    4: "감정 표현 활동",
    5: "감정 관리",
    6: "스트레스 대처",
    7: "미래 비전 구체화",
    8: "액션 플랜 수립"
}