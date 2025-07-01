from typing import Dict, List, Optional
import random
from database.models import FinalType


class CharacterAIService:
    """캐릭터 AI 응답 서비스"""
    
    # 캐릭터별 기본 페르소나 정의
    CHARACTER_PERSONAS = {
        "default": {
            "greeting": "안녕하세요! 오늘 기분은 어떠세요?",
            "responses": [
                "그렇군요. 어떤 기분이신지 더 자세히 말씀해 주실 수 있나요?",
                "이해합니다. 그런 상황에서는 어떤 감정을 느끼셨나요?",
                "흥미롭네요. 그 경험에 대해 더 말씀해 주시겠어요?",
                "공감이 됩니다. 그런 일이 있었군요.",
                "그런 느낌이 드는 것은 자연스러운 반응이에요."
            ],
            "encouragements": [
                "힘내세요! 당신은 충분히 잘하고 있어요.",
                "어려운 시간이지만 분명 극복하실 수 있을 거예요.",
                "한 걸음씩 천천히 나아가는 것도 좋은 방법이에요.",
                "당신의 마음을 소중히 여기세요.",
                "지금 이 순간도 의미 있는 시간이에요."
            ]
        }
    }
    
    @staticmethod
    def get_character_greeting(character_type: FinalType) -> str:
        """
        캐릭터별 인사말 생성
        
        Args:
            character_type: 캐릭터 유형
            
        Returns:
            str: 인사말
        """
        if character_type.greeting:
            return character_type.greeting
        
        # 기본 인사말에 캐릭터 정보 추가
        default_greeting = CharacterAIService.CHARACTER_PERSONAS["default"]["greeting"]
        return f"안녕하세요! 저는 {character_type.name}({character_type.animal})입니다. {default_greeting}"
    
    @staticmethod
    def generate_response(
        character_type: FinalType,
        user_message: str,
        conversation_context: Optional[List[str]] = None
    ) -> str:
        """
        사용자 메시지에 대한 캐릭터 응답 생성
        
        Args:
            character_type: 캐릭터 유형
            user_message: 사용자 메시지
            conversation_context: 대화 맥락 (선택사항)
            
        Returns:
            str: 캐릭터 응답
        """
        # 메시지 길이에 따른 응답 선택
        if len(user_message.strip()) < 10:
            # 짧은 메시지에 대한 응답
            responses = [
                "더 자세히 말씀해 주실 수 있나요?",
                "어떤 의미인지 궁금해요.",
                "좀 더 구체적으로 설명해 주시겠어요?",
                "그 마음을 이해하고 싶어요."
            ]
        else:
            # 일반적인 응답
            responses = CharacterAIService.CHARACTER_PERSONAS["default"]["responses"]
        
        # 감정 키워드 기반 응답
        emotional_keywords = {
            "슬프": "슬픈 마음이 드시는군요. 그런 감정을 느끼는 것은 자연스러운 일이에요.",
            "기쁘": "기쁜 일이 있으셨나봐요! 좋은 감정을 나누어 주셔서 감사해요.",
            "화나": "화가 나는 상황이었군요. 그런 감정을 표현하는 것도 중요해요.",
            "불안": "불안한 마음이 드시는군요. 천천히 호흡하며 이야기해 보세요.",
            "걱정": "걱정이 많으시군요. 어떤 것들이 마음에 걸리시나요?",
            "스트레스": "스트레스를 받고 계시는군요. 어떤 상황 때문인지 말씀해 주세요.",
            "외로": "외로운 마음이 드시는군요. 그런 감정을 나누어 주셔서 고마워요."
        }
        
        # 감정 키워드 매칭
        for keyword, response in emotional_keywords.items():
            if keyword in user_message:
                return response
        
        # 캐릭터 특성 반영 (간단한 예시)
        if character_type.animal:
            animal_responses = {
                "고슴도치": "조금씩 마음을 여는 것부터 시작해보세요.",
                "늑대": "강한 의지로 극복할 수 있을 거예요.",
                "토끼": "부드러운 마음으로 받아들여 보세요.",
                "곰": "든든한 마음으로 지켜보고 있어요.",
                "여우": "영리하게 해결책을 찾아보세요."
            }
            
            if character_type.animal in animal_responses:
                if random.random() < 0.3:  # 30% 확률로 동물 특성 응답
                    return animal_responses[character_type.animal]
        
        # 기본 응답 중 랜덤 선택
        return random.choice(responses)
    
    @staticmethod
    def get_encouragement_message(character_type: FinalType) -> str:
        """
        격려 메시지 생성
        
        Args:
            character_type: 캐릭터 유형
            
        Returns:
            str: 격려 메시지
        """
        encouragements = CharacterAIService.CHARACTER_PERSONAS["default"]["encouragements"]
        
        # 캐릭터 특성 반영한 격려 메시지
        if character_type.strengths:
            strengths = character_type.strengths
            if isinstance(strengths, list) and strengths:
                strength = random.choice(strengths)
                return f"당신의 {strength} 같은 면이 정말 좋아요. 그 힘으로 충분히 해낼 수 있을 거예요!"
        
        return random.choice(encouragements)
    
    @staticmethod
    def handle_goodbye_message(character_type: FinalType) -> str:
        """
        작별 인사 메시지 생성
        
        Args:
            character_type: 캐릭터 유형
            
        Returns:
            str: 작별 인사
        """
        goodbyes = [
            "오늘 이야기를 나누어 주셔서 감사했어요. 좋은 하루 되세요!",
            "함께한 시간이 의미 있었어요. 언제든 다시 찾아오세요.",
            "소중한 시간을 함께해 주셔서 고마워요. 항상 응원하고 있을게요!",
            "오늘 대화가 도움이 되었길 바라요. 건강하게 지내세요!"
        ]
        
        return random.choice(goodbyes)