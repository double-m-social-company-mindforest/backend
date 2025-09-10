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


# Session info
SESSION_TITLES = {
    1: "삶의 목표 설정",
    2: "자기초월",
    3: "가치관 탐색",
    4: "관계 패턴 이해",
    5: "감정 관리",
    6: "스트레스 대처",
    7: "미래 비전 구체화",
    8: "액션 플랜 수립"
}