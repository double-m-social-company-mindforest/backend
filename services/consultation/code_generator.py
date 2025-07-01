import random
import string
from sqlalchemy.orm import Session
from database.models import Consultation


def generate_consultation_code(db: Session) -> str:
    """
    9자리 영문+숫자 조합의 고유한 상담 코드 생성
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        str: 9자리 상담 코드
    """
    while True:
        # 영문 대문자와 숫자를 조합하여 9자리 코드 생성
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=9))
        
        # 하이픈 없이 9자리 코드 그대로 사용
        formatted_code = code
        
        # 중복 확인
        existing = db.query(Consultation).filter(
            Consultation.consultation_code == formatted_code
        ).first()
        
        if not existing:
            return formatted_code